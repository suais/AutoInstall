# -*- coding: utf-8 -*-
"""测试安装命令行构建（引号修复）与安装路径清洗"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.installer import InstallerEngine

fails = 0

def check(desc, actual, expected):
    global fails
    if actual == expected:
        print(f"  ✓ {desc}")
    else:
        fails += 1
        print(f"  ✗ {desc}")
        print(f"      期望: {expected!r}")
        print(f"      实际: {actual!r}")

print("─── 命令行构建（关键：引号必须是原生引号，不能出现 \\\" 转义）───")
b = InstallerEngine._build_cmdline

check("Inno /DIR=",
      b(r"C:\Apps\Setup.exe", ["/VERYSILENT", "/NORESTART"],
        '/DIR="{path}"', r"C:\Program Files"),
      r'"C:\Apps\Setup.exe" /VERYSILENT /NORESTART /DIR="C:\Program Files"')

check("NSIS /D=（不带引号）",
      b(r"C:\Apps\w.exe", ["/S"], "/D={path}", r"C:\Program Files"),
      r'"C:\Apps\w.exe" /S /D=C:\Program Files')

check("MSI INSTALLDIR=",
      b("msiexec", ["/i", '"C:\\Apps\\x.msi"', "/quiet"], 'INSTALLDIR="{path}"',
        r"C:\Program Files"),
      r'"msiexec" /i "C:\Apps\x.msi" /quiet INSTALLDIR="C:\Program Files"')

check("Advanced APPDIR=",
      b(r"C:\Apps\m.exe", ["/exenoui", "/qn", "/norestart"], 'APPDIR="{path}"',
        r"C:\Program Files"),
      r'"C:\Apps\m.exe" /exenoui /qn /norestart APPDIR="C:\Program Files"')

check("无 path_arg",
      b(r"C:\Apps\n.exe", ["/S"], None, r"C:\Program Files"),
      r'"C:\Apps\n.exe" /S')

check("路径带空格",
      b(r"C:\Apps\Setup.exe", ["/S"], '/DIR="{path}"', r"D:\My Programs\App"),
      r'"C:\Apps\Setup.exe" /S /DIR="D:\My Programs\App"')

# 反斜杠结尾的路径拼进带引号模板时，不能把结尾引号转义掉
check("路径尾部反斜杠已由清洗处理（此处直接验证拼接行为）",
      "包含 \\\" 即失败: " + (
          "OK" if '\\"' not in b(r"C:\a.exe", ["/S"], '/DIR="{path}"', r"C:\Apps")
          else "BAD"),
      "包含 \\\" 即失败: OK")

print("─── 安装路径清洗 ───")
s = InstallerEngine._sanitize_install_path

check("正常路径原样保留", s(r"C:\Program Files"), r"C:\Program Files")
check("去掉尾部反斜杠", s("C:\\Program Files\\"), r"C:\Program Files")
check("多个尾部反斜杠", s("C:\\Program Files\\\\\\"), r"C:\Program Files")
check("去掉首尾引号", s('"C:\\Program Files"'), r"C:\Program Files")
check("去掉首尾空白+引号", s('  "C:\\Program Files"  '), r"C:\Program Files")
check("盘符根保留反斜杠", s("C:\\"), "C:\\")

for bad in ['C:\\Pro<gram', 'C:\\App|X', 'C:\\a?b', 'D:\\x*y', 'C:\\a:b']:
    try:
        s(bad)
        check(f"非法路径应报错: {bad}", "未报错", "应抛 ValueError")
    except ValueError:
        check(f"非法路径应报错: {bad}", "ValueError", "ValueError")

print("─── 引擎路径错误拦截（GUI 不崩溃）───")
from src.core.models import PackageInfo
pkg = PackageInfo(filepath=r"C:\Apps\x.exe", filename="x.exe", ext=".exe",
                  size=100, name="X")
eng = InstallerEngine(install_path='C:\\bad<path>')
ok = eng.install(pkg)
check("非法路径时 install() 返回 False", ok, False)
check("路径错误已记录", "非法字符" in eng._path_error, True)

# 正常路径引擎构造不报错
eng2 = InstallerEngine(install_path="C:\\Program Files\\")
check("尾部反斜杠被清洗", eng2.install_path, r"C:\Program Files")

print("─── 每个软件装进自己的子文件夹 ───")
eng3 = InstallerEngine(install_path=r"C:\Program Files")
p_winscp = PackageInfo(filepath=r"C:\a.exe", filename="WinSCP.exe", ext=".exe",
                       size=1, name="WinSCP")
p_vscode = PackageInfo(filepath=r"C:\a.exe", filename="VSCode.exe", ext=".exe",
                       size=1, name="Visual Studio Code")
p_cn = PackageInfo(filepath=r"C:\a.exe", filename="dt.exe", ext=".exe",
                   size=1, name="钉钉 (DingTalk)")
p_bad = PackageInfo(filepath=r"C:\a.exe", filename="a:b.exe", ext=".exe",
                    size=1, name='App?Name:"bad"|')

check("WinSCP 子文件夹", eng3._target_dir(p_winscp), r"C:\Program Files\WinSCP")
check("带空格软件名", eng3._target_dir(p_vscode), r"C:\Program Files\Visual Studio Code")
check("中文名保留", eng3._target_dir(p_cn), r"C:\Program Files\钉钉 (DingTalk)")
check("非法字符剔除", eng3._target_dir(p_bad), r"C:\Program Files\AppNamebad")

print()
if fails:
    print(f"✗ {fails} 个用例失败")
    sys.exit(1)
print("✅ 全部通过")
