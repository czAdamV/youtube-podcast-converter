from ytproxy import create_app
from base64 import a85decode as decode
import io
import pathlib
import pytest
import pytube
import urllib

# A minimalistic valid WAV file. Used by YouTubeMock to moct output of valid
# audio stream. It would be nice if a slnt RIFF chunk could be used to make
# the audio a bit longer but it seems ffmpeg doesn't support that :(
audio = decode(";Fs>I-3+#G=$]kUAo2W4&-)\\1!<<-#7'$@g7'$@g!<<B*A79Rg!<<*\"J,f")


class PyTubeMock:
    def __init__(self):
        self.extract = ExtractMock
        self.YouTube = YouTubeMock


class ExtractMock:
    def watch_url(url):
        return url


class YouTubeMock:
    def __init__(self, uri):
        if 'invalid' in uri:
            raise pytube.exceptions.RegexMatchError('', '')

        if 'nonexistent' in uri:
            raise pytube.exceptions.VideoUnavailable('')

        if 'livestream' in uri:
            raise pytube.exceptions.LiveStreamError()

        if 'generic_error' in uri:
            raise pytube.exceptions.PytubeError()

        if 'connection_error' in uri:
            raise urllib.error.URLError('test')

        self.streams = YouTubeMockStreams()


class YouTubeMockStreams:
    def get_audio_only(self):
        return YouTubeMockAudioOnly()


class YouTubeMockAudioOnly:
    def __init__(self):
        self.mime_type = 'audio/wav'

    def stream_to_buffer(self):
        return io.BytesIO(audio)


@pytest.fixture
def app():
    app = create_app(PyTubeMock())
    app.config['TESTING'] = True
    return app


class TestAPI:
    def test_root(self, app):
        request = app.test_client().get('/')
        assert request.status_code == 200
        data = request.get_json()

        assert 'allowed_formats' in data
        assert data['allowed_formats'] == []

    @pytest.mark.parametrize("uri,code,body", [
        ('invalid', 400, b'Invalid video_id'),
        ('nonexistent', 404, b'Video does not exist'),
        ('livestream', 400, b'Video is a live stream'),
        ('generic_error', 500, b'Couldn\'t process request'),
        ('connection_error', 502, b'Bad gateway')])
    def test_errors(self, app, uri, code, body):
        request = app.test_client().get(f'/download/{uri}')

        assert request.status_code == code
        assert body in request.data

    def test_download(self, app):
        request = app.test_client().get('/download/7spQqq1o36c')

        assert request.status_code == 200
