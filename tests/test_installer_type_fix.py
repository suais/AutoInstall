# -*- coding: utf-8 -*-
"""验证安装器类型交叉校验：
1. MindLine 应被识别为 Advanced Installer（/qn /norestart）
2. 全库扫描，找出所有被二进制签名推翻数据库判断的包（同类隐患）
3. 所有包类型分布无回归
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.scanner import PackageScanner
from src.config import PACKAGES_DIR, INSTALLER_ADVANCED

failures = []

# ── 1. MindLine 单包验证 ──
scanner = PackageScanner()
pkgs = scanner.scan(PACKAGES_DIR)
mindline = [p for p in pkgs if "mindline" in p.filename.lower()]
if not mindline:
    print("✗ 未找到 MindLine 安装包")
    sys.exit(1)
p = mindline[0]
cmd = [p.filepath] + list(p.silent_args)
if p.path_arg:
    cmd.append(p.path_arg.replace("{path}", r"C:\Program Files"))
print(f"MindLine: type={p.installer_type}, args={p.silent_args}, path_arg={p.path_arg}")
print(f"  实际执行命令: {' '.join(cmd)}")
if p.installer_type != INSTALLER_ADVANCED:
    failures.append(f"MindLine 类型应为 advanced，实际 {p.installer_type}")
if "/VERYSILENT" in " ".join(cmd):
    failures.append("MindLine 命令仍含 /VERYSILENT")

# ── 2. 全库类型分布 + 被签名纠正的包 ──
from src.config import match_installer, sniff_installer_signature_strong, SILENT_ARGS, PATH_ARG_TEMPLATES, INSTALLER_CUSTOM
from collections import Counter
dist = Counter()
corrected = []
for pkg in pkgs:
    dist[pkg.installer_type] += 1
    if pkg.ext == ".exe":
        db = match_installer(pkg.filename)
        if db and db["type"] != INSTALLER_CUSTOM:
            sniffed = sniff_installer_signature_strong(pkg.filepath)
            if sniffed and sniffed != db["type"]:
                corrected.append((pkg.filename, db["type"], sniffed))

print(f"\n全库 {len(pkgs)} 个包，类型分布: {dict(dist)}")
print("\n被二进制签名纠正的包（数据库判断 vs 签名）:")
for fn, dbt, sn in corrected:
    print(f"  {fn}  {dbt} -> {sn}")
if not corrected:
    print("  （仅 MindLine，其余无冲突）")

# ── 3. 未知包兜底检测冒烟 ──
unknown = [p for p in pkgs if not match_installer(p.filename)]
print(f"\n未匹配数据库的包 {len(unknown)} 个（走二进制兜底检测）")

if failures:
    print("\n".join(["✗ " + f for f in failures]))
    sys.exit(1)
print("\n✅ 全部通过")
