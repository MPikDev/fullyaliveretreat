"""Data model for camp registration.

``CampSeason`` holds everything that used to be a hardcoded per-season constant
spread across ``settings.py``, ``views.py``, ``urls.py`` and the templates.
Opening a new camp is now a matter of adding a row in the admin.

``Camper`` is one registration for one season.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

SIZE_CHOICES = (
    ("XS", "Extra Small"),
    ("S", "Small"),
    ("M", "Medium"),
    ("L", "Large"),
    ("XL", "Extra Large"),
    ("XXL", "2X Large"),
    ("3XL", "3X Large"),
    ("4XL", "4X Large"),
    ("5XL", "5X Large"),
)

PHONE_VALIDATOR = RegexValidator(
    regex=r"^[0-9+().\-\s]{7,20}$",
    message="Enter a phone number, for example 509-555-0123.",
)


class CampSeason(models.Model):
    """One camp. Everything season-specific lives here rather than in code."""

    class Theme(models.TextChoices):
        SUMMER = "summer", "Summer / coast"
        WINTER = "winter", "Winter"

    slug = models.SlugField(
        max_length=40,
        unique=True,
        help_text="URL key, for example 'summer-2026'.",
    )
    name = models.CharField(
        max_length=120,
        help_text="Display name, for example 'Fully Alive Retreat 2026'.",
    )
    legacy_filter_key = models.CharField(
        max_length=48,
        unique=True,
        help_text=(
            "The value stored in Camper.camp_filter for this season. Do not "
            "change this on an existing season; historical records match on it."
        ),
    )

    is_active = models.BooleanField(
        default=False,
        help_text="The season the public site shows. Exactly one may be active.",
    )
    registration_open = models.BooleanField(
        default=False,
        help_text="Uncheck to close registration immediately.",
    )
    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)

    capacity = models.PositiveIntegerField(default=150)
    base_price = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("330.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    merch_enabled = models.BooleanField(default=True)
    merch_deadline = models.DateTimeField(
        null=True, blank=True,
        help_text="After this moment merchandise can no longer be ordered.",
    )
    hoodie_price = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("45.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    mug_enabled = models.BooleanField(default=False)
    mug_price = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("10.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    venue_name = models.CharField(max_length=120, blank=True, default="Twin Rocks Camp")
    venue_address = models.CharField(
        max_length=200, blank=True, default="18705 N Hwy 101, Rockaway Beach, OR 97136"
    )
    venue_url = models.URLField(blank=True, default="http://www.twinrocks.org")

    min_age = models.PositiveSmallIntegerField(
        default=23, help_text="Youngest age admitted, measured on the first day of camp."
    )
    max_age = models.PositiveSmallIntegerField(
        default=45, help_text="Campers at or above this age are directed to the age notice."
    )

    paypal_item_name = models.CharField(
        max_length=127,
        blank=True,
        help_text="Line item shown on the PayPal receipt. Defaults to the season name.",
    )
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.SUMMER)

    registration_deadline_note = models.CharField(
        max_length=120, blank=True,
        help_text="Free text shown on the info page, for example 'August 16th'.",
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-starts_at", "-id")
        verbose_name = "camp season"
        verbose_name_plural = "camp seasons"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Exactly one active season. Enforced after save so the newly activated
        # row wins rather than being cleared along with the others.
        if self.is_active:
            CampSeason.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    @classmethod
    def active(cls):
        """The season the public site is currently showing, or None."""
        return cls.objects.filter(is_active=True).first()

    @property
    def item_name(self):
        return self.paypal_item_name or f"Registration for {self.name}"

    @property
    def merch_closed(self):
        if not self.merch_enabled:
            return True
        if self.merch_deadline is None:
            return False
        return timezone.now() > self.merch_deadline

    @property
    def paid_count(self):
        return self.campers.filter(paid=True).count()

    @property
    def is_full(self):
        return self.paid_count >= self.capacity

    @property
    def spots_remaining(self):
        return max(self.capacity - self.paid_count, 0)

    @property
    def accepting_registrations(self):
        """Whether the registration form should accept a new submission."""
        if not self.registration_open or self.is_full:
            return False
        now = timezone.now()
        if self.registration_opens_at and now < self.registration_opens_at:
            return False
        if self.registration_closes_at and now > self.registration_closes_at:
            return False
        return True

    def price_for(self, *, hoodie_count=0, mug=False):
        """Authoritative server-side price. Never trust a client-submitted amount."""
        total = self.base_price + (self.hoodie_price * hoodie_count)
        if mug:
            total += self.mug_price
        return total


class Camper(models.Model):
    """One person's registration for one season."""

    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        REJECTED_MARRIED = "rejected_married", "Not eligible (married / not a church member)"
        REJECTED_AGE = "rejected_age", "Not eligible (age)"

    season = models.ForeignKey(
        CampSeason,
        on_delete=models.PROTECT,
        related_name="campers",
        null=True,
        blank=True,
    )
    # Retained so historical records and any external report keep resolving.
    # New rows get it from season.legacy_filter_key.
    camp_filter = models.CharField(max_length=48, default="not caught", editable=False)

    first_name = models.CharField(max_length=48)
    last_name = models.CharField(max_length=48)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=1,
        choices=(("m", "Male"), ("f", "Female")),
        null=True,
        blank=True,
        default=None,
        help_text="Blank on legacy campers registered before this field existed.",
    )
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=15, validators=[PHONE_VALIDATOR])
    city = models.CharField(max_length=48)
    state = models.CharField(max_length=48)
    med_notes = models.CharField(
        max_length=400,
        blank=True,
        default="",
        verbose_name="Medical notes",
        help_text="Allergies, conditions or medication we should know about.",
    )
    church = models.CharField(max_length=100)
    pastor = models.CharField(max_length=100)
    pastor_number = models.CharField(
        max_length=15, null=True, blank=True, default=None, validators=[PHONE_VALIDATOR]
    )
    church_member = models.BooleanField(default=False)
    not_married = models.BooleanField(default=False)

    tshirt_size = models.CharField(
        max_length=4, choices=SIZE_CHOICES, null=True, blank=True, default=None,
        verbose_name="Sage hoodie size", help_text="Blank means none ordered.",
    )
    swshirt_size = models.CharField(
        max_length=4, choices=SIZE_CHOICES, null=True, blank=True, default=None,
        verbose_name="Forest hoodie size", help_text="Blank means none ordered.",
    )
    mug = models.BooleanField(default=False)

    # Legacy winter-camp fields, kept so historical rows are not lossy.
    region = models.CharField(
        max_length=8,
        choices=(("oregon", "Oregon"), ("seattle", "Seattle"), ("spokane", "Spokane")),
        null=True, blank=True, default=None,
    )
    activity = models.CharField(
        max_length=4,
        choices=(("ski", "Ski / snowboard"), ("tub", "Tubing"), ("stay", "Stay at the cabin")),
        null=True, blank=True, default=None,
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REGISTERED, db_index=True
    )
    # The price this camper owes, computed on the server at registration time.
    # Payment verification checks the PayPal amount against this value.
    amount_due = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    amount_paid = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Gross amount PayPal reported. Set by the IPN handler.",
    )
    paid = models.BooleanField(default=False)
    payment_flagged = models.BooleanField(
        default=False,
        help_text="A payment arrived that did not match the expected amount or receiver.",
    )
    payment_note = models.CharField(max_length=255, blank=True, default="")
    email_sent = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ("pk",)
        indexes = [
            models.Index(fields=["season", "paid"]),
            models.Index(fields=["camp_filter", "paid"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        state = "paid" if self.paid else "unpaid"
        return f"{self.first_name} {self.last_name} ({state})"

    def save(self, *args, **kwargs):
        # Keep the legacy key in step so old reports keep working.
        if self.season_id and self.camp_filter in ("", "not caught"):
            self.camp_filter = self.season.legacy_filter_key
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def ordered_merch(self):
        """The merchandise lines this camper actually ordered."""
        items = []
        if self.swshirt_size:
            items.append(("Forest hoodie", self.swshirt_size))
        if self.tshirt_size:
            items.append(("Sage hoodie", self.tshirt_size))
        if self.mug:
            items.append(("Mug", ""))
        return items

    def age_on(self, when):
        """Age in whole years on a given date, month and day included."""
        if hasattr(when, "date"):
            when = when.date()
        return (
            when.year
            - self.date_of_birth.year
            - ((when.month, when.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )
