# Zero-Trust Secure Document Management System with AI-Based Anomaly Detection

An academic full-stack project for securely storing and governing sensitive documents under zero-trust principles. It will combine Django REST APIs, a React interface, encrypted document storage, SHA-256 integrity verification, tamper-evident audit records, role-based access control, and explainable anomaly detection.

## Current status

- **Completed:** Phase 1 foundation and Phase 2 JWT authentication/RBAC, including token refresh, refresh-token blacklisting on logout, authenticated profiles, administrator user listing, and reusable role policy classes.
- **Planned:** Document storage and encryption, audit hash chain, anomaly detection, React UI, Docker, and comprehensive tests.

## Technology stack

| Technology | Purpose |
| --- | --- |
| Python 3.14.3 / Django 6.1.1 | Secure backend and ORM |
| Django REST Framework 3.18.1 / Simple JWT 5.5.1 | REST API and JWT authentication |
| PostgreSQL 18.6 / psycopg 3.3.5 | Relational persistence |
| React (planned) | Responsive web interface |
| scikit-learn (planned) | Isolation Forest anomaly detection |

## Project layout

```text
backend/                 Django project and applications
  apps/authentication/   Custom user identity and future JWT flows
  apps/documents/        Secure document lifecycle (planned)
  apps/audit/            Tamper-evident audit records (planned)
  apps/security/         Security policy/events (planned)
  apps/anomaly_detection/ ML anomaly pipeline (planned)
frontend/                Planned React application
ml/                      Planned model training and synthetic data tools
docs/                    Architecture, security, API, and database notes
```

## Local setup

Prerequisites are the existing Python 3.14.3 virtual environment and PostgreSQL 18.6 server with the already-created `secure_document_db` database.

1. Copy `.env.example` to `.env` and enter local-only values, including the PostgreSQL password. Never commit `.env`.
2. Run checks: `venv\\Scripts\\python.exe backend\\manage.py check`
3. Apply migrations: `venv\\Scripts\\python.exe backend\\manage.py migrate`
4. Start the API: `venv\\Scripts\\python.exe backend\\manage.py runserver`
5. Visit `http://127.0.0.1:8000/api/health/` for the unauthenticated health endpoint.

Dependencies are pinned in `backend/requirements.txt`. JWT is the default API authentication mechanism. The health endpoint and login/token-refresh routes are deliberately public; all other DRF endpoints require a valid JWT for an active application account.

## Authentication and authorization

Use `POST /api/auth/login/` with `email` and `password` to receive access and refresh tokens. Use `Authorization: Bearer <access-token>` for protected endpoints. Access tokens last 15 minutes by default; refresh tokens last one day by default, rotate when refreshed, and can be blacklisted through logout. Deployments can change token lifetimes using `JWT_ACCESS_TOKEN_MINUTES` and `JWT_REFRESH_TOKEN_DAYS` in the ignored environment configuration.

Administrators may list user profiles. Reusable permissions define the following Phase 2 policy for later modules: all active roles can access permitted documents; Managers and Administrators can manage documents; Administrators and Auditors can read audit logs, security data, and anomaly data. Current document, audit, security, and anomaly endpoints are intentionally not exposed yet.

## Security baseline

Configuration secrets and database credentials are read from environment variables. `.env` is ignored by Git. `DJANGO_SECRET_KEY` is required outside debug mode; debug-only runs without it receive a process-local random key rather than a source-controlled fallback. The custom user model uses Django password hashing through `set_password`; plaintext passwords are never persisted. Email is the login identifier and role, department, clearance level, activity state, and audit timestamps are stored on the user record.

## Known limitations

The PostgreSQL connection, applied migrations, and authentication API test suite have been verified. Token revocation depends on the database-backed Simple JWT blacklist. No document endpoints, encryption, audit chaining, or machine-learning claims have been implemented yet.

See `docs/` for architecture and data design, and `IMPLEMENTATION_LOG.md` for a chronological record.
