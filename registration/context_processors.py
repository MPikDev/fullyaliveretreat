"""Template context available on every page.

Templates read season details and site links from here rather than hardcoding
them, so a new camp needs no template edits.
"""

from django.conf import settings

from registration.models import CampSeason


def site_context(request):
    return {
        "site_name": settings.SITE_NAME,
        "site_tagline": settings.SITE_TAGLINE,
        "instagram_url": settings.INSTAGRAM_URL,
        "telegram_url": settings.TELEGRAM_URL,
        "video_url": settings.VIDEO_URL,
        "contact_email": settings.CONTACT_EMAIL,
        "ga_measurement_id": settings.GA_MEASUREMENT_ID,
        "season": CampSeason.active(),
    }
