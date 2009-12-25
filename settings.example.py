# This is an example settings file. Customize these values for your
# site and rename the file as settings.py.

from database import Database
import os
settings = {
    # what domain is your app running at?
    'domain': 'my.domain.com',

    # what port do you want to run on? port numbers less than 1024
    # typically require root privileges.
    'port': 1234,

    # the local path to your default gravatar
    'default_gravatar': {
        50: "/static/images/gravatar_50.png",
        80: "/static/images/gravatar_80.png",
        125: "/static/images/gravatar_125.png",        
        },

    # on you localhost and for development, you probably want this to
    # be False. when email_enabled == False and debug == True,
    # clicking on profile edit links will let you edit peoples'
    # profiles directly, which is very useful for testing. if
    # email_enabled is set to True, this will use the email facilities
    # on the server to send emails, so make sure smtp_user and
    # smtp_pass are set properly.
    'email_enabled': True,

    # if debug == True, additional information will be printed to the
    # command line while the app is running.
    'debug': False,

    # set these when using email. 
    'smtp_user': 'admin@my.domain.com',
    'smtp_pass': 'seekret',

    # you should probably stop editing here unless you know what
    # you're doing
    'db':Database().connect(),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    'login_url': '/',
}
