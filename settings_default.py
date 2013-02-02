import os
import os.path
import sys
import logging

SITE_NAME = 'bassradio'

# Directories
#########
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIRS = (os.path.join(CURRENT_DIR, 'templates'),)
STATIC_ROOT = os.path.join(CURRENT_DIR, 'static')

# Logging
#########
LOG_LEVEL = logging.DEBUG
LOGGER_NAME = SITE_NAME
LOG_DIR = os.path.join(CURRENT_DIR, 'log')
LOG_FILE = os.path.join(LOG_DIR, '%s.log' % LOGGER_NAME)

