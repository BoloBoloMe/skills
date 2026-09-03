# Podman rootless 镜像元数据调研

日期: 2026-09-03

环境: Podman 5.7.0, Buildah 1.42.1, linux/amd64. `podman info --format '{{.Host.Security.Rootless}}'` 输出 `true`, 因此以下结论来自 rootless 模式。

实验约定: 测试镜像和容器使用独立的临时存储 `/tmp/podman-sandbox-meta-root` 和 `/tmp/podman-sandbox-meta-run`, 不污染用户默认镜像存储。报告中的长哈希、路径和时间来自本次实测, 只摘录关键部分。

## 1. Image labels

### 结论

Podman 原生支持在构建阶段写入 image label, 来源可以是 Containerfile 的 `LABEL` 或 `podman build --label`. label 保存在 OCI image config 中, 可用 `podman image inspect --format` 读取, 也可由 `podman images --filter label=...` 按 key 或 key/value 查询。

label 是适合记录镜像构建事实的载体, 例如项目标识、构建输入摘要、工具链 profile、SBOM 地址或内容清单摘要。它不是内容证明: label 中写 `git,jdk,node` 不会自动验证镜像里确实有这些工具。

### 实测证据

1. 同时使用 Containerfile `LABEL` 和 build `--label`:

```text
$ podman ... build --tag localhost/sandbox-meta-project-a:v1 \
    --label com.example.sandbox.project=sandbox-project-a \
    --label com.example.sandbox.version=2026.09.05 ...
STEP 2/3: LABEL ... com.example.sandbox.version='from-containerfile'
STEP 3/3: LABEL ... com.example.sandbox.version="2026.09.05" ...
COMMIT localhost/sandbox-meta-project-a:v1
Successfully tagged localhost/sandbox-meta-project-a:v1
```

读取结果:

```text
Labels=map[
  com.example.sandbox.contents:git,jdk,node
  com.example.sandbox.project:sandbox-project-a
  com.example.sandbox.source:workspace/project-a
  com.example.sandbox.version:2026.09.05
  io.buildah.version:1.42.1
  org.opencontainers.image.description:test image]
```

同名 key 的 build `--label` 覆盖了 Containerfile 中的值, 例如 `com.example.sandbox.version` 从 `from-containerfile` 变为 `2026.09.05`。这适合由编排器在 build 时注入项目上下文, 但应避免把未审计的命令行值误当成镜像内容事实。

2. 查询过滤:

```text
$ podman images --filter label=com.example.sandbox.project=sandbox-project-a
localhost/sandbox-meta-project-a|v1|sha256:b05426920816...

$ podman images --filter label=com.example.sandbox.project
localhost/sandbox-meta-inspect|v1|sha256:05863a508c1c...
localhost/sandbox-meta-project-a|patched|sha256:6ff119ce1428...
localhost/sandbox-meta-project-a|v1|sha256:b05426920816...

$ podman images --filter label=com.example.sandbox.project=does-not-exist
# 无输出

$ podman images --filter label!=com.example.sandbox.project=sandbox-project-a
localhost/sandbox-meta-inspect:v1|sha256:05863a508c1c...
```

`label=key` 匹配存在该 key 的镜像, `label=key=value` 匹配 key 和值; `label!=...` 可反向筛选。一个镜像有多个 tag 时, 过滤结果会按引用显示同一镜像的多个名字。

3. 已有镜像追加/修改 label:

```text
$ podman image --help
... build ... inspect ... tag ... untag ...
# 没有 image label set/update 命令

$ podman commit --change 'LABEL com.example.sandbox.version=patched' \
    --change 'LABEL com.example.sandbox.extra=commit-created' \
    sandbox-meta-commit-src localhost/sandbox-meta-project-a:patched
committed_image_id=6ff119ce1428...

original:
... id=b05426920816... digest=sha256:94ed42399013... \
labels=...version:2026.09.05...
committed:
... id=6ff119ce1428... digest=sha256:39d3681c8f35... \
labels=...version:patched ... extra:commit-created...
```

结论是已有镜像的原对象不能原地改 label。`podman image tag` 只能添加引用, 不改 image config; 需要 `podman build` 重建, 或从容器 `podman commit --change LABEL` 生成一个新 image ID 和新 digest。后者还可能携带容器文件系统变化, 不应作为普通元数据更新的首选。

4. key/value 字符集和长度探测:

