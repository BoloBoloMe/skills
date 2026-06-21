---
name: springboot-hcurl-generator
description: Spring Boot Controller 到 Hurl/.hcurl 接口测试脚本包的生成流程.
disable-model-invocation: true
---

# SpringBoot Hcurl 脚本包生成

## 目标

从 Spring Boot Controller 源码生成一个可执行的标准 `.hcurl` 脚本包，目录形态固定为：

```text
<输出根目录>/<项目名>/
├─ _env/
│  ├─ local.properties
│  └─ test.properties
├─ <ControllerSimpleName>/
│  └─ <methodName>.hcurl
└─ README.md
```

若工作区已有统一执行脚本，例如 `run-hurl.ps1`，不要重复生成；在 README 中说明使用方式。

## 使用时机

当用户要求“根据 Controller 生成 hcurl / hurl / 接口脚本 / 脚本包 / 接口测试样例”时使用本技能。

## 输入确认

开始前只确认必要信息：

1. Spring Boot 源码目录，默认从当前目录递归查找 `src/main/java`。
2. 输出根目录，默认当前目录。
3. 脚本包项目名，默认取模块目录名；若不确定，使用用户给出的业务名。
4. 是否覆盖已有 `.hcurl`，默认不覆盖，只新增缺失文件。

## Controller 识别

递归扫描 Java 文件，纳入以下类：

- 标注 `@RestController`
- 标注 `@Controller`
- 类或方法存在 Spring MVC 映射注解

识别映射注解：

- `@RequestMapping`
- `@GetMapping`
- `@PostMapping`
- `@PutMapping`
- `@DeleteMapping`
- `@PatchMapping`

URL 由类级映射 + 方法级映射拼接，统一去重 `/`。

## Java 解析降级

优先使用语法级解析或可靠的 IDE/AST 信息. 如果只能用文本解析, 必须显式标记 `解析模式: 文本启发式`, 并采用保守策略:

- 只为能明确识别 HTTP method 和 URL 的方法生成脚本.
- 对复杂注解表达式, 常量拼接, 元注解, 泛型 DTO 字段推断失败的情况, 在 README 的 `解析限制` 中列出.
- 不确定的参数不要编造业务含义, 使用安全占位值并添加注释.
- 解析失败的方法写入跳过清单, 不生成可能误导的 `.hcurl`.

HTTP method 规则：

1. `@GetMapping` 等专用注解直接取对应方法。
2. `@RequestMapping(method = RequestMethod.X)` 取 `X`。
3. 未声明 method 时：有 `@RequestBody` 或明显写操作方法名时用 `POST`，否则用 `GET`。

## 参数生成规则

- `@RequestBody`：生成 JSON body，并加 `Content-Type: application/json`。
- `@RequestParam`：GET 放查询串，POST 无 body 时也可放查询串。
- `@PathVariable`：替换路径变量为示例值，如 `{id}` → `1`。
- `@RequestHeader`：生成请求头，值用 `example`；鉴权头优先写成注释。
- `MultipartFile` / `@RequestPart`：生成 `[MultipartFormData]`。
- 无法推断字段类型时使用安全占位值：字符串 `"example"`，数字 `1`，布尔 `true`，数组 `["example"]`，对象 `{}`。

## .hcurl 文件模板

普通 JSON 接口：

```hurl
# <Controller>.<method>
# Controller: <Controller>
# Method: <method>
# Source: <相对源码路径>:<行号>
# 说明: 示例值需按测试环境替换；如接口受保护，可启用 Authorization 头。
POST {{baseUrl}}/api/path
Accept: application/json
# Authorization: Bearer {{token}}
Content-Type: application/json

{
  "id": 1
}

HTTP 200
[Asserts]
jsonpath "$" exists
jsonpath "$.code" exists
```

GET / 下载 / 非 JSON 接口：

```hurl
GET {{baseUrl}}/api/path?id=1
Accept: application/json
# Authorization: Bearer {{token}}

HTTP 200
[Asserts]
body exists
```

文件上传接口：

```hurl
POST {{baseUrl}}/api/upload
Accept: application/json
# Authorization: Bearer {{token}}

[MultipartFormData]
file: file,./sample-upload-file.bin; application/octet-stream

HTTP 200
[Asserts]
jsonpath "$" exists
jsonpath "$.code" exists
```

## 环境文件

若不存在则生成：

`_env/local.properties`

```properties
baseUrl=http://localhost:8080
token=replace-me
```

`_env/test.properties`

```properties
baseUrl=https://replace-me.example.com
token=replace-me
```

## README 内容

README 必须简短包含：

- 脚本包结构
- `baseUrl`、`token` 变量说明
- hurl 原生命令
- 若存在 `run-hurl.ps1`，给出执行示例
- 说明示例值需替换为真实测试数据

## 执行约束

- 生成前先列出将新增/覆盖的文件清单。
- 默认不覆盖已有 `.hcurl`；需要覆盖时必须得到用户确认。
- 不把真实 token、密钥、生产域名写入脚本。
- 每个 Controller 一个目录，每个 Controller 方法一个 `.hcurl` 文件。
- 文件名使用 Java 方法名；重名时追加短路径或序号避免覆盖。
- 生成完成后汇总 Controller 数、方法脚本数、跳过数、输出路径。

## 生成后校验

完成生成后执行轻量校验, 不要求真实服务在线:

1. 检查每个 `.hcurl` 至少包含请求行, `HTTP 200`, `[Asserts]`.
2. 检查 `_env/local.properties` 和 `_env/test.properties` 均包含 `baseUrl`.
3. 如本机存在 `hurl`, 对每个脚本运行语法校验或 dry-run 级命令; 如果 hurl 版本不支持 dry-run, 记录未执行原因.
4. 如果存在项目统一脚本 `run-hurl.ps1`, 验证 README 中引用的路径存在.

完成标准: 最终汇总包含生成数量, 跳过数量, 校验结果, 未执行校验原因和输出路径.
