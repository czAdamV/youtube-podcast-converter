from ytfeed import create_app, NotFoundError
import pathlib
import pytest


class SampleConf:
    def __init__(self):
        self.DEVELOPER_KEY = "foo"
        self.FEED_BACKEND = 'http://example.com/'


class YouTubeMock:
    def __init__(self, key):
        pass

    def playlist_info(self, playlist_id):
        if 'nonexistent_playlist' in playlist_id:
            raise NotFoundError()

        return {
            'title': 'Test playlist',
            'description': 'Playlist used for testing purposes',
            'playlist_id': playlist_id,
            'channel_title': 'Meow',
            'thumbnail_url': 'http://example.com/thumb.jpg',
        }

    def playlist_videos(self, playlist_id):
        return [
            {
                'video_id': '12345678912',
                'title': 'Testing video 1',
                'description': 'Video description',
                'published_at': '2020-02-02T12:00:00.000Z',
            },
            {
                'video_id': '12345678913',
                'title': 'Testing video 2',
                'description': 'Different video description',
                'published_at': '2020-02-02T13:00:00.000Z',
            },
        ]


@pytest.fixture
def app():
    app = create_app(SampleConf(), YouTubeMock)
    app.config['TESTING'] = True
    return app


class TestInitialization:
    def test_no_backend(self):
        conf = SampleConf()
        del conf.FEED_BACKEND

        with pytest.raises(RuntimeError) as e:
            create_app(conf)

        assert 'FEED_BACKEND variable not configured' in str(e.value)

    @pytest.mark.vcr
    def test_backend_error(self):
        with pytest.raises(RuntimeError) as e:
            create_app(SampleConf())

        assert 'Backend returned unexpected status code' in str(e.value)

    @pytest.mark.vcr
    def test_invalid_backend_response(self):
        with pytest.raises(RuntimeError) as e:
            create_app(SampleConf())

        assert 'Invalid json in backend response' in str(e.value)

    @pytest.mark.vcr
    @pytest.mark.skip(reason="This feature is not implemented yet.")
    def test_keyless(self):
        conf = SampleConf()
        del conf.DEVELOPER_KEY

        create_app(conf)

    @pytest.mark.vcr
    def test_initialization_simple(self):
        app = create_app(SampleConf(), YouTubeMock)

        assert app.config['ALLOWED_FORMATS'] == set()
        assert not app.config['FORMAT_BACKEND']

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/format_backend_root.yaml')
    def test_initialization_format(self):
        app = create_app(SampleConf(), YouTubeMock)

        assert app.config['ALLOWED_FORMATS'] == set([
                ('mp3', 1), ('mp3', 2), ('mp3', 3), ('aac', 1), ('aac', 2)])

        assert app.config['DEFAULT_FORMAT'] == tuple(['mp3', 3])
        assert app.config['FORMAT_BACKEND']


class TestAPI:
    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/format_backend_root.yaml')
    def test_root(self, app):
        request = app.test_client().get('/')
        assert request.status_code == 200
        data = request.get_json()

        assert 'allowed_formats' in data
        assert set(tuple(item) for item in data['allowed_formats']) == set([
                ('mp3', 1), ('mp3', 2), ('mp3', 3), ('aac', 1), ('aac', 2)])

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/format_backend_root.yaml')
    def test_invalid_type(self, app):
        request = app.test_client().get('/playlist.xml')
        assert request.status_code == 404

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/format_backend_root.yaml')
    def test_nonexistent(self, app):
        request = app.test_client().get(
            '/nonexistent_playlist.atom')
        assert request.status_code == 404

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/format_backend_root.yaml')
    def test_rss(self, app):
        request = app.test_client().get(
            '/PLFsQleAWXsj_4yDeebiIADdH5FMayBiJo.rss')
        assert request.status_code == 200
        # todo some very basic validity tests

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/format_backend_root.yaml')
    def test_atom(self, app):
        request = app.test_client().get(
            '/PLFsQleAWXsj_4yDeebiIADdH5FMayBiJo.atom')
        assert request.status_code == 200
        # todo some very basic validity tests
