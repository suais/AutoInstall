# -*- coding: utf-8 -*-
"""真实环境诊断：扫描注册表 + Packages，用新逻辑检测已安装状态"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.scanner import PackageScanner, InstalledScanner, check_package_installed, _clean_name
from src.core.models import InstallStatus

PACKAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Packages")


def main():
    scanner = PackageScanner()
    packages = scanner.scan(PACKAGES_DIR)
    print(f"扫描到 {len(packages)} 个安装包\n")

    installed_scanner = InstalledScanner()
    installed = installed_scanner.scan()
    print(f"注册表已安装软件 {len(installed)} 条\n")

    # 建立 sw_clean -> sw 映射便于反查
    installed_clean = {_clean_name(sw.name): sw for sw in installed}

    not_installed = []
    installed_count = 0
    for pkg in packages:
        matched = check_package_installed(pkg, installed)
        if matched:
            installed_count += 1
            # 反查匹配到的注册表条目
            sw_clean = _clean_name(pkg.product_name or "")
            print(f"  [已装] {pkg.name}  (已装 v{pkg.installed_version})")
        else:
            not_installed.append(pkg)
            print(f"  [未装] {pkg.name}")

    print(f"\n{'='*60}")
    print(f"已安装 {installed_count} | 未安装 {len(not_installed)} | 共 {len(packages)}")

    print(f"\n--- 未安装列表（人工核对，确认是否误判）---")
    for pkg in not_installed:
        aliases = [pkg.product_name] + (pkg.registry_names or [])
        print(f"  {pkg.name:<28} 包: {pkg.filename}")
        # 模糊提示：与注册表中哪些名字相近
        hints = []
        for sw in installed:
            a = _clean_name(sw.name)
            b = _clean_name(pkg.product_name or pkg.name)
            if b and (b in a or a in b):
                hints.append(f"'{sw.name}'")
        if hints:
            print(f"       → 注册表中有相近条目: {', '.join(hints[:3])}")


if __name__ == "__main__":
    main()
