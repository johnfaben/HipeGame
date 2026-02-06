import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Use DATABASE_URL from Render/Heroku, fall back to local SQLite for development
database_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
# Render provides postgres:// but SQLAlchemy needs postgresql://
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
    }
}

MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

# pagination
POSTS_PER_PAGE = 10

# admin list
ADMINS = [os.environ.get('ADMIN_EMAIL', 'admin@example.com')]
