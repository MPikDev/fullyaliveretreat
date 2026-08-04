"""Outbound camper email.

Message bodies are rendered from templates rather than built with f-strings, so
camper-supplied values are HTML-escaped and the copy can change without a code
edit. Sending is skipped when no app password is configured, which keeps tests
and local development off the network.
"""

import logging

from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger("registration")


def _send(to, subject, html):
    """Send one HTML message through the retreat's Gmail account."""
    if not settings.FAR_EMAIL_APP_PASSWORD:
        logger.warning(
            "FAR_EMAIL_APP_PASSWORD is not set; skipping email to %s (%r).", to, subject
        )
        return False

    import yagmail  # imported lazily so the app boots without network libraries warm

    yag = yagmail.SMTP(settings.FAR_EMAIL_ADDRESS, settings.FAR_EMAIL_APP_PASSWORD)
    try:
        yag.send(to=to, subject=subject, contents=[html])
    finally:
        try:
            yag.close()
        except Exception:  # pragma: no cover - closing is best effort
            pass
    return True


def send_registration_email(camper):
    """Confirm a completed registration and payment."""
    season = camper.season
    subject = f"You're registered for {season.name}!" if season else "You're registered!"
    html = render_to_string(
        "email/registration_confirmation.html",
        {
            "camper": camper,
            "season": season,
            "merch": camper.ordered_merch,
            "telegram_url": settings.TELEGRAM_URL,
            "instagram_url": settings.INSTAGRAM_URL,
        },
    )
    sent = _send(camper.email, subject, html)
    if sent:
        logger.info("Registration confirmation sent to camper %s.", camper.pk)
    return sent


def send_bulk_email(campers, subject, template, extra_context=None, dry_run=False):
    """Send one templated message to many campers.

    Returns (sent, failed) counts. With dry_run=True nothing is sent.
    """
    sent = failed = 0
    for camper in campers:
        context = {"camper": camper, "season": camper.season}
        context.update(extra_context or {})
        html = render_to_string(template, context)
        if dry_run:
            logger.info("[dry-run] would email %s <%s>", camper.full_name, camper.email)
            sent += 1
            continue
        try:
            _send(camper.email, subject, html)
        except Exception:
            logger.exception("Email failed for camper %s", camper.pk)
            failed += 1
        else:
            sent += 1
    return sent, failed
