"""Back up user data (accounts + solved hipes) to a JSON file.

Usage:
    # Back up from Render (paste the External Database URL from Render dashboard):
    DATABASE_URL="postgresql://user:pass@host/dbname" python backup_users.py

    # Back up from local dev database:
    python backup_users.py

    # Restore into current database:
    python backup_users.py --restore backup_users_2026-02-06.json
"""
import json
import os
import sys
from datetime import datetime, date

from app import app, db
from app.models import User, Hipe, solvers


def json_serial(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def backup():
    # Override database URL if provided via environment
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    with app.app_context():
        if db_url:
            db._app_engines[app].pop(None, None)
            db.init_app(app)

        users = User.query.all()
        data = []
        for u in users:
            solved_letters = [h.letters for h in u.solved.all()]
            data.append({
                'username': u.username,
                'email': u.email,
                'display_name': u.display_name,
                'about_me': u.about_me,
                'solved': solved_letters,
            })

        filename = f"backup_users_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=json_serial)

        print(f"Backed up {len(data)} users to {filename}")


def restore(filename):
    with app.app_context():
        with open(filename) as f:
            data = json.load(f)

        restored = 0
        for entry in data:
            user = User.query.filter_by(email=entry['email']).first()
            if not user:
                user = User(
                    username=entry['username'],
                    email=entry['email'],
                    display_name=entry.get('display_name'),
                    about_me=entry.get('about_me'),
                )
                db.session.add(user)
                db.session.flush()

            for letters in entry.get('solved', []):
                hipe = Hipe.query.filter_by(letters=letters).first()
                if hipe and not user.has_solved(hipe):
                    user.solve(hipe)

            restored += 1

        db.session.commit()
        print(f"Restored {restored} users from {filename}")


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--restore':
        restore(sys.argv[2])
    else:
        backup()
