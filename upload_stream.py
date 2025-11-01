import argparse
import time
import threading
import ctypes
import os
import platform
import signal
from youtube.client import YouTubeClient
from youtube.thumbnail import generate_stream_thumbnail, add_caption_to_image
from streamer import Streamer

def shutdown_after_duration(duration_seconds, duration_hours):
    """
    Waits for a given duration and then sends a Ctrl+C signal to the process
    to trigger a graceful shutdown. This function is cross-platform.
    """
    time.sleep(duration_seconds)
    print(f"\n{duration_hours}-hour limit reached. Initiating shutdown...")

    if platform.system() == "Windows":
        # On Windows, this sends a Ctrl+C event to the process console.
        ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, 0)
    else:
        # On Linux/macOS, send a SIGINT signal (equivalent to Ctrl+C).
        os.kill(os.getpid(), signal.SIGINT)

def main():
    parser = argparse.ArgumentParser(description="YouTube Live Streamer")
    parser.add_argument("--auth_dir", required=True, help="Directory for authentication files (client_secret.json and token.json).")
    parser.add_argument("--video_file", required=True, help="Path to the video file to stream.")
    parser.add_argument("--title", default="My Live Stream", help="Title of the live stream.")
    parser.add_argument("--description", default="", help="Description of the live stream.")
    parser.add_argument("--privacy_status", default="unlisted", help="Privacy status of the live stream (public, private, or unlisted).")
    parser.add_argument("--proxy", help="Proxy server to use for requests (e.g., http://localhost:7897)", default=None)
    parser.add_argument("--duration", type=float, default=3.0, help="Maximum duration of the live stream in hours. Set to 0 for no limit.")
    # Thumbnail and caption options (aligned with upload_video.py)
    parser.add_argument("--thumbnail", type=str, help="Optional path to a custom thumbnail image")
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
    args = parser.parse_args()

    credentials_file = os.path.join(args.auth_dir, "client_secret.json")
    token_file = os.path.join(args.auth_dir, "token.json")

    if not os.path.exists(credentials_file):
        print(f"错误: 在目录 '{args.auth_dir}' 中未找到 'client_secret.json'。")
        print("请从 Google Cloud Console 下载您的 OAuth 2.0 客户端ID文件，")
        print(f"并将其重命名为 'client_secret.json' 后放置在 '{args.auth_dir}' 目录中。")
        return

    client = YouTubeClient(credentials_file, token_file=token_file, proxy=args.proxy)

    print("正在检查已存在的直播...")
    existing_broadcasts = client.get_all_broadcasts()
    if existing_broadcasts:
        print(f"发现 {len(existing_broadcasts)} 个已存在的直播。正在关闭它们...")
        for broadcast in existing_broadcasts:
            broadcast_id = broadcast['id']
            status = broadcast['status']['lifeCycleStatus']
            if status in ['live', 'testing']:
                print(f"正在关闭直播 {broadcast_id} (状态: {status})...")
                try:
                    client.close_live_broadcast(broadcast_id)
                    print(f"直播 {broadcast_id} 已关闭。")
                    time.sleep(3)  # Add a 3-second delay
                except Exception as e:
                    print(f"无法关闭直播 {broadcast_id}: {e}")
            elif status == 'created':
                print(f"正在删除直播 {broadcast_id} (状态: {status})...")
                try:
                    client.delete_live_broadcast(broadcast_id)
                    print(f"直播 {broadcast_id} 已删除。")
                    time.sleep(3)  # Add a 3-second delay
                except Exception as e:
                    print(f"无法删除直播 {broadcast_id}: {e}")
        print("已完成关闭所有存在的直播。")
    else:
        print("未发现已存在的直播。")

    time.sleep(3)  # Add a 3-second delay before creating a new broadcast
    print("正在创建新的直播...")
    broadcast, stream = client.create_live_broadcast(
        args.title, args.description, args.privacy_status
    )

    if not broadcast or broadcast.get("status", {}).get("lifeCycleStatus") != "ready":
        print("无法创建直播或直播状态不正确，请检查您的 YouTube 凭据和配额。")
        if broadcast:
            print(f"收到的直播状态: {broadcast.get('status', {}).get('lifeCycleStatus')}")
        return

    broadcast_id = broadcast["id"]

    # Prepare and set the thumbnail (supports caption and color, consistent with upload_video.py)
    print("Preparing thumbnail for the stream...")

    def prepare_thumbnail_with_caption(video_path: str, base_thumbnail: str, caption: str, color: str) -> str:
        """Prepare a thumbnail for the stream.

        - Always generate a thumbnail from the video (auto-generation for streams).
        - If a caption is provided and a base thumbnail exists, overlay the caption on a copy of the base.
        - If caption is provided but no base thumbnail, overlay the caption on the generated thumbnail.
        - If no caption is provided, generate from the video without caption.

        Args:
            video_path: The source video path used to generate thumbnail.
            base_thumbnail: An existing thumbnail image to copy and caption, if caption is provided.
            caption: The text to overlay on the thumbnail.
            color: The color for caption text (e.g., 'yellow', 'red', 'blue').
        """
        caption_text = caption.strip() if caption else ""

        # If caption provided and base thumbnail exists, overlay on base copy
        if caption_text and base_thumbnail and os.path.exists(base_thumbnail):
            root, ext = os.path.splitext(base_thumbnail)
            ext = ext or ".jpg"
            captioned_path = f"{root}_captioned{ext}"
            try:
                import shutil
                shutil.copy(base_thumbnail, captioned_path)
                result = add_caption_to_image(captioned_path, caption_text, color=color)
                if result:
                    return result
                else:
                    print("Failed to overlay caption on provided thumbnail. Will attempt to generate from video.")
            except Exception as e:
                print(f"Error preparing captioned thumbnail from provided file: {e}")

        # Generate from video (with caption if provided)
        generated = generate_stream_thumbnail(video_path, caption_text if caption_text else None, color=color)
        if generated:
            return generated
        else:
            print("Failed to generate thumbnail from video.")
            return None

    thumbnail_path = prepare_thumbnail_with_caption(
        args.video_file, args.thumbnail, args.thumbnail_caption, args.thumbnail_color
    )

    if thumbnail_path:
        try:
            client.set_thumbnail(broadcast_id, thumbnail_path)
            print(f"Successfully set thumbnail: {thumbnail_path}")
            # Clean up generated thumbnail if it was produced during this run
            try:
                os.remove(thumbnail_path)
                print(f"Removed generated thumbnail: {thumbnail_path}")
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to set thumbnail: {e}")
    else:
        print("Thumbnail preparation failed or was skipped.")

    stream_url = f"{stream['cdn']['ingestionInfo']['ingestionAddress']}/{stream['cdn']['ingestionInfo']['streamName']}"

    time.sleep(3)  # Add a 3-second delay before starting the stream
    streamer = Streamer(stream_url, args.video_file)
    print(f"Stream URL: {stream_url}")
    print("Starting stream...")
    streamer.start_streaming()

    # Wait for the stream to be in the 'live' state
    print("Waiting for YouTube to start the stream automatically (up to 5 minutes)...")
    start_time = time.time()
    while time.time() - start_time < 300:
        status = client.get_live_broadcast_status(broadcast_id)
        print(f"Current broadcast status: {status}")
        if status == 'live':
            print(f"Broadcast {broadcast_id} is now live.")
            break
        time.sleep(5)
    else:
        print("Timeout waiting for stream to go live. Aborting.")
        streamer.stop_streaming()
        # Since auto-start is enabled, the broadcast might be in a weird state.
        # Deleting it is safer than trying to close it.
        try:
            client.delete_live_broadcast(broadcast_id)
            print(f"直播 {broadcast_id} 已删除。")
        except Exception as e:
            print(f"无法删除直播 {broadcast_id}: {e}")
        return

    if args.duration > 0:
        # Start the shutdown timer thread
        duration_limit_seconds = args.duration * 3600  # Convert hours to seconds
        monitor_thread = threading.Thread(
            target=shutdown_after_duration,
            args=(duration_limit_seconds, args.duration),
            daemon=True
        )
        monitor_thread.start()
        print(f"监控已启动：直播将在 {args.duration} 小时后自动关闭。")

    try:
        while True:
            status = client.get_live_broadcast_status(broadcast_id)
            print(f"Broadcast status: {status}")
            if status != 'live':
                print(f"直播已不再进行 (当前状态: {status})。正在退出。")
                streamer.stop_streaming()
                break
            print("Stream is live. Press Ctrl+C to stop.")
            time.sleep(15) # Check status less frequently
    except KeyboardInterrupt:
        print("\n正在停止推流...")
        streamer.stop_streaming()
        print("正在关闭直播间...")
        try:
            client.close_live_broadcast(broadcast_id)
            print("直播已结束。")
        except Exception as e:
            print(f"关闭直播间时出错: {e}")
            print("可能是因为直播已通过其他方式结束。")

if __name__ == "__main__":
    main()