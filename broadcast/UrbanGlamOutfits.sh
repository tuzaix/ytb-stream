#!/bin/bash
#
#卤味直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

title="🔴 LIVE 🔴 Trendy Chinese Street Fashion: Beautiful Girl Outfits & Styles 🔥🥀"
description="Trendy Chinese Street Fashion: Beautiful Girl Outfits & Styles 🔥🥀#shorts #viral #douyin #tiktok"


# # 参数
# CATEGORY=$1    # 类型：cook, tetris等
# THETITLE=$2    # 直播标题
# TIMESCOPE=$3  # 时间点：7:00~9:30(2.5h), 10:00~13:30(3.5h), 22:00~次1:30(3.5h), 次2:00~次3:30(2.5h)
# DURATION=$4    # 指定直播时长，默认是2.5h
# RUN_DATE=$5    # 指定天的素材: 2025-10-20
# DESCRIPTION=$6        # 直播说明

timescope=$1
duration=$2
thedate=$3


bash $bin/../start-broadcast.sh "UrbanGlamOutfits" "$title" "$timescope" "$duration" "$thedate" "$description"









