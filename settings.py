from database import Database
import os
settings = {
    # what domain is your app running at?
    'domain': 'people.opennasa.com',
    'port': 8989,
    'email_enabled': False,
    'debug': True,
    'smtp_user': 'people@opennasa.com',
    'smtp_pass': '',

    # you should probably stop editing here unless you know what
    # you're doing
    'db':Database().connect(),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'login_url': '/',
}
