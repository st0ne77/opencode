# GENERAL RULES

1.始终以简体中文输出计划和回复。
2.每次回复都叫我老大。
3.不要假设我清楚自己想要什么，动机或目标不清晰时，停下来讨论。
4.我发出的指令目标清晰但方案不是最佳，直接告诉我并建议更好的办法。
5.遇到问题追根因，不打补丁。每个决策都要能回答"为什么”。
6.不要过度考虑边界，当前项目中不可能出现的边界情况不需要处理。
7.如你认为某个目录为空，**必须**再用dir命令验证一次。
8.先读后写，每次修改文件之前都要重新读取目标文件的最新内容。
10.只读必要的文件
11.如果验证连接的是本地服务，禁止通过端口找进程去读服务源码
12.禁止对wsl进行读写等操作
13.自动测试验证过程中以主要目标为第一目的，中间如果发现其它问题先记录，搞定主要问题后请示我是否需要继续刚才发现的问题

## 统一命令执行协议（最高优先级，覆盖其它所有命令规则）

**所有 shell 命令必须且只能通过 python 通道执行，opencode 权限已硬性拦截其它所有 bash 命令。**

- 唯一被放行的命令是（二选一，先探测哪个可用）：
  - Windows 通常：`python .opencode/script/run_cmd.py`
  - Linux 通常：`python3 .opencode/script/run_cmd.py`
  - **首次使用前先探测**：`python --version` 可用则用 `python`，否则用 `python3`（两者都已在权限中放行）。
  - **路径必须写正斜杠**，与权限配置字面严格一致；写成反斜杠会被拒绝。
  - 不需要、也不允许追加其它参数。
- 执行任何命令的标准两步流程：
  1. 用 write 工具把命令原文写入 `<工作目录>/.opencode/script/cmd.txt`（UTF-8）。
  2. 调用 `python .opencode/script/run_cmd.py`（Linux 用 `python3`）执行。
- 需要向子进程 stdin 提供输入时，用 write 工具把输入内容写入 `<工作目录>/.opencode/script/input.txt`（UTF-8），执行器会一次性投喂。
- `.opencode/script/` 目录或 `run_cmd.py` 不存在时，先用 write 工具创建（write 工具不受 bash 权限限制）。
- 命令原文直接写进 cmd.txt，不要再操心 shell 转义：`$`、`%`、`&`、管道、重定向均可按目标 shell 语法原样书写。
- 交互式命令无法实时双向交互（opencode 不提供实时 stdin 通道），只能把已知输入预置到 input.txt 一次性投喂；需要真实时交互时停下来告知我。
- 常见坑：`echo 中文` 这类由 cmd.exe 内建命令产生的中文，仍可能按 GBK 输出导致乱码；需要输出中文时优先用 python 产生（python 全程 UTF-8）。

### 常驻服务启动规则（禁止死等）

常驻服务（appium、daemon、server 等）**必须"启动即返回"，绝不能让 run_cmd.py 等它退出**。每次现写 python 命令实现，不依赖任何辅助脚本。

- **严禁**会阻塞/继承句柄的写法：
  - ❌ `start "" /b cmd /c "服务 ..."` —— 子进程继承 stdout/stderr 句柄，run_cmd.py 读管道会一直等到服务退出（死等 600 秒）。
  - ❌ 直接前台执行服务程序。
- **正确做法**：cmd.txt 中写一条 python `-c` 命令，用 `Popen` 非阻塞启动，**三个流全部指向空设备**并脱离父进程，例如：

  ```
  python -c "import subprocess,sys;subprocess.Popen(['D:\\path\\appium.cmd','--port','4723'],creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);print('launched')"
  ```

  - 关键点：`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` + `stdin/stdout/stderr=DEVNULL`。
  - Linux 用 `start_new_session=True` 替代 `creationflags`。
- 启动后**立即返回**，随后用独立的短命令检查端口/进程确认服务就绪，再继续后续操作。
- run_cmd.py 对超时**一律杀掉整棵进程树**（Windows `taskkill /F /T`，Linux `killpg`），无需也不允许 AI 自行决定是否杀进程。

## 本地环境配置（dev.md）

`~/.config/opencode/dev.md` 是我本机的开发环境配置（数据库连接、内网服务地址等），**该文件可能不存在**。

- 每次会话开始后，无条件用 Read 工具读取该文件，不要等我提及数据库或环境需求。
- 读取失败（文件不存在）时：静默跳过，不报错、不重试、不询问，按无该配置继续。
- 读取成功时：其中内容视为强制生效的本地配置。
