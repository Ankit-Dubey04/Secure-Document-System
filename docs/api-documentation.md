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
| `/api/documents/` | GET | Active JWT | Lists only documents visible to the caller's role and object policy. |
| `/api/documents/` | POST | Active JWT; Administrator, Manager, or Employee | Creates a document owned by the JWT user. Multipart form data requires `title`, `document_type`, `classification`, and `file`; `description` is optional. |
| `/api/documents/<uuid>/` | GET | Active JWT + object policy | Returns authorized metadata only; no storage path or file download URL. |
| `/api/documents/<uuid>/` | PUT/PATCH | Active JWT + manager policy | Updates authorized metadata/file. Employee owners may manage only their own documents. |
| `/api/documents/<uuid>/` | DELETE | Active JWT + manager policy | Soft-deletes an authorized document; returns 204. |
| `/api/documents/<uuid>/download/` | GET | Active JWT + object policy | Decrypts and SHA-256 verifies an encrypted document before returning an attachment. Returns generic 422 without plaintext on cryptographic/integrity failure. |
| `/api/audit/` | GET | Administrator or Auditor JWT | Read-only audit events; supports exact server-side event/outcome/resource/user filters. |
| `/api/audit/verify/` | GET | Administrator or Auditor JWT | Returns safe hash-chain verification status. |
| `/api/anomalies/status/` | GET | Administrator or Auditor JWT | Returns safe model/version/status capabilities, not model internals. |
| `/api/anomalies/run/` | POST | Administrator or Auditor JWT | Runs advisory analysis for `window_days` 1–90 (default 7) and audits the operation. |
| `/api/anomalies/` | GET | Administrator or Auditor JWT | Lists up to 200 persisted safe anomaly results, newest first. |
| `/api/anomalies/<id>/` | GET | Administrator or Auditor JWT | Retrieves one persisted safe anomaly result. |

Audit APIs are read-only. Unauthorized authenticated audit requests are recorded as denied security events; unauthenticated requests return 401 without a user association. Audit response metadata is sanitized and does not include credentials, tokens, keys, cookies, or request bodies.

The anomaly run response contains `trained` with processed result count or `insufficient_data` when fewer than five active-user profiles exist. For trained data, lower scores are more anomalous and negative scores have the `ANOMALOUS` classification. Result data contains aggregate feature counts only. Invalid/non-numeric windows, or values outside 1–90, return 400; unauthenticated and unauthorized callers receive 401/403.

The UI prototype consumes the documented authentication, documents, audit, and admin-only users endpoints directly. It does not add a dashboard aggregation API: document counts are derived client-side from the caller's authorized document list, and audit/security panels use only the caller-authorized audit list.

## Planned API groups

`/api/security/` remains reserved for a later phase.

## Document request constraints

`classification` must be one of `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, or `RESTRICTED`; callers cannot exceed their clearance (except administrators). `document_type` must be one of `FIR`, `CHARGE_SHEET`, `WITNESS_STATEMENT`, `FORENSIC_REPORT`, `COURT_FILING`, or `OTHER`.

The API accepts PDF, DOC, DOCX, and ODT files only, requires the corresponding allowed MIME type, and limits payloads to 10 MiB. Typical errors are 400 (invalid upload/validation), 401 (missing/invalid JWT), 403 (visible document but role cannot modify it), and 404 (not visible under object policy).
