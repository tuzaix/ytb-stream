import os
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz

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