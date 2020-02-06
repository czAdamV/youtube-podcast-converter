from ytproxy import create_app
import pathlib
import pytest


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


class TestAPI:
    def test_root(self, app):
        request = app.test_client().get('/')
        assert request.status_code == 200
        data = request.get_json()

        assert 'allowed_formats' in data
        assert data['allowed_formats'] == []

    @pytest.mark.block_network
    def test_invalid_video_id(self, app):
        request = app.test_client().get('/download/a')

        assert request.status_code == 400
        assert b'Invalid video_id' in request.data

    @pytest.mark.vcr
    def test_nonexistent_video(self, app):
        request = app.test_client().get('/download/12345678912')

        assert request.status_code == 404
        assert b'Video does not exist' in request.data

    @pytest.mark.vcr
    @pytest.mark.skip(reason='PyTube throws a KeyError instead of a '
                      'LiveStreamError when asked to download live stream. '
                      'This seems to be a bug in PyTube.')
    def test_is_livestream(self, app):
        request = app.test_client().get('/download/hHW1oY26kxQ')

        assert request.status_code == 400
        assert b'Video is a live stream' in request.data

    @pytest.mark.vcr
    def test_download(self, app):
        request = app.test_client().get('/download/7spQqq1o36c')

        assert request.status_code == 200
