# University Dating App

A Django-based dating application designed for university students to connect, match, and chat with each other.

## Features

- **User Registration & Authentication**: Sign up, login, and logout functionality
- **Profile Management**: Create and edit your profile with:
  - Bio
  - Major and year of study
  - Interests
  - Profile picture
  - Age, gender, and dating preferences
- **Browse Profiles**: Swipe through other student profiles
- **Matching System**: Like profiles and get matched when there's mutual interest
- **Messaging**: Chat with your matches in real-time
- **Modern UI**: Clean, responsive design with Bootstrap 5

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Navigate to the project directory**:
   ```bash
   cd datingsites
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   cd datingsite
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

1. **Register**: Click "Sign Up" to create a new account
2. **Complete Profile**: Fill in your profile information (major, year, interests, etc.)
3. **Browse**: Click "Browse" to view other profiles
4. **Like/Dislike**: Use the heart or X buttons to like or pass on profiles
5. **Matches**: When both users like each other, you'll get a match!
6. **Chat**: Click on a match to start chatting

## Project Structure

```
datingsite/
├── datingsite/          # Main Django project
│   ├── settings.py      # Project settings
│   ├── urls.py          # Main URL configuration
│   └── wsgi.py          # WSGI configuration
├── dating/              # Main dating app
│   ├── models.py        # Database models
│   ├── views.py         # View functions
│   ├── urls.py          # App URL configuration
│   ├── forms.py         # Form classes
│   ├── admin.py         # Admin configuration
│   └── templates/       # HTML templates
└── manage.py            # Django management script
```

## Models

- **UserProfile**: Extends Django's User model with university-specific fields
- **Like**: Tracks likes between users
- **Match**: Represents mutual likes between two users
- **Message**: Chat messages between matched users

## Customization

To customize for your university:

1. Update the site name in `templates/dating/base.html`
2. Modify the color scheme in the CSS section of `base.html`
3. Add university-specific fields to the UserProfile model
4. Update the year range validators if needed

## Deploy on Render (free tier)

One-click style deploy with the included Blueprint:

1. Push this repo to GitHub/GitLab.
2. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect the repo — Render reads `render.yaml` and creates:
   - **Web service** (Python, free)
   - **PostgreSQL** database (free)
4. Wait for the first deploy (~5–10 min). Migrations run in `build.sh`.
5. Create an admin user: **Shell** tab on the web service:
   ```bash
   cd datingsite && python manage.py createsuperuser
   ```
6. Open your app at `https://<your-service>.onrender.com`

**Free tier notes:**

| Topic | Behavior |
|--------|----------|
| **Sleep** | App spins down after ~15 min idle; first request may take 30–60s |
| **Redis** | Not included — sessions/cache use PostgreSQL (`createcachetable` in build) |
| **Media uploads** | Stored on ephemeral disk; files may be lost on redeploy. For production photos use S3/Cloudinary later |
| **Workers** | 1 Gunicorn worker (512 MB RAM limit) |

**Manual Render setup** (without Blueprint): Web Service → Build: `./build.sh` → Start: `cd datingsite && gunicorn datingsite.wsgi:application -c ../gunicorn.conf.py` → Add Postgres → Link `DATABASE_URL` → Env: `DJANGO_ENV=production`, `RENDER=true`.

Health check path: `/health/`

---

## Production deployment (500+ users)

The app supports production via **PostgreSQL**, **Redis**, and **Gunicorn**.

### Quick start with Docker

```bash
cp .env.example .env
# Edit .env: set DJANGO_SECRET_KEY, POSTGRES_PASSWORD, DJANGO_ALLOWED_HOSTS

docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

- App: http://localhost:8000/
- Health check: http://localhost:8000/health/

### Architecture

| Component | Role |
|-----------|------|
| **PostgreSQL** | Concurrent reads/writes (replaces SQLite) |
| **Redis** | Session store + browse/dashboard cache |
| **Gunicorn** | Multi-worker WSGI server (`gthread` workers) |
| **WhiteNoise** | Compressed static files in production |

### Environment variables

Copy `.env.example` and set at minimum:

- `DJANGO_ENV=production`
- `DJANGO_SECRET_KEY` (long random string)
- `DJANGO_ALLOWED_HOSTS` (your domain)
- `POSTGRES_PASSWORD`
- `CORS_ALLOWED_ORIGINS` (if using the API from a frontend)

### Capacity tuning (500+ users)

| Variable | Default | Notes |
|----------|---------|-------|
| `WEB_CONCURRENCY` | `2 * CPU + 1` | Gunicorn worker processes |
| `GUNICORN_THREADS` | `2` | Threads per worker |
| `DB_CONN_MAX_AGE` | `60` | Reuse PostgreSQL connections |
| `BROWSE_CACHE_TTL` | `300` | Caches like/pass exclusions |
| `DRF_THROTTLE_USER` | `300/minute` | API rate limit per user |

For **500 concurrent users**, a single server with 4 workers, PostgreSQL, and Redis is typically sufficient. Beyond ~1k active users, add a reverse proxy (Nginx), separate media storage (S3), and horizontal scaling behind a load balancer.

### Local development

```bash
export DJANGO_ENV=development  # default — uses SQLite + in-memory cache
python manage.py runserver
```

## Security Notes

- Never commit `.env` or real `DJANGO_SECRET_KEY` values
- `DEBUG` is off automatically when `DJANGO_ENV=production`
- HTTPS headers enabled in production (`SECURE_SSL_REDIRECT`, secure cookies)

## License

This project is for educational purposes.
