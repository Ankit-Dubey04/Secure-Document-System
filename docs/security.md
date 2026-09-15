# Security Notes

Phase 1 avoids embedding secrets in source code. Database credentials and the Django secret key are externalized through environment variables, and `.env` is ignored. Passwords are passed to Django's `set_password`, which stores a salted password hash rather than the submitted value.

The default REST permission requires authentication. JWT authentication, RBAC policy enforcement, authenticated document encryption, integrity verification, audit-chain implementation, and anomaly detection are planned modules—not current security claims.

Phase 1 verification confirmed the custom user model is active and password writes use Django's hashing API. The test suite created an isolated test database and removed it after completion; it did not use application document data.
