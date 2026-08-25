# -*- coding: utf-8 -*-
"""对比子进程收到的原始命令行（安装器真正解析的东西）"""
import subprocess

PY = r"C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
OUT1 = r"C:\Users\Administrator\Downloads\AutoInstall\tests\_cmdline_list.txt"
OUT2 = r"C:\Users\Administrator\Downloads\AutoInstall\tests\_cmdline_str.txt"
ARG = '/DIR="C:\\Program Files"'

# 子进程代码：把 GetCommandLineW 原始内容写入文件
code = (
    "import ctypes,sys;"
    "k=ctypes.windll.kernel32;"
    "k.GetCommandLineW.restype=ctypes.c_wchar_p;"
    "open(sys.argv[1],'w',encoding='utf-8').write(k.GetCommandLineW())"
)

# 方式1: 列表参数（当前代码做法）—— subprocess 给含引号的元素做转义包裹
r1 = subprocess.run([PY, "-c", code, OUT1, ARG], capture_output=True)
print("子进程1 stderr:", r1.stderr.decode(errors="replace").strip() or "(无)")

# 方式2: 手工拼接字符串 —— CreateProcess 原样透传
cmdline = f'"{PY}" -c "{code}" "{OUT2}" {ARG}'
r2 = subprocess.run(cmdline, capture_output=True)
print("子进程2 stderr:", r2.stderr.decode(errors="replace").strip() or "(无)")

for label, path in [("列表方式 ", OUT1), ("字符串方式", OUT2)]:
    try:
        print(label, "原始命令行:", open(path, encoding="utf-8").read())
    except Exception as e:
        print(label, "读取失败:", e)
