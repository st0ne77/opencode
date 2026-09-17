# opencode-config

opencode 的跨设备同步配置仓库（私有）。

核心目的：在 Windows 下把**所有 shell 命令统一收敛到一条 python 通道**，规避 PowerShell / cmd / git bash 之间的转义差异与字符编码乱码问题。

## 目录结构

```
opencode-config/
├── AGENTS.md                # 本项目目的说明（同时被 opencode 当规则加载）
├── README.md                # 本文件
├── install.py               # 跨平台安装脚本
├── user/                    # 部署源（会被 install.py 安装到目标机器）
│   ├── AGENTS.md            # 全局规则 -> ~/.config/opencode/AGENTS.md
│   ├── dev.sample.md        # 本地环境配置示例 -> ~/.config/opencode/dev.sample.md
│   └── opencode.json        # 项目级权限 -> <项目根>/opencode.json
└── .opencode/script/
    ├── run_cmd.py           # 统一命令执行器
    └── .gitignore           # 忽略 cmd.txt / input.txt
```

## 工作原理

三层机制协作：

| 层 | 机制 | 作用 |
|---|---|---|
| L1 | `user/AGENTS.md` 规则 | 要求所有命令走 python 通道（软约束） |
| L2 | `run_cmd.py` | 强制 UTF-8 输出、统一读 cmd.txt、预置 stdin、超时杀进程树、退出码回传 |
| L3 | `user/opencode.json` 权限 | `bash` 全 `deny`，仅放行 python 通道（硬拦截） |

### 命令执行流程

1. 用 write 工具把命令原文写入 `<工作目录>/.opencode/script/cmd.txt`（UTF-8）
2. 执行 `python .opencode/script/run_cmd.py`
3. 脚本读 cmd.txt，以项目根为 cwd 用 cmd.exe 执行，输出统一 UTF-8

需要 stdin 输入时，写入 `.opencode/script/input.txt`，脚本会一次性投喂。

### 超时看门狗

- 默认超时 600 秒（可用环境变量 `RUN_CMD_TIMEOUT` 覆盖，`0` 表示不限制）。
- **超时后强制杀掉整棵进程树**：Windows 用 `taskkill /F /T /PID`，Linux 用 `killpg`。避免后台服务残留或会话死等。
- 常驻服务（appium/server 等）必须用 python `Popen` + `DETACHED_PROCESS` + `DEVNULL` 启动，启动即返回，**绝不**让 run_cmd.py 等它退出。

## 已知限制

- **交互式命令无法实时双向交互**：opencode 不自带实时 stdin 通道，只能预置输入一次性投喂。
- **cmd.exe 内建命令的中文**（如 `echo 中文`）按 GBK 输出，会乱码；需要中文输出时用 python 产生。
- **转义未 100% 消除**：`shell=True` 走 cmd.exe，`%`、`&` 仍按 cmd 规则解释；消除的是 PowerShell 那层与编码乱码。
- 权限为 `"*": "deny"` 单条放行，容错为零：若匹配失败会锁死会话，需手动把 `"*"` 改回 `"ask"` 排障。

### 权限配置要点（`user/opencode.json`）

- `external_directory` 放行 `~/.config/opencode/**`，使 agent 能跨机器免申请读取 `dev.md` / `AGENTS.md`。
  - 注意：`external_directory` 必须用**目录通配 `**`**，精确到具体文件不生效。
- `edit` 对 `~/.config/opencode/**` 设为 `ask`：改动该目录下的配置文件需要审批，防止密钥被篡改。
- `read` 拒绝读取 `.env`、`*.pem`、`*.key`、`id_rsa*`、`.npmrc`、`.netrc`、`credentials*` 等敏感文件（但允许覆盖编辑）。

## 新设备部署

使用 `install.py`（跨平台，Windows / Linux 通用）。**必须显式指定安装项，脚本不默认安装任何内容。**

```bash
git clone https://github.com/st0ne77/opencode.git
cd opencode

python install.py -a                     # 安装用户级 AGENTS.md + dev.sample.md
python install.py -p <项目根目录>         # 安装项目级配置到指定项目
python install.py -a -p <项目根目录>      # 两者都安装
python install.py                        # 仅打印用法
```

Windows 下若 `python` 不可用，改用 `python3`。

| 参数 | 说明 | 目标位置 |
|---|---|---|
| `-a` / `--agents` | 安装用户级规则与示例 | `~/.config/opencode/AGENTS.md`、`~/.config/opencode/dev.sample.md`（已存在则备份 `.bak`） |
| `-p` / `--project DIR` | 安装项目级配置 + 执行器 | `<DIR>/opencode.json` 与 `<DIR>/.opencode/script/run_cmd.py` |

安装完成后**重启 opencode** 使权限生效。

### 本地环境配置（dev.md）

每台机器的数据库连接、内网地址等本机信息放在 `~/.config/opencode/dev.md`，**该文件不入库**。

- `-a` 会把仓库里的 `dev.sample.md` 安装到 `~/.config/opencode/dev.sample.md` 作为示例模板。
- 需要本地环境配置时，把 `dev.sample.md` 复制为同目录的 `dev.md`，填入本机真实值。
- `dev.md` 不存在时，agent 会静默跳过读取，不报错。

> 项目级 `opencode.json` 放在**项目根目录**（opencode 文档规定项目配置位于项目根；配置文件是合并语义，项目级覆盖全局级）。


## 安全说明

本仓库**不保存任何 API key、内网地址或机器相关绝对路径**。真实密钥与本机 MCP/provider 配置保留在 `~/.config/opencode/opencode.json`，不入库。
