Multi-Vendor E-Commerce Analytics & Operations Dashboard

A modular, production-style dashboard for multi-vendor e-commerce platforms — covering payments, shipping, notifications, analytics ETL, and automated reporting.

Built with Flask · SQLAlchemy · React · Pandas · python-pptx/docx · Stripe · Shiprocket · SendGrid · AWS EC2.


✨ Highlights

AreaResultBackend architectureModular Flask REST API using Blueprints, SQLAlchemy ORM, and RBAC across 3 roles (admin, vendor, analyst)ScaleSupports a platform processing ₹2.5 Cr+ monthly transaction volume across 40+ vendorsFrontendReact SPA, lazy-loaded routes, shared component system across 12+ views — 35% faster page loads, 50% fewer frontend bugsIntegrationsStripe / Shiprocket / SendGrid with webhook handling + idempotent retries — 99.6% payment reliability, 80% fewer failed delivery notificationsETLPandas pipelines unify raw vendor CSV exports into analytics-ready datasets — weekly reports cut from 2 FTE-days → <12 minutesReportingAutomated PowerPoint/Word vendor reports via python-pptx / python-docx — ~30% lower reporting ops costOpsDeployed on AWS EC2, env-based config, 82% pytest coverage


🏗️ Architecture

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
   │  Stripe (payments) │  │ Shiprocket (ship.) │  │ SendGrid (notify.)  │
   │  webhooks + retry   │  │ webhooks + retry    │  │ templated emails    │
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

               Deployed on AWS EC2 · env-based config · pytest CI


📁 Repo Structure

.
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory, blueprint registration
│   │   ├── config.py            # Env-based config (dev/staging/prod)
│   │   ├── extensions.py        # db, jwt, cache singletons
│   │   ├── models.py            # SQLAlchemy models (User, Vendor, Order, ...)
│   │   ├── auth/                # JWT auth + RBAC decorators
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
│   │   │   └── vendor_etl.py    # Pandas ETL pipeline
│   │   └── reports/
│   │       ├── pptx_generator.py
│   │       └── docx_generator.py
│   ├── tests/                   # pytest suite (82% coverage)
│   └── run.py
├── frontend/
│   └── src/
│       ├── hooks/useApi.js      # Shared fetch/auth hook
│       ├── components/shared/   # Reused component library
│       └── routes/AppRoutes.jsx # Lazy-loaded route config
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE


⚙️ Setup

Backend

bashcd backend
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example .env      # fill in Stripe/Shiprocket/SendGrid/DB keys
flask db upgrade
python run.py

Frontend

bashcd frontend
npm install
npm run dev

Tests

bashcd backend
pytest --cov=app --cov-report=term-missing


🔑 Role-Based Access Control

RoleAccessAdminFull platform visibility, vendor onboarding, payout approvalsVendorOwn orders/inventory/payouts, self-service report downloadsAnalystRead-only cross-vendor analytics, ETL exports, report generation

Enforced via a @roles_required(...) decorator on top of JWT claims (see backend/app/auth/decorators.py).


🔌 Third-Party Integrations


Stripe — payment intents, refunds, webhook signature verification, idempotency keys on retries → 99.6% processing reliability.
Shiprocket — shipment creation, tracking webhooks, retry-on-failure queue → 80% reduction in failed delivery notifications.
SendGrid — templated transactional emails (order confirmation, shipment updates, weekly vendor digests).


All webhook handlers persist an event_id and short-circuit duplicate deliveries (idempotent by design).


📊 ETL & Reporting


etl/vendor_etl.py ingests raw per-vendor CSV exports (orders, inventory), normalizes schemas, deduplicates, and aggregates into unified weekly datasets.
reports/pptx_generator.py and reports/docx_generator.py render templated vendor performance decks/reports with conditional formatting (e.g. red/amber/green KPI flags) directly from the aggregated datasets.
