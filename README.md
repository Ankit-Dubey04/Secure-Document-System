# Zero-Trust Secure Document Management System with AI-Based Anomaly Detection

An academic full-stack project for securely storing and governing sensitive documents under zero-trust principles. It combines Django REST APIs, a Django-template presentation UI, encrypted document storage, SHA-256 integrity verification, tamper-evident audit records, role-based access control, and explainable anomaly detection.

## Current status

- **Completed:** Phases 1–6: foundation, JWT/RBAC, encrypted document retrieval, tamper-evident audit logging, and advisory anomaly detection.
- **In progress:** Django-template UI prototype for presentation.
- **Planned:** Docker and deployment tests.

## Technology stack

| Technology | Purpose |
| --- | --- |
| Python 3.14.3 / Django 6.1.1 | Secure backend and ORM |
| Django REST Framework 3.18.1 / Simple JWT 5.5.1 | REST API and JWT authentication |
| PostgreSQL 18.6 / psycopg 3.3.5 | Relational persistence |
| Django templates, CSS, vanilla JavaScript | Presentation-ready UI prototype |
| scikit-learn 1.9.1 | Isolation Forest anomaly detection |

## Project layout

```text
backend/                 Django project and applications
  apps/authentication/   Custom user identity and future JWT flows
  apps/documents/        Secure document metadata, upload validation, and access control
  apps/audit/            Tamper-evident audit records
  apps/security/         Security policy/events (planned)
  apps/anomaly_detection/ Audit-derived anomaly detection and result APIs
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

Administrators may list user profiles. Reusable permissions define the following policy: all active roles can access permitted documents; Managers and Administrators can manage documents; Administrators and Auditors can read audit logs, security data, and anomaly data. Anomaly result and analysis APIs are available only to the latter two roles.

## Secure document management

`/api/documents/` supports authenticated document creation and authorized listing; `/api/documents/<uuid>/` supports authorized retrieval, updates, and soft deletion. Files are stored through Django storage under generated server-side names, while PostgreSQL stores metadata only. No media route is registered, and Phase 3 does not expose download URLs.

Uploads accept PDF, DOC, DOCX, and ODT only, with matching declared MIME type, a non-empty payload, a 10 MiB maximum, and a filename free of path components. Client owner fields are ignored; the JWT principal is always recorded as owner. See the API and security documentation for the role/object policy.

## Security baseline

Configuration secrets and database credentials are read from environment variables. `.env` is ignored by Git. `DJANGO_SECRET_KEY` is required outside debug mode; debug-only runs without it receive a process-local random key rather than a source-controlled fallback. The custom user model uses Django password hashing through `set_password`; plaintext passwords are never persisted. Email is the login identifier and role, department, clearance level, activity state, and audit timestamps are stored on the user record.

## Encrypted storage and retrieval

New uploads are SHA-256 hashed as plaintext, encrypted with AES-256-GCM using a fresh 96-bit nonce, and stored only as ciphertext. `GET /api/documents/<uuid>/download/` is JWT- and object-authorization-bound; it decrypts and compares the resulting plaintext hash before returning a download. A failed authenticated decryption or hash check returns no plaintext.

Set `DOCUMENT_ENCRYPTION_KEY` only in the ignored local environment configuration as a Base64-url encoded 32-byte key. Production deployments should use managed secrets, per-key document key wrapping, and rotation rather than a single application key.

## Tamper-evident auditing

Meaningful authentication and document actions are recorded by a server-side append-only audit service. Each event has deterministic canonical JSON and a SHA-256 hash linked to the immediately preceding event, beginning with `GENESIS`. Administrator and Auditor roles can list events and verify the chain through `/api/audit/` and `/api/audit/verify/`; there are no write, update, or delete audit APIs. Audit records and chain state are read-only in Django admin.

## Advisory anomaly detection

`scikit-learn` Isolation Forest builds one profile per active user over a requested 1–90 day window (seven days by default). Its fixed `audit-profile-v1` feature order is total non-analysis events, successful/failed logins, document views/downloads/mutations, denied attempts, unique document IDs, and events outside 06:00–21:59 in `Asia/Kolkata`. Passwords, tokens, keys, raw audit metadata, and document contents are never features or returned output.

An authorized Administrator or Auditor can run `POST /api/anomalies/run/`, check `/api/anomalies/status/`, and list/retrieve read-only results at `/api/anomalies/`. Training requires at least five active-user profiles; otherwise it explicitly returns `insufficient_data` and writes no results. Lower Isolation Forest decision scores are more anomalous; a negative score receives `ANOMALOUS`. Results are advisory only: they never disable users, block documents, or alter RBAC. The configured contamination (default `0.15`) and random seed (default `42`) are non-secret environment settings, and the in-memory model is not serialized.

## UI prototype

The root route serves a Django template shell with a secure login, dashboard, document upload/list/detail/download workflow, profile, role-aware navigation, audit-chain verification, security overview, and read-only user list. It uses the existing REST APIs; JWTs are held only in browser session storage, while all authorization, encryption, and audit generation remain server-side. The Security page remains an audit-focused UI view; anomaly analysis is performed through its protected API.

## Known limitations

The MVP reads plaintext into process memory during encryption/decryption and uses one application-level key. The audit hash chain is tamper-evident rather than immutable against a database administrator who can rewrite both events and chain state. Isolation Forest is unsupervised and has no labelled accuracy evaluation, persisted cross-process model artifact, automatic retraining schedule, or automated enforcement action. It has no malware scanning, key rotation/KMS, streamed encryption, or external audit checkpointing. Legacy Phase 3 documents remain marked unencrypted and cannot use the secure download endpoint until re-uploaded.

See `docs/` for architecture and data design, and `IMPLEMENTATION_LOG.md` for a chronological record.
