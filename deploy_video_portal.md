# 创建目录：
mkdir /yourpath/service
cd /yourpath/service
# 克隆代码 
git clone https://github.com/tuzaix/ytb-stream.git

cd ytb-stream

# 更新子模块
git submodule init 
git submodule update
cd dev_tools
git pull origin master 

# 创建venv虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt

# 创建配置
cd /yourpath/service/ytb-stream/video_portal
cp settings.json.example settings.json

# 启动应用
cd /yourpath/service/ytb-stream/video_portal
/yourpath/service/ytb-stream/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000


# 配置nginx
```
server {
    # 443 HTTPS 反向代理
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name yourdomain;

    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 引入通用 SSL 证书配置
    include /etc/nginx/conf.d/common-ssl-params.conf;
}
```

# 重启nginx
nginx -t
sudo systemctl restart nginx

# 配置systemd服务
```
[Unit]
Description=Video Portal Backend Service
After=network.target vsftpd.service

[Service]
# 必须使用 root 用户，因为需要创建系统 FTP 账户
User=root
Group=root
WorkingDirectory=/root/work/service/ytb-stream/video_portal
ExecStart=/root/work/service/ytb-stream/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
# 失败自动重启
Restart=always
RestartSec=5

# 环境变量配置 (在此处修改密码等敏感信息)
# Environment="ADMIN_USERNAME=admin"
# Environment="ADMIN_PASSWORD=这里填写您的强密码"
# Environment="ACCESS_TOKEN=这里填写您的API令牌"

# 日志输出
StandardOutput=append:/var/log/video_portal.log
StandardError=append:/var/log/video_portal.error.log

[Install]
WantedBy=multi-user.target
```

# 启动服务
sudo systemctl enable video-portal.service
sudo systemctl start video-portal.service


