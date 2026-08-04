"""Tests for registration, validation and payment verification.

Run with:  python manage.py test --settings=personal_code.settings_test

The previous suite had seven tests using bare ``assert`` (silently skipped
under ``python -O``) with dates hardcoded to specific years, so the age tests
would start failing on their own in 2027. Dates here are derived from a season
the test itself creates, so the suite does not depend on the calendar.
"""

import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.ipn.signals import valid_ipn_received

from registration.forms import CamperRegistrationForm
from registration.models import Camper, CampSeason
from registration.services import reconcile_season

RECEIVER = "nwasbc.youth@gmail.com"


def make_season(**overrides):
    """An open season starting a year from now."""
    starts = timezone.now() + datetime.timedelta(days=365)
    defaults = {
        "slug": "test-season",
        "name": "Test Retreat",
        "legacy_filter_key": "test camp",
        "is_active": True,
        "registration_open": True,
        "capacity": 150,
        "base_price": Decimal("330.00"),
        "hoodie_price": Decimal("45.00"),
        "mug_price": Decimal("10.00"),
        "merch_enabled": True,
        "merch_deadline": starts - datetime.timedelta(days=17),
        "starts_at": starts,
        "ends_at": starts + datetime.timedelta(days=3),
        "min_age": 23,
        "max_age": 45,
    }
    defaults.update(overrides)
    return CampSeason.objects.create(**defaults)


def form_data(season, **overrides):
    """A valid registration payload for a camper aged 30 at camp."""
    dob = (season.starts_at - datetime.timedelta(days=365 * 30 + 8)).date()
    data = {
        "first_name": "Anna",
        "last_name": "Ivanova",
        "date_of_birth": dob.isoformat(),
        "gender": "f",
        "email": "anna@example.com",
        "email_confirm": "anna@example.com",
        "phone": "509-555-0123",
        "city": "Spokane",
        "state": "Washington",
        "church": "ЦЕРКОВЬ 'НА ГОРЕ' (SPOKANE, WA)",
        "pastor": "Pastor Bob",
        "pastor_number": "509-555-0199",
        "church_member": "true",
        "not_married": "true",
        "med_notes": "",
        "tshirt_size": "",
        "swshirt_size": "",
    }
    data.update(overrides)
    return data


