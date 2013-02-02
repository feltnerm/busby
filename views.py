import shlex
import os
import os.path

import simplejson as json 
import mimetypes

from flask import (abort, current_app, Blueprint, jsonify, request, send_file, 
        Response)
from werkzeug.datastructures import Headers
from werkzeug.utils import secure_filename

from flask.ext.login import login_required, make_secure_token
from flask.ext.mail import Message

from extensions import db, mail, cache, logout_user, login_user
from helpers.streams import send_file_partial
from models import Item, Album, User


class UserView:
    api = Blueprint('users', __name__)
    @login_required
    @api.route("/u/<username>")
    def get(username):
        user = User.query.filter(User.username == username).first()
        if user:
            return jsonify(user.to_json())
        return abort(404)
    

    @api.route("/login", methods=["POST"])
    def login():
        username = request.values.get('username')
        password = request.values.get('password')

        potential_user = User.query.filter(User.username == username).first()
        current_app.logger.info(potential_user)
        if potential_user is None:
            return jsonify(error="Invalid username.")
        elif not potential_user.check_password(password):
            return jsonify(error="Invalid password.")
        login_user(potential_user)
        return jsonify(potential_user.to_json())

    @login_required
    @api.route("/invite", methods=["POST"])
    def invite():
        email = request.values.get("email")
        new_user = User(email)
        db.session.add(new_user)
        db.session.commit()
        #msg = Message(
        #        "Register here: http://nalanda.bd.to/#/register/?token=%s" 
        #        % new_user.invite_code, 
        #        recipients=[email])

        #mail.send(msg)
        return jsonify(token=new_user.invite_code)


    @api.route("/register/<invite_code>", methods=["POST"])
    def register(invite_code):

        new_user = User.query.filter(User.activated != True).filter(User.invite_code == invite_code).first()
        username = request.values.get('username')
        password = request.values.get('password')

        if new_user:
            new_user.activate(username, password)
            db.session.commit()
            return jsonify(new_user.to_json())
        return jsonify(error="Invalid activation code.")


    @login_required
    @api.route("/logout", methods=["POST"])
    def logout():
        logout_user()
        return jsonify({})


class FileView:
    api = Blueprint('files', __name__)

    @login_required
    @api.route("/<int:id>.<ext>")
    @api.route("/<int:id>")
    def get(id, ext=None):
        item = Item.query.get_or_404(id)

        path = os.path.normpath(item.path)
        if not os.path.exists(path):
            return abort(404)
        headers = Headers()
        headers.add("X-Content-Duration", item.length)
        headers.add("X-Accel-Buffering", "no")
        range_header = request.headers.get('Range', None)
        if range_header is not None:
            range_header = range_header.split('-')
            try:
                range_header = intval(range_header[0])
            except:
                range_header = None

        current_app.logger.info(mimetypes.guess_type(item.path))
        return send_file_partial(item.path,
                    mimetype=mimetypes.guess_type(item.path)[0],
                    headers=headers,
                    attachment_filename=secure_filename(
                        "%d - %s - %s (%s)[%s]" %
                        (item.track, item.title,
                            item.artist, item.album,
                            item.year)))
        abort(404)

class ListView:
    api = Blueprint('lists', __name__)

    @login_required
    @api.route("/<string:key>", defaults={ 'value': '' })
    @api.route("/<string:key>/<string:value>")
    def list(key, value):
        query = None
        if key == 'album':
            query = Album.query.as_list(key, value).sort()
        else:
            query = Item.query.as_list(key, value).sort()

        if query is None:
            abort(404)

        if key in ('album', 'title'):
            result = sorted(set([(i.id, getattr(i, key)) for i in query]), key=lambda e: e[1].lower())
            result = dict(map(None, result))
        else:
            result = sorted(set([getattr(i, key) for i in query]))

        return Response(json.dumps(result),
                status=200,
                mimetype="application/json")

class SongView:
    api = Blueprint('songs', __name__)

    @login_required
    @api.route("/<int:id>")
    @api.route("/<int:id>/")
    def get(id):
        item = Item.query.get_or_404(id)
        result = {}
        result['song'] = item.json
        
        return jsonify(**result)


class AlbumView:
    api = Blueprint('albums', __name__)

    @login_required
    @api.route("/<int:id>")
    @api.route("/<int:id>/")
    def get(id):
        album_dict = {}
        album = Album.query.get_or_404(id)
        return jsonify(album.json)

    @cache.cached(timeout=300, key_prefix="covers")
    @login_required
    @api.route("/<int:id>/cover")
    @api.route("/<int:id>/cover/")
    def get_cover(id):
        album = Album.query.get_or_404(id)
        if album.artpath:
            if os.path.exists(album.artpath):
                return send_file(album.artpath)
        abort(404)

class ArtistView:
    api = Blueprint('artists', __name__)

    @login_required
    @api.route("/<string:name>")
    @api.route("/<string:name>/")
    def get(name):
        item = Item.query.filter(Item.artist == name).first()

        if not item:
            abort(404)

        return jsonify(artist=item.artist)


class QueryView:
    api = Blueprint('query', __name__)

    @login_required
    @api.route("/<string:object_type>/<string:search_query>")
    @api.route("/<string:object_type>", defaults={"search_query": ""})
    @api.route("/", defaults={"object_type": "", "search_query": ""})
    def query(object_type, search_query):

        if not search_query:
            search_query = object_type
            object_type = None

        offset = request.args.get('offset', 0, int)
        limit = request.args.get('limit', None, int)
        if offset < 0:
            offset = 0
        if limit is not None and limit < 0:
            limit = 0

        if 'includes' in request.args:
            includes = request.args.get('include').split("+")

        filter_map = { 
                "artist": Item.artist, 
                "album": Item.album, 
                "title": Item.title, 
                "id": Item.id, 
                "bitrate": Item.bitrate, 
                "album_id": Item.album_id,
                "albumartist": Item.albumartist,
                "genre": Item.genre,
                }
        if object_type == 'album':
            filter_map = { 
                    "album": Album.album, 
                    "id": Album.id, 
                    "artist": Album.albumartist,
                    "genre": Album.genre, 
                    "year": Album.year }

        filter_chain= None

        try:
            terms = shlex.split(search_query)
        except:
            return jsonify(total=0, offset=offset, songs=[])

        for term in terms:
            field = term.split(':', 1)
            if len(field) == 1 or field[0] not in filter_map:
                word = term.strip().replace("*", "%")
                if len(word) == 0:
                    continue
                term_filter = Item.id == word
                if object_type == "album":
                    term_filter = Album.id == word

                word = "%" + word + "%"
                for filter in filter_map:
                    term_filter |= filter_map[filter].ilike(word)
            else:
                term_filter = filter_map[field[0]].like(field[1].replace("*", "%"))
            if filter_chain is None:
                filter_chain = term_filter
            else:
                filter_chain &= term_filter

        query = Item.query
        if object_type == 'album':
            query = Album.query
        if filter_chain is not None:
            query = query.filter(filter_chain)

        total = query.count()
        query = query.sort().offset(offset)

        if limit is not None:
            query = query.limit(limit)
        
        items = [item.json for item in query]

        typ = object_type if object_type else "songs"
        result = {
                typ: items,
                'total': total,
                'offset': offset,
                'limit': limit
                }
        return jsonify(**result)
