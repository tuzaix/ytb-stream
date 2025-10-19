#!/bin/bash
#
#卤味直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

title="🔴 LIVE 🔴 Simmering & Bubbling: ASMR Braising Process! So Satisfying & Mouthwatering."

timescope=$1
duration=$2
thedate=$3


bash $bin/../start-broadcast.sh "luwei" "$title" "$timescope" "$duration" "$thedate"










