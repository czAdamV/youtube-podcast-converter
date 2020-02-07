from flask import Flask, Blueprint, Response, current_app, send_file
import io
import json
import pytube
import urllib

ytproxy_blueprint = Blueprint('ytproxy', __name__)


def create_app(pytube_module=None):
    """Create a configured Flask application

    :param pytube_module: Alternative pytube module used for testing
    :type  pytube_module: object, optional

    :return: Flask application
    :rtype:  class:`flask.app.Flask`
    """
    app = Flask(__name__)
    app.register_blueprint(ytproxy_blueprint)

    app.config['PYTUBE'] = pytube_module or pytube

    return app


@ytproxy_blueprint.route('/download/<video_id>')
def download(video_id):
    """Audio download endpoint

    :param video_id: video id
    :type  video_id: str
    """
    pytube_module = current_app.config['PYTUBE']
    youtube = pytube_module.YouTube
    watch_url = pytube_module.extract.watch_url

    try:
        stream = (
            youtube(watch_url(video_id))
            .streams
            .get_audio_only()
        )
        bytestream = stream.stream_to_buffer()

    except pytube.exceptions.RegexMatchError as e:
        return 'Invalid video_id', 400

    except pytube.exceptions.VideoUnavailable as e:
        return 'Video does not exist', 404

    except pytube.exceptions.LiveStreamError as e:
        return 'Video is a live stream', 400

    except pytube.exceptions.PytubeError as e:
        return f'Couldn\'t process request: {e}', 500

    except urllib.error.URLError as e:
        return f'Bad gateway: {e}', 502

    # This is a workaround needed because of what I believe is a bug in
    # pytube3. Todo investigate the behavior and report it to the
    # developers if it really is a bug.
    bytestream.seek(0)

    return send_file(bytestream, mimetype=stream.mime_type)


@ytproxy_blueprint.route('/')
def root():
    """Root web entry point, returns information about supported formats.
    """
    return Response(
        json.dumps({'allowed_formats': []}),
        mimetype='application/json'
    )