本次 Podman 5.7 rootless 本地 OCI 存储实测接受了以下 label:

```text
key=""                         -> accepted, value=""
key="key with space"           -> accepted
key="key:colon"                -> accepted
key="key@at"                   -> accepted
key="key..dots"                -> accepted
key="key/value"                -> accepted
value="v=with=equals"          -> accepted, 等号保留在 value 中
key/value 含中文                 -> accepted
value 含换行                    -> 存储/JSON 呈现为转义换行
key length=1024                -> accepted
value length=65536             -> accepted
```

代表性输出:

```text
spec='key with space=v' ACCEPT {"key with space":"v"}
spec='key/value=v' ACCEPT {"key/value":"v"}
spec='key=v=with=equals' ACCEPT {"key":"v=with=equals"}
value_length=65536 result=ACCEPT
```

Podman 的 build help 只定义输入为 `label=value`, 可重复使用, 未给出 key/value 的 Podman 数值长度上限; 现有 image inspect man page 将 Labels 描述为 label map, 也未列出长度上限。因此不能把常见 Docker/OCI 命名建议当成 Podman 实现的硬上限。本次只能确认上述输入范围在本机版本可用, 不能据此声称任意超大值都可用。

实践上仍应主动采用可移植格式: ASCII 小写命名空间加 `/`, 例如 `io.example.sandbox.project-id`; value 使用 UTF-8 JSON 字符串可表达的短值, 长清单放外部文件并在 label 中存摘要或引用。不要依赖本地 Podman 接受的空 key、空格、中文 key 或大值, 因为推送到 registry、转换 Docker 格式、其他引擎和工具可能收紧限制。label key/value 属于元数据, 不适合放凭据。

### 限制和文档出处

- `man podman-build`, `--label`: build label 是 image metadata, 可重复; `--inherit-labels` 默认继承 base image labels; `--unsetlabel` 可在重新 build 时取消继承, 见 `/usr/share/man/man1/podman-build.1.gz` 的 `--label`、`--inherit-labels`、`--unsetlabel` 条目。
- `man podman-images`, `--filter`: 支持 `label=key`, `label=key=value`, `label!=key`, `label!=key=value`, 见 `/usr/share/man/man1/podman-images.1.gz` 的 `--filter` 条目。
- `man podman-image-prune`: image prune 也支持 label filter, 但只是在候选集上再筛选, 不会把 label 变成保留锁, 见 `/usr/share/man/man1/podman-image-prune.1.gz` 的 `--filter` 条目。

## 2. `podman image inspect` 可读到什么

### 结论

`podman image inspect` 给出本地镜像对象的低层信息, 足以做启动前预检和一致性核对, 但不是软件内容清单。Podman 5.7 本次 inspect 的顶层字段如下, 字段随 manifest 类型和 Podman 版本可能为空或变化:

| 字段 | 作用和预检价值 |
| --- | --- |
| `Id` | 本地 image ID, 内容配置变化后会变化 |
| `Digest` | manifest digest, 适合作为精确不可变版本 |
| `RepoTags` | 当前本地 repository:tag 引用列表 |
| `RepoDigests` | repository@digest 引用列表, 有 registry/repository 语境时才一定有意义 |
| `Parent` | 父 image ID, 可辅助判断构建关系 |
| `Comment` | image comment |
| `Created` | 创建时间, 可做新鲜度或缓存策略判断 |
| `Config` | 运行配置: `User`, `ExposedPorts`, `Env`, `Entrypoint`, `Cmd`, `Volumes`, `WorkingDir`, `Labels` 等 |
| `Version` | image version 字段, 本次 scratch 构建为空, 不能当可靠构建版本 |
| `Author` | image author |
| `Architecture`, `Os` | 平台预检, 防止在错误架构/系统上运行 |
| `Size`, `VirtualSize` | 镜像占用/虚拟大小, 可做磁盘配额和成本预检 |
| `GraphDriver` | 存储驱动及本地路径数据, 可诊断但不适合作为跨机器事实 |
| `RootFS` | `Type` 和 `Layers` 的 rootfs 层信息, 可做层/父镜像核对 |
| 顶层 `Labels` | image config labels 的便捷副本, 适合查项目/构建元数据 |
| `Annotations` | manifest annotations, 与 labels 不同; 适合 OCI manifest 层面的声明 |
| `ManifestType` | OCI/Docker manifest 类型预检 |
| `User` | 默认运行用户, 与 `Config.User` 同类信息 |
| `History` | 每个构建历史条目的 `created`, `created_by`, `comment`, `empty_layer` 等 |
| `NamesHistory` | 曾经绑定过的镜像名字历史, 可辅助诊断 retag/untag |

