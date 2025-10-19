#!/bin/bash

#俄罗斯方块直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

title="🔴 LIVE 🔴 Let's see who the real Tetris master is!"

timescope=$1
duration=$2
thedate=$3


bash $bin/../start-broadcast.sh "tetris" "$title" "$timescope" "$duration" "$thedate"














