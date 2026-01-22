import argparse
import time
import threading
import ctypes
import os
import platform
import signal
import logging
from typing import Optional
from youtube.client import YouTubeClient
from youtube.thumbnail import generate_stream_thumbnail, add_caption_to_image
from streamer import Streamer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def shutdown_after_duration(duration_seconds, duration_hours, stop_event=None):
    """
    Waits for a given duration and then sends a signal to stop the process.
    If stop_event is provided (threading mode), it sets the event.
    """
    if stop_event:
        logger.info(f"Monitor started: shutting down in {duration_hours} hours.")
        if stop_event.wait(duration_seconds):
            return # Stopped externally
        logger.info(f"\n{duration_hours}-hour limit reached. Signaling stop...")
        stop_event.set()
    else:
        # Legacy process-based shutdown
        time.sleep(duration_seconds)
        print(f"\n{duration_hours}-hour limit reached. Initiating shutdown...")

        if platform.system() == "Windows":
            # On Windows, this sends a Ctrl+C event to the process console.
            ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, 0)
        else:
            # On Linux/macOS, send a SIGINT signal (equivalent to Ctrl+C).
            os.kill(os.getpid(), signal.SIGINT)

def run_broadcast(
    auth_dir: str,
    video_file: str,
    title: str = "My Live Stream",
    description: str = "",
    privacy_status: str = "unlisted",
    proxy: Optional[str] = None,
    duration: float = 3.0,
    thumbnail: Optional[str] = None,
    thumbnail_caption: str = "",
    thumbnail_color: str = "yellow",
    log_file: Optional[str] = None
):
    """
    Main entry point for running a broadcast programmatically.
    """
    # Configure file logging if requested
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to setup log file {log_file}: {e}")

    # Use a threading Event to control the loop
    stop_event = threading.Event()
    
    credentials_file = os.path.join(auth_dir, "client_secret.json")
    token_file = os.path.join(auth_dir, "token.json")

    if not os.path.exists(credentials_file):
        logger.error(f"Error: 'client_secret.json' not found in '{auth_dir}'.")
        return

    try:
        client = YouTubeClient(credentials_file, token_file=token_file, proxy=proxy)
    except Exception as e:
        logger.error(f"Failed to initialize YouTubeClient: {e}")
        return

    logger.info("Checking for existing broadcasts...")
    try:
        existing_broadcasts = client.get_all_broadcasts()
        if existing_broadcasts:
            logger.info(f"Found {len(existing_broadcasts)} existing broadcasts. Closing them...")
            for broadcast in existing_broadcasts:
                broadcast_id = broadcast['id']
                status = broadcast['status']['lifeCycleStatus']
                if status in ['live', 'testing']:
                    logger.info(f"Closing broadcast {broadcast_id} (status: {status})...")
                    try:
                        client.close_live_broadcast(broadcast_id)
                        logger.info(f"Broadcast {broadcast_id} closed.")
                        time.sleep(3)
                    except Exception as e:
                        logger.error(f"Failed to close broadcast {broadcast_id}: {e}")
                elif status == 'created':
                    logger.info(f"Deleting broadcast {broadcast_id} (status: {status})...")
                    try:
                        client.delete_live_broadcast(broadcast_id)
                        logger.info(f"Broadcast {broadcast_id} deleted.")
                        time.sleep(3)
                    except Exception as e:
                        logger.error(f"Failed to delete broadcast {broadcast_id}: {e}")
            logger.info("Finished closing existing broadcasts.")
        else:
            logger.info("No existing broadcasts found.")
    except Exception as e:
        logger.error(f"Error checking existing broadcasts: {e}")

    time.sleep(3)
    logger.info("Creating new broadcast...")
    try:
        broadcast, stream = client.create_live_broadcast(title, description, privacy_status)
    except Exception as e:
        logger.error(f"Failed to create broadcast: {e}")
        return

    if not broadcast or broadcast.get("status", {}).get("lifeCycleStatus") != "ready":
        logger.error("Failed to create broadcast or incorrect status.")
        if broadcast:
            logger.error(f"Status: {broadcast.get('status', {}).get('lifeCycleStatus')}")
        return

    broadcast_id = broadcast["id"]
    logger.info(f"Broadcast created. ID: {broadcast_id}")

    # Thumbnail handling
    logger.info("Preparing thumbnail...")
    
    def prepare_thumbnail_with_caption(video_path, base_thumbnail, caption, color):
        caption_text = caption.strip() if caption else ""
        if caption_text and base_thumbnail and os.path.exists(base_thumbnail):
            root, ext = os.path.splitext(base_thumbnail)
            ext = ext or ".jpg"
            captioned_path = f"{root}_captioned{ext}"
            try:
                import shutil
                shutil.copy(base_thumbnail, captioned_path)
                result = add_caption_to_image(captioned_path, caption_text, color=color)
                if result: return result
            except Exception as e:
                logger.error(f"Error preparing captioned thumbnail: {e}")

        generated = generate_stream_thumbnail(video_path, caption_text if caption_text else None, color=color)
        return generated

    if thumbnail and os.path.exists(thumbnail):
        thumbnail_path = thumbnail
    else:
        thumbnail_path = prepare_thumbnail_with_caption(video_file, thumbnail, thumbnail_caption, thumbnail_color)

    if thumbnail_path:
        try:
            client.set_thumbnail(broadcast_id, thumbnail_path)
            logger.info(f"Thumbnail set: {thumbnail_path}")
            if thumbnail_path != thumbnail: # If generated or captioned copy
                 try:
                    os.remove(thumbnail_path)
                 except: pass
        except Exception as e:
            logger.error(f"Failed to set thumbnail: {e}")
    else:
        logger.warning("Thumbnail preparation failed.")

    stream_url = f"{stream['cdn']['ingestionInfo']['ingestionAddress']}/{stream['cdn']['ingestionInfo']['streamName']}"
    
    time.sleep(3)
    streamer = Streamer(stream_url, video_file)
    logger.info(f"Starting stream to {stream_url}")
    streamer.start_streaming()

    logger.info("Waiting for stream to go live...")
    start_wait_time = time.time()
    is_live = False
    while time.time() - start_wait_time < 300:
        if stop_event.is_set(): break
        status = client.get_live_broadcast_status(broadcast_id)
        logger.info(f"Status: {status}")
        if status == 'live':
            is_live = True
            logger.info(f"Broadcast {broadcast_id} is live.")
            break
        time.sleep(5)
    
    if not is_live and not stop_event.is_set():
        logger.error("Timeout waiting for live status.")
        streamer.stop_streaming()
        try:
            client.delete_live_broadcast(broadcast_id)
        except: pass
        return

    # Monitor loop
    monitor_thread = None
    if duration > 0:
        duration_limit_seconds = duration * 3600
        monitor_thread = threading.Thread(
            target=shutdown_after_duration,
            args=(duration_limit_seconds, duration, stop_event),
            daemon=True
        )
        monitor_thread.start()

    try:
        while not stop_event.is_set():
            status = client.get_live_broadcast_status(broadcast_id)
            if status != 'live':
                logger.warning(f"Broadcast no longer live (status: {status}). Stopping.")
                break
            time.sleep(15)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received.")
        pass
    except Exception as e:
        logger.error(f"Error in monitor loop: {e}")
    finally:
        logger.info("Stopping stream and closing broadcast...")
        stop_event.set() # Ensure monitor thread knows
        streamer.stop_streaming()
        try:
            client.close_live_broadcast(broadcast_id)
            logger.info("Broadcast closed.")
        except Exception as e:
            logger.error(f"Error closing broadcast: {e}")

