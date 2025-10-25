import argparse
import os
import random
import shutil
from youtube.client import YouTubeClient

def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("--auth_dir", required=True, help="Directory containing client_secrets.json and token.json.")
    parser.add_argument("--video_dirs", required=True, nargs='+', help="Directory containing video files.")
    parser.add_argument("--title", required=True, help="The title of the video.")
    parser.add_argument("--description", required=True, help="The description of the video.")
    parser.add_argument("--privacy", type=str, default="private", help="The privacy status of the video (e.g., private, public, unlisted)")
    parser.add_argument("--thumbnail", type=str, help="The path to the thumbnail image")
    parser.add_argument("--publish", action="store_true", help="Publish the video after processing")
    parser.add_argument("--tags", type=str, help="A comma-separated list of tags for the video")

    args = parser.parse_args()

    # Randomly select a directory from the provided list
    print(f"Available video directories: {args.video_dirs}")

    # 先检查目录是否存在，并且目录下是否有视频文件，筛选出有视频文件的目录
    valid_dirs = []
    for dir in args.video_dirs:
        if os.path.exists(dir) and os.path.isdir(dir):
            video_files = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
            if video_files:
                valid_dirs.append(dir)
        else:
            print(f"Warning: Directory {dir} does not exist or is not a directory.")

    if not valid_dirs:
        print("No valid video directories with video files found.")
        return

    selected_dir = random.choice(valid_dirs)
    print(f"Selected directory: {selected_dir}")

    video_files = [f for f in os.listdir(selected_dir) if os.path.isfile(os.path.join(selected_dir, f))]
    if not video_files:
        print(f"No video files found in {selected_dir}.")
        return

    video_to_upload = os.path.join(selected_dir, random.choice(video_files))
    print(f"Selected video: {video_to_upload}")

    client = YouTubeClient(os.path.join(args.auth_dir, "client_secrets.json"), os.path.join(args.auth_dir, "token.json"))

    video_tags = args.tags.split(",") if args.tags else None

    _, published = client.upload_video(
        file_path=video_to_upload,
        title=args.title,
        description=args.description,
        privacy_status=args.privacy,
        tags=video_tags,
        thumbnail_path=args.thumbnail,
        publish_after_processing=args.publish
    )

    if published:
        published_dir = f"{selected_dir}_published"
        if not os.path.exists(published_dir):
            os.makedirs(published_dir)
        shutil.move(video_to_upload, os.path.join(published_dir, os.path.basename(video_to_upload)))
        print(f"Moved {video_to_upload} to {published_dir}")

if __name__ == "__main__":
    main()