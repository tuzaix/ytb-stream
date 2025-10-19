# YouTube Live Streamer

This project provides a Python module to create and stream to a YouTube live broadcast using the YouTube Data API and FFmpeg.

## 功能

- **创建直播**: 自动创建 YouTube 直播活动。
- **视频推流**: 将本地视频文件推送到指定的直播流。
- **状态监控**: 实时监控直播状态。
- **自动结束**: 在推流结束后自动结束直播。
- **可配置性**: 支持通过命令行参数配置直播标题、描述和隐私状态。
- **持久化认证**: 一次认证后，凭据将被保存，无需重复认证。
- **默认为“非儿童内容”**: 所有创建的直播将自动标记为“不适合儿童”。
- **快速开播**: 创建直播后，将立即开始推流，无需手动干预。
- **视频循环播放**: 自动循环播放指定的视频文件，实现 24/7 直播。
- **网络断线自动重连**: 在网络波动或中断时，推流将自动尝试重新连接。
- **默认1080p/30fps**: 直播将以 1080p 分辨率和 30fps 帧率进行。

## Installation

1.  Clone the repository:
    ```
    git clone https://github.com/your-username/ytb-stream.git
    cd ytb-stream
    ```

2.  Install the required dependencies:
    ```
    # pip install -r requirements.txt
    pip install -r requirements.txt --index-url https://pypi.org/simple
    ```

3.  Install FFmpeg. Make sure it is in your system's PATH.

## Getting YouTube API Credentials

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **YouTube Data API v3**.
4.  Create an **OAuth 2.0 Client ID** for a **Desktop application**.
5.  Download the JSON credentials file and save it as `client_secret.json` in the root of the project.

The first time you run the script, you will be prompted to authorize the application in your browser. A `token.json` file will be created to store your credentials for future use.

## Usage

Run the `main.py` script with the required arguments:

```
python main.py --credentials_file client_secret.json --video_file /path/to/your/video.mp4 --title "My Awesome Stream" --description "This is a test stream."

### 使用代理

如果您的网络环境需要代理才能访问 Google 服务，您可以使用 `--proxy` 参数指定代理服务器：

```bash
python main.py --credentials_file client_secret.json --video_file /path/to/your/video.mp4 --proxy http://your-proxy-server:port
```

### 关闭直播

如果你需要手动关闭一个直播，可以使用 `test_close_broadcast.py` 脚本：

```bash
python test_close_broadcast.py --credentials_file client_secret.json --broadcast_id YOUR_BROADCAST_ID
```

### 获取所有直播

你可以使用 `get_broadcast_ids.py` 脚本来获取所有直播的列表及其状态：

```bash
python get_broadcast_ids.py --credentials_file client_secret.json
```

默认情况下，所有通过此工具创建的直播都将被标记为 **不面向儿童**。
```

The first time you run the script, you will be prompted to authorize the application in your browser. A `token.json` file will be created to store your credentials for future use.

### Command-Line Arguments

*   `--credentials_file`: (Required) Path to the credentials file (e.g., `client_secret.json`).
*   `--video_file`: (Required) Path to the video file to stream.
*   `--title`: Title of the live stream (default: "My Live Stream").
*   `--description`: Description of the live stream (default: "").
*   `--privacy_status`: Privacy status of the live stream (public, private, or unlisted) (default: "private").