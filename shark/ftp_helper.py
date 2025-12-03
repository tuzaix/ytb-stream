import os
import secrets
import string
from ftplib import FTP, error_perm

# -------------------------- 配置常量 ---------------------------
FTP_BASE = "/home/ftp"
SHARED_GROUP = "ftp_shared_workgroup"
WORK_USER = "work"

def generate_password(length=12):
    """生成随机密码"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def get_create_ftp_user_script(username, password=None, quota_mb=0):
    """
    生成创建FTP用户的Shell脚本内容
    :param username: 用户名
    :param password: 密码 (如果为None，则自动生成)
    :param quota_mb: 磁盘配额大小(MB)，0表示不限制
    :return: (script_content, password)
    """
    if not password:
        password = generate_password()

    # 构造配额设置的脚本片段
    quota_script_part = ""
    if quota_mb > 0:
        # 转换为KB (setquota通常使用KB)
        quota_kb = int(quota_mb) * 1024
        soft_limit = quota_kb
        hard_limit = quota_kb
        
        quota_script_part = f"""
# 设置磁盘配额
setup_disk_quota() {{
    local username="$1"
    local soft_limit="{soft_limit}"
    local hard_limit="{hard_limit}"
    local user_dir="$FTP_BASE/$username"
    
    # 检查是否安装了quota工具
    if ! command -v setquota &> /dev/null; then
        echo "警告: 未找到 'setquota' 命令，正在尝试安装 'quota'..."
        apt-get update && apt-get install -y quota
    fi
    
    if ! command -v setquota &> /dev/null; then
        echo "错误: 无法安装或找到 'setquota' 命令，跳过配额设置。"
        return
    fi
    
    # 获取目录所在的文件系统挂载点
    # df -P 输出格式: Filesystem 1024-blocks Used Available Capacity Mounted on
    local mount_point=$(df -P "$user_dir" | tail -1 | awk '{{print $6}}')
    
    echo "正在为用户 $username 在 $mount_point 设置配额 (限制: {quota_mb}MB)..."
    
    # 设置配额: setquota -u <user> <block-soft> <block-hard> <inode-soft> <inode-hard> <mount-point>
    # 0表示不限制inode
    if setquota -u "$username" "$soft_limit" "$hard_limit" 0 0 "$mount_point"; then
        echo "配额设置成功。"
    else
        echo "错误: 配额设置失败。请确保:"
        echo "  1. 文件系统已在 /etc/fstab 中启用配额功能 (usrquota)。"
        echo "  2. 已重新挂载文件系统 (mount -o remount $mount_point)。"
        echo "  3. 已运行 quotacheck 初始化配额文件。"
        # 不退出，仅警告，以免影响用户创建的主流程
    fi
}}
"""

    script = f"""#!/bin/bash
set -e

# 变量定义
FTP_BASE="{FTP_BASE}"
SHARED_GROUP="{SHARED_GROUP}"
WORK_USER="{WORK_USER}"
NEW_USER="{username}"
NEW_PASS="{password}"

# -------------------------- 函数定义 ---------------------------

# 检查Root权限
check_root() {{
    if [[ $EUID -ne 0 ]]; then
        echo "错误：此脚本必须以 root 权限运行。"
        exit 1
    fi
}}

# 检查用户是否存在
check_user_existence() {{
    if id "$1" &>/dev/null; then
        echo "错误：用户 '$1' 已存在。"
        exit 1
    fi
}}

# 创建共享组
create_shared_group() {{
    if ! getent group "$SHARED_GROUP" > /dev/null; then
        groupadd "$SHARED_GROUP"
        echo "已创建共享用户组: $SHARED_GROUP"
    fi
    
    # 将work用户加入组
    if id "$WORK_USER" &>/dev/null; then
        usermod -aG "$SHARED_GROUP" "$WORK_USER"
    fi
}}

# 创建FTP用户
create_ftp_user() {{
    local username="$1"
    local password="$2"
    
    # 创建系统用户，指定家目录和nologin shell
    useradd -m -d "$FTP_BASE/$username" -s /sbin/nologin -G "$SHARED_GROUP" "$username"
    
    # 设置密码
    echo "$username:$password" | chpasswd
    echo "用户 $username 创建成功。"
}}

