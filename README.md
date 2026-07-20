# Multi-Vendor E-Commerce Analytics & Operations Dashboard

A modular Flask + React reference application for a multi-vendor e-commerce back office — covering role-based order/vendor management, payment and shipping webhook handling, a Pandas ETL pipeline, and automated PowerPoint/Word vendor reporting.

Built with Flask · SQLAlchemy · React · Pandas · python-pptx/docx · Stripe · Shiprocket · SendGrid.

> This is a portfolio/reference project, not a live production deployment. The numbers below describe the codebase itself (routes, models, tests) rather than real-world traffic or business metrics.

## 🚀 Live Demo

- **Frontend**: https://frolicking-semolina-4f3a60.netlify.app/login
- **Backend API**: https://multi-vendor-e-commerce-1n4h.onrender.com/api/health

Seeded demo logins (created automatically on deploy via `flask seed-admin` / `flask seed-demo-data`, see `backend/app/__init__.py`):

| Role | Email | Password | Lands on |
|---|---|---|---|
| Admin | `admin@example.com` | *(set via `ADMIN_PASSWORD` env var)* | `/admin` — platform-wide order/vendor summary |
| Vendor | `vendor@example.com` | `VendorDemo123` | `/vendor/orders` — scoped to one seeded vendor's orders only |
| Analyst | `analyst@example.com` | `AnalystDemo123` | `/analyst/reports` — run the ETL, download a generated vendor report deck |

**Known limitations of this deployment:**
- Backend runs on Render's free tier — the first request after ~15 minutes of inactivity takes 30–60s to wake up.
- Stripe and SendGrid integrations are implemented (see `stripe_service.py`, `sendgrid_service.py`, `webhooks/routes.py`) but not configured in this deployment — Stripe requires an invite for India-based accounts, and no SendGrid key is set. Both fail gracefully (webhook signature verification catches the unconfigured state and returns a clean `400`, no crash).
- `VendorInventory.jsx` and `AnalystTrends.jsx` are UI placeholders — there's no backend route for inventory or trends aggregation yet.
- The ETL pipeline (`vendors_etl.py`) reads from CSV files on disk, decoupled from the live `Order`/`Vendor` tables that power the dashboards — this mirrors a real batch-ingestion pattern (e.g. vendors uploading weekly sales exports) rather than querying the transactional DB directly. Demo CSVs are seeded alongside the DB data so "Run ETL" / "Download Deck" produce real output.

## ✨ Highlights

| Area | What's actually in the repo |
|---|---|
| **Backend architecture** | Flask app factory with Blueprints (`admin`, `vendor`, `analyst`, `auth`, `webhooks`), SQLAlchemy models, and a `roles_required` / `vendor_scoped` decorator pair enforcing 3 roles (admin, vendor, analyst) |
| **Frontend** | React SPA (Vite) with `react-router-dom`, 6 lazy-loaded views (Login, AdminDashboard, VendorOrders, VendorInventory, AnalystReports, AnalystTrends), one shared `DataTable` component, and a `useApi` fetch/auth hook |
| **Integrations** | Stripe (payment intents + webhook signature verification), Shiprocket (shipment creation + tracking webhooks), SendGrid (templated transactional email) — all webhook events are deduplicated via a `WebhookEvent` table keyed on `event_id` |
| **ETL** | `app/etl/vendors_etl.py` loads per-vendor CSV exports with Pandas, cleans/dedupes them, and aggregates into a weekly summary dataframe |
| **Machine learning** | `app/ml/` — scikit-learn pipeline for demand forecasting (`GradientBoostingRegressor`), order anomaly/fraud scoring (`IsolationForest`), and vendor segmentation (`KMeans`), all versioned via a joblib-backed model registry (`ml_model_versions` table) and exposed through a dedicated `ml` blueprint |
| **Reporting** | `app/reports/pptx_generator.py` and `docx_generator.py` render a vendor performance deck/doc from the aggregated ETL output |
| **Tests** | `pytest` suite (`backend/tests/`) covering auth/login, RBAC enforcement, webhook idempotency, and the ML pipeline — 12 tests, all passing |
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
                     ┌──────────▼───────────┐          ┌───────────────────────┐
                     │  Report Generation     │          │   ML Pipeline (app/ml) │
                     │ python-pptx / -docx    │          │ forecast · fraud · seg │
                     └───────────────────────┘          └───────────┬───────────┘
                                                          ┌───────────▼───────────┐
                                                          │  Model Registry         │
                                                          │ joblib + ml_model_ver.  │
                                                          └────────────────────────┘

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
│   │   ├── models.py            # SQLAlchemy models (User, Vendor, Order, WebhookEvent, MLModelVersion)
│   │   ├── auth/                # JWT auth routes + RBAC decorators
│   │   ├── blueprints/
│   │   │   ├── admin/           # Admin-tier routes
│   │   │   ├── vendor/          # Vendor-tier routes
│   │   │   ├── analyst/         # Analyst-tier routes
│   │   │   └── ml/              # ML API routes (forecast/fraud/vendor-scoring)
│   │   ├── integrations/
│   │   │   ├── stripe_service.py
│   │   │   ├── shiprocket_service.py
│   │   │   └── sendgrid_service.py
│   │   ├── webhooks/            # Idempotent webhook receivers
│   │   ├── etl/
│   │   │   └── vendors_etl.py   # Pandas ETL pipeline
│   │   ├── ml/
│   │   │   ├── features.py      # Feature engineering (vendor-week + order-level)
│   │   │   ├── demand_forecast.py  # GradientBoostingRegressor per vendor
│   │   │   ├── fraud_detection.py  # IsolationForest anomaly scoring
│   │   │   ├── vendor_scoring.py   # KMeans segmentation + composite score
│   │   │   └── registry.py      # joblib model persistence + versioning
│   │   └── reports/
│   │       ├── pptx_generator.py
│   │       └── docx_generator.py
│   ├── migrations/              # Flask-Migrate/Alembic scripts
│   ├── tests/                   # pytest suite (12 tests, incl. app/ml)
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

