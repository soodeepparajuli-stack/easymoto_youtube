import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    """
    Authenticate the user and return the YouTube service object.
    It expects 'client_secret.json' in the root directory.
    It saves 'token.pickle' for reuse.
    """
    creds = None
    token_path = "token.pickle"
    
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secret = "client_secret.json"
            if not os.path.exists(client_secret):
                print("client_secret.json not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
            
    return build("youtube", "v3", credentials=creds)

def upload_video(file, title, description, keywords, category_id="2"):
    """
    Uploads a video to YouTube.
    category_id '2' is usually Autos & Vehicles.
    """
    youtube = get_authenticated_service()
    if not youtube:
        print("YouTube authentication failed or skipped.")
        return None

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": keywords,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "private", # Start as private for safety
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    print(f"Uploading {file}...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")
            
    print("Upload Complete!")
    return response.get("id")
