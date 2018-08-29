import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///'+os.path.join(basedir,'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir,'db_repository')

WFT_CSRF_ENABLED = True
SECRET_KEY = 'female-sword-touch-review-52828'

OPENID_PROVIDERS = [
            {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
            {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
            {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
            {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
            {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}
        ]

OAUTH_CREDENTIALS = { 'facebook' : {'id': '897116857119779',
    'secret': '359373e23a7ff9c0ee2ebc4974b4ce94',
    },
      'google' : {'id': '996061203539-bf7o4rv0su6psemhng8ep2aafajecseq.apps.googleusercontent.com', 'secret': 'RbgZiX35MLBuYelTCOvXGn2C'
    }
    }

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'thegameofhipe@gmail.com'
MAIL_PASSWORD = 'CalumnyBagdropWaist'

#pagination
POSTS_PER_PAGE = 3


# admin list
ADMINS = ['jdfaben@gmail.com']
