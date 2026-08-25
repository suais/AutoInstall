# -*- coding: utf-8 -*-
"""扫描器：扫描 Packages 文件夹 + 扫描系统已安装软件"""

import os
import re
import ctypes
import struct
import winreg
from typing import List, Optional
from .models import PackageInfo, InstalledSoftware, InstallStatus
from ..config import (
    PACKAGES_DIR, match_installer, detect_installer_type,
    sniff_installer_signature_strong, SILENT_ARGS, PATH_ARG_TEMPLATES,
    INSTALLER_MSI, INSTALLER_CUSTOM,
)


class PackageScanner:
    """扫描 Packages 文件夹，收集安装包信息"""

    VALID_EXTS = {".exe", ".msi", ".msix", ".msixbundle"}

    def scan(self, packages_dir: str = None) -> List[PackageInfo]:
        """扫描指定文件夹，返回安装包信息列表"""
        packages_dir = packages_dir or PACKAGES_DIR
        if not os.path.isdir(packages_dir):
            return []

        results = []
        for filename in sorted(os.listdir(packages_dir)):
            filepath = os.path.join(packages_dir, filename)
            if not os.path.isfile(filepath):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.VALID_EXTS:
                continue

            pkg = self._build_package(filepath, filename, ext)
            results.append(pkg)

        return results

    def _build_package(self, filepath: str, filename: str, ext: str) -> PackageInfo:
        """构建单个安装包信息"""
        size = os.path.getsize(filepath)

        # 从数据库匹配
        db_match = match_installer(filename)
        if db_match:
            name = db_match["name"]
            registry_names = list(db_match.get("registry_names") or [])
            product_name = registry_names[0] if registry_names else ""
            installer_type = db_match["type"]
            silent_args = db_match.get("args", [])
            path_arg = db_match.get("path_arg")

            # ─── 二进制签名交叉校验 ───
            # 数据库按文件名猜测类型，可能出错（例：MindLine 文件名像 Inno，
            # 实为 Advanced Installer 引导器，收到 /VERYSILENT 弹 "Invalid
            # command line"）。强签名与数据库冲突时，以签名为准，并改用
            # 该类型的默认静默参数——数据库里的参数是按错误类型写的，不能再用
            if ext == ".exe" and installer_type != INSTALLER_CUSTOM:
                sniffed = sniff_installer_signature_strong(filepath)
                if sniffed and sniffed != installer_type:
                    installer_type = sniffed
                    silent_args = list(SILENT_ARGS.get(sniffed, ["/S"]))
                    path_arg = PATH_ARG_TEMPLATES.get(sniffed)
        else:
            # 数据库未匹配，尝试自动检测
            installer_type = detect_installer_type(filepath)
            name = self._derive_name_from_filename(filename)
            product_name = name
            registry_names = []
            silent_args = self._get_default_silent_args(installer_type)
            path_arg = None

        # 尝试从文件属性提取版本信息
        version = self._get_file_version(filepath)

        # 尝试从文件属性提取产品名
        file_product = self._get_file_product_name(filepath)
        if file_product and not db_match:
            name = file_product

        return PackageInfo(
            filepath=filepath,
            filename=filename,
            ext=ext,
            size=size,
            name=name,
            product_name=product_name or name,
            registry_names=registry_names,
            version=version,
            installer_type=installer_type,
            silent_args=silent_args,
            path_arg=path_arg,
            is_msix=ext in (".msix", ".msixbundle"),
        )

    def _derive_name_from_filename(self, filename: str) -> str:
        """从文件名推导可读的产品名"""
        name = os.path.splitext(filename)[0]
        # 去掉版本号
        name = re.sub(r"[_\-]v?\d+\.\d+.*$", "", name)
        # 去掉 setup/installer 后缀
        name = re.sub(r"[_\-\s]?(setup|installer|install|x64|x86|win|windows|user|stable)$", "", name, flags=re.IGNORECASE)
        # 替换分隔符为空格
        name = re.sub(r"[_\-]", " ", name)
        return name.strip().title()

    def _get_default_silent_args(self, installer_type: str) -> list:
        """根据安装器类型返回默认静默参数"""
        from ..config import SILENT_ARGS
        return SILENT_ARGS.get(installer_type, ["/S"])

    def _get_file_version(self, filepath: str) -> str:
        """使用 Windows API 获取文件版本"""
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
            if not size:
                return ""
            buf = ctypes.create_string_buffer(size)
            if not ctypes.windll.version.GetFileVersionInfoW(filepath, None, size, buf):
                return ""

            # 查询 VarFileInfo\Translation
            translation_ptr = ctypes.c_uint()
            translation_len = ctypes.c_uint()
            ret = ctypes.windll.version.VerQueryValueW(
                buf.raw, r"\VarFileInfo\Translation",
                ctypes.byref(translation_ptr), ctypes.byref(translation_len)
            )
            if not ret or translation_len.value < 4:
                return ""

            # 读取语言/代码页
            raw = ctypes.string_at(translation_ptr, min(translation_len.value, 4))
            if len(raw) < 4:
                return ""
            lang, codepage = struct.unpack("<HH", raw[:4])

            # 查询 FileVersion
            query = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\FileVersion"
            ptr = ctypes.c_wchar_p()
            length = ctypes.c_uint()
            ret = ctypes.windll.version.VerQueryValueW(
                buf.raw, query, ctypes.byref(ptr), ctypes.byref(length)
            )
            if ret and length.value > 0:
                return ptr.value
        except Exception:
            pass
        return ""

    def _get_file_product_name(self, filepath: str) -> str:
        """使用 Windows API 获取文件产品名"""
        try:
            size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
            if not size:
                return ""
            buf = ctypes.create_string_buffer(size)
            if not ctypes.windll.version.GetFileVersionInfoW(filepath, None, size, buf):
                return ""

            translation_ptr = ctypes.c_uint()
            translation_len = ctypes.c_uint()
            ret = ctypes.windll.version.VerQueryValueW(
                buf.raw, r"\VarFileInfo\Translation",
                ctypes.byref(translation_ptr), ctypes.byref(translation_len)
            )
            if not ret or translation_len.value < 4:
                return ""

            raw = ctypes.string_at(translation_ptr, min(translation_len.value, 4))
            if len(raw) < 4:
                return ""
            lang, codepage = struct.unpack("<HH", raw[:4])

            query = f"\\StringFileInfo\\{lang:04x}{codepage:04x}\\ProductName"
            ptr = ctypes.c_wchar_p()
            length = ctypes.c_uint()
            ret = ctypes.windll.version.VerQueryValueW(
                buf.raw, query, ctypes.byref(ptr), ctypes.byref(length)
            )
            if ret and length.value > 0:
                return ptr.value
        except Exception:
            pass
        return ""


