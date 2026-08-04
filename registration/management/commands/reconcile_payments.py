"""Re-check recorded PayPal notifications against camper records.

The IPN handler marks campers paid as notifications arrive. This is the manual
fallback for a notification that was missed or arrived out of order. It applies
the same verification rules, so it can never mark someone paid that the live
handler would have rejected.

    python manage.py reconcile_payments --season summer-2026
"""

from django.core.management.base import BaseCommand, CommandError

from registration.models import CampSeason
from registration.services import reconcile_season


class Command(BaseCommand):
    help = "Re-check PayPal payments for a season and update camper records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--season",
            help="Season slug. Defaults to the active season.",
        )
        parser.add_argument(
            "--no-email", action="store_true",
            help="Update payment status without sending confirmation emails.",
        )

    def handle(self, *args, **options):
        if options["season"]:
            try:
                season = CampSeason.objects.get(slug=options["season"])
            except CampSeason.DoesNotExist:
                available = ", ".join(CampSeason.objects.values_list("slug", flat=True))
                raise CommandError(
                    f"No season with slug {options['season']!r}. Available: {available}"
                )
        else:
            season = CampSeason.active()
            if season is None:
                raise CommandError("No active season. Pass --season explicitly.")

        self.stdout.write(f"Reconciling {season.name}...")
        updated, flagged = reconcile_season(season, send_email=not options["no_email"])

        self.stdout.write(self.style.SUCCESS(f"{updated} camper record(s) updated."))
        if flagged:
            self.stdout.write(
                self.style.ERROR(
                    f"{flagged} payment(s) flagged for review — see the staff dashboard."
                )
            )