### 实测证据

使用一个含 `ENV`, `WORKDIR`, `USER`, `ENTRYPOINT`, `CMD`, `EXPOSE`, `VOLUME` 的 scratch 镜像:

```text
$ podman image inspect localhost/sandbox-meta-inspect:v1
{
  "Id": "05863a508c1c...",
  "Digest": "sha256:2795242497a7...",
  "RepoTags": ["localhost/sandbox-meta-inspect:v1"],
  "RepoDigests": ["localhost/sandbox-meta-inspect@sha256:279524..."],
  "Created": "2026-09-03T05:21:20.269222582Z",
  "Config": {
    "User": "1000",
    "ExposedPorts": {"8080/tcp": {}},
    "Env": ["PATH=...", "APP_MODE=preflight", "APP_VERSION=42"],
    "Entrypoint": ["/bin/agent"],
    "Cmd": ["--serve"],
    "Volumes": {"/data": {}},
    "WorkingDir": "/workspace",
    "Labels": {"com.example.sandbox.project": "sandbox-project-b", ...}
  },
  "Architecture": "amd64",
  "Os": "linux",
  "Size": 4298,
  "VirtualSize": 4298,
  "RootFS": {"Type": "layers", "Layers": ["sha256:5ce760..."]},
  "ManifestType": "application/vnd.oci.image.manifest.v1+json",
  "History": [{"created": "...", "created_by": "... ENV ..."}, ...],
  "NamesHistory": ["localhost/sandbox-meta-inspect:v1"]
}
```

另一镜像的格式化读取也确认 `Labels`, `Created`, `Digest`, `Size`, `VirtualSize`, `ManifestType`, `Config`, `RootFS`, `History`, `RepoTags`, `RepoDigests` 都可由 Go template 访问:

```text
ID=b05426920816...
Digest=sha256:94ed42399013...
Created=2026-09-03 05:18:50.65535408 +0000 UTC
Size=1863
VirtualSize=1863
ManifestType=application/vnd.oci.image.manifest.v1+json
Labels=map[com.example.sandbox.project:sandbox-project-a ...]
RootFS={layers []}
History=[{... LABEL ...} {... LABEL ...}]
```

### 适合 sandbox-worktree 的预检

建议在创建容器前至少核对:

1. `Digest` 或 `Id`: 是否是编排记录的精确镜像, 避免同 tag 被重新指向后静默换镜像。
2. `Labels`: `project-id`, image schema/version, toolchain profile, contents manifest digest 等是否匹配。
3. `Architecture`, `Os`, `ManifestType`: 是否符合宿主/运行时预期。
4. `Config.Env`, `Entrypoint`, `Cmd`, `WorkingDir`, `User`, `ExposedPorts`, `Volumes`: 是否满足启动契约。
5. `Size`, `RootFS.Layers`: 是否超过资源预算或与预期层结构明显不符。
6. `Created`: 是否满足缓存新鲜度策略。

`History` 只适合诊断构建来源, `GraphDriver.Data` 含本地 storage 路径, `Version` 经常为空, 不应作为项目版本或跨主机身份。`RootFS.Layers` 是层摘要, 不是 `/usr/bin` 文件列表、包列表或 SBOM。若“内容物有什么”要求可验证, 应在构建时生成 SBOM/工具版本清单, 用 OCI label 记录其摘要和外部路径, 或把清单作为独立签名制品。

### 文档出处

完整字段清单和示例来自本机 `man podman-image-inspect`, `/usr/share/man/man1/podman-image-inspect.1.gz`, `--format` 的 placeholders 和 EXAMPLE 段。该手册明确列出 `.Annotations`, `.Architecture`, `.Config`, `.Created`, `.Digest`, `.GraphDriver`, `.History`, `.ID`, `.Labels`, `.ManifestType`, `.NamesHistory`, `.Os`, `.Parent`, `.RepoDigests`, `.RepoTags`, `.RootFS`, `.Size`, `.User`, `.Version`, `.VirtualSize`。

## 3. 镜像命名和 tag 策略

