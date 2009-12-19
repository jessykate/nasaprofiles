from database import Database
import os
settings = {
    'db':Database().connect(),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'domain': 'localhost',
    'port': 8989,
    'email_enabled': False,
    'debug': True,
    'smtp_user': 'people@opennasa.com',
    'smtp_pass': '',
    'login_url': '/',
}
