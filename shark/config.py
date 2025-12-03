import os

class Config:
    # Database
    DB_USER = "root"
    DB_PASSWORD = "root"
    DB_HOST = "localhost"
    DB_PORT = "3306"
    DB_NAME = "ytb_shark"
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # JWT
    SECRET_KEY = "your-secret-key-keep-it-secret" # Change this in production
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    # External Scripts
    FTP_SCRIPT_PATH = r"d:\develop\ytb-stream\dev_tools\vsftpd\create_ftpuser.sh"
    UPLOAD_SCRIPT_PATH = r"d:\develop\ytb-stream\ytb_upload_video_by_account.py"
    MATERIAL_CONFIG_PATH = r"d:\develop\ytb-stream\ytb_account_material_config.py"
    
    # FTP Connection Info
    FTP_HOST = "127.0.0.1"
    FTP_PORT = 21
    
    # File Storage
    UPLOAD_DIR = r"d:\develop\ytb-stream\shark_uploads"
    
    # FTP Root (Template)
    # format: {username} is the User.username, {account_name} is YoutubeAccount.account_name
    BASE_FTP_HOME = "/home/ftp/{username}/{account_name}"

    # YouTube Auth Files Path (Template)
    # format: {username} is the User.username, {account_name} is YoutubeAccount.account_name
    YOUTUBE_AUTH_FILES_HOME = "/home/youtube_auth_files/{username}/{account_name}"

config = Config()
