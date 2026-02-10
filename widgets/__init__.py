"""Widget modules for Syronss's Media Downloader."""

from widgets.queue_item import QueueItem, QueueItemWidget
from widgets.video_preview import VideoPreviewFrame
from widgets.history_item import DownloadHistoryItem
from widgets.stats_panel import StatsPanel

__all__ = [
    "QueueItem",
    "QueueItemWidget",
    "VideoPreviewFrame",
    "DownloadHistoryItem",
    "StatsPanel",
]
