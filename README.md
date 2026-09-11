Multi-Vendor E-Commerce Analytics & Operations Dashboard

A full-stack multi-vendor e-commerce back-office application built with
Flask, React, PostgreSQL, Pandas, scikit-learn, Docker, AWS, and
Vercel.

The application provides role-based order and vendor management, webhook
integrations, ETL analytics, machine-learning workflows, and automated
vendor reporting.

🚀 Live Deployment

Frontend: https://multi-vendor-e-commerce-nu.vercel.app/login
[Email: admin@example.com, Password:1234]

Backend API:
https://su-382ca15e5098416e9d60dd738a2603c0.ecs.ap-south-1.on.aws

Backend health check: /api/health

Architecture

                         ┌──────────────────────┐
                         │       Browser        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Vercel Frontend    │
                         │   React + Vite SPA   │
                         └──────────┬───────────┘
                                    │ HTTPS / REST
                                    ▼
                         ┌──────────────────────┐
                         │   AWS ECS Express    │
                         │  Flask + Gunicorn    │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴───────────┐
                         ▼                      ▼
                ┌─────────────────┐    ┌─────────────────┐
                │ Amazon RDS      │    │ Amazon S3       │
                │ PostgreSQL      │    │ Vendor Reports  │
                └─────────────────┘    └─────────────────┘

The frontend communicates with the deployed backend through the
VITE_API_BASE_URL environment variable.

👤 Demo Accounts

Demo data is automatically seeded when the backend starts.

Role              Email                   Password           Dashboard

Admin             admin@example.com     Set through        /admin
ADMIN_PASSWORD

Vendor            vendor@example.com    VendorDemo123    /vendor/orders

Analyst           analyst@example.com   AnalystDemo123   /analyst/reports

Role Permissions

Role          Access

Admin     Platform-wide vendor and order information
Vendor    Own vendor's orders and vendor-scoped operations
Analyst   ETL, reporting, analytics, and ML workflows

Authentication uses JWTs with role-based authorization.

✨ Features

Backend

Flask application factory

Modular Flask Blueprints

SQLAlchemy ORM

PostgreSQL persistence

Flask-Migrate / Alembic

JWT authentication

Role-based access control

Vendor-scoped authorization

REST APIs

CORS

Health endpoint at /api/health

Idempotent webhook processing

Gunicorn production server

Dockerized deployment

Frontend

React

Vite

React Router

Lazy-loaded views

Shared API/auth hook

Shared DataTable component

Admin dashboard

Vendor orders dashboard

Vendor inventory interface

Analyst reporting interface

Analyst trends interface

Vercel deployment

SPA routing through frontend/vercel.json

Analytics & ETL

Pandas-based vendor CSV ingestion

Data cleaning

Deduplication

Weekly vendor aggregation

Vendor performance summaries

Machine Learning

Demand forecasting using GradientBoostingRegressor

Order anomaly detection using IsolationForest

Vendor segmentation using KMeans

Feature engineering

Joblib model persistence

Versioned model registry

ML metrics stored in PostgreSQL

Reporting

PowerPoint reports using python-pptx

Word reports using python-docx

Vendor-specific report generation

Amazon S3 report storage

Presigned S3 download URLs

Local-file fallback when S3 is unavailable

Integrations

Stripe payment intents and webhooks

Shiprocket shipment and tracking workflows

SendGrid transactional email

Webhook deduplication through WebhookEvent

🏗️ Project Structure

.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models.py
│   │   ├── auth/
│   │   ├── blueprints/
│   │   │   ├── admin/
│   │   │   ├── vendor/
│   │   │   ├── analyst/
│   │   │   └── ml/
│   │   ├── integrations/
│   │   │   ├── stripe_service.py
│   │   │   ├── shiprocket_service.py
│   │   │   ├── sendgrid_service.py
│   │   │   └── s3_service.py
│   │   ├── webhooks/
│   │   ├── etl/
│   │   │   └── vendors_etl.py
│   │   ├── ml/
│   │   │   ├── features.py
│   │   │   ├── demand_forecast.py
│   │   │   ├── fraud_detection.py
│   │   │   ├── vendor_scoring.py
│   │   │   └── registry.py
│   │   └── reports/
│   │       ├── pptx_generator.py
│   │       └── docx_generator.py
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   ├── components/
│   │   ├── views/
│   │   └── routes/
│   ├── vercel.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yaml
├── requirements.txt
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md

⚙️ Local Setup

Prerequisites

Python 3.12+

Node.js / npm

PostgreSQL

Docker and Docker Compose (optional)

Backend

cd backend

python -m venv venv
source venv/bin/activate

pip install -r ../requirements.txt

cp ../.env.example .env

Configure the required environment variables.

Run migrations:

flask db upgrade

Start the backend:

python run.py

The backend runs on port 5000.

Health check:

GET /api/health

Frontend

cd frontend

npm install
npm run dev

The frontend uses:

VITE_API_BASE_URL

to determine the backend API base URL.

🐳 Docker

From the repository root:

docker compose up --build

Docker Compose provides:

