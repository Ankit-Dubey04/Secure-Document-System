# Architecture

## Phase 1 backend architecture

The project uses a modular Django monolith with Django REST Framework at its API boundary and PostgreSQL as its system of record. It is intentionally separated by responsibility:

- `authentication`: user identity, JWT login/refresh/logout/profile APIs, and reusable role policies.
- `documents`: private storage references, metadata, upload validation, soft deletion, and object-level authorization.
- `audit`: append-only, hash-linked operational records.
- `security`: authorization policies and security events (pending).
- `anomaly_detection`: audit-derived behavioural features, Isolation Forest analysis, and advisory result APIs.

Configuration is read from the process environment, with a local `.env` convenience loader that never overrides supplied environment variables. The local `.env` is ignored by Git.

## Verification status

The backend has successfully connected to the configured local PostgreSQL server and the initial custom-user migration is applied. Phase 1 is complete. Database-backed authentication tests use Django's disposable `test_secure_document_db` database rather than modifying application data.

## Request path

`Client → Django URL routing → DRF JWT authentication → active-account/RBAC + object policy → document API → upload validation → PostgreSQL metadata + private file storage`

JWT access tokens authenticate protected requests. `IsActiveUser` requires that the corresponding user record is still active, while role-specific policies build on that condition. The Simple JWT blacklist tables persist revoked refresh-token records. Login and token refresh are public by necessity; the health route remains public for readiness checks.

Phase 4 adds: `Client → JWT → RBAC/object authorization → upload validation → SHA-256 plaintext hash → AES-256-GCM encryption → encrypted private storage + cryptographic metadata in PostgreSQL`. Retrieval is `Client → JWT → RBAC/object authorization → ciphertext → authenticated decryption → SHA-256 comparison → plaintext response`. No media URL route is configured.

Phase 5 appends meaningful authentication/document/security outcomes through `Application event → Audit service → canonical event data → previous hash → SHA-256 → AuditLog`. The audit service locks its chain-state row in a transaction to serialize application writes. Audit records then provide structured input for a later anomaly-detection module.

Login outcomes, refresh/logout, document lifecycle and secure retrieval outcomes enter this audit flow only after their relevant application result is known. Successful document mutations and their audit append share a database transaction; failed authentication, authorization denials, and integrity failures are independently recorded. Audit APIs are read-only and restricted to Administrators/Auditors.

## Phase 6 anomaly-analysis path

`Authorized Administrator/Auditor → POST /api/anomalies/run/ → bounded audit-event aggregation → fixed numeric feature matrix → IsolationForest → atomic AnomalyDetectionResult upsert → safe result API`. Only active users are profiled; five or more profiles are required to train. A run is written to the audit chain as a `SYSTEM_EVENT`, but query aggregation excludes those `AnomalyDetection` records so running analysis cannot feed its own operational event back into a future behavioural profile.

The service trains only on explicit authorized run requests, not status/list/detail reads. It uses `audit-profile-v1`, `isolation-forest-v1`, deterministic feature order, configured contamination/random-state settings, and a process-memory cache for status only. The model itself is never exposed, serialized, or loaded from user input. Results are transactionally upserted by subject/window/model version and remain advisory.

## UI prototype

`Django template shell → vanilla JavaScript → existing JWT REST APIs → existing authorization/document/audit services`. The UI contains no cryptographic or authorization business logic. Role-aware navigation is a usability layer only; backend APIs remain the authority. Static source assets are in `backend/static/ui/`, templates in `backend/templates/ui/`, and collected deployment assets use `STATIC_ROOT`.