# 设置目录权限
setup_ftp_directory() {{
    local username="$1"
    local user_dir="$FTP_BASE/$username"
    local upload_dir="$user_dir/upload"
    
    # 确保上传目录存在
    mkdir -p "$upload_dir"
    
    # 1. 家目录权限 (Chroot安全要求: 所有者为root, 且用户不可写)
    chown root:root "$user_dir"
    chmod 755 "$user_dir"
    
    # 2. 上传目录权限 (用户实际读写目录)
    chown "$username:$SHARED_GROUP" "$upload_dir"
    chmod 770 "$upload_dir"
    
    echo "目录权限已设置:"
    echo "  - Home (Root):   $user_dir (755)"
    echo "  - Upload (User): $upload_dir (770)"
}}

{quota_script_part}

# -------------------------- 主执行 ---------------------------
check_root
check_user_existence "$NEW_USER"
create_shared_group
create_ftp_user "$NEW_USER" "$NEW_PASS"
setup_ftp_directory "$NEW_USER"
"""

    if quota_mb > 0:
        script += 'setup_disk_quota "$NEW_USER"\n'
    
    script += f'\necho "FTP用户创建完成: $NEW_USER"\n'
    return script, password

def get_delete_ftp_user_script(username):
    """
    生成删除FTP用户的Shell脚本内容
    :param username: 用户名
    :return: script_content
    """
    script = f"""#!/bin/bash
set -e

# 变量定义
FTP_BASE="{FTP_BASE}"
TARGET_USER="{username}"

# 检查Root权限
if [[ $EUID -ne 0 ]]; then
    echo "错误：此脚本必须以 root 权限运行。"
    exit 1
fi

# 检查用户是否存在
if ! id "$TARGET_USER" &>/dev/null; then
    echo "警告：用户 '$TARGET_USER' 不存在。"
    exit 0
fi

echo "正在删除用户: $TARGET_USER ..."

# 杀死用户的所有进程
pkill -u "$TARGET_USER" || true

# 删除用户及其家目录
# -r 选项会删除用户的家目录和邮件池
userdel -r "$TARGET_USER" || echo "Warning: userdel encountered an issue (possibly root-owned home dir)"

# 清理可能残留的目录
USER_DIR="$FTP_BASE/$TARGET_USER"
if [ -d "$USER_DIR" ]; then
    echo "清理残留目录: $USER_DIR"
    rm -rf "$USER_DIR"
fi

echo "用户 $TARGET_USER 已删除。"
"""
    return script

class FtpDirHelper:
    @staticmethod
    def create_nested_dirs(host, username, password, remote_path):
        """
        Recursively create directories on the FTP server.
        :param host: FTP server IP
        :param username: FTP username
        :param password: FTP password
        :param remote_path: The full path of the directory to be created
        """
        ftp = FTP()
        try:
            ftp.connect(host)
            ftp.login(username, password)
            
            dirs = [d for d in remote_path.split('/') if d]
            current_path = ""

            for d in dirs:
                current_path = f"{current_path}/{d}"
                try:
                    ftp.cwd(current_path)
                except error_perm:
                    try:
                        ftp.mkd(current_path)
                        ftp.cwd(current_path)
                        print(f"Created directory: {current_path}")
                    except error_perm as e:
                        print(f"Failed to create directory {current_path}: {e}")
                        return False
            return True
        except Exception as e:
            print(f"FTP Operation Failed: {e}")
            return False
        finally:
            try:
                ftp.quit()
            except:
                try:
                    ftp.close()
                except:
                    pass

if __name__ == "__main__":
    # 测试生成
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        user = sys.argv[2] if len(sys.argv) > 2 else "testuser"
        
        if action == "create":
            # 默认测试 1GB 配额
            quota = 1024 
            if len(sys.argv) > 3:
                quota = int(sys.argv[3])
            
            script, pwd = get_create_ftp_user_script(user, quota_mb=quota)
            print(f"# Generated Password: {pwd}")
            print(script)
        elif action == "delete":
            print(get_delete_ftp_user_script(user))
        else:
            print("Usage: python ftp_helper.py [create|delete] [username] [quota_mb]")
