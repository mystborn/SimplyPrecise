import json
import os

_config = json.load(open('config.json', 'r'))
_basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    TESTING = _config['testing']
    SECRET_KEY = _config['secret']
    SQLALCHEMY_DATABASE_URI = _config.get('database_uri') or 'sqlite:///' + os.path.join(_basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = _config['mail'].get('server')
    MAIL_PORT = _config['mail'].get('port', 25)
    MAIL_USE_TLS = _config['mail'].get('use_tls', False)
    MAIL_USERNAME = _config['mail'].get('username')
    MAIL_PASSWORD = _config['mail'].get('password')
    ADMINS = _config['admins']
    RECAPTCHA_PUBLIC_KEY = _config['recaptcha']['public']
    RECAPTCHA_PRIVATE_KEY = _config['recaptcha']['private']
    RECAPTCHA_USE_SSL = _config['recaptcha']['use_ssl']
    POSTS_PER_PAGE = 5