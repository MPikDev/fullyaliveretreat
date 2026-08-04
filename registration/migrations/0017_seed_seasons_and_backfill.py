"""Seed the camp seasons and migrate existing campers onto them.

Every season previously existed only as a constant in ``settings.py`` and a
matching string in ``Camper.camp_filter``. This creates a real row per season
and points each camper at the right one, keeping ``camp_filter`` intact so any
historical report that matches on it still works.

It also cleans up two long-standing data problems:

* Merchandise columns stored the four-character strings ``'None'`` and
  ``'null'`` to mean "nothing ordered". Those become real NULLs, which is what
  made confirmation emails read "Forest Sweater: null".
* ``amount_due`` is backfilled for paid campers so the payment verification
  introduced alongside this migration has something to check against.
"""

from decimal import Decimal

from django.db import migrations

# The historical values from the old settings module. These are facts about
# records already in the database and must never change.
SEASONS = [
    # slug, name, legacy camp_filter key, theme, start (local), end (local)
    ("spring-2019", "Fully Alive Retreat 2019", "camp 2019", "summer", "2019-06-13", "2019-06-16"),
    ("spring-2020", "Fully Alive Retreat Spring 2020", "spring camp 2020", "summer", "2020-06-11", "2020-06-14"),
    ("fall-2020", "Fully Alive Retreat Fall 2020", "fall 2020 camp", "summer", "2020-09-17", "2020-09-20"),
    ("fall-2021", "Fully Alive Retreat Fall 2021", "fall 2021 camp", "summer", "2021-09-16", "2021-09-19"),
    ("summer-2022", "Fully Alive Retreat 2022", "summer 2022 camp", "summer", "2022-08-18", "2022-08-21"),
    ("summer-2023", "Fully Alive Retreat 2023", "summer 2023 camp", "summer", "2023-08-17", "2023-08-20"),
    ("summer-2024", "Fully Alive Retreat 2024", "summer 2024 camp", "summer", "2024-06-13", "2024-06-16"),
    ("summer-2025", "Fully Alive Retreat 2025", "summer 2025 camp", "summer", "2025-08-22", "2025-08-25"),
    ("winter-2026", "Fully Alive Retreat Winter 2026", "winter 2026 camp", "winter", "2026-01-02", "2026-01-05"),
    ("summer-2026", "Fully Alive Retreat 2026", "summer 2026 camp", "summer", "2026-08-21", "2026-08-24"),
]

ACTIVE_SLUG = "summer-2026"

# Values the old code used to mean "not set".
EMPTY_SENTINELS = {"None", "null", "none", "NULL", ""}


def seed_and_backfill(apps, schema_editor):
    import datetime

    from django.utils import timezone

    CampSeason = apps.get_model("registration", "CampSeason")
    Camper = apps.get_model("registration", "Camper")

    def local(date_string, hour=16):
        naive = datetime.datetime.strptime(date_string, "%Y-%m-%d").replace(hour=hour)
        return timezone.make_aware(naive)

    by_key = {}
    for slug, name, legacy_key, theme, starts, ends in SEASONS:
        season, _ = CampSeason.objects.update_or_create(
            legacy_filter_key=legacy_key,
            defaults={
                "slug": slug,
                "name": name,
                "theme": theme,
                "starts_at": local(starts, hour=16),
                "ends_at": local(ends, hour=12),
                "is_active": slug == ACTIVE_SLUG,
                # Past seasons are closed. The active one is opened deliberately
                # by staff rather than switched on by a migration.
                "registration_open": False,
                "capacity": 150,
                "base_price": Decimal("330.00"),
                "hoodie_price": Decimal("45.00"),
                "mug_price": Decimal("10.00"),
                "merch_enabled": slug == ACTIVE_SLUG,
                "min_age": 23,
                "max_age": 45,
                "venue_name": "Twin Rocks Camp",
                "venue_address": "18705 N Hwy 101, Rockaway Beach, OR 97136",
                "venue_url": "http://www.twinrocks.org",
            },
        )
        by_key[legacy_key] = season

    # The 2026 summer camp is the live one; carry over its known configuration.
    active = by_key.get("summer 2026 camp")
    if active:
        active.registration_opens_at = local("2026-02-01", hour=0)
        active.registration_closes_at = local("2026-08-25", hour=0)
        active.merch_deadline = local("2026-08-04", hour=0)
        active.registration_deadline_note = "August 16th"
        active.save()

    # Point every camper at its season.
    for legacy_key, season in by_key.items():
        Camper.objects.filter(camp_filter=legacy_key).update(season=season)

    # Campers whose camp_filter matched nothing keep camp_filter but get no
    # season; they remain reachable in the admin and are not silently reassigned.

    # "None"/"null" meant "nothing ordered". Store that as NULL.
    for field in ("tshirt_size", "swshirt_size", "region", "activity"):
        Camper.objects.filter(**{f"{field}__in": list(EMPTY_SENTINELS)}).update(**{field: None})

    # Give paid campers an amount_due so payment verification has a baseline.
    # Derived from what they ordered, using the historical prices.
    for season in by_key.values():
        campers = Camper.objects.filter(season=season, amount_due__isnull=True)
        for camper in campers.iterator():
            hoodies = sum(
                1 for value in (camper.tshirt_size, camper.swshirt_size) if value
            )
            total = season.base_price + (season.hoodie_price * hoodies)
            if camper.mug:
                total += season.mug_price
            camper.amount_due = total
            camper.save(update_fields=["amount_due"])


def unseed(apps, schema_editor):
    CampSeason = apps.get_model("registration", "CampSeason")
    Camper = apps.get_model("registration", "Camper")
    Camper.objects.update(season=None)
    CampSeason.objects.filter(legacy_filter_key__in=[s[2] for s in SEASONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0016_campseason_and_camper_rebuild"),
    ]

    operations = [
        migrations.RunPython(seed_and_backfill, unseed),
    ]
