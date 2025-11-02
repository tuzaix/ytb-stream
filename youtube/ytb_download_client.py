from __future__ import annotations
import os
import re
from typing import List, Tuple, Optional, Dict, Any, Callable
from dataclasses import dataclass
import time
from datetime import datetime

try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None  # Will be checked at runtime


def _ensure_yt_dlp_available():
    """检查 yt-dlp 是否已安装。

    如果未安装则抛出异常，提示用户先在环境中安装依赖。
    """
    if YoutubeDL is None:
        raise RuntimeError("yt-dlp not installed. Please install with: pip install yt-dlp")


def _normalize_channel_identifier(identifier_or_url: str) -> str:
    """将传入的个人页标识或 URL 规范化为频道基地址。

    规则：
    - 若为完整 URL，则保留域名与路径基础部分（移除末尾 /videos 或 /shorts）。
    - 若以 'UC' 开头（典型频道 ID），拼接为 'https://www.youtube.com/channel/{id}'。
    - 若以 '@' 开头（频道 Handle），拼接为 'https://www.youtube.com/{handle}'。
    - 其他情况，直接当作自定义路径名：'https://www.youtube.com/{identifier}'.

    参数：
    - identifier_or_url: 频道 ID、Handle 或完整 URL。

    返回：
    - 频道基地址字符串，不含 tabs 后缀。
    """
    s = identifier_or_url.strip()
    if s.startswith("http://") or s.startswith("https://"):
        # 去除末尾 /videos 或 /shorts
        s = re.sub(r"/(videos|shorts)/?$", "", s)
        return s
    if s.startswith("UC"):
        return f"https://www.youtube.com/channel/{s}"
    if s.startswith("@"):
        return f"https://www.youtube.com/{s}"
    # 兜底：自定义路径名，如 'c/SomeName' 或其他
    return f"https://www.youtube.com/{s}"


def build_channel_tab_urls(identifier_or_url: str) -> Tuple[str, str]:
    """构造频道的 Videos 与 Shorts Tab URL。

    参数：
    - identifier_or_url: 频道 ID、Handle 或完整 URL。

    返回：
    - (videos_tab_url, shorts_tab_url)
    """
    base = _normalize_channel_identifier(identifier_or_url)
    return f"{base}/videos", f"{base}/shorts"


def _ensure_dir(path: str) -> None:
    """确保目录存在，不存在则创建。"""
    os.makedirs(path, exist_ok=True)


def list_video_urls_from_tab(tab_url: str, settings: Optional[YTDLPSettings] = None) -> List[str]:
    """从频道某个 Tab（videos 或 shorts）提取视频链接列表。

    使用 yt-dlp 的 `extract_info(download=False)` 来解析页面，并在需要时启用
    `extract_flat=True` 以加速元数据提取。返回包含 `watch?v=` 或 `/shorts/` 的条目 URL。

    参数：
    - tab_url: 频道 Tab 页面 URL。

    返回：
    - 视频链接列表。
    """
    _ensure_yt_dlp_available()
    urls: List[str] = []
    ydl_opts: Dict[str, Any] = {
        "ignoreerrors": True,
        "quiet": True,
        "extract_flat": True,  # 仅提取条目而不解析所有格式
    }
    if settings:
        if settings.proxy:
            ydl_opts["proxy"] = settings.proxy
        if settings.cookiefile:
            ydl_opts["cookiefile"] = settings.cookiefile
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(tab_url, download=False)
        if not info:
            return urls
        # playlist 下的 entries
        entries = info.get("entries") or []
        for e in entries:
            # 对 shorts / watch 两类链接进行支持
            url = e.get("url") or e.get("webpage_url")
            if not url:
                # 有的条目只有 id
                vid = e.get("id")
                if vid:
                    # 构造 watch 链接
                    url = f"https://www.youtube.com/watch?v={vid}"
            if url:
                urls.append(url)
    return urls


