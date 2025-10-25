#!/bin/bash
bin=`dirname "$0"`
bin=`cd $bin; pwd`



# usage: upload_video.py [-h] --auth_dir AUTH_DIR --video_dirs VIDEO_DIRS [VIDEO_DIRS ...] --title TITLE --description DESCRIPTION [--privacy PRIVACY]
#                        [--thumbnail THUMBNAIL] [--publish] [--tags TAGS]

# Upload a video to YouTube.

# options:
#   -h, --help            show this help message and exit
#   --auth_dir AUTH_DIR   Directory containing client_secrets.json and token.json.
#   --video_dirs VIDEO_DIRS [VIDEO_DIRS ...]
#                         Directory containing video files.
#   --title TITLE         The title of the video.
#   --description DESCRIPTION
#                         The description of the video.
#   --privacy PRIVACY     The privacy status of the video (e.g., private, public, unlisted)
#   --thumbnail THUMBNAIL
#                         The path to the thumbnail image
#   --publish             Publish the video after processing
#   --tags TAGS           A comma-separated list of tags for the video


CHOICE=$1


BASE_DIR=/home/ftpuser_hostinger/files

auth_base_dir=$BASE_DIR/auth_impt/$CHOICE
video_base_dir=$BASE_DIR/video/$CHOICE


sub_dirs=$(ls $video_base_dir)
OPTS_VIDEO_DIRS=""

for sub_dir in $sub_dirs
do
    # 判断不是以_published未结尾的文件夹
    if [[ $sub_dir != *_published ]]; then
        OPTS_VIDEO_DIRS+="\"$video_base_dir/$sub_dir\" "
    fi
done

echo "$OPTS_VIDEO_DIRS"

