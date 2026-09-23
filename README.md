# opencode-config

opencode 的跨设备同步配置仓库（私有）。

核心目的：在 Windows 下把**所有 shell 命令统一收敛到一条 python 通道**，规避 PowerShell / cmd / git bash 之间的转义差异与字符编码乱码问题。

## 目录结构

```
opencode-config/
├── AGENTS.md                # 本项目目的说明（同时被 opencode 当规则加载）
├── README.md                # 本文件
├── install.py               # 跨平台安装脚本
└── user/                    # 部署源（会被 install.py 安装到目标机器）
    ├── AGENTS.md            # 全局规则 -> ~/.config/opencode/AGENTS.md
    ├── opencode.json        # 全局权限 -> ~/.config/opencode/opencode.json
    ├── agents/              # 自定义 agent -> ~/.config/opencode/agents/*.md
    │   └── test-engineer.md # 自动化测试工程师
    ├── dev.sample.md        # 本地环境配置示例 -> <项目>/.opencode/dev.sample.md
    ├── opencode.gitignore   # 项目忽略规则 -> <项目>/.opencode/.gitignore
    └── script/
        └── run_cmd.py       # 命令执行器 -> <项目>/.opencode/script/run_cmd.py
```

## 部署目标

| 源 | 目标 | 级别 |
|---|---|---|
| `user/AGENTS.md` | `~/.config/opencode/AGENTS.md` | 用户级（全局，所有项目） |
| `user/opencode.json` | `~/.config/opencode/opencode.json` | 用户级（全局，所有项目） |
| `user/agents/*.md` | `~/.config/opencode/agents/*.md` | 用户级（全局，所有项目） |
| `user/dev.sample.md` | `<项目>/.opencode/dev.sample.md` | 项目级 |
| `user/opencode.gitignore` | `<项目>/.opencode/.gitignore` | 项目级 |
| `user/script/run_cmd.py` | `<项目>/.opencode/script/run_cmd.py` | 项目级 |

> **为什么这样分层**：`AGENTS.md` / `opencode.json` 由 opencode **原生读取**（无需 `external_directory`）；`run_cmd.py`、`cmd.txt`、`dev.md` 放在**项目工作区内**，避免触发 `external_directory` 粗粒度开关，从而让 `edit` 等细粒度权限规则保持有效。

## 工作原理

三层机制协作：

| 层 | 机制 | 作用 |
|---|---|---|
| L1 | `user/AGENTS.md` 规则 | 要求所有命令走 python 通道（软约束） |
| L2 | `run_cmd.py` | 强制 UTF-8 输出、读同目录 cmd.txt、以项目根为 cwd、预置 stdin、超时杀进程树、退出码回传 |
| L3 | `user/opencode.json` 权限 | `bash` 全 `deny`，仅放行 python 通道（硬拦截） |

### 命令执行流程

1. 用 write 工具把命令原文写入 `<项目>/.opencode/script/cmd.txt`（UTF-8）
2. 执行 `python .opencode/script/run_cmd.py`（cwd = 项目根）
3. 脚本读 cmd.txt，以**业务项目根**为 cwd 用 cmd.exe 执行，输出统一 UTF-8

需要 stdin 输入时，写入 `<项目>/.opencode/script/input.txt`，脚本会一次性投喂。

### 超时看门狗

- 默认超时 600 秒（可用环境变量 `RUN_CMD_TIMEOUT` 覆盖，`0` 表示不限制）。
- **超时后强制杀掉整棵进程树**：Windows 用 `taskkill /F /T /PID`，Linux 用 `killpg`。避免后台服务残留或会话死等。
- 常驻服务（appium/server 等）必须用 python `Popen` + `DETACHED_PROCESS` + `DEVNULL` 启动，启动即返回，**绝不**让 run_cmd.py 等它退出。

## 已知限制

- **交互式命令无法实时双向交互**：opencode 不自带实时 stdin 通道，只能预置输入一次性投喂。
- **cmd.exe 内建命令的中文**（如 `echo 中文`）按 GBK 输出，会乱码；需要中文输出时用 python 产生。
- **转义未 100% 消除**：`shell=True` 走 cmd.exe，`%`、`&` 仍按 cmd 规则解释；消除的是 PowerShell 那层与编码乱码。
- 权限为 `"*": "deny"` 单条放行，容错为零：若匹配失败会锁死会话，需手动把 `"*"` 改回 `"ask"` 排障。
- **`external_directory` 是粗粒度二选一开关**：对某路径设 `allow` 后，该路径**完全继承工作区默认权限，同路径的 `read`/`edit` 细粒度规则全部失效**（实测 opencode 1.18.18，官方文档所述 "allow + edit deny" 组合实际无效）。因此 `run_cmd.py`、`dev.md` 一律放在项目工作区内，不依赖 `external_directory`。

