#!/bin/bash
bin=`dirname "$0"`
bin=`cd $bin; pwd`

source $bin/.venv/bin/activate

GROUP=$1
CHOICE=$2
TITLE=$3
DESCRIPTION=$4

if [ -z "$GROUP" ] || [ -z "$CHOICE" ] || [ -z "$TITLE" ] || [ -z "$DESCRIPTION" ]; then
    echo "错误：缺少必要参数."
    echo "用法：$0 <分组> <类别> <视频标题> <视频说明>"
    echo "示例：$0 beauty WokStar \"视频标题\" \"视频说明\""
    exit 1
fi

BASE_DIR=/home/ftp/${GROUP}/files

auth_base_dir=$BASE_DIR/auth2.0/$CHOICE
video_base_dir=$BASE_DIR/video/$CHOICE

OPTS_VIDEO_DIRS=()

while IFS= read -r -d '' sub_dir; do
    if [[ $sub_dir == $video_base_dir ]]; then
        continue
    fi  

    # 假设 $video_base_dir 已经设置
    if [[ "$sub_dir" == *_published ]]; then
        continue
    fi  
    echo "$sub_dir" # 建议打印时也加引号

    OPTS_VIDEO_DIRS+=("$sub_dir")
done < <(find "$video_base_dir" -maxdepth 1 -type d -print0)
#  ^              ^
#  | 告诉 while 从这里获取输入
#  | 使用进程替换 <(...) 来执行 find，并将 find 的输出重定向到 while 循环的标准输入

echo "video_dirs: ${OPTS_VIDEO_DIRS[@]}"

python $bin/upload_video.py --auth_dir $auth_base_dir \
                                --video_dirs "${OPTS_VIDEO_DIRS[@]}" \
                                --title "$TITLE" \
                                --description "$DESCRIPTION" \
                                --publish
