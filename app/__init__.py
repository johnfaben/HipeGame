import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from config import basedir, ADMINS

app = Flask(__name__)
app.config.from_object('config')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

if not app.debug:
    file_handler = RotatingFileHandler('tmp/hipegame.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('hipegame startup')

from app import views, models