class RegistrationFormTests(TestCase):
    def setUp(self):
        self.season = make_season()

    def test_valid_registration_is_accepted(self):
        form = CamperRegistrationForm(form_data(self.season), season=self.season)
        self.assertTrue(form.is_valid(), form.errors)
        camper = form.save()
        self.assertEqual(camper.status, Camper.Status.REGISTERED)
        self.assertEqual(camper.season, self.season)
        self.assertEqual(camper.camp_filter, self.season.legacy_filter_key)

    def test_missing_required_field_is_rejected(self):
        form = CamperRegistrationForm(
            form_data(self.season, pastor_number=""), season=self.season
        )
        self.assertFalse(form.is_valid())
        self.assertIn("pastor_number", form.errors)

    def test_mismatched_emails_are_rejected(self):
        form = CamperRegistrationForm(
            form_data(self.season, email_confirm="other@example.com"), season=self.season
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email_confirm", form.errors)

    def test_malformed_email_is_rejected(self):
        """The email column used to be a CharField, so anything was accepted."""
        form = CamperRegistrationForm(
            form_data(self.season, email="not-an-email", email_confirm="not-an-email"),
            season=self.season,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_size_choice_is_rejected(self):
        """Sizes came straight from POST and were never checked against choices."""
        form = CamperRegistrationForm(
            form_data(self.season, swshirt_size="HUGE"), season=self.season
        )
        self.assertFalse(form.is_valid())
        self.assertIn("swshirt_size", form.errors)

    def test_not_ordering_merch_stores_null_not_the_string_none(self):
        form = CamperRegistrationForm(form_data(self.season), season=self.season)
        self.assertTrue(form.is_valid(), form.errors)
        camper = form.save()
        self.assertIsNone(camper.tshirt_size)
        self.assertIsNone(camper.swshirt_size)
        self.assertEqual(camper.ordered_merch, [])


class AgeBoundaryTests(TestCase):
    """Age is measured on the first day of camp, month and day included.

    The old code computed ``today.year - dob.year``, which was wrong by up to a
    year on either side of both boundaries.
    """

    def setUp(self):
        self.season = make_season()

    def _dob_for_age_at_camp(self, age, days_offset=0):
        camp_day = self.season.starts_at.date()
        try:
            birthday = camp_day.replace(year=camp_day.year - age)
        except ValueError:  # 29 February
            birthday = camp_day.replace(year=camp_day.year - age, day=28)
        return birthday + datetime.timedelta(days=days_offset)

    def test_exactly_min_age_on_first_day_is_accepted(self):
        dob = self._dob_for_age_at_camp(23)
        form = CamperRegistrationForm(
            form_data(self.season, date_of_birth=dob.isoformat()), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_one_day_short_of_min_age_is_rejected(self):
        """Turns 23 the day after camp starts — the year-only maths admitted this."""
        dob = self._dob_for_age_at_camp(23, days_offset=1)
        form = CamperRegistrationForm(
            form_data(self.season, date_of_birth=dob.isoformat()), season=self.season
        )
        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)

    def test_one_day_short_of_max_age_is_not_flagged_as_too_old(self):
        dob = self._dob_for_age_at_camp(45, days_offset=1)
        form = CamperRegistrationForm(
            form_data(self.season, date_of_birth=dob.isoformat()), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.is_over_age())

    def test_exactly_max_age_on_first_day_is_flagged(self):
        dob = self._dob_for_age_at_camp(45)
        form = CamperRegistrationForm(
            form_data(self.season, date_of_birth=dob.isoformat()), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.is_over_age())
        self.assertEqual(form.save().status, Camper.Status.REJECTED_AGE)

    def test_future_date_of_birth_is_rejected(self):
        future = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
        form = CamperRegistrationForm(
            form_data(self.season, date_of_birth=future), season=self.season
        )
        self.assertFalse(form.is_valid())


class EligibilityTests(TestCase):
    def setUp(self):
        self.season = make_season()

    def test_married_camper_is_recorded_but_not_accepted(self):
        form = CamperRegistrationForm(
            form_data(self.season, not_married="false"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        camper = form.save()
        self.assertEqual(camper.status, Camper.Status.REJECTED_MARRIED)

    def test_non_church_member_is_recorded_but_not_accepted(self):
        form = CamperRegistrationForm(
            form_data(self.season, church_member="false"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().status, Camper.Status.REJECTED_MARRIED)

    def test_ineligible_campers_are_excluded_from_the_unpaid_list(self):
        form = CamperRegistrationForm(
            form_data(self.season, not_married="false"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        unpaid = self.season.campers.filter(paid=False, status=Camper.Status.REGISTERED)
        self.assertEqual(unpaid.count(), 0)


class CapacityAndClosureTests(TestCase):
    """Capacity is enforced in the form, so a direct POST cannot bypass it."""

    def _fill_to(self, season, count):
        for index in range(count):
            Camper.objects.create(
                season=season, camp_filter=season.legacy_filter_key,
                first_name="C", last_name=str(index),
                date_of_birth=datetime.date(1995, 1, 1),
                email=f"c{index}@example.com", phone="509-555-0000",
                city="X", state="Washington", church="X", pastor="X",
                church_member=True, not_married=True,
                paid=True, amount_due=Decimal("330.00"),
            )

    def test_registration_allowed_one_below_capacity(self):
        season = make_season(capacity=3)
        self._fill_to(season, 2)
        form = CamperRegistrationForm(form_data(season), season=season)
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_rejected_at_capacity(self):
        """The old check used ``>`` and only ran when the open flag was set."""
        season = make_season(capacity=3)
        self._fill_to(season, 3)
        form = CamperRegistrationForm(form_data(season), season=season)
        self.assertFalse(form.is_valid())

    def test_direct_post_cannot_bypass_capacity(self):
        season = make_season(capacity=1)
        self._fill_to(season, 1)
        response = self.client.post(reverse("register"), form_data(season))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(season.campers.filter(paid=False).count(), 0)

    def test_direct_post_cannot_bypass_closed_registration(self):
        season = make_season(registration_open=False)
        self.client.post(reverse("register"), form_data(season))
        self.assertEqual(season.campers.count(), 0)

    def test_closing_registration_does_not_disable_the_capacity_check(self):
        """Closing used to *disable* the capacity gate rather than close the form."""
        season = make_season(registration_open=False, capacity=1)
        self._fill_to(season, 5)
        form = CamperRegistrationForm(form_data(season), season=season)
        self.assertFalse(form.is_valid())


class MerchDeadlineTests(TestCase):
    def test_merch_offered_before_the_deadline(self):
        season = make_season()
        form = CamperRegistrationForm(season=season)
        self.assertIn("swshirt_size", form.fields)

    def test_merch_fields_removed_after_the_deadline(self):
        season = make_season(merch_deadline=timezone.now() - datetime.timedelta(days=1))
        form = CamperRegistrationForm(season=season)
        self.assertNotIn("swshirt_size", form.fields)
        self.assertNotIn("tshirt_size", form.fields)

    def test_post_after_the_deadline_cannot_order_merch(self):
        season = make_season(merch_deadline=timezone.now() - datetime.timedelta(days=1))
        form = CamperRegistrationForm(
            form_data(season, swshirt_size="L", tshirt_size="M"), season=season
        )
        self.assertTrue(form.is_valid(), form.errors)
        camper = form.save()
        self.assertIsNone(camper.swshirt_size)
        self.assertEqual(camper.amount_due, season.base_price)

    def test_registration_page_renders_after_the_deadline(self):
        """The merch deadline used to break the page's JavaScript entirely."""
        make_season(merch_deadline=timezone.now() - datetime.timedelta(days=1))
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)


class PricingTests(TestCase):
    def setUp(self):
        self.season = make_season()

    def test_base_price_only(self):
        form = CamperRegistrationForm(form_data(self.season), season=self.season)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().amount_due, Decimal("330.00"))

    def test_one_hoodie(self):
        form = CamperRegistrationForm(
            form_data(self.season, swshirt_size="L"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().amount_due, Decimal("375.00"))

    def test_two_hoodies(self):
        form = CamperRegistrationForm(
            form_data(self.season, swshirt_size="L", tshirt_size="M"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().amount_due, Decimal("420.00"))

    def test_paypal_form_uses_the_server_side_amount(self):
        form = CamperRegistrationForm(
            form_data(self.season, swshirt_size="L"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        camper = form.save()
        response = self.client.get(reverse("pay_now", args=[camper.pk]))
        self.assertContains(response, 'value="375.00"')


class PaymentVerificationTests(TestCase):
    """The central security regression tests.

    Previously any Completed IPN carrying a camper's invoice number set
    ``paid = True``; the amount was never compared against anything. Because the
    amount was submitted from a form rendered in the browser, a camper could
    edit it, pay a token sum, and be recorded as fully paid.
    """

    def setUp(self):
        self.season = make_season()
        form = CamperRegistrationForm(
            form_data(self.season, swshirt_size="L"), season=self.season
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.camper = form.save()  # amount_due == 375.00

    def fire_ipn(self, **overrides):
        fields = {
            "payment_status": "Completed",
            "invoice": str(self.camper.pk),
            "receiver_email": RECEIVER,
            "mc_currency": "USD",
            "mc_gross": Decimal("375.00"),
            "txn_id": overrides.pop("txn_id", "TXN-TEST-1"),
        }
        fields.update(overrides)
        ipn = PayPalIPN.objects.create(**fields)
        valid_ipn_received.send(sender=ipn)
        self.camper.refresh_from_db()
        return ipn

    def test_correct_payment_marks_the_camper_paid(self):
        self.fire_ipn()
        self.assertTrue(self.camper.paid)
        self.assertEqual(self.camper.amount_paid, Decimal("375.00"))
        self.assertFalse(self.camper.payment_flagged)

    def test_underpayment_does_not_mark_the_camper_paid(self):
        self.fire_ipn(mc_gross=Decimal("1.00"))
        self.assertFalse(self.camper.paid)
        self.assertTrue(self.camper.payment_flagged)
        self.assertIn("Underpayment", self.camper.payment_note)

    def test_payment_missing_the_hoodie_amount_is_rejected(self):
        """Paying only the base price when merch was ordered is an underpayment."""
        self.fire_ipn(mc_gross=Decimal("330.00"))
        self.assertFalse(self.camper.paid)
        self.assertTrue(self.camper.payment_flagged)

    def test_overpayment_is_accepted(self):
        self.fire_ipn(mc_gross=Decimal("400.00"))
        self.assertTrue(self.camper.paid)

    def test_payment_to_the_wrong_receiver_is_rejected(self):
        self.fire_ipn(receiver_email="attacker@example.com")
        self.assertFalse(self.camper.paid)
        self.assertIn("Receiver mismatch", self.camper.payment_note)

    def test_payment_in_the_wrong_currency_is_rejected(self):
        self.fire_ipn(mc_currency="EUR")
        self.assertFalse(self.camper.paid)
        self.assertIn("Currency mismatch", self.camper.payment_note)

    def test_unknown_invoice_changes_nothing(self):
        self.fire_ipn(invoice="999999")
        self.assertFalse(self.camper.paid)
        self.assertFalse(self.camper.payment_flagged)

    def test_non_completed_status_changes_nothing(self):
        self.fire_ipn(payment_status="Pending")
        self.assertFalse(self.camper.paid)

    def test_refund_reverses_a_payment(self):
        self.fire_ipn()
        self.assertTrue(self.camper.paid)
        self.fire_ipn(payment_status="Refunded", txn_id="TXN-TEST-2")
        self.assertFalse(self.camper.paid)

    def test_legacy_float_invoice_still_resolves(self):
        """Historical invoices were sometimes recorded as '88.0'."""
        self.fire_ipn(invoice=f"{self.camper.pk}.0")
        self.assertTrue(self.camper.paid)

    def test_return_url_does_not_change_payment_state(self):
        """/return used to run a full reconciliation and send mail, unauthenticated."""
        response = self.client.get(reverse("your-return-view"))
        self.assertEqual(response.status_code, 200)
        self.camper.refresh_from_db()
        self.assertFalse(self.camper.paid)


class ReconciliationTests(TestCase):
    def setUp(self):
        self.season = make_season(
            registration_opens_at=timezone.now() - datetime.timedelta(days=30),
            registration_closes_at=timezone.now() + datetime.timedelta(days=30),
        )
        form = CamperRegistrationForm(form_data(self.season), season=self.season)
        self.assertTrue(form.is_valid(), form.errors)
        self.camper = form.save()  # amount_due == 330.00

    def test_reconcile_marks_a_correctly_paid_camper(self):
        PayPalIPN.objects.create(
            payment_status="Completed", invoice=str(self.camper.pk),
            receiver_email=RECEIVER, mc_currency="USD",
            mc_gross=Decimal("330.00"), txn_id="R1", flag=False,
        )
        _, flagged = reconcile_season(self.season, send_email=False)
        self.camper.refresh_from_db()
        self.assertTrue(self.camper.paid)
        self.assertEqual(flagged, 0)

    def test_reconcile_flags_rather_than_accepting_an_underpayment(self):
        PayPalIPN.objects.create(
            payment_status="Completed", invoice=str(self.camper.pk),
            receiver_email=RECEIVER, mc_currency="USD",
            mc_gross=Decimal("5.00"), txn_id="R2", flag=False,
        )
        _, flagged = reconcile_season(self.season, send_email=False)
        self.camper.refresh_from_db()
        self.assertFalse(self.camper.paid)
        self.assertEqual(flagged, 1)


class StaffAccessTests(TestCase):
    def setUp(self):
        self.season = make_season()
        self.user = User.objects.create_user("staff", "s@example.com", "pw-for-tests-123")

    def test_camper_info_requires_authentication(self):
        response = self.client.get(reverse("camper_info"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])

    def test_csv_export_requires_authentication(self):
        response = self.client.get(reverse("camper_export", args=[self.season.slug]))
        self.assertEqual(response.status_code, 302)

    def test_camper_info_is_reachable_when_signed_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("camper_info"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")
        self.assertIn("no-store", response["Cache-Control"])

    def test_registration_toggle_rejects_get(self):
        """Open/close used to be a plain GET, so it was CSRF-triggerable."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("set_registration_status"))
        self.assertEqual(response.status_code, 405)

    def test_registration_toggle_persists_to_the_database(self):
        """The old flag lived on the settings module, per worker process."""
        self.client.force_login(self.user)
        self.client.post(reverse("set_registration_status"), {"action": "close"})
        self.season.refresh_from_db()
        self.assertFalse(self.season.registration_open)

    def test_registration_toggle_requires_authentication(self):
        response = self.client.post(reverse("set_registration_status"), {"action": "open"})
        self.assertEqual(response.status_code, 302)

    def test_reconcile_endpoint_rejects_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("reconcile_payments")).status_code, 405)


class SeasonModelTests(TestCase):
    def test_only_one_season_can_be_active(self):
        first = make_season(slug="a", legacy_filter_key="a camp")
        second = make_season(slug="b", legacy_filter_key="b camp")
        first.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)
        self.assertEqual(CampSeason.objects.filter(is_active=True).count(), 1)

    def test_price_for_computes_merch_totals(self):
        season = make_season()
        self.assertEqual(season.price_for(), Decimal("330.00"))
        self.assertEqual(season.price_for(hoodie_count=2), Decimal("420.00"))
        self.assertEqual(season.price_for(hoodie_count=1, mug=True), Decimal("385.00"))


class PublicPageTests(TestCase):
    def setUp(self):
        make_season()

    def test_every_public_page_renders(self):
        for name in [
            "home", "info", "schedule", "fellowship", "photos",
            "register", "paypal_issues", "your-return-view", "your-cancel-view",
            "full", "login", "robots",
        ]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_robots_disallows_the_staff_area(self):
        body = self.client.get(reverse("robots")).content.decode()
        self.assertIn("Disallow: /camper-info/", body)

    def test_legacy_urls_redirect(self):
        for old, new in [("/register/", "/registration/"), ("/camper_info/", "/camper-info/")]:
            with self.subTest(url=old):
                response = self.client.get(old)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response["Location"], new)

    def test_home_page_includes_event_structured_data(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "application/ld+json")
        self.assertContains(response, '"@type": "Event"')
