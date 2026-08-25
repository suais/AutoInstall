# -*- coding: utf-8 -*-
"""安装进度对话框 - 显示安装过程和日志"""

import os
import subprocess
import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QTextEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal


class InstallProgressDialog(QDialog):
    """安装进度对话框"""

    cancel_requested = Signal()

    def __init__(self, total: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("正在安装")
        self.setFixedSize(580, 460)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._total = total
        self._current = 0
        self._done = False
        self._log_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        # 标题
        self.title_label = QLabel("正在安装软件")
        self.title_label.setObjectName("dialogTitle")
        layout.addWidget(self.title_label)

        # 进度信息
        info_layout = QHBoxLayout()
        self.info_label = QLabel(f"准备中... (0/{total})")
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 当前安装项
        self.current_label = QLabel("")
        self.current_label.setStyleSheet("color: #888; font-size: 12px; padding: 4px 0;")
        layout.addWidget(self.current_label)

        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logTextEdit")
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text, 1)

        # 日志文件提示（完成时显示）
        self.log_path_label = QLabel("")
        self.log_path_label.setStyleSheet("color: #888; font-size: 11px;")
        self.log_path_label.setWordWrap(True)
        self.log_path_label.hide()
        layout.addWidget(self.log_path_label)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.open_log_btn = QPushButton("打开日志文件夹")
        self.open_log_btn.hide()
        self.open_log_btn.clicked.connect(self._open_log_folder)
        btn_layout.addWidget(self.open_log_btn)
        self.cancel_button = QPushButton("取消安装")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.clicked.connect(self._on_cancel)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

    def _open_log_folder(self):
        """在资源管理器中打开日志文件所在目录（并选中日志文件）"""
        if not self._log_path:
            return
        path = self._log_path
        if sys.platform == "win32":
            try:
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
                return
            except Exception:
                pass
        # 兜底：打开所在目录
        try:
            dirname = os.path.dirname(path)
            if sys.platform == "win32":
                os.startfile(dirname)
            else:
                subprocess.Popen(["xdg-open", dirname])
        except Exception:
            pass

    def update_progress(self, current: int, total: int, name: str, percent: int):
        """更新进度"""
        self._current = current
        self.info_label.setText(f"正在安装 ({current}/{total})")
        self.progress_bar.setValue(percent)
        self.current_label.setText(f"当前: {name}")

    def append_log(self, message: str):
        """追加日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def set_done(self, success_count: int, fail_count: int, skipped: int = 0, log_path: str = None):
        """安装完成（或被取消）"""
        if skipped > 0 and success_count == 0 and fail_count == 0:
            self.title_label.setText("安装已取消")
        else:
            self.title_label.setText("安装完成")
        info = f"成功: {success_count}  失败: {fail_count}"
        if skipped:
            info += f"  跳过: {skipped}"
        self.info_label.setText(info)
        self.progress_bar.setValue(100)
        self.cancel_button.setText("关闭")
        self.cancel_button.setEnabled(True)
        self.current_label.setText("")
        self._done = True
        # 断开取消信号
        try:
            self.cancel_button.clicked.disconnect()
        except Exception:
            pass
        self.cancel_button.clicked.connect(self.accept)

        # 显示日志文件信息
        if log_path and os.path.exists(log_path):
            self._log_path = log_path
            self.log_path_label.setText(f"安装日志: {log_path}")
            self.log_path_label.show()
            self.open_log_btn.show()

    def closeEvent(self, event):
        """安装进行中点 X：视为取消请求，而不是直接关闭"""
        if self._done:
            event.accept()
        else:
            event.ignore()
            self._on_cancel()

    def _on_cancel(self):
        if self._done or not self.cancel_button.isEnabled():
            return
        self.cancel_button.setText("取消中...")
        self.cancel_button.setEnabled(False)
        self.cancel_requested.emit()
