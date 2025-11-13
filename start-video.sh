#!/bin/bash
bin=`dirname "$0"`
bin=`cd $bin; pwd`

source $bin/.venv/bin/activate

ACCOUNT=$1

if [ -z "$ACCOUNT" ]; then
    echo "错误：缺少必要参数."
    echo "用法：$0 <账号>"
    echo "示例：$0 QuickSnackMasters"
    exit 1
fi

# 视频物料基础目录
BASE_DIR=/home/ftp/${ACCOUNT}

auth_dir=$BASE_DIR/auth2.0
video_dir=$BASE_DIR/video

OPTS_VIDEO_DIRS=()

while IFS= read -r -d '' sub_dir; do
    if [[ $sub_dir == $video_dir ]]; then
        continue
    fi  

    # 假设 $video_dir 已经设置
    if [[ "$sub_dir" == *_published ]]; then
        continue
    fi  
    echo "$sub_dir" # 建议打印时也加引号

    OPTS_VIDEO_DIRS+=("$sub_dir")
done < <(find "$video_dir" -maxdepth 1 -type d -print0)
#  ^              ^
#  | 告诉 while 从这里获取输入
#  | 使用进程替换 <(...) 来执行 find，并将 find 的输出重定向到 while 循环的标准输入

echo "video_dirs: ${OPTS_VIDEO_DIRS[@]}"

# 通过账号上传视频
python $bin/ytb_upload_video_by_account.py --auth_dir $auth_dir \
                                            --video_dirs "${OPTS_VIDEO_DIRS[@]}" \
                                            --account $ACCOUNT