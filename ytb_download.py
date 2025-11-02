import os
import sys
from typing import Optional, List, Dict

# 默认代理（当未显式提供 --proxy 时生效）
DEFAULT_PROXY = "127.0.0.1:7897"

try:
    # 引用封装好的下载客户端与工具函数
    from youtube.ytb_download_client import (
        YTBDownloadClient,
        YTDLPSettings,
        build_channel_tab_urls,
    )
except Exception as e:
    YTBDownloadClient = None  # type: ignore
    YTDLPSettings = None  # type: ignore
    build_channel_tab_urls = None  # type: ignore
    _import_error = e


def _ensure_imports():
    """检查依赖模块是否可用，否则抛出明确错误。

    此函数用于在运行期确保 youtube.ytb_download_client 的导入成功。
    """
    if YTBDownloadClient is None or YTDLPSettings is None or build_channel_tab_urls is None:
        raise RuntimeError(
            f"Failed to import youtube.ytb_download_client: {_import_error}"
        )


def _ensure_dir(path: str) -> None:
    """确保目录存在，不存在则创建。"""
    os.makedirs(path, exist_ok=True)


def _normalize_proxy_url(proxy: Optional[str]) -> Optional[str]:
    """规范化代理地址字符串，自动补全协议前缀。

    如果传入的代理不包含协议（如 "127.0.0.1:7897"），默认补全为 "http://"。
    支持的示例：
    - "http://127.0.0.1:7897"
    - "https://127.0.0.1:7897"
    - "socks5://127.0.0.1:7897"
    - "127.0.0.1:7897" -> "http://127.0.0.1:7897"
    """
    if not proxy:
        return None
    p = proxy.strip()
    if "://" not in p:
        return f"http://{p}"
    return p


def download_single_video(output_dir: str, video_url: str, settings: Optional[YTDLPSettings] = None) -> Optional[str]:
    """下载单个视频到指定输出目录。

    参数：
    - output_dir: 视频保存的根目录。
    - video_url: YouTube 视频链接。
    - settings: 可选的下载配置（格式、代理、Cookies 等）。

    返回：
    - 成功返回最终文件路径；失败返回 None。
    """
    _ensure_imports()
    _ensure_dir(output_dir)
    client = YTBDownloadClient(target_dir=output_dir, settings=settings)
    return client.download_video_by_url(video_url)


def download_channel(output_dir: str, channel_identifier: str, settings: Optional[YTDLPSettings] = None) -> Dict[str, List[str]]:
    """下载频道的 Videos 与 Shorts，分别保存至子目录。

    行为：
    - Videos 页下载到 `output_dir/videos`。
    - Shorts 页下载到 `output_dir/shorts`。

    参数：
    - output_dir: 根输出目录。
    - channel_identifier: 频道 ID/Handle/URL。
    - settings: 可选的下载配置。

    返回：
    - 字典：{"videos": [filepaths...], "shorts": [filepaths...]}
    """
    _ensure_imports()
    videos_tab, shorts_tab = build_channel_tab_urls(channel_identifier)

    # 分别创建两个子目录
    videos_dir = os.path.join(output_dir, channel_identifier, "videos")
    shorts_dir = os.path.join(output_dir, channel_identifier, "shorts")
    _ensure_dir(videos_dir)
    _ensure_dir(shorts_dir)

    # 分别为两个目录创建客户端，以便各自拥有独立的下载记录与文件命名空间
    videos_client = YTBDownloadClient(target_dir=videos_dir, settings=settings)
    shorts_client = YTBDownloadClient(target_dir=shorts_dir, settings=settings)

    # 列出每个 Tab 的 URL 列表
    v_urls = videos_client.list_video_urls_from_tab(videos_tab)
    s_urls = shorts_client.list_video_urls_from_tab(shorts_tab)

    # 执行下载
    v_files = videos_client.download_videos(v_urls)
    s_files = shorts_client.download_videos(s_urls)

    return {"videos": v_files, "shorts": s_files}


def main(argv: Optional[List[str]] = None) -> int:
    """命令行入口：根据参数执行单视频或频道下载。

    支持参数：
    - --output-dir 输出目录（必需）
    - --url 视频链接（可选，与 --channel 互斥）
    - --channel 频道 ID/Handle/URL（可选，与 --url 互斥）
    - --proxy 为所有请求设置统一代理（如 127.0.0.1:7897 或 http://127.0.0.1:7897；不写协议默认 http）
    - 默认代理：未提供 --proxy 时，使用 127.0.0.1:7897

    返回：
    - 进程退出码，0 表示成功，非 0 表示失败。
    """
    import argparse

    parser = argparse.ArgumentParser(description="YouTube downloader wrapper (single or channel)")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--url", required=False, help="YouTube 视频链接（与 --channel 互斥）")
    parser.add_argument("--channel", required=False, help="YouTube 频道 ID/Handle/URL（与 --url 互斥）")
    parser.add_argument("--proxy", required=False, help="统一代理（如 127.0.0.1:7897 或 http://127.0.0.1:7897；不写协议默认 http)")

    args = parser.parse_args(argv)

    output_dir: str = args.output_dir
    url: Optional[str] = args.url
    channel: Optional[str] = args.channel

    # 互斥校验
    if (url and channel) or (not url and not channel):
        print("错误：必须且只能提供 --url 或 --channel 其中之一。", file=sys.stderr)
        return 2

    try:
        # 先校验依赖导入，避免后续 NoneType 调用错误
        _ensure_imports()

        # 配置统一代理：若未提供 --proxy，则使用默认值
        raw_proxy: str = args.proxy if args.proxy else DEFAULT_PROXY
        proxy: Optional[str] = _normalize_proxy_url(raw_proxy)

        # 设置环境变量，确保 http/https 均使用统一代理
        if proxy:
            os.environ["HTTP_PROXY"] = proxy
            os.environ["http_proxy"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
            os.environ["https_proxy"] = proxy

        # 将代理与提取器参数传入设置：
        # - 默认强制使用 android 客户端，规避 SABR 与 nsig 警告
        # - 默认将视频转码为 mp4，提升兼容性
        settings = YTDLPSettings(
            proxy=proxy,
            extractor_args={"youtube": {"player_client": "android"}},
            no_warnings=True,
            recode_video="mp4",
            # 更保守的格式优先表达式（尽量选择 mp4/m4a），如需更激进可调整
            format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        )  # 可按需扩展更多命令行参数
        if url:
            fp = download_single_video(output_dir=output_dir, video_url=url, settings=settings)
            print("Downloaded:", fp)
        else:
            result = download_channel(output_dir=output_dir, channel_identifier=channel, settings=settings)  # type: ignore[arg-type]
            print("Downloaded videos:", len(result.get("videos", [])))
            print("Downloaded shorts:", len(result.get("shorts", [])))
        return 0
    except Exception as e:
        print(f"下载失败：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())