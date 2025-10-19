#!/bin/bash
#
bin=`dirname "$0"`
bin=`cd $bin; pwd`

cd $bin
source .venv/bin/activate

LOG_DIR=/home/work/logs

# ytb api 验证文件目录，不同直播账号有不同的目录，跟视频文件一样的命名逻辑
base_auth_dir=/home/ftpuser_hostinger/files/auth_impt

# 视频流的目录
base_stream_dir=/home/ftpuser_hostinger/files/stream

# 参数
CATEGORY=$1    # 类型：cook, tetris等
THETITLE=$2    # 直播标题
TIMESCOPE=$3  # 时间点：7:00~9:30(2.5h), 10:00~13:30(3.5h), 22:00~次1:30(3.5h), 次2:00~次3:30(2.5h)
DURATION=$4    # 指定直播时长，默认是2.5h
RUN_DATE=$5    # 指定天的素材: 2025-10-20


# 必选参数
if [ -z "$CATEGORY" ] || [ -z "$THETITLE" ] || [ -z "$TIMESCOPE" ]; then
    echo "错误：缺少必要参数."
    echo "用法：$0 <类别> <标题> <直播时段:2/7/10/22> [直播时长：默认是2.5h] [直播时间:2025-10-20]"
    echo "示例：$0 cook "直播标题" 2 2.5 2025-10-20"
    exit 1
fi

# 可选参数, 直播时长，小时为单位
if [ -z "$DURATION" ]; then
    the_duration=2.5
else
	the_duration=$DURATION
fi

# 执行的天数
if [ -z "$RUN_DATE" ]; then
    thedate=$(date +%Y-%m-%d)
else
	# 检查日期格式 (使用正则表达式 YYYY-MM-DD)
    # 注意: 这个正则只能检查格式，不能验证日期是否合法 (如 2025-02-30)
    DATE_REGEX="^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    if [[ "$RUN_DATE" =~ $DATE_REGEX ]]; then
        thedate="$RUN_DATE"
    else
        echo "错误: 日期格式不正确。请使用 YYYY-MM-DD 格式 (例如: 2025-10-11)。"
        exit 1
    fi
fi


# 配置参数
the_auth_dir=$base_auth_dir/$CATEGORY
#the_video_file=
the_title=$THETITLE
#the_duration
#
log_file=$LOG_DIR/broadcast-$CATEGORY-$thedate-$TIMESCOPE.log

VIDEO_DIR=$base_stream_dir/$CATEGORY/$thedate-$TIMESCOPE

for file in "$VIDEO_DIR"/*.mp4 "$VIDEO_DIR"/*.ts; do
	# 检查文件是否存在（防止目录中没有文件时报错）
	if [ -f "$file" ]; then
	    echo ""
	    echo "*****************************************************"
	    echo ">>>> 正在推流文件: $file"
	    echo "*****************************************************"
        echo --auth_dir="$the_auth_dir" --video_file "$file" --title "$the_title" --duration "$the_duration" --privacy_status public
		python $bin/main.py --auth_dir="$the_auth_dir" --video_file "$file" --title "$the_title" --duration "$the_duration" --privacy_status public > $log_file 2>&1 
	    break
	fi
done

wait

