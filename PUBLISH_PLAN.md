# HIPE Game — Publish Plan

## What the App Is

HIPE is a word puzzle game based on a game described by mathematician Peter Winkler. The rules:

1. You're shown a short string of letters (e.g. "HQ")
2. You must find an English word containing those letters as a substring (e.g. "eartHQuake")
3. Your answer is validated against a pre-loaded dictionary of accepted answers
4. You can track which HIPEs you've solved, play random unsolved ones, and view all answers after solving

The app is built with Flask 3.1 (Python), Bootstrap 4, SQLite (dev) / PostgreSQL (prod), and supports Google OAuth login. It has 1,468 puzzles with 2,648 answers (loaded from `list_of_hipes.txt` via `seed_db.py`).

---

## Part 1: Code Fixes — ALL COMPLETE

All critical and important fixes have been applied:

- [x] Renamed `async` decorator to `run_async` (Python 3.7+ keyword conflict)
- [x] Moved all secrets to environment variables (`config.py`)
- [x] Fixed missing `follower_notification` import in `views.py`
- [x] Fixed Procfile (`app:app` instead of `app:hipegame`)
- [x] Fixed HTML bugs in `hipe.html` and `user.html`
- [x] Switched jQuery to HTTPS and pinned version (3.7.1)
- [x] Removed dead OpenID code and templates
- [x] Removed Facebook OAuth (broken, deprecated API) — Google only
- [x] Updated `follower_email.html` (removed microblog references)
- [x] Removed leftover microblog artifacts (`post.html`, `search_results.html`, `pagination.html`, `PostForm`)
- [x] Fixed `WTF_CSRF_ENABLED` typo
- [x] Switched from `sqlalchemy-migrate` to Flask-Migrate (Alembic)
- [x] Switched from `rauth` (abandoned) to `authlib` for OAuth
- [x] Upgraded to Flask 3.1, SQLAlchemy 2.0, and modern dependency stack
- [x] Log file renamed from `microblog.log` to `hipegame.log`
- [x] Gravatar URLs use `https://`

---

## Part 2: Feature Ideas (not yet started)

### Quick Wins (small effort, big impact)

**A. Play Without Login**
- Currently the entire app requires login. Let people play as a guest — only require login to save progress. This massively reduces friction.

**B. Hint System**
- "Reveal first letter", "Show word length", "Show category" — let players get unstuck without giving up

**C. More Puzzles**
- There are only 13 HIPEs. You could programmatically generate hundreds by:
  - Taking a dictionary file (e.g. `/usr/share/dict/words` or an English word list)
  - Finding interesting 2-4 letter substrings that appear in multiple words but aren't obvious
  - Auto-populating the `answer` table

**D. Difficulty Levels**
- Rate puzzles by how common the substring is (e.g. "hipe" is hard because few words contain it; "ing" would be trivial)
- Let players choose easy/medium/hard

**E. Score / Points System**
- The `solvers` table already has a `score` column that's never used
- Award points based on difficulty, speed, or number of answers found

### Medium Effort

**F. Daily HIPE**
- One puzzle per day, same for everyone (like Wordle)
- Great for sharing on social media: "I solved today's HIPE in 3 tries!"

**G. Multiplayer / Competitive Mode**
- Two players get the same HIPE, race to solve it
- Or: who can find the most answers in 60 seconds

**H. Leaderboard**
- Global leaderboard by total HIPEs solved, points earned, or streak
- Weekly/monthly rankings

**I. "Am I Wrong?" Button**
- When a player submits a valid English word that contains the letters but isn't in your answer list, the form says "I do not think that X is a word. Am I wrong?"
- Add a button that lets them flag it for review, or auto-validate against a dictionary API

**J. Email/Password Login**
- Not everyone wants to use Google. Add basic email+password registration using Flask-Login's built-in support or Flask-Security.

### Bigger Features

