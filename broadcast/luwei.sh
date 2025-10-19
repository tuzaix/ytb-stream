#!/bin/bash
#
#卤味直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

start_broadcast=$bin/../start-broadcast.sh

category=$1
timescope=$2
duration=$3
thedate=$4

title="🔴 LIVE 🔴 Simmering & Bubbling: ASMR Braising Process! So Satisfying & Mouthwatering."

bash $start_broadcast $category $title $timescope $duration $thedate














