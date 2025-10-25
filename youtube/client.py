import os
import time
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timedelta
import pytz
from .thumbnail import generate_thumbnail

class YouTubeClient:
    def __init__(self, credentials_file, token_file, proxy=None):
        """
        Initializes the YouTube client.

        Args:
            credentials_file (str): Path to the credentials file.
            token_file (str): Path to the token file.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        self.youtube = self._build_youtube_service(proxy)

    def _build_youtube_service(self, proxy=None):
        """
        Build the YouTube service using OAuth 2.0 credentials.

        This method handles the OAuth 2.0 flow, including storing and refreshing credentials.
        """
        if proxy:
            os.environ['HTTP_PROXY'] = proxy
            os.environ['HTTPS_PROXY'] = proxy

        credentials = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            credentials = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(google.auth.transport.requests.Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(credentials.to_json())

        return build('youtube', 'v3', credentials=credentials)

    def get_stream(self, title):
        """Gets a stream by title."""
        request = self.youtube.liveStreams().list(
            part="id,snippet,cdn,status",
            mine=True
        )
        response = request.execute()
        for stream in response.get("items", []):
            if stream["snippet"]["title"] == title:
                return stream
        return None

    def create_live_broadcast(self, title, description, privacy_status):
        """
        Creates a live broadcast.

        Args:
            title (str): The title of the broadcast.
            description (str): The description of the broadcast.
            privacy_status (str): The privacy status of the broadcast (e.g., "public", "private", "unlisted").

        Returns:
            tuple: A tuple containing the created broadcast and stream resources.
        """
        now = datetime.now(pytz.utc)
        scheduled_start_time = now.isoformat()

        broadcast_request = self.youtube.liveBroadcasts().insert(
            part="snippet,status,contentDetails",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "scheduledStartTime": scheduled_start_time
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                },
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True
                }
            }
        )
        broadcast_response = broadcast_request.execute()

        stream_title = "Default Stream Key"
        stream_response = self.get_stream(stream_title)

        if not stream_response:
            stream_request = self.youtube.liveStreams().insert(
                part="snippet,cdn",
                body={
                    "snippet": {
                        "title": stream_title
                    },
                    "cdn": {
                        "format": "1080p",
                        "ingestionType": "rtmp",
                        "resolution": "1080p",
                        "frameRate": "30fps"
                    }
                }
            )
            stream_response = stream_request.execute()

        bind_request = self.youtube.liveBroadcasts().bind(
            part="id,contentDetails,status",
            id=broadcast_response["id"],
            streamId=stream_response["id"]
        )
        broadcast_response = bind_request.execute()

        return broadcast_response, stream_response

    def get_live_broadcast_status(self, broadcast_id):
        """
        Gets the status of a live broadcast.

        Args:
            broadcast_id (str): The ID of the broadcast.

        Returns:
            str: The status of the broadcast.
        """
        request = self.youtube.liveBroadcasts().list(
            part="status",
            id=broadcast_id
        )
        response = request.execute()

        if response["items"]:
            return response["items"][0]["status"]["lifeCycleStatus"]
        
    def close_live_broadcast(self, broadcast_id):
        """
        Closes a live broadcast.

        Args:
            broadcast_id (str): The ID of the broadcast.
        """
        request = self.youtube.liveBroadcasts().transition(
            part="status",
            id=broadcast_id,
            broadcastStatus="complete"
        )
        request.execute()

    def delete_live_broadcast(self, broadcast_id):
        """
        Deletes a live broadcast.

        Args:
            broadcast_id (str): The ID of the broadcast.
        """
        request = self.youtube.liveBroadcasts().delete(
            id=broadcast_id
        )
        request.execute()

    def transition_to_live(self, broadcast_id):
        """
        This method transitions the specified broadcast to a "live" status.
        """
        self.youtube.liveBroadcasts().transition(
            part="id,snippet,contentDetails,status",
            id=broadcast_id,
            broadcastStatus="live"
        ).execute()

    def get_all_broadcasts(self):
        """
        This method retrieves all live broadcasts for the authenticated user.
        """
        request = self.youtube.liveBroadcasts().list(
            part="id,snippet,contentDetails,status",
            mine=True
        )
        response = request.execute()
        return response.get("items", [])

    def upload_video(self, file_path, title, description, privacy_status, tags=None, thumbnail_path=None, publish_after_processing=False):
        """
        Uploads a video to YouTube.

        Args:
            file_path (str): Path to the video file.
            title (str): The title of the video.
            description (str): The description of the video.
            privacy_status (str): The privacy status of the video (e.g., "public", "private", "unlisted").
            tags (list, optional): A list of tags for the video. Defaults to None.
            thumbnail_path (str, optional): Path to the thumbnail image. Defaults to None.
            publish_after_processing (bool): If True, waits for the video to be processed and then sets its privacy to public.
        """
        generated_thumbnail = False
        if not thumbnail_path:
            print("No thumbnail provided, attempting to generate one...")
            thumbnail_path = generate_thumbnail(file_path)
            if thumbnail_path:
                generated_thumbnail = True
                print("Thumbnail generated successfully.")
            else:
                print("Thumbnail generation skipped. Proceeding without one.")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = self.youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        video_id = response.get('id')
        print(f"Upload successful! Video ID: {video_id}")

        if thumbnail_path:
            self.set_thumbnail(video_id, thumbnail_path)
            if generated_thumbnail and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                print(f"Removed generated thumbnail: {thumbnail_path}")

        if publish_after_processing:
            published = self.wait_for_processing_and_publish(video_id)
            if published:
                return response, True

        return response, False

    def wait_for_processing_and_publish(self, video_id):
        """Waits for video processing and then publishes it."""
        print("Waiting for video processing to complete...")
        while True:
            status = self.get_video_processing_status(video_id)
            if status == 'succeeded':
                print("Video processing succeeded.")
                self.update_video_privacy(video_id, 'public')
                print("Video has been published.")
                return True
            elif status in ['failed', 'terminated']:
                print(f"Video processing failed with status: {status}")
                return False
            else:
                print(f"Current processing status: {status}. Waiting...")
                time.sleep(30) # Wait for 30 seconds before checking again

    def get_video_processing_status(self, video_id):
        """Gets the processing status of a video."""
        request = self.youtube.videos().list(
            part="processingDetails",
            id=video_id
        )
        response = request.execute()
        if not response["items"]:
            return None
        return response["items"][0]["processingDetails"]["processingStatus"]

    def update_video_privacy(self, video_id, privacy_status):
        """Updates the privacy status of a video."""
        body = {
            "id": video_id,
            "status": {
                "privacyStatus": privacy_status
            }
        }
        request = self.youtube.videos().update(
            part="status",
            body=body
        )
        request.execute()

    def set_thumbnail(self, video_id, thumbnail_path):
        """
        Sets a custom thumbnail for a video.

        Args:
            video_id (str): The ID of the video.
            thumbnail_path (str): Path to the thumbnail image.
        """
        media = MediaFileUpload(thumbnail_path)

        request = self.youtube.thumbnails().set(
            videoId=video_id,
            media_body=media
        )

        request.execute()
        print("Thumbnail set successfully.")