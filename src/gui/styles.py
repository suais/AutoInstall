# -*- coding: utf-8 -*-
"""QSS 样式表 - Vercel 风格极简黑白设计"""

STYLE_SHEET = """
/* ─── 全局 ─── */
QWidget {
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-size: 13px;
    color: #1a1a1a;
}

QMainWindow {
    background-color: #ffffff;
}

/* ─── 头部 ─── */
#header {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5e5;
}

#titleLabel {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
}

/* ─── 工具栏 ─── */
#toolbar {
    background-color: #fafafa;
    border-bottom: 1px solid #e5e5e5;
}

/* ─── 搜索框 ─── */
#searchInput {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px 10px 6px 28px;
    font-size: 13px;
    color: #333;
}

/* ─── 当前安装包路径 ─── */
#packagesPathLabel {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 0 10px;
    font-size: 12px;
    color: #666;
}

#searchInput:focus {
    border-color: #333;
}

#searchInput::placeholder {
    color: #aaa;
}

/* ─── 按钮 ─── */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    color: #333;
}

QPushButton:hover {
    background-color: #f5f5f5;
    border-color: #ccc;
}

QPushButton:pressed {
    background-color: #ebebeb;
}

QPushButton:disabled {
    color: #ccc;
    background-color: #f9f9f9;
}

/* 主按钮（安装按钮） */
#installButton {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #1a1a1a;
    font-weight: 600;
    padding: 8px 24px;
    border-radius: 6px;
}

#installButton:hover {
    background-color: #333;
    border-color: #333;
}

#installButton:pressed {
    background-color: #000;
}

#installButton:disabled {
    background-color: #e0e0e0;
    color: #999;
    border-color: #e0e0e0;
}

/* ─── 包列表区域 ─── */
#packageScrollArea {
    background-color: #ffffff;
    border: none;
}

#packageScrollArea > QWidget > #scrollContent {
    background-color: #ffffff;
}

QScrollBar:vertical {
    background-color: #f5f5f5;
    width: 10px;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #ccc;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #999;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    border: none;
}

QScrollBar:horizontal {
    height: 0;
    border: none;
}

/* ─── 包卡片 ─── */
#packageCard {
    background-color: #ffffff;
    border: none;
    border-bottom: 1px solid #f0f0f0;
    padding: 8px 12px;
}

#packageCard:hover {
    background-color: #fafafa;
}

#packageCardSelected {
    background-color: #f0f4ff;
    border-bottom: 1px solid #e0e8ff;
}

#packageNameLabel {
    font-size: 13px;
    font-weight: 500;
    color: #1a1a1a;
}

#packageMetaLabel {
    font-size: 11px;
    color: #888;
}

#packageStatusLabel {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
}

/* 状态颜色 */
#statusNotInstalled {
    color: #666;
    background-color: #f0f0f0;
}

#statusInstalled {
    color: #fff;
    background-color: #00875a;
}

#statusInstalling {
    color: #fff;
    background-color: #0052cc;
}

#statusFailed {
    color: #fff;
    background-color: #de350b;
}

#statusSkipped {
    color: #666;
    background-color: #eee;
}

/* ─── 底部栏 ─── */
#footer {
    background-color: #fafafa;
    border-top: 1px solid #e5e5e5;
}

#pathInput {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    color: #333;
}

#pathInput:focus {
    border-color: #333;
}

#browseButton {
    padding: 6px 12px;
}

/* ─── 进度条 ─── */
QProgressBar {
    background-color: #f0f0f0;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    font-size: 10px;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #1a1a1a;
    border-radius: 4px;
}

/* ─── 对话框 ─── */
QDialog {
    background-color: #ffffff;
}

#dialogTitle {
    font-size: 16px;
    font-weight: 600;
    color: #1a1a1a;
}

#logTextEdit {
    background-color: #1a1a1a;
    color: #c8c8c8;
    border: 1px solid #333;
    border-radius: 6px;
    font-family: "Consolas", "Cascadia Code", monospace;
    font-size: 12px;
    padding: 8px;
}

/* ─── 复选框 ─── */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #ccc;
    border-radius: 3px;
    background-color: #fff;
}

QCheckBox::indicator:hover {
    border-color: #999;
}

QCheckBox::indicator:checked {
    background-color: #1a1a1a;
    border-color: #1a1a1a;
    image: url(:/icons/check.png);
}

QCheckBox::indicator:checked:hover {
    background-color: #333;
    border-color: #333;
}

QCheckBox::indicator:checked:disabled {
    background-color: #e0e0e0;
    border-color: #ddd;
    image: url(:/icons/check.png);
}

/* ─── 分组框 ─── */
QGroupBox {
    border: 1px solid #e5e5e5;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    font-size: 12px;
    color: #666;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

/* ─── 统计标签 ─── */
#statsLabel {
    font-size: 12px;
    color: #888;
    padding: 4px 0;
}
"""
