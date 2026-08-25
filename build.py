# -*- coding: utf-8 -*-
"""构建脚本：清理旧构建、运行 PyInstaller、验证产物"""

import os
import sys
import shutil
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE = os.path.join(PROJECT_DIR, "AutoInstall.spec")
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
PYTHON_EXE = sys.executable


def clean():
    """清理旧的构建产物（容错：删除失败不影响构建，PyInstaller --noconfirm 会覆盖）"""
    print("=" * 60)
    print("清理旧构建产物...")
    print("=" * 60)
    for path in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"  已删除: {path}")
            except OSError as e:
                print(f"  跳过删除 {path}（{e}，PyInstaller 将覆盖）")
    # 删除 __pycache__
    for root, dirs, files in os.walk(PROJECT_DIR):
        for d in dirs:
            if d == "__pycache__":
                try:
                    shutil.rmtree(os.path.join(root, d))
                except OSError:
                    pass


def run_pyinstaller():
    """运行 PyInstaller"""
    print("\n" + "=" * 60)
    print("开始 PyInstaller 打包...")
    print("=" * 60)

    cmd = [
        PYTHON_EXE, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        SPEC_FILE
    ]
    print(f"执行命令: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr)
        return False
    return True


def verify_output():
    """验证输出"""
    print("\n" + "=" * 60)
    print("验证输出...")
    print("=" * 60)

    exe_path = os.path.join(DIST_DIR, "AutoInstall.exe")
    if not os.path.exists(exe_path):
        print(f"✗ 可执行文件不存在: {exe_path}")
        return False

    size = os.path.getsize(exe_path)
    print(f"✓ 可执行文件已生成: {exe_path}")
    print(f"  大小: {size / 1024 / 1024:.2f} MB")

    # 检查 Packages 目录
    packages_dir = os.path.join(PROJECT_DIR, "Packages")
    if os.path.exists(packages_dir):
        count = len([f for f in os.listdir(packages_dir) if f.endswith(('.exe', '.msi', '.msix', '.msixbundle'))])
        print(f"✓ Packages 目录: {count} 个安装包（位于 exe 同级目录）")

    return True


def main():
    clean()
    if not run_pyinstaller():
        print("\n✗ 打包失败！")
        sys.exit(1)
    if not verify_output():
        print("\n✗ 验证失败！")
        sys.exit(1)
    print("\n" + "=" * 60)
    print("✓ 打包完成！")
    print("=" * 60)
    print(f"\n可执行文件: {os.path.join(DIST_DIR, 'AutoInstall.exe')}")
    print(f"安装包目录: {os.path.join(PROJECT_DIR, 'Packages')}")
    print(f"\n使用方法:")
    print(f"  1. 将 AutoInstall.exe 放到任意目录")
    print(f"  2. 在同目录创建 Packages 文件夹，放入安装包")
    print(f"  3. 双击运行 AutoInstall.exe")


if __name__ == "__main__":
    main()
