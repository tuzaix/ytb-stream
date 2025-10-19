#!/bin/bash

#俄罗斯方块直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

cd $bin/../

category=$1
timescope=$2
duration=$3
thedate=$4

title="🔴 LIVE 🔴 Let's see who the real Tetris master is!"

bash start-broadcast.sh $category $title $timescope $duration $thedate














