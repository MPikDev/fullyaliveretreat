"""Payment reconciliation.

The IPN handler in ``registration.signals`` is the normal way a camper becomes
paid. This module re-derives the same conclusion from the stored IPN records,
for the case where a notification was missed or arrived before the camper row
existed.

It applies exactly the same checks as the live handler — receiver, currency and
amount — so reconciling can never mark someone paid that the handler would have
rejected.
"""

import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_COMPLETED, ST_PP_REFUNDED, ST_PP_REVERSED

from registration.emails import send_registration_email
from registration.models import Camper

logger = logging.getLogger("registration.payments")

AMOUNT_TOLERANCE = Decimal("0.01")


def _invoice_to_id(raw):
    """Normalise an invoice value to a camper id, tolerating legacy '88.0' forms."""
    try:
        return int(Decimal((raw or "").strip()))
    except (InvalidOperation, ValueError):
        return None


def reconcile_season(season, send_email=True):
    """Re-check every IPN for a season. Returns (updated, flagged) counts.

    Only transactions recorded during the season's registration window are
    considered, so reconciling one camp cannot touch another.
    """
    ipns = PayPalIPN.objects.filter(flag=False)
    if season.registration_opens_at:
        ipns = ipns.filter(created_at__gte=season.registration_opens_at)
    if season.registration_closes_at:
        ipns = ipns.filter(created_at__lte=season.registration_closes_at)

    campers = {c.pk: c for c in season.campers.all()}
    expected_receiver = (settings.PAYPAL_RECEIVER_EMAIL or "").lower()

    to_mark_paid = {}
    to_mark_unpaid = set()
    flagged = 0

    for ipn in ipns.iterator():
        camper_id = _invoice_to_id(ipn.invoice)
        camper = campers.get(camper_id)
        if camper is None:
            continue

        if ipn.payment_status in {ST_PP_REFUNDED, ST_PP_REVERSED}:
            to_mark_unpaid.add(camper.pk)
            to_mark_paid.pop(camper.pk, None)
            continue

        if ipn.payment_status != ST_PP_COMPLETED:
            continue

        gross = ipn.mc_gross if ipn.mc_gross is not None else Decimal("0.00")
        reason = None
        if expected_receiver and (ipn.receiver_email or "").lower() != expected_receiver:
            reason = f"Receiver mismatch: {ipn.receiver_email!r}"
        elif (ipn.mc_currency or "").upper() != settings.PAYPAL_CURRENCY:
            reason = f"Currency mismatch: {ipn.mc_currency!r}"
        elif camper.amount_due is None:
            reason = "No amount_due recorded; cannot verify amount."
        elif gross + AMOUNT_TOLERANCE < camper.amount_due:
            reason = f"Underpayment: received {gross}, expected {camper.amount_due}."

        if reason:
            camper.payment_flagged = True
            camper.payment_note = reason[:255]
            camper.save(update_fields=["payment_flagged", "payment_note", "updated"])
            logger.warning("Reconcile flagged camper %s: %s", camper.pk, reason)
            flagged += 1
            continue

        to_mark_paid[camper.pk] = gross

    updated = 0
    newly_paid = []

    for camper_id, gross in to_mark_paid.items():
        if camper_id in to_mark_unpaid:
            continue
        camper = campers[camper_id]
        if camper.paid and camper.amount_paid == gross:
            continue
        was_paid = camper.paid
        camper.paid = True
        camper.amount_paid = gross
        camper.payment_flagged = False
        camper.payment_note = ""
        updated += 1
        if not was_paid and not camper.email_sent:
            newly_paid.append(camper)

    for camper_id in to_mark_unpaid:
        camper = campers[camper_id]
        if camper.paid:
            camper.paid = False
            updated += 1

    changed = [
        campers[cid] for cid in set(to_mark_paid) | to_mark_unpaid if cid in campers
    ]
    if changed:
        Camper.objects.bulk_update(
            changed, ["paid", "amount_paid", "payment_flagged", "payment_note"]
        )

    if send_email:
        for camper in newly_paid:
            try:
                send_registration_email(camper)
            except Exception:
                logger.exception("Confirmation email failed for camper %s", camper.pk)
            else:
                Camper.objects.filter(pk=camper.pk).update(email_sent=True)

    logger.info(
        "Reconciled %s: %s campers updated, %s flagged.", season.slug, updated, flagged
    )
    return updated, flagged
