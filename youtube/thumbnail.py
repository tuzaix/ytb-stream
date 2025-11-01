import subprocess
import random
import os
import uuid
import numpy as np
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont

def _escape_drawtext_text(text: str) -> str:
    """Escapes text for ffmpeg drawtext filter.

    - Replaces newlines with literal \n for multi-line rendering
    - Escapes characters that conflict with drawtext option delimiters
    """
    if text is None:
        return ""
    # ffmpeg drawtext uses ':' as option delimiter and single quotes for text
    escaped = text.replace('\\', r'\\')
    escaped = escaped.replace(':', r'\:')
    escaped = escaped.replace("'", r"\'")
    escaped = escaped.replace('\n', r'\\n')  # normalize any existing newline
    return escaped

def _find_font_file() -> str:
    """Finds an available (preferably bold) font file on Windows supporting Latin and CJK.

    Priority order (bold first): Microsoft YaHei Bold, SimHei, Microsoft YaHei, Arial Bold, Arial.
    Returns empty string if none found, letting PIL pick a default.
    """
    candidates = [
        r"C:\\Windows\\Fonts\\msyhbd.ttc",  # Microsoft YaHei Bold
        r"C:\\Windows\\Fonts\\msyhbd.ttf",
        r"C:\\Windows\\Fonts\\simhei.ttf",   # SimHei (heavy weight)
        r"C:\\Windows\\Fonts\\msyh.ttc",    # Microsoft YaHei
        r"C:\\Windows\\Fonts\\msyh.ttf",
        r"C:\\Windows\\Fonts\\arialbd.ttf", # Arial Bold
        r"C:\\Windows\\Fonts\\arial.ttf",   # Arial
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return ""

def _wrap_caption(text: str, max_chars_per_line: int) -> str:
    """Wraps caption text to multiple lines based on a max characters per line.

    - Uses word-based wrapping when spaces exist
    - Falls back to character-chunk wrapping for long CJK sequences without spaces
    """
    if not text:
        return ""
    text = text.strip()
    if max_chars_per_line <= 1:
        return text

    words = text.split()
    lines = []
    current = ""
    if len(words) > 1:
        for w in words:
            if not current:
                current = w
            elif len(current) + 1 + len(w) <= max_chars_per_line:
                current += " " + w
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
    else:
        # No spaces, likely CJK string; chunk by character count
        s = text
        for i in range(0, len(s), max_chars_per_line):
            lines.append(s[i:i + max_chars_per_line])

    return "\n".join(lines)

def _compute_fontsize(image_w: int, image_h: int, longest_line_len: int, num_lines: int) -> int:
    """Computes font size so caption block looks balanced and prominent.

    Heuristics (optimized for larger text with tighter padding):
    - Base size ~10% of image height for prominence
    - Width constraint: longest line ~90% of safe width (glyph width ~0.6*fontsize)
    - Height constraint: total lines occupy up to ~80% of image height,
      with comfortable line height ~1.10x and line spacing ~0.10x fontsize.
    Returns the final fontsize clamped to reasonable bounds.
    """
    base = max(24, int(image_h * 0.10))
    approx_glyph_ratio = 0.6
    # Available area after padding: left/right 10% -> 80% width; top/bottom 10% -> 80% height
    target_width_ratio = 0.80
    target_height_ratio = 0.80

    width_font = int((image_w * target_width_ratio) / (max(1, longest_line_len) * approx_glyph_ratio))
    # Adjust spacing for ~1.10x line height: extra spacing ~0.10 * fontsize
    line_height_ratio = 1.10
    line_spacing_ratio = 0.10
    line_spacing = int(base * line_spacing_ratio)
    height_font = int(
        ((image_h * target_height_ratio) - max(0, num_lines - 1) * line_spacing)
        / (max(1, num_lines) * line_height_ratio)
    )

    # Clamp to sane range and pick the most restrictive
    upper_cap = int(image_h * 0.18)
    final = max(32, min(base, width_font, height_font, upper_cap))
    return final

def add_caption_to_image(image_path: str, caption: str, color: str = 'yellow') -> str:
    """
    Render caption onto an image using MoviePy + PIL.

    Visual rules:
    - Keep original case for text, configurable fill color with black stroke/shadow.
    - Safe area: 10% left/right padding, 10% top/bottom padding; text centered.
    - Adaptive font size to fit ~80% width and ~80% height of image.
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

    # Derive max chars per line from safe width (80%) and estimated glyph width,
    # and intentionally reduce per-line character count to enlarge font size.
    base_for_wrap = max(24, int(h * 0.10))
    available_width = w * 0.80
    estimated_glyph_width = base_for_wrap * 0.6
    # Reduce allowable chars per line by ~15% to encourage wrapping
    derived_chars = int(available_width / max(1, estimated_glyph_width))
    max_chars_per_line = max(5, int(derived_chars * 0.85))
    wrapped = _wrap_caption(caption_up, max_chars_per_line)
    lines = wrapped.split('\n') if wrapped else []
    longest = max((len(line) for line in lines), default=len(wrapped))
    num_lines = max(1, len(lines))
    fontsize = _compute_fontsize(w, h, longest, num_lines)
    spacing = int(max(0, fontsize * 0.10))

    # Choose font
    font_path = _find_font_file()
    try:
        font = ImageFont.truetype(font_path, fontsize) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Create transparent overlay the same size as base
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Compute safe area and text bounding box
    safe_x = int(w * 0.10)
    safe_y = int(h * 0.10)
    safe_w = int(w * 0.80)
    safe_h = int(h * 0.80)

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

    def _draw_text_block(origin_x, origin_y, lines_list, fill=(255, 255, 0, 255), stroke_width=0, stroke_fill=None):
        x0, y0 = origin_x, origin_y
        _, _, typical_h = _measure_text_block(lines_list)
        y = y0
        for ln in lines_list:
            # center each line inside safe area horizontally
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
            x = origin_x + max(0, (safe_w - line_w) // 2)
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
    _draw_text_block(tx + shadow_offset[0], ty + shadow_offset[1], lines, fill=(0, 0, 0, 180))
    # Simulate bold: extra passes without stroke
    bold_offset = max(1, int(fontsize * 0.02))
    for ox, oy in [(bold_offset, 0), (-bold_offset, 0), (0, bold_offset), (0, -bold_offset)]:
        _draw_text_block(tx + ox, ty + oy, lines, fill=(*text_color, 255))
    # Main text: specified color with black stroke
    _draw_text_block(tx, ty, lines, fill=(*text_color, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))

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

    output_thumbnail_path = os.path.join(os.path.dirname(video_path), 'generated_thumbnail.jpg')
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