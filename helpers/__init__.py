from flask import request

import simplejson as json


def format_time(millis, format = "%d:%02d"):
    minutes = millis / 60
    seconds = minutes * 60 
    if minutes > 1.0:
        seconds = minutes % math.floor(minutes) * 60
    return "%d:%02d" % (round(minutes), round(seconds))


def to_json(inst, cls):
    convert = dict()
    # add your coversions for things like datetime's 
    # and what-not that aren't serializable.
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type in convert.keys() and v is not None:
            try:
                d[c.name] = convert[c.type](v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
        return json.dumps(d)


def request_wants_json():
    """
    usage:
    from flask import jsonify, render_template

    @app.route('/')
    def show_items():
        items = get_items_from_database()
        if request_wants_json():
            return jsonify(items=[x.to_json() for x in items])
        return render_template('show_items.html', items=items)
    """
    best = request.accept_mimetypes \
            .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
            request.accept_mimetypes[best] > \
            request.accept_mimetypes['text/html']

