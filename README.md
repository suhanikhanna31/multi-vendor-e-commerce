# Multi-Vendor E-Commerce Analytics & Operations Dashboard

A modular Flask + React reference application for a multi-vendor e-commerce back office — covering role-based order/vendor management, payment and shipping webhook handling, a Pandas ETL pipeline, and automated PowerPoint/Word vendor reporting.

Built with Flask · SQLAlchemy · React · Pandas · python-pptx/docx · Stripe · Shiprocket · SendGrid.

> This is a portfolio/reference project, not a live production deployment. The numbers below describe the codebase itself (routes, models, tests) rather than real-world traffic or business metrics.

## ✨ Highlights

| Area | What's actually in the repo |
|---|---|
| **Backend architecture** | Flask app factory with Blueprints (`admin`, `vendor`, `analyst`, `auth`, `webhooks`), SQLAlchemy models, and a `roles_required` / `vendor_scoped` decorator pair enforcing 3 roles (admin, vendor, analyst) |
| **Frontend** | React SPA (Vite) with `react-router-dom`, 6 lazy-loaded views (Login, AdminDashboard, VendorOrders, VendorInventory, AnalystReports, AnalystTrends), one shared `DataTable` component, and a `useApi` fetch/auth hook |
| **Integrations** | Stripe (payment intents + webhook signature verification), Shiprocket (shipment creation + tracking webhooks), SendGrid (templated transactional email) — all webhook events are deduplicated via a `WebhookEvent` table keyed on `event_id` |
| **ETL** | `app/etl/vendors_etl.py` loads per-vendor CSV exports with Pandas, cleans/dedupes them, and aggregates into a weekly summary dataframe |
| **Reporting** | `app/reports/pptx_generator.py` and `docx_generator.py` render a vendor performance deck/doc from the aggregated ETL output |
| **Tests** | `pytest` suite (`backend/tests/`) covering auth/login, RBAC enforcement, and webhook idempotency — 6 tests, all passing, **55% statement coverage** measured via `pytest-cov` |
| **Config** | Env-based config for dev/production/testing (`app/config.py`); `docker-compose.yml` runs Postgres + the Flask backend (gunicorn) + the React frontend (nginx) together; no CI workflow yet |

## 🏗️ Architecture

```
                     ┌─────────────────────┐
                     │      React SPA       │
                     │  (lazy routes, hooks) │
                     └──────────┬───────────┘
                                │ REST / JWT
                     ┌──────────▼───────────┐
                     │     Flask API         │
                     │  Blueprints + RBAC     │
                     └───┬──────┬──────┬─────┘
         ┌───────────────┘      │      └───────────────┐
┌─────────▼────────┐  ┌──────────▼─────────┐  ┌──────────▼─────────┐
│ Stripe (payments) │  │ Shiprocket (ship.) │  │ SendGrid (notify.)  │
│ webhooks + verify  │  │ webhooks + retry    │  │ templated emails    │
└─────────────────────┘  └──────────────────────┘  └─────────────────────┘
                                │
                     ┌──────────▼───────────┐
                     │   Pandas ETL Layer     │
                     │ vendor CSV → analytics │
                     └──────────┬───────────┘
                     ┌──────────▼───────────┐
                     │  Report Generation     │
                     │ python-pptx / -docx    │
                     └───────────────────────┘

           Env-based config (dev / production / testing) · pytest
```

## 📁 Repo Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory, blueprint registration
│   │   ├── config.py            # Env-based config (dev/production/testing)
│   │   ├── extensions.py        # db, jwt, cors, migrate singletons
│   │   ├── models.py            # SQLAlchemy models (User, Vendor, Order, WebhookEvent)
│   │   ├── auth/                # JWT auth routes + RBAC decorators
│   │   ├── blueprints/
│   │   │   ├── admin/           # Admin-tier routes
│   │   │   ├── vendor/          # Vendor-tier routes
│   │   │   └── analyst/         # Analyst-tier routes
│   │   ├── integrations/
│   │   │   ├── stripe_service.py
│   │   │   ├── shiprocket_service.py
│   │   │   └── sendgrid_service.py
│   │   ├── webhooks/            # Idempotent webhook receivers
│   │   ├── etl/
│   │   │   └── vendors_etl.py   # Pandas ETL pipeline
│   │   └── reports/
│   │       ├── pptx_generator.py
│   │       └── docx_generator.py
│   ├── migrations/              # Flask-Migrate/Alembic scripts
│   ├── tests/                   # pytest suite (55% coverage)
│   ├── Dockerfile
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── hooks/useApi.js      # Shared fetch/auth hook
│   │   ├── components/shared/   # DataTable.jsx
│   │   ├── views/                # 6 lazy-loaded route views
│   │   └── routes/AppRoutes.jsx # Route config
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .dockerignore
├── .gitignore
└── LICENSE
```

## ⚙️ Setup

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example .env      # fill in Stripe/Shiprocket/SendGrid/DB keys
flask db upgrade
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

### Docker

```bash
cp .env.example .env      # fill in Stripe/Shiprocket/SendGrid keys; DATABASE_URL is overridden by compose
docker compose up --build
```

This starts three services:
- `db` — Postgres 16, exposed on `5432`
- `backend` — Flask + gunicorn, runs `flask db upgrade` on startup, exposed on `5000`
- `frontend` — Vite build served by nginx, exposed on `8080`, proxies `/api/*` to `backend:5000`

Open `http://localhost:8080`. The Docker setup was validated by building the Dockerfiles' logic and linting `docker-compose.yml`, but wasn't run end-to-end in this environment (no Docker daemon here) — test it locally before relying on it.

## 🔑 Role-Based Access Control

| Role | Access |
|---|---|
| **Admin** | Lists all vendors, views platform-wide order/vendor summary |
| **Vendor** | Own orders only, enforced by `vendor_scoped` (cross-vendor requests return 403) |
| **Analyst** | Triggers the ETL aggregation and generates per-vendor report decks |

Enforced via `@roles_required(...)` and `@vendor_scoped` decorators on top of JWT claims (see `backend/app/auth/decorators.py`).

## 🔌 Third-Party Integrations

- **Stripe** — payment intent handling, webhook signature verification.
- **Shiprocket** — shipment creation, tracking webhooks.
- **SendGrid** — templated transactional emails (e.g. order confirmation) triggered from the Stripe webhook handler.

All webhook handlers persist a `WebhookEvent.event_id` and short-circuit duplicate deliveries, verified by `tests/test_webhooks.py::test_stripe_webhook_is_idempotent`.

## 📊 ETL & Reporting

- `etl/vendors_etl.py` ingests raw per-vendor CSV exports, cleans/deduplicates them, and aggregates into a weekly summary dataframe (`run_weekly_aggregation`).
- `reports/pptx_generator.py` and `reports/docx_generator.py` render a vendor performance deck/report from that aggregated dataframe, exposed via the analyst blueprint's `/api/analyst/reports/<vendor_id>/deck` endpoint.
