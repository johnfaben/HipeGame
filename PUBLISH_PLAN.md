# HIPE Game — Deploy Guide

## What the App Is

HIPE is a word puzzle game based on a game described by mathematician Peter Winkler. You're shown a short string of letters (e.g. "HQ") and must find an English word containing them as a substring (e.g. "eartHQuake"). Built with Flask 3.1, Bootstrap 4, SQLite (dev) / PostgreSQL (prod), Google OAuth. 1,135 puzzles, ~3,500 answers.

---

## Deploying to Render

### Prerequisites
- A GitHub account with the repo pushed
- A Render account (free at render.com)
- Google OAuth credentials (from console.cloud.google.com)

### Step 1: Set Up Google OAuth

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Go to **APIs & Services > OAuth consent screen**
   - Choose "External" user type
   - Fill in the app name ("HIPE Game"), support email, etc.
   - Add the scope `email`, `profile`, and `openid`
   - Add your email as a test user (while in "Testing" status)
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth 2.0 Client ID** (Web application)
6. Set **Authorized redirect URIs** to: `https://your-app-name.onrender.com/callback/google`
   - Also add `http://localhost:5000/callback/google` for local development
7. Note the **Client ID** and **Client Secret**

### Step 2: Create a Render PostgreSQL Database

1. Log in at https://render.com
2. Go to **Dashboard > New > PostgreSQL**
3. Name it `hipegame-db` (different from the web service name so they're easy to tell apart)
4. Choose the **Free** plan
5. Click **Create Database**
6. Wait for the database to finish creating (takes a minute or two)
7. On the database's info page, scroll down to **Connections**
8. Copy the **Internal Database URL** — it starts with `postgres://...`
9. You'll paste this as the `DATABASE_URL` environment variable in the next step

### Step 3: Create a Render Web Service

1. **Dashboard > New > Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `hipegame` (or whatever you like)
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt && python seed_db.py`
   - **Start Command**: `gunicorn app:app`
4. Add **Environment Variables**:
   - `DATABASE_URL` = the Internal Database URL from Step 2
   - `SECRET_KEY` = generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `GOOGLE_CLIENT_ID` = from Step 1
   - `GOOGLE_CLIENT_SECRET` = from Step 1
   - `PYTHON_VERSION` = `3.13.0`
5. Click **Create Web Service**

### Step 4: Verify

1. Visit your Render URL
2. The home page should load — guests can play without signing in
3. Click "Play HIPE" to test gameplay
4. Try "sign in with google" to test OAuth
5. After signing in, your profile page should show solved hipes

### How the Database Gets Populated

The build command runs `seed_db.py` on every deploy. This script:
1. Calls `db.create_all()` to create tables (safe to re-run)
2. Reads `list_of_hipes.txt` from the project root (committed to git)
3. Populates hipes and answers (skips if already populated)

To force a fresh database (e.g. after curating hipes): delete the Render database, create a new one, update `DATABASE_URL`, and redeploy.

### Notes

- Free tier sleeps after 15 minutes of inactivity (~30s cold start on next request)
- Free PostgreSQL expires after 30 days — back up user data with `backup_users.py` before then (see TODO.md)
- Every push to GitHub triggers an automatic redeploy

---

## Project Structure

```
app/
  __init__.py          # App setup, db, login manager, Flask-Migrate
  views.py             # All routes
  models.py            # User, Hipe, Answer models
  forms.py             # EditForm, AnswerForm
  oauth.py             # Google OAuth via authlib
  templates/           # Jinja2 templates
  static/              # CSS, JS, images
config.py              # Config from environment variables
seed_db.py             # Populate puzzles from list_of_hipes.txt
backup_users.py        # Back up / restore user data
list_of_hipes.txt      # Puzzle data (letters,answer1,answer2,...)
run.py                 # Local dev server (python run.py)
Procfile               # gunicorn app:app (for Render)
requirements.txt       # Python dependencies
.env.example           # Template for local .env file
```
