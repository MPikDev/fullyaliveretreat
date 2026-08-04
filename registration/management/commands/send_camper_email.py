"""Send a templated email to a selected group of campers.

Replaces five near-identical one-off scripts (``paided_email``, ``pic_email``,
``survey_email``, ``email_unregs`` and friends), each of which hardcoded both
its message text and its recipient selection as a magic primary-key threshold
such as ``pk__gt=193``.

Recipients are chosen by season and audience; the body comes from a template.
Nothing is sent without ``--confirm``, so the default behaviour is a dry run.

    python manage.py send_camper_email --season summer-2026 --audience unpaid \\
        --template email/reminder.html --subject "Don't forget to pay" --confirm
"""

from django.core.management.base import BaseCommand, CommandError

from registration.emails import send_bulk_email
from registration.models import Camper, CampSeason

AUDIENCES = {
    "paid": lambda qs: qs.filter(paid=True, status=Camper.Status.REGISTERED),
    "unpaid": lambda qs: qs.filter(paid=False, status=Camper.Status.REGISTERED),
    "all": lambda qs: qs.filter(status=Camper.Status.REGISTERED),
    "flagged": lambda qs: qs.filter(payment_flagged=True),
}


class Command(BaseCommand):
    help = "Send a templated email to campers in one season."

    def add_arguments(self, parser):
        parser.add_argument(
            "--season", required=True,
            help="Season slug, for example 'summer-2026'.",
        )
        parser.add_argument(
            "--audience", required=True, choices=sorted(AUDIENCES),
            help="Which campers to send to.",
        )
        parser.add_argument(
            "--template", required=True,
            help="Template path, for example 'email/reminder.html'.",
        )
        parser.add_argument("--subject", required=True)
        parser.add_argument(
            "--exclude", default="",
            help="Comma-separated camper ids to skip.",
        )
        parser.add_argument(
            "--unique-emails", action="store_true",
            help="Send at most one message per email address.",
        )
        parser.add_argument(
            "--confirm", action="store_true",
            help="Actually send. Without this the command only reports.",
        )

    def handle(self, *args, **options):
        try:
            season = CampSeason.objects.get(slug=options["season"])
        except CampSeason.DoesNotExist:
            available = ", ".join(CampSeason.objects.values_list("slug", flat=True))
            raise CommandError(
                f"No season with slug {options['season']!r}. Available: {available}"
            )

        campers = AUDIENCES[options["audience"]](season.campers.all()).order_by("pk")

        excluded = {
            int(value) for value in options["exclude"].split(",") if value.strip().isdigit()
        }
        if excluded:
            campers = campers.exclude(pk__in=excluded)

        recipients = list(campers)
        if options["unique_emails"]:
            seen, unique = set(), []
            for camper in recipients:
                key = camper.email.lower()
                if key not in seen:
                    seen.add(key)
                    unique.append(camper)
            recipients = unique

        if not recipients:
            self.stdout.write(self.style.WARNING("No campers matched. Nothing to do."))
            return

        dry_run = not options["confirm"]
        self.stdout.write(
            f"{'[dry run] ' if dry_run else ''}"
            f"{len(recipients)} recipient(s) — {season.name} / {options['audience']}"
        )

        sent, failed = send_bulk_email(
            recipients,
            subject=options["subject"],
            template=options["template"],
            dry_run=dry_run,
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {sent} message(s) would be sent. "
                    f"Re-run with --confirm to send."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Sent {sent}, failed {failed}."))