class InstalledScanner:
    """扫描系统已安装软件（通过 Windows 注册表）"""

    # 注册表卸载信息路径
    REG_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    # 注册表值名
    REG_VALUE_MAP = {
        "name": "DisplayName",
        "version": "DisplayVersion",
        "publisher": "Publisher",
        "install_location": "InstallLocation",
        "uninstall_string": "UninstallString",
    }

    def scan(self) -> List[InstalledSoftware]:
        """扫描注册表，返回已安装软件列表"""
        results = []
        seen_names = set()

        for root_key, subpath in self.REG_PATHS:
            try:
                for software in self._scan_reg_path(root_key, subpath):
                    if software.name and software.name not in seen_names:
                        seen_names.add(software.name)
                        results.append(software)
            except Exception:
                continue

        return results

    def _scan_reg_path(self, root_key, subpath: str) -> List[InstalledSoftware]:
        """扫描单个注册表路径"""
        results = []
        try:
            with winreg.OpenKey(root_key, subpath) as key:
                index = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        index += 1
                        software = self._read_subkey(root_key, subpath, subkey_name)
                        if software:
                            results.append(software)
                    except OSError:
                        break
        except FileNotFoundError:
            pass
        return results

    def _read_subkey(self, root_key, parent_path: str, subkey_name: str) -> Optional[InstalledSoftware]:
        """读取单个卸载子键的值"""
        full_path = f"{parent_path}\\{subkey_name}"
        try:
            with winreg.OpenKey(root_key, full_path) as key:
                values = {}
                for field, reg_name in self.REG_VALUE_MAP.items():
                    try:
                        value, _ = winreg.QueryValueEx(key, reg_name)
                        values[field] = str(value).strip() if value else ""
                    except FileNotFoundError:
                        values[field] = ""

                if not values.get("name"):
                    return None

                return InstalledSoftware(
                    name=values["name"],
                    version=values.get("version", ""),
                    publisher=values.get("publisher", ""),
                    install_location=values.get("install_location", ""),
                    uninstall_string=values.get("uninstall_string", ""),
                    registry_key=full_path,
                )
        except OSError:
            return None


def _clean_name(name: str) -> str:
    """清理名称：统一小写、去除非字母数字（保留中文）"""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", name.lower())


def _strip_version(clean: str) -> str:
    """剥离名称尾部的版本号/架构描述，返回核心名。
    例: python3131264bit -> python, nmap795 -> nmap, gitversion2430 -> gitversion
    """
    core = clean
    changed = True
    while changed and core:
        changed = False
        # 先剥架构描述 (x64/64bit/32位 等)
        new = re.sub(r"(?:x86|x64|amd64|arm64|32bit|64bit|32位|64位)$", "", core)
        if new != core:
            core, changed = new, True
            continue
        # 再剥数字结尾（版本号）
        new = re.sub(r"\d+$", "", core)
        if new != core:
            core, changed = new, True
    return core


