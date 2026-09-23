#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""opencode-config 跨平台安装脚本。

用法:
    python install.py -a                     # 安装用户级配置
    python install.py -p <项目根目录>         # 安装项目级配置
    python install.py -a -p <项目根目录>      # 两者都安装
    python install.py                        # 打印用法

说明:
    -a/--agents   把下列内容安装到 ~/.config/opencode/（已存在则备份 .bak）：
                    user/AGENTS.md        -> ~/.config/opencode/AGENTS.md
                    user/opencode.json    -> ~/.config/opencode/opencode.json
                    user/agents/*.md      -> ~/.config/opencode/agents/*.md（逐个，不删除同名以外文件）

    -p/--project  把下列内容安装到 <项目根>/.opencode/（已存在则备份 .bak）：
                    user/dev.sample.md        -> <项目根>/.opencode/dev.sample.md
                    user/script/run_cmd.py    -> <项目根>/.opencode/script/run_cmd.py
                    user/opencode.gitignore   -> <项目根>/.opencode/.gitignore

    AGENTS.md 与 opencode.json 为**用户级全局配置**，对所有项目生效；
    dev.md、run_cmd.py、cmd.txt 等留在**项目** .opencode/ 内，不触发 external_directory。

Windows 与 Linux 通用；用户配置目录统一为 ~/.config/opencode。
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
USER_DIR = REPO_DIR / "user"
USER_CONFIG_DIR = Path.home() / ".config" / "opencode"


def log(msg: str) -> None:
    sys.stdout.write(msg + "\n")


def _force_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def backup_if_exists(path: Path) -> None:
    if path.exists():
        bak = path.with_name(path.name + ".bak")
        shutil.copy2(path, bak)
        log("  已备份: %s" % bak)


def _install_file(src: Path, dst: Path, label: str) -> int:
    if not src.is_file():
        sys.stderr.write("[错误] 仓库中缺少 %s: %s\n" % (label, src))
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    backup_if_exists(dst)
    shutil.copy2(src, dst)
    log("已安装%s -> %s" % (label, dst))
    return 0


def install_agent_definitions() -> int:
    src_dir = USER_DIR / "agents"
    if not src_dir.is_dir():
        log("  跳过 agents：仓库中无 user/agents/ 目录")
        return 0
    rc = 0
    for src in sorted(src_dir.rglob("*.md")):
        rel = src.relative_to(src_dir)
        rc |= _install_file(
            src, USER_CONFIG_DIR / "agents" / rel, "agent 定义 %s" % rel.as_posix()
        )
    return rc


def install_agents() -> int:
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    rc = 0
    rc |= _install_file(USER_DIR / "AGENTS.md", USER_CONFIG_DIR / "AGENTS.md", "用户级 AGENTS.md")
    rc |= _install_file(USER_DIR / "opencode.json", USER_CONFIG_DIR / "opencode.json", "全局权限配置")
    rc |= install_agent_definitions()
    return rc


def install_project(project: str) -> int:
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        sys.stderr.write("[错误] 项目目录不存在: %s\n" % root)
        return 1

    oc_dir = root / ".opencode"
    rc = 0
    rc |= _install_file(USER_DIR / "dev.sample.md", oc_dir / "dev.sample.md", "示例配置")
    rc |= _install_file(USER_DIR / "script" / "run_cmd.py", oc_dir / "script" / "run_cmd.py", "命令执行器")
    rc |= _install_file(USER_DIR / "opencode.gitignore", oc_dir / ".gitignore", "项目 gitignore")
    return rc


def main() -> int:
    _force_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="opencode-config 跨平台安装脚本（必须显式指定安装项，不默认安装任何内容）",
        add_help=True,
    )
    parser.add_argument(
        "-a", "--agents", action="store_true",
        help="安装用户级配置到 ~/.config/opencode/（AGENTS.md、opencode.json、agents/*.md）",
    )
    parser.add_argument(
        "-p", "--project", metavar="DIR",
        help="安装项目级配置到 <DIR>/.opencode/（dev.sample.md、script/run_cmd.py、.gitignore）",
    )
    args = parser.parse_args()

    if not args.agents and not args.project:
        parser.print_help()
        sys.stderr.write("\n[错误] 必须显式指定 -a 或 -p，脚本不默认安装任何内容。\n")
        return 1

    rc = 0
    if args.agents:
        rc |= install_agents()
    if args.project:
        rc |= install_project(args.project)

    if rc == 0:
        log("\n完成。请重启 opencode 使配置生效。")
    return rc


if __name__ == "__main__":
    sys.exit(main())
