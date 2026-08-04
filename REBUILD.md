# Fully Alive Retreat — site rebuild

A full rebuild of `fullyaliveretreat.com`, done on the `Dillon-claudeRemake` branch.
**Nothing here has been deployed.** Production is untouched and still running the old code.

The site had grown by accretion since 2019: each camp was shipped by editing hardcoded constants
and copy-pasting templates. That left a payment vulnerability, ten dependencies with known CVEs, a
~12 MB homepage, twenty templates with no shared layout, and two JavaScript crashes on the
registration page.

---

## Contents

1. [Read this first](#1-read-this-first) — the two things that need your action
2. [Security](#2-security)
3. [Bugs fixed](#3-bugs-fixed)
4. [Performance](#4-performance)
5. [Design and accessibility](#5-design-and-accessibility)
6. [Architecture](#6-architecture)
7. [Dependencies](#7-dependencies)
8. [Running it locally](#8-running-it-locally)
9. [Deploying](#9-deploying)
10. [Running a camp season](#10-running-a-camp-season)
11. [Not done / deferred](#11-not-done--deferred)

---

## 1. Read this first

### 1.1 Credentials in git history — rotate these

Commit `0bf4057` moved secrets to environment variables **in the working tree only**. History was
never rewritten, so these are still readable by anyone who clones the public repo, and are valid
until you rotate them. This is the single most urgent item, and it is independent of whether you
deploy the rebuild.

| What | Where it leaked | Do this |
|---|---|---|
| Gmail app password `weqf ucmg cksi znvy` | `registration/views.py` @ `176e8db` | Revoke at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), create a new one, set `FAR_EMAIL_APP_PASSWORD` |
| Gmail account password `lluFfull` | same | Change the account password, turn on 2FA |
| `SECRET_KEY` `ml6jd5!%0@!as&3p9fzf1nluv!2alchgps%fn4ubpm#96ax41*` | `personal_code/settings.py` @ `912e79e` | Generate a new one (below), set `DJANGO_SECRET_KEY` |
| PayPal IPN path `V4LrfBrC9UbZYm3k` | `personal_code/urls.py` @ `9516b5e` | Pick a new random path, set `PAYPAL_ENDPOINT`, update the Notification URL in PayPal |

Generate a new secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Rotating `SECRET_KEY` signs everyone out — that is expected and harmless.

**On rewriting history:** you can scrub these with `git filter-repo`, but a force-push cannot
un-leak anything already cloned, forked, or cached by GitHub. **Rotation is the part that actually
protects you.** Treat history rewriting as optional cleanup, done after rotating.

### 1.2 Camper PII in git history

`db.sqlite3` was committed in four early commits (`912e79e`, `a5256a0`, `d2b11fa`, `97399b9`) and
is still retrievable from the public repo. It contains camper names, dates of birth, emails, phone
numbers and **medical notes**.

It is gitignored now, so nothing new is being added, but the historical copy is exposed. Depending
on how you read your obligations to those campers, this may warrant notifying them. At minimum,
purging it is the one case where rewriting history is worth doing — the data cannot be "rotated".

---

## 2. Security

### 2.1 Anyone could pay $1 and be marked fully paid

This was the most serious problem in the codebase.

The PayPal amount was rendered into a form **in the browser** (`views.py:377-390`), and
`check_who_paid_helper()` (`views.py:91-125`) marked a camper paid based on the invoice number
alone. `mc_gross` — what PayPal reported was actually paid — was never compared against anything.

```python
# before — registration/views.py:106-108
for camper in paid_all_campers:      # everyone with a Completed IPN
    camper.paid = True               # amount never checked
    camper.save()
```

Edit the hidden `amount` field in devtools, pay $1, get a confirmed spot.

**Now:** the price is computed on the server at registration time and stored on
`Camper.amount_due`. A new IPN handler (`registration/signals.py`) checks every notification
against it before anything changes:

- the receiver is our PayPal account, not one the payer chose
- the currency is USD
- `mc_gross >= amount_due`
- the invoice resolves to a real camper
- the status is `Completed`

Anything that does not line up is **logged and flagged for review, never auto-accepted**. Flagged
payments appear in a red banner on the staff dashboard. Refunds and reversals now reverse `paid`.

Covered by twelve regression tests in `PaymentVerificationTests`, including the exact
pay-$1 attack.

### 2.2 Other security fixes

| Issue | Before | Now |
|---|---|---|
| `/return` | `@csrf_exempt`, unauthenticated, ran a full DB reconciliation and sent email on every GET — trivially loopable for DoS / mail-reputation damage | A static thank-you page. Payment state changes only via verified IPN |
| `ALLOWED_HOSTS` | `['*']` — Host-header poisoning | From env, defaults to the real domain |
| HTTPS | No `SECURE_SSL_REDIRECT`, no HSTS, no `SECURE_PROXY_SSL_HEADER` | All set, plus a 1-year preloading HSTS header |
| Cookies | `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` both unset (default `False`) | Both on in production, `SameSite=Lax`, 12-hour sessions |
| `local_settings.py` | Wildcard-imported *after* `DEBUG = False`; the file sets `DEBUG = True`. On the server it would silently serve full tracebacks | File and import both deleted; config comes from `.env` |
| `SECRET_KEY` | `os.getenv()` with no default — became `None` and failed obscurely later | Raises `ImproperlyConfigured` at boot in production |
| Open/close registration | Unprotected `GET /open_reg` mutating `settings.GLOBAL_OPEN_REG_FLAG` — CSRF-triggerable, and per-worker so it applied to one gunicorn process and died on restart | POST-only, CSRF-protected, stored on the season row |
| Login | Hand-rolled, unlimited brute force, no error feedback, ran a password hash on every GET | Django's `LoginView` + `django-axes` (5 attempts, 1-hour lockout) |
| Admin URL | `path(r'admin', ...)` — missing slash, malformed routing | `path(f'{ADMIN_URL}/', ...)`, path configurable via env |
| IPN endpoint | Interpolated `None` into the URL when the env var was unset, mounting the listener at `/None/` | Refuses to boot if `PAYPAL_ENDPOINT` is unset |
| Staff dashboard | Full camper PII including medical notes, no cache or index protection | `Cache-Control: no-store`, `X-Robots-Tag: noindex`, and a `robots.txt` disallow |
| Input validation | Every field read raw from `request.POST`; sizes, gender and state never checked against their choices | A real `ModelForm` validates everything |
| Middleware order | WhiteNoise above `SecurityMiddleware`, so static responses got no security headers | Correct order |
| Dependencies | ~10 packages with known CVEs | `pip-audit` clean; Dependabot enabled |

`python manage.py check --deploy --fail-level WARNING` passes with no issues, and runs in CI.

---

## 3. Bugs fixed

**Two JavaScript crashes on the registration page.** `register.html:686` called
`document.getElementById("openMugModal").onclick` on markup that was entirely commented out — that
threw on every page load. Worse, line 644 did the same for `#openTshirtModal`, which sat inside
`{% if not remove_merch_date %}`. With `MERCH_DEAD_LINE_DATETIME = datetime.datetime(2026, 8, 4)`,
that meant **from 4 August the first line of the script block threw**, killing the date-picker
fallback with it. All JavaScript now lives in `static/registration/js/`, and every element lookup
is guarded.

**Closing registration disabled the capacity check.** The capacity gate only ran *inside*
`if settings.GLOBAL_OPEN_REG_FLAG:`, so "closing" registration turned the limit off rather than
closing the form. The comparison also used `>` instead of `>=`, admitting 151 campers against a
capacity of 150 — and `reg()` had no capacity check at all, so a direct POST bypassed it entirely.
All three are fixed and tested.

**Age was computed as `today.year - dob.year`**, ignoring month and day, so it was wrong by up to
a year at both the 23 and 45 boundaries. Age is now measured properly against the first day of camp.

**`filter_campers()` crashed on every call** — it read `camper.timestamp`, a field renamed to
`created` back in migration `0005` (July 2020). It also returned a 6-tuple that its only caller
unpacked as 3 values, so `manage.py email_unregs` had been dead for years. Deleted.

**Confirmation emails said "null".** The merchandise columns stored the literal strings `'None'`
and `'null'` to mean "nothing ordered", and the email printed both hoodie lines unconditionally, so
campers who ordered nothing received *"Forest Sweater: null / Sage Sweater: null"*. Those are real
NULLs now, and the email lists only what was actually ordered.

**PayPal receipts said "Winter 2026"** while the active camp was Summer 2026. The line item comes
from the season record now.

**Duplicate `id="camper_church"`** on two different elements — invalid HTML that only worked
because the jQuery toggle selected by `name`. Replaced with a `<datalist>`, which gives
autocomplete over the 27 member churches *and* free-text entry, in one control.

**Content fixes:** "August 21th – 24st" → proper ordinals; Sunday "12:00 AM - Lunch" → 12:00 PM;
the date-of-birth picker capped at `yearRange: "1930:2019"`; `fullyalive.ics` still advertising
2025 dates (removed — it was unreferenced).

**Also:** `paided.py` had no date filter at all and would have marked every camper since 2019 as
paid. `views.py` read `FAR_EMAIL_PASS_CODE` while the management commands read
`FAR_EMAIL_PASSWORD`, so one path was always broken — now one variable,
`FAR_EMAIL_APP_PASSWORD`. Thirteen templates were missing `</head>`, three were missing `</html>`,
and `cancel.html` carried a leftover `<title>More Info</title>`.

---

## 4. Performance

Every page except the homepage loaded `background_new.jpeg` — **9.9 MB at 5760×2884** — including
the 1.5 KB error pages. The mobile media query re-specified the identical file, so phones got no
benefit. The homepage pulled ~11 MB of backgrounds plus 733 KB of TrueType fonts.

Measured, uncompressed, first visit:

| Page | Before | After | |
|---|---:|---:|---|
| Home | ~12 MB | **247 KB** | 98% smaller |
| Registration | ~10.2 MB | **194 KB** | 98% smaller |
| More info | ~10.1 MB | **184 KB** | 98% smaller |
| Schedule | ~10.1 MB | **182 KB** | 98% smaller |
| Message pages | ~10.1 MB | **279 KB** | 97% smaller |

What changed:

- **Responsive images.** Sources are resized to 1280/1920/2560 as WebP with JPEG fallback, served
  through `<picture>`. `background_new.jpeg` goes 9.9 MB → 100 KB at 1280px WebP.
- **Fonts to WOFF2.** 606 KB + 127 KB of TTF → 49 KB + 60 KB, with `font-display: swap`. The
  display face is subset to the wordmark characters only; the body face keeps all glyphs because
  it carries the Cyrillic used by the church names.
- **jQuery and Bootstrap deleted.** 169 KB was loading on 19 of 20 pages; only one page used it.
  Replaced with ~4 KB of vanilla JS and a purpose-built 32 KB stylesheet.
- **Static tree: 33 MB → 2.5 MB.** ~11 MB of unreferenced files (old shirt mockups, an unused
  webfont kit that was publicly serving its own demo page, a 1.1 MB PDF) deleted. Source
  photographs moved to `assets-src/`, which is **not** served — they were being collected and
  exposed by WhiteNoise.
- **Queries.** The staff dashboard evaluated the same queryset four times via `len()` and rendered
  every camper unpaginated; it now uses one aggregate query and paginates at 50.
- **Caching.** Hashed filenames with a 1-year `Cache-Control`, plus brotli/gzip via WhiteNoise.

Regenerate derived assets after changing a source photo or the wordmark:

```bash
.venv/bin/pip install Pillow "fonttools[woff]"
.venv/bin/python tools/build_assets.py
```

---

## 5. Design and accessibility

The look is a refresh, not a redesign — same coast photography, same `Austhind` display face, same
warm palette (charcoal `#4d4d4d`, sand `#d0a47e`, sea-teal `#508080`). What changed is the system
underneath:

- **Design tokens** for colour, an 8px spacing scale, and a `clamp()` type scale. The old CSS sized
  headings in raw viewport units (`font-size: 13vw`), so text scaled without limit on wide screens.
- **One stylesheet.** The site was running Bootstrap 3.4 from a CDN on 18 pages and Bootstrap 4.6
  locally on two — and those two used `col-xs-*` classes that Bootstrap 4 removed, so the layout
  held together by accident. Replaced with 32 KB of purpose-built CSS.
- **Rebuilt components** — buttons, cards, form fields with real focus rings and inline error
  states, a capacity meter, and a staff table that scrolls inside its own container rather than
  making the page scroll sideways.
- **No CDN assets.** Everything is self-hosted, which also closes the SRI gap (there were zero
  `integrity` attributes) and the `http://` jQuery-UI that `document.write` was injecting into an
  HTTPS page.

Accessibility, all of which was previously absent:

- **Real `<label for>` on every field.** The old form used `<div class="form-label">`, so screen
  readers announced nothing for any of the 16 registration inputs. Yes/no questions are now
  `<fieldset>`/`<legend>` radio groups.
- **Keyboard-navigable.** Every nav item was an `<a>` with no `href`, navigating via `onclick` —
  not focusable, not announced as a link. All are real links now, plus a skip-link and visible
  `:focus-visible` rings.
- Alt text on the logos (they had none); `user-scalable=no` removed from two pages; `<th scope>`
  and `<caption>` on the data tables; corrected heading order; `prefers-reduced-motion` respected.

SEO, also previously absent: meta descriptions, Open Graph and Twitter cards (the site is shared
mainly through Instagram and Telegram, and previously produced a blank card), canonical URLs,
JSON-LD `Event` structured data driven by the season record, a real favicon (it was hotlinked from
icons8), and a `robots.txt`.

The dead `UA-135068928-1` Universal Analytics tag — duplicated across 19 templates and collecting
nothing since UA shut down in July 2023 — is gone. **Set `GA_MEASUREMENT_ID` to a GA4 `G-` ID if
you want analytics back**; the tag renders only when that variable is set.

---

## 6. Architecture

### `CampSeason` — the main structural change

Every per-season value used to be hardcoded across `settings.py`, `views.py`, `urls.py` and several
templates. Opening a camp meant editing source in five places, including a nine-branch `if/elif`
chain mapping URL keywords to camp names.

All of it now lives in one `CampSeason` row: dates, venue, capacity, price, merch prices and
deadline, age limits, the PayPal line item, and whether registration is open. **A new camp is a
form in the admin.** This also fixed the multi-worker registration-toggle bug and gave payment
verification a server-side price to check against.

A data migration seeds all ten historical camps and points every existing camper at the right one.
`Camper.camp_filter` is preserved, so historical records stay matched.

### Other changes

- **Templates**: `base.html` plus 20 pages that extend it. There was previously no `base.html`, no
  `{% extends %}`, and no `{% include %}` anywhere — the same 30-line `<head>` was pasted into 13
  files. Ten near-identical outcome pages now extend one `_message_base.html` and are ~15 lines each.
- **`forms.py`**: a `ModelForm` replaces ~150 lines of hand-rolled validation that lived inside a
  single bare `try/except Exception`, which swallowed every failure into a generic error page.
- **`signals.py` / `services.py`**: payment verification, and a reconciliation fallback that applies
  identical rules.
- **Model fixes**: `date_of_birth` `DateTimeField` → `DateField`; `email` `CharField` → `EmailField`
  (there was no email validation anywhere in the stack); `'None'`-string defaults → real NULLs; a
  `status` field so campers rejected for eligibility stop polluting the unpaid lists; indexes on the
  columns actually queried; the write-only `paypal` column dropped.
- **Deleted**: the empty `fullyalive2019` app (still in `INSTALLED_APPS`), a stray tracked file that
  was a duplicate of `.gitignore`, `import pdb` in production code, ~60 lines of commented-out code
  in `views.py`, and three tracked `.DS_Store` files.
- **Logging**: every `print()` replaced with real logging. There was no `LOGGING` config at all, and
  camper names and payment status were being printed to stdout.
- **Management commands**: five near-identical blast scripts — each with its recipients hardcoded as
  a magic threshold like `pk__gt=193` — became one `send_camper_email` command with `--season`,
  `--audience` and a **dry run by default**, plus `reconcile_payments`.
- **URLs**: named routes throughout, one `camper-info/<slug:season>/` replacing nine hardcoded
  paths, and permanent redirects from every old URL so existing links and PayPal's stored return
  URLs keep working.

### Tests

**53 tests, up from 7.** The old ones used bare `assert` (silently skipped under `python -O`) and
hardcoded birth years, so the age tests would have started failing on their own in 2027. Dates are
now derived from a season the test creates.

Coverage: form validation, age boundaries at exactly ±1 day, capacity including the direct-POST
bypass, the merch deadline, pricing, **payment verification including the pay-$1 attack**,
reconciliation, staff authorization, and every public page.

---

## 7. Dependencies

| Package | Before | After | Why |
|---|---|---|---|
| Django | `4.2` (the `.0`) | `5.2 LTS` | 4.2 is end-of-life; the pinned `.0` predates ~25 security releases |
| gunicorn | `19.10.0` (2018) | `23+` | CVE-2024-1135, CVE-2024-6827 — HTTP request smuggling |
| requests | `2.28.2` | `2.32.4+` | CVE-2023-32681, CVE-2024-35195 |
| urllib3 | `1.26.14` | `2.2+` | CVE-2023-45803, CVE-2024-37891 |
| certifi | `2022.12.7` | current | CVE-2023-37920 — trusted a revoked CA |
| idna | `3.4` | `3.7+` | CVE-2024-3651 |
| whitenoise | `4.1.4` | `6.9+` | Incompatible with Django 4.2's storage API |
| django-paypal | `1.1.2` | `2.1` | Handles money; four years of fixes |
| dj-database-url | `0.5.0` | `3.x` | `config()` returned `{}` on a missing env var, wiping the DB config |
| psycopg2 | `2.9.5` | `psycopg[binary] 3.x` | Source build → wheel |
| **`pi==0.1.2`** | present | **removed** | A 2013 single-maintainer package nothing imported — supply-chain risk |
| djangorestframework | `3.11.0` | **removed** | CVE-2024-21520, and it wasn't even in `INSTALLED_APPS` — used only for HTTP status constants |
| pytz, six | pinned | **removed** | `pytz==2018.9` was an eight-year-old timezone database |
| django-axes | — | added | Login throttling |

Python 3.11.9 → 3.12 (`.python-version`).

---

## 8. Running it locally

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
# set DJANGO_DEBUG=true and any DJANGO_SECRET_KEY; PAYPAL_ENDPOINT can be anything locally

.venv/bin/python manage.py migrate          # seeds all ten camp seasons
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

```bash
.venv/bin/python manage.py test --settings=personal_code.settings_test
.venv/bin/python manage.py check --deploy
.venv/bin/pip-audit
```

**Note:** the `db.sqlite3` that was in the working tree was a stale dev copy — two test campers,
and its migration history had diverged from the committed migrations at `0009`. It is preserved as
`db.sqlite3.stale-dev` and is not used. Production runs Postgres.

---

## 9. Deploying

Only after you have reviewed the site and decided to go ahead.

**1. Back up the database first.** The migration changes column types and rewrites merchandise
values.

```bash
heroku pg:backups:capture --app <app>
heroku pg:backups:download --app <app>
```

**2. Set the environment variables** (rotated per §1.1):

```bash
heroku config:set \
  DJANGO_SECRET_KEY='<new key>' \
  PAYPAL_ENDPOINT='<new random path>' \
  FAR_EMAIL_APP_PASSWORD='<new app password>' \
  DJANGO_DEBUG=false \
  DJANGO_ALLOWED_HOSTS='fullyaliveretreat.com,www.fullyaliveretreat.com' \
  DJANGO_ADMIN_URL='<something other than admin>' \
  DJANGO_ADMIN_EMAILS='you@example.com' \
  --app <app>
```

Old variables `FAR_EMAIL_PASSWORD` and `FAR_EMAIL_PASS_CODE` can be removed.

**3. Update the PayPal Notification URL** to `https://fullyaliveretreat.com/<PAYPAL_ENDPOINT>/`.
Miss this and payments will not be recorded.

**4. Deploy.** The `Procfile` now runs `migrate` in the release phase, so migrations apply
automatically — and a failed release rolls back rather than leaving a half-migrated app.

**5. Verify:**

```bash
heroku run python manage.py check --deploy --app <app>
```

Then check that `/camper-info/summer-2026/` shows the expected camper count, that
`/camper-info/summer-2025/` and the older seasons still list their campers, and that dates of birth
display correctly.

**6. Test one real payment** end to end and confirm the camper flips to paid.

If you need to roll back: `heroku releases:rollback`, then restore the backup — the migration is
reversible, but restoring is the safer path once real data has been written.

---

## 10. Running a camp season

This used to require a developer. It is now admin work.

**Opening a new camp** — Admin → Camp seasons → Add:

- **Slug** `summer-2027`, **name** "Fully Alive Retreat 2027"
- **Legacy filter key** `summer 2027 camp` — must be unique, and never change it once campers exist
- **Active** — checking this automatically deactivates the previous season
- Registration window, capacity, price, age limits
- Merch deadline and hoodie price
- Camp start and end, venue

The public site, the countdown, the info and schedule pages, the PayPal line item, the confirmation
email, and the `Event` structured data all follow from that row.

**Opening and closing registration**: the button on the staff dashboard, or the `Registration open`
checkbox. It takes effect immediately across all workers and survives restarts.

**During camp season:**

- `/camper-info/` — registrations, with tabs for paid, unpaid, flagged and ineligible
- **Flagged** means a payment arrived that did not match the expected amount, currency or receiver.
  Those campers are *not* marked paid. Review each one and decide.
- **Export CSV** for check-in lists
- **Re-check payments** re-runs verification against recorded PayPal notifications, for a missed
  notification

**Emailing campers:**

```bash
# Always dry-runs first; --confirm actually sends.
python manage.py send_camper_email --season summer-2027 --audience unpaid \
    --template email/reminder.html --subject "Don't forget to pay"
```

**Adding a church to the registration form:** edit `registration/churches.py`.

---

## 11. Not done / deferred

- **Nothing is deployed**, and no commits were made to `master`.
- **Secret rotation is yours** — I cannot reach your Gmail, Heroku or PayPal accounts. See §1.1.
- **Git history not rewritten.** Rotation matters more; see the note in §1.1.
- **No GA4 property.** The dead UA tag is removed. Give me a `G-` ID and analytics come back.
- **Payments not tested against live PayPal.** Verification is covered by tests that simulate IPNs,
  but a real sandbox transaction should be run before the next camp opens. This needs your sandbox
  credentials.
- **Not visually reviewed on real devices.** Rendering has been checked, but the design refresh
  needs your eyes — that is the gate for whether any of it ships.
- **Content still needs a pass.** Topic and speakers are "To be announced", and the schedule is
  carried over from 2026.
- **`region` and `activity` kept** on the model. They are winter-camp fields, unused by the summer
  form, retained so historical winter records are not lossy.
- **No Content-Security-Policy header yet.** All inline scripts and the CDN dependencies are gone,
  so the site is *ready* for one — but adding it needs testing against the PayPal form, which
  renders its own markup. Worth doing as a follow-up.
- **No rate limit on registration POSTs.** Login is throttled by django-axes; registration is not.
  It has never been abused, and adding it needs a decision about what limit is reasonable for a
  church group where several people may register from one church's network.
