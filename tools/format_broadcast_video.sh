#!/bin/bash

# 脚本名称: organize_videos.sh
# 描述: 遍历指定目录下的mp4和ts文件，按给定日期依次创建编号目录（01, 02, 03...），
#       并将视频文件逐一移动到这些新目录中（每目录一个文件）。

# --- 1. 参数检查和变量设置 ---

if [ "$#" -ne 2 ]; then
    echo "使用方法: $0 <视频根目录> <起始日期>"
    echo "示例: $0 /path/to/videos 2025-10-11"
    exit 1
fi

VIDEO_ROOT_DIR="$1"
START_DATE="$2"

# 检查目录是否存在
if [ ! -d "$VIDEO_ROOT_DIR" ]; then
    echo "错误: 目录 '$VIDEO_ROOT_DIR' 不存在。"
    exit 1
fi

# 检查日期格式 (简单检查，例如 YYYY-MM-DD)
if ! [[ "$START_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "错误: 日期格式 '$START_DATE' 不正确。请使用 YYYY-MM-DD 格式。"
    exit 1
fi

# --- 2. 查找并安全地存储视频文件路径到数组 ---

# 使用 find -print0 和 while read -d '' 安全地处理包含空格的文件名
# 查找根目录下（-maxdepth 1）所有 .mp4 和 .ts 文件
VIDEO_FILES=()
find "$VIDEO_ROOT_DIR" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.ts" \) -print0 | 
while IFS= read -r -d '' filepath; do
    # 将文件路径安全地添加到数组中
    VIDEO_FILES+=("$filepath")
done

if [ ${#VIDEO_FILES[@]} -eq 0 ]; then
    echo "未在目录 '$VIDEO_ROOT_DIR' 下找到 .mp4 或 .ts 文件。"
    exit 0
fi

echo "找到 ${#VIDEO_FILES[@]} 个视频文件，开始组织..."

# --- 3. 遍历文件，创建目录并移动 ---

# 初始化一个计数器，用于生成目录编号 (01, 02, 03...)
COUNTER=1

# 初始化日期变量，用于日期递增
CURRENT_DATE="$START_DATE"

for VIDEO_FILE_PATH in "${VIDEO_FILES[@]}"; do
    
    # 获取文件名（不包含路径）
    FILE_NAME=$(basename "$VIDEO_FILE_PATH")

    # 构造目标目录名称
    # 格式：YYYY-MM-DD-NN (其中 NN 是两位数字编号)
    DIR_NUMBER=$(printf "%02d" "$COUNTER")
    TARGET_DIR_NAME="${CURRENT_DATE}-${DIR_NUMBER}"
    
    # 构造目标目录完整路径
    TARGET_DIR_FULL_PATH="${VIDEO_ROOT_DIR}/${TARGET_DIR_NAME}"

    # 创建目标目录
    if [ ! -d "$TARGET_DIR_FULL_PATH" ]; then
        echo "创建目录: $TARGET_DIR_FULL_PATH"
        mkdir -p "$TARGET_DIR_FULL_PATH"
        if [ $? -ne 0 ]; then
            echo "错误: 无法创建目录 $TARGET_DIR_FULL_PATH。停止操作。"
            exit 1
        fi
    fi

    # 移动文件
    echo "  移动文件: $FILE_NAME -> $TARGET_DIR_NAME"
    mv "$VIDEO_FILE_PATH" "$TARGET_DIR_FULL_PATH/"
    
    # 检查移动是否成功
    if [ $? -ne 0 ]; then
        echo "警告: 移动文件 '$FILE_NAME' 失败。"
    fi
    
    # 递增计数器
    COUNTER=$((COUNTER + 1))
    
    # 每两个文件（即每完成 01 和 02 两个目录），日期递增一天，并重置计数器
    if [ "$DIR_NUMBER" -eq 2 ]; then
        # 使用 date 命令进行日期递增
        # 注意：不同系统（如 macOS/BSD 和 Linux）的 date 命令语法可能略有不同
        # 下面使用 GNU date (Linux 常见) 语法
        if command -v gdate &> /dev/null; then
            # 如果安装了 gdate (GNU date)，则使用它 (常见于 macOS)
            CURRENT_DATE=$(gdate -d "$CURRENT_DATE + 1 day" +%Y-%m-%d)
        elif command -v date &> /dev/null && [[ "$(uname)" == "Linux" ]]; then
            # 否则，如果是 Linux，使用标准 date
            CURRENT_DATE=$(date -d "$CURRENT_DATE + 1 day" +%Y-%m-%d)
        else
            echo "警告: 无法执行日期递增操作。请确保安装了 GNU date 或脚本运行在支持 -d 选项的 Linux 系统上。"
            # 如果无法递增，则继续使用当前日期
        fi
        
        COUNTER=1
        echo "--- 日期递增到: $CURRENT_DATE ---"
    fi
done

echo "组织和移动完成。"