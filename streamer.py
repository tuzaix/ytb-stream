import subprocess

class Streamer:
    def __init__(self, stream_url, video_path):
        """
        Initializes the streamer.

        Args:
            stream_url (str): The RTMP URL to stream to.
            video_path (str): The path to the video file to stream.
        """
        self.stream_url = stream_url
        self.video_path = video_path
        self.process = None

    def start_streaming(self):
        """Starts the FFmpeg streaming process."""
        command = [
            'ffmpeg',
            '-re',
            '-stream_loop', '-1',
            '-i', self.video_path,
            # '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-r', '30', '-g', '60', '-b:v', '2500k',
            # '-acodec', 'aac', '-ar', '44100', '-b:a', '128k',
            '-f', 'flv',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-reconnect_on_network_error', '1',
            self.stream_url
        ]
        self.process = subprocess.Popen(command)

    def stop_streaming(self):
        """Stops the FFmpeg streaming process."""
        if self.process:
            self.process.terminate()