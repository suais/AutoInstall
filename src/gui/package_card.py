# -*- coding: utf-8 -*-
"""安装包卡片组件 - 列表中的单个安装包行"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QCheckBox, QFrame
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from ..core.models import PackageInfo, InstallStatus


class PackageCard(QWidget):
    """单个安装包的卡片组件"""

    toggled = Signal(str, bool)  # (filename, checked)

    def __init__(self, package: PackageInfo, icon: QPixmap = None, parent=None):
        super().__init__(parent)
        self.package = package
        self.setObjectName("packageCard")
        self.setFixedHeight(56)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(10)

        # 复选框
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(package.selected)
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        # 图标区：优先用提取到的真实图标，否则回退到文字占位符
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignCenter)
        if icon is not None and not icon.isNull():
            self.icon_label.setPixmap(
                icon.scaled(26, 26, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.icon_label.setStyleSheet("QLabel { background-color: transparent; border-radius: 6px; }")
        else:
            self.icon_label.setText(self._get_icon_text())
            self.icon_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    color: #666;
                }
            """)
        layout.addWidget(self.icon_label)

        # 名称和元信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name_text = package.name
        if package.version:
            name_text += f"  v{package.version}"
        self.name_label = QLabel(name_text)
        self.name_label.setObjectName("packageNameLabel")
        info_layout.addWidget(self.name_label)

        meta_parts = [package.size_text]
        if package.installer_type:
            meta_parts.append(package.installer_type)
        self.meta_label = QLabel("  ·  ".join(meta_parts))
        self.meta_label.setObjectName("packageMetaLabel")
        info_layout.addWidget(self.meta_label)

        layout.addLayout(info_layout, 1)

        # 状态标签
        self.status_label = QLabel(package.status_text)
        self.status_label.setObjectName("statusNotInstalled")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(22)
        layout.addWidget(self.status_label)

        self._update_style()

    def _get_icon_text(self) -> str:
        """根据安装包类型返回图标文字"""
        ext = self.package.ext.lower()
        if ext == ".msi":
            return "MSI"
        elif ext in (".msix", ".msixbundle"):
            return "MSX"
        elif "browser" in self.package.name.lower() or "chrome" in self.package.name.lower() or "firefox" in self.package.name.lower():
            return "WWW"
        elif any(k in self.package.name.lower() for k in ["code", "ide", "edit", "studio", "jetbrains", "sublime", "cursor"]):
            return "</>"
        elif any(k in self.package.name.lower() for k in ["git", "docker", "node", "python", "go ", "rust", "java", "conda"]):
            return "DEV"
        else:
            return "APP"

    def _on_toggled(self, checked: bool):
        self.package.selected = checked
        self._update_style()
        self.toggled.emit(self.package.filename, checked)

    def _update_style(self):
        """根据选中状态更新样式"""
        if self.checkbox.isChecked():
            self.setStyleSheet("QWidget#packageCard { background-color: #f0f4ff; border-bottom: 1px solid #e0e8ff; } QWidget#packageCard:hover { background-color: #e8efff; }")
        else:
            self.setStyleSheet("")

    def update_status(self):
        """更新状态显示"""
        status = self.package.status
        self.status_label.setText(self.package.status_text)

        # 状态颜色映射
        status_styles = {
            InstallStatus.NOT_INSTALLED: ("statusNotInstalled", False),
            InstallStatus.INSTALLED: ("statusInstalled", True),
            InstallStatus.INSTALLING: ("statusInstalling", False),
            InstallStatus.FAILED: ("statusFailed", False),
            InstallStatus.SKIPPED: ("statusSkipped", False),
            InstallStatus.UNKNOWN: ("statusNotInstalled", False),
        }

        obj_name, disable = status_styles.get(status, ("statusNotInstalled", False))
        self.status_label.setObjectName(obj_name)
        # 强制刷新样式
        self.status_label.setStyle(self.status_label.style())

        # 已安装的禁用复选框
        if status == InstallStatus.INSTALLED:
            self.checkbox.setEnabled(False)
            self.checkbox.setChecked(False)

        # 更新名称（如果有已安装版本）
        name_text = self.package.name
        if self.package.version:
            name_text += f"  v{self.package.version}"
        if self.package.installed_version:
            name_text += f"  (已装 v{self.package.installed_version})"
        self.name_label.setText(name_text)
