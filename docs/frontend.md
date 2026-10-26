# Frontend development

## Architecture

`frontend/` is a separate React 19 + TypeScript Vite application styled with Tailwind CSS. It is intentionally independent of the legacy Django-template prototype. A single API client centralizes the `/api` base path, bearer authorization, a 15-second request timeout, structured DRF error display, and one refresh-and-retry attempt after an expired access token.

The current Django backend returns JWT pairs in JSON and does not implement secure-cookie authentication. The client therefore keeps access/refresh tokens in `sessionStorage`, never in URLs, local storage, application logs, or source files. Tokens are removed on logout or failed refresh. This is a pragmatic current-backend compatibility choice, not XSS-proof storage; production should add a reviewed HttpOnly/SameSite cookie flow before handling higher-risk deployments.

Vite proxies `/api` to `http://127.0.0.1:8000` by default for local development. This avoids adding broad CORS settings to Django. In production, serve the built SPA and the API behind one trusted origin/reverse proxy. If a distinct frontend origin becomes necessary, add an explicit allow-list to Django rather than wildcard CORS.

## Local commands

From the repository root:

```powershell
venv\Scripts\python.exe backend\manage.py runserver
cd frontend
npm install
npm run dev
```

Open the Vite URL printed by the development server. Use `VITE_API_PROXY_TARGET` only to point the development proxy at another trusted local API origin. `VITE_API_BASE_URL` can be set for a same-origin deployment path; neither variable is a secret.

```powershell
cd frontend
npm test
npm run build
```

## Connected APIs and role behavior

The dashboard uses `/api/auth/login/`, `/token/refresh/`, `/logout/`, `/me/`, `/users/`; `/api/documents/` and authorized download URLs; `/api/audit/` and `/verify/`; and all implemented anomaly endpoints. It does not claim successful integrity verification except when the authorized download endpoint succeeds, and it renders the audit verifier's actual response.

Navigation is a usability filter only. The backend remains authoritative: Administrators and Auditors receive audit/anomaly navigation; only Administrators receive the user directory; Auditors do not receive upload navigation. Backend 401/403/422 responses are displayed rather than bypassed or reinterpreted.

## Test scope and limitations

Vitest tests session-only token storage, expired-token refresh/retry, and role-aware navigation. The Vite build type-checks and bundles the application. Browser end-to-end tests against a live Django server and HttpOnly-cookie auth are not yet implemented. The previous Django-template UI is intentionally preserved and is not used by the React application.
