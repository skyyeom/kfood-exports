# Deploying the WellGTM dashboard on Render

The dashboard is a small Python web server (`python -m pipeline.preview`) that reads from the Supabase database, so it needs a host that runs Python. GitHub Pages can't. `render.yaml` in the repo root describes the service. After the one-time setup below, Render rebuilds and redeploys automatically on every merge to `main`.

What you get: a free web service with HTTPS at a URL like `https://wellgtm.onrender.com`, with the same sign-in as locally.

**Free-plan behaviour:**
- The service sleeps after about 15 minutes without visitors, and the first visit after that takes 30–60 seconds to wake it.
- Each restart signs everyone out, because sessions are kept in memory.
- The scheduled data jobs keep running on GitHub Actions regardless.

## One-time setup (about 10 minutes)

1. **Sign in to Render** at <https://render.com>, using **GitHub** (the account that owns `skyyeom/kfood-exports`). No credit card is needed for the free plan.
2. **Create the service from the Blueprint:**
   1. **New → Blueprint**, then connect the `kfood-exports` repository (allow Render to access it when GitHub asks).
   2. Render reads `render.yaml` and shows one web service, `wellgtm`.
   3. It then asks for the values marked `sync: false`. Paste each one from your local `.env`, without quotes or spaces:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | the Supabase **Session pooler** string (same as `.env`) |
   | `DASHBOARD_USERNAME` | your dashboard username (same as `.env`) |
   | `DASHBOARD_PASSWORD_HASH` | the `scrypt:…` line from `.env` (the hash, not the password) |
   | `SUPABASE_URL` | same as `.env` |
   | `SUPABASE_SERVICE_ROLE_KEY` | same as `.env` |
   | `KCS_API_KEY` | same as `.env` (used when someone presses a 관세청 **Run** button) |

   To use a different login for the website, run `.venv/bin/python -m pipeline.auth set` locally, then copy the new `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD_HASH` from `.env`.
3. **Deploy:** click **Apply**. The first build takes a few minutes. When the dashboard shows **Live**, open the service's URL and sign in.

## Checking it

- `https://<your-service>.onrender.com/healthz` should show `{"ok": true}`. This is the public health check Render uses; it reveals no data.
- Every other page asks you to sign in first.
- **Logs:** if a deploy fails, Render → `wellgtm` → **Logs** shows why. A missing or wrong `DATABASE_URL` is the most common cause.

## How it is configured (`render.yaml`)

| Setting | Why |
|---|---|
| `buildCommand: pip install ".[postgres]"` | Installs the package and the Postgres driver. A plain `pip install .` leaves the driver out, and the site then crashes on startup. |
| `startCommand: python -m pipeline.preview` | Starts the dashboard; it reads Render's `PORT`. |
| `HOST=0.0.0.0` | Listens on Render's network instead of only on localhost. |
| `TRUST_PROXY=1` | Visitors arrive through Render's HTTPS proxy. The server then marks the sign-in cookie `Secure` and counts failed sign-ins per real visitor address, rather than locking everyone out together. |
| `healthCheckPath: /healthz` | Render restarts the service if this stops answering. |
| `region: singapore` | The nearest Render region to the Supabase project in Tokyo. |

## Limits and next steps

- **Weekly-report PDFs:** these use a Unicode font found on the server. Render's Linux image may have none that covers Korean, in which case 관세청 is written as "Korea Customs Service" in the PDF.
- **Run buttons:** these run the pipeline inside the web service. Long runs (the full 관세청 history takes about 5 minutes) can stop if the free instance goes to sleep, but the scheduled GitHub jobs remain the reliable path.
- **Paid plan:** a paid Render plan ($7/month at the time of writing) removes sleeping and keeps sessions across idle periods.
