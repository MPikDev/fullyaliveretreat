"""Registration form.

Replaces roughly 150 lines of hand-rolled validation that read straight from
``request.POST``. Everything is validated here, which means a direct POST that
skips the rendered page is subject to exactly the same rules as one that does
not: choice values are checked against the model, capacity and the merchandise
deadline are enforced server-side, and the age test uses the full date of birth
rather than the year alone.
"""

import copy

from django import forms
from django.utils import timezone

from registration.models import SIZE_CHOICES, Camper

STATE_CHOICES = [
    ("", "Select a state"),
    ("Washington", "Washington"),
    ("Oregon", "Oregon"),
    ("Idaho", "Idaho"),
    ("California", "California"),
    ("Montana", "Montana"),
    ("Alaska", "Alaska"),
    ("Other", "Other"),
]

SIZE_FIELD_CHOICES = [("", "Not ordering")] + list(SIZE_CHOICES)


class CamperRegistrationForm(forms.ModelForm):
    """Validates one camper's registration against a given season."""

    email_confirm = forms.EmailField(
        label="Confirm email",
        max_length=100,
        error_messages={"required": "Please re-enter your email address."},
    )
    church_member = forms.TypedChoiceField(
        label="Are you a member of a church?",
        choices=(("true", "Yes"), ("false", "No")),
        coerce=lambda value: value == "true",
        widget=forms.RadioSelect,
        empty_value=None,
        error_messages={"required": "Please tell us whether you are a church member."},
    )
    not_married = forms.TypedChoiceField(
        label="Have you ever been married?",
        # The stored field is "not_married", so the answers are inverted here.
        choices=(("false", "Yes"), ("true", "No")),
        coerce=lambda value: value == "true",
        widget=forms.RadioSelect,
        empty_value=None,
        error_messages={"required": "Please answer the marital status question."},
    )

    class Meta:
        model = Camper
        fields = [
            "first_name", "last_name", "date_of_birth", "gender",
            "email", "phone", "city", "state",
            "church", "pastor", "pastor_number",
            "church_member", "not_married",
            "med_notes", "tshirt_size", "swshirt_size",
        ]
        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "date_of_birth": "Date of birth",
            "gender": "Gender",
            "email": "Email",
            "phone": "Phone number",
            "city": "City",
            "state": "State",
            "church": "Church",
            "pastor": "Pastor's name",
            "pastor_number": "Pastor's phone number",
            "med_notes": "Medical notes",
            "tshirt_size": "Sage hoodie",
            "swshirt_size": "Forest hoodie",
        }
        help_texts = {
            "med_notes": "Allergies, conditions or medication we should know about. Optional.",
        }
        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "autocomplete": "bday"}, format="%Y-%m-%d"
            ),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(
                attrs={"type": "tel", "autocomplete": "tel", "placeholder": "509-555-0123"}
            ),
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "pastor_number": forms.TextInput(attrs={"type": "tel", "placeholder": "509-555-0123"}),
            "med_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, season=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season

        self.fields["state"] = forms.ChoiceField(
            label="State", choices=STATE_CHOICES,
            error_messages={"required": "Please select your state."},
        )
        self.fields["gender"].required = True
        self.fields["gender"].choices = [("", "Select")] + list(
            Camper._meta.get_field("gender").choices
        )
        # The model's help text explains the blank value to admins; it means
        # nothing to a camper filling in the form.
        self.fields["gender"].help_text = ""
        self.fields["med_notes"].required = False
        self.fields["pastor_number"].required = True

        # Merchandise is optional, and disappears entirely once the deadline
        # passes or the season has it turned off.
        for name in ("tshirt_size", "swshirt_size"):
            self.fields[name].required = False
            self.fields[name].choices = SIZE_FIELD_CHOICES
            # The "Not ordering" option already says this.
            self.fields[name].help_text = ""

        if season is not None and season.merch_closed:
            merch_fields = ("tshirt_size", "swshirt_size")
            for name in merch_fields:
                del self.fields[name]
            # ModelForm builds the instance from Meta.fields, so those entries
            # have to go too. Copy the options object first — it lives on the
            # class and is shared by every other instance of this form.
            self._meta = copy.copy(self._meta)
            self._meta.fields = [
                name for name in self._meta.fields if name not in merch_fields
            ]

        if season is not None:
            dob = self.fields["date_of_birth"]
            reference = (season.starts_at or timezone.now()).date()
            dob.widget.attrs["max"] = reference.replace(year=reference.year - season.min_age).isoformat()
            dob.widget.attrs["min"] = "1930-01-01"

        # Give every visible control the shared styling hook.
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.RadioSelect, forms.CheckboxInput)):
                continue
            css = "form-control"
            if isinstance(widget, forms.Select):
                css = "form-select"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()

    # -- field-level validation ---------------------------------------------

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_email_confirm(self):
        return self.cleaned_data["email_confirm"].strip().lower()

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        today = timezone.localdate()
        if dob > today:
            raise forms.ValidationError("That date is in the future.")
        if dob.year < 1900:
            raise forms.ValidationError("Please check the year of birth.")
        return dob

    # -- cross-field validation ---------------------------------------------

    def clean(self):
        cleaned = super().clean()
        season = self.season

        email = cleaned.get("email")
        email_confirm = cleaned.get("email_confirm")
        if email and email_confirm and email != email_confirm:
            self.add_error("email_confirm", "The two email addresses do not match.")

        if season is None:
            raise forms.ValidationError(
                "Registration is not open at the moment. Please check back soon."
            )

        # Capacity and the open/closed state are checked here rather than in the
        # view so a direct POST cannot bypass them.
        if not season.registration_open:
            raise forms.ValidationError("Registration is closed.")
        if season.is_full:
            raise forms.ValidationError("Camp is full.")

        now = timezone.now()
        if season.registration_opens_at and now < season.registration_opens_at:
            raise forms.ValidationError("Registration has not opened yet.")
        if season.registration_closes_at and now > season.registration_closes_at:
            raise forms.ValidationError("Registration has closed for this camp.")

        # Merchandise cannot be ordered after the deadline, even by a POST that
        # supplies the fields directly.
        if season.merch_closed:
            cleaned["tshirt_size"] = None
            cleaned["swshirt_size"] = None

        dob = cleaned.get("date_of_birth")
        if dob and season.starts_at:
            age = self._age_on(dob, season.starts_at.date())
            if age < season.min_age:
                self.add_error(
                    "date_of_birth",
                    f"Campers must be at least {season.min_age} by the first day of camp.",
                )

        return cleaned

    @staticmethod
    def _age_on(dob, when):
        """Whole years old on a date, counting month and day."""
        return when.year - dob.year - ((when.month, when.day) < (dob.month, dob.day))

    # -- outcome helpers -----------------------------------------------------

    def is_over_age(self):
        """Whether the camper is at or above the season's upper age limit.

        Not a validation error: these registrations are still recorded, and the
        camper is shown the age notice.
        """
        dob = self.cleaned_data.get("date_of_birth")
        if not dob or not self.season or not self.season.starts_at:
            return False
        return self._age_on(dob, self.season.starts_at.date()) >= self.season.max_age

    def is_ineligible(self):
        """Married campers and non-church-members are recorded but not accepted."""
        return not self.cleaned_data.get("not_married") or not self.cleaned_data.get("church_member")

    def save(self, commit=True):
        camper = super().save(commit=False)
        season = self.season
        camper.season = season
        camper.camp_filter = season.legacy_filter_key
        camper.mug = False

        if self.is_ineligible():
            camper.status = Camper.Status.REJECTED_MARRIED
        elif self.is_over_age():
            camper.status = Camper.Status.REJECTED_AGE
        else:
            camper.status = Camper.Status.REGISTERED

        # The authoritative price. The PayPal form is rendered from this value
        # and the IPN handler verifies the payment against it.
        hoodies = sum(
            1 for field in ("tshirt_size", "swshirt_size") if self.cleaned_data.get(field)
        )
        camper.amount_due = season.price_for(hoodie_count=hoodies, mug=camper.mug)

        if commit:
            camper.save()
        return camper
