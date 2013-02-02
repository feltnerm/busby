#!/usr/bin/env python

from flask import Flask


def configure_app(app, filename):

    import os.path

    app.config.from_pyfile(os.path.abspath('settings_default.py'))
    try:
        app.config.from_pyfile(os.path.abspath(filename))
    except IOError, e:
        print e
    app.logger.info("Configuration file: %s" % filename)


def configure_before_handlers(app):
    pass
    """
    @app.before_request
    def authenticate():
        g.user = getattr(g.identity, 'user', None)
    """


def configure_error_handlers(app):

    from flask import (jsonify, redirect, request, url_for)
    from helpers import request_wants_json

    def make_json_error(error, code):
        response = jsonify(message=str(error))
        response.status_code = code
        return response

    @app.errorhandler(401)
    def unauthorized(error):
        return make_json_error(error, 401)

    @app.errorhandler(403)
    def forbidden(error):
        return make_json_error(error, 403)

    @app.errorhandler(404)
    def page_not_found(error):
        return make_json_error(error, 404)

    @app.errorhandler(413)
    def entity_too_large(error):
        return make_json_error(error, 413)

    @app.errorhandler(415)
    def unsupported_media(error):
        return make_json_error(error, 415)

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error("Server error! %s" % error)
        return make_json_error(error, 500)

    @app.errorhandler(501)
    def not_implemented(error):
        return make_json_error(error, 501)


def configure_extensions(app):

    from extensions import cache, db, mail, Login 

    # initialize mail
    mail = mail.init_app(app)

    # initialize cache
    cache = cache.init_app(app)

    # initialize database
    db.init_app(app)
    app.logger.info("Database initialized.")
    db.app = app
    db.metadata.bind = db.get_engine(app)
    db.metadata.reflect()
    app.logger.info("Database tables reflected.")
    from models import User
    db.create_all(bind=['users'])

    # login
    Login.manager.setup_app(app)
    @Login.manager.user_loader
    def load_user(userid):
        return User.query.get(userid)

    @Login.manager.token_loader
    def load_token(token):
        return User.query.filter(User.passkey == token).first()


def configure_logging(app):

    from logbook import Logger
    from logbook import (NestedSetup, FileHandler, StreamHandler,
            NullHandler)
    from logbook.compat import RedirectLoggingHandler
    app.logger = Logger('bassradio')


def configure_routes(app):

    from views import (AlbumView, ArtistView, FileView, ListView,
            SongView, QueryView, UserView)

    default_url_prefix = '/api'
    for view, prefix in (
            (AlbumView, '/album'), 
            (ArtistView, '/artist'),
            (FileView, '/file'),
            (SongView, '/song'),
            (QueryView, '/query'),
            (ListView, '/list'),
            (UserView, '/user'),):
        api_url_prefix = default_url_prefix + prefix
        app.register_blueprint(view.api, url_prefix=api_url_prefix)
        app.logger.info("Blueprint: <%s> added." % view.api)


def init_app(config='settings_prod.py'):

    app = Flask(__name__)

    configure_app(app, config)
    configure_before_handlers(app)
    configure_error_handlers(app)
    configure_extensions(app)
    configure_routes(app)

    if not app.debug:
        app.logger.info("Applying proxy fix.")

        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

    #if app.debug:

    #    from pprint import pprint
    #    confstr = ""
    #    for key, val in app.config.iteritems():
    #        confstr += "  %s: %s\n" % (key, val)
    #    app.logger.info(confstr)

    return app
