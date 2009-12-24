# This is an example settings file. Customize these values for your
# site and rename the file as settings.py.

from database import Database
import os
settings = {
    'db':Database().connect(),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'domain': 'my.domain.com',
    'port': 1234,
    'email_enabled': True,
    'debug': False,
    'smtp_user': 'admin@my.domain.com',
    'smtp_pass': 'seekret',
    'login_url': '/',
}
