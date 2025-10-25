import subprocess
import random
import os

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
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
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
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        width, height = map(int, result.stdout.strip().split('x'))
        return width, height
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"Error getting video resolution: {e}")
        return None, None

def generate_thumbnail(video_path):
    """
    Generates a thumbnail by stitching three random frames from a video
    if the video is a vertical video (height > width).

    Args:
        video_path (str): The path to the video file.

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

    temp_dir = 'temp_frames'
    os.makedirs(temp_dir, exist_ok=True)

    frame_paths = []
    for i in range(3):
        random_time = random.uniform(duration * 0.1, duration * 0.9)
        frame_path = os.path.join(temp_dir, f'frame_{i+1}.jpg')

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
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
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
        subprocess.run(stitch_command, check=True, capture_output=True, text=True, encoding='utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error stitching frames: {e.stderr if isinstance(e, subprocess.CalledProcessError) else e}")
        output_thumbnail_path = None

    for fp in frame_paths:
        os.remove(fp)
    os.rmdir(temp_dir)

    return output_thumbnail_path

def generate_stream_thumbnail(video_path):
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
        return generate_thumbnail(video_path) # Reuse existing logic for vertical videos
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
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            return output_thumbnail_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error extracting single frame: {e.stderr if isinstance(e, subprocess.CalledProcessError) else e}")
            return None