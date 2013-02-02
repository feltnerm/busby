import math
import hashlib
import os
from datetime import datetime

from flask import abort

from unidecode import unidecode
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import format_time, to_json
from extensions import db
from flask.ext.login import make_secure_token

from logging import getLogger
logger = getLogger("bassradio")


class User(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(80))
    activated = db.Column(db.Boolean)
    pwdhash = db.Column(db.String)
    invite_code = db.Column(db.String)
    passkey = db.Column(db.String)
    creation = db.Column(db.Date)

    def to_json(self):
        return {
                'id': self.id,
                'username': self.username,
                'email': self.email,
                'passkey': self.passkey,
                'activated': self.activated
                }

    def __init__(self, email):
        self.email = email
        self.activated = False
        self.invite_code = hashlib.sha1(os.urandom(42)).hexdigest()
        self.created = datetime.utcnow()

    def activate(self, username, password):
        self.username = username
        self.pwdhash = self.make_password(password)
        self.passkey = self.make_passkey(self.pwdhash)
        self.activated = True
        self.creation = datetime.utcnow()

    def make_passkey(self, string):
        return make_secure_token(string)

    def make_password(self, password):
        pwdhash = generate_password_hash(password)
        return pwdhash

    def check_password(self, password):
       return check_password_hash(self.pwdhash, password)

    def __str__(self):
        return "<User %r>" % (self.username)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.activated

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def get_auth_token(self):
        return self.passkey

class AlbumQuery(db.Query):

    def as_list(self, key, value=None):
        filter_mapping = {
                'album': Album.album
            }

        if key not in filter_mapping:
            abort(404)

        if value is None:
            query = self(filter_mapping[key]).distinct()
        else:
            query = self.filter(filter_mapping[key].startswith(value))
        
        return query

    def sort(self):
        return self.order_by(Album.year) \
                .order_by(Album.album) \

    def to_json(self):
        for i in self.all():
            yield i.json


class Album(db.Model):
    __table__ = db.Table('albums', db.metadata, autoload=True)
    __tablename__ = 'albums'
    query_class = AlbumQuery

    def sort(self):
        return self.order_by(Album.name) \
                .order_by(Album.year) \
                .order_by(Album.disc) \
                .order_by(Album.artist) \

    @property
    def json(self):

        result = dict.fromkeys([key for key in self.__table__.columns.keys()])
        for key in result.iterkeys():
            result[key] = getattr(self, key, None)

        return result

    @property
    def length_formatted(self):
        return format_time(self.length)


class ItemQuery(db.Query):

    def as_list(self, key, value=None):
        filter_mapping = {
                'artist': Item.artist,
                'title': Item.title
            }
        if key not in filter_mapping:
            abort(404)

        if value is None:
            query = self.filter(filter_mapping[key]).distinct()
        else:
            query = self.filter(filter_mapping[key].startswith(value))
        
        return query

    def sort(self):
        return self.order_by(Item.artist) \
                .order_by(Item.year) \
                .order_by(Item.album) \
                .order_by(Item.disc) \
                .order_by(Item.track) \
                .order_by(Item.title)

    def to_json(self):
        for i in self.all():
            yield  i.json


class Item(db.Model):
    __table__ = db.Table('items', db.metadata, autoload=True)
    __tablename__ = 'items'
    query_class = ItemQuery

    @property
    def json(self):

        result = dict.fromkeys([key for key in self.__table__.columns.keys()])
        for key in result.iterkeys():
            val = getattr(self, key, None)
            if (isinstance(val, unicode) or 
                isinstance(val, str)):
                try:
                    val = unidecode(val)
                    result[key] = val
                except:
                    pass
                    #raise Exception((repr(val), type(val)))
            else:
                result[key] = val

        return result


    @property
    def length_formatted(self):
        return format_time(self.length)
