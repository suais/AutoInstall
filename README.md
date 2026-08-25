# AutoInstall

一键自动安装 Windows 软件包的工具。适合系统重装后快速建立工作环境。

## 功能特性

- 自动扫描 `Packages` 文件夹内的所有 `.exe`/`.msi`/`.msix` 安装包
- 智能识别安装包类型（NSIS / Inno Setup / MSI / Squirrel / InstallShield 等）
- 自动检测系统已安装软件，过滤已安装项
- 静默安装模式（无需人工点击下一步/同意/安装）
- 自动点击模式（兜底处理不支持静默安装的安装器）
- 可自定义安装路径
- 80+ 款常用软件预置静默参数（VSCode、Chrome、Git、Node.js、Docker、JetBrains Toolbox 等）
- 安装日志持久化：每次安装会话自动生成日志文件，可随时查看历史记录
- 极简 Vercel 风格界面

## 使用方法

### 快速开始

1. 运行 `AutoInstall.exe`
2. 在窗口中查看自动识别的安装包列表
3. 取消勾选不需要安装的软件（或点击「全选」全部安装）
4. 设置安装路径（默认 `C:\Program Files`）
5. 点击「开始安装」按钮

### 安装日志

每次安装会话自动在 `logs/` 目录生成日志文件（`install_时间戳.log`），包含：

- 会话信息：开始时间、安装路径、自动点击开关、待安装清单
- 逐条安装过程：执行的命令、安装器输出、返回码、AutoClicker 动作
- 结果摘要：结束时间、总耗时、成功/失败/跳过统计、日志文件路径

安装完成后，进度对话框会显示日志文件路径，点击「打开日志文件夹」可直接定位。

### 添加新的安装包

将安装包（`.exe`、`.msi` 或 `.msix`）放入 `Packages` 文件夹即可。重新运行程序或点击「刷新」按钮识别新包。

### 目录结构

```
AutoInstall/
├── AutoInstall.exe          # 主程序
├── Packages/                # 安装包目录
│   ├── WeChatWin_4.1.13.exe
│   ├── ChromeSetup.exe
│   ├── node-v24.19.0-x64.msi
│   └── ...
├── logs/                    # 安装日志目录（自动生成）
│   └── install_20260824_171500.log
├── assets/
│   └── icon.ico             # 应用图标
└── README.md
```

## 支持的安装器类型

| 类型 | 静默参数 | 说明 |
|------|----------|------|
| NSIS | `/S` | Nullsoft Scriptable Install System |
| Inno Setup | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART` | 多数商业安装器使用 |
| MSI | `msiexec /i ... /quiet /norestart` | Windows Installer |
| Squirrel | `--silent` | Electron 应用常用 |
| InstallShield | `/s /v/qn` | 老牌商业安装器 |
| WiX | `-quiet -norestart` | .NET 生态常用 |

## 静默安装参数数据库

程序内置 80+ 款常用软件的静默安装参数，匹配规则基于文件名关键字：

- 浏览器：Chrome、Firefox
- 通讯：WeChat（微信）、Foxmail、DingTalk（钉钉）
- 开发工具：VSCode、Cursor、JetBrains Toolbox、Sublime、Zed、各类 IDE
- 运行时：Node.js、Python、Java JDK/JRE、Git、Go、Rust、Docker
- 数据库：MongoDB、DBeaver
- 远程控制：ToDesk、向日葵（AweSun）、UrBackup
- 网络工具：WinSCP、Wireshark、Nmap
- 媒体：VLC、HandBrake、剪映
- 设计：Figma、MasterGo、Pixso、draw.io、Affinity
- AI 工具：Kimi、豆包、Ollama、LM Studio
- 效率：Obsidian、Notion、Everything、Postman

## 自定义静默安装参数

如果某个安装包的静默参数不正确，可以编辑 `src/config.py` 的 `INSTALLER_DB` 字典，添加或修改对应软件的正则表达式和参数。

## 系统要求

- Windows 10 / 11 (64-bit)
- 部分安装包需要管理员权限（UAC）
- 部分 .msix 包需要 Windows 10 1809+ 和「应用安装程序」

## 技术栈

- **GUI**: PySide6 (Qt 6.6+)
- **自动点击**: pywinauto
- **日志**: 自研 InstallLogger（线程安全文件写入）
- **打包**: PyInstaller
- **图标**: Pillow

## 许可

仅供个人使用。
