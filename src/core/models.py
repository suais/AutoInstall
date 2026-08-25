# -*- coding: utf-8 -*-
"""数据模型定义"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InstallStatus(Enum):
    """安装状态"""
    NOT_INSTALLED = "not_installed"   # 未安装
    INSTALLED = "installed"            # 已安装
    INSTALLING = "installing"         # 正在安装
    FAILED = "failed"                  # 安装失败
    SKIPPED = "skipped"                # 已跳过
    UNKNOWN = "unknown"                # 未知


@dataclass
class PackageInfo:
    """安装包信息"""
    filepath: str                      # 文件完整路径
    filename: str                      # 文件名
    ext: str                           # 扩展名 (.exe / .msi / .msix)
    size: int                          # 文件大小 (bytes)
    name: str                          # 显示名称 (从数据库或文件名推导)
    product_name: str = ""             # 产品名 (用于注册表匹配)
    registry_names: list = field(default_factory=list)  # 注册表候选名称列表 (多别名)
    version: str = ""                  # 版本号
    installer_type: str = ""           # 安装器类型
    silent_args: list = field(default_factory=list)  # 静默安装参数
    path_arg: Optional[str] = None     # 安装路径参数模板
    is_msix: bool = False              # 是否为 MSIX 包
    selected: bool = True              # 是否被选中
    status: InstallStatus = InstallStatus.NOT_INSTALLED
    installed_version: str = ""        # 已安装版本号
    install_log: str = ""             # 安装日志

    @property
    def status_text(self) -> str:
        """状态中文显示文本"""
        texts = {
            InstallStatus.NOT_INSTALLED: "未安装",
            InstallStatus.INSTALLED: "已安装",
            InstallStatus.INSTALLING: "安装中",
            InstallStatus.FAILED: "失败",
            InstallStatus.SKIPPED: "已跳过",
            InstallStatus.UNKNOWN: "未知",
        }
        return texts.get(self.status, "未知")

    @property
    def size_text(self) -> str:
        """文件大小可读文本"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.2f} GB"


@dataclass
class InstalledSoftware:
    """已安装软件信息"""
    name: str                          # 软件名称
    version: str = ""                  # 版本
    publisher: str = ""                # 发布者
    install_location: str = ""         # 安装路径
    uninstall_string: str = ""         # 卸载命令
    registry_key: str = ""             # 注册表键
