# Deployment guide

## Recommended topology

Deploy the Next.js frontend to Vercel and the FastAPI backend to one stateful service with a persistent disk. For this portfolio release, Render is the simplest documented path because the repository includes `render.yaml` with a health check and disk mount.

```text
Browser → Vercel frontend → HTTPS FastAPI service → persistent SQLite file
```

Do not deploy the SQLite backend to an ephemeral/serverless filesystem. Only files written beneath a platform's mounted persistent path survive restarts and deploys. Keep the backend at one instance: SQLite is not a multi-instance application database.

## Environment variables

### Backend

| Variable | Required | Example | Purpose |
|---|---:|---|---|
| `ENVIRONMENT` | Yes in deployment | `production` | Disables development CORS defaults. |
| `CORS_ORIGINS` | Yes in deployment | `https://covenantiq.vercel.app,https://preview.example.com` | Comma-separated exact browser origins; no wildcard is added. |
| `COVENANTIQ_DB_PATH` | Yes for persistence | `/var/data/covenantiq.db` | Absolute path on the mounted disk. |
| `PORT` | Platform-provided | `8000` | Port used by Uvicorn. |

When `ENVIRONMENT=production` and `CORS_ORIGINS` is absent, the API permits no cross-origin browser requests. Server-to-server and direct API requests still work. Credentials are disabled because v1.0 has no authentication or cookies.

### Frontend

| Variable | Required | Example | Purpose |
|---|---:|---|---|
| `NEXT_PUBLIC_API_URL` | Yes for split deployment | `https://covenantiq-api.onrender.com` | Public HTTPS backend origin, without a trailing slash. |

`NEXT_PUBLIC_API_URL` is browser-visible and contains no secret. Next.js embeds `NEXT_PUBLIC_*` values during the build, so a changed API origin requires a new frontend deployment.

## Render backend

The root [Render Blueprint](../render.yaml) configures the `backend/` root directory, dependency install, Uvicorn start command, `/health` check, and a 1 GB disk mounted at `/var/data`.

1. Create a Render Blueprint from the repository.
2. Enter `CORS_ORIGINS` when prompted. Use the exact Vercel production URL; add preview origins only when they are known and trusted.
3. Confirm that the selected Render service plan supports persistent disks.
4. Deploy and open `https://<service>.onrender.com/health`.

Equivalent dashboard values:

```text
Root directory: backend
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check: /health
Disk mount: /var/data
COVENANTIQ_DB_PATH: /var/data/covenantiq.db
```

Only data under the disk mount survives deploys. An attached Render disk also limits horizontal scaling and changes deployment behavior, which is acceptable for this single-instance portfolio demo.

## Railway backend

1. Create a service from the repository and set its root directory to `backend`.
2. Use `pip install -r requirements.txt` as the build command.
3. Use this start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

4. Add a Railway volume mounted at `/data`.
5. Set `COVENANTIQ_DB_PATH=/data/covenantiq.db`, `ENVIRONMENT=production`, and exact `CORS_ORIGINS`.
6. Generate a public domain and verify `/health`.

## Fly.io backend

The checked-in `backend/Dockerfile` runs Uvicorn as a non-root user. From `backend/`:

```bash
fly launch --no-deploy
fly volumes create covenantiq_data --size 1 --region <region>
```

Configure the generated `fly.toml`:

```toml
[http_service]
  internal_port = 8000
  force_https = true

[mounts]
  source = "covenantiq_data"
  destination = "/data"

[env]
  ENVIRONMENT = "production"
  COVENANTIQ_DB_PATH = "/data/covenantiq.db"
  PORT = "8000"
```

Set `CORS_ORIGINS` with `fly secrets set CORS_ORIGINS=https://<frontend-domain>` and run `fly deploy`. Use one Machine while SQLite is the persistence layer.

## Vercel frontend

1. Import the monorepo as a Vercel project.
2. Set the project Root Directory to `frontend`.
3. Keep the detected Next.js build command (`npm run build`).
4. Add `NEXT_PUBLIC_API_URL=https://<backend-domain>` to Production and any Preview environments you intend to use.
5. Deploy, then add the deployed frontend origin to backend `CORS_ORIGINS` and restart the backend.

Vercel environment changes apply to new deployments, not already-built bundles.

## Local production commands

Backend:

```bash
cd backend
ENVIRONMENT=production \
CORS_ORIGINS=http://localhost:3000 \
COVENANTIQ_DB_PATH=./app/data/covenantiq.db \
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run start
```

## Smoke checklist

```bash
curl -fsS https://<backend>/health
curl -fsS https://<backend>/borrowers
curl -fsS https://<backend>/guided-demos
```

Then verify one private-credit analysis, create/read/delete one saved analysis, and open the generated memo from the deployed frontend.

Expected health response:

```json
{"status":"ok","service":"covenantiq-api","calculation_mode":"deterministic"}
```

## Seed and persistence behavior

- Five fictional demo borrowers ship as read-only JSON and are available on every start.
- The SQLite table initializes automatically when the API imports.
- Saved analyses are not seeded. A fresh database starts with an empty saved-analysis list.
- Deleting or replacing the database file deletes saved cases but does not affect borrower demo data.

## Platform references

- [Render web services](https://render.com/docs/web-services)
- [Render persistent disks](https://render.com/docs/disks)
- [Render health checks](https://render.com/docs/health-checks)
- [Railway volumes](https://docs.railway.com/overview/the-basics)
- [Fly.io application configuration](https://fly.io/docs/reference/configuration/)
- [Vercel monorepos](https://vercel.com/docs/monorepos)
- [Vercel environment variables](https://vercel.com/docs/environment-variables)
