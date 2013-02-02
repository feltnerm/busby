# Global Settings
#########
PRODUCTION = {{ PRODUCTION }}
DEVELOPMENT = not PRODUCTION

DEBUG = not PRODUCTION
TESTING = DEBUG
ASSETS_DEBUG = DEBUG
SECRET_KEY = """{{ SECRET_KEY }}"""

# Music Database
#########
MUSIC_DATABASE = """{{ MUSIC_DATABASE }}"""

SQLALCHEMY_DATABASE_URI = "sqlite:///%s" % MUSIC_DATABASE

# Other Databases
#########
SQLALCHEMY_BINDS = {
        "users": "sqlite:///%s" % "{{ USERS_DATABASE }}",
        }
SQLALCHEMY_ECHO = DEVELOPMENT

# Mail
#########
MAIL_SERVER = "{{ MAIL_SERVER }}"
MAIL_PORT = 25
DEFAULT_MAIL_SENDER = "bassradio"

# Cache
#########
if DEVELOPMENT:
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
else:
    CACHE_TYPE = 'memcache'
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_MEMCACHED_SERVERS = ["127.0.0.1:11211"]
