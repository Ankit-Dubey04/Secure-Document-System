# Zero-Trust Secure Document Management System with AI-Based Anomaly Detection

An academic full-stack project for securely storing and governing sensitive documents under zero-trust principles. It will combine Django REST APIs, a React interface, encrypted document storage, SHA-256 integrity verification, tamper-evident audit records, role-based access control, and explainable anomaly detection.

## Current status

- **Completed:** Phase 1 project scaffolding; verified PostgreSQL configuration via environment variables; custom email-based user model; Django REST Framework foundation; applied initial user migration; user-model test.
- **In progress:** Phase 2 authentication and role-based access control.
- **Planned:** Document storage and encryption, audit hash chain, anomaly detection, React UI, Docker, and comprehensive tests.

## Technology stack

| Technology | Purpose |
| --- | --- |
| Python 3.14.3 / Django 6.1.1 | Secure backend and ORM |
| Django REST Framework 3.18.1 | REST API foundation |
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

Dependencies are pinned in `backend/requirements.txt`. The API currently defaults to authenticated access globally; the health endpoint is deliberately a small public readiness endpoint. JWT endpoints are planned for Phase 2.

## Security baseline

Configuration secrets and database credentials are read from environment variables. `.env` is ignored by Git. The custom user model uses Django password hashing through `set_password`; plaintext passwords are never persisted. Email is the login identifier and role, department, clearance level, activity state, and audit timestamps are stored on the user record.

## Known limitations

The PostgreSQL connection, applied user migration, and user-model test have been verified. No document endpoints, encryption, audit chaining, or machine-learning claims have been implemented yet.

See `docs/` for architecture and data design, and `IMPLEMENTATION_LOG.md` for a chronological record.
