from collections import deque
import googleapiclient.discovery


class NotFoundError(RuntimeError):
    pass


class youtube_api:
    def __init__(self, api_key):
        self.session = googleapiclient.discovery.build(
            'youtube', 'v3', developerKey=api_key)

    def __get_playlist_page(self, playlist, page_token=None, max_results=None):
        return self.session.playlistItems().list(
            part="contentDetails,snippet",
            maxResults=max_results,
            pageToken=page_token,
            playlistId=playlist
        ).execute()

    def __playlist_pages(self, playlist):
        page = None
        while True:
            response = self.__get_playlist_page(playlist, page, 50)
            page = response.get('nextPageToken')
            yield response

            if not page:
                break

    def playlist_info(self, playlist):
        items = self.session.playlists().list(
            part="contentDetails,id,snippet",
            id=playlist
        ).execute()['items']

        if not items:
            raise NotFoundError('Couldn\'t find specified playlist.')

        info = items[0]

        # return info
        return {
            'playlist_id': info['id'],
            'title': info['snippet']['title'],
            'description': info['snippet']['description'],
            'channel_title': info['snippet']['channelTitle'],
            'thumbnail_url': info['snippet']['thumbnails']['default']['url'],
        }

    def playlist_videos(self, playlist):
        for page in self.__playlist_pages(playlist):
            for item in page['items']:
                yield {
                    'video_id': item['contentDetails']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['contentDetails']['videoPublishedAt'],
                }
