"""Upload a video by account material configuration.

This CLI loads account-specific copywriting and settings from
`ytb_account_material_config.py`, then delegates the actual upload
to `upload_video.upload_video_once`.
"""

import argparse
import random
from typing import Dict, Any, NoReturn, List, Optional

from upload_video import upload_video_once
from ytb_account_material_config import YTB_ACCOUNT_MATERIAL_CONFIG


def pick_copywriting(config: Dict[str, Any]) -> Dict[str, str]:
    """Pick one copywriting item from config or return sensible defaults.

    Expected schema:
      config["copywriting"]: List[{"title": str, "description": str}]

    Returns a dict with keys: `title`, `description`.
    """
    items = config.get("copywriting") or []
    if isinstance(items, list) and items:
        choice = random.choice(items)
        title = str(choice.get("title", ""))
        description = str(choice.get("description", ""))
        return {"title": title, "description": description}
    # Fallback defaults
    return {"title": "", "description": ""}


def pick_caption(config: Dict[str, Any]) -> str:
    """Pick one caption from config["caption"] list or return empty string."""
    captions = config.get("caption") or []
    if isinstance(captions, list) and captions:
        return str(random.choice(captions))
    return ""


def build_tags_string(config: Dict[str, Any]) -> Optional[str]:
    """Build a comma-separated tags string from config or return None when absent."""
    tags = config.get("tags") or []
    if isinstance(tags, list) and tags:
        return ",".join(str(t) for t in tags)
    return None


def main() -> NoReturn:
    """Parse args, resolve account materials, and upload a video.

    Parameters from CLI:
      --auth_dir: Directory containing `client_secrets.json` and `token.json`.
      --video_dirs: One or more directories containing video files.
      --account: Account key to select materials from `YTB_ACCOUNT_MATERIAL_CONFIG`.

    Optional overrides:
      --privacy: Override privacy status (default: private).
      --thumbnail: Optional base thumbnail path or directory.
      --thumbnail_color: Caption color (default: yellow).

    The `published` flag is derived from account materials.
    """
    parser = argparse.ArgumentParser(description="Upload a video using account materials.")
    parser.add_argument("--auth_dir", required=True, help="Directory containing client_secrets.json and token.json.")
    parser.add_argument("--video_dirs", required=True, nargs="+", help="Directories containing video files.")
    parser.add_argument("--account", required=True, help="Account key in YTB_ACCOUNT_MATERIAL_CONFIG.")

    args = parser.parse_args()

    # Resolve account configuration
    account_cfg = YTB_ACCOUNT_MATERIAL_CONFIG.get(args.account)
    if not account_cfg:
        raise SystemExit(f"Account '{args.account}' not found in YTB_ACCOUNT_MATERIAL_CONFIG.")

    copywriting = pick_copywriting(account_cfg)
    title = copywriting.get("title", "")
    description = copywriting.get("description", "")
    tags_str = build_tags_string(account_cfg)
    caption = pick_caption(account_cfg)
    published_flag = bool(account_cfg.get("published", False))

    print(f"Account: {args.account}")
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"Tags: {tags_str}")
    print(f"Caption: {caption}")
    print(f"Published: {published_flag}")

    result = upload_video_once(
        auth_dir=args.auth_dir,
        video_dirs=args.video_dirs,
        title=title,
        description=description,
        publish=published_flag,
        tags=tags_str,
    )

    print("Upload result:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()