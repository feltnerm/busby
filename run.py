#!/usr/bin/env python
import sys
import argparse
from pprint import pprint

from werkzeug import script

from app import init_app
from extensions import db

def make_shell(app):
    return dict(app=app,
            db_session=db.session,
            db_metadata=db.metadata)
    
def parse_args(args_list):
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument('debug', action='store_true', default=False)
    ap.add_argument('--host', default='0.0.0.0')
    ap.add_argument('-p', '--port', default=5000)
    ap.add_argument('-c', '--config', default="settings_prod.py")
    ap.add_argument('-s', '--shell',  action='store_true', default=False)

    args = ap.parse_args(args_list)
    return args


def main(argv=None):

    if not argv:
        argv = sys.argv[1:]

    options = parse_args(argv)

    app = init_app(options.config)

    if options.shell:
        script.make_shell(make_shell, use_ipython=True)
    else:
        app.run(host=options.host, port=int(options.port))

    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
else:
    app = init_app('settings_prod.py')
