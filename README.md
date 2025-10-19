# YouTube Live Streaming Tool

This tool automates the process of streaming a local video file to YouTube Live. It creates a live broadcast, streams the video, and can automatically stop the broadcast after a configured duration.

## Features

- **Automated Broadcast Creation**: Automatically creates a new live broadcast on YouTube.
- **Push-to-Start**: The broadcast automatically starts when the stream begins.
- **Push-to-Stop**: The broadcast automatically stops when the stream ends.
- **Configurable Duration**: Set a maximum duration for the live stream, after which it will automatically shut down.
- **Multi-Account Support**: Easily manage credentials for different YouTube accounts using separate directories.
- **Robust Error Handling**: Provides clear instructions for common authentication and configuration issues.

## Deployment on Ubuntu

This guide will walk you through deploying and running the YouTube Live Streaming Tool on an Ubuntu server.

### 1. System Preparation

First, update your package list and install essential packages: `python3`, `pip`, and `ffmpeg`.

```bash
sudo apt update
sudo apt install python3 python3-pip ffmpeg -y
```

### 2. Project Setup

Clone the project repository or copy the files to your Ubuntu server.

```bash
git clone <your-repository-url>
cd ytb-stream
```

### 3. Install Python Dependencies

Install the necessary Python libraries using the `requirements.txt` file.

```bash
pip3 install -r requirements.txt
```

### 4. Google Cloud Authentication

To stream to YouTube, you need to authenticate using OAuth 2.0 credentials.

1.  **Create a Google Cloud Project**: If you don't have one, create a project at the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable the YouTube Data API**: In your project, go to "APIs & Services" > "Library" and enable the "YouTube Data API v3".
3.  **Configure the OAuth Consent Screen**:
    *   Go to "APIs & Services" > "OAuth consent screen".
    *   Choose **External** and create the consent screen.
    *   Fill in the required app information.
    *   **Crucially**, if your app is in the "Testing" publishing status, you must add your Google account's email address under "Test users".
4.  **Create OAuth 2.0 Credentials**:
    *   Go to "APIs & Services" > "Credentials".
    *   Click "+ CREATE CREDENTIALS" and select "OAuth client ID".
    *   For the application type, select **Desktop app**.
    *   Download the JSON file. It will be named something like `client_secret_xxxxxxxx.json`.

### 5. Configure Credentials in the Project

1.  Create a directory to hold your authentication files. This allows you to manage multiple accounts easily.

    ```bash
    mkdir the_robot_guy
    ```

2.  Rename the downloaded JSON file to `client_secret.json` and move it into the directory you just created.

    ```bash
    mv /path/to/your/downloaded/client_secret.json the_robot_guy/client_secret.json
    ```

### 6. Prepare the Video File

Place the video file you want to stream (e.g., `stream.mp4`) in the project's root directory.

### 7. Run the Application

Execute the `main.py` script with the appropriate arguments.

```bash
python3 main.py \
  --auth_dir="the_robot_guy" \
  --video_file="stream.mp4" \
  --title="My Awesome Live Stream" \
  --description="Check out this cool stream!" \
  --privacy_status="public" \
  --duration=10800
```

**Argument Explanations:**

*   `--auth_dir`: The directory containing your `client_secret.json`.
*   `--video_file`: The path to the video you want to stream.
*   `--title`: The title of your YouTube live broadcast.
*   `--description`: The description for the broadcast.
*   `--privacy_status`: The privacy of the stream (`public`, `private`, or `unlisted`).
*   `--duration`: The time in **seconds** after which the stream will automatically stop. Set to `0` to disable auto-shutdown. (Default: 10800 seconds = 3 hours).

#### First-Time Authorization

The first time you run the script for a new account, you will be prompted to authorize the application:

1.  A URL will be printed in the console.
2.  Copy this URL and paste it into a web browser.
3.  Log in with the Google account you added as a "Test user".
4.  Grant the application permission to access your YouTube account.

After successful authorization, a `token.json` file will be created in your `--auth_dir` directory. Subsequent runs will use this token and will not require manual authorization.

### 8. (Optional) Running as a Background Service

For long-running streams, it's best to run the script as a background service using a process manager like `systemd` or `supervisor`. This ensures the stream continues even if you close your terminal.

This completes the deployment and execution guide for running the tool on Ubuntu.