PostgreSQL

Flask + Gunicorn backend

React frontend served through nginx

The frontend proxies /api/* requests to the backend inside the Docker
network.

🧪 Testing

Run:

cd backend
pytest --cov=app --cov-report=term-missing

The test suite covers:

Authentication

Login

RBAC enforcement

Vendor-scoped access

Webhook idempotency

Demand forecasting

Anomaly detection

Vendor scoring

ML authorization

🔐 Environment Variables

Important backend variables include:

DATABASE_URL
JWT_SECRET_KEY

ADMIN_EMAIL
ADMIN_PASSWORD

STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET

SHIPROCKET_EMAIL
SHIPROCKET_PASSWORD

SENDGRID_API_KEY
SENDGRID_FROM_EMAIL

AWS_S3_BUCKET
AWS_REGION

ML_MODEL_DIR
VENDOR_ETL_OUTPUT_DIR

Frontend:

VITE_API_BASE_URL

Security

Never commit:

Database passwords

AWS access keys

API keys

JWT secrets

Webhook secrets

Other production credentials

to the repository.

AWS application credentials are obtained through the AWS credential
provider chain and IAM roles rather than being hard-coded.

☁️ AWS Deployment

The backend is deployed using AWS ECS Express.

ECS

The Dockerized Flask application runs with Gunicorn:

Client
  ↓
ECS Express Gateway / Load Balancer
  ↓
Flask + Gunicorn

The container listens on port 5000.

The load balancer health check uses:

GET /api/health

The endpoint returns HTTP 200 when the application is healthy.

Amazon RDS

PostgreSQL is hosted on Amazon RDS.

The database stores:

Users

Vendors

Orders

Webhook events

ML model versions

Amazon S3

Vendor reports can be stored in Amazon S3.

Reports are written under:

reports/

The backend uses boto3 for S3 operations and can return presigned URLs
for generated reports.

🌐 Vercel Deployment

The React frontend is deployed independently from the backend.

Vercel configuration:

Framework: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist

The frontend receives the AWS backend URL through:

VITE_API_BASE_URL

The project contains:

frontend/vercel.json

with a SPA rewrite so React Router routes such as /login, /admin,
and /vendor/orders work when accessed directly.

{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}

🔒 Role-Based Access Control

Authorization is implemented through JWT claims and decorators.

@roles_required(...)
@vendor_scoped

Admin

Can access platform-wide vendor and order information.

Vendor

Can access only their own vendor data.

Cross-vendor access is rejected by the vendor-scoping layer.

Analyst

Can run analytics, ETL, reporting, and authorized ML workflows.

📊 ETL & Reporting

The ETL pipeline is located at:

backend/app/etl/vendors_etl.py

The pipeline:

Loads vendor CSV exports

Cleans the data

Removes duplicate records

Aggregates vendor activity

Produces analytics-ready data

The reporting layer uses:

python-pptx
python-docx

to generate vendor performance reports.

Generated reports can be uploaded to S3 and accessed through presigned
URLs.

🤖 Machine Learning

The ML layer contains three major workflows.

Demand Forecasting

Vendor historical data
        ↓
Feature engineering
        ↓
GradientBoostingRegressor
        ↓
Revenue prediction

Fraud / Anomaly Detection

Order data
    ↓
Order-level features
    ↓
IsolationForest
    ↓
Risk score + anomaly flag

Vendor Segmentation

Vendor features
      ↓
KMeans clustering
      ↓
Vendor segments
      ↓
Composite score

Models are persisted through a joblib-backed model registry.

Each trained model is versioned and associated with metadata such as
metrics and features.

🔌 ML API

Method & Path                               Role                    Description

POST /api/ml/forecast/<vendor_id>/train   Analyst, Admin          Train a demand
forecasting model

GET /api/ml/forecast/<vendor_id>          Analyst, Admin, Vendor  Return next-week
(own)                   revenue prediction

POST /api/ml/fraud/train                  Analyst, Admin          Train anomaly detector

GET /api/ml/fraud/orders                  Analyst, Admin          Score current orders

🔗 Third-Party Integrations

Stripe

Payment intent handling and webhook signature verification.

Shiprocket

Shipment creation and tracking webhook workflows.

SendGrid

Transactional email functionality.

Webhook Idempotency

Webhook events are stored using WebhookEvent.event_id.

Duplicate webhook deliveries are ignored safely.

📌 Deployment Status

The application is deployed as a split frontend/backend architecture:

GitHub
  │
  ├── frontend
  │      ↓
  │    Vercel
  │
  └── backend
         ↓
      Docker
         ↓
     AWS ECS
      │    │
      │    └── Amazon S3
      │
      └── Amazon RDS

Current deployment components:

React frontend on Vercel

Flask backend on AWS ECS Express

PostgreSQL on Amazon RDS

Vendor report storage on Amazon S3

Vercel SPA routing via frontend/vercel.json

ECS health checks through /api/health

Frontend/backend communication through VITE_API_BASE_URL

Automatic demo data seeding during backend startup

📄 License

See LICENCE in the repository.
