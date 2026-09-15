# Security Notes

Phase 1 avoids embedding secrets in source code. Database credentials and the Django secret key are externalized through environment variables, and `.env` is ignored. Passwords are passed to Django's `set_password`, which stores a salted password hash rather than the submitted value.

The default REST permission requires authentication. JWT authentication, RBAC policy enforcement, authenticated document encryption, integrity verification, audit-chain implementation, and anomaly detection are planned modules—not current security claims.
