# -*- coding: utf-8 -*-
"""安装日志记录器 - 将每次安装会话持久化到 logs/ 目录下的日志文件"""

import os
import time
import threading
from typing import List

from ..config import LOGS_DIR, APP_NAME, APP_VERSION


class InstallLogger:
    """安装会话日志记录器

    每次安装会话生成一个文件：logs/install_YYYYMMDD_HHMMSS.log
    文件包含：会话头（时间/路径/软件清单）、逐条日志（带时间戳）、
    结束摘要（结果统计/耗时/日志路径）。
    线程安全：通过锁保护写入，可从工作线程调用。
    """

    def __init__(self):
        self._file = None
        self._lock = threading.Lock()
        self._path = None
        self._start_time = None
        self._log_dir = LOGS_DIR

    @property
    def path(self) -> str:
        """当前日志文件路径（未开始时为 None）"""
        return self._path

    def start_session(self, install_path: str, packages: List) -> str:
        """开始新的日志会话，返回日志文件路径"""
        self._start_time = time.localtime()
        ts = time.strftime("%Y%m%d_%H%M%S", self._start_time)

        try:
            os.makedirs(self._log_dir, exist_ok=True)
        except Exception:
            # 日志目录创建失败不阻塞安装，回退到临时目录
            import tempfile
            self._log_dir = os.path.join(tempfile.gettempdir(), APP_NAME, "logs")
            try:
                os.makedirs(self._log_dir, exist_ok=True)
            except Exception:
                return ""

        self._path = os.path.join(self._log_dir, f"install_{ts}.log")

        header = [
            "=" * 56,
            f" {APP_NAME} v{APP_VERSION} 安装日志",
            f" 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', self._start_time)}",
            f" 安装路径: {install_path}",
            f" 软件数量: {len(packages)}",
            "-" * 56,
            " 待安装清单:",
        ]
        for pkg in packages:
            header.append(f"   - {pkg.name} ({pkg.filename})")
        header.append("=" * 56)
        header.append("")

        with self._lock:
            try:
                self._file = open(self._path, "w", encoding="utf-8")
                self._file.write("\n".join(header) + "\n")
                self._file.flush()
            except Exception:
                self._file = None
        return self._path

    def log(self, message: str) -> None:
        """写入一条带时间戳的日志"""
        if not self._file:
            return
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {message}"
        with self._lock:
            try:
                self._file.write(line + "\n")
                self._file.flush()
            except Exception:
                pass

    def finish(self, success: int, fail: int, skipped: int) -> None:
        """结束会话，写入统计摘要并关闭文件"""
        if not self._file:
            return
        end = time.localtime()
        try:
            elapsed = time.mktime(end) - time.mktime(self._start_time)
        except Exception:
            elapsed = 0
        mm, ss = divmod(int(elapsed), 60)
        hh, mm = divmod(mm, 60)
        dur = f"{hh}时{mm}分{ss}秒" if hh else (f"{mm}分{ss}秒" if mm else f"{ss}秒")

        footer = [
            "",
            "=" * 56,
            f" 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', end)}",
            f" 总耗时: {dur}",
            f" 结果: 成功 {success} | 失败 {fail} | 跳过 {skipped}",
            f" 日志文件: {self._path}",
            "=" * 56,
        ]
        with self._lock:
            try:
                self._file.write("\n".join(footer) + "\n")
                self._file.flush()
                self._file.close()
            except Exception:
                pass
            self._file = None