def _first_token(name: str) -> str:
    """提取显示名的第一个有意义词（清理后）。
    例: 'Git version 2.43.0' -> 'git', 'Nmap 7.95' -> 'nmap'
    """
    m = re.search(r"[a-z0-9\u4e00-\u9fff]+", name.lower())
    return m.group(0) if m else ""


def _find_words(name: str) -> list:
    """按非字母数字分隔提取词列表（清理后）。
    例: 'VLC media player 3.0.20' -> ['vlc', 'media', 'player', '3020']
    """
    return [w for w in re.findall(r"[a-z0-9\u4e00-\u9fff]+", name.lower()) if w]


# 反向后缀匹配时排除的通用词（避免 'desktop'/'code' 等误配）
REVERSE_SUFFIX_EXCLUDE = {
    "code", "studio", "visual", "desktop", "client", "tools", "tool",
    "editor", "browser", "player", "reader", "viewer", "manager",
    "server", "service", "system", "platform", "framework", "runtime",
    "sdk", "kit", "core", "pack", "suite", "app", "apps", "launcher",
    "updater", "plugin", "extension", "official", "user", "community",
    "professional", "enterprise", "basic", "home", "pro", "lite", "free",
    "build", "edition", "version", "setup", "installer", "install",
}


def _alias_matches(alias: str, has_cjk: bool, sw_clean: str, sw_core: str, sw_words: list) -> bool:
    """判断单个别名是否与某个已安装软件名匹配"""
    # 1. 精确匹配（清理后 / 剥离版本号后）
    #    例: 'WeChat' == 'wechat', 'Python' == 'python' (来自 'Python 3.13.12 (64-bit)')
    if alias == sw_clean or alias == sw_core:
        return True

    first = sw_words[0] if sw_words else ""

    # 2. 词级匹配（仅限首词，避免 'NVIDIA NodeJS' 等厂商组件名干扰）
    #    例: 'Git version 2.x' -> 'git', 'Nmap 7.95' -> 'nmap'
    if alias == first:
        return True
    # 词头 + 版本号/架构后缀：'cursor2024' -> 'cursor'；中文粘连名 '剪映专业版' -> '剪映'
    if len(alias) >= 2 and first.startswith(alias):
        tail = first[len(alias):]
        if has_cjk or not tail or re.fullmatch(r"\d+(?:bit|x86|x64)?", tail):
            return True

    # 4. 前缀 + 修饰后缀：注册表名比别名多出 user/x64/版本号 等尾巴
    #    'Microsoft Visual Studio Code (User)' -> 'microsoftvisualstudiocode'
    #    白名单严格限定，避免 'Microsoft Visual Studio' 误配 VS Code（剩余 'code' 被拒）
    if sw_clean.startswith(alias):
        rest = sw_clean[len(alias):]
        if rest and re.fullmatch(
            r"(?:\d+(?:bit|x86|x64)?|user|x64|win64|x86|32bit|64bit|cn|cnuser|beta|stable|preview|dev|official)+",
            rest,
        ):
            return True

    # 3. 反向后缀匹配：注册表名比别名短时（'Mozilla Firefox' -> 'firefox'）
    #    排除通用词与完全相等的词，避免 'desktop' 误配 'GitHub Desktop'/'Docker Desktop'
    for w in sw_words:
        if not w or w == alias or len(w) < 5:
            continue
        if w in REVERSE_SUFFIX_EXCLUDE:
            continue
        if alias.endswith(w):
            return True

    return False


def check_package_installed(package: PackageInfo, installed: List[InstalledSoftware]) -> bool:
    """检查安装包是否已安装。

    匹配优先级：
    1. 配置的 registry_names 多别名（最可靠，含中英文别名）
    2. 产品名 / 显示名（清理、剥离版本号、词级匹配）
    """
    if not installed:
        return False

    # 收集候选别名（清理后），顺序：registry_names → product_name → name
    raw_aliases = list(package.registry_names or [])
    for raw in (package.product_name, package.name):
        if raw and raw not in raw_aliases:
            raw_aliases.append(raw)

    aliases = {}
    for raw in raw_aliases:
        clean = _clean_name(raw)
        if len(clean) >= 2:
            aliases[clean] = bool(re.search(r"[\u4e00-\u9fff]", clean))

    if not aliases:
        return False

    for sw in installed:
        sw_clean = _clean_name(sw.name)
        if not sw_clean or len(sw_clean) < 2:
            continue
        sw_core = _strip_version(sw_clean)
        sw_words = _find_words(sw.name)

        for alias, has_cjk in aliases.items():
            if _alias_matches(alias, has_cjk, sw_clean, sw_core, sw_words):
                package.installed_version = sw.version
                return True

    return False
