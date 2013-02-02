import binascii
import os

from fabric.colors import *
from fabric.api import *
from fabric.contrib.console import *
from fabric.utils import *

from jinja2 import Environment, FileSystemLoader


def pblue(s, bold=False):
        puts(blue(s,bold))
def pcyan(s, bold=False):
        puts(cyan(s,bold))
def pgreen(s, bold=False):
        puts(green(s, bold))
def pmage(s, bold=False):
        puts(magenta(s,bold))
def pred(s, bold=False):
        puts(red(s, bold))
def pwhite(s, bold=False):
        puts(white(s, bold))
def pyellow(s, bold=False):
        puts(yellow(s, bold))

# ==
# Environment settings
# =
env.PROJECT_ROOT = os.path.dirname(__file__)
env.PROJECT_VENV = 'bassradio'
env.user = 'mark'
env.roledefs = {
    'local': ['localhost'],
    'web': ['nalanda.bd.to']
}

def server():
    env.PROJECT_ROOT = '/srv/apps'
    env.user = 'mark'

@task
def web():
    server()
    env.roles = ['web']

# =
# Application settings
# =
def create_settings():
    settings = {}
    pcyan("## Environment settings.")
    settings['PRODUCTION'] = False
    if confirm(blue("Are these settings for a production server?")):
        settings['PRODUCTION'] = True

    puts('')
    pcyan("## Database Info:")
    settings['MUSIC_DATABASE'] = prompt(blue("Absolute path to music database: "))
    settings['USERS_DATABASE'] = prompt(blue("Absolute path to users database: "))
    settings['MAIL_SERVER'] = prompt(blue("Mail server URI: "))

    secret_key = binascii.b2a_hqx(os.urandom(42))
    pred('\nSECRET_KEY: %s' % secret_key)
    if confirm(yellow("Verify everything looks correct?")):
        settings['SECRET_KEY'] = secret_key
        return settings

    return None


@task
def settings():

    settings = create_settings()
    if settings:
        jenv = Environment(loader=FileSystemLoader('.'))
        text = jenv.get_template('settings_template.py').render(**settings or {})
        outputfile_name = 'settings_dev.py'
        if settings.get("PRODUCTION"):
            outputfile_name = 'settings_prod.py'
        with open(outputfile_name, 'w') as outputfile:
            outputfile.write(text)

def settings_upload():
    settings = create_settings()
    if settings:
        outputfile_name = 'settings_dev.py'
        if settings.get('PRODUCTION'):
            outputfile_name = 'settings_prod.py'
        with cd(env.PROJECT_ROOT):
            with prefix('workon %s' % env.PROJECT_VENV):
                upload_template('settings_default.py',
                                os.path.join(env.PROJECT_ROOT, outputfile_name),
                                context=settings, use_jinja=True, backup=False
                                )

@task
def deploy():
    local('git push origin master')
    with cd(env.PROJECT_ROOT):
        run('git clone git://github.com/feltnerm/MADmin.git')

@task
def update():
    local('git push origin master')
    with cd(env.PROJECT_ROOT+'/MADmin'):
        run('git pull origin master')

