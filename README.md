# Zero-Trust Secure Document Management System with AI-Based Anomaly Detection

An academic full-stack project for securely storing and governing sensitive documents under zero-trust principles. It will combine Django REST APIs, a React interface, encrypted document storage, SHA-256 integrity verification, tamper-evident audit records, role-based access control, and explainable anomaly detection.

## Current status

- **Completed:** Phases 1–5: foundation, JWT/RBAC, encrypted document retrieval, and tamper-evident audit logging.
- **Planned:** Anomaly detection, React UI, Docker, and deployment tests.

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
  apps/documents/        Secure document metadata, upload validation, and access control
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

## Known limitations

The MVP reads plaintext into process memory during encryption/decryption and uses one application-level key. The audit hash chain is tamper-evident rather than immutable against a database administrator who can rewrite both events and chain state. It has no malware scanning, key rotation/KMS, streamed encryption, external audit checkpointing, or anomaly detection. Legacy Phase 3 documents remain marked unencrypted and cannot use the secure download endpoint until re-uploaded.

See `docs/` for architecture and data design, and `IMPLEMENTATION_LOG.md` for a chronological record.
