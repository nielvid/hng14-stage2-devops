# FIXES.md

Every bug found in the original codebase, in the order they were discovered.

---

## Bug 1 — `.env` committed to source control

| Field | Detail |
|---|---|
| **File** | `.env` (repo root) |
| **Line** | entire file |
| **Problem** | The `.env` file containing real configuration values was committed to the repository. Any secret placed there would be permanently exposed in git history. |
| **Fix** | Added `.env` to `.gitignore`. Created `.env.sample` (later renamed `.env.example`) with placeholder values so contributors know what variables are required without exposing real values. |

---

## Bug 2 — `.env` placed inside `api/` directory

| Field | Detail |
|---|---|
| **File** | `api/.env` |
| **Line** | entire file |
| **Problem** | A second `.env` was nested inside `api/`, making it easy to accidentally copy into a Docker image via a broad `COPY . .` instruction. |
| **Fix** | Removed the file from `api/`. All configuration is now passed via environment variables at runtime through Docker Compose. |

---

## Bug 3 — `API_URL` hardcoded to `localhost` in frontend

| Field | Detail |
|---|---|
| **File** | `frontend/app.js` |
| **Line** | 6 (original) |
| **Problem** | `const API_URL = 'http://localhost:8000'` — inside a container `localhost` refers to the container itself, not the API service. Every proxied request to the API would fail with a connection refused error. |
| **Fix** | Extracted all runtime config into `frontend/config.js`. `apiUrl` reads from `process.env.API_URL` with a fallback, and `docker-compose.yml` injects `API_URL=http://api:8000` so the frontend resolves the API by its service name on the internal network. |

---

## Bug 4 — Frontend port hardcoded to `3000`

| Field | Detail |
|---|---|
| **File** | `frontend/app.js` |
| **Line** | 30–31 (original) |
| **Problem** | `app.listen(3000, ...)` — the port was a magic number. Running multiple instances or changing the port required editing source code. |
| **Fix** | `app.listen(config.appPort, ...)` where `config.appPort` reads `process.env.APP_PORT \|\| 3000`. The Compose file sets `APP_PORT=3000` explicitly, making the binding visible and overridable. |

---

## Bug 5 — Redis host hardcoded to `localhost` in API

| Field | Detail |
|---|---|
| **File** | `api/main.py` |
| **Line** | 8 (original) |
| **Problem** | `redis.Redis(host='localhost', port=6379)` — inside the API container `localhost` is not Redis. The connection would fail immediately on startup. |
| **Fix** | Changed to `redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)`. The Compose file injects `REDIS_HOST=redis`. |

---

## Bug 6 — Redis host hardcoded to `localhost` in worker

| Field | Detail |
|---|---|
| **File** | `worker/worker.py` |
| **Line** | 6 (original) |
| **Problem** | Same as Bug 5 — `redis.Redis(host='localhost')` fails inside a container. |
| **Fix** | Changed to `redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379)`. |

---

## Bug 7 — `signal` imported but graceful shutdown never wired up

| Field | Detail |
|---|---|
| **File** | `worker/worker.py` |
| **Line** | 4, 11–16 (original) |
| **Problem** | `signal` was imported and `shutdown_handler` was defined, but `signal.signal(...)` was never called. Docker sends `SIGTERM` when stopping a container; without a handler the process would be killed immediately, potentially mid-job. |
| **Fix** | Added `signal.signal(signal.SIGINT, shutdown_handler)` and `signal.signal(signal.SIGTERM, shutdown_handler)` so the worker finishes the current job before exiting. |

---

## Bug 8 — No `/health` endpoint on the API

| Field | Detail |
|---|---|
| **File** | `api/main.py` |
| **Line** | — (missing) |
| **Problem** | The Dockerfile `HEALTHCHECK` and the Compose `depends_on: condition: service_healthy` both require a health endpoint. Without one, the health check would always fail, blocking the frontend from ever starting. |
| **Fix** | Added `GET /health` returning `{"status": "ok"}` at line 11 of `api/main.py`. |

---

## Bug 9 — No `.dockerignore` in any service directory

| Field | Detail |
|---|---|
| **Files** | `api/`, `worker/`, `frontend/` — all missing |
| **Line** | — (missing) |
| **Problem** | Without a `.dockerignore`, the Docker build context sent to the daemon includes everything in the service directory: virtual environments, `node_modules`, test files, `.env` files, `__pycache__`, coverage reports, and `.git` metadata. This bloats the build context, slows builds, and risks copying sensitive files (e.g. a local `.env`) into the image. |
| **Fix** | Added a `.dockerignore` to each service directory. Each file excludes: dev/editor artifacts (`.env`, `.env.*`, `*.md`, `.git`, `.gitignore`, `Dockerfile`), language-specific cache and build output (`__pycache__`, `*.pyc`, `node_modules`), and test/coverage artifacts (`tests/`, `.coverage`, `coverage.xml`, `.pytest_cache`, `eslint.config.js`). |

---

## Bug 10 — PEP 8 violations in `api/main.py` and `worker/worker.py`

| Field | Detail |
|---|---|
| **Files** | `api/main.py`, `worker/worker.py` |
| **Lines** | `main.py` 15, 22 — `worker.py` 11, 17, 20, 26, 31, 33 |
| **Problem** | Multiple flake8 violations: missing two blank lines between top-level function definitions (E302), missing two blank lines after a function before module-level code (E305), a blank line containing trailing whitespace (W293), and no newline at end of file (W292). |
| **Fix** | Added the required blank lines between all top-level definitions in both files, removed trailing whitespace from the blank line inside the `while` loop in `worker.py`, and added a trailing newline at end of file. |

---

## Bug 11 — ESLint config used ESM syntax in a CommonJS package

| Field | Detail |
|---|---|
| **File** | `frontend/eslint.config.js` |
| **Line** | 1 |
| **Problem** | `eslint.config.js` used `export default [...]` (ESM) but `package.json` has no `"type": "module"`, so Node treats all `.js` files as CommonJS. ESLint failed to parse its own config with: `Parsing error: 'import' and 'export' may appear only with 'sourceType: module'`. |
| **Fix** | Changed `export default [...]` to `module.exports = [...]` to match the package's CommonJS module type. |

---

## Bug 12 — ESLint linted its own config file and failed

| Field | Detail |
|---|---|
| **File** | `frontend/eslint.config.js` |
| **Line** | 1 |
| **Problem** | ESLint attempted to lint `eslint.config.js` itself. The file uses `module` which was not listed in the declared globals, causing a `no-undef` error. |
| **Fix** | Added `ignores: ["eslint.config.js"]` to the config so ESLint skips linting its own config file. |

---

## Bug 13 — Unused `err` variables in catch blocks

| Field | Detail |
|---|---|
| **File** | `frontend/app.js` |
| **Lines** | 17, 26 |
| **Problem** | Both `catch (err)` blocks never referenced `err` — the handler only returns a generic error response. This triggered the `no-unused-vars` ESLint rule. |
| **Fix** | Renamed both to `_err`. The underscore prefix is the conventional signal for an intentionally unused variable and is recognised by `no-unused-vars` as an allowed pattern. |