**K. User-Submitted HIPEs**
- Let players submit their own letter combinations + answers for others to play
- Moderation queue or community voting

**L. Progressive Web App (PWA)**
- Add a manifest and service worker so it can be installed on phones and played offline

**M. API for a Mobile App**
- Add a REST API so you could build a native iOS/Android app later

---

## Part 3: Deploying to Render — Step by Step

### Prerequisites
- A GitHub account
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

### Step 2: Push to GitHub

The project is already a git repo. Make sure your `.gitignore` is correct (it should already exclude `venv/`, `__pycache__/`, `*.db`, `.env`, `tmp/`, etc.), then:

```bash
git add .
git commit -m "Prepare for deployment"
git remote add origin https://github.com/YOUR_USERNAME/hipegame.git
git push -u origin master
```

If the remote already exists, just `git push`.

### Step 3: Create a Render PostgreSQL Database

1. Log in at https://render.com
2. Go to **Dashboard > New > PostgreSQL**
3. Name it `hipegame-db`
4. Choose the **Free** plan
5. Click **Create Database**
6. Copy the **Internal Database URL** (starts with `postgres://...`)

### Step 4: Create a Render Web Service

1. **Dashboard > New > Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name**: `hipegame` (or whatever you like)
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt && python seed_db.py`
   - **Start Command**: `gunicorn app:app`
4. Add **Environment Variables**:
   - `DATABASE_URL` = (paste the Internal Database URL from Step 3)
   - `SECRET_KEY` = (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `GOOGLE_CLIENT_ID` = (from Step 1)
   - `GOOGLE_CLIENT_SECRET` = (from Step 1)
   - `PYTHON_VERSION` = `3.13.0`
5. Click **Create Web Service**

### Step 5: Initialize the Database

The build command above runs `seed_db.py` which calls `db.create_all()` and populates the puzzles. On first deploy this creates all the tables and seeds the data.

For future schema changes, use Flask-Migrate:
```bash
# Locally:
flask db init          # one-time setup
flask db migrate -m "description of change"
flask db upgrade

# On Render, add to the build command:
# pip install -r requirements.txt && flask db upgrade && python seed_db.py
```

### Step 6: Verify

1. Visit `https://hipegame.onrender.com` (or your chosen URL)
2. You should see the login page with a "sign in with google" button
3. Click it and authenticate with your Google account
4. After authenticating, you should land on the home page
5. Click "Play HIPE" to test gameplay

### Ongoing

- Render's free tier spins down after 15 minutes of inactivity (first request after sleep takes ~30 seconds)
- Upgrade to the Starter plan ($7/month) if you want it always-on
- Push to GitHub to auto-deploy updates

---

## Current Project Structure

```
hipegame/
  app/
    __init__.py          # Flask app factory, db, login manager, Flask-Migrate
    views.py             # All routes (index, login, hipe, answer, oauth, etc.)
    models.py            # User, Hipe, Answer models
    forms.py             # EditForm, AnswerForm
    oauth.py             # Google OAuth via authlib
    email.py             # Follower notification emails
    decorators.py        # run_async decorator
    static/
      css/               # Bootstrap, bootstrap-social
      js/                # Bootstrap JS
      fontawesome/
      img/
    templates/
      base.html          # Layout with navbar
      index.html          # Home page
      login.html          # Google sign-in
      hipe.html           # Puzzle page
      answer.html         # Answer reveal page
      user.html           # User profile
      edit.html           # Edit profile
      flash.html          # Flash messages
      404.html / 500.html # Error pages
      follower_email.html / .txt  # Email templates
  config.py              # All config, secrets from env vars
  run.py                 # Dev server entry point
  flask_app.py           # Alternate dev entry point
  Procfile               # gunicorn app:app
  requirements.txt       # Flask 3.1, authlib, Flask-Migrate, etc.
  seed_db.py             # Populates puzzles and answers
  .env.example           # Template for local .env file
  .gitignore
```
