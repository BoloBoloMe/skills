# Pi 模型配置与密钥

`models.json` 只保存入口/模型声明和环境变量引用, 不保存密钥明文, 同步时也不展开环境变量.

| provider | `apiKey` | Pi 启动前须设置 |
| --- | --- | --- |
| `cli` (CLIProxyAPI) | `$CLIPROXYAPI_KEY` | `CLIPROXYAPI_KEY` |
| `ai-work-deepseek` | `$CHANG_ZHI_AI_WORK` | `CHANG_ZHI_AI_WORK` |

Pi 支持 `$NAME`/`${NAME}`. 不要只写 `NAME`, 它会被当作密钥字面值. 变量未设置时无法认证, 不应改回明文或通过 `/login` 另存一份密钥. 已有 `auth.json` 中的同 provider 凭据优先于 `models.json`, 须先核对并通过 `/logout` 移除旧凭据, 才能保证使用环境变量; 不要直接清空其他 provider 的认证数据.

## 不写密钥进命令历史的临时设置

在将要启动 Pi 的 Bash 中执行, 从隐藏输入读取 Key, 不把值写在命令行中:

```bash
set +x
IFS= read -r -s -p 'CLIProxyAPI Key: ' CLIPROXYAPI_KEY
printf '\n'
export CLIPROXYAPI_KEY
pi
# Pi 退出后, 不再需要时清除本 shell 的副本.
unset CLIPROXYAPI_KEY
```

环境变量必须存在于启动 Pi 的父进程中. 从 Herdr/桌面启动时, 要由启动 Herdr/桌面的进程或服务注入; 另一个终端的 `export` 不会更新已经运行的进程. 改环境后须重新启动相应进程, 只执行 `/reload` 不会获得父进程的新环境.

需要跨登录持久保存时, 交给系统凭据管理器或受保护的启动服务, 在启动时注入变量. 不把 Key 写进仓库, shell 启动脚本, `/etc/environment`, `env.conf` 或 `models.json`; 不用 `echo`/`printenv`/`env` 检查密钥值. 环境变量不是加密或同账户进程之间的隔离, agent 及其子进程仍能读取, 调试日志/环境转储也可能泄漏.

## sandbox 容器

`use-sandbox-worktree` 的 CLIProxyAPI 模板不使用这份宿主模型配置. 容器三个客户端统一读取 `SWT_AGENT_CLIENT_KEY`, 固定启动入口从一份私有共享凭据文件注入进程环境, 不需要手工 `export`/source, 也不把宿主 `CLIPROXYAPI_KEY` 经 `podman create -e` 传入容器. 详见 [模板凭据与验收边界](../workflow/use-sandbox-worktree/reference/agent-templates.md#凭据与验收边界).

## 已提交明文的处理

同步配置前先确认新启动环境已设置变量. 同步工具会将旧 `models.json` 备份为 `models.json.bak`, 其中可能仍含旧明文, 也须按凭据处理.

删除当前文件中的明文不会清除 Git 历史或已有克隆. 旧 Key 若曾提交, 应在中转站轮换客户端 Key, 再更新受保护的凭据来源/启动环境; 不在提交说明或日志里复述旧值. 环境变量配置修改不自动轮换旧 Key, 也不追溯修改已创建容器的固定凭据.
