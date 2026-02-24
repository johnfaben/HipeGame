# Deploying a new Flask site on the Hetzner VPS

The server (`johnfaben-cloud1`) is already set up with Ubuntu 24.04, Nginx,
PostgreSQL 16, Certbot, and a `deploy` user. Wildcard DNS `*.johnfaben.com`
points to the server, so any subdomain works automatically.

Replace `newsite` throughout with the actual app name.

---

## 1. Create the database

```bash
sudo -u postgres psql
```

```sql
CREATE USER newsite WITH PASSWORD 'PICK_A_STRONG_PASSWORD';
CREATE DATABASE newsite OWNER newsite;
\q
```

---

## 2. Deploy the app

### 2a. Create the directory and get the code

```bash
sudo mkdir -p /var/www/newsite
sudo chown deploy:deploy /var/www/newsite
```

**Option A — Git clone:**

```bash
cd /var/www/newsite
git clone https://github.com/YOUR_USERNAME/newsite.git .
```

**Option B — rsync from local machine** (Git Bash / WSL):

```bash
rsync -avz --exclude venv --exclude hipevenv --exclude __pycache__ --exclude app.db --exclude .env \
  /c/Users/jdfab/Dropbox/Flask/newsite/ deploy@johnfaben-cloud1:/var/www/newsite/
```

### 2b. Virtual environment

```bash
cd /var/www/newsite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2c. Create the `.env` file

```bash
nano /var/www/newsite/.env
```

```env
SECRET_KEY=GENERATE_WITH_python3 -c "import secrets; print(secrets.token_hex(32))"
DATABASE_URL=postgresql://newsite:PICK_A_STRONG_PASSWORD@localhost/newsite
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

Lock it down:

```bash
chmod 600 /var/www/newsite/.env
```

### 2d. Create the log directory

```bash
mkdir -p /var/www/newsite/tmp
```

### 2e. Seed the database

```bash
cd /var/www/newsite
source venv/bin/activate
python seed_db.py
```

### 2f. Smoke test

```bash
cd /var/www/newsite
source venv/bin/activate
gunicorn --bind 127.0.0.1:8001 app:app
```

`curl http://127.0.0.1:8001/` in another terminal — you should get HTML back.
Ctrl+C to stop.

---

## 3. Gunicorn systemd service

```bash
sudo nano /etc/systemd/system/newsite.service
```

```ini
[Unit]
Description=newsite (gunicorn)
After=network.target postgresql.service

[Service]
User=deploy
Group=deploy
WorkingDirectory=/var/www/newsite
Environment="PATH=/var/www/newsite/venv/bin"
ExecStart=/var/www/newsite/venv/bin/gunicorn --workers 2 --bind unix:/var/www/newsite/newsite.sock app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable newsite
sudo systemctl start newsite
sudo systemctl status newsite --no-pager
```

---

## 4. Nginx

```bash
sudo nano /etc/nginx/sites-available/newsite
```

```nginx
server {
    listen 80;
    server_name newsite.johnfaben.com;

    location /static/ {
        alias /var/www/newsite/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://unix:/var/www/newsite/newsite.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/newsite /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. SSL

```bash
sudo certbot --nginx -d newsite.johnfaben.com
```

Choose to redirect HTTP to HTTPS when prompted. Verify renewal:

```bash
sudo certbot renew --dry-run
```

---

## 6. Google OAuth

In the [Google Cloud Console](https://console.cloud.google.com/):

1. **APIs & Services > Credentials** > your OAuth client
2. Add to **Authorized redirect URIs**: `https://newsite.johnfaben.com/callback/google`
3. Restart the app: `sudo systemctl restart newsite`

If the consent screen is in "Testing" mode, either add test users or publish
the app.

---

## 7. Deploying updates

**Via rsync** (from local machine):

```bash
rsync -avz --exclude venv --exclude hipevenv --exclude __pycache__ --exclude app.db --exclude .env \
  /c/Users/jdfab/Dropbox/Flask/newsite/ deploy@johnfaben-cloud1:/var/www/newsite/
```

Then on the server:

```bash
sudo systemctl restart newsite
```

**Via git** (on the server):

```bash
cd /var/www/newsite
git pull
source venv/bin/activate
pip install -r requirements.txt   # only if dependencies changed
sudo systemctl restart newsite
```

**If the database schema changed:**

```bash
cd /var/www/newsite
source venv/bin/activate
flask db upgrade
sudo systemctl restart newsite
```

---

## 8. Maintenance

### Database backups

Daily backup cron is already set up at `/etc/cron.daily/backup-postgres`.
Backups are in `/home/deploy/backups/`. To download one:

```bash
scp deploy@johnfaben-cloud1:~/backups/all-databases-20260222.sql.gz .
```

### Logs

```bash
sudo journalctl -u newsite -n 100       # App logs
sudo tail -f /var/log/nginx/access.log   # Nginx access
sudo tail -f /var/log/nginx/error.log    # Nginx errors
cat /var/www/newsite/tmp/newsite.log     # App-level log file
```

### Disk space

```bash
df -h
du -sh /var/www/*/
```

---

## 9. Troubleshooting

### 502 Bad Gateway
Gunicorn isn't running or the socket path is wrong.

```bash
sudo systemctl status newsite
ls -la /var/www/newsite/newsite.sock
sudo journalctl -u newsite -n 50
```

### Permission denied on socket

```bash
sudo usermod -aG deploy www-data
sudo systemctl restart nginx
```

### Database connection refused

```bash
sudo systemctl status postgresql
```

Check `DATABASE_URL` in `.env` matches the user/password/database from step 1.

### App works locally but not on server
- `.env` exists and has correct values?
- `tmp/` directory exists?
- `sudo journalctl -u newsite -n 50` for Python errors?

---

## Quick reference

| Task | Command |
|------|---------|
| Start a site | `sudo systemctl start newsite` |
| Stop a site | `sudo systemctl stop newsite` |
| Restart a site | `sudo systemctl restart newsite` |
| View site logs | `sudo journalctl -u newsite -f` |
| Reload Nginx | `sudo systemctl reload nginx` |
| Renew SSL certs | `sudo certbot renew` |
| PostgreSQL shell | `sudo -u postgres psql` |
| Backup all DBs | `sudo -u postgres pg_dumpall > backup.sql` |
