import os
import sys
import argparse
import subprocess
from typing import List, Tuple
from typing import Optional


SUPPORTED_EXTS = {
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".ts", ".flv", ".wmv", ".3gp"
}


def is_video_file(filename: str) -> bool:
    """Return True if filename ends with a supported video extension."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in SUPPORTED_EXTS


def ensure_dir(path: str) -> None:
    """Create directory path if it does not exist."""
    os.makedirs(path, exist_ok=True)


def build_output_path(base_dir: str, cover_dir: str, dirpath: str, filename: str, fmt: str = "jpg") -> str:
    """Build output JPG path under `cover_dir`, mirroring the input directory structure.

    - Mirrors subdirectories under `cover_dir` to avoid filename collisions for same basenames.
    - Changes extension to `.jpg`.
    """
    rel = os.path.relpath(dirpath, start=base_dir)
    out_dir = os.path.join(cover_dir, rel) if rel != "." else cover_dir
    ensure_dir(out_dir)
    name, _ = os.path.splitext(filename)
    ext = "png" if fmt.lower() == "png" else "jpg"
    return os.path.join(out_dir, f"{name}.{ext}")


def probe_video_resolution(video_path: str) -> Optional[Tuple[int, int]]:
    """Probe video resolution using ffprobe. Returns (width, height) or None on failure."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        video_path,
    ]
    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        out = res.stdout.strip()
        if not out:
            return None
        parts = out.split('x')
        if len(parts) != 2:
            return None
        width = int(parts[0])
        height = int(parts[1])
        return width, height
    except Exception:
        return None


def extract_first_frame(
    video_path: str,
    output_path: str,
    overwrite: bool = False,
    quality: int = 2,
    fmt: str = "jpg",
    seek: float = 0.0,
) -> Tuple[bool, str]:
    """Extract the very first frame of a video to a JPEG using ffmpeg.

    Args:
        video_path: Input video file path.
        output_path: Target image path (.jpg).
        overwrite: Whether to overwrite existing image.

    Returns:
        (ok, message): ok indicates success; message includes info or error detail.
    """
    if (not overwrite) and os.path.exists(output_path):
        return True, f"Skip existing: {output_path}"

    # Build ffmpeg command. Use -ss before -i for fast seek; small positive seek can avoid black frames.
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
    ]

    # If seek provided and > 0, use it; otherwise use 0
    cmd += ["-ss", str(seek if seek and seek > 0 else 0)]
    cmd += ["-i", video_path, "-frames:v", "1"]

    # Output format specific options
    if fmt.lower() == "jpg" or fmt.lower() == "jpeg":
        # -q:v: 2 is high quality, 1 is best. Range 1-31 (lower better)
        cmd += ["-q:v", str(max(1, min(31, quality))), output_path]
    elif fmt.lower() == "png":
        # PNG uses -compression_level 0-9 (0 fastest, 9 smallest)
        # Map quality 1-31 to compression 0-9 inversely
        comp = int(max(0, min(9, round((31 - max(1, min(31, quality))) / 31 * 9))))
        cmd += ["-compression_level", str(comp), output_path]
    else:
        # default fallback
        cmd += ["-q:v", str(max(1, min(31, quality))), output_path]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return True, f"Saved: {output_path}"
    except subprocess.CalledProcessError as e:
        # Show stderr for troubleshooting
        return False, f"ffmpeg error for {video_path}: {e.stderr or e}"
    except FileNotFoundError:
        return False, "ffmpeg not found. Please install ffmpeg and ensure it is in PATH."


def scan_and_extract(
    base_dir: str,
    overwrite: bool = False,
    recursive: bool = True,
    quality: int = 2,
    fmt: str = "jpg",
    seek: float = 0.0,
) -> List[str]:
    """Traverse `base_dir` and extract first frames for all videos to `cover` subdirectory.

    - Mirrors input directory structure under `cover` to avoid collisions.
    - Skips files already extracted unless `overwrite=True`.

    Returns:
        A list of status messages for each processed file.
    """
    base_dir = os.path.abspath(base_dir)
    if not os.path.isdir(base_dir):
        return [f"Not a directory: {base_dir}"]

    cover_dir = os.path.join(base_dir, "cover")
    ensure_dir(cover_dir)

    messages: List[str] = []

    if recursive:
        walker = os.walk(base_dir)
    else:
        # Non-recursive: only top-level files
        walker = [(base_dir, [], os.listdir(base_dir))]

    for dirpath, dirnames, filenames in walker:
        # Avoid traversing the 'cover' output directory itself
        dirnames[:] = [d for d in dirnames if os.path.join(dirpath, d) != cover_dir]

        for fname in filenames:
            if not is_video_file(fname):
                continue
            in_path = os.path.join(dirpath, fname)
            # Probe resolution to route into subdirectories like cover/1080x1920
            wh = probe_video_resolution(in_path)
            if wh:
                res_dir = os.path.join(cover_dir, f"{wh[0]}x{wh[1]}")
            else:
                res_dir = os.path.join(cover_dir, "unknown_resolution")
            ensure_dir(res_dir)

            # Use res_dir as the base for mirroring relative structure
            rel = os.path.relpath(dirpath, start=base_dir)
            out_parent_dir = os.path.join(res_dir, rel) if rel != "." else res_dir
            ensure_dir(out_parent_dir)
            name, _ = os.path.splitext(fname)
            ext = "png" if fmt.lower() == "png" else "jpg"
            out_path = os.path.join(out_parent_dir, f"{name}.{ext}")
            ok, msg = extract_first_frame(
                in_path, out_path, overwrite=overwrite, quality=quality, fmt=fmt, seek=seek
            )
            messages.append(msg)

    return messages


def parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Traverse a directory and extract the first frame of all video files "
            "into a 'cover' subdirectory (mirrors structure)."
        )
    )
    parser.add_argument("directory", help="Base directory to scan for video files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing cover images")
    parser.add_argument("--no-recursive", action="store_true", help="Do not scan subdirectories")
    parser.add_argument("--format", choices=["jpg", "png"], default="jpg", help="Output image format")
    parser.add_argument(
        "--quality",
        type=int,
        default=2,
        help="JPEG quality 1-31 (lower is better); for PNG maps to compression level",
    )
    parser.add_argument(
        "--seek",
        type=float,
        default=0.0,
        help="Seek seconds before first frame (e.g., 0.2 to avoid black frames)",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    """CLI entry point: process args and run extraction."""
    args = parse_args(argv)
    base_dir = args.directory
    recursive = not args.no_recursive
    overwrite = args.overwrite

    print(f"Scanning: {os.path.abspath(base_dir)}")
    print(f"Recursive: {recursive} | Overwrite: {overwrite}")

    messages = scan_and_extract(
        base_dir,
        overwrite=overwrite,
        recursive=recursive,
        quality=args.quality,
        fmt=args.format,
        seek=args.seek,
    )
    for m in messages:
        print(m)

    # Indicate success if at least one file processed or no errors
    has_error = any(m.lower().startswith("ffmpeg error") or m.lower().startswith("not a directory") for m in messages)
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))