# API Documentation

## Implemented

| Endpoint | Method | Authentication | Description |
| --- | --- | --- | --- |
| `/api/health/` | GET | No | Returns a minimal service readiness response. |
| `/api/auth/login/` | POST | No | Accepts `email` and `password`; returns JWT access and refresh tokens for an active account. |
| `/api/auth/token/refresh/` | POST | No | Accepts a valid refresh token and returns a new access token (and rotated refresh token when configured). |
| `/api/auth/logout/` | POST | Active JWT | Accepts the caller's refresh token and blacklists it. Returns 204. |
| `/api/auth/me/` | GET | Active JWT | Returns the caller's non-sensitive profile fields. |
| `/api/auth/users/` | GET | Administrator JWT | Lists non-sensitive user profiles for administration. |

## Planned API groups

`/api/documents/`, `/api/audit/`, `/api/security/`, and `/api/anomalies/` remain reserved for later phases. Their Phase 2 role policies are implemented but no placeholder endpoints have been exposed.