### 结论

本地镜像引用可以采用 `localhost/<name>:<tag>`. `name` 是 repository 路径, 可包含多个 `/`; `tag` 是同一 image 的可变人类别名。项目标识和构建版本可以部分编码进 name/tag, 但它们不是完整、不可变的元数据模型:

- name/tag 适合人读、补全和按引用定位。
- digest 才是内容身份; tag 可被重建或重新指向。
- 复杂项目路径需要规范化或 hash, 不能原样照搬所有文件系统字符。
- 必须保留至少一个稳定 tag 才能避免镜像成为 dangling image, 但稳定 tag 会带来覆盖语义。

### 实测证据: 路径和字符

```text
nested-name localhost/sandbox-worktree/project-a:v1       ACCEPT
uppercase-name localhost/Sandbox-Worktree:v1              REJECT: repository name must be lowercase
name-underscore localhost/sandbox_worktree:v1             ACCEPT
name-dot localhost/sandbox.worktree:v1                    ACCEPT
name-plus localhost/sandbox+worktree:v1                   REJECT: invalid reference format
name-leading-dash localhost/-sandbox:v1                   REJECT: invalid reference format
```

因此项目路径 `/home/bolo/Workspace/project-a` 应先转为约定 slug, 例如 `project-a`, 或转为稳定编码/hash; 可以使用 `sandbox-worktree/project-a` 这样的 repository 层级, 但不能把任意绝对路径直接当 name。

本地参考解析的额外规则来自 `man containers-transports`, `/usr/share/man/man5/containers-transports.5.gz`: 不带 slash 的 name 默认按 `docker.io/library/name` 解释; 含 slash 时, 第一个组件只有包含 `.`、`:` 或恰为 `localhost` 才被当 registry, 否则按 `docker.io/name` 解释。因此本方案使用显式 `localhost/` 可避免短名和远端 registry 解析歧义。

### 实测证据: 长度和 tag 字符

```text
name component length=245 with localhost/  ACCEPT
name component length=246 with localhost/  REJECT: repository name must not be more than 255 characters

tag length=128                                  ACCEPT
tag length=129                                  REJECT: invalid reference format
tag=V1.2_RC                                    ACCEPT
tag=v1+build                                   REJECT: invalid reference format
tag=v1/build                                    REJECT: invalid reference format
```

这里的 245/246 是在 `localhost/<single-component>` 下探测的: Podman 报告 repository name 总长度上限 255, `localhost/` 占 10 个字符, 所以该形态的单一 name component 可用长度最多为 245。tag 的本机实测上限为 128 字符。采用 `localhost/<project-slug>:<version>` 时, 应为前缀和多路径段预留长度, 不应把版本完整描述或大 JSON 塞进 tag。

### 实测证据: tag 可变, digest 不可变引用

同一镜像增加 alias:

```text
$ podman image tag localhost/sandbox-meta-project-a:v1 localhost/sandbox-meta-project-a:alias
localhost/sandbox-meta-project-a|alias|sha256:b05426920816...|sha256:94ed42399013...
localhost/sandbox-meta-project-a|v1|sha256:b05426920816...|sha256:94ed42399013...
```

通过 digest 引用同一对象:

```text
$ podman image inspect localhost/sandbox-meta-project-a@sha256:94ed42399013... \
    --format 'digest-ref={{.Id}} {{.Digest}} {{.RepoTags}}'
digest-ref=b05426920816... sha256:94ed42399013... [localhost/sandbox-meta-project-a:alias ... localhost/sandbox-meta-project-a:v1]
```

同一 tag 重新 build:

```text
first_id=9ad715a74ff2... first_digest=sha256:9861be00c24...
second_id=dcebe09da82... second_digest=sha256:c7cdb0b690f5...
all mutable-name records:
localhost/sandbox-tag-mutable|v1|sha256:dcebe09da82...|... version:two
```

所以 `:v1` 表示“当前这个名字指向的版本”, 不是第一次构建的永久身份; 编排记录应保存 digest, tag 只作为选择/展示别名。

### 实测证据: untag 和 prune

```text
$ podman image untag localhost/sandbox-prune-test:keep
$ podman images --all --filter dangling=true
<none>|<none>|sha256:17831bf9d7d...|map[com.example.sandbox.prune:me ...]

$ podman image prune --force --filter label=com.example.sandbox.prune=me
17831bf9d7d7b9872e3ad5c1c27d99ea44413ceb5...

$ podman image exists localhost/sandbox-prune-test:keep
# exit code 1
```

