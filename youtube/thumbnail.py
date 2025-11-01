import subprocess
import random
import os
import uuid
import numpy as np
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont
import os 

# 字体目录
FONTS_RELATIVE_PATH = os.path.join(os.path.dirname(__file__), "..", "fonts")

def _find_font_file() -> str:
    """Finds an available (preferably bold) font file on Windows supporting Latin and CJK.

    Priority order (bold first): Microsoft YaHei Bold, SimHei, Microsoft YaHei, Arial Bold, Arial.
    Returns empty string if none found, letting PIL pick a default.
    """
    candidates = [
        # "SourceHanSansCN-Bold.otf",
        # "SourceHanSansCN-ExtraLight.otf",
        "SourceHanSansCN-Heavy.otf",
        # "SourceHanSansCN-Light.otf",
        # "SourceHanSansCN-Medium.otf",
        # "SourceHanSansCN-Normal.otf",
        # "SourceHanSansCN-Regular.otf",
    ]
    for font in candidates:
        path = os.path.join(FONTS_RELATIVE_PATH, font)
        print(f"Checking font: {path}")
        if os.path.exists(path):
            return path
    return ""

def add_caption_to_image(image_path: str, caption: str, color: str = 'yellow') -> str:
    """
    Render caption onto an image using MoviePy + PIL.

    Visual rules:
    - Keep original case for text, configurable fill color with black stroke/shadow.
    - Safe area: 15% left/right padding, 15% top/bottom padding; text centered.
    - Fixed font size at 130px; wrapping derived from safe width and glyph width.
    - Line spacing ~1.1x (spacing = 0.10 * fontsize).
    - Letter spacing: default for English (ASCII-only) lines; slightly increased for CJK lines.

    Args:
        image_path: Path to the base image.
        caption: Text to overlay.
        color: Text color ('yellow', 'red', 'blue', 'green', 'white', 'orange', 'purple', 'cyan').

    Returns:
        Path to the output image with caption applied.
    """
    # Color mapping
    color_map = {
        'yellow': (255, 255, 0),
        'red': (255, 0, 0),
        'blue': (0, 100, 255),
        'green': (0, 255, 0),
        'white': (255, 255, 255),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'cyan': (0, 255, 255),
    }
    
    # Get RGB color, default to yellow if not found
    text_color = color_map.get(color.lower(), color_map['yellow'])
    """Adds a centered, wrapped caption to an image using MoviePy + PIL.

    - Auto-wraps text within a safe area (70% width, 40% height) with 15%/30% padding
    - Centers the text block, uses 1.1x line height equivalent (spacing ~0.1*fontsize)
    - Yellow uppercase text with black stroke for readability

    Returns the path to the updated image (overwrites original). On error, returns None.
    """
    if not caption:
        return image_path

    try:
        base_img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error opening image for caption overlay: {e}")
        return None

    w, h = base_img.size

    # Keep English text in original case, only apply uppercase to non-CJK text if needed
    # For now, we'll keep original case for all text to maintain natural readability
    caption_up = caption

    # Fixed font size and wrapping derived from safe area and glyph width
    fontsize = 160
    spacing = int(max(0, fontsize * 0.50))  # 1.5x line height spacing

    # Choose font
    font_path = _find_font_file()
    print(f"Using font: {font_path}")
    try:
        font = ImageFont.truetype(font_path, fontsize) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Create transparent overlay the same size as base
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Compute safe area and text bounding box
    safe_x = int(w * 0.15)
    safe_y = int(h * 0.15)
    safe_w = int(w * 0.70)
    safe_h = int(h * 0.70)

    # Derive wrapping: if text has spaces, use word-based wrap; otherwise measure per-character to split.
    available_width = safe_w
    estimated_glyph_width = fontsize * 0.6

    # Precompute letter spacing for this block once
    try:
        line_letter_spacing_px = _line_letter_spacing(caption_up)
    except Exception:
        line_letter_spacing_px = int(max(0, fontsize * 0.02))

    def _split_no_space_text_to_lines(text: str) -> list:
        """Split a long string without spaces into lines based on measured widths.

        Measures each character width using the current font and accumulates until
        the line reaches available width considering per-character letter spacing.
        """
        if not text:
            return []
        lines_acc = []
        current_line = []
        current_width = 0
        # Use precomputed letter spacing for this text block
        ls_px = line_letter_spacing_px

        for i, ch in enumerate(text):
            try:
                ch_bbox = draw.textbbox((0, 0), ch, font=font)
                ch_w = ch_bbox[2] - ch_bbox[0]
            except Exception:
                ch_w = int(estimated_glyph_width)

            # extra spacing before this char except first in line
            extra = ls_px if current_line else 0
            if current_width + extra + ch_w <= available_width:
                current_line.append(ch)
                current_width += extra + ch_w
            else:
                # finalize current line
                if current_line:
                    lines_acc.append(''.join(current_line))
                # start new line
                current_line = [ch]
                current_width = ch_w

        if current_line:
            lines_acc.append(''.join(current_line))
        return lines_acc

    if ' ' in caption_up:
        # word-based wrapping using measured pixel widths; fallback to char-splitting for long words
        try:
            space_bbox = draw.textbbox((0, 0), " ", font=font)
            space_w = space_bbox[2] - space_bbox[0]
        except Exception:
            space_w = int(estimated_glyph_width * 0.33)

        def _wrap_by_words_measured(text: str) -> list:
            """Wrap text by words to fit available width using measured pixel widths.

            - Measures each word with `draw.textbbox` for accurate width.
            - Adds space width and letter spacing between words.
            - If a single word exceeds available width, splits it using
              `_split_no_space_text_to_lines(word)` and places segments accordingly.
            """
            words = text.split()
            if not words:
                return []
            ls_px_line = line_letter_spacing_px
            lines_acc = []
            current_words = []
            current_width = 0

            for idx, word in enumerate(words):
                # measure word width
                try:
                    w_bbox = draw.textbbox((0, 0), word, font=font)
                    w_w = w_bbox[2] - w_bbox[0]
                except Exception:
                    w_w = int(len(word) * estimated_glyph_width)

                # width to add if appended to current line
                sep_w = (space_w + ls_px_line) if current_words else 0
                need_w = sep_w + w_w

                if need_w <= available_width and current_width + need_w <= available_width:
                    # fits current line
                    current_words.append(word)
                    current_width += need_w
                else:
                    # if the word itself is too long, split by characters and place segments
                    if w_w > available_width:
                        # finalize current line first if it has content
                        if current_words:
                            lines_acc.append(' '.join(current_words))
                            current_words = []
                            current_width = 0

                        segments = _split_no_space_text_to_lines(word)
                        # place each segment as its own line
                        for seg in segments:
                            lines_acc.append(seg)
                    else:
                        # move current line to accumulator and start a new line with this word
                        if current_words:
                            lines_acc.append(' '.join(current_words))
                        current_words = [word]
                        current_width = w_w

            if current_words:
                lines_acc.append(' '.join(current_words))
            return lines_acc

        lines = _wrap_by_words_measured(caption_up)
    else:
        # no spaces: split using measured widths
        lines = _split_no_space_text_to_lines(caption_up)

    # Helper: detect if a character is CJK/Han/Hangul/Katakana/Hiragana
    def _is_cjk_char(ch: str) -> bool:
        cp = ord(ch)
        ranges = [
            (0x4E00, 0x9FFF),   # CJK Unified Ideographs
            (0x3400, 0x4DBF),   # CJK Unified Ideographs Extension A
            (0x20000, 0x2A6DF), # Extension B
            (0x2A700, 0x2B73F), # Extension C
            (0x2B740, 0x2B81F), # Extension D
            (0x2B820, 0x2CEAF), # Extension E
            (0xF900, 0xFAFF),   # CJK Compatibility Ideographs
            (0x2F800, 0x2FA1F), # CJK Compatibility Ideographs Supplement
            (0x3040, 0x309F),   # Hiragana
            (0x30A0, 0x30FF),   # Katakana
            (0x31F0, 0x31FF),   # Katakana Phonetic Extensions
            (0xAC00, 0xD7AF),   # Hangul Syllables
        ]
        return any(start <= cp <= end for start, end in ranges)

    # Per-line letter spacing: 0 for pure English lines, slight spacing for CJK / mixed lines
    def _line_letter_spacing(ln: str) -> int:
        has_cjk = any(_is_cjk_char(ch) for ch in ln)
        if has_cjk:
            return max(1, int(fontsize * 0.04))
        # English/default: no extra tracking
        return 0

    def _measure_text_block(lines_list):
        # Measure typical line height
        try:
            bbox_h = draw.textbbox((0, 0), "Hg", font=font)
            typical_h = bbox_h[3] - bbox_h[1]
        except Exception:
            typical_h = int(fontsize)

        max_w = 0
        total_h = 0
        for idx, ln in enumerate(lines_list):
            line_w = 0
            ls_px = _line_letter_spacing(ln)
            for i, ch in enumerate(ln):
                try:
                    ch_bbox = draw.textbbox((0, 0), ch, font=font)
                    ch_w = ch_bbox[2] - ch_bbox[0]
                except Exception:
                    ch_w = int(fontsize * 0.6)
                line_w += ch_w
                if i < len(ln) - 1:
                    line_w += ls_px
            max_w = max(max_w, line_w)
            total_h += typical_h
            if idx < len(lines_list) - 1:
                total_h += spacing
        return max_w, total_h, typical_h

    def _draw_text_block(origin_x, origin_y, lines_list, block_w, fill=(255, 255, 0, 255), stroke_width=0, stroke_fill=None):
        x0, y0 = origin_x, origin_y
        _, _, typical_h = _measure_text_block(lines_list)
        y = y0
        for ln in lines_list:
            # center each line inside the text block width
            line_w = 0
            ch_widths = []
            ls_px = _line_letter_spacing(ln)
            for i, ch in enumerate(ln):
                try:
                    ch_bbox = draw.textbbox((0, 0), ch, font=font)
                    ch_w = ch_bbox[2] - ch_bbox[0]
                except Exception:
                    ch_w = int(fontsize * 0.6)
                ch_widths.append(ch_w)
                line_w += ch_w
                if i < len(ln) - 1:
                    line_w += ls_px
            x = origin_x + max(0, (block_w - line_w) // 2)
            for i, ch in enumerate(ln):
                draw.text((x, y), ch, font=font, fill=fill,
                          stroke_width=stroke_width or 0,
                          stroke_fill=stroke_fill)
                x += ch_widths[i]
                if i < len(ln) - 1:
                    x += ls_px
            y += typical_h + spacing

    # Measure block size to center within safe area
    text_w, text_h, typical_h = _measure_text_block(lines)
    tx = safe_x + max(0, (safe_w - text_w) // 2)
    ty = safe_y + max(0, (safe_h - text_h) // 2)

    # Subtle shadow
    shadow_offset = (2, 2)
    _draw_text_block(tx + shadow_offset[0], ty + shadow_offset[1], lines, text_w, fill=(0, 0, 0, 180))
    # Simulate bold: extra passes without stroke
    bold_offset = max(1, int(fontsize * 0.02))
    for ox, oy in [(bold_offset, 0), (-bold_offset, 0), (0, bold_offset), (0, -bold_offset)]:
        _draw_text_block(tx + ox, ty + oy, lines, text_w, fill=(*text_color, 255))
    # Main text: specified color with black stroke
    _draw_text_block(tx, ty, lines, text_w, fill=(*text_color, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))

    # Composite using MoviePy
    try:
        base_clip = mp.ImageClip(np.array(base_img))
        overlay_clip = mp.ImageClip(np.array(overlay))
        composite = mp.CompositeVideoClip([base_clip, overlay_clip])
        composite.save_frame(image_path)
        return image_path
    except Exception as e:
        print(f"Error composing caption with MoviePy: {e}")
        try:
            # Fallback: paste overlay directly with PIL
            composed = base_img.convert("RGBA")
            composed.alpha_composite(overlay)
            composed.convert("RGB").save(image_path)
            return image_path
        except Exception as e2:
            print(f"Error saving captioned image with PIL fallback: {e2}")
            return None

def get_video_duration(video_path):
    """Gets the duration of a video in seconds using ffprobe."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        return float(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting video duration: {e}")
        return None

def get_video_resolution(video_path):
    """Gets the resolution of a video using ffprobe."""
    command = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=x:p=0',
        video_path
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
        width, height = map(int, result.stdout.strip().split('x'))
        return width, height
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"Error getting video resolution: {e}")
        return None, None

def generate_thumbnail(video_path, caption: str = None, color: str = 'yellow'):
    """
    Generates a thumbnail by stitching three random frames from a video
    if the video is a vertical video (height > width).

    Args:
        video_path (str): The path to the video file.
        caption (str): Optional caption to overlay on the thumbnail.
        color (str): Color for the caption text.

    Returns:
        str: The path to the generated thumbnail, or None if generation fails or conditions are not met.
    """
    duration = get_video_duration(video_path)
    width, height = get_video_resolution(video_path)

    print(f"Video duration: {duration} seconds")
    print(f"Video resolution: {width}x{height}")

    if duration is None or width is None or height is None:
        return None

    if not (height > width):
        print("Video is not a vertical video, skipping thumbnail generation.")
        return None

    if duration < 180: # 不足3分钟，则是shorts，不需要生成缩略图
        print("Video duration is less than 180 seconds, skipping thumbnail generation.")
        return None

    # Use a unique temp directory per run to avoid concurrency conflicts
    temp_dir = f"temp_frames_{uuid.uuid4().hex}"
    os.makedirs(temp_dir, exist_ok=True)

    frame_paths = []
    run_id = uuid.uuid4().hex  # Unique suffix for frame file names
    for i in range(3):
        random_time = random.uniform(duration * 0.1, duration * 0.9)
        # Make frame file names unique to avoid conflicts during concurrent runs
        frame_path = os.path.join(temp_dir, f'frame_{i+1}_{run_id}.jpg')

        command = [
            'ffmpeg',
            '-ss', str(random_time),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            frame_path,
            '-y'
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            frame_paths.append(frame_path)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error extracting frame {i+1}: {e.stderr if isinstance(e, subprocess.CalledProcessError) else e}")
            for fp in frame_paths:
                if os.path.exists(fp):
                    os.remove(fp)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            return None

    if len(frame_paths) != 3:
        print("Could not extract 3 frames.")
        for fp in frame_paths:
            os.remove(fp)
        os.rmdir(temp_dir)
        return None

    # Use a randomized filename to avoid conflicts/overwrites in concurrent or repeated runs
    output_thumbnail_path = os.path.join(
        os.path.dirname(video_path), f"generated_thumbnail_{uuid.uuid4().hex[:8]}.jpg"
    )
    
    stitch_command = [
        'ffmpeg',
        '-i', frame_paths[0],
        '-i', frame_paths[1],
        '-i', frame_paths[2],
        '-filter_complex', 'hstack=inputs=3',
        output_thumbnail_path,
        '-y'
    ]
    try:
        subprocess.run(stitch_command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        # If a caption is provided, overlay it on the stitched thumbnail
        if caption:
            result = add_caption_to_image(output_thumbnail_path, caption, color=color)
            if result is None:
                output_thumbnail_path = None
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error stitching frames: {e.stderr if isinstance(e, subprocess.CalledProcessError) else e}")
        output_thumbnail_path = None

    for fp in frame_paths:
        os.remove(fp)
    os.rmdir(temp_dir)

    return output_thumbnail_path

def generate_stream_thumbnail(video_path, caption: str = None, color: str = 'yellow'):
    """
    Generates a thumbnail for a live stream based on video orientation.

    - For vertical videos (height > width), it stitches 3 random frames.
    - For horizontal videos (width >= height), it extracts a single random frame.

    Args:
        video_path (str): The path to the video file.

    Returns:
        str: The path to the generated thumbnail, or None if generation fails.
    """
    duration = get_video_duration(video_path)
    width, height = get_video_resolution(video_path)

    if duration is None or width is None or height is None:
        return None

    output_thumbnail_path = os.path.join(os.path.dirname(video_path), 'generated_stream_thumbnail.jpg')

    if height > width:  # Vertical video
        print("Vertical video detected. Generating a 3-frame stitched thumbnail.")
        return generate_thumbnail(video_path, caption, color) # Reuse existing logic; add caption if provided
    else:  # Horizontal or square video
        print("Horizontal/square video detected. Generating a single-frame thumbnail.")
        random_time = random.uniform(duration * 0.1, duration * 0.9)
        command = [
            'ffmpeg',
            '-ss', str(random_time),
            '-i', video_path,
            '-vframes', '1',
            '-q:v', '2',
            output_thumbnail_path,
            '-y'
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if caption:
                result = add_caption_to_image(output_thumbnail_path, caption, color=color)
                return result
            return output_thumbnail_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error extracting single frame: {e.stderr if isinstance(e, subprocess.CalledProcessError) else e}")
            return None