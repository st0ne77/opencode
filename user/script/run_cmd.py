#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一命令执行器：读 cmd.txt 执行，统一 UTF-8 输出。

用法:
    python .opencode/script/run_cmd.py

说明:
    - 部署在各业务项目的 .opencode/script/run_cmd.py。
    - cmd.txt / input.txt 与执行器同目录（<项目>/.opencode/script/）。
    - 命令以**业务项目根**（.opencode 的上级目录）为 cwd 执行。

可选:
    input.txt  存在时，其内容作为子进程 stdin（一次性投喂）
    环境变量 RUN_CMD_TIMEOUT  超时秒数，默认 600；0 表示不限制
"""

import os
import signal
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CMD_FILE = os.path.join(SCRIPT_DIR, "cmd.txt")
INPUT_FILE = os.path.join(SCRIPT_DIR, "input.txt")

IS_WINDOWS = os.name == "nt"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _kill_tree(proc) -> None:
    """强制杀掉整个进程树（含孙进程），避免后台子进程残留。"""
    if proc.poll() is not None:
        return
    if IS_WINDOWS:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _run_one(line: str, stdin_data) -> int:
    """执行单条命令，超时则杀掉整棵进程树。返回退出码（超时为 124）。"""
    popen_kwargs = dict(
        shell=True,
        cwd=PROJECT_DIR,
        stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if IS_WINDOWS:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen(line, **popen_kwargs)

    try:
        out, err = proc.communicate(input=stdin_data, timeout=timeout_arg)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=5)
        except Exception:
            out, err = "", ""
        if out:
            sys.stdout.write(out)
        if err:
            sys.stderr.write(err)
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stderr.write("\n[run_cmd] 超时(%ss)已终止整棵进程树: %s\n" % (timeout, line))
        return 124

    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return proc.returncode


def main() -> int:
    if not os.path.isfile(CMD_FILE):
        sys.stderr.write("[run_cmd] 缺少 cmd.txt: %s\n" % CMD_FILE)
        return 2

    with open(CMD_FILE, "r", encoding="utf-8") as f:
        cmd = f.read().strip()

    if not cmd:
        sys.stderr.write("[run_cmd] cmd.txt 为空\n")
        return 2

    lines = [ln.strip() for ln in cmd.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        sys.stderr.write("[run_cmd] cmd.txt 无有效命令\n")
        return 2

    stdin_data = None
    if os.path.isfile(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            stdin_data = f.read()

    try:
        timeout = int(os.environ.get("RUN_CMD_TIMEOUT", "600"))
    except ValueError:
        timeout = 600
    global timeout_arg
    timeout_arg = None if timeout <= 0 else timeout

    multi = len(lines) > 1
    returncode = 0
    for idx, line in enumerate(lines):
        if multi:
            sys.stdout.write("[%d/%d] %s\n" % (idx + 1, len(lines), line))
            sys.stdout.flush()
        code = _run_one(line, stdin_data if idx == 0 else None)
        if code == 124:
            return 124
        returncode = code

    return returncode


if __name__ == "__main__":
    sys.exit(main())
