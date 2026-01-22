import os
import json
import sys

# 配置文件路径
_current_dir = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(_current_dir, "settings.json")
SETTINGS_EXAMPLE_FILE = os.path.join(_current_dir, "settings.json.example")

if not os.path.exists(SETTINGS_FILE):
    print(f"Error: 配置文件 {SETTINGS_FILE} 不存在。")
    print(f"请将 {SETTINGS_EXAMPLE_FILE} 复制为 {SETTINGS_FILE} 并根据需要修改配置。")
    print(f"命令示例: cp {SETTINGS_EXAMPLE_FILE} {SETTINGS_FILE}")
    sys.exit(1)

try:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        tmp_config = json.load(f)
except Exception as e:
    print(f"Error: 无法解析配置文件 {SETTINGS_FILE}: {e}")
    sys.exit(1)

# 检查对应的key是否存在，不存在则剔除，方便下面使用默认值
keys = tmp_config.keys()
_config = {}
for key, value in tmp_config.items():
    if not value:
        continue 
    _config[key] = value

# 后台管理账号配置
# 优先使用环境变量，其次使用配置文件中的值，最后使用默认值
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", _config.get("ADMIN_USERNAME", "admin"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", _config.get("ADMIN_PASSWORD", "admin"))

# API 访问令牌
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", _config.get("ACCESS_TOKEN", "fake-super-secret-token"))

# 限制创建的账户群个数
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", _config.get("MAX_ACCOUNTS", 6)))

# 限制每个账户的发布时间数量
MAX_PUBLISH_TIMES_PER_ACCOUNT = int(os.getenv("MAX_PUBLISH_TIMES_PER_ACCOUNT", _config.get("MAX_PUBLISH_TIMES_PER_ACCOUNT", 5)))

# 调度器最大并发线程数
SCHEDULER_MAX_WORKERS = int(os.getenv("SCHEDULER_MAX_WORKERS", _config.get("SCHEDULER_MAX_WORKERS", 10)))

# ftp的根目录
# 处理相对路径
_ftp_root_raw = os.getenv("FTP_ROOT_DIR", _config.get("FTP_ROOT_DIR", os.path.join(_current_dir, "ftp")))
if not os.path.isabs(_ftp_root_raw):
    FTP_ROOT_DIR = os.path.abspath(os.path.join(_current_dir, _ftp_root_raw))
else:
    FTP_ROOT_DIR = _ftp_root_raw

# FTP下的子目录
SUBDIRS = _config.get("SUBDIRS", "")

