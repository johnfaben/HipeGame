import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Use DATABASE_URL env var for PostgreSQL in production, fall back to local SQLite for dev
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
# Some providers use postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URI = database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False

WTF_CSRF_ENABLED = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

OAUTH_CREDENTIALS = {
    'google': {
        'id': os.environ.get('GOOGLE_CLIENT_ID', ''),
        'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
    },
}

RESEND_API_KEY = os.environ.get('RESEND_API_KEY')

# pagination
POSTS_PER_PAGE = 10

# admin list
ADMINS = [os.environ.get('ADMIN_EMAIL', 'admin@example.com')]
