#!/bin/bash
#
#卤味直播

bin=`dirname "$0"`
bin=`cd $bin; pwd`

title="🔴 LIVE 🔴 chinese delicious street food|中國美味街頭美食|美味しい中華屋台料理"
description="#chinesefood #streetfood #delicious #deliciousfood #美食 #グルメ"



timescope=$1
duration=$2
thedate=$3


bash $bin/../start-broadcast.sh "TasteofChinaStreets" "$title" "$timescope" "$duration" "$thedate" "$description"










