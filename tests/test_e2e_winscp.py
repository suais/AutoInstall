# -*- coding: utf-8 -*-
"""端到端验证：用修复后的引擎静默安装 WinSCP（此前因引号转义失败）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.installer import InstallerEngine
from src.core.scanner import PackageScanner, InstalledScanner, check_package_installed

# 扫描找到 WinSCP 包
pkgs = [p for p in PackageScanner().scan() if 'winscp' in p.filename.lower()]
if not pkgs:
    print("未找到 WinSCP 安装包")
    sys.exit(1)

pkg = pkgs[0]
print(f"包: {pkg.filename}  类型: {pkg.installer_type}  path_arg: {pkg.path_arg}")

engine = InstallerEngine(install_path=r"C:\Program Files")
ok = engine.install(pkg, on_log=lambda m: print("  [日志]", m))

print(f"\n安装结果: {'成功' if ok else '失败'} (状态: {pkg.status})")

# 注册表验证
for sw in InstalledScanner().scan():
    if 'winscp' in sw.name.lower():
        print(f"注册表确认: {sw.name!r} v{sw.version} @ {sw.install_location}")
        break
else:
    print("注册表未找到 WinSCr — 安装未成功")
