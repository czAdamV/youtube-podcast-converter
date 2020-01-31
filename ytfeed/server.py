from .youtube import youtube_api, NotFoundError
from feedgen.feed import FeedGenerator
from flask import Flask, Blueprint, Response, current_app, abort
import json
import mimetypes
import requests


ytfeed_blueprint = Blueprint('ytfeed', __name__)


def create_app(conf=None):
    app = Flask(__name__)
    app.register_blueprint(ytfeed_blueprint)
    app.config.from_envvar('YTFEED_CONFIG')

    try:
        r = requests.get(app.config['BACKEND'])

        if r.status_code != 200:
            raise RuntimeError('Backend returned unexpected status code.')

        app.config['ALLOWED_FORMATS'] = set(
            tuple(item) for item in r.json()['allowed_formats']
        )
        app.config['FORMAT_BACKEND'] = len(app.config['ALLOWED_FORMATS']) != 0
        app.config['DEFAULT_FORMAT'] = \
            r.json()['default_format'] if app.config['FORMAT_BACKEND'] else ''
    except Exception as e:
        raise RuntimeError(
            f'Error when communicatin with backend server. {e}'
        ) from e

    if 'DEVELOPER_KEY' in app.config:
        app.config['SESSION'] = youtube_api(app.config['DEVELOPER_KEY'])

    else:
        raise NotImplementedError(
            'DEVELOPER_KEY not configured, '
            'keyless operation is not yet implemented'
        )

    return app


@ytfeed_blueprint.route('/<playlist_id>.<any(rss, atom):type>')
def playlist(playlist_id, type):
    session = current_app.config['SESSION']
    try:
        info = session.playlist_info(playlist_id)
    except NotFoundError as e:
        abort(404)

    videos = list(session.playlist_videos(playlist_id))

    description = info['description']
    link = f"https://www.youtube.com/playlist?list={info['playlist_id']}"
    other_type = 'atom' if type == 'rss' else 'rss'

    fg = FeedGenerator()
    fg.id(f"ytfeed-{playlist_id}")
    fg.title(info['title'])
    fg.description(description if description else 'No description')
    fg.author({'name': info['channel_title']})
    fg.link(href=link, rel='alternate')
    fg.link(href=f'{playlist_id}.{other_type}', rel='self')
    fg.logo(info['thumbnail_url'])

    for video in reversed(videos):
        video_id = video['video_id']
        description = video['description']
        item_link = f'https://www.youtube.com/watch?v={video_id}'
        mime_type = mimetypes.guess_type(
            f'a.{current_app.config["DEFAULT_FORMAT"][0]}'
        )[0] if current_app.config['FORMAT_BACKEND'] else 'audio/unknown'

        fe = fg.add_entry()

        fe.id(video_id)
        fe.title(video['title'])
        fe.description(description if description else 'No description')
        fe.link({'href': item_link, 'rel': 'alternate'})
        fe.published(video['published_at'])
        fe.enclosure(
            f'{current_app.config["BACKEND"]}download/{video_id}',
            0,
            mime_type
        )

    return Response(
        fg.rss_str() if type == 'rss' else fg.atom_str(),
        mimetype=f'application/{type}+xml')
    return fg.rss_str()


@ytfeed_blueprint.route('/')
def root():
    return Response(
        json.dumps({
            'allowed_formats': list(
                current_app.config['ALLOWED_FORMATS']
            ),
            'default_format': current_app.config['DEFAULT_FORMAT']
        }),
        mimetype='application/json'
    )
