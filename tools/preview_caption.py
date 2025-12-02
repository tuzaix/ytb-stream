"""
Generate preview images to validate caption rendering differences between English and CJK.

Creates two base images and overlays captions using youtube.thumbnail.add_caption_to_image.
Outputs: preview_en.png (default letter spacing), preview_zh.png (increased letter spacing for CJK).
"""

import os
import sys
from PIL import Image

# Ensure project root is on sys.path for imports when run directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from youtube.thumbnail import add_caption_to_image


def _make_base(path: str, size=(1280, 720)) -> None:
    """Create a dark base image for caption previews."""
    img = Image.new("RGB", size, (20, 20, 20))
    img.save(path)


def main() -> None:
    """Generate English and Chinese caption previews for visual inspection."""
    base_en = "preview_base_en.png"
    base_zh = "preview_base_zh.png"
    _make_base(base_en)
    _make_base(base_zh)

    # Generate English preview (default yellow) on local base image
    en_output = add_caption_to_image(
        base_en,
        "Delicious Street Food Recipe - Quick and Easy Cooking Tips for Everyone!"
    )
    if en_output:
        import shutil
        shutil.move(en_output, "preview_en.png")
        print(" - preview_en.png (yellow)")
    
    # Generate Chinese preview (red color)
    zh_output = add_caption_to_image(
        base_zh,
        "美味街头小食制作秘籍 - 简单易学的烹饪技巧分享",
        color="red"
    )
    if zh_output:
        import shutil
        shutil.move(zh_output, "preview_zh.png")
        print(" - preview_zh.png (red)")
        
    # Generate additional color previews
    colors = ['blue', 'green', 'orange', 'purple']
    for i, color in enumerate(colors):
        # Use a fresh base per color to avoid missing base after prior moves
        base_color = f"preview_base_{color}.png"
        _make_base(base_color)
        color_output = add_caption_to_image(
            base_color,
            f"Color Test: {color.upper()} Caption Style",
            color=color
        )
        if color_output:
            import shutil
            shutil.move(color_output, f"preview_{color}.png")
            print(f" - preview_{color}.png ({color})")

    print("Generated:")


if __name__ == "__main__":
    main()