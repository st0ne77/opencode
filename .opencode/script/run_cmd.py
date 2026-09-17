#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一命令执行器：读 cmd.txt 执行，统一 UTF-8 输出。

用法:
    python .opencode/script/run_cmd.py

可选:
    input.txt  存在时，其内容作为子进程 stdin（一次性投喂）
    环境变量 RUN_CMD_TIMEOUT  超时秒数，默认 600；0 表示不限制
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CMD_FILE = os.path.join(SCRIPT_DIR, "cmd.txt")
INPUT_FILE = os.path.join(SCRIPT_DIR, "input.txt")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if not os.path.isfile(CMD_FILE):
        sys.stderr.write("[run_cmd] 缺少 cmd.txt: %s\n" % CMD_FILE)
        return 2

    with open(CMD_FILE, "r", encoding="utf-8") as f:
        cmd = f.read().strip()

    if not cmd:
        sys.stderr.write("[run_cmd] cmd.txt 为空\n")
        return 2

    stdin_data = None
    if os.path.isfile(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            stdin_data = f.read()

    try:
        timeout = int(os.environ.get("RUN_CMD_TIMEOUT", "600"))
    except ValueError:
        timeout = 600
    timeout_arg = None if timeout <= 0 else timeout

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=PROJECT_DIR,
            input=stdin_data,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_arg,
        )
    except subprocess.TimeoutExpired as exc:
        if exc.stdout:
            sys.stdout.write(exc.stdout)
        if exc.stderr:
            sys.stderr.write(exc.stderr)
        sys.stderr.write("\n[run_cmd] 超时(%ss)已终止\n" % timeout)
        return 124

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
