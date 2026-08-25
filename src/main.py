# -*- coding: utf-8 -*-
"""AutoInstall 主入口"""

import sys
import os
import logging

# 确保能导入 src 模块
if __name__ == "__main__" and not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

# 加载 Qt 资源（复选框对勾图标等）
import src.resources_rc  # noqa: F401

# 高 DPI 支持
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("AutoInstall")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AutoInstall")

    # 加载图标
    icon_path = os.path.join(
        getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "assets", "icon.ico"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 导入并创建主窗口
    from src.gui.main_window import MainWindow

    window = MainWindow()
    window.show()

    ret = app.exec()
    sys.exit(ret)


if __name__ == "__main__":
    main()