## 🤖 ML Pipeline & API

`app/ml/` adds three scikit-learn models on top of the existing data layer, plus a versioned model registry — no new infra (message queues, GPU workers, external ML platform) required to run it.

### Pipeline design

```
Weekly vendor CSVs ──▶ ETL (existing) ──▶ app/ml/features.py ──▶ model training ──▶ app/ml/registry.py
        │                                        │                    │                     │
        │                              vendor-week features    scikit-learn         joblib artifact +
        │                              (lags, rolling means)    estimator             ml_model_versions row
        │
Live Order table ──────────────────────▶ order-level features ──▶ IsolationForest (fraud)
```

- **Feature engineering** (`features.py`) reuses the existing ETL output rather than reading raw CSVs a second time — `build_vendor_week_features` adds lag-1 and trailing 3-week rolling averages per vendor; `build_order_features` adds per-vendor amount z-scores and time-of-day features for the live `Order` table.
- **Model registry** (`registry.py`) persists each trained pipeline to disk with `joblib` and records a row in `ml_model_versions` (metrics, feature list, file path). Training always creates a new version rather than overwriting — predictions are traceable to the exact model version that produced them.
- **No online/real-time training** — training is a deliberate, explicit action (mirroring the existing "Run ETL" button), not triggered on every request; inference reads the latest saved model.

### Algorithms

| Model | Algorithm | Why this algorithm |
|---|---|---|
| **Demand forecasting** | `GradientBoostingRegressor` (per vendor) | Vendor-week series are short (tens, not thousands, of timesteps) — boosted trees on lag/rolling features are a standard, explainable baseline for short retail series; an RNN/LSTM would be overkill and undertrained on this little data. |
| **Fraud / anomaly detection** | `IsolationForest` (unsupervised) | A new marketplace has little or no labelled fraud data to train a classifier against. Isolation Forest flags orders that look statistically unlike a vendor's own normal pattern (amount z-score, hour, day of week) — a reasonable triage signal, not a fraud verdict. |
| **Vendor segmentation** | `KMeans` + weighted composite score | Exploratory segmentation, not prediction — there's no ground-truth "vendor quality" label. Clusters group similar vendors; `composite_score` (revenue-weighted) is what should be used for ranking. |

### API design

All routes live under `/api/ml` in a dedicated blueprint (`app/blueprints/ml/routes.py`) and reuse the existing `roles_required` / `vendor_scoped` RBAC decorators — no separate ML-specific auth. Training and inference are split into separate endpoints: training is a heavier action gated to `analyst`/`admin`, while inference stays cheap enough for a `vendor` to call for their own forecast.

| Method & Path | Role | Description |
|---|---|---|
| `POST /api/ml/forecast/<vendor_id>/train` | analyst, admin | Trains a demand-forecast model for one vendor from its weekly ETL history; returns the new model version + eval metrics (MAE, MAPE). |
| `GET /api/ml/forecast/<vendor_id>` | analyst, admin, vendor (own only) | Returns next-week revenue prediction; trains a model on first call if none exists yet. |
| `POST /api/ml/fraud/train` | analyst, admin | Trains the anomaly detector on all current orders. |
| `GET /api/ml/fraud/orders` | analyst, admin | Scores every order, returning a 0–1 `risk_score` and `is_anomalous` flag per order. |
| `GET /api/ml/vendors/scores?clusters=3` | admin, analyst | Returns all vendors with `cluster` and `composite_score`, sorted descending. |

Example:

```bash
curl -X POST http://localhost:5000/api/ml/forecast/1/train \
  -H "Authorization: Bearer $TOKEN"
# {"model_name": "demand_forecast", "model_version": "20260720000000",
#  "metrics": {"mae_inr": 42.1, "mape_pct": 6.3, "training_rows": 10}}

curl http://localhost:5000/api/ml/forecast/1 -H "Authorization: Bearer $TOKEN"
# {"vendor_id": 1, "predicted_revenue_inr": 812.5,
#  "model_name": "demand_forecast", "model_version": "20260720000000", "model_metrics": {...}}
```

### Migration & dependencies

- Adds one table, `ml_model_versions` (see `migrations/versions/160364ee0504_add_ml_model_versions.py`) — run `flask db upgrade` after pulling.
- Adds `scikit-learn` and `joblib` to `requirements.txt`.
- Model artifacts are written to `ML_MODEL_DIR` (defaults to `data/models`, same pattern as the ETL's `VENDOR_ETL_OUTPUT_DIR`).

### Tests

`backend/tests/test_ml.py` covers: minimum-history validation, train → predict round-trip for the forecaster, anomaly flagging on an injected outlier order, vendor ranking by composite score, and RBAC enforcement on the `/api/ml/*` routes (12 tests total in the suite, all passing).

