# -*- coding: utf-8 -*-
"""配置文件：安装器类型识别、静默安装参数数据库、常量定义"""

import json
import os
import re
import sys

# ─── 路径常量 ──────────────────────────────────────────────
APP_NAME = "AutoInstall"
APP_VERSION = "1.0.0"

# PyInstaller 打包后，以 exe 所在目录为根目录
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PACKAGES_DIR = os.path.join(BASE_DIR, "Packages")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")
ICON_SVG = os.path.join(BASE_DIR, "assets", "icon.svg")

# 用户设置持久化文件（exe 同级 settings.json）
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")


def load_settings() -> dict:
    """读取 settings.json，失败返回空 dict"""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_settings(updates: dict):
    """合并写入 settings.json（读写失败静默忽略，不影响主流程）"""
    data = load_settings()
    data.update(updates)
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_packages_dir() -> str:
    """获取安装包文件夹：优先用户设置（且目录仍存在），否则回退默认 Packages"""
    custom = load_settings().get("packages_dir")
    if custom and os.path.isdir(custom):
        return custom
    return PACKAGES_DIR


def set_packages_dir(path: str):
    """保存用户指定的安装包文件夹"""
    save_settings({"packages_dir": path})

# 打包后资源路径（PyInstaller _MEIPASS）
if getattr(sys, "frozen", False):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = BASE_DIR

DEFAULT_INSTALL_PATH = r"C:\Program Files"

# ─── 安装器类型 ────────────────────────────────────────────
INSTALLER_MSI = "msi"
INSTALLER_NSIS = "nsis"
INSTALLER_INNO = "inno"
INSTALLER_SQUIRREL = "squirrel"
INSTALLER_INSTALLSHIELD = "installshield"
INSTALLER_WIX = "wix"
INSTALLER_ADVANCED = "advanced"   # Advanced Installer (Caphyon) EXE 引导器，底层 MSI
INSTALLER_CUSTOM = "custom"

# ─── 静默安装参数模板 ──────────────────────────────────────
# 每种安装器类型的默认静默参数
SILENT_ARGS = {
    INSTALLER_MSI: ["/quiet", "/norestart"],
    INSTALLER_NSIS: ["/S"],
    INSTALLER_INNO: ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
    INSTALLER_SQUIRREL: ["--silent"],
    INSTALLER_INSTALLSHIELD: ["/s", "/v/qn"],
    INSTALLER_WIX: ["-quiet", "-norestart"],
    # Advanced Installer EXE 引导器：/exenoui 隐藏引导器 UI，再透传 msiexec 参数
    # （官方推荐语法 setup.exe /exenoui /qn，实测 MindLine 验证通过）
    INSTALLER_ADVANCED: ["/exenoui", "/qn", "/norestart"],
    INSTALLER_CUSTOM: ["/S"],
}

# ─── 安装路径参数 ──────────────────────────────────────────
# 不同安装器传递安装路径的方式
PATH_ARG_TEMPLATES = {
    INSTALLER_MSI: 'INSTALLDIR="{path}"',          # msiexec 用
    INSTALLER_NSIS: '/D="{path}"',                  # NSIS 用
    INSTALLER_INNO: '/DIR="{path}"',                # Inno Setup 用
    INSTALLER_SQUIRREL: None,                       # Squirrel 不支持自定义路径
    INSTALLER_INSTALLSHIELD: None,
    INSTALLER_WIX: None,
    INSTALLER_ADVANCED: 'APPDIR="{path}"',         # Advanced Installer 默认目录属性
    INSTALLER_CUSTOM: None,
}

