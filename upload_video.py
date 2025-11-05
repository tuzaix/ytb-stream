import argparse
import os
import random
import shutil
from youtube.client import YouTubeClient
from youtube.thumbnail import generate_stream_thumbnail, add_caption_to_image, get_video_duration

def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("--auth_dir", required=True, help="Directory containing client_secrets.json and token.json.")
    parser.add_argument("--video_dirs", required=True, nargs='+', help="Directory containing video files.")
    parser.add_argument("--title", required=True, help="The title of the video.")
    parser.add_argument("--description", required=True, help="The description of the video.")
    parser.add_argument("--privacy", type=str, default="private", help="The privacy status of the video (e.g., private, public, unlisted)")
    parser.add_argument("--thumbnail", type=str, help="The path to the thumbnail image")
    parser.add_argument("--thumbnail_caption", type=str, default="", help="Caption text for the thumbnail (empty by default); will auto-wrap and center")
    parser.add_argument(
        "--thumbnail_color",
        type=str,
        default="yellow",
        help=(
            "Caption color (default: yellow). Options include: yellow, red, blue, "
            "green, white, orange, purple, cyan"
        ),
    )
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
    selected_dir_cover_dir = os.path.join(selected_dir, "screen_cover") # 封面图目录
    print(f"Selected directory: {selected_dir} {selected_dir_cover_dir}")

    video_files = [f for f in os.listdir(selected_dir) if os.path.isfile(os.path.join(selected_dir, f))]
    if not video_files:
        print(f"No video files found in {selected_dir}.")
        return
    thumbnail_files = [f for f in os.listdir(selected_dir_cover_dir) if os.path.isfile(os.path.join(selected_dir_cover_dir, f))]
    if not thumbnail_files:
        thumbnail_to_upload = None
    else:
        thumbnail_to_upload = os.path.join(selected_dir_cover_dir, random.choice(thumbnail_files))
    print(f"Selected thumbnail: {thumbnail_to_upload}")

    video_to_upload = os.path.join(selected_dir, random.choice(video_files))
    print(f"Selected video: {video_to_upload}")

    client = YouTubeClient(os.path.join(args.auth_dir, "client_secrets.json"), os.path.join(args.auth_dir, "token.json"))

    video_tags = args.tags.split(",") if args.tags else None

    def prepare_thumbnail_with_caption(video_path: str, base_thumbnail: str, caption: str, color: str) -> str:
        """Prepare a thumbnail with an optional caption overlay.

        - If `base_thumbnail` is a file, copy it and overlay the caption.
        - If `base_thumbnail` is a directory, randomly pick one image, move it to a
          sibling directory named "<dir>_published", then use it as the base and overlay caption.
        - If no usable base image, generate a thumbnail from the video and overlay caption.

        Returns the path to the prepared thumbnail, or None on failure.

        Args:
            video_path: The source video path used to generate thumbnail when no base provided.
            base_thumbnail: An existing thumbnail image path or a directory containing images.
            caption: The text to overlay on the thumbnail.
            color: The color for caption text (e.g., 'yellow', 'red', 'blue').
        """
        # If a directory is provided, randomly select one image and move it to '<dir>_published'
        try:
            if base_thumbnail and os.path.isdir(base_thumbnail):
                allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
                candidates = []
                for name in os.listdir(base_thumbnail):
                    full = os.path.join(base_thumbnail, name)
                    if os.path.isfile(full) and os.path.splitext(name)[1].lower() in allowed_exts:
                        candidates.append(full)
                if not candidates:
                    print(f"No image candidates found in directory: {base_thumbnail}")
                    base_thumbnail = None
                else:
                    chosen = random.choice(candidates)
                    print(f"Selected image to publish as thumbnail: {chosen}")
                    base_thumbnail = chosen
        except Exception as e:
            print(f"Error handling thumbnail directory input: {e}")

        # If no caption requested, return base thumbnail directly
        if not caption:
            return base_thumbnail

        # If a thumbnail exists, copy and overlay caption to avoid mutating original
        if base_thumbnail and os.path.exists(base_thumbnail):
            root, ext = os.path.splitext(base_thumbnail)
            ext = ext or ".jpg"
            captioned_path = f"{root}_captioned{ext}"
            try:
                shutil.copy(base_thumbnail, captioned_path)
                result = add_caption_to_image(captioned_path, caption, color=color)
                if result:
                    return result
                else:
                    print("Failed to overlay caption on provided thumbnail. Will attempt to generate from video.")
            except Exception as e:
                print(f"Error preparing captioned thumbnail from provided file: {e}")

        # Generate from video with caption
        generated = generate_stream_thumbnail(video_path, caption, color=color)
        if generated:
            return generated
        else:
            print("Failed to generate captioned thumbnail from video.")
            return None

    # Decide on thumbnail generation based on rules:
    # - If a base thumbnail is provided, optionally overlay caption.
    # - If no base thumbnail is provided, generate only if video duration > 3 minutes.
    duration_sec = get_video_duration(video_to_upload)
    thumbnail_path = None
    if duration_sec is not None and duration_sec > 180:
        if args.thumbnail:
            thumbnail_path = prepare_thumbnail_with_caption(video_to_upload, args.thumbnail, args.thumbnail_caption, args.thumbnail_color)
        else:
            # caption_text = args.thumbnail_caption.strip()
            # thumbnail_path = generate_stream_thumbnail(video_to_upload, caption_text if caption_text else None, color=args.thumbnail_color)
            thumbnail_path = thumbnail_to_upload
    
    print(f"Thumbnail path: {thumbnail_path}")

    _, published = client.upload_video(
        file_path=video_to_upload,
        title=args.title,
        description=args.description,
        privacy_status=args.privacy,
        tags=video_tags,
        thumbnail_path=thumbnail_path,
        publish_after_processing=args.publish
    )

    if published:
        published_dir = f"{selected_dir}_published"
        if not os.path.exists(published_dir):
            os.makedirs(published_dir)
        shutil.move(video_to_upload, os.path.join(published_dir, os.path.basename(video_to_upload)))
        print(f"Moved {video_to_upload} to {published_dir}")
    if thumbnail_path:
        # 删除生成的缩略图
        os.remove(thumbnail_path)
        print(f"Deleted generated thumbnail: {thumbnail_path}")

if __name__ == "__main__":
    main()