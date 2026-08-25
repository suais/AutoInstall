# -*- coding: utf-8 -*-
"""安装引擎：执行静默安装、管理进程"""

import os
import re
import sys
import time
import subprocess
import logging
from typing import Callable, Optional
from .models import PackageInfo, InstallStatus
from ..config import (
    INSTALLER_MSI, INSTALLER_CUSTOM, DEFAULT_INSTALL_PATH,
)

logger = logging.getLogger(__name__)

# 回调类型：(package, message, progress_pct) -> None
ProgressCallback = Callable[[PackageInfo, str, int], None]
LogCallback = Callable[[str], None]


class InstallerEngine:
    """安装引擎：负责执行软件的静默安装

    流程：
    1. 构建安装命令（msiexec / 直接运行 exe / Add-AppxPackage）
    2. 启动安装进程
    3. 等待安装完成
    4. 汇报结果
    """

    def __init__(self, install_path: str = None):
        self._path_error = None
        try:
            self.install_path = self._sanitize_install_path(
                install_path or DEFAULT_INSTALL_PATH)
        except ValueError as e:
            # 不在这里抛异常（引擎在 GUI 线程构造），
            # 记录错误并在每个包安装前拦截，日志给出明确提示
            self.install_path = (install_path or DEFAULT_INSTALL_PATH).strip().strip('"')
            self._path_error = str(e)
        self._cancelled = False

    @staticmethod
    def _sanitize_install_path(path: str) -> str:
        """清洗用户输入的安装路径，避免非法字符进入安装器。

        - 去掉首尾空白与引号（用户从输入框复制路径常带引号）
        - 去掉尾部反斜杠（`C:\\Apps\\` 拼进 `/DIR="..."` 时，`\\"` 会把引号转义掉）
        - 校验非法字符：文件夹名不允许 <>:"|?*（盘符冒号除外）
        """
        p = path.strip().strip('"').strip()
        while len(p) > 3 and p.endswith("\\"):
            p = p[:-1]

        # 非法字符校验（跳过盘符位置的冒号，如 C:\）
        bad_chars = [c for i, c in enumerate(p)
                     if c in '<>:"|?*' and not (c == ':' and i == 1)]
        if bad_chars:
            raise ValueError(
                f"安装路径包含非法字符 {' '.join(bad_chars)}: {path!r}，"
                f"路径中不允许 <>:\"|?*")
        if not p:
            raise ValueError(f"安装路径为空: {path!r}")
        return p

    def cancel(self):
        """取消安装"""
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def install(self, package: PackageInfo,
                on_progress: ProgressCallback = None,
                on_log: LogCallback = None) -> bool:
        """安装单个软件包

        Args:
            package: 安装包信息
            on_progress: 进度回调 (package, message, percent)
            on_log: 日志回调 (message)

        Returns:
            True=安装成功, False=失败/取消
        """
        # 注意：不要在这里重置 self._cancelled，否则取消请求可能被
        # 下一个包的 install() 覆盖掉（竞态导致取消失效）

        def log(msg: str):
            logger.info(f"[Install:{package.name}] {msg}")
            package.install_log += msg + "\n"
            if on_log:
                on_log(msg)

        def progress(msg: str, pct: int):
            if on_progress:
                on_progress(package, msg, pct)

        package.status = InstallStatus.INSTALLING
        progress(f"开始安装: {package.name}", 0)

        # 安装路径非法时直接拦截（错误在构造时已记录），不再传给安装器。
        # 放在 log() 定义之后，保证错误信息能进 UI 和安装日志
        if self._path_error:
            log(f"无法安装: {self._path_error}")
            package.status = InstallStatus.FAILED
            progress("安装路径非法", 100)
            return False

        # ─── MSIX 包特殊处理 ───
        if package.is_msix:
            return self._install_msix(package, log, progress)

        # ─── MSI 包使用 msiexec ───
        if package.ext == ".msi" or package.installer_type == INSTALLER_MSI:
            return self._install_msi(package, log, progress)

        # ─── 普通 EXE 安装 ───
        return self._install_exe(package, log, progress)

    def _target_dir(self, package: PackageInfo) -> str:
        """计算单个软件的安装目录：基础路径 + 软件名子文件夹。

        用户在界面填的是安装根目录（如 C:\\Program Files），每个软件
        应装进自己的子文件夹（C:\\Program Files\\WinSCP），
        否则文件会直接散落在根目录。
        软件名中的非法文件夹字符会被剔除。
        """
        folder = re.sub(r'[<>:"/\\|?*]', "", package.name).strip()
        if not folder:
            folder = os.path.splitext(package.filename)[0]
        return os.path.join(self.install_path, folder)

    @staticmethod
    def _build_cmdline(executable: str, args, path_arg: str, install_path: str) -> str:
        """手工拼接完整命令行字符串。

        必须传字符串而不是列表给 Popen：Windows 下 subprocess 会给列表里
        含引号的参数（如 /DIR="C:\\Program Files"）自动加转义，子进程原始
        命令行变成 /DIR=\\"C:\\Program Files\\"，Inno/NSIS 按原始命令行解析，
        反斜杠和引号被当作路径的一部分，导致安装器报
        「文件夹名不能包含下列任何字符：/:*?"<>|」。
        path_arg 模板自带引号（/DIR="{path}"），直接整体替换 {path} 即可。
        """
        parts = [f'"{executable}"']
        parts.extend(args or [])
        if path_arg:
            parts.append(path_arg.replace("{path}", install_path))
        return " ".join(parts)

    def _install_msi(self, package: PackageInfo, log, progress) -> bool:
        """使用 msiexec 安装 MSI 包"""
        log("使用 msiexec 安装")

        cmd = self._build_cmdline(
            "msiexec",
            ["/i", f'"{package.filepath}"'] + (package.silent_args or ["/quiet", "/norestart"]),
            package.path_arg,
            self._target_dir(package),
        )

        return self._run_process(package, cmd, log, progress, timeout=600)

    def _install_exe(self, package: PackageInfo, log, progress) -> bool:
        """直接运行 EXE 安装包"""
        log(f"安装器类型: {package.installer_type}")

        cmd = self._build_cmdline(
            package.filepath,
            package.silent_args,
            package.path_arg,
            self._target_dir(package),
        )

        return self._run_process(package, cmd, log, progress, timeout=900)

    def _install_msix(self, package: PackageInfo, log, progress) -> bool:
        """使用 PowerShell Add-AppxPackage 安装 MSIX 包"""
        log("使用 Add-AppxPackage 安装 MSIX 包")

        # 转义路径中的单引号
        escaped_path = package.filepath.replace("'", "''")
        ps_script = f"Add-AppxPackage -Path '{escaped_path}'"

        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-Command", ps_script]

        return self._run_process(package, cmd, log, progress, timeout=600)

    def _kill_process(self, process, log=None):
        """强制结束安装进程及其子进程（taskkill /T 杀进程树）"""
        try:
            process.terminate()
        except Exception:
            pass
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True, timeout=10,
            )
        except Exception as e:
            if log:
                log(f"结束进程失败: {e}")

    def _run_process(self, package: PackageInfo, cmd: str, log, progress, timeout: int) -> bool:
        """运行安装进程并等待完成。

        cmd 必须是完整命令行字符串（引号已按安装器文档拼好），
        Popen 直接透传给 CreateProcess，不做任何二次转义。
        """

        log(f"执行命令: {cmd}")

        try:
            # 以管理员权限运行（很多安装器需要提权）
            import ctypes
            try:
                # 尝试使用 runas 提权
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    startupinfo=startupinfo,
                    shell=False,
                )
            except Exception as e:
                log(f"启动进程失败: {e}")
                package.status = InstallStatus.FAILED
                progress("启动失败", 100)
                return False

            # 等待进程完成，带超时
            start_time = time.time()
            while True:
                if self._cancelled:
                    log("安装被取消")
                    self._kill_process(process, log)
                    package.status = InstallStatus.SKIPPED
                    progress("已取消", 100)
                    return False

                ret = process.poll()
                if ret is not None:
                    break

                elapsed = time.time() - start_time
                if elapsed > timeout:
                    log(f"安装超时 ({timeout}秒)")
                    self._kill_process(process, log)
                    package.status = InstallStatus.FAILED
                    progress("安装超时", 100)
                    return False

                # 更新进度（估算）
                elapsed_pct = min(int(elapsed / timeout * 100), 95)
                progress(f"正在安装... ({int(elapsed)}s)", elapsed_pct)

                time.sleep(1)

            # 读取输出
            stdout_data = b""
            stderr_data = b""
            try:
                stdout_data, stderr_data = process.communicate(timeout=5)
            except Exception:
                pass

            if stdout_data:
                log(f"输出: {stdout_data.decode('utf-8', errors='replace')[:500]}")
            if stderr_data:
                err_text = stderr_data.decode('utf-8', errors='replace')[:500]
                if err_text.strip():
                    log(f"错误输出: {err_text}")

            ret_code = process.returncode

            # 判断安装结果
            if ret_code == 0:
                log("安装完成 (返回码: 0)")
                package.status = InstallStatus.INSTALLED
                progress("安装成功", 100)
                return True
            elif ret_code == 1602 or ret_code == 1603:
                # 1602 = 用户取消, 1603 = 安装时出错
                log(f"安装返回码: {ret_code}")
                package.status = InstallStatus.FAILED
                progress(f"安装失败 (返回码: {ret_code})", 100)
                return False
            elif ret_code == 3010:
                # 3010 = 需要重启
                log("安装完成，需要重启计算机")
                package.status = InstallStatus.INSTALLED
                progress("安装成功（需重启）", 100)
                return True
            else:
                log(f"安装返回码: {ret_code}")
                package.status = InstallStatus.FAILED
                progress(f"安装失败 (返回码: {ret_code})", 100)
                return False

        except Exception as e:
            log(f"安装异常: {e}")
            package.status = InstallStatus.FAILED
            progress(f"安装异常: {e}", 100)
            return False
