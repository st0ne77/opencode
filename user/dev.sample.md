# 本地开发环境配置示例（dev.sample.md）

> 本文件是**示例模板**，随仓库一起提交与安装。
> 使用方式：把本文件复制为同目录下的 `dev.md`，填入本机真实值。`dev.md` 不入库。
> `dev.md` 可能不存在，agent 读取失败时应静默跳过，不报错、不重试。

## MySQL（局域网测试库）
- host: 192.168.x.x
- port: 3306
- user: dev_user
- password: <本地私密，勿提交>
- database: test_db
- 用途: 本地资源有限，部署/功能验证时连该库

## Docker（局域网）
- 远程主机: ssh://user@192.168.x.x
- 方式: docker context over SSH（不开 2375 明文端口）