`podman image prune` 默认清理 dangling 镜像, 即无 tag 的候选; `-a` 会进一步清理没有关联容器的未使用镜像。label filter 只缩小清理范围, 不能防止一个 untagged 镜像被默认 prune。若缓存必须可发现/可保留, 应保留稳定 tag, 并用 digest 做真实版本校验; 定期清理由编排器按 label 和 age 执行。

### 限制和推荐策略

推荐:

```text
localhost/sandbox-worktree/<project-slug>:<human-version>
```

并在 image labels 记录:

```text
io.example.sandbox.project-id=<canonical-id>
io.example.sandbox.schema-version=1
io.example.sandbox.contents-digest=sha256:...
io.example.sandbox.build-id=<build-id>
```

项目路径到 slug 的映射必须稳定、可逆性要求明确、冲突检测必须存在。路径中的 `/` 可以作为 repository 层级, 但绝对路径、大小写、特殊字符、过长路径、不同路径归一化后同名等都可能造成冲突。真正的内容版本使用 digest, tag 只承载人类版本/缓存选择。

### 文档出处

- `man podman-tag`, `/usr/share/man/man1/podman-tag.1.gz`: image reference 是完整 name 加可选 tag; 未提供 tag 时默认 `latest`; 一个 image 可以有多个 tag。
- `man containers-transports`, `/usr/share/man/man5/containers-transports.5.gz`: reference 形态为 `name[:tag | @digest]`, registry/name 解析规则, digest 可用于 destination/reference。
- `man podman-image-prune`, `/usr/share/man/man1/podman-image-prune.1.gz`: 默认 dangling, `-a` 清理没有关联容器的 unused images, 支持 label/until filter。

## 4. 容器侧 label 机制

### 结论

`podman create/run --label key=value` 可以设置容器 metadata, `podman ps --filter label=key` 或 `label=key=value` 可以过滤。创建容器时, image labels 会继承到容器 labels; 若 `create/run --label` 指定同名 key, 容器值覆盖 image 值。容器 label 是记录具体 sandbox-worktree 身份的合适载体, 因为一个 image 可以被多个 worktree/container 复用。

建议至少设置:

```text
io.example.sandbox.identity=<stable-sandbox-id>
io.example.sandbox.project-id=<canonical-project-id>
io.example.sandbox.worktree-path=<absolute-worktree-path>
io.example.sandbox.image-digest=sha256:...
```

其中 stable sandbox ID 用于程序关联, path 用于人工诊断。path 可能因宿主迁移而变化, 不应单独作为主键。

### 实测证据: create/run 设置和继承

创建一个只带 image labels 的容器:

```text
$ podman create --name sandbox-meta-inherit localhost/sandbox-meta-project-a:v1 /bin/sh
$ podman container inspect sandbox-meta-inherit --format 'image={{.ImageName}} labels={{.Config.Labels}}'
image=localhost/sandbox-meta-project-a:v1 labels=map[
  com.example.sandbox.project:sandbox-project-a
  com.example.sandbox.contents:git,jdk,node
  com.example.sandbox.version:2026.09.05 ...]
```

创建时增加并覆盖 label:

```text
$ podman create --name sandbox-meta-explicit \
    --label com.example.sandbox.project=container-project \
    --label com.example.sandbox.worktree=/home/bolo/Workspace/skills/project-a \
    --label com.example.sandbox.identity=sandbox-worktree/project-a \
    localhost/sandbox-meta-project-a:v1 /bin/sh
$ podman container inspect sandbox-meta-explicit --format ...
... com.example.sandbox.project:container-project ...
... com.example.sandbox.worktree:/home/bolo/Workspace/skills/project-a ...
... com.example.sandbox.identity:sandbox-worktree/project-a ...
```

这里 image 的 `com.example.sandbox.project=sandbox-project-a` 被容器值 `container-project` 覆盖, 其他 image labels 仍保留。

运行态 `run --label`:

