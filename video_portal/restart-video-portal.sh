#!/bin/bash

# Video Portal 服务重启脚本
# 该脚本用于重启 Video Portal 的 Systemd 服务
# 必须以 root 权限或 sudo 执行

SERVICE_NAME="video-portal.service"

echo "正在检查权限..."
if [[ $EUID -ne 0 ]]; then
   echo "错误：此脚本必须以 root 权限运行。请使用 sudo 执行。"
   echo "示例: sudo ./restart-video-portal.sh"
   exit 1
fi

echo "正在重启 $SERVICE_NAME ..."
systemctl restart $SERVICE_NAME

if [ $? -eq 0 ]; then
    echo "服务重启指令已发送。"
    echo "正在检查服务状态..."
    sleep 2
    
    # 检查服务是否处于 active (running) 状态
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ 服务 $SERVICE_NAME 已成功启动并正在运行。"
        systemctl status $SERVICE_NAME --no-pager | grep "Active:"
    else
        echo "❌ 服务启动失败或未能正常运行。请检查日志："
        echo "sudo journalctl -u $SERVICE_NAME -n 20"
        exit 1
    fi
else
    echo "❌ 重启失败。请检查 Systemd 服务是否存在。"
    exit 1
fi

echo "完成。"
