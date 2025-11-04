"""
生成横向拼接的封面图片（screen_cover）的小工具。

功能概述：
- 从一个图片目录中随机选择若干图片（默认每个封面 3 张）。
- 调用 `youtube.thumbnail.generate_thumbnail(image_paths=..., caption=...)` 生成横向拼接的封面图片（可叠加字幕）。
- 将拼接后的封面图片保存到图片目录下的 `screen_cover/` 子目录。

命令行参数：
- `images_dir`：图片目录（必填）。
- `--caption`：字幕文本（可选）。
- `--count`：要生成的封面图片个数（默认 10）。
- `--per-video`：每个封面由几张图片组成（默认 3）。
- `--seed`：随机种子（可选，便于复现）。
- `--color`：字幕颜色（默认 yellow）。

依赖：
- 依赖项目内的 `youtube/thumbnail.py`（仅调用其中的 `generate_thumbnail` 进行合成）。
"""

import argparse
import os
import random
import sys
import uuid
from typing import List
import shutil


# 允许从项目根目录运行 `python tools/generate_screen_covers.py`
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from youtube.thumbnail import generate_thumbnail  # type: ignore
except Exception as e:
    print(f"Error importing youtube.thumbnail.generate_thumbnail: {e}")
    raise


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def list_images(images_dir: str) -> List[str]:
    """列出目录中的图片文件路径。

    - 仅扫描一级目录，不递归。
    - 支持常见图片扩展名：jpg/jpeg/png/webp/bmp。

    Args:
        images_dir: 图片目录路径。

    Returns:
        图片文件绝对路径列表。
    """
    files: List[str] = []
    for name in os.listdir(images_dir):
        p = os.path.join(images_dir, name)
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTS:
            files.append(os.path.abspath(p))
    return files


def choose_images(candidates: List[str], k: int) -> List[str]:
    """从候选图片中选择 k 张。

    - 若候选数 >= k，使用 `random.sample` 无重复抽取。
    - 若候选数 < k，使用 `random.choices` 允许重复抽取。

    Args:
        candidates: 候选图片路径列表。
        k: 选择数量。

    Returns:
        选择的图片路径列表（长度为 k）。
    """
    if not candidates:
        return []
    if len(candidates) >= k:
        return random.sample(candidates, k)
    return random.choices(candidates, k=k)


def ensure_dir(path: str) -> None:
    """确保目录存在，不存在则创建。"""
    os.makedirs(path, exist_ok=True)


# 不再导出视频，因此移除分辨率/帧率相关解析


def save_stitched_cover(stitched_image_path: str, images_dir: str) -> str:
    """把拼接好的封面图片移动到 `images_dir/screen_cover/` 并返回新路径。

    Args:
        stitched_image_path: `generate_thumbnail` 返回的图片路径。
        images_dir: 用户提供的图片目录路径，用于创建 `screen_cover` 子目录。

    Returns:
        新的封面图片路径（JPG）。
    """
    out_dir = os.path.join(images_dir, "screen_cover")
    ensure_dir(out_dir)
    ext = os.path.splitext(stitched_image_path)[1].lower() or ".jpg"
    out_name = f"screen_cover_{uuid.uuid4().hex[:8]}{ext}"
    out_path = os.path.join(out_dir, out_name)

    try:
        shutil.copy2(stitched_image_path, out_path)
        return out_path
    except Exception as e:
        print(f"Error copying stitched cover: {e}")
        return stitched_image_path


def generate_one_cover(
    images_dir: str,
    image_paths: List[str],
    caption: str | None,
    color: str = "yellow",
) -> str | None:
    """从若干图片生成一个横向拼接的封面图片并保存到 `screen_cover/`。

    Returns the final saved path or None on failure.
    """
    stitched_path = generate_thumbnail(image_paths=image_paths, caption=caption, color=color)
    if not stitched_path or not os.path.exists(stitched_path):
        print("Failed to generate stitched cover image.")
        return None

    out_path = save_stitched_cover(stitched_path, images_dir)
    return out_path


def main() -> None:
    """命令行入口：批量生成横向拼接的封面图片（screen_cover）。"""
    parser = argparse.ArgumentParser(description="Generate stitched cover images from a directory of photos.")
    parser.add_argument("images_dir", help="图片目录")
    parser.add_argument("--caption", default=None, help="字幕文本")
    parser.add_argument("--count", type=int, default=10, help="生成的封面图片个数，默认 10")
    parser.add_argument("--per-cover", type=int, default=3, help="每个封面由几张图片组成，默认 3")
    parser.add_argument("--seed", type=int, default=None, help="随机种子，可选")
    parser.add_argument("--color", default="yellow", help="字幕颜色，默认 yellow")

    args = parser.parse_args()

    images_dir = os.path.abspath(args.images_dir)
    if not os.path.isdir(images_dir):
        print(f"Not a directory: {images_dir}")
        sys.exit(1)

    if args.seed is not None:
        random.seed(args.seed)

    all_images = list_images(images_dir)
    if not all_images:
        print(f"No images found in {images_dir}")
        sys.exit(1)

    print(f"Found {len(all_images)} images. Generating {args.count} covers, {args.per_cover} images per cover.")

    generated = 0
    for i in range(args.count):
        picks = choose_images(all_images, args.per_cover)
        print(f"[{i+1}/{args.count}] Using images: {', '.join(os.path.basename(p) for p in picks)}")
        out_path = generate_one_cover(
            images_dir=images_dir,
            image_paths=picks,
            caption=args.caption,
            color=args.color,
        )
        if out_path:
            generated += 1
            print(f"Generated cover: {out_path}")
        else:
            print("Failed to generate cover for this batch.")

    print(f"Done. Successfully generated {generated}/{args.count} covers.")


if __name__ == "__main__":
    main()