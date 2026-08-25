# -*- coding: utf-8 -*-
"""主窗口 - AutoInstall 应用主界面"""

import os
import sys
import logging
from typing import List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QScrollArea,
    QFileDialog, QFrame, QGroupBox, QApplication, QStatusBar
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QIcon, QFont

from ..core.models import PackageInfo, InstallStatus
from ..core.scanner import PackageScanner, InstalledScanner, check_package_installed
from ..core.installer import InstallerEngine
from ..core.install_logger import InstallLogger
from ..config import (
    APP_NAME, ICON_PATH,
    DEFAULT_INSTALL_PATH, BUNDLE_DIR, BASE_DIR,
    get_packages_dir, set_packages_dir
)
from .package_card import PackageCard
from .install_dialog import InstallProgressDialog
from .styles import STYLE_SHEET

logger = logging.getLogger(__name__)


class InstallWorker(QThread):
    """安装工作线程（后台执行安装，通过信号通知 UI）"""

    progress_signal = Signal(int, int, str, int)  # current, total, name, percent
    log_signal = Signal(str)                       # log message
    status_signal = Signal(str, str)               # filename, status_text
    finished_signal = Signal(int, int, int)        # success_count, fail_count, skipped_count

    def __init__(self, packages: List[PackageInfo], install_path: str):
        super().__init__()
        self.packages = packages
        self.engine = InstallerEngine(install_path=install_path)
        self._cancelled = False
        self.logger = InstallLogger()

    def cancel(self):
        """请求取消"""
        self._cancelled = True
        self.engine.cancel()

    def run(self):
        """执行安装"""
        success_count = 0
        fail_count = 0
        skipped_count = 0
        total = len(self.packages)

        # 创建安装日志文件（logs/install_时间戳.log）
        log_path = self.logger.start_session(
            install_path=self.engine.install_path,
            packages=self.packages,
        )
        self.log_signal.emit(f"日志文件: {log_path}")

        def _log(msg: str):
            """同时输出到 UI 和日志文件"""
            self.log_signal.emit(msg)
            self.logger.log(msg)

        for i, pkg in enumerate(self.packages):
            if self._cancelled:
                pkg.status = InstallStatus.SKIPPED
                skipped_count += 1
                self.status_signal.emit(pkg.filename, pkg.status_text)
                continue

            current = i + 1
            self.progress_signal.emit(current, total, pkg.name, 0)
            _log(f"\n{'='*50}")
            _log(f"[{current}/{total}] 开始安装: {pkg.name}")

            def on_progress(package, message, pct):
                self.progress_signal.emit(current, total, f"{package.name} - {message}", pct)
                if pct >= 100:
                    self.status_signal.emit(package.filename, package.status_text)

            def on_log(msg):
                _log(f"  {msg}")

            success = self.engine.install(pkg, on_progress=on_progress, on_log=on_log)
            self.status_signal.emit(pkg.filename, pkg.status_text)

            if success:
                success_count += 1
                _log(f"✓ {pkg.name} 安装成功")
            else:
                if pkg.status == InstallStatus.SKIPPED:
                    skipped_count += 1
                    _log(f"⊘ {pkg.name} 已跳过")
                else:
                    fail_count += 1
                    _log(f"✗ {pkg.name} 安装失败")

            self.progress_signal.emit(current, total, pkg.name, 100)

        # 写入日志摘要并关闭文件
        self.logger.finish(success_count, fail_count, skipped_count)
        self.finished_signal.emit(success_count, fail_count, skipped_count)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.packages: List[PackageInfo] = []
        self.cards: dict[str, PackageCard] = {}  # filename -> card
        self.worker: InstallWorker = None
        self.progress_dialog: InstallProgressDialog = None
        self.packages_dir = get_packages_dir()  # 支持用户手动指定

        self._setup_window()
        self._setup_ui()
        self._scan_and_display()

    def _setup_window(self):
        """窗口基本设置"""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(760, 640)
        self.resize(880, 720)

        # 加载图标
        icon_path = os.path.join(BUNDLE_DIR, "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        elif os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.setStyleSheet(STYLE_SHEET)

    def _setup_ui(self):
        """构建界面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─── 头部 ───
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(52)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(6)

        # 图标 + 标题
        icon_label = QLabel("AI")
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #fff;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
            }
        """)
        header_layout.addWidget(icon_label)

        title_label = QLabel(APP_NAME)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        layout.addWidget(header)

        # ─── 工具栏 ───
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(48)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 6, 16, 6)
        toolbar_layout.setSpacing(8)

        # 当前安装包路径（过长时中间省略，悬停显示完整路径）
        self.packages_path_label = QLabel()
        self.packages_path_label.setObjectName("packagesPathLabel")
        self.packages_path_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.packages_path_label.setFixedHeight(32)
        self.packages_path_label.setMaximumWidth(260)
        toolbar_layout.addWidget(self.packages_path_label)
        self._update_packages_path_label()

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("搜索安装包...")
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self._on_search)
        toolbar_layout.addWidget(self.search_input, 1)

        # 选择安装包文件夹
        self.folder_btn = QPushButton("选择文件夹")
        self.folder_btn.setFixedHeight(32)
        self.folder_btn.setToolTip(f"当前文件夹: {self.packages_dir}")
        self.folder_btn.clicked.connect(self._on_change_folder)
        toolbar_layout.addWidget(self.folder_btn)

        # 全选
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setFixedHeight(32)
        self.select_all_btn.clicked.connect(self._on_select_all)
        toolbar_layout.addWidget(self.select_all_btn)

        # 反选
        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.setFixedHeight(32)
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        toolbar_layout.addWidget(self.deselect_all_btn)

        # 刷新
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.clicked.connect(self._on_refresh)
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addWidget(toolbar)

        # ─── 统计栏 ───
        self.stats_label = QLabel("扫描中...")
        self.stats_label.setObjectName("statsLabel")
        self.stats_label.setContentsMargins(16, 4, 16, 4)
        layout.addWidget(self.stats_label)

        # ─── 包列表 ───
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("packageScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, 1)

        # ─── 底部 ───
        footer = QWidget()
        footer.setObjectName("footer")
        footer.setFixedHeight(64)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(8)

        path_label = QLabel("安装路径:")
        path_label.setStyleSheet("font-size: 12px; color: #666;")
        footer_layout.addWidget(path_label)

        self.path_input = QLineEdit(DEFAULT_INSTALL_PATH)
        self.path_input.setObjectName("pathInput")
        self.path_input.setFixedHeight(32)
        footer_layout.addWidget(self.path_input, 1)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setObjectName("browseButton")
        self.browse_btn.setFixedHeight(32)
        self.browse_btn.clicked.connect(self._on_browse)
        footer_layout.addWidget(self.browse_btn)

        self.install_btn = QPushButton("开始安装")
        self.install_btn.setObjectName("installButton")
        self.install_btn.setFixedHeight(36)
        self.install_btn.setFixedWidth(120)
        self.install_btn.clicked.connect(self._on_install)
        footer_layout.addWidget(self.install_btn)

        layout.addWidget(footer)

    def _scan_and_display(self):
        """扫描安装包和已安装软件，然后显示"""
        self.stats_label.setText("正在扫描安装包...")

        # 使用 QTimer 延迟执行，让 UI 先更新
        QTimer.singleShot(50, self._do_scan)

    def _do_scan(self):
        """实际执行扫描"""
        # 1. 扫描安装包文件夹
        scanner = PackageScanner()
        self.packages = scanner.scan(self.packages_dir)

        if not self.packages:
            self.stats_label.setText(f"未找到安装包 (当前文件夹: {self.packages_dir})")
            return

        # 2. 扫描已安装软件
        self.stats_label.setText(f"找到 {len(self.packages)} 个安装包，正在检查已安装软件...")
        QApplication.processEvents()

        installed_scanner = InstalledScanner()
        installed = installed_scanner.scan()

        # 3. 匹配已安装状态
        for pkg in self.packages:
            if check_package_installed(pkg, installed):
                pkg.status = InstallStatus.INSTALLED
                pkg.selected = False

        # 4. 显示
        self._display_packages()

        # 5. 更新统计
        total = len(self.packages)
        installed_count = sum(1 for p in self.packages if p.status == InstallStatus.INSTALLED)
        not_installed = total - installed_count
        selected_count = sum(1 for p in self.packages if p.selected)
        self.stats_label.setText(
            f"共 {total} 个安装包 | 已安装 {installed_count} | 未安装 {not_installed} | 已选 {selected_count}"
        )

    def _display_packages(self):
        """将安装包列表渲染为卡片"""
        # 清空旧卡片
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards.clear()

        # 图标提取器（主线程惰性创建 QFileIconProvider）
        from ..core.icon_extractor import IconExtractor
        icon_extractor = IconExtractor.get_instance()

        # 按状态排序：未安装在前
        sorted_pkgs = sorted(
            self.packages,
            key=lambda p: (p.status == InstallStatus.INSTALLED, p.name)
        )

        for pkg in sorted_pkgs:
            icon = icon_extractor.get_icon(pkg.filepath, 32)
            card = PackageCard(pkg, icon=icon)
            card.toggled.connect(self._on_card_toggled)
            # 插入到 stretch 之前
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)
            self.cards[pkg.filename] = card

    def _on_card_toggled(self, filename: str, checked: bool):
        """卡片选中状态变化"""
        card = self.cards.get(filename)
        if card:
            card.update_status()
        self._update_stats()

    def _update_stats(self):
        """更新统计栏"""
        total = len(self.packages)
        installed = sum(1 for p in self.packages if p.status == InstallStatus.INSTALLED)
        selected = sum(1 for p in self.packages if p.selected)
        self.stats_label.setText(
            f"共 {total} 个安装包 | 已安装 {installed} | 未安装 {total - installed} | 已选 {selected}"
        )

    def _on_search(self, text: str):
        """搜索过滤"""
        text_lower = text.lower().strip()
        for filename, card in self.cards.items():
            visible = not text_lower or text_lower in card.package.name.lower() or text_lower in filename.lower()
            card.setVisible(visible)

    def _on_select_all(self):
        """全选未安装的"""
        for pkg in self.packages:
            if pkg.status != InstallStatus.INSTALLED:
                pkg.selected = True
                card = self.cards.get(pkg.filename)
                if card:
                    card.checkbox.setChecked(True)
        self._update_stats()

    def _on_deselect_all(self):
        """取消全选"""
        for pkg in self.packages:
            if pkg.status != InstallStatus.INSTALLED:
                pkg.selected = False
                card = self.cards.get(pkg.filename)
                if card:
                    card.checkbox.setChecked(False)
        self._update_stats()

    def _on_refresh(self):
        """重新扫描"""
        self.search_input.clear()
        self._scan_and_display()

    def _on_change_folder(self):
        """手动指定安装包文件夹，保存并重新扫描"""
        start = self.packages_dir if os.path.isdir(self.packages_dir) else BASE_DIR
        path = QFileDialog.getExistingDirectory(self, "选择安装包文件夹", start)
        if not path:
            return

        self.packages_dir = path
        set_packages_dir(path)  # 持久化到 settings.json
        self._update_packages_path_label()
        self.folder_btn.setToolTip(f"当前文件夹: {path}")
        logger.info(f"切换安装包文件夹: {path}")

        self.search_input.clear()
        self._scan_and_display()

    def _update_packages_path_label(self):
        """更新工具栏路径显示（过长省略中间，悬停显示完整路径）"""
        path = self.packages_dir
        elided = self.packages_path_label.fontMetrics().elidedText(
            path, Qt.ElideMiddle, 236
        )
        self.packages_path_label.setText(elided)
        self.packages_path_label.setToolTip(f"当前安装包文件夹: {path}")

    def _on_browse(self):
        """浏览选择安装路径"""
        path = QFileDialog.getExistingDirectory(
            self, "选择安装路径", self.path_input.text()
        )
        if path:
            self.path_input.setText(path)

    def _on_install(self):
        """开始安装选中的软件"""
        selected = [p for p in self.packages if p.selected and p.status != InstallStatus.INSTALLED]

        if not selected:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "没有选中需要安装的软件")
            return

        # 确认安装
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "确认安装",
            f"将安装 {len(selected)} 个软件到:\n{self.path_input.text()}\n\n是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        # 创建工作线程
        install_path = self.path_input.text().strip() or DEFAULT_INSTALL_PATH
        self.worker = InstallWorker(selected, install_path)

        # 创建进度对话框
        self.progress_dialog = InstallProgressDialog(len(selected), self)
        self.progress_dialog.cancel_requested.connect(self.worker.cancel)

        # 连接信号
        self.worker.progress_signal.connect(self._on_install_progress)
        self.worker.log_signal.connect(self.progress_dialog.append_log)
        self.worker.status_signal.connect(self._on_install_status)
        self.worker.finished_signal.connect(self._on_install_finished)

        # 禁用安装按钮
        self.install_btn.setEnabled(False)
        self.install_btn.setText("安装中...")

        # 启动（线程结束后自动清理，避免"线程仍在运行时被销毁"）
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()
        self.progress_dialog.exec()

    def _on_install_progress(self, current: int, total: int, name: str, percent: int):
        """安装进度更新"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, name, percent)

    def _on_install_status(self, filename: str, status_text: str):
        """安装状态更新"""
        card = self.cards.get(filename)
        if card:
            card.update_status()
        self._update_stats()

    def _on_install_finished(self, success: int, fail: int, skipped: int = 0):
        """安装完成"""
        if self.progress_dialog:
            log_path = self.worker.logger.path if self.worker else None
            self.progress_dialog.set_done(success, fail, skipped, log_path)

        self.install_btn.setEnabled(True)
        self.install_btn.setText("开始安装")