```text
$ podman run -d --name sandbox-meta-run \
    --label com.example.sandbox.identity=sandbox-worktree/run-demo \
    --label com.example.sandbox.worktree=/home/bolo/Workspace/skills/demo \
    --label com.example.sandbox.project=run-project \
    ubuntu:24.04 sleep 30
run_container_id=554c36397716...
state=running image=docker.io/library/ubuntu:24.04 labels=map[
  com.example.sandbox.identity:sandbox-worktree/run-demo
  com.example.sandbox.project:run-project
  com.example.sandbox.worktree:/home/bolo/Workspace/skills/demo
  org.opencontainers.image.version:24.04]
```

过滤:

```text
$ podman ps --filter label=com.example.sandbox.identity=sandbox-worktree/run-demo
sandbox-meta-run|Up 1 second|map[... identity:sandbox-worktree/run-demo ...]

$ podman ps --all --filter label=com.example.sandbox.project=sandbox-project-a
sandbox-meta-inherit|...|map[... project:sandbox-project-a ...]
```

`podman ps` 默认只看 running containers, 查已停止或仅 `create` 的容器要加 `--all`。同 key 的 label filter 按文档是特殊的 exclusive 行为, 多个不同 key 通常交集过滤; 实现查询时应使用精确 key/value, 避免把完整 map 的展示文本当接口。

### 限制

- 容器 label 不会回写 image; 容器专属的 worktree path/identity 不应写入 image label。
- label 只是本地 metadata, 不提供认证、访问控制、不可篡改保证; 能操作 Podman 存储的用户可以删除/重建容器并改值。
- path 可能含空格、中文或迁移后失效, 程序主关联应使用规范化 stable ID, path 作为辅助信息。
- 容器删除后 label 也随容器对象删除, 需要跨生命周期追踪时应在外部 state/事件日志保留记录。
- `--label` 与 SELinux 的 `--security-opt label=...` 是两个不同概念: 前者是容器 metadata, 后者控制进程/文件的 MAC label。

### 文档出处

- `man podman-create`/`man podman-run`, `/usr/share/man/man1/podman-create.1.gz`、`/usr/share/man/man1/podman-run.1.gz`: `--label, -l=key=value` 是 container metadata, `--label-file` 读取逐行 label。
- `man podman-ps`, `/usr/share/man/man1/podman-ps.1.gz`: label filter 支持 `[Key]` 或 `[Key=Value]`, `.Label`/`.Labels` 可用于输出, 示例为 `podman ps --filter label=app=frontend`。
- 本次 `podman container inspect` 实测验证继承和同名覆盖, 不仅依赖文档描述。

## 汇总建议

| 事实 | 推荐载体 | 一句话理由 |
| --- | --- | --- |
| 项目标识 | image label `io.example.sandbox.project-id`, name 中保留短 slug | label 可按 key/value 查询, name 只做可读索引且受字符/长度规则约束 |
| 内容物清单 | 外部 SBOM/工具清单制品 + image label 中的 `contents-digest`/URI, inspect 读取 `Config.Env` 等启动契约 | inspect 能读配置和层摘要, 不能证明安装文件/包的完整内容 |
| 版本号 | digest 作为精确版本, tag 作为人类版本/缓存别名, 可补 image label 的 schema/build version | tag 可被覆盖, digest 随 manifest 内容固定 |
| sandbox-worktree 身份 | 容器 label `identity`, `project-id`, `worktree-path`, `image-digest`, 必要时外部生命周期 state | 身份属于具体运行实例而非可复用 image, `podman ps --filter label=...` 可直接找回 |

最终建议: image 是带项目构建事实的缓存制品, 由 labels 承载可查询元数据, tag 承载可读索引, digest 承载精确身份, inspect 承载启动前核验, 容器 labels 承载某次 sandbox-worktree 实例身份。长内容清单和跨容器生命周期状态不要硬塞进 label。

## 实验清理

已清理独立临时存储中的测试对象:

```text
$ podman --root /tmp/podman-sandbox-meta-root --runroot /tmp/podman-sandbox-meta-run image rm --all
$ podman --root /tmp/podman-sandbox-meta-root --runroot /tmp/podman-sandbox-meta-run container rm --all --force
$ rm -rf /tmp/podman-sandbox-meta-root /tmp/podman-sandbox-meta-run
```

清理后检查临时 root/runroot 不存在, 默认用户镜像存储仍只保留实验前的对象:

```text
$ podman images --format '{{.Repository}}:{{.Tag}}'
localhost/nettest-tools:latest
docker.io/library/ubuntu:24.04
quay.io/podman/hello:latest
```
