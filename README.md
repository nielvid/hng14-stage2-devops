# hng14-stage2-devops

A containerised job-processing stack: a Node.js frontend, a FastAPI backend, a Python worker, and Redis — all wired together with Docker Compose and a GitHub Actions CI/CD pipeline.

---

## Architecture

```
Browser → Frontend (Node/Express :3000)
               ↓  HTTP
           API (FastAPI :8000)
               ↓  Redis queue
          Worker (Python)
               ↓
            Redis (internal only)
```

All four services run on a single internal Docker bridge network. Redis is never exposed to the host. The frontend is the only service with a host port binding.

---

## Prerequisites

| Tool | Minimum version | Install |
|---|---|---|
| Docker | 24.x | https://docs.docker.com/get-docker/ |
| Docker Compose | v2 (bundled with Docker Desktop) | included above |
| Git | any | https://git-scm.com/ |

Verify:

```bash
docker --version        # Docker version 24.x.x
docker compose version  # Docker Compose version v2.x.x
```

No cloud account, no Kubernetes, no extra tooling required.

---

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/nielvid/hng14-stage2-devops.git
cd hng14-stage2-devops
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Open `.env` and fill in any values you want to override. The defaults work out of the box for local development — you only **must** set `API_URL` if you change the service names.

```
# .env (minimum for local dev — defaults already set in compose)
FRONTEND_PORT=3000
API_URL=http://api:8000
```

### 3. Build and start the stack

```bash
docker compose up --build -d
```

This will:
1. Build the `api`, `worker`, and `frontend` images from their respective Dockerfiles.
2. Pull `redis:7-alpine`.
3. Start Redis first, wait for it to be healthy.
4. Start `api` and `worker` once Redis is healthy.
5. Start `frontend` once `api` is healthy.

### 4. Verify everything is running

```bash
docker compose ps
```

Expected output (all services `healthy` or `running`):

```
NAME                IMAGE               STATUS                   PORTS
...-redis-1         redis:7-alpine      Up X seconds (healthy)
...-api-1           ...-api             Up X seconds (healthy)
...-worker-1        ...-worker          Up X seconds (healthy)
...-frontend-1      ...-frontend        Up X seconds (healthy)   0.0.0.0:3000->3000/tcp
```

### 5. Use the application

Open your browser at **http://localhost:3000**.

- Click **Submit New Job** — a job ID appears and its status starts as `queued`.
- Within ~3 seconds the worker processes it and the status updates to `completed`.

You can also hit the API directly:

```bash
# Create a job
curl -X POST http://localhost:8000/jobs

# Check a job (replace <job_id>)
curl http://localhost:8000/jobs/<job_id>

# Health check
curl http://localhost:8000/health
```

### 6. View logs

```bash
docker compose logs -f            # all services
docker compose logs -f worker     # worker only
```

### 7. Tear down

```bash
docker compose down -v            # stops containers and removes volumes
```

---

## Project structure

```
.
├── api/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
│       ├── conftest.py
│       └── test_main.py
├── worker/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── worker.py
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── app.js
│   ├── config.js
│   ├── eslint.config.js
│   ├── package.json
│   └── views/
│       └── index.html
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── FIXES.md
```

Each service directory contains a `.dockerignore` that prevents virtual environments, caches, test files, `.env` files, and other dev artifacts from being included in the Docker build context.

---

## Running tests locally

```bash
cd api
pip install -r requirements.txt
pytest tests/ --cov=. --cov-report=term
```

Expected output:

```
tests/test_main.py .....                                    [100%]

---------- coverage: platform ... ----------
Name       Stmts   Miss  Cover
-------------------------------
main.py       14      0   100%
TOTAL         14      0   100%

5 passed in 0.XXs
```

---

## CI/CD pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and PR. Stages run in strict order — a failure stops all subsequent stages:

| Stage | Trigger | What it does |
|---|---|---|
| `lint` | every push/PR | flake8 (Python), eslint (JS), hadolint (Dockerfiles) |
| `test` | after lint | pytest with mocked Redis, uploads `coverage.xml` artifact |
| `build` | after test | builds all 3 images, tags `<git-sha>` + `latest`, pushes to in-job registry |
| `security` | after build | Trivy scans all images, fails on any CRITICAL CVE, uploads SARIF artifact |
| `integration` | after security | brings full stack up inside runner, submits a job, polls until `completed`, tears down |
| `deploy` | `main` branch only | rolling update over SSH — new container must pass health check within 60 s before old one is stopped |

### Deploy stage

The deploy stage runs on `main` branch pushes only, entirely within the GitHub Actions runner — no external server or cloud account required. It:

1. Builds fresh images tagged with the git SHA
2. Starts the full stack with `docker compose up`
3. Performs a rolling update — replaces each service one at a time, waiting up to 60 seconds for the new container to pass its health check before stopping the old one
4. Verifies the frontend is serving traffic
5. Tears the stack down cleanly

No secrets are required for the deploy stage.

---

## Environment variables reference

See `.env.example` for the full list. All variables have safe defaults for local development.

| Variable | Default | Description |
|---|---|---|
| `REDIS_HOST` | `redis` | Hostname of the Redis service |
| `API_URL` | `http://api:8000` | URL the frontend uses to reach the API |
| `FRONTEND_PORT` | `3000` | Host port mapped to the frontend container |
| `REDIS_CPU_LIMIT` | `0.25` | CPU limit for Redis |
| `REDIS_MEM_LIMIT` | `128m` | Memory limit for Redis |
| `API_CPU_LIMIT` | `0.50` | CPU limit for the API |
| `API_MEM_LIMIT` | `256m` | Memory limit for the API |
| `WORKER_CPU_LIMIT` | `0.50` | CPU limit for the worker |
| `WORKER_MEM_LIMIT` | `256m` | Memory limit for the worker |
| `FRONTEND_CPU_LIMIT` | `0.50` | CPU limit for the frontend |
| `FRONTEND_MEM_LIMIT` | `256m` | Memory limit for the frontend |
