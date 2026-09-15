# Security Notes

The application avoids embedding secrets in source code. Database credentials and the Django secret key are externalized through environment variables, and `.env` is ignored. `DJANGO_SECRET_KEY` is mandatory outside debug mode. If it is absent during debug-only development, Django receives a fresh process-local random key; this is not suitable for persistent sessions or production. Passwords are passed to Django's `set_password`, which stores a salted password hash rather than the submitted value.

The default REST permission requires a valid JWT for an application account with `account_active=True`. Access and refresh tokens are issued by Simple JWT; access tokens default to 15 minutes, refresh tokens default to one day, and both lifetimes are environment-configurable. Refresh token rotation and database-backed blacklisting are enabled. Logout blacklists the presented refresh token, preventing its further use to obtain access tokens.

Email/password login still delegates password verification to Django's authentication backend and never serializes password fields. Profile and user-administration serializers return an explicit allow-list of non-secret fields.

RBAC is centralized in `apps.authentication.permissions`: Administrator-only user administration; all active roles may access future authorized documents; Manager/Administrator document management; Administrator/Auditor audit, security, and anomaly visibility. Document encryption, integrity verification, audit chaining, and anomaly detection are still planned modules—not current security claims.

## Phase 3 document controls

All document endpoints require JWT authentication and an active account. The backend assigns ownership from the JWT user; payload owner identifiers are read-only and ignored. Querysets enforce object visibility, preventing an identifier change from revealing inaccessible metadata.

- Administrators can read and manage all active documents.
- Managers can read and manage documents owned by users in their non-empty department.
- Employees can read their own and Public documents; they can create documents and manage only their own.
- Auditors can read their own plus Public, Internal, and Confidential documents, but cannot create, update, or delete them. Restricted documents are not visible unless owned.

Uploads allow PDF (`application/pdf`), DOC (`application/msword`), DOCX (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`), and ODT (`application/vnd.oasis.opendocument.text`) up to 10 MiB. Empty files, unsupported extensions, and extension/MIME mismatches are rejected. Django normalizes multipart filenames; the API also rejects path separators if present and never uses the client filename for storage paths. Generated names avoid collisions and API serializers do not expose the storage path.

This is a validation baseline only: declared MIME type does not prove file safety, and no malware/content scanning is performed. Files are not encrypted or integrity-hashed until the next security phase. There is intentionally no download endpoint or public media route until authorization-bound secure serving and cryptographic protections are added.

Phase 1 verification confirmed the custom user model is active and password writes use Django's hashing API. The test suite created an isolated test database and removed it after completion; it did not use application document data.
