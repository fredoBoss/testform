# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app is

A customer feedback form delivered as a **Progressive Web App**, built with Django 5.2 (server-rendered templates, SQLite, no JS framework or build step). Users sign up and log in. There are two roles: `customer` (submits feedback, sees only their own) and `admin` (sees, replies to, and deletes everyone's feedback; creates other admins).

## Commands

The project uses a virtualenv at `.venv` (Windows paths shown; Python 3.11).

```sh
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt   # first-time setup
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py seed_demo          # demo admin + customers + sample feedback (DEBUG only; credentials in the command file)
.venv/Scripts/python manage.py createsuperuser    # real first admin (superusers get role=admin)
.venv/Scripts/python manage.py runserver

.venv/Scripts/python manage.py test                                                   # all tests
.venv/Scripts/python manage.py test feedback                                          # one app
.venv/Scripts/python manage.py test feedback.tests.CustomerTests.test_cannot_view_other_customers_feedback  # one test
.venv/Scripts/python manage.py check
.venv/Scripts/python manage.py makemigrations
```

Settings read `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (`1`/`0`, defaults to `1`), `DJANGO_ALLOWED_HOSTS` (comma-separated) and `DATABASE_URL` (Postgres; SQLite at `db.sqlite3` when unset) from the environment. With `DEBUG` off, settings refuse to start without `DJANGO_SECRET_KEY`, because the built-in fallback key is public. They also add WhiteNoise to serve `collectstatic` output, so run `collectstatic` first. With `DEBUG` on, `runserver` serves static files and WhiteNoise isn't loaded.

### Docker

`Dockerfile` builds a production image: Python 3.11-slim, non-root `app` user, `DJANGO_DEBUG=0`, and static files collected at build time and served by WhiteNoise. On start the container runs `migrate`, then gunicorn on `$PORT` (default 8000), with `WEB_CONCURRENCY` workers (default 3). `compose.yaml` adds Postgres 17 and wires up `DATABASE_URL`. It refuses to start until `DJANGO_SECRET_KEY` is set in `.env` (copy `.env.example`).

```sh
docker compose up --build                                          # http://localhost:8000
docker compose exec web python manage.py createsuperuser
docker compose run --rm -e DJANGO_DEBUG=1 web python manage.py seed_demo   # demo data needs DEBUG
docker compose down            # add -v to also delete the Postgres volume
```

### Deployment (Vercel)

Deployed on Vercel with its zero-config Django support: it finds `manage.py`, uses `WSGI_APPLICATION`, runs `collectstatic` into `STATIC_ROOT` and serves `/static/` from its CDN. When `VERCEL=1`, settings default `DEBUG` to off, add Vercel's domains to `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`, enable secure cookies, and refuse to start without `DJANGO_SECRET_KEY` or a Postgres `DATABASE_URL`, because Vercel's filesystem is read-only and per-instance. Vercel imports the settings during the build, not just at runtime. So `DJANGO_SECRET_KEY` and `DATABASE_URL` must already be set for Production and Preview before a deploy, or the build fails with `DJANGO_SETTINGS_FAILED`. The database comes from the Neon integration, which sets `DATABASE_URL` (pooled through PgBouncer, hence `disable_server_side_cursors`) and `DATABASE_URL_UNPOOLED`.

The `buildCommand` in `vercel.json` runs only for production deploys (`VERCEL_ENV=production`). It applies `migrate` over `DATABASE_URL_UNPOOLED`, then runs `bootstrap_admin`, which creates the first admin from `DJANGO_SUPERUSER_USERNAME`/`_EMAIL`/`_PASSWORD` and does nothing once any admin exists. Preview deploys share the production database, so they never migrate. A migration therefore reaches the database only when it's merged to `main`, and a failing migration fails the production build. `.vercelignore` keeps `.venv` and `db.sqlite3` out of CLI uploads.

## Architecture

Three apps under `config/` (project settings and root URLs):

- **`accounts`**: custom `User` (`AUTH_USER_MODEL = 'accounts.User'`) with a `role` field and `is_admin` / `is_customer` properties. `AdminRequiredMixin` and `CustomerRequiredMixin` in `accounts/mixins.py` are the access-control primitives: anonymous users are sent to the login page, logged-in users with the wrong role get a 403. Admins have a user list and a form to create admins.
- **`feedback`**: the `Feedback` model, the customer views (create, list, detail) and the admin views (dashboard with stats and filters, review, delete). `home` (at `/`) redirects by role.
- **`pwa`**: serves `/sw.js`, `/manifest.webmanifest` and `/offline/` from templates, mounted at the site root.

Project-wide templates (`base.html`, `includes/`) live in `templates/`. The single stylesheet is `static/css/app.css`. Everything else is app-local (`<app>/templates/<app>/`, `pwa/static/pwa/`).

Colours are CSS custom properties on `:root` in `app.css`, sampled from the logo: brand blue as the accent, plus red and green. The theme is light only, on a white background, and `theme-color` and the manifest colours are white to match. Use the semantic tokens (`--accent`, `--danger`, `--success`, ...) rather than raw hex values. The raw `--brand-red` and `--brand-green` fail text contrast, so don't use them for text or behind white text.

### Role and data-access rules

- **The role is the single source of truth for permissions.** It is independent of Django's `is_staff`/`is_superuser`, which only gate `/admin/`. `UserManager.create_superuser` sets `role=admin` so `createsuperuser` can seed the first admin.
- **Sign-up can't grant admin.** `SignUpForm` sets the role from a class attribute in `save()` and never reads it from POST data. `AdminCreationForm` subclasses it with `role = ADMIN` and is used only behind `AdminRequiredMixin`.
- **Scope every feedback query for a user with `Feedback.objects.visible_to(user)`**: admins get everything, customers only their own, anonymous users nothing. Detail views use it as their queryset, so another customer's feedback returns 404 rather than 403 and its existence isn't revealed.
- **Customer-owned fields come from the request.** The create view sets `customer` from `request.user`, and `status` and `admin_response` aren't in `FeedbackForm`, so a customer can't set them.
- `FeedbackReviewView` accepts POST only and renders `feedback_detail.html` on validation errors, so the detail template must work with a bound `form` in context.
- Tests in `accounts/tests.py` and `feedback/tests.py` check these rules, including attempts to bypass them. Extend those tests when adding views.

### PWA constraints

- The service worker must stay at `/sw.js`, because its scope is limited to its own path. `pwa/tests.py` checks this.
- The service worker caches only static assets and `/offline/`. Page navigations are network-only and never stored, because pages are user-specific and admin pages contain every customer's feedback. Since nothing user-specific is cached, logout has nothing to clear. If you ever cache user data, clear it on logout.
- `pwa/offline.html` is precached for whoever happens to install the service worker, so it must not extend `base.html` or show any user data (also checked by tests).
- When you change a file listed in `PRECACHE_URLS` (`pwa/templates/pwa/sw.js`), bump `CACHE_VERSION` in `pwa/views.py`. Static files use stale-while-revalidate, so in development a CSS change can take one extra reload to appear (or use DevTools → Application → "Update on reload").
- Service workers only register on secure origins. `localhost`/`127.0.0.1` work over HTTP, but a LAN IP needs HTTPS.
- Offline feedback submission is not implemented. If you add it, queue submissions locally and send them only once the user is back online and still logged in as the same user.
- `static/css/app.css` deliberately loads no web fonts or CDNs, so cached pages render offline.
- The logo and app icons are the Perfect Milling Corporation PNGs in `static/icons/` (`icon-<size>x<size>.png`, white background). They serve as the header logo, favicon, apple-touch icon and manifest icons. The lettering reaches the edges, so they're declared `purpose: "any"` only. Don't mark them `maskable` unless a padded version is added.
