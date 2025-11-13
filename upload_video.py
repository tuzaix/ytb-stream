import os
import random
import shutil
from typing import List, Optional, Tuple, Dict, Any
from youtube.client import YouTubeClient
from youtube.thumbnail import generate_stream_thumbnail, add_caption_to_image, get_video_duration


def prepare_thumbnail_with_caption(video_path: str, base_thumbnail: Optional[str], caption: str, color: str) -> Tuple[Optional[str], bool]:
    """Prepare a thumbnail with an optional caption overlay.

    Behavior:
    - If `base_thumbnail` is a directory, randomly pick one image (jpg/jpeg/png/webp) from it.
    - If caption is empty and a base image exists, return it directly (no mutation).
    - If a base image exists and caption provided, copy it and overlay caption (non-destructive).
    - If no base image usable, generate a thumbnail from the video with caption.

    Returns:
    - (thumbnail_path, is_generated):
      - thumbnail_path: The resolved thumbnail path or None if failed.
      - is_generated: True if we created a new file (either generated or captioned copy) and caller may safely delete it.

    Args:
      video_path: The source video path used to generate thumbnail when no base provided.
      base_thumbnail: An existing thumbnail image path or a directory containing images.
      caption: The text to overlay on the thumbnail.
      color: The color for caption text (e.g., 'yellow', 'red', 'blue').
    """
    # If a directory is provided, randomly select one image
    try:
        if base_thumbnail and os.path.isdir(base_thumbnail):
            allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}
            candidates: List[str] = []
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
    if caption == "" and base_thumbnail:
        return base_thumbnail, False

    # If a thumbnail exists, copy and overlay caption to avoid mutating original
    if base_thumbnail and os.path.exists(base_thumbnail) and caption:
        root, ext = os.path.splitext(base_thumbnail)
        ext = ext or ".jpg"
        captioned_path = f"{root}_captioned{ext}"
        try:
            shutil.copy(base_thumbnail, captioned_path)
            result = add_caption_to_image(captioned_path, caption, color=color)
            if result:
                return result, True
            else:
                print("Failed to overlay caption on provided thumbnail. Will attempt to generate from video.")
        except Exception as e:
            print(f"Error preparing captioned thumbnail from provided file: {e}")

    # Generate from video with caption (only if caption provided)
    if caption:
        generated = generate_stream_thumbnail(video_path, caption, color=color)
        if generated:
            return generated, True
        else:
            print("Failed to generate captioned thumbnail from video.")
            return None, False

    # No caption and no base image
    return None, False


def upload_video_once(
    auth_dir: str,
    video_dirs: List[str],
    title: str,
    description: str,
    privacy: str = "private",
    thumbnail: Optional[str] = None,
    thumbnail_caption: str = "",
    thumbnail_color: str = "yellow",
    publish: bool = False,
    tags: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload one video chosen from given directories, with optional thumbnail handling.

    High-level flow:
      1) Filter input directories to those containing files, pick one randomly.
      2) Pick a random video file from the selected directory.
      3) If screen_cover/ exists, preselect one image as candidate thumbnail.
      4) If duration > 3 minutes and a --thumbnail provided, prepare captioned thumbnail.
         Otherwise use preselected thumbnail from screen_cover if present.
      5) Upload via YouTubeClient; optionally publish.
      6) If published, move video to <selected_dir>_published.
      7) Clean up generated thumbnail files only.

    Returns a dict with details:
      {
        "selected_dir": str,
        "video_path": str,
        "thumbnail_path": Optional[str],
        "thumbnail_generated": bool,
        "published": bool,
        "uploaded_video_id": Optional[str]
      }
    """
    # 1) Filter valid dirs
    print(f"Available video directories: {video_dirs}")
    valid_dirs: List[str] = []
    for d in video_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            any_files = any(os.path.isfile(os.path.join(d, f)) for f in os.listdir(d))
            if any_files:
                valid_dirs.append(d)
        else:
            print(f"Warning: Directory {d} does not exist or is not a directory.")
    if not valid_dirs:
        raise RuntimeError("No valid video directories with files found.")

    # 2) Select directory & video file
    selected_dir = random.choice(valid_dirs)
    selected_dir_cover_dir = os.path.join(selected_dir, "screen_cover")
    print(f"Selected directory: {selected_dir} {selected_dir_cover_dir}")
    video_files = [f for f in os.listdir(selected_dir) if os.path.isfile(os.path.join(selected_dir, f))]
    if not video_files:
        raise RuntimeError(f"No video files found in {selected_dir}.")
    video_to_upload = os.path.join(selected_dir, random.choice(video_files))
    print(f"Selected video: {video_to_upload}")

    # 3) Preselect thumbnail from screen_cover
    thumbnail_preselected: Optional[str] = None
    if os.path.exists(selected_dir_cover_dir) and os.path.isdir(selected_dir_cover_dir):
        thumb_candidates = [
            f for f in os.listdir(selected_dir_cover_dir)
            if os.path.isfile(os.path.join(selected_dir_cover_dir, f))
        ]
        if thumb_candidates:
            thumbnail_preselected = os.path.join(selected_dir_cover_dir, random.choice(thumb_candidates))
    print(f"Preselected thumbnail: {thumbnail_preselected}")

    # 4) Prepare final thumbnail based on rules
    duration_sec = get_video_duration(video_to_upload)
    final_thumb: Optional[str] = None
    final_thumb_generated: bool = False
    if duration_sec is not None and duration_sec > 180:
        if thumbnail:
            final_thumb, final_thumb_generated = prepare_thumbnail_with_caption(
                video_to_upload, thumbnail, thumbnail_caption, thumbnail_color
            )
        else:
            final_thumb = thumbnail_preselected
            final_thumb_generated = False

    print(f"Thumbnail path: {final_thumb}")

    # 5) Upload
    client = YouTubeClient(
        os.path.join(auth_dir, "client_secrets.json"),
        os.path.join(auth_dir, "token.json"),
    )
    video_tags = tags.split(",") if tags else None
    uploaded_id, published_flag = client.upload_video(
        file_path=video_to_upload,
        title=title,
        description=description,
        privacy_status=privacy,
        tags=video_tags,
        thumbnail_path=final_thumb,
        publish_after_processing=publish,
    )

    # 6) Move published video
    if published_flag:
        published_dir = f"{selected_dir}_published"
        if not os.path.exists(published_dir):
            os.makedirs(published_dir)
        shutil.move(video_to_upload, os.path.join(published_dir, os.path.basename(video_to_upload)))
        print(f"Moved {video_to_upload} to {published_dir}")

    # 7) Cleanup generated thumbnail only
    if final_thumb and final_thumb_generated:
        try:
            os.remove(final_thumb)
            print(f"Deleted generated thumbnail: {final_thumb}")
        except Exception as e:
            print(f"Failed to delete generated thumbnail: {e}")

    return {
        "selected_dir": selected_dir,
        "video_path": video_to_upload,
        "thumbnail_path": final_thumb,
        "thumbnail_generated": final_thumb_generated,
        "published": bool(published_flag),
        "uploaded_video_id": uploaded_id,
    }


# CLI has been moved to upload_video_cli.py to keep this module import-only.