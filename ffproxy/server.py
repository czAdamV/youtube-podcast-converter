from .helpers import transcode
from flask import Flask, Blueprint, Response, request, current_app, send_file
from itertools import chain, product
import io
import json
import mimetypes
import requests


root_blueprint = Blueprint('root', __name__)


def create_app(conf=None):
    app = Flask(__name__)
    app.register_blueprint(root_blueprint)
    app.config.from_envvar('FFPROXY_CONFIG')

    # Turn ALLOWED_COMBINATIONS into a set of tuples and merge a cartesian
    # product of ALLOWED_FORMATS and ALLOWED_BITRATES into it.
    app.config['ALLOWED_COMBINATIONS'] = set(
        chain(
            (tuple(item) for item in app.config['ALLOWED_COMBINATIONS']),
            product(
                app.config['ALLOWED_FORMATS'],
                app.config['ALLOWED_BITRATES']
            )
        )
    )

    # todo maybe check validity of app.config['ALLOWED_COMBINATIONS']

    app.config['DEFAULT_COMBINATION'] = tuple(
        app.config['DEFAULT_COMBINATION']
    )

    if app.config['DEFAULT_COMBINATION'] not in \
       app.config['ALLOWED_COMBINATIONS']:
        raise RuntimeError(
            'Default combination is not in allowed combinations set.'
        )

    return app


@root_blueprint.route('/download/<video_id>')
def proxy(video_id):
    default_combination = current_app.config['DEFAULT_COMBINATION']
    allowed_combinations = current_app.config['ALLOWED_COMBINATIONS']
    encoder_translate = current_app.config['FORMAT_ENCODER_TRANSLATE']

    if 'format' not in request.args and 'bitrate' not in request.args:
        format = default_combination[0]
        bitrate = default_combination[1]

    elif 'format' not in request.args or 'bitrate' not in request.args:
        return 'Either both format and bitrate args should be requested, ' \
               'or none of them.', 400

    else:
        format = request.args.get('format')
        bitrate = int(request.args.get('bitrate'))

    if (format, bitrate) not in allowed_combinations:
        return 'This combination of format and bitrate is not allowed.', 400

    encoder = encoder_translate.get(format, format)

    try:
        r = requests.get(
            current_app.config['PROXY_PASS'].format(video_id=video_id)
        )
    except requests.exceptions.RequestException as e:
        return f'Gateway error', 502

    if r.status_code != 200:
        return 'Gateway error, upstream responded with ' \
               'unexpected status code', 502

    try:
        output = transcode(r.content, encoder, bitrate)
    except RuntimeError as e:
        return f'Transcode error: {e}', 500

    return send_file(
        io.BytesIO(output),
        mimetype=mimetypes.guess_type(f'a.{format}')[0]
    )


@root_blueprint.route('/', methods=['GET'])
def root():
    return Response(
        json.dumps({
            'allowed_formats': list(
                current_app.config['ALLOWED_COMBINATIONS']
            ),
            'default_format': current_app.config['DEFAULT_COMBINATION']
        }),
        mimetype='application/json'
    )
