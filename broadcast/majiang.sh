#!/bin/bash

# 麻将直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

start_broadcast=$bin/../start-broadcast.sh

category=$1
timescope=$2
duration=$3
thedate=$4

title="🔴 LIVE 🔴 血戰到底！挑戰八方牌友，今夜決勝負！"

bash $start_broadcast $category $title $timescope $duration $thedate