def main():
    parser = argparse.ArgumentParser(description="YouTube Live Streamer")
    parser.add_argument("--auth_dir", required=True, help="Directory for authentication files (client_secret.json and token.json).")
    parser.add_argument("--video_file", required=True, help="Path to the video file to stream.")
    parser.add_argument("--title", default="My Live Stream", help="Title of the live stream.")
    parser.add_argument("--description", default="", help="Description of the live stream.")
    parser.add_argument("--privacy_status", default="unlisted", help="Privacy status of the live stream (public, private, or unlisted).")
    parser.add_argument("--proxy", help="Proxy server to use for requests (e.g., http://localhost:7897)", default=None)
    parser.add_argument("--duration", type=float, default=3.0, help="Maximum duration of the live stream in hours. Set to 0 for no limit.")
    parser.add_argument("--thumbnail", type=str, help="Optional path to a custom thumbnail image")
    parser.add_argument("--thumbnail_caption", type=str, default="", help="Caption text for the thumbnail")
    parser.add_argument("--thumbnail_color", type=str, default="yellow", help="Caption color")
    args = parser.parse_args()

    run_broadcast(
        auth_dir=args.auth_dir,
        video_file=args.video_file,
        title=args.title,
        description=args.description,
        privacy_status=args.privacy_status,
        proxy=args.proxy,
        duration=args.duration,
        thumbnail=args.thumbnail,
        thumbnail_caption=args.thumbnail_caption,
        thumbnail_color=args.thumbnail_color
    )

if __name__ == "__main__":
    main()