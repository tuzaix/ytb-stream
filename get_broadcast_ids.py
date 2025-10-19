import argparse
from youtube.client import YouTubeClient

def main():
    """
    This function retrieves and lists all live broadcasts for the authenticated user.
    """
    parser = argparse.ArgumentParser(description="Get all live broadcasts for the authenticated user.")
    parser.add_argument("--credentials_file", required=True, help="Path to the client secrets file.")
    args = parser.parse_args()

    client = YouTubeClient(args.credentials_file)
    broadcasts = client.get_all_broadcasts()

    if not broadcasts:
        print("No broadcasts found.")
        return

    for broadcast in broadcasts:
        broadcast_id = broadcast["id"]
        title = broadcast["snippet"]["title"]
        status = broadcast["status"]["lifeCycleStatus"]
        print(f"ID: {broadcast_id}, Title: {title}, Status: {status}")

if __name__ == "__main__":
    main()