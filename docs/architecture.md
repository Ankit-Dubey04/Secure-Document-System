# Architecture

## Phase 1 backend architecture

The project uses a modular Django monolith with Django REST Framework at its API boundary and PostgreSQL as its system of record. It is intentionally separated by responsibility:

- `authentication`: user identity, roles, login/JWT flows (JWT pending).
- `documents`: document metadata, encrypted storage, and authorization (pending).
- `audit`: append-only, hash-linked operational records (pending).
- `security`: authorization policies and security events (pending).
- `anomaly_detection`: behavioural feature generation and Isolation Forest integration (pending).

Configuration is read from the process environment, with a local `.env` convenience loader that never overrides supplied environment variables. The local `.env` is ignored by Git.

## Verification status

The backend has successfully connected to the configured local PostgreSQL server and the initial custom-user migration is applied. Phase 1 is complete. Database-backed authentication tests use Django's disposable `test_secure_document_db` database rather than modifying application data.

## Request path

`Client → Django URL routing → DRF view (future) → authorization check → domain app → PostgreSQL/encrypted storage (future) → audit event (future)`

Each sensitive future request will authenticate, authorize, validate input, execute the narrow operation, and emit an audit event. The health route is the only current public endpoint.
