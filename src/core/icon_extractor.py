# -*- coding: utf-8 -*-
"""安装包图标提取器 - 从 exe/msi 文件提取嵌入的应用图标，带磁盘缓存"""

import os
import re
import hashlib
import logging

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QFileInfo
from PySide6.QtWidgets import QFileIconProvider

from ..config import BASE_DIR

logger = logging.getLogger(__name__)


class IconExtractor:
    """从安装包文件提取图标，带内存 + 磁盘二级缓存。

    QFileIconProvider 底层调用 Shell SHGetFileInfo，
    对 .exe 文件能取出 exe 内嵌的第一个图标资源。
    必须在主线程（QApplication 存在时）使用。
    """

    _provider: QFileIconProvider = None   # 单例，主线程惰性创建
    _instance: "IconExtractor" = None

    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(BASE_DIR, ".icon_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self._mem_cache: dict[str, QPixmap] = {}

    @classmethod
    def get_instance(cls) -> "IconExtractor":
        if cls._instance is None:
            cls._instance = IconExtractor()
        return cls._instance

    def get_icon(self, filepath: str, size: int = 32) -> QPixmap | None:
        """获取文件图标 (QPixmap)，提取失败返回 None。"""
        if not filepath or not os.path.isfile(filepath):
            return None

        key = f"{filepath}::{size}"
        if key in self._mem_cache:
            return self._mem_cache[key]

        # 磁盘缓存命中
        disk_path = self._disk_cache_path(filepath, size)
        pixmap = None
        if os.path.exists(disk_path):
            pm = QPixmap(disk_path)
            if not pm.isNull():
                pixmap = pm

        # 磁盘未命中 → 提取
        if pixmap is None:
            pixmap = self._extract(filepath, size)
            if pixmap is not None and not pixmap.isNull():
                try:
                    pixmap.save(disk_path, "PNG")
                except Exception as e:
                    logger.debug("图标缓存写入失败 %s: %s", disk_path, e)
            else:
                pixmap = None

        if pixmap is not None:
            self._mem_cache[key] = pixmap
        return pixmap

    def _extract(self, filepath: str, size: int) -> QPixmap | None:
        """用 QFileIconProvider 提取图标。"""
        try:
            if self._provider is None:
                self._provider = QFileIconProvider()
            icon = self._provider.icon(QFileInfo(filepath))
            if icon.isNull():
                return None
            pm = icon.pixmap(size, size)
            return pm if not pm.isNull() else None
        except Exception as e:
            logger.debug("图标提取失败 %s: %s", filepath, e)
            return None

    def _disk_cache_path(self, filepath: str, size: int) -> str:
        """生成磁盘缓存文件完整路径。"""
        try:
            st = os.stat(filepath)
            raw = f"{os.path.basename(filepath)}_{st.st_size}_{int(st.st_mtime)}_{size}"
        except OSError:
            raw = f"{os.path.basename(filepath)}_{size}_{hashlib.md5(filepath.encode('utf-8')).hexdigest()[:8]}"
        safe = re.sub(r"[^\w\-.]", "_", raw)
        return os.path.join(self.cache_dir, safe + ".png")
