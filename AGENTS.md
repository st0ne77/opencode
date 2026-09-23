# 本项目的目的

这是一个**跨设备同步的 opencode 配置仓库**（私有），不是业务代码项目。

## 要解决的问题

Windows 下 AI 助手执行 shell 命令时会持续踩坑：

1. **字符编码**：PowerShell / cmd.exe 默认 GBK，中文输出经常乱码。
2. **转义地狱**：cmd 与 git bash 转义规则不同（`^` vs `\`、`%VAR%` vs `$VAR`），而且 opencode 的环境里两种 shell 都可能出现，无法预判。

## 解决思路

把**所有 shell 命令统一收敛到一条 python 通道**：

```
write 命令原文到 <项目>/.opencode/script/cmd.txt
        ↓
python .opencode/script/run_cmd.py  执行（cwd = 业务项目根）
        ↓
python 强制 UTF-8 输出，彻底绕开 shell 转义与编码差异
```

三层机制：

| 层 | 位置 | 作用 |
|---|---|---|
| 规则 | `user/AGENTS.md` | 要求所有命令走 python 通道（软约束） |
| 执行器 | `<项目>/.opencode/script/run_cmd.py` | 读同目录 cmd.txt、以项目根为 cwd、强制 UTF-8、逐行执行、超时/退出码回传 |
| 权限 | `user/opencode.json` | `bash` 全 deny，仅放行 python 通道（硬拦截） |

## 目录结构

```
opencode/
├── AGENTS.md                  # 本文件：项目目的说明（同时会被 opencode 当规则加载）
├── README.md                  # 详细说明与部署文档
├── install.py                 # 跨平台安装脚本
└── user/                      # 部署源（会被 install.py 安装到目标机器）
    ├── AGENTS.md              # 全局规则模板 -> ~/.config/opencode/AGENTS.md
    ├── opencode.json          # 全局权限模板 -> ~/.config/opencode/opencode.json
    ├── dev.sample.md          # 本地环境配置示例 -> <项目>/.opencode/dev.sample.md
    ├── opencode.gitignore     # 项目忽略规则 -> <项目>/.opencode/.gitignore
    ├── agents/                # 自定义 agent 定义目录
    │   └── test-engineer.md   # 自动化测试工程师 -> ~/.config/opencode/agents/
    └── script/
        └── run_cmd.py         # 命令执行器 -> <项目>/.opencode/script/run_cmd.py
```

## 部署方式

```bash
python install.py -a                     # 安装用户级配置（AGENTS.md + opencode.json + agents/）
python install.py -p <项目根目录>         # 安装项目级配置到 <项目>/.opencode/
python install.py -a -p <项目根目录>      # 两者都安装
python install.py                        # 仅打印用法
```

## 重要约定

- **`user/` 下的全部文件是"部署源"**：改它们等于改变所有目标机器的配置。
- **`AGENTS.md` 与 `opencode.json` 部署到用户级**（`~/.config/opencode/`），对所有项目生效。
- **`run_cmd.py`、`dev.md`、`.gitignore` 部署到项目级**（`<项目>/.opencode/`），避免触发 `external_directory` 粗粒度开关，从而保留细粒度权限规则的有效性。
- `run_cmd.py` 以**业务项目根**（`.opencode` 的上级目录）为子进程 cwd，因此命令里的相对路径按业务项目解析。
- `<项目>/.opencode/script/cmd.txt`、`input.txt`、`<项目>/.opencode/dev.md` 是运行时产物，由 `.opencode/.gitignore` 忽略，**不要提交**。
- 新增功能或约定时，同步更新本文件与 `README.md`。
