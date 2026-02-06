# HIPE Game — Future Ideas & Maintenance

## Feature Ideas

### Featured Daily HIPE
A featured hipe on the home page that changes each day — deterministic from the date (hash the date to pick a hipe, no cron job needed). Players can still play random hipes as much as they want; this is just a spotlight, not a limit. Could add a shareable link: "I solved today's featured HIPE!"

### "Am I Wrong?" Button
When someone submits a real English word that's not in the answer list, the game says "I do not think that X is a word." Add a button to flag it for manual review. Store flagged words in a table (word, hipe, timestamp) and add an admin view to approve/reject them. This grows the answer lists over time without needing a dictionary API.

### Leaderboard / Public Profiles
A leaderboard page showing all signed-in users ranked by hipes solved. Each user links to their public profile, which shows their solved hipe badges (already implemented — just needs to be visible to other users, not just yourself). Add a progress graphic — a bar or percentage showing how much of the total they've completed.

### Difficulty Rating
Rate hipes by how obscure the answers are. Could be automatic — count how many answers each hipe has, or score answers by word frequency. Let players filter by easy/medium/hard, or show difficulty after solving.

### Progress Bar
Show a visual progress indicator on the profile page (e.g. a Bootstrap progress bar showing "12% complete") and maybe on the home page too. More motivating than just a number.

### Better Wrong-Answer Feedback
Currently a wrong answer just shows a form error. Could be more helpful: "X doesn't contain the letters HQ" vs "X contains HQ but isn't in our word list" (which leads naturally into the "Am I Wrong?" button).

### Challenge Link
A "share this hipe" button on the puzzle page that copies a link to that specific hipe. Simple sharing — no accounts or multiplayer needed. The link just goes to `/hipe/<letters>`.

### Achievement Badges
Milestones displayed on the profile page. Ideas:
- **First solve** — solved your first hipe
- **On a roll** — solved 10 in a row without giving up
- **Alphabet soup** — solved a hipe starting with every letter of the alphabet
- **Century** — solved 100 hipes
- **Halfway there** — solved 50% of all hipes
- **Completionist** — solved every hipe

Would need a badges table and logic to check/award them after each solve.

### Keyboard Shortcuts
After solving a hipe, press Enter (or a key) to jump straight to the next random hipe. Makes binge-playing smoother. Could also add shortcuts on the puzzle page (Enter to submit, H for hint, etc.).

### Word Facts ("Did You Know?")
After solving, optionally show a one-liner about one of the answer words — etymology, fun facts, unusual usage. Needs manual curation so it's a slow-burn project. e.g. after solving ZPA: "CHUTZPAH comes from Yiddish and originally meant 'shameless audacity'."

## Maintenance

### Database Backup (every ~80 days on free tier)
Render's free PostgreSQL expires after 90 days. Before it does:
```
DATABASE_URL="<External Database URL from Render>" python backup_users.py
```
Then recreate the database on Render, update `DATABASE_URL` env var if the connection string changed, trigger a redeploy, and restore:
```
DATABASE_URL="<new External Database URL>" python backup_users.py --restore backup_users_YYYY-MM-DD.json
```

### Curating Hipes
- Edit `list_of_hipes.txt` to add/remove hipes and answers
- Run `python seed_db.py` locally to test
- Removing a hipe from the file doesn't remove it from an existing database — you'd need to delete it manually or recreate the database
- The email link on missing-hipe pages (jdfaben+hipegame@gmail.com) will surface user suggestions

### Updating Dependencies
Periodically run `pip list --outdated` and update `requirements.txt`. The main dependencies are Flask, SQLAlchemy, authlib, and gunicorn.
