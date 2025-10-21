#!/bin/bash

# 麻将直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

title="🔴 LIVE 🔴 血戰到底！挑戰八方牌友，今夜決勝負！"

timescope=$1
duration=$2
thedate=$3

bash $bin/../start-broadcast.sh "majiang" "$title" "$timescope" "$duration" "$thedate"











