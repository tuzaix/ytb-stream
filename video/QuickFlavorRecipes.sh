#!/bin/bash
bin=`dirname "$0"`
bin=`cd $bin; pwd`

TITLE=$1
DESCRIPTION=$2

bash $bin/../start-video.sh "QuickFlavorRecipes" "$TITLE" "$DESCRIPTION"
