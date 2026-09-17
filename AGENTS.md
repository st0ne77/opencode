# 本项目的目的

这是一个**跨设备同步的 opencode 配置仓库**（私有），不是业务代码项目。

## 要解决的问题

Windows 下 AI 助手执行 shell 命令时会持续踩坑：

1. **字符编码**：PowerShell / cmd.exe 默认 GBK，中文输出经常乱码。
2. **转义地狱**：cmd 与 git bash 转义规则不同（`^` vs `\`、`%VAR%` vs `$VAR`），而且 opencode 的环境里两种 shell 都可能出现，无法预判。

## 解决思路

把**所有 shell 命令统一收敛到一条 python 通道**：

```
write 命令原文到 .opencode/script/cmd.txt
        ↓
python .opencode/script/run_cmd.py  执行
        ↓
python 强制 UTF-8 输出，彻底绕开 shell 转义与编码差异
```

三层机制：

| 层 | 位置 | 作用 |
|---|---|---|
| 规则 | `user/AGENTS.md` | 要求所有命令走 python 通道（软约束） |
| 执行器 | `.opencode/script/run_cmd.py` | 读 cmd.txt、强制 UTF-8、逐行执行、超时/退出码回传 |
| 权限 | `user/opencode.json` | `bash` 全 deny，仅放行 python 通道（硬拦截） |

## 目录结构

```
opencode/
├── AGENTS.md                  # 本文件：项目目的说明（同时会被 opencode 当规则加载）
├── README.md                  # 详细说明与部署文档
├── install.py                 # 跨平台安装脚本
├── user/                      # 部署物（会被 install.py 安装到目标机器）
│   ├── AGENTS.md              # 全局规则模板 -> ~/.config/opencode/AGENTS.md
│   ├── opencode.json          # 项目级权限模板 -> <项目根>/opencode.json
│   └── dev.sample.md          # 本地环境配置示例 -> ~/.config/opencode/dev.sample.md
└── .opencode/script/
    ├── run_cmd.py             # 命令执行器
    └── .gitignore             # 忽略 cmd.txt / input.txt
```

## 部署方式

```bash
python install.py -a                    # 安装用户级 AGENTS.md + dev.sample.md
python install.py -p <项目根目录>         # 安装项目级 opencode.json + run_cmd.py
python install.py -a -p <项目根目录>      # 两者都安装
```

## 重要约定

- **修改本仓库文件时，注意 `user/` 下的三个文件是"部署源"**：改它们等于改变所有目标机器的配置。
- `.opencode/script/cmd.txt`、`input.txt` 是运行时产物，已被忽略，**不要提交**。
- 新增功能或约定时，同步更新本文件与 `README.md`。
