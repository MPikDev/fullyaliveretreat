# Fully Alive Retreat

The website for the Fully Alive Retreat: camp registration, PayPal payment, and camper email.
Django 5.2, deployed to Heroku.

> **Rebuilt.** See [REBUILD.md](REBUILD.md) for what changed, why, and the deployment steps.
> **Read section 1 of that document first** — there are credentials in this repository's git
> history that need rotating.

---

## Getting set up

Requires Python 3.12 (see `.python-version`).

```bash
git clone https://github.com/MPikDev/fullyaliveretreat.git
cd fullyaliveretreat

python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
```

Edit `.env` and set at least:

```
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=<anything, for local use>
PAYPAL_ENDPOINT=<anything, for local use>
```

Generate a real secret key with:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Then:

```bash
.venv/bin/python manage.py migrate          # also seeds all ten camp seasons
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

The site runs at http://127.0.0.1:8000/, the admin at `/admin/`.

Local development uses SQLite. Set `DATABASE_URL` to use Postgres instead.

## Common tasks

```bash
# Tests
.venv/bin/python manage.py test --settings=personal_code.settings_test

# Production configuration check
.venv/bin/python manage.py check --deploy

# Dependency vulnerability scan
.venv/bin/pip install pip-audit && .venv/bin/pip-audit

# Re-check PayPal payments against camper records
.venv/bin/python manage.py reconcile_payments --season summer-2026

# Email campers (dry run unless --confirm is passed)
.venv/bin/python manage.py send_camper_email --season summer-2026 --audience unpaid \
    --template email/reminder.html --subject "Don't forget to pay"

# Rebuild derived images and fonts from assets-src/
.venv/bin/pip install Pillow "fonttools[woff]"
.venv/bin/python tools/build_assets.py
```

## Opening a new camp

Add a **Camp season** in the admin. Dates, venue, capacity, price, merchandise and age limits all
live on that record — the public pages, the countdown, the PayPal line item and the confirmation
email follow from it. No code changes needed. See
[REBUILD.md § 10](REBUILD.md#10-running-a-camp-season).

## Layout

```
personal_code/      settings, URLs, WSGI
registration/       the app — models, forms, views, payment verification
  models.py           CampSeason and Camper
  forms.py            registration form and all validation
  signals.py          PayPal IPN verification — the only place a camper becomes paid
  services.py         payment reconciliation
  churches.py         the church list offered on the form
templates/          base.html plus every page
static/registration/  served assets — css, js, img, fonts (generated)
assets-src/         source photographs and fonts, never served
tools/              build_assets.py
```

## Configuration

All configuration is environment variables; see `.env.example` for the full list with comments.
Nothing secret belongs in this repository.

In production, missing required variables cause the app to refuse to start rather than fall back
to an insecure default.