# ─── 已知安装包数据库 ──────────────────────────────────────
# 基于文件名模式匹配，提供产品名、注册表名、安装器类型、特殊参数
# key: 文件名正则模式 (不区分大小写)
INSTALLER_DB = {
    # ─── 通讯/社交 ───
    r"wechat": {
        "name": "微信 (WeChat)",
        "registry_names": ["WeChat", "微信"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"foxmail": {
        "name": "Foxmail",
        "registry_names": ["Foxmail"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"dingtalk|dingding": {
        "name": "钉钉 (DingTalk)",
        "registry_names": ["DingTalk", "钉钉"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"feishu|lark": {
        "name": "飞书 (Feishu)",
        "registry_names": ["Feishu", "飞书", "Lark"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"tencentmeeting|tencent.?meeting|wemeet|qqmeeting": {
        "name": "腾讯会议 (Tencent Meeting)",
        "registry_names": ["Tencent Meeting", "腾讯会议", "Wemeet"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 浏览器 ───
    r"chromesetup|chrome.*setup|chrome.*installer": {
        "name": "Google Chrome",
        "registry_names": ["Google Chrome"],
        "type": INSTALLER_CUSTOM,
        "args": ["/silent", "/install"],
        "path_arg": None,
    },
    r"firefox.*installer|firefox.*setup": {
        "name": "Mozilla Firefox",
        "registry_names": ["Mozilla Firefox"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 办公 ───
    r"kdocs|wps": {
        "name": "金山文档 (WPS)",
        "registry_names": ["WPS Office", "金山文档", "KDocs"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"lky_officetools|lky.*office": {
        "name": "LKY Office Tools",
        "registry_names": ["LKY Office Tools"],
        "type": INSTALLER_CUSTOM,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 开发工具 / IDE ───
    r"vscode|visual.?studio.?code": {
        "name": "Visual Studio Code",
        "registry_names": ["Microsoft Visual Studio Code"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART", "/MERGETASKS=!runcode"],
        "path_arg": "/DIR=\"{path}\"",
    },
    r"cursor": {
        "name": "Cursor",
        "registry_names": ["Cursor"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"qoder": {
        "name": "Qoder",
        "registry_names": ["Qoder"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"traecode|trae.?code": {
        "name": "Trae Code",
        "registry_names": ["Trae", "TraeCode"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"traework": {
        "name": "Trae Work",
        "registry_names": ["Trae Work"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"qwenwork": {
        "name": "Qwen Work",
        "registry_names": ["Qwen Work", "通义灵码"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"codebuddy": {
        "name": "CodeBuddy",
        "registry_names": ["CodeBuddy"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"workbuddy": {
        "name": "WorkBuddy",
        "registry_names": ["WorkBuddy"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"jetbrains.*toolbox": {
        "name": "JetBrains Toolbox",
        "registry_names": ["JetBrains Toolbox"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"sublime_text": {
        "name": "Sublime Text",
        "registry_names": ["Sublime Text"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART"],
        "path_arg": "/DIR=\"{path}\"",
    },
    r"zed.*x86_64": {
        "name": "Zed",
        "registry_names": ["Zed"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"kiro.*ide": {
        "name": "Kiro IDE",
        "registry_names": ["Kiro"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"joycode": {
        "name": "JoyCode",
        "registry_names": ["JoyCode"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"zcode": {
        "name": "ZCode",
        "registry_names": ["ZCode"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"opencode.*desktop": {
        "name": "OpenCode Desktop",
        "registry_names": ["OpenCode"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"minimax.?code": {
        "name": "MiniMax Code",
        "registry_names": ["MiniMax Code"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"dumate": {
        "name": "Dumate",
        "registry_names": ["Dumate"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"xterminal": {
        "name": "XTerminal",
        "registry_names": ["XTerminal"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"android.?studio": {
        "name": "Android Studio",
        "registry_names": ["Android Studio"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"warp.*setup": {
        "name": "Warp Terminal",
        "registry_names": ["Warp"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"alacritty": {
        "name": "Alacritty Terminal",
        "registry_names": ["Alacritty"],
        "type": INSTALLER_MSI,
        "args": ["/quiet", "/norestart"],
        "path_arg": 'INSTALLDIR="{path}"',
    },
    r"tabby.*setup": {
        "name": "Tabby Terminal",
        "registry_names": ["Tabby"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },

    # ─── 开发运行时 ───
    r"node-v\d": {
        "name": "Node.js",
        "registry_names": ["Node.js"],
        "type": INSTALLER_MSI,
        "args": ["/quiet", "/norestart", "ADDLOCAL=ALL"],
        "path_arg": 'INSTALLDIR="{path}"',
    },
    r"miniconda3": {
        "name": "Miniconda3",
        "registry_names": ["Miniconda3"],
        "type": INSTALLER_CUSTOM,
        "args": ["/InstallationType=JustMe", "/RegisterPython=1", "/S", "/D=C:\\Miniconda3"],
        "path_arg": None,
    },
    r"git-\d": {
        "name": "Git",
        "registry_names": ["Git"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART", "/NOCANCEL", "/SP-", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"],
        "path_arg": "/DIR=\"{path}\"",
    },
    r"rustup-init": {
        "name": "Rust (rustup)",
        "registry_names": ["Rust"],
        "type": INSTALLER_CUSTOM,
        "args": ["-y"],
        "path_arg": None,
    },
    r"go\d+\.\d+.*windows.*amd64": {
        "name": "Go (Golang)",
        "registry_names": ["Go Programming Language"],
        "type": INSTALLER_MSI,
        "args": ["/quiet", "/norestart"],
        "path_arg": None,
    },
    r"jdk-\d+.*windows": {
        "name": "Java JDK",
        "registry_names": ["Java(TM) SE Development Kit", "JDK"],
        "type": INSTALLER_CUSTOM,
        "args": ["/s"],
        "path_arg": None,
    },
    r"jre-\d": {
        "name": "Java JRE",
        "registry_names": ["Java 8", "Java(TM) SE Runtime Environment"],
        "type": INSTALLER_CUSTOM,
        "args": ["/s"],
        "path_arg": None,
    },
    r"python-manager": {
        "name": "Python Manager",
        "registry_names": ["Python"],
        "type": INSTALLER_CUSTOM,
        "args": ["--quiet"],
        "path_arg": None,
    },

    # ─── 数据库 ───
    r"mongodb.*windows.*signed": {
        "name": "MongoDB",
        "registry_names": ["MongoDB"],
        "type": INSTALLER_MSI,
        "args": ["/quiet", "/norestart", "ADDLOCAL=all"],
        "path_arg": 'INSTALLDIR="{path}"',
    },
    r"dbeaver.*windows": {
        "name": "DBeaver CE",
        "registry_names": ["DBeaver"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART"],
        "path_arg": "/DIR=\"{path}\"",
    },

    # ─── 容器/虚拟化 ───
    r"docker.*desktop.*installer": {
        "name": "Docker Desktop",
        "registry_names": ["Docker Desktop"],
        "type": INSTALLER_CUSTOM,
        "args": ["install", "--quiet", "--accept-license"],
        "path_arg": None,
    },

    # ─── 远程控制 ───
    r"todesk.*installer": {
        "name": "ToDesk",
        "registry_names": ["ToDesk"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"awesun": {
        "name": "向日葵远程控制 (AweSun)",
        "registry_names": ["AweSun", "向日葵"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"urbackup.*client": {
        "name": "UrBackup Client",
        "registry_names": ["UrBackup"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART"],
        "path_arg": "/DIR=\"{path}\"",
    },

    # ─── 网络工具 ───
    r"winscp.*setup": {
        "name": "WinSCP",
        "registry_names": ["WinSCP"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART"],
        "path_arg": "/DIR=\"{path}\"",
    },
    r"wireshark.*x64": {
        "name": "Wireshark",
        "registry_names": ["Wireshark"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        # NSIS 规范: /D= 必须是最后一个参数，且值不能加引号
        # （引擎保证 path_arg 拼接在命令行末尾）
        "path_arg": "/D={path}",
    },
    r"nmap-\d.*setup": {
        "name": "Nmap",
        "registry_names": ["Nmap"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 下载工具 ───
    r"xunlei.*xl\d|xunleiweb": {
        "name": "迅雷 (XunLei)",
        "registry_names": ["Thunder", "迅雷"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"baidunetdisk|baidu.*netdisk": {
        "name": "百度网盘 (BaiduNetdisk)",
        "registry_names": ["baiduNetdisk", "百度网盘"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 媒体 ───
    r"vlc-\d.*win32": {
        "name": "VLC Media Player",
        "registry_names": ["VLC media player"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"handbrake.*win.*gui": {
        "name": "HandBrake",
        "registry_names": ["HandBrake"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART"],
        "path_arg": "/DIR=\"{path}\"",
    },
    r"jianying": {
        "name": "剪映 (JianYing)",
        "registry_names": ["JianyingPro", "剪映"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 设计工具 ───
    r"figma.*setup": {
        "name": "Figma",
        "registry_names": ["Figma"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"mastergo": {
        "name": "MasterGo",
        "registry_names": ["MasterGo"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"pixso": {
        "name": "Pixso",
        "registry_names": ["Pixso"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"draw\.?io.*installer": {
        "name": "draw.io",
        "registry_names": ["draw.io"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"affinitycn": {
        "name": "Affinity (CN)",
        "registry_names": ["Affinity"],
        "type": INSTALLER_CUSTOM,
        "args": ["--quiet"],
        "path_arg": None,
    },

    # ─── AI 工具 ───
    r"kimi_\d": {
        "name": "Kimi",
        "registry_names": ["Kimi"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"doubao_client|doubao.*client": {
        "name": "豆包 (Doubao)",
        "registry_names": ["Doubao", "豆包"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"ollama.*setup": {
        "name": "Ollama",
        "registry_names": ["Ollama"],
        "type": INSTALLER_CUSTOM,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"lm-studio": {
        "name": "LM Studio",
        "registry_names": ["LM Studio"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"bionic": {
        "name": "Bionic",
        "registry_names": ["Bionic"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"cherry.?studio": {
        "name": "Cherry Studio",
        "registry_names": ["Cherry Studio"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 效率工具 ───
    r"obsidian-\d": {
        "name": "Obsidian",
        "registry_names": ["Obsidian"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"notion-\d": {
        "name": "Notion",
        "registry_names": ["Notion"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"everything.*setup": {
        "name": "Everything",
        "registry_names": ["Everything"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"pdfgear.*setup": {
        "name": "pdfgear",
        "registry_names": ["pdfgear"],
        "type": INSTALLER_INNO,
        "args": ["/VERYSILENT", "/NORESTART"],
        "path_arg": "/DIR=\"{path}\"",
    },
    r"mindline.*setup": {
        "name": "MindLine",
        "registry_names": ["MindLine", "MindLine思维导图"],
        # 实测 MindLineSetup-x64-5.1.8.exe 是 Advanced Installer 引导器
        # （含 AI_INST_MAJORUPGRADE / advancedinstaller.com 签名），
        # 不认 Inno 的 /VERYSILENT，会弹 "Invalid command line"
        "type": INSTALLER_ADVANCED,
        "args": ["/exenoui", "/qn", "/norestart"],
        "path_arg": "APPDIR=\"{path}\"",
    },
    r"imageglass": {
        "name": "ImageGlass",
        "registry_names": ["ImageGlass"],
        "type": INSTALLER_CUSTOM,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"nutstore|坚果云": {
        "name": "坚果云 (Nutstore)",
        "registry_names": ["Nutstore", "坚果云"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"uuyc": {
        "name": "UUYC",
        "registry_names": ["UUYC"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
    r"desktopappinstaller": {
        "name": "Microsoft App Installer",
        "registry_names": ["App Installer"],
        "type": INSTALLER_CUSTOM,
        "args": ["--quiet"],
        "path_arg": None,
    },

    # ─── API 工具 ───
    r"postman.*x64": {
        "name": "Postman",
        "registry_names": ["Postman"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"eolink.*apikit": {
        "name": "Eolink Apikit",
        "registry_names": ["Apikit", "Eolink"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },

    # ─── 其他 ───
    r"github.*desktop.*setup": {
        "name": "GitHub Desktop",
        "registry_names": ["GitHub Desktop"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"sourcetree.*setup": {
        "name": "Sourcetree",
        "registry_names": ["Sourcetree"],
        "type": INSTALLER_SQUIRREL,
        "args": ["--silent"],
        "path_arg": None,
    },
    r"omap.*x64.*setup": {
        "name": "Omap",
        "registry_names": ["Omap"],
        "type": INSTALLER_NSIS,
        "args": ["/S"],
        "path_arg": None,
    },
}


def match_installer(filename: str) -> dict:
    """通过文件名匹配安装器数据库，返回匹配的配置字典。
    如果没有匹配，返回 None。
    """
    lower = filename.lower()
    for pattern, config in INSTALLER_DB.items():
        if re.search(pattern, lower):
            return config
    return None


def detect_installer_type(filepath: str) -> str:
    """通过读取二进制文件内容检测安装器类型（仅用于未知 exe 的兜底检测）"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".msi":
        return INSTALLER_MSI
    if ext in (".msix", ".msixbundle"):
        return INSTALLER_CUSTOM

    sniffed = sniff_installer_signature(filepath)
    return sniffed or INSTALLER_CUSTOM


# 嗅探窗口：安装器引导器（stub）位于文件头部，但部分引导器（如
# Advanced Installer）的签名在 2.4MB+ 偏移处，取 12MB 足够覆盖
_SNIFF_WINDOW = 12 * 1024 * 1024

# 二进制特征签名：安装器类型 -> [(特征字节, 是否强签名)]
# 强签名才允许推翻文件名数据库的判断；弱签名（如 squirrel 可能出现在
# 应用资源里）仅用于未知包的兜底检测
_SIGNATURES = {
    INSTALLER_INNO: [
        (b"Inno Setup", True),
    ],
    INSTALLER_NSIS: [
        (b"Nullsoft", True),
    ],
    INSTALLER_ADVANCED: [
        ("Advanced Installer".encode("utf-16-le"), True),
        (b"advancedinstaller", True),          # advancedinstaller.com URL
        ("AI_INST_".encode("utf-16-le"), True),
    ],
    INSTALLER_INSTALLSHIELD: [
        (b"InstallShield", True),
    ],
    INSTALLER_WIX: [
        (b"wixburn", True),
    ],
    INSTALLER_SQUIRREL: [
        (b"Squirrel", False),
    ],
}


def sniff_installer_signature(filepath: str) -> str:
    """读取 exe 文件头部，返回识别到的安装器类型（无匹配返回 None）。

    多签名命中时取偏移最小者——最外层引导器的 stub 总在文件最前面，
    内嵌的子安装器（如 bootstrapper 里包的 MSI/NSIS 载荷）偏移靠后。
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read(_SNIFF_WINDOW)
    except Exception:
        return None

    best_type, best_offset, best_strong = None, -1, False
    for installer_type, sigs in _SIGNATURES.items():
        for sig, strong in sigs:
            idx = data.find(sig)
            if idx < 0:
                continue
            # 同偏移时强签名优先；更早偏移优先
            if (best_offset < 0 or idx < best_offset
                    or (idx == best_offset and strong and not best_strong)):
                best_type, best_offset, best_strong = installer_type, idx, strong
    return best_type


def sniff_installer_signature_strong(filepath: str) -> str:
    """同 sniff_installer_signature，但只返回强签名结果（用于校验数据库判断）"""
    try:
        with open(filepath, "rb") as f:
            data = f.read(_SNIFF_WINDOW)
    except Exception:
        return None

    best_type, best_offset = None, -1
    for installer_type, sigs in _SIGNATURES.items():
        for sig, strong in sigs:
            if not strong:
                continue
            idx = data.find(sig)
            if idx < 0:
                continue
            if best_offset < 0 or idx < best_offset:
                best_type, best_offset = installer_type, idx
    return best_type
