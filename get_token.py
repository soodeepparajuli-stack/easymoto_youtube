
import os
import pickle
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    creds = None
    token_path = "token.pickle"
    client_secret = "client_secret.json"
    
    # 1. Check for existing token
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            try:
                creds = pickle.load(token)
            except Exception as e:
                print(f"Error reading existing token: {e}. generating new one.")

    # 2. Refresh or Login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Refresh failed: {e}. Re-authenticating...")
                creds = None
        
        if not creds:
            if not os.path.exists(client_secret):
                print("ERROR: client_secret.json not found in this folder.")
                print("Please download it from Google Cloud Console and place it here.")
                return

            print("Launching browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save new/refreshed token
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
            print("Token refreshed and saved to 'token.pickle'.")

    # 3. Encode to Base64
    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            
        print("\n" + "="*60)
        print("COPY THE STRING BELOW FOR GITHUB SECRET 'YOUTUBE_TOKEN_PICKLE_BASE64'")
        print("="*60 + "\n")
        print(encoded)
        print("\n" + "="*60)
    else:
        print("Failed to generate token.")

if __name__ == "__main__":
    main()
