from database import Database
import os
settings = {
    'db':Database().connect(),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'domain': 'localhost',
    'port': 8989,
    'email_enabled': True,
    'debug': True,
    'smtp_user': 'jessy.cowansharp@gmail.com',
    'smtp_pass': open('/home/jessy/.gmailpw').read().strip(),
    'login_url': '/',
}
