import argparse
from youtube.client import YouTubeClient

def main():
    """
    This function closes a YouTube live broadcast.
    """
    parser = argparse.ArgumentParser(description="Close a YouTube live broadcast.")
    parser.add_argument("--credentials_file", required=True, help="Path to the client secrets file.")
    parser.add_argument("--broadcast_id", required=True, help="The ID of the broadcast to close.")
    args = parser.parse_args()

    client = YouTubeClient(args.credentials_file)
    client.close_live_broadcast(args.broadcast_id)
    print(f"Broadcast {args.broadcast_id} has been closed.")

if __name__ == "__main__":
    main()