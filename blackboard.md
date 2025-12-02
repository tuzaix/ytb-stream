
# yt的个人页视频tab
https://www.youtube.com/@DIYTechTrends/videos --> https://www.youtube.com/@{yourchannel}/videos

# yt 的个人页shorts tab
https://www.youtube.com/@24tubelight/shorts --> https://www.youtube.com/@{yourchannel}/shorts


# youtube stream downloader prompt

```
在 {} 目录下创建一个ytb_download_client.py模块，使用python的yt-dlp库，用于下载ytb视频，支持视频和shorts下载，
模块需要实现以下功能：
1. 批量下载，根据传入的个人页id，提取该个人页的视频tab和shorts tab中的视频链接
    1. 从ytb的个人页视频tab和shorts tab中提取视频链接
    2. 下载视频到指定目录，视频文件名格式为：{视频标题}.{视频格式}
    3. 支持批量下载视频，并且支持断点下载，对于已经下载过的视频，不会重复下载
2. 支持指定视频的链接，单独下载该视频
    1. 从传入的视频链接中提取视频id
    2. 下载该视频到指定目录，视频文件名格式为：{视频标题}.{视频格式}
```
