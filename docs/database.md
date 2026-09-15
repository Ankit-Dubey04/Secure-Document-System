# Database Design

## Current schema

The initial migration creates the `authentication_user` table in the existing PostgreSQL database `secure_document_db`.

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

## Planned relations

Documents will belong to an owner and department; document permissions will represent explicit grants. Audit entries, security events, activities, and anomaly results will reference users and resources through foreign keys or controlled identifiers. These tables are deliberately deferred until the custom user migration has been applied successfully.
