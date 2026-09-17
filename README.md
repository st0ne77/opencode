# opencode-config

opencode 的跨设备同步配置仓库（私有）。

核心目的：在 Windows 下把**所有 shell 命令统一收敛到一条 python 通道**，规避 PowerShell / cmd / git bash 之间的转义差异与字符编码乱码问题。

## 目录结构

```
opencode-config/
├── README.md                # 本文件
├── AGENTS.md                # opencode 全局规则（复制到 ~/.config/opencode/AGENTS.md）
├── opencode.json            # 提炼版配置（仅 permission，复制到 ~/.config/opencode/opencode.json）
└── .opencode/script/
    ├── run_cmd.py           # 统一命令执行器
    └── .gitignore           # 忽略 cmd.txt / input.txt
```

## 工作原理

三层机制协作：

| 层 | 机制 | 作用 |
|---|---|---|
| L1 | `AGENTS.md` 规则 | 要求所有命令走 python 通道（软约束） |
| L2 | `run_cmd.py` | 强制 UTF-8 输出、统一读 cmd.txt、预置 stdin、超时与退出码回传 |
| L3 | `opencode.json` 权限 | `bash` 全 `deny`，仅放行 `python .opencode/script/run_cmd.py`（硬拦截） |

### 命令执行流程

1. 用 write 工具把命令原文写入 `<工作目录>/.opencode/script/cmd.txt`（UTF-8）
2. 执行 `python .opencode/script/run_cmd.py`
3. 脚本读 cmd.txt，以项目根为 cwd 用 cmd.exe 执行，输出统一 UTF-8

需要 stdin 输入时，写入 `.opencode/script/input.txt`，脚本会一次性投喂。

## 已知限制

- **交互式命令无法实时双向交互**：opencode 不自带实时 stdin 通道，只能预置输入一次性投喂。
- **cmd.exe 内建命令的中文**（如 `echo 中文`）按 GBK 输出，会乱码；需要中文输出时用 python 产生。
- **转义未 100% 消除**：`shell=True` 走 cmd.exe，`%`、`&` 仍按 cmd 规则解释；消除的是 PowerShell 那层与编码乱码。
- 权限为 `"*": "deny"` 单条放行，容错为零：若匹配失败会锁死会话，需手动把 `"*"` 改回 `"ask"` 排障。

## 新设备部署

1. clone 本仓库
2. 将 `AGENTS.md` 复制/软链到 `~/.config/opencode/AGENTS.md`
3. 将 `opencode.json` 的 `permission` 合并到 `~/.config/opencode/opencode.json`（**注意保留本机原有的 provider / mcp / apiKey，本仓库不保存密钥**）
4. 需要命令通道的项目中，确保存在 `.opencode/script/run_cmd.py`
5. 重启 opencode 使权限生效

## 安全说明

本仓库**不保存任何 API key、内网地址或机器相关绝对路径**。真实密钥与本机 MCP/provider 配置保留在 `~/.config/opencode/opencode.json`，不入库。
