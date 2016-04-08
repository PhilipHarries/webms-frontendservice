from flask import Flask, abort, make_response, url_for, send_file, jsonify
from flask import redirect, render_template
from flask.ext.pymongo import PyMongo
import logging
import requests
from logging.handlers import RotatingFileHandler
import cStringIO


# should rewrite the abort handlers to return (helpful) html

debug = False

handler = RotatingFileHandler('./logs/frontendservice.log', maxBytes=40960, backupCount=3)
handler.setLevel(logging.DEBUG)

# set the project root directory as the static folder
app = Flask(__name__, static_url_path='/static')

app.logger.addHandler(handler)
log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)
log.addHandler(handler)


def debug_print(s):
    app.logger.debug(s)
    if(debug):
        print s


def error_print(e):
    app.logger.error(e)
    if(debug):
        print e

# connect to mongo with defaults
mongo = PyMongo(app)

blog_service_url = "http://localhost:5434/blog/api/v1.0"
flickr_service_url = "http://localhost:5433/flickr/api/v1.0"
flickr_userid = "Philip_UK"


@app.errorhandler(404)
def not_found(error):
    debug_print(error)
    return make_response(jsonify({'error': '404: not found'}), 404)


@app.errorhandler(400)
def bad_request(error):
    debug_print(error)
    return make_response(jsonify({'error': '400: bad request'}), 400)


@app.errorhandler(409)
def duplicate_resource(error):
    debug_print(error)
    return make_response(jsonify({'error': '409: duplicate resource id'}), 409)


@app.errorhandler(500)
def internal_server_error(error):
    debug_print(error)
    return make_response(jsonify({'error': '500: internal server error'}), 500)


@app.errorhandler(501)
def not_implemented(error):
    debug_print(error)
    return make_response(jsonify({'error': '501: HTTP request not understood in this context'}), 501)


@app.errorhandler(502)
def bad_gateway(error):
    debug_print(error)
    return make_response(jsonify({'error': '502: server received an invalid response from an upstream server'}), 502)


@app.errorhandler(503)
def service_unavailable(error):
    debug_print(error)
    return make_response(jsonify({'error': '503: service unavailable - try back later'}), 503)


@app.errorhandler(504)
def gateway_timeout(error):
    debug_print(error)
    return make_response(jsonify({'error': '504: upstream timeout - the server stopped waiting for a response from upstream'}), 504)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', name="Philip")


@app.route('/blogs', methods=['GET'])
def get_blogs():
    r = requests.get("{}/blogs".format(blog_service_url))
    if r.status_code == 200:
        blogs = r.json()["blogs"]
        blogs.reverse()
        return render_template('blogs_index.html', blogs=blogs)
    else:
        debug_print("blog microservice threw an error: {}".format(r.json()))
        abort(502)


@app.route('/blog/<string:blog_id>', methods=['GET'])
def get_blog(blog_id):
    r = requests.get("{}/blogs".format(blog_service_url))
    if r.status_code == 404:
        abort(404)
    blogs = r.json()["blogs"]
    count = 0
    for blog in blogs:
        if blog["id"] == blog_id:
            break
        count = count + 1
    return render_template('blog.html', blogs=blogs, count=count)


@app.route('/albums', methods=['GET'])
def get_photos():
    albums = []
    debug_print("Contacting {}/albums/{}".format(flickr_service_url, flickr_userid))
    albums_request = requests.get("{}/albums/{}".format(flickr_service_url, flickr_userid))
    for album in albums_request.json()["albums"]:
        if album["id"] != "cacheInfo":
            albums.append(album)
    return render_template('albums_index.html', albums=albums)


@app.route('/album/<string:album_id>', methods=['GET'])
def get_album(album_id):
    debug_print("Contacting {}/album/{}/{}".format(flickr_service_url, flickr_userid, album_id))
    album_request = requests.get("{}/album/{}/{}".format(flickr_service_url, flickr_userid, album_id))
    if album_request.status_code == 404:
        abort(404)
    elif album_request.status_code == 500:
        abort(500)
    debug_print(album_request.json())
    album = album_request.json()["album"]
    return render_template('album.html', album=album)


@app.route('/slideshow/<string:album_id>', methods=['GET'])
def get_slideshow_default_chunk(album_id):
    return redirect(url_for('get_slideshow', album_id=album_id, chunk_num=1, _external=False))


@app.route('/slideshow/<string:album_id>/<int:chunk_num>', methods=['GET'])
def get_slideshow(album_id, chunk_num):
    chunk_size = 8
    chunk_num = chunk_num - 1
    debug_print("Contacting {}/album/{}/{}/{}/{}".format(flickr_service_url, flickr_userid, album_id, chunk_size, chunk_num))
    album_request = requests.get("{}/album/{}/{}/{}/{}".format(flickr_service_url, flickr_userid, album_id, chunk_size, chunk_num))
    if album_request.status_code == 404:
        abort(404)
    elif album_request.status_code == 500:
        abort(500)
    debug_print(album_request.json())
    album = album_request.json()["album"]
    return render_template('slideshow.html', album=album)


@app.route('/image/flickr/<string:user_id>/<string:album_id>/<string:image_id>/<string:image_type>', methods=['GET'])
def get_image(user_id, album_id, image_id, image_type):
    debug_print("Contacting {}/{}/{}/{}/{}".format(flickr_service_url, image_type, flickr_userid, album_id, image_id))
    image_request = requests.get("{}/{}/{}/{}/{}".format(flickr_service_url, image_type, flickr_userid, album_id, image_id))
    if image_request.status_code == 404:
        abort(404)
    elif image_request.status_code == 500:
        abort(500)

    img_io = cStringIO.StringIO()
    img_io.write(image_request.content)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
