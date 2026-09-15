# Architecture

## Phase 1 backend architecture

The project uses a modular Django monolith with Django REST Framework at its API boundary and PostgreSQL as its system of record. It is intentionally separated by responsibility:

- `authentication`: user identity, JWT login/refresh/logout/profile APIs, and reusable role policies.
- `documents`: private storage references, metadata, upload validation, soft deletion, and object-level authorization.
- `audit`: append-only, hash-linked operational records (pending).
- `security`: authorization policies and security events (pending).
- `anomaly_detection`: behavioural feature generation and Isolation Forest integration (pending).

Configuration is read from the process environment, with a local `.env` convenience loader that never overrides supplied environment variables. The local `.env` is ignored by Git.

## Verification status

The backend has successfully connected to the configured local PostgreSQL server and the initial custom-user migration is applied. Phase 1 is complete. Database-backed authentication tests use Django's disposable `test_secure_document_db` database rather than modifying application data.

## Request path

`Client → Django URL routing → DRF JWT authentication → active-account/RBAC + object policy → document API → upload validation → PostgreSQL metadata + private file storage`

JWT access tokens authenticate protected requests. `IsActiveUser` requires that the corresponding user record is still active, while role-specific policies build on that condition. The Simple JWT blacklist tables persist revoked refresh-token records. Login and token refresh are public by necessity; the health route remains public for readiness checks.

Phase 4 adds: `Client → JWT → RBAC/object authorization → upload validation → SHA-256 plaintext hash → AES-256-GCM encryption → encrypted private storage + cryptographic metadata in PostgreSQL`. Retrieval is `Client → JWT → RBAC/object authorization → ciphertext → authenticated decryption → SHA-256 comparison → plaintext response`. No media URL route is configured. Audit chaining and anomaly detection remain later phases.

Phase 5 appends meaningful authentication/document/security outcomes through `Application event → Audit service → canonical event data → previous hash → SHA-256 → AuditLog`. The audit service locks its chain-state row in a transaction to serialize application writes. Audit records then provide structured input for a later anomaly-detection module.

Login outcomes, refresh/logout, document lifecycle and secure retrieval outcomes enter this audit flow only after their relevant application result is known. Successful document mutations and their audit append share a database transaction; failed authentication, authorization denials, and integrity failures are independently recorded. Audit APIs are read-only and restricted to Administrators/Auditors.
