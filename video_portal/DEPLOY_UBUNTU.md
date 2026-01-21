# Video Portal Ubuntu 部署手册

本手册将指导您如何在 Ubuntu 20.04/22.04 环境下部署 Video Portal 服务。

## 1. 环境准备

### 1.1 更新系统
首先确保系统软件包是最新的：
```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 安装基础软件
安装 Python 3、Git 和 FTP 服务 (vsftpd)：
```bash
sudo apt install -y python3 python3-pip python3-venv git vsftpd
```

### 1.3 启动 FTP 服务
确保 vsftpd 已启动并设置为开机自启：
```bash
sudo systemctl enable vsftpd
sudo systemctl start vsftpd
```

## 2. 获取代码与安装依赖

本服务依赖于项目根目录下的 `dev_tools` 脚本，因此需要克隆完整的 `ytb-stream` 仓库。
假设我们将项目部署在 `/opt/ytb-stream` 目录下。

### 2.1 克隆代码
```bash
cd /opt
# 请将 <Repo-URL> 替换为实际的 Git 仓库地址
sudo git clone <Repo-URL> ytb-stream
cd ytb-stream
```

### 2.2 创建 Python 虚拟环境
```bash
# 创建虚拟环境
sudo python3 -m venv venv

# 激活虚拟环境 (仅当前会话有效，Systemd 服务会直接引用路径)
source venv/bin/activate

# 安装项目依赖
sudo ./venv/bin/pip install -r video_portal/requirements.txt
```

## 3. 系统配置

### 3.1 赋予脚本执行权限
项目包含用于管理 FTP 用户的 Shell 脚本，必须赋予其执行权限：
```bash
sudo chmod +x dev_tools/vsftpd/*.sh
```

### 3.2 配置文件设置
您可以直接修改 `video_portal/settings.py`，或者在后续的 Systemd 配置中使用环境变量来覆盖默认值。

主要配置项：
- `ADMIN_USERNAME`: 后台登录用户名
- `ADMIN_PASSWORD`: 后台登录密码
- `ACCESS_TOKEN`: API 访问令牌

## 4. 配置 Systemd 服务

为了确保服务在后台运行并开机自启，我们需要创建一个 Systemd 服务文件。

**注意**：由于 FTP 账号创建脚本 (`create_ftpuser.sh`) 需要执行 `useradd` 等系统命令，**本服务必须以 root 权限运行**。

### 4.1 创建服务文件
使用编辑器创建 `/etc/systemd/system/video-portal.service`：

```bash
sudo nano /etc/systemd/system/video-portal.service
```

粘贴以下内容（请根据实际情况修改路径和密码）：

```ini
[Unit]
Description=Video Portal Backend Service
After=network.target vsftpd.service

[Service]
Type=simple
# 必须使用 root 用户，因为需要创建系统 FTP 账户
User=root
Group=root
WorkingDirectory=/opt/ytb-stream

# 启动命令
ExecStart=/opt/ytb-stream/venv/bin/uvicorn video_portal.main:app --host 0.0.0.0 --port 8000

# 失败自动重启
Restart=always
RestartSec=5

# 环境变量配置 (在此处修改密码等敏感信息)
Environment="ADMIN_USERNAME=admin"
Environment="ADMIN_PASSWORD=这里填写您的强密码"
Environment="ACCESS_TOKEN=这里填写您的API令牌"

# 日志输出
StandardOutput=append:/var/log/video_portal.log
StandardError=append:/var/log/video_portal.error.log

[Install]
WantedBy=multi-user.target
```

### 4.2 启动服务
```bash
# 重载配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable video-portal

# 启动服务
sudo systemctl start video-portal
```

### 4.3 查看状态与日志
查看服务运行状态：
```bash
sudo systemctl status video-portal
```

查看实时日志：
```bash
sudo tail -f /var/log/video_portal.log
```

## 5. 配置 Nginx 反向代理 (可选)

虽然 Uvicorn 可以直接提供服务，但在生产环境中，建议使用 Nginx 作为反向代理来处理端口转发、SSL 加密等。

### 5.1 安装 Nginx
```bash
sudo apt install -y nginx
```

### 5.2 配置站点
项目目录中已提供 Nginx 配置文件模板 `video_portal/video_portal.nginx.conf`。

1. 复制配置文件到 Nginx 目录：
```bash
sudo cp /opt/ytb-stream/video_portal/video_portal.nginx.conf /etc/nginx/sites-available/video-portal
```

2. 编辑配置文件，修改 `server_name` 为您的实际域名或 IP：
```bash
sudo nano /etc/nginx/sites-available/video-portal
```
将 `server_name example.com;` 修改为 `server_name <您的IP或域名>;`。

3. 启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/video-portal /etc/nginx/sites-enabled/
```

4. 检查配置并重启 Nginx：
```bash
sudo nginx -t
sudo systemctl restart nginx
```

现在，您可以通过 `http://<您的IP或域名>` (默认 80 端口) 访问服务，而无需在 URL 中添加 `:8000`。

## 6. 验证部署

1. 打开浏览器访问 `http://<服务器IP>:8000`。
2. 使用配置的账号密码登录。
3. 尝试创建一个测试账号，观察是否成功生成 FTP 信息，并验证 FTP 连接是否可用。

## 7. 常见问题排查

**Q: 创建账号时报错 "Permission denied"？**
A: 请检查 Systemd 服务是否配置为 `User=root`，因为非 root 用户无法执行 `useradd` 命令。

**Q: FTP 连接失败？**
A: 
1. 检查服务器防火墙是否放行了 21 端口及被动模式端口范围。
2. 检查 `vsftpd` 服务是否正常运行。
3. 检查云服务商的安全组设置。

**Q: 上传视频卡住？**
A: 检查服务器网络连接，特别是针对 YouTube API 的访问是否通畅。
