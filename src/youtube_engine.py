import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeEngine:
    def __init__(self, client_secrets_file='client_secrets.json'):
        self.client_secrets_file = client_secrets_file
        self.youtube = self._authenticate()

    def _authenticate(self):
        """Handles OAuth 2.0 authentication and returns the YouTube service client."""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"Missing '{self.client_secrets_file}'. "
                        "Please download your OAuth 2.0 Client ID from the Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES)
                # This will open a browser window for authentication
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, video_path: str, title: str, description: str, tags: list):
        """Uploads the video to YouTube via Data API v3 as Private."""
        print(f"Uploading '{title}' to YouTube...")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # 22 = People & Blogs (Change as needed)
            },
            'status': {
                'privacyStatus': 'private', # Always upload as private first for safety
                'selfDeclaredMadeForKids': False
            }
        }

        # Call the API's videos.insert method to create and upload the video.
        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )

        response = insert_request.execute()
        print(f"Upload complete. Video ID: {response.get('id')}")
        return response.get('id')
