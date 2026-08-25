# -*- coding: utf-8 -*-
"""反查注册表中可疑条目"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.scanner import InstalledScanner

installed = InstalledScanner().scan()

# 按版本号找
for ver in ["3.0.67", "3.28.0.417"]:
    print(f"=== DisplayVersion = {ver} 的条目 ===")
    for sw in installed:
        if sw.version == ver:
            print(f"  '{sw.name}'  pub={sw.publisher}  key={sw.registry_key}")

# 按名称找关键字
print("\n=== 含 vlc / feishu / notion / kimi / doubao / zed / go / java / nmap 的条目 ===")
for sw in installed:
    n = sw.name.lower()
    if any(k in n for k in ["vlc", "feishu", "notion", "kimi", "doubao", "zed", "golang", "java", "nmap", "code", "node", "minimax", "trae", "zcode"]):
        print(f"  '{sw.name}'  v{sw.version}  pub={sw.publisher}")
