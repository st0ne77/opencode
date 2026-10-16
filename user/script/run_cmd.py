#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一命令执行器：读命令文件执行，统一 UTF-8 输出。

用法:
    python .opencode/script/run_cmd.py [命令文件名]

说明:
    - 部署在各业务项目的 .opencode/script/run_cmd.py。
    - 命令文件与执行器同目录（<项目>/.opencode/script/）。
    - 不传参数：读 cmd.txt（主代理默认）。
    - 传参数：读 <参数>，例如 cmd_attack.txt；用于**多子代理并行**时各用独立命令文件，
      避免多个代理读写同一个 cmd.txt 互相覆盖。
    - 参数只取文件名 basename（禁止路径），可省略 .txt。
    - 命令以**业务项目根**（.opencode 的上级目录）为 cwd 执行。

可选:
    stdin 文件  与命令文件同源派生，存在时作为子进程 stdin（一次性投喂）：
                cmd.txt -> input.txt；cmd_<名字>.txt -> input_<名字>.txt
    环境变量 RUN_CMD_TIMEOUT  超时秒数，默认 600；0 表示不限制
"""

import os
import signal
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

IS_WINDOWS = os.name == "nt"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _resolve_files(argv):
    """决定本次要读的命令文件与 stdin 文件。

    - 无参数：cmd.txt / input.txt（主代理默认）。
    - 有参数：<basename(argv[1])>，缺 .txt 自动补；stdin 文件按前缀派生：
      cmd_<名字>.txt -> input_<名字>.txt，其它 -> input.txt。
    多子代理并行时各自传入 cmd_<名字>.txt，读写互不覆盖。
    """
    name = "cmd.txt"
    if len(argv) > 1 and argv[1].strip():
        name = os.path.basename(argv[1].strip())
        if not name.endswith(".txt"):
            name += ".txt"
    cmd_file = os.path.join(SCRIPT_DIR, name)

    if name.startswith("cmd_") and name.endswith(".txt"):
        input_name = "input_" + name[len("cmd_"):]
    else:
        input_name = "input.txt"
    input_file = os.path.join(SCRIPT_DIR, input_name)
    return cmd_file, input_file, name


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
        sys.stderr.write("\n[run_cmd] 超时(%ss)已终止整棵进程树: %s\n" % (timeout_arg, line))
        return 124

    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return proc.returncode


def main() -> int:
    cmd_file, input_file, name = _resolve_files(sys.argv)

    if not os.path.isfile(cmd_file):
        sys.stderr.write("[run_cmd] 缺少命令文件: %s\n" % cmd_file)
        return 2

    with open(cmd_file, "r", encoding="utf-8") as f:
        cmd = f.read().strip()

    if not cmd:
        sys.stderr.write("[run_cmd] %s 为空\n" % name)
        return 2

    lines = [ln.strip() for ln in cmd.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        sys.stderr.write("[run_cmd] %s 无有效命令\n" % name)
        return 2

    stdin_data = None
    if os.path.isfile(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
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
