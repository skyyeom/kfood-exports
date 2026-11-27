# Setting up Supabase for WellGTM

About 10 minutes. Supabase hosts the database the scheduled jobs write to and the dashboard reads from. The free plan is enough.

Supabase's dashboard layout changes from time to time. If a label below doesn't match exactly, look for the nearest equivalent.

## 1. Create the project
1. Go to <https://supabase.com> and sign in. You can sign in with GitHub.
2. Click **New project** and fill in:
   - **Organization:** your personal organization is fine.
   - **Name:** `wellgtm`.
   - **Database password:** click *Generate a password* and **save it in your password manager**. You need it in step 2, and Supabase won't show it again.
   - **Region:** **Northeast Asia (Seoul)**, the closest to the team and to the 관세청 API.
   - **Plan:** Free.
3. Click **Create new project** and wait 1–2 minutes until the dashboard shows the project as ready.

## 2. Copy three values into `.env`
Open `.env` in the repo folder (it already has `KCS_API_KEY`). Add the three lines below, using `.env.example` as the template. **Don't paste these values into chat or commit them.**

| Line in `.env` | Where to find it |
|---|---|
| `SUPABASE_URL=` | **Project Settings → API** (or *Data API*): the **Project URL**, like `https://abcdefghijklmnop.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY=` | **Project Settings → API Keys**: the **secret** key (`sb_secret_…`), or under *Legacy API keys* the **service_role** key (`eyJ…`). Either works. Never use it in a browser. |
| `DATABASE_URL=` | Click **Connect** at the top of the dashboard → **Connection string** → **Session pooler**. Copy the URI and replace `[YOUR-PASSWORD]` with the password from step 1. |

Use the **Session pooler** string (host `aws-0-ap-northeast-2.pooler.supabase.com`, user `postgres.<project-ref>`), **not** the direct one (`db.<project-ref>.supabase.co`). The direct address is IPv6-only, and GitHub Actions can't reach it.

If the password contains special characters such as `@`, `:` or `/`, either generate one without them or percent-encode them in the URL (`@` → `%40`).

The finished lines look like this:
```
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:<password>@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres
```

## 3. Run the setup
```bash
set -a; . ./.env; set +a
.venv/bin/python -m pipeline.supabase_setup
```
The setup does the following:
1. Checks the settings, and explains any problem in plain language (wrong host, mismatched projects, a leftover placeholder password).
2. Applies `supabase/migrations/0001_init.sql`: tables, row-level security, BI views, the `raw` storage bucket, Realtime and the read-only `bi_reader` role. Running it again is safe.
3. Verifies that everything is in place.
4. Loads the full history of every source (a few minutes), re-ranks, and writes the first weekly report.

To check it worked, open **Table Editor** in Supabase. `ingest_runs` should have one row per source, `bi_rankings` should list the TOP3, and `reports` should hold this week's report.

## 4. Add the GitHub secrets
The scheduled jobs need the same values. In the repository, go to **Settings → Secrets and variables → Actions → New repository secret** and add `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` and `KCS_API_KEY` (and `COMTRADE_API_KEY` if you have one).

Alternatively, with a `gh` login that has admin rights on the repo, run `scripts/set_github_secrets.sh`. It copies the secrets from `.env` without printing them.

## 5. Merge and keep it running
- Merge the pull request into `main`. GitHub only runs scheduled workflows from the default branch.
- Free Supabase projects pause after about a week without activity. The daily ingest job keeps the project active.
- **Optional, for BI tools:** enable the read-only login with one line in the SQL editor (see [bi_guide.md](bi_guide.md)):
  ```sql
  alter role bi_reader with login password '<a long random password>';
  ```