def list_channel_videos(identifier_or_url: str, settings: Optional[YTDLPSettings] = None,
                        from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[str]:
    """提取频道 Videos 与 Shorts 两个 Tab 的全部视频链接并去重。

    参数：
    - identifier_or_url: 频道 ID、Handle 或完整 URL。

    返回：
    - 视频链接列表（去重后）。
    """
    videos_tab, shorts_tab = build_channel_tab_urls(identifier_or_url)
    v_urls = list_video_urls_from_tab(videos_tab, settings=settings)
    s_urls = list_video_urls_from_tab(shorts_tab, settings=settings)
    # 去重保持顺序
    seen = set()
    merged: List[str] = []
    for u in v_urls + s_urls:
        if u not in seen:
            seen.add(u)
            merged.append(u)
    # 如果需要按日期过滤，则尝试解析各链接的 upload_date（YYYYMMDD），无则保留
    if from_date or to_date:
        _ensure_yt_dlp_available()
        filtered: List[str] = []
        with YoutubeDL({"quiet": True, "ignoreerrors": True, **({"proxy": settings.proxy} if settings and settings.proxy else {})}) as ydl:
            for u in merged:
                inf = ydl.extract_info(u, download=False)
                if not inf:
                    continue
                up = inf.get("upload_date")  # YYYYMMDD 字符串
                if not up:
                    # 如果没有日期信息，保留该条目
                    filtered.append(u)
                    continue
                if from_date and up < from_date:
                    continue
                if to_date and up > to_date:
                    continue
                filtered.append(u)
        return filtered
    return merged


def extract_video_id(url: str) -> Optional[str]:
    """从视频链接中提取视频 ID（支持 watch 与 shorts）。

    参数：
    - url: 视频链接。

    返回：
    - 视频 ID 或 None。
    """
    _ensure_yt_dlp_available()
    ydl_opts = {"quiet": True, "ignoreerrors": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            return None
        return info.get("id")


def _default_archive_path(target_dir: str) -> str:
    """返回下载记录文件路径，防重复下载。"""
    return os.path.join(target_dir, "download_archive.txt")


def download_video_by_url(url: str, target_dir: str, settings: Optional[YTDLPSettings] = None) -> Optional[str]:
    """向后兼容包装：使用类封装进行单个视频下载。"""
    raise RuntimeError("Deprecated API. Instantiate YTBDownloadClient and call download_video_by_url.")


def batch_download_channel(identifier_or_url: str, target_dir: str, max_downloads: Optional[int] = None,
                           settings: Optional[YTDLPSettings] = None,
                           from_date: Optional[str] = None,
                           to_date: Optional[str] = None) -> List[str]:
    """向后兼容包装：使用类封装进行批量下载。"""
    raise RuntimeError("Deprecated API. Instantiate YTBDownloadClient and call batch_download_channel.")


if __name__ == "__main__":
    # 简易演示：根据环境变量或默认值进行测试（可自行修改）
    import sys
    print("ytb_download_client ready. Use functions in this module from your scripts.")
    if len(sys.argv) >= 3 and sys.argv[1] == "single":
        url = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) >= 4 else os.path.join(os.getcwd(), "downloads")
        client = YTBDownloadClient(target_dir=target)
        fp = client.download_video_by_url(url)
        print("Downloaded:", fp)
    elif len(sys.argv) >= 3 and sys.argv[1] == "channel":
        ident = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) >= 4 else os.path.join(os.getcwd(), "downloads")
        client = YTBDownloadClient(target_dir=target)
        files = client.batch_download_channel(ident)
        print("Downloaded files:", files)
