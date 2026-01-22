import os
import json
import sys

# 配置文件路径
_current_dir = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(_current_dir, "settings.json")
SETTINGS_EXAMPLE_FILE = os.path.join(_current_dir, "settings.json.example")

if not os.path.exists(SETTINGS_FILE):
    # Fallback to defaults if no settings file, but warn
    pass

_config = {}
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            tmp_config = json.load(f)
            # 检查对应的key是否存在，不存在则剔除，方便下面使用默认值
            for key, value in tmp_config.items():
                if value:
                    _config[key] = value
    except Exception as e:
        print(f"Error: 无法解析配置文件 {SETTINGS_FILE}: {e}")
        sys.exit(1)

# 后台管理账号配置
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", _config.get("ADMIN_USERNAME", "admin"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", _config.get("ADMIN_PASSWORD", "admin"))

# API 访问令牌
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", _config.get("ACCESS_TOKEN", "fake-super-secret-token"))

# 限制创建的账户群个数
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", _config.get("MAX_ACCOUNTS", 6)))

# 调度器最大并发线程数
SCHEDULER_MAX_WORKERS = int(os.getenv("SCHEDULER_MAX_WORKERS", _config.get("SCHEDULER_MAX_WORKERS", 10)))

# ftp的根目录
_ftp_root_raw = os.getenv("FTP_ROOT_DIR", _config.get("FTP_ROOT_DIR", os.path.join(_current_dir, "ftp")))
if not os.path.isabs(_ftp_root_raw):
    FTP_ROOT_DIR = os.path.abspath(os.path.join(_current_dir, _ftp_root_raw))
else:
    FTP_ROOT_DIR = _ftp_root_raw

# FTP下的子目录
SUBDIRS = _config.get("SUBDIRS", "")

# Broadcast Script Path
_broadcast_script_raw = os.getenv("BROADCAST_SCRIPT_PATH", _config.get("BROADCAST_SCRIPT_PATH", os.path.abspath(os.path.join(_current_dir, "..", "start-broadcast.sh"))))
if not os.path.isabs(_broadcast_script_raw):
    BROADCAST_SCRIPT_PATH = os.path.abspath(os.path.join(_current_dir, _broadcast_script_raw))
else:
    BROADCAST_SCRIPT_PATH = _broadcast_script_raw

# Max broadcast times per account
MAX_BROADCAST_TIMES_PER_ACCOUNT = int(os.getenv("MAX_BROADCAST_TIMES_PER_ACCOUNT", _config.get("MAX_BROADCAST_TIMES_PER_ACCOUNT", 4)))

