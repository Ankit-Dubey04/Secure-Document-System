# Security Notes

The application avoids embedding secrets in source code. Database credentials and the Django secret key are externalized through environment variables, and `.env` is ignored. `DJANGO_SECRET_KEY` is mandatory outside debug mode. If it is absent during debug-only development, Django receives a fresh process-local random key; this is not suitable for persistent sessions or production. Passwords are passed to Django's `set_password`, which stores a salted password hash rather than the submitted value.

The default REST permission requires a valid JWT for an application account with `account_active=True`. Access and refresh tokens are issued by Simple JWT; access tokens default to 15 minutes, refresh tokens default to one day, and both lifetimes are environment-configurable. Refresh token rotation and database-backed blacklisting are enabled. Logout blacklists the presented refresh token, preventing its further use to obtain access tokens.

Email/password login still delegates password verification to Django's authentication backend and never serializes password fields. Profile and user-administration serializers return an explicit allow-list of non-secret fields.

RBAC is centralized in `apps.authentication.permissions`: Administrator-only user administration; all active roles may access future authorized documents; Manager/Administrator document management; Administrator/Auditor audit, security, and anomaly visibility. Document encryption, integrity verification, audit chaining, and anomaly detection are still planned modules—not current security claims.

Phase 1 verification confirmed the custom user model is active and password writes use Django's hashing API. The test suite created an isolated test database and removed it after completion; it did not use application document data.