@dataclass
class YTDLPSettings:
    """下载配置选项。

    - format: 指定下载格式表达式，例如 'bestvideo*+bestaudio/best'；音频下载可用 'bestaudio/best'
    - audio_only: 仅下载音频（将启用音频后处理）
    - audio_format: 音频封装格式（如 'mp3', 'm4a', 'aac', 'opus'），仅在 audio_only=True 时使用
    - audio_quality: 音频质量（如 '192'），仅在 audio_only=True 时使用
    - proxy: 代理地址字符串，例如 'http://127.0.0.1:7890' 或 'socks5://127.0.0.1:1080'
    - cookiefile: Cookies 文件路径（用于需登录的视频）
    - ratelimit: 下载速率限制（字节/秒），例如 5*1024*1024 表示 5MB/s
    - sleep_interval: 下载条目之间的最小休眠秒数
    - max_sleep_interval: 下载条目之间的最大休眠秒数
    - quiet: 是否静默运行（减少输出），默认 True
    - max_retries: 每个 URL 的最大重试次数，默认 2
    - retry_sleep: 重试前的休眠秒数，默认 2.0
    - extractor_args: 提供给 yt-dlp 的 extractor_args（例如强制使用 android 客户端）
    - no_warnings: 是否忽略警告输出，默认 True
    - recode_video: 将下载后的视频转码为指定格式（如 'mp4'）
    - merge_output_format: 将合并输出封装为指定容器（如 'mp4'），不一定转码
    """
    format: str = "bestvideo*+bestaudio/best"
    audio_only: bool = False
    audio_format: Optional[str] = None
    audio_quality: Optional[str] = None
    proxy: Optional[str] = None
    cookiefile: Optional[str] = None
    ratelimit: Optional[int] = None
    sleep_interval: Optional[float] = None
    max_sleep_interval: Optional[float] = None
    quiet: bool = True
    max_retries: int = 2
    retry_sleep: float = 2.0
    extractor_args: Optional[Dict[str, Dict[str, Any]]] = None
    no_warnings: bool = True
    recode_video: Optional[str] = None
    merge_output_format: Optional[str] = None


def _build_ydl_opts(outtmpl: str, archive_path: str, settings: Optional[YTDLPSettings] = None, noplaylist: bool = False, progress_hooks: Optional[List[Callable[[Dict[str, Any]], None]]] = None) -> Dict[str, Any]:
    """根据设置生成 yt-dlp 选项字典。

    参数：
    - outtmpl: 输出文件名模板。
    - archive_path: 下载记录文件路径。
    - settings: YTDLPSettings 配置，用于控制格式、代理、Cookies 等。
    - noplaylist: 是否禁用播放列表（仅下载单个视频）。
    - progress_hooks: 进度回调列表（接收一个包含进度信息的字典）。
    """
    base: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "continuedl": True,
        "ignoreerrors": True,
        "nooverwrites": True,
        "download_archive": archive_path,
        "quiet": (settings.quiet if settings is not None else True),
    }
    if noplaylist:
        base["noplaylist"] = True
    if progress_hooks:
        base["progress_hooks"] = progress_hooks
    if settings:
        if settings.format:
            base["format"] = settings.format
        if settings.proxy:
            base["proxy"] = settings.proxy
        if settings.cookiefile:
            base["cookiefile"] = settings.cookiefile
        if settings.extractor_args:
            base["extractor_args"] = settings.extractor_args
        if settings.no_warnings:
            base["no_warnings"] = True
        # 视频容器/转码设置：当非仅音频下载时才应用
        if not (settings.audio_only):
            if settings.recode_video:
                base["recode_video"] = settings.recode_video
            elif settings.merge_output_format:
                base["merge_output_format"] = settings.merge_output_format
        if settings.ratelimit is not None:
            base["ratelimit"] = settings.ratelimit
        if settings.sleep_interval is not None:
            base["sleep_interval"] = settings.sleep_interval
        if settings.max_sleep_interval is not None:
            base["max_sleep_interval"] = settings.max_sleep_interval
        if settings.audio_only:
            # 设置只下载音频，并进行后处理提取为指定格式
            base["format"] = settings.format or "bestaudio/best"
            pp = {"key": "FFmpegExtractAudio"}
            if settings.audio_format:
                pp["preferredcodec"] = settings.audio_format
            if settings.audio_quality:
                pp["preferredquality"] = settings.audio_quality
            base.setdefault("postprocessors", []).append(pp)
    return base


