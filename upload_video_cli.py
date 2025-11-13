"""Command-line entrypoint for uploading a video to YouTube.

This module isolates the CLI concerns from `upload_video.py`, keeping
the latter import-friendly for reuse in other modules.
"""

import argparse
from typing import NoReturn

from upload_video import upload_video_once


def main() -> NoReturn:
    """Parse CLI arguments and invoke `upload_video_once`.

    Behavior:
    - Collects all parameters needed to upload a video.
    - Delegates the actual upload logic to `upload_video_once`.
    - Prints a concise summary of the operation for CLI users.
    """
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("--auth_dir", required=True, help="Directory containing client_secrets.json and token.json.")
    parser.add_argument("--video_dirs", required=True, nargs="+", help="Directory containing video files.")
    parser.add_argument("--title", required=True, help="The title of the video.")
    parser.add_argument("--description", required=True, help="The description of the video.")
    parser.add_argument("--privacy", type=str, default="private", help="Privacy status: private, public, or unlisted.")
    parser.add_argument("--thumbnail", type=str, help="Path to the thumbnail image (file or directory).")
    parser.add_argument(
        "--thumbnail_caption",
        type=str,
        default="",
        help="Caption text for the thumbnail (auto-wrapped and centered).",
    )
    parser.add_argument(
        "--thumbnail_color",
        type=str,
        default="yellow",
        help="Caption color: yellow (default), red, blue, green, white, orange, purple, cyan.",
    )
    parser.add_argument("--publish", action="store_true", help="Publish the video after processing.")
    parser.add_argument("--tags", type=str, help="Comma-separated list of tags for the video.")

    args = parser.parse_args()

    result = upload_video_once(
        auth_dir=args.auth_dir,
        video_dirs=args.video_dirs,
        title=args.title,
        description=args.description,
        privacy=args.privacy,
        thumbnail=args.thumbnail,
        thumbnail_caption=args.thumbnail_caption,
        thumbnail_color=args.thumbnail_color,
        publish=args.publish,
        tags=args.tags,
    )

    print("Upload result:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()