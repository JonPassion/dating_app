# Deploy to Render (free tier)

Your repo already includes `render.yaml` (Postgres + web service + env vars + `/health/` check).

## Option A — One click (recommended)

1. Sign in to [Render](https://dashboard.render.com/) (GitHub or Google).
2. Open this link:

   **https://render.com/deploy?repo=https://github.com/JonPassion/dating_app**

3. Click **Apply** — Render creates:
   - PostgreSQL (`unidate-db`, free)
   - Web service (`unidate`, free)
   - `DATABASE_URL` (linked automatically)
   - `DJANGO_ENV=production`, `RENDER=true`
   - `DJANGO_SECRET_KEY` (auto-generated)
   - Health check: `/health/`
4. Wait for the first deploy (~5–10 min).
5. **Shell** on the web service:
   ```bash
   cd datingsite && python manage.py createsuperuser
   ```
6. Open your app URL (e.g. `https://unidate.onrender.com`).

## Option B — Dashboard Blueprint

1. [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
2. Connect GitHub → select **`JonPassion/dating_app`**
3. **Apply** (same as Option A)

## Option C — API script (no browser)

1. Create an API key: [Render Account Settings → API Keys](https://dashboard.render.com/u/settings#api-keys)
2. Run:
   ```bash
   export RENDER_API_KEY=rnd_your_key_here
   ./scripts/deploy-render.sh
   ```

## After code changes

```bash
git add .
git commit -m "Your message"
git push
```

Render auto-redeploys `main` when auto-deploy is on (default).

## Free tier reminders

- Service **sleeps** after ~15 min idle; first load may take 30–60s.
- **No Redis** — cache/sessions use PostgreSQL (configured in `production.py`).
- **Uploaded images** are on ephemeral disk; use S3/Cloudinary for persistence later.
