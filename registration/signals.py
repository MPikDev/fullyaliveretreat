"""PayPal IPN handling.

This module is the single place a camper can be marked paid.

The previous implementation trusted the invoice number alone: any completed
PayPal transaction carrying a camper's id flipped ``paid = True``, and the
amount was never inspected. Because the amount is submitted from a form
rendered in the browser, a camper could edit the hidden ``amount`` field, pay a
token sum, and be recorded as fully paid.

Here every notification is checked against server-side state before it is
allowed to change anything: the receiver, the currency, the payment status, and
the gross amount against ``Camper.amount_due``. Anything that does not line up
is recorded and flagged for a human rather than silently accepted or silently
dropped.
"""

import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.dispatch import receiver
from paypal.standard.ipn.signals import invalid_ipn_received, valid_ipn_received
from paypal.standard.models import ST_PP_COMPLETED, ST_PP_REFUNDED, ST_PP_REVERSED

from registration.emails import send_registration_email
from registration.models import Camper

logger = logging.getLogger("registration.payments")

# Payment statuses that reverse a completed payment.
REVERSING_STATUSES = {ST_PP_REFUNDED, ST_PP_REVERSED}

# Tolerance for float/rounding noise in the reported gross amount.
AMOUNT_TOLERANCE = Decimal("0.01")


def _camper_for(ipn):
    """Resolve the Camper an IPN refers to, or None.

    Historical invoices were sometimes written as floats ("88.0"), so the value
    is normalised before lookup.
    """
    raw = (ipn.invoice or "").strip()
    if not raw:
        return None
    try:
        camper_id = int(Decimal(raw))
    except (InvalidOperation, ValueError):
        logger.warning("IPN %s has an unparseable invoice %r", ipn.txn_id, raw)
        return None
    return Camper.objects.filter(pk=camper_id).first()


def _flag(camper, reason):
    """Record a payment that needs a human decision. Never marks the camper paid."""
    logger.error("Payment flagged for camper %s: %s", camper.pk if camper else "?", reason)
    if camper is None:
        return
    camper.payment_flagged = True
    camper.payment_note = reason[:255]
    camper.save(update_fields=["payment_flagged", "payment_note", "updated"])


@receiver(valid_ipn_received)
def handle_valid_ipn(sender, **kwargs):
    """Apply a PayPal-verified notification, after checking it against our records."""
    ipn = sender

    camper = _camper_for(ipn)
    if camper is None:
        logger.error(
            "IPN %s references invoice %r which matches no camper; ignoring.",
            ipn.txn_id, ipn.invoice,
        )
        return

    if ipn.payment_status in REVERSING_STATUSES:
        _handle_reversal(ipn, camper)
        return

    if ipn.payment_status != ST_PP_COMPLETED:
        logger.info(
            "IPN %s for camper %s has status %s; no action taken.",
            ipn.txn_id, camper.pk, ipn.payment_status,
        )
        return

    # The money must have gone to our account, not one the payer chose.
    expected_receiver = (settings.PAYPAL_RECEIVER_EMAIL or "").lower()
    actual_receiver = (ipn.receiver_email or "").lower()
    if expected_receiver and actual_receiver != expected_receiver:
        _flag(camper, f"Receiver mismatch: paid to {actual_receiver!r}, expected {expected_receiver!r}")
        return

    if (ipn.mc_currency or "").upper() != settings.PAYPAL_CURRENCY:
        _flag(camper, f"Currency mismatch: got {ipn.mc_currency!r}, expected {settings.PAYPAL_CURRENCY}")
        return

    # The amount owed was computed on the server when the camper registered.
    # A client-supplied amount is never used for this comparison.
    if camper.amount_due is None:
        _flag(camper, "No amount_due recorded; cannot verify the payment amount.")
        return

    gross = ipn.mc_gross if ipn.mc_gross is not None else Decimal("0.00")
    if gross + AMOUNT_TOLERANCE < camper.amount_due:
        _flag(
            camper,
            f"Underpayment: received {gross} {ipn.mc_currency}, expected {camper.amount_due}.",
        )
        return

    _mark_paid(ipn, camper, gross)


def _mark_paid(ipn, camper, gross):
    """Record a fully verified payment and send the confirmation email."""
    with transaction.atomic():
        camper = Camper.objects.select_for_update().get(pk=camper.pk)
        already_paid = camper.paid
        camper.paid = True
        camper.amount_paid = gross
        camper.payment_flagged = False
        camper.payment_note = ""
        camper.save(update_fields=["paid", "amount_paid", "payment_flagged", "payment_note", "updated"])

    logger.info(
        "Camper %s marked paid from IPN %s (%s %s).",
        camper.pk, ipn.txn_id, gross, ipn.mc_currency,
    )

    if already_paid or camper.email_sent:
        return

    try:
        send_registration_email(camper)
    except Exception:
        # A mail failure must never roll back a recorded payment.
        logger.exception("Confirmation email failed for camper %s", camper.pk)
    else:
        Camper.objects.filter(pk=camper.pk).update(email_sent=True)


def _handle_reversal(ipn, camper):
    """A refund or reversal removes the camper's paid status."""
    if not camper.paid:
        return
    camper.paid = False
    camper.payment_note = f"{ipn.payment_status} on {ipn.txn_id}"[:255]
    camper.save(update_fields=["paid", "payment_note", "updated"])
    logger.warning(
        "Camper %s marked unpaid: %s on IPN %s.", camper.pk, ipn.payment_status, ipn.txn_id
    )


@receiver(invalid_ipn_received)
def handle_invalid_ipn(sender, **kwargs):
    """PayPal could not verify this notification. Record it; change nothing."""
    logger.error(
        "Invalid IPN received (txn %s, invoice %r): %s",
        sender.txn_id, sender.invoice, sender.flag_info,
    )
