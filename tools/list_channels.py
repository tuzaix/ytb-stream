import argparse
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from youtube.client import YouTubeClient

def list_channels(auth_dir, proxy="http://127.0.0.1:7897"):
    """Lists all channels for the authenticated user."""
    client = YouTubeClient(
        os.path.join(auth_dir, "client_secret.json"),
        os.path.join(auth_dir, "token.json"),
        proxy=proxy
    )

    try:
        request = client.youtube.channels().list(
            part="id,snippet",
            mine=True
        )
        response = request.execute()

        if 'items' in response and response['items']:
            print("Channels found:")
            for item in response['items']:
                channel_id = item['id']
                channel_title = item['snippet']['title']
                print(f"  - ID: {channel_id}, Title: {channel_title}")
        else:
            print("No channels found for this account.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List all YouTube channels for the authenticated user.")
    parser.add_argument("--auth_dir", required=True, help="Directory containing client_secrets.json and token.json.")
    parser.add_argument("--proxy", help="Proxy server to use for the request.")
    args = parser.parse_args()
    list_channels(args.auth_dir, args.proxy)