# Database Design

## Current schema

The initial migration creates the `authentication_user` table in the existing PostgreSQL database `secure_document_db`. Migration `authentication.0001_initial` is applied and the connection was verified through Django's database backend.

| Field | Purpose |
| --- | --- |
| `id` | Django primary key |
| `email` | Unique email login identifier |
| `password` | Django-generated password hash, never plaintext |
| `name` | User display/legal name |
| `role` | Administrator, Manager, Employee, or Auditor |
| `department` | Organizational scope for future access policies |
| `clearance_level` | Public, Internal, Confidential, or Restricted |
| `account_active` | Application-level account state |
| `created_at`, `updated_at` | Lifecycle timestamps |

Django's inherited authorization fields (`is_staff`, `is_superuser`, groups, and permissions) remain available for administrative use. `email` is unique and replaces Django's username as the authentication identifier.

## Document schema

`documents_document` uses a UUID primary key to make identifiers non-sequential. It stores title, optional description, controlled document type and classification choices, the private storage reference, original filename, file size, declared content type, active/deleted state, and creation/update timestamps.

Every document has a protected foreign-key owner and optional protected `updated_by` user. Indexes support owner/active and classification/active authorization queries. The binary is not stored in PostgreSQL. Soft deletion sets `is_active=False`, preserving metadata for later audit capabilities while excluding the document from all normal querysets.

Classification choices are Public, Internal, Confidential, and Restricted. Types are FIR, Charge Sheet, Witness Statement, Forensic Report, Court Filing, and Other. Client requests cannot set owner, file-derived metadata, timestamps, or the active state through the serializer.

Phase 4 adds `plaintext_sha256` (lowercase 64-character original-content digest), `encryption_algorithm`, `encryption_nonce`, `is_encrypted`, and `integrity_verified_at`. The existing file reference now points to AES-GCM ciphertext, not plaintext. The nonce and algorithm are non-secret metadata necessary for decryption; the encryption key is not a database field. Existing Phase 3 records default to unencrypted and are not eligible for secure download until reprocessed.

`audit_auditlog` stores UUID events, timestamp, optional user, controlled event/outcome, resource fields, direct remote IP, bounded user agent, sanitized selected metadata, and previous/current chain hashes. `audit_auditchainstate` is a single locked state row used to serialize ordinary appends.

Audit records are application-append-only: no create/update/delete API exists, and Django admin disables normal mutations for both the event and state models. Database-level append-only permissions are not part of this MVP.

## Anomaly result schema

`anomaly_detection_anomalydetectionresult` stores advisory output rather than raw model artifacts. It has a foreign key to the subject user, bounded aggregation `window_start`/`window_end`, a floating-point Isolation Forest decision score, `NORMAL`/`ANOMALOUS` classification, model and feature-schema versions, safe aggregate feature summary, detection timestamp, and review flag. The unique constraint on `(subject_user, window_start, window_end, model_version)` makes re-running the same daily-bounded window idempotent. An index on classification/detection timestamp supports security review queries.

No password, token, encryption key, audit metadata, document body, or serialized model is stored in this table. The initial schema is supplied by `anomaly_detection.0001_initial`.

## Planned relations

Future explicit document permissions, security events, and activities will reference users and resources through foreign keys or controlled identifiers.
