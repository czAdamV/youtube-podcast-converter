from flask import Flask, Blueprint, send_file
import io
import json
import pytube
import urllib

root_blueprint = Blueprint('root', __name__)


def create_app(conf=None):
    app = Flask(__name__)
    app.register_blueprint(root_blueprint)

    return app


@root_blueprint.route('/download/<video_id>')
def download(video_id):
    try:
        stream = (
            pytube.YouTube(pytube.extract.watch_url(video_id))
            .streams
            .get_audio_only()
        )
        bytestream = stream.stream_to_buffer()

    except pytube.exceptions.RegexMatchError as e:
        return 'Invalid video_id', 400

    except pytube.exceptions.VideoUnavailable as e:
        return 'Video unavailable', 404

    except pytube.exceptions.LiveStreamError as e:
        return 'Video is a live stream', 400

    except pytube.exceptions.PytubeError as e:
        return f'Couldn\' process request: {e}', 500

    except urllib.error.URLError as e:
        return f'Bad gateway: {e}', 502

    # This is a workaround needed because of what I believe is a bug in
    # pytube3. Todo investigate the behavior and report it to the
    # developers if it really is a bug.
    bytestream.seek(0)

    return send_file(bytestream, mimetype=stream.mime_type,)
