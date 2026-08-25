# -*- coding: utf-8 -*-
"""已安装检测逻辑测试：用真实注册表名场景验证匹配与防误报"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.models import PackageInfo, InstalledSoftware
from src.core.scanner import check_package_installed, _clean_name, _strip_version, _first_token

# ─── 辅助：构造测试对象 ───
def make_pkg(filename, registry_names=None):
    """构造与 _build_package 逻辑一致的 PackageInfo"""
    from src.config import match_installer
    db = match_installer(filename)
    if db:
        regs = list(db.get("registry_names") or [])
        return PackageInfo(
            filepath=f"C:/fake/{filename}", filename=filename, ext=".exe", size=1,
            name=db["name"], product_name=regs[0] if regs else "",
            registry_names=regs,
        )
    return PackageInfo(
        filepath=f"C:/fake/{filename}", filename=filename, ext=".exe", size=1,
        name=filename, product_name=filename,
    )


def make_sw(name, version="1.0"):
    return InstalledSoftware(name=name, version=version)


# ─── 辅助函数单测 ───
def test_helpers():
    assert _strip_version("python3131264bit") == "python", _strip_version("python3131264bit")
    assert _strip_version("nmap795") == "nmap", _strip_version("nmap795")
    assert _strip_version("vlcmediaplayer3020") == "vlcmediaplayer"
    assert _strip_version("gitversion2430") == "gitversion"
    assert _strip_version("wireshark420") == "wireshark"
    assert _strip_version("everything150138a") == "everything150138a"
    assert _first_token("Git version 2.43.0") == "git"
    assert _first_token("Nmap 7.95") == "nmap"
    assert _first_token("剪映专业版") == "剪映专业版"
    assert _clean_name("Microsoft Visual Studio Code") == "microsoftvisualstudiocode"
    print("PASS: 辅助函数")


# ─── 应匹配用例：包 → 已安装软件（真实注册表名）───
MATCH_CASES = [
    # (包文件名, 已安装软件名, 说明)
    ("Git-2.43.0-64-bit.exe", "Git version 2.43.0", "Git 带版本号"),
    ("Git-2.43.0-64-bit.exe", "Git", "Git 纯名"),
    ("python-manager.exe", "Python 3.13.12 (64-bit)", "Python 带版本+架构"),
    ("nmap-7.95-setup.exe", "Nmap 7.95", "Nmap 带版本"),
    ("vlc-3.0.20-win32.exe", "VLC media player 3.0.20", "VLC 带版本"),
    ("kdocs_wps.exe", "WPS Office", "WPS 注册表英文名"),
    ("kdocs_wps.exe", "金山文档", "WPS 注册表中文名"),
    ("WeChatSetup.exe", "微信", "微信中文注册名"),
    ("WeChatSetup.exe", "WeChat", "微信英文注册名"),
    ("JianyingPro_Setup.exe", "剪映专业版", "剪映带专业版后缀"),
    ("VSCodeUserSetup-x64.exe", "Microsoft Visual Studio Code", "VS Code 完整名"),
    ("VSCodeUserSetup-x64.exe", "Microsoft Visual Studio Code (User)", "VS Code 用户级"),
    ("BaiduNetdisk_7.0.exe", "百度网盘", "百度网盘中文名"),
    ("AweSun_Setup.exe", "向日葵", "向日葵中文名"),
    ("everything-1.5.0.138a-setup.exe", "Everything 1.5.0.138a", "Everything 带版本"),
    ("Docker Desktop Installer.exe", "Docker Desktop", "Docker"),
    ("PostmanSetup-x64.exe", "Postman", "Postman"),
    ("node-v20.11.0-x64.msi", "Node.js", "Node.js"),
    ("Wireshark-4.2.0-x64.exe", "Wireshark 4.2.0", "Wireshark"),
    ("DingTalk_v7.0.exe", "钉钉", "钉钉中文名"),
    ("DingTalk_v7.0.exe", "DingTalk", "钉钉英文名"),
    ("go1.22.0.windows-amd64.msi", "Go Programming Language", "Go 完整注册名"),
    ("Obsidian-1.4.13.exe", "Obsidian", "Obsidian"),
    ("xunlei_XL10Setup.exe", "Thunder", "迅雷英文名"),
    ("xunlei_XL10Setup.exe", "迅雷", "迅雷中文名"),
    ("Kimi_0.5.exe", "Kimi", "Kimi"),
    ("OllamaSetup.exe", "Ollama", "Ollama"),
    ("Doubao_client.exe", "豆包", "豆包中文名"),
    ("zed-x86_64.exe", "Zed", "Zed"),
    ("CursorSetup.exe", "Cursor", "Cursor"),
    ("Figma-Setup.exe", "Figma", "Figma"),
    ("Firefox Setup.exe", "Mozilla Firefox", "Firefox 完整名"),
    ("Firefox Setup.exe", "Firefox", "Firefox 简称"),
    ("sublime_text_build_4169.exe", "Sublime Text", "Sublime Text"),
    ("dbeaver-windows-x64.exe", "DBeaver 23.2.0", "DBeaver"),
    ("MasterGo_Setup.exe", "MasterGo", "MasterGo"),
    ("draw.io-24.0.0-windows-installer.exe", "draw.io", "draw.io"),
    ("Notion-3.1.0.exe", "Notion", "Notion"),
    ("Obsidian-1.4.13.exe", "Obsidian 1.4.13", "Obsidian 带版本"),
    ("TraeCodeSetup.exe", "Trae", "Trae"),
    ("CodeBuddy_Setup.exe", "CodeBuddy", "CodeBuddy"),
    ("Omap-x64-Setup.exe", "Omap", "Omap"),
    ("PDFGear-Setup.exe", "pdfgear", "pdfgear"),
    ("ImageGlass_9.exe", "ImageGlass", "ImageGlass"),
    ("WinSCP-6.1.2-Setup.exe", "WinSCP 6.1.2", "WinSCP"),
    ("Eolink_Apikit.exe", "Apikit", "Apikit"),
    ("GitHubDesktopSetup.exe", "GitHub Desktop", "GitHub Desktop"),
    ("Alacritty-0.13.2-installer.msi", "Alacritty 0.13.2", "Alacritty"),
    ("Tabby-1.0.183-setup.exe", "Tabby", "Tabby"),
    ("XTerminal_Setup.exe", "XTerminal", "XTerminal"),
    ("MindLine-Setup.exe", "MindLine", "MindLine"),
    ("HandBrake-1.7.2-Win_GUI.exe", "HandBrake", "HandBrake"),
    ("xiaomi_jianying.exe", "JianyingPro", "剪映英文注册名"),
    ("Feishu-win32_x64-7.74.16-signed.exe", "飞书", "飞书中文名"),
    ("Feishu-win32_x64-7.74.16-signed.exe", "Feishu", "飞书英文名"),
    ("TencentMeeting_0300000000_3.45.2.405_x86_64.publish.officialwebsite.exe", "腾讯会议", "腾讯会议中文名"),
    ("TencentMeeting_0300000000_3.45.2.405_x86_64.publish.officialwebsite.exe", "Tencent Meeting", "腾讯会议英文名"),
    ("Cherry-Studio-2.0.8-x64-setup.exe", "Cherry Studio", "Cherry Studio"),
    ("NutstoreWindowsWPFInstaller.exe", "坚果云", "坚果云中文名"),
    ("NutstoreWindowsWPFInstaller.exe", "Nutstore", "坚果云英文名"),
]


# ─── 应不匹配用例：包 → 已安装软件（防误报）───
NO_MATCH_CASES = [
    ("Git-2.43.0-64-bit.exe", "GitHub Desktop", "git 不能误配 GitHub"),
    ("Git-2.43.0-64-bit.exe", "GitHub, Inc.", "git 不能误配 GitHub 公司"),
    ("VSCodeUserSetup-x64.exe", "Microsoft Visual Studio", "VS Code 不能误配完整 VS"),
    ("VSCodeUserSetup-x64.exe", "Visual Studio Build Tools", "VS Code 不能误配 VS 组件"),
    ("xunlei_XL10Setup.exe", "Mozilla Thunderbird (x64 en-US)", "迅雷不能误配 Thunderbird"),
    ("kdocs_wps.exe", "WPS PDF", "WPS Office 不能误配 WPS PDF"),
    ("CursorSetup.exe", "CursorFX", "Cursor 不能误配 CursorFX"),
    ("chromesetup.exe", "Chromium", "Chrome 不能误配 Chromium"),
    ("everything-1.5.0.138a-setup.exe", "EverythingToolbar", "Everything 不能误配 Toolbar"),
    ("Notion-3.1.0.exe", "NotionSandbox", "Notion 不能误配粘连名"),
    ("kimi_0.5.exe", "KimiKun", "Kimi 不能误配粘连名"),
    ("node-v20.11.0-x64.msi", "NVIDIA NodeJS", "Node.js 不能误配 NVIDIA 驱动组件"),
    ("node-v20.11.0-x64.msi", "NVIDIA GeForce Experience", "Node.js 不能误配 GeForce"),
    ("VSCodeUserSetup-x64.exe", "MiniMax Code 3.0.67", "VS Code 不能误配 MiniMax Code"),
    ("VSCodeUserSetup-x64.exe", "Docker Desktop 4.87.0", "VS Code 不能误配 Docker Desktop"),
    ("TraeCodeSetup.exe", "MiniMax Code 3.0.67", "Trae Code 不能误配 MiniMax Code"),
    ("ZCodeSetup.exe", "MiniMax Code 3.0.67", "ZCode 不能误配 MiniMax Code"),
    ("GitHubDesktopSetup-x64.exe", "Docker Desktop 4.87.0", "GitHub Desktop 不能误配 Docker"),
    ("GitHubDesktopSetup-x64.exe", "OpenCode 1.18.21", "GitHub Desktop 不能误配 OpenCode"),
]


def run_cases():
    fails = 0
    for filename, sw_name, desc in MATCH_CASES:
        pkg = make_pkg(filename)
        installed = [make_sw(sw_name)]
        result = check_package_installed(pkg, installed)
        if not result:
            fails += 1
            print(f"  ✗ 漏判: {filename} vs '{sw_name}' ({desc})  [aliases={pkg.registry_names or [pkg.product_name]}]")
        else:
            print(f"  ✓ {filename} vs '{sw_name}' ({desc})")

    for filename, sw_name, desc in NO_MATCH_CASES:
        pkg = make_pkg(filename)
        installed = [make_sw(sw_name)]
        result = check_package_installed(pkg, installed)
        if result:
            fails += 1
            print(f"  ✗ 误判: {filename} vs '{sw_name}' ({desc})  [aliases={pkg.registry_names or [pkg.product_name]}]")
        else:
            print(f"  ✓ 未误判: {filename} vs '{sw_name}' ({desc})")

    return fails


if __name__ == "__main__":
    test_helpers()
    print(f"\n应匹配用例 {len(MATCH_CASES)} 个，防误报用例 {len(NO_MATCH_CASES)} 个")
    fails = run_cases()
    print(f"\n{'全部通过 ✅' if fails == 0 else f'{fails} 个用例失败 ❌'}")
    sys.exit(1 if fails else 0)
