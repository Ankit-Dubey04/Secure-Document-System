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

## Planned relations

Future explicit document permissions, audit entries, security events, activities, and anomaly results will reference users and resources through foreign keys or controlled identifiers.