### 权限配置要点（`user/opencode.json`）

- `bash` 放行规则匹配**命令字符串**，使用项目内相对路径：`python .opencode/script/run_cmd.py*`（含 `python3`）。
  - 相对路径基于**调用时的 cwd**（项目根），opencode 不展开 `~`，故**禁止在命令里用 `~`**。
- `external_directory` 放行 `~/.config/opencode/**`，使 agent 能免申请读取用户级 `AGENTS.md` 等。
  - 注意：`external_directory` 必须用**目录通配 `**`**，精确到具体文件不生效。
- `read` 拒绝读取 `.env`、`*.pem`、`*.key`、`id_rsa*`、`.npmrc`、`.netrc`、`credentials*` 等敏感文件。
- `edit` 默认 `allow`，但 `**/dev.md` 设为 `deny`：项目内 `dev.md` 含本机密钥，禁止 agent 改写。
  - 该规则**仅在文件位于工作区内时有效**；用户级目录的写保护无法用 `edit` 规则实现（被 `external_directory` 架空），故不设置无效规则。

## 新设备部署

使用 `install.py`（跨平台，Windows / Linux 通用）。**必须显式指定安装项，脚本不默认安装任何内容。**

```bash
git clone https://github.com/st0ne77/opencode.git
cd opencode

python install.py -a                     # 安装用户级配置（AGENTS.md + opencode.json + agents/）
python install.py -p <项目根目录>         # 安装项目级配置到 <项目>/.opencode/
python install.py -a -p <项目根目录>      # 两者都安装
python install.py                        # 仅打印用法
```

Windows 下若 `python` 不可用，改用 `python3`。

| 参数 | 说明 | 目标位置 |
|---|---|---|
| `-a` / `--agents` | 安装用户级配置 | `~/.config/opencode/AGENTS.md`、`~/.config/opencode/opencode.json`、`~/.config/opencode/agents/*.md`（已存在则备份 `.bak`） |
| `-p` / `--project DIR` | 安装项目级配置 | `<DIR>/.opencode/dev.sample.md`、`<DIR>/.opencode/.gitignore`、`<DIR>/.opencode/script/run_cmd.py`（已存在则备份 `.bak`） |

安装完成后**重启 opencode** 使权限生效。

### 本地环境配置（dev.md）

每台（项目所在）机器的数据库连接、内网地址等本机信息放在 `<项目>/.opencode/dev.md`，**该文件不入库**（已被 `.opencode/.gitignore` 忽略）。

- `-p` 会把仓库里的 `dev.sample.md` 安装到 `<项目>/.opencode/dev.sample.md` 作为示例模板。
- 需要本地环境配置时，把 `dev.sample.md` 复制为同目录的 `dev.md`，填入本机真实值。
- `dev.md` 不存在时，agent 会静默跳过读取，不报错。

> opencode 配置文件是**合并语义**：用户级 `~/.config/opencode/opencode.json` 对所有项目生效，项目级会覆盖同名键。

## 自定义 Agent

`user/agents/*.md` 由 `-a` 安装到 `~/.config/opencode/agents/`，对所有项目生效。当前提供：

| Agent | mode | 用途 |
|---|---|---|
| `test-engineer` | `all` | 自动化测试工程师：后端接口测试（dbhub + python 通道）、前端 Web 页面测试（chrome-devtools）；只写测试代码，发现业务缺陷只报告不改实现 |

用法：

- **作为主 agent**：会话中切换到 `test-engineer`，直接让它测。
- **作为 subagent**：对主 agent 说「用 test-engineer 子代理测一下 XX 接口 / XX 页面」。

权限要点：`edit` 默认 `deny`，仅放行测试路径（`*test/*`、`*tests/*`、`*__tests__/*`、`*e2e/*`、`*integration_test/*`、`*_test.*`、`*.test.*`、`*.spec.*`、`*test_*.*`、`*test-*.*`、`*conftest.py`），确保它只能在测试代码里动刀；`shell` 沿用全局，仍只走 python 通道。

新增自定义 agent：在 `user/agents/` 下加 `<name>.md`（frontmatter + Markdown 正文作为 system prompt），重新执行 `python install.py -a` 即可。

## 安全说明

本仓库**不保存任何 API key、内网地址或机器相关绝对路径**。真实密钥与本机 MCP/provider 配置保留在 `~/.config/opencode/opencode.json`，不入库。