class YTBDownloadClient:
    """YouTube 下载器客户端（封装版）。

    提供统一的类封装，用于：
    - 列出频道 Videos/Shorts Tab 的视频链接
    - 根据 URL 提取视频 ID
    - 下载单个视频，或批量下载频道视频

    优化：支持进度回调、文件名模板配置、代理与 Cookies 统一管理、日期范围筛选、断点续传与下载记录。
    """

    def __init__(
        self,
        target_dir: str,
        settings: Optional[YTDLPSettings] = None,
        file_naming_template: str = "%(title)s.%(ext)s",
        archive_filename: str = "download_archive.txt",
        progress_hooks: Optional[List[Callable[[Dict[str, Any]], None]]] = None,
    ) -> None:
        """初始化下载客户端。

        参数：
        - target_dir: 下载保存目录。
        - settings: 下载配置（格式、音频、代理、Cookies、速率限制等）。
        - file_naming_template: 文件名模板，默认 "%(title)s.%(ext)s"。
        - archive_filename: 下载记录文件名，默认 "download_archive.txt"。
        - progress_hooks: 可选的进度回调列表。
        """
        # 统一为绝对路径，避免后续路径拼接出现重复目录
        abs_target = os.path.abspath(target_dir)
        _ensure_dir(abs_target)
        self.target_dir = abs_target
        self.settings = settings or YTDLPSettings()
        self.file_naming_template = file_naming_template
        self.archive_filename = archive_filename
        self.progress_hooks = progress_hooks or []

    @property
    def archive_path(self) -> str:
        """返回下载记录文件完整路径。"""
        return os.path.join(self.target_dir, self.archive_filename)

    def set_settings(self, settings: YTDLPSettings) -> None:
        """更新下载配置。"""
        self.settings = settings

    def add_progress_hook(self, hook: Callable[[Dict[str, Any]], None]) -> None:
        """添加一个进度回调函数。"""
        self.progress_hooks.append(hook)

    def clear_progress_hooks(self) -> None:
        """清空所有进度回调函数。"""
        self.progress_hooks.clear()

    def _ydl_opts(self, noplaylist: bool = False, override_outtmpl: Optional[str] = None) -> Dict[str, Any]:
        """构建 yt-dlp 选项字典。"""
        outtmpl = os.path.join(self.target_dir, override_outtmpl or self.file_naming_template)
        return _build_ydl_opts(outtmpl, self.archive_path, settings=self.settings, noplaylist=noplaylist, progress_hooks=self.progress_hooks)

    def _format_publish_date(self, info: Dict[str, Any]) -> str:
        """提取并格式化发布时间为 YYYY-MM-DD。

        优先使用 info['upload_date'] (YYYYMMDD)，其次尝试 'release_timestamp'/'timestamp'（epoch秒）。
        当无法获取时，使用当前本地时间。
        """
        

        up: Optional[str] = info.get("upload_date")
        if isinstance(up, str) and len(up) == 8 and up.isdigit():
            return f"{up[0:4]}-{up[4:6]}-{up[6:8]}"
        ts: Optional[int] = None
        for key in ("release_timestamp", "timestamp"):
            val = info.get(key)
            if isinstance(val, (int, float)):
                ts = int(val)
                break
        if ts is not None:
            try:
                # 本地时间格式化
                return time.strftime("%Y-%m-%d", time.localtime(ts))
            except Exception:
                pass
        # 回退当前时间
        return datetime.now().strftime("%Y-%m-%d")

    def _format_publish_datetime(self, info: Dict[str, Any]) -> str:
        """提取并格式化发布时间为 YYYY年MM月DD日-HH时MM分SS秒（本地时间）。

        优先使用 'release_timestamp' 或 'timestamp'（epoch 秒）。
        若仅有 'upload_date'（YYYYMMDD），则日期取该值、时间取当前时间。
        若均不可用，则使用当前日期时间。
        """
        ts: Optional[int] = None
        for key in ("release_timestamp", "timestamp"):
            val = info.get(key)
            if isinstance(val, (int, float)):
                ts = int(val)
                break
        if ts is not None:
            try:
                return time.strftime(f"%Y-%m-%d-%H-%M-%S", time.localtime(ts))
            except Exception:
                pass
        up: Optional[str] = info.get("upload_date")
        if isinstance(up, str) and len(up) == 8 and up.isdigit():
            today_time = datetime.now().strftime("%H-%M-%S")
            return f"{up[0:4]}-{up[4:6]}-{up[6:8]}-{today_time}"
        return datetime.now().strftime(f"%Y-%m-%d-%H-%M-%S")

    def _safe_rename_with_date(self, filepath: Optional[str], info: Dict[str, Any]) -> Optional[str]:
        """在文件名前加上发布时间，避免覆盖，返回新路径。

        当 filepath 不存在或为 None 时直接返回 None。
        """
        if not filepath:
            return None
        try:
            # 规范为绝对路径，避免重复拼接目录
            filepath = os.path.abspath(filepath)
            if not os.path.exists(filepath):
                return filepath  # 若文件不存在，保持原样（有些后处理路径可能不同）
            date_str = self._format_publish_datetime(info)
            base = os.path.basename(filepath)
            stem, ext = os.path.splitext(base)
            new_stem = f"{date_str}-{stem}"
            candidate = os.path.join(self.target_dir, new_stem + ext)
            if candidate == filepath:
                return filepath
            if not os.path.exists(candidate):
                os.replace(filepath, candidate)
                return candidate
            # 若存在同名，则追加序号避免覆盖
            idx = 1
            while True:
                candidate_i = os.path.join(self.target_dir, f"{new_stem}-{idx}{ext}")
                if not os.path.exists(candidate_i):
                    os.replace(filepath, candidate_i)
                    return candidate_i
                idx += 1
        except Exception:
            # 重命名失败则返回原路径
            return filepath

    def _resolve_final_filepath(self, info: Dict[str, Any], ydl: Any) -> Optional[str]:
        """尽可能解析最终文件路径，兼容 requested_downloads 与后处理变更扩展名。"""
        fp: Optional[str] = None
        try:
            reqs = info.get("requested_downloads")
            if isinstance(reqs, list) and reqs:
                for item in reqs:
                    fp = item.get("_filename") or (ydl.prepare_filename(item) if hasattr(ydl, "prepare_filename") else None)
                    if fp:
                        break
            if not fp:
                fp = info.get("_filename") or (ydl.prepare_filename(info) if hasattr(ydl, "prepare_filename") else None)
            # 若开启了 recode_video，检查同名 mp4 是否存在；统一为绝对路径
            fp_abs = os.path.abspath(fp) if fp else fp
            if fp_abs and not os.path.exists(fp_abs) and (self.settings and self.settings.recode_video):
                stem, _ = os.path.splitext(fp_abs)
                mp4 = stem + ".mp4"
                if os.path.exists(mp4):
                    fp_abs = mp4
            return fp_abs or fp
        except Exception:
            return fp

    def list_video_urls_from_tab(self, tab_url: str) -> List[str]:
        """从频道某个 Tab（videos 或 shorts）提取视频链接列表。"""
        _ensure_yt_dlp_available()
        urls: List[str] = []
        ydl_opts: Dict[str, Any] = {
            "ignoreerrors": True,
            "quiet": self.settings.quiet,
            "extract_flat": True,
        }
        if self.settings.proxy:
            ydl_opts["proxy"] = self.settings.proxy
        if self.settings.cookiefile:
            ydl_opts["cookiefile"] = self.settings.cookiefile
        if self.settings.extractor_args:
            ydl_opts["extractor_args"] = self.settings.extractor_args
        if self.settings.no_warnings:
            ydl_opts["no_warnings"] = True
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(tab_url, download=False)
            if not info:
                return urls
            entries = info.get("entries") or []
            for e in entries:
                url = e.get("url") or e.get("webpage_url")
                if not url:
                    vid = e.get("id")
                    if vid:
                        url = f"https://www.youtube.com/watch?v={vid}"
                if url:
                    urls.append(url)
        return urls

    def list_channel_videos(self, identifier_or_url: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[str]:
        """提取频道 Videos 与 Shorts 两个 Tab 的全部视频链接并去重，支持日期筛选。"""
        videos_tab, shorts_tab = build_channel_tab_urls(identifier_or_url)
        v_urls = self.list_video_urls_from_tab(videos_tab)
        s_urls = self.list_video_urls_from_tab(shorts_tab)
        seen = set()
        merged: List[str] = []
        for u in v_urls + s_urls:
            if u not in seen:
                seen.add(u)
                merged.append(u)
        if from_date or to_date:
            _ensure_yt_dlp_available()
            filtered: List[str] = []
            base_opts: Dict[str, Any] = {"quiet": self.settings.quiet, "ignoreerrors": True}
            if self.settings.proxy:
                base_opts["proxy"] = self.settings.proxy
            if self.settings.cookiefile:
                base_opts["cookiefile"] = self.settings.cookiefile
            if self.settings.extractor_args:
                base_opts["extractor_args"] = self.settings.extractor_args
            if self.settings.no_warnings:
                base_opts["no_warnings"] = True
            with YoutubeDL(base_opts) as ydl:
                for u in merged:
                    inf = ydl.extract_info(u, download=False)
                    if not inf:
                        continue
                    up = inf.get("upload_date")
                    if not up:
                        filtered.append(u)
                        continue
                    if from_date and up < from_date:
                        continue
                    if to_date and up > to_date:
                        continue
                    filtered.append(u)
            return filtered
        return merged

    def extract_video_id(self, url: str) -> Optional[str]:
        """从视频链接中提取视频 ID（支持 watch 与 shorts）。"""
        _ensure_yt_dlp_available()
        ydl_opts: Dict[str, Any] = {"quiet": self.settings.quiet, "ignoreerrors": True}
        if self.settings.proxy:
            ydl_opts["proxy"] = self.settings.proxy
        if self.settings.cookiefile:
            ydl_opts["cookiefile"] = self.settings.cookiefile
        if self.settings.extractor_args:
            ydl_opts["extractor_args"] = self.settings.extractor_args
        if self.settings.no_warnings:
            ydl_opts["no_warnings"] = True
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            return info.get("id")

    def download_video_by_url(self, url: str) -> Optional[str]:
        """下载单个视频到 `target_dir`，文件名格式为：{标题}.{扩展名}。"""
        _ensure_yt_dlp_available()
        ydl_opts = self._ydl_opts(noplaylist=True)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None
            fp = self._resolve_final_filepath(info, ydl)
            # 加前缀：发布时间-标题
            return self._safe_rename_with_date(fp, info)

    def download_videos(self, urls: List[str], max_downloads: Optional[int] = None) -> List[str]:
        """下载给定 URL 列表，支持数量限制与失败重试。

        重试策略：每个 URL 按 `settings.max_retries` 次重试，重试间隔 `settings.retry_sleep` 秒。
        """
        _ensure_yt_dlp_available()
        selected = urls[:max_downloads] if max_downloads is not None else urls
        ydl_opts = self._ydl_opts()
        downloaded_files: List[str] = []
        with YoutubeDL(ydl_opts) as ydl:
            for u in selected:
                attempts = 0
                while True:
                    try:
                        info = ydl.extract_info(u, download=True)
                        if not info:
                            raise RuntimeError("Empty info returned")
                        fp = self._resolve_final_filepath(info, ydl)
                        fp2 = self._safe_rename_with_date(fp, info)
                        if fp2:
                            downloaded_files.append(fp2)
                            break
                        # 若未获取到文件名视为失败
                        raise RuntimeError("No filename in info")
                    except Exception:
                        attempts += 1
                        if attempts > (self.settings.max_retries or 0):
                            break
                        if self.settings.retry_sleep:
                            import time
                            time.sleep(self.settings.retry_sleep)
        return downloaded_files

    def batch_download_channel(self, identifier_or_url: str, max_downloads: Optional[int] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[str]:
        """批量下载个人页的 Videos 与 Shorts 两个 Tab 的视频，支持数量限制和日期筛选。"""
        urls = self.list_channel_videos(identifier_or_url, from_date=from_date, to_date=to_date)
        return self.download_videos(urls, max_downloads=max_downloads)