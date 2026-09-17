#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""opencode-config 跨平台安装脚本。

用法:
    python install.py -a                     # 安装用户级 AGENTS.md
    python install.py -p <项目根目录>         # 安装项目级 opencode.json + run_cmd.py
    python install.py -a -p <项目根目录>      # 两者都安装
    python install.py                        # 打印用法

说明:
    -a/--agents   复制 <repo>/AGENTS.md 到 ~/.config/opencode/AGENTS.md（已存在则备份 .bak）
    -p/--project  在 <项目根>/.opencode/script/ 下部署 run_cmd.py，
                  并把 opencode.json 复制到 <项目根>/opencode.json

Windows 与 Linux 通用；用户配置目录统一为 ~/.config/opencode。
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
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


def install_agents() -> int:
    src = REPO_DIR / "AGENTS.md"
    if not src.is_file():
        sys.stderr.write("[错误] 仓库中缺少 AGENTS.md: %s\n" % src)
        return 1
    dst = USER_CONFIG_DIR / "AGENTS.md"
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    backup_if_exists(dst)
    shutil.copy2(src, dst)
    log("已安装用户级 AGENTS.md -> %s" % dst)
    return 0


def install_project(project: str) -> int:
    root = Path(project).expanduser().resolve()
    if not root.is_dir():
        sys.stderr.write("[错误] 项目目录不存在: %s\n" % root)
        return 1

    runner_src = REPO_DIR / ".opencode" / "script" / "run_cmd.py"
    if not runner_src.is_file():
        sys.stderr.write("[错误] 仓库中缺少 run_cmd.py: %s\n" % runner_src)
        return 1
    runner_dst = root / ".opencode" / "script" / "run_cmd.py"
    runner_dst.parent.mkdir(parents=True, exist_ok=True)
    backup_if_exists(runner_dst)
    shutil.copy2(runner_src, runner_dst)
    log("已安装命令执行器 -> %s" % runner_dst)

    config_src = REPO_DIR / "opencode.json"
    if not config_src.is_file():
        sys.stderr.write("[错误] 仓库中缺少 opencode.json: %s\n" % config_src)
        return 1
    config_dst = root / "opencode.json"
    backup_if_exists(config_dst)
    shutil.copy2(config_src, config_dst)
    log("已安装项目级配置 -> %s" % config_dst)
    return 0


def main() -> int:
    _force_utf8_stdio()
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="opencode-config 跨平台安装脚本（必须显式指定安装项，不默认安装任何内容）",
        add_help=True,
    )
    parser.add_argument(
        "-a", "--agents", action="store_true",
        help="安装用户级 AGENTS.md 到 ~/.config/opencode/AGENTS.md",
    )
    parser.add_argument(
        "-p", "--project", metavar="DIR",
        help="安装项目级配置到指定项目根目录（opencode.json + .opencode/script/run_cmd.py）",
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
