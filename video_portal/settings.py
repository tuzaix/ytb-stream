import os

# 后台管理账号配置
# 建议在生产环境中通过环境变量覆盖默认值
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# API 访问令牌
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "fake-super-secret-token")
