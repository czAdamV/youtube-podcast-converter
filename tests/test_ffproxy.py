from ffproxy import create_app
import pathlib
import pytest


class SampleConf:
    def __init__(self):
        self.ALLOWED_FORMATS = ['mp3', 'aac']
        self.ALLOWED_BITRATES = [1, 2]
        self.ALLOWED_COMBINATIONS = [
            ['mp3', 3]
        ]
        self.DEFAULT_COMBINATION = ['mp3', 3]
        self.FORMAT_ENCODER_TRANSLATE = {'aac': 'adts'}
        self.PROXY_PASS = 'http://example.com/download/{video_id}'


@pytest.fixture
def app():
    app = create_app(SampleConf())
    app.config['TESTING'] = True
    return app


class TestInitialization:
    def test_create_app_no_conf(self):
        with pytest.raises(RuntimeError) as e:
            create_app()

        assert 'FFPROXY_CONFIG' in str(e.value)

    def test_create_app(self):
        app = create_app(SampleConf())

        assert app.config['ALLOWED_COMBINATIONS'] == set([
                ('mp3', 1), ('mp3', 2), ('mp3', 3), ('aac', 1), ('aac', 2)])

        assert app.config['DEFAULT_COMBINATION'] == tuple(['mp3', 3])
        assert app.config['FORMAT_ENCODER_TRANSLATE'] == {'aac': 'adts'}

    def test_create_app_invalid_default(self):
        conf = SampleConf()
        conf.DEFAULT_COMBINATION = ['aac', 3]

        with pytest.raises(RuntimeError) as e:
            create_app(conf)

        assert 'Default combination is not in allowed combinations set' \
               in str(e.value)


class TestAPI:
    @pytest.mark.block_network
    def test_root(self, app):
        request = app.test_client().get('/')
        assert request.status_code == 200
        data = request.get_json()

        assert set(tuple(item) for item in data['allowed_formats']) == \
            set([('mp3', 1), ('mp3', 2), ('mp3', 3), ('aac', 1), ('aac', 2)])

        assert data['default_format'] == ['mp3', 3]

    @pytest.mark.block_network
    @pytest.mark.parametrize("param,value", [
        ('format', 'mp3'), ('bitrate', '2')])
    def test_require_both_parameters(self, app, param, value):
        request = app.test_client().get(
            f'/download/7spQqq1o36c?{param}={value}')

        assert request.status_code == 400
        assert b'Either both format and bitrate args should be requested, ' \
               b'or none of them.' in request.data

    @pytest.mark.block_network
    def test_invalid_combination(self, app):
        request = app.test_client().get(
            '/download/7spQqq1o36c?format=aac&bitrate=3')

        assert request.status_code == 400
        assert b'This combination of format and bitrate is not allowed' \
               in request.data

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/ytproxy_response.yaml')
    def test_download_simple(self, app):
        request = app.test_client().get('/download/7spQqq1o36c')

        assert request.status_code == 200

    @pytest.mark.vcr(str(pathlib.Path(__file__).parent.absolute()) +
                     '/cassettes/ytproxy_response.yaml')
    @pytest.mark.parametrize("format,bitrate", [
        ('mp3', '1'),
        ('mp3', '2'),
        ('mp3', '3'),
        ('aac', '1'),
        ('aac', '2'),
    ])
    def test_download_formats(self, app, format, bitrate):
        request = app.test_client().get(
            f'/download/7spQqq1o36c?format={format}&bitrate={bitrate}')

        assert request.status_code == 200

    @pytest.mark.vcr
    def test_nonexistent_video(self, app):
        request = app.test_client().get(f'/download/12345678912')

        assert request.status_code == 404
        assert b'Video not found' in request.data

    @pytest.mark.vcr
    def test_invalid_id(self, app):
        request = app.test_client().get(f'/download/a')

        assert request.status_code == 400
        assert b'Invalid video_id' in request.data

    @pytest.mark.vcr
    def test_gateway_error(self, app):
        request = app.test_client().get('/download/12345678912')

        assert request.status_code == 502
        assert b'Gateway error' in request.data

    @pytest.mark.vcr
    def test_ffmpeg_error(self, app):
        request = app.test_client().get('/download/12345678912')

        assert request.status_code == 500
        assert b'Invalid data' in request.data
