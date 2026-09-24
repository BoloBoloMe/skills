"""navigate roadmap 守门脚本: ROADMAP.json 的唯一读写入口 (D002).

CLI commands:
  save   <file> <path> <content>  - 写指定字段; 文件不存在自动初始化顶层结构,
                                    中间节点自动创建; content 先按 JSON 解析,
                                    失败按裸字符串存 (D003)
  delete <file>                   - 删除整个 ROADMAP.json
  query  <file> <path>            - 读指定字段

stdout: single UTF-8 JSON object. Exit 0 success, exit 1 failure.

结构: run_* 是命令核心, 一律返回结果 dict, 不碰 stdout 与 sys.exit.
main() 是薄 CLI 适配器: argv 解析, JSON 序列化, 退出码.
不变量: save 全程 fcntl 锁覆盖 读-改-写, 落盘经临时文件 rename 原子替换 (D007).
path 语义: 点分隔; 数字段为数组下标, == 长度追加, > 长度报错;
里程碑 id 形如 milestone-01 非纯数字, 不按下标解析 (D004).
"""

import fcntl
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

SCHEMA_VERSION = "0.0.1"

TOP_LEVEL_FIELDS = [
    "schema_version", "title", "destination", "notes",
    "milestones", "unknown_seas", "off_course",
]

STATUS_VALUES = ["待处理", "进行中", "已关闭"]
TYPE_VALUES = ["research", "deliberate", "prototype", "task"]

# 新增里程碑用户必填字段 (BR-004); 其余成员字段由默认值补齐
MILESTONE_REQUIRED = ["title", "type", "question"]


# ---------------------------------------------------------------------------
# Result construction (core produces dicts, never prints or exits)
# ---------------------------------------------------------------------------

def _err(command, code, error):
    return {"success": False, "command": command, "code": code, "error": error}


def _success(command, payload):
    return {"success": True, "command": command, **payload}


class _SaveError(Exception):
    """可预期的读写失败, 携带 (code, error) 由 run_* 转为结果 dict."""

    def __init__(self, code, error):
        super().__init__(error)
        self.code = code
        self.error = error


# ---------------------------------------------------------------------------
# Document load / init
# ---------------------------------------------------------------------------

def _initial_document():
    """文件不存在时 save 自动初始化的顶层结构 (D005)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "title": "",
        "destination": "",
        "notes": [],
        "milestones": {},
        "unknown_seas": [],
        "off_course": [],
    }


def _load_document(file_path):
    if not file_path.exists():
        return _initial_document()
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise _SaveError("invalid_json", f"文件不是合法 JSON: {file_path} ({e})")


def _parse_content(raw):
    """content 先按 JSON 解析, 失败按裸字符串存 (D003)."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


# ---------------------------------------------------------------------------
# Lock + atomic write (D007)
# ---------------------------------------------------------------------------

def _lock_file_path(file_path):
    """锁文件放系统临时目录, 按目标文件绝对路径哈希区分, 不弄脏路线图目录."""
    digest = hashlib.sha256(
        str(file_path.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"navigate-roadmap-{os.getuid()}-{digest}.lock"


def _atomic_write_json(file_path, data):
    """写临时文件再 rename 原子替换 (对齐 present _atomic_write_json 先例)."""
    tmp = file_path.with_name(file_path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, file_path)


# ---------------------------------------------------------------------------
# Path resolution (D004)
# ---------------------------------------------------------------------------

def _is_index(segment):
    """数字段 (纯 ASCII 数字) 为数组下标; milestone-01 等 id 不是."""
    return segment.isascii() and segment.isdigit()


def _descend(node, seg, nxt):
    """向下走一层, 缺失的中间节点按下一层段类型自动创建 (dict 或 list)."""
    if isinstance(node, dict):
        if _is_index(seg):
            raise _SaveError("invalid_path", f"数字段 {seg} 仅可用作数组下标")
        if seg not in node:
            node[seg] = [] if _is_index(nxt) else {}
        return node[seg]
    if isinstance(node, list):
        if not _is_index(seg):
            raise _SaveError("invalid_path", f"数组下标必须为数字段: {seg}")
        idx = int(seg)
        if idx > len(node):
            raise _SaveError("index_out_of_bounds",
                             f"数组下标 {idx} 越界 (数组长度 {len(node)})")
        if idx == len(node):
            node.append([] if _is_index(nxt) else {})
        return node[idx]
    raise _SaveError("invalid_path", f"路径途经标量值, 无法继续向下: {seg}")


def _assign(node, seg, value):
    """末段写入: dict 按键, list 按下标 (== 长度追加, > 长度报错)."""
    if isinstance(node, dict):
        if _is_index(seg):
            raise _SaveError("invalid_path", f"数字段 {seg} 仅可用作数组下标")
        node[seg] = value
        return
    if isinstance(node, list):
        if not _is_index(seg):
            raise _SaveError("invalid_path", f"数组下标必须为数字段: {seg}")
        idx = int(seg)
        if idx > len(node):
            raise _SaveError("index_out_of_bounds",
                             f"数组下标 {idx} 越界 (数组长度 {len(node)})")
        if idx == len(node):
            node.append(value)
        else:
            node[idx] = value
        return
    raise _SaveError("invalid_path", f"路径途经标量值, 无法写入: {seg}")


def _apply_write(doc, segments, value):
    node = doc
    for i, seg in enumerate(segments[:-1]):
        node = _descend(node, seg, segments[i + 1])
    _assign(node, segments[-1], value)


def _resolve_path(doc, segments, raw_path):
    node = doc
    for seg in segments:
        if isinstance(node, dict) and not _is_index(seg) and seg in node:
            node = node[seg]
        elif isinstance(node, list) and _is_index(seg) and int(seg) < len(node):
            node = node[int(seg)]
        else:
            raise _SaveError("path_not_found", f"路径不存在: {raw_path}")
    return node


# ---------------------------------------------------------------------------
# Validation (D006 快速通道: 字段级, 写前; D007 兜底: 整文档, 写后内存复核)
# ---------------------------------------------------------------------------

def _fast_validate(doc, segments, value):
    """字段级写前校验, 发现问题抛 _SaveError; 不落盘."""
    top = segments[0]
    if top not in TOP_LEVEL_FIELDS:
        raise _SaveError(
            "unknown_field",
            f"未知顶层字段: {top}; 合法顶层字段: {', '.join(TOP_LEVEL_FIELDS)}")
    if top != "milestones" or len(segments) < 2:
        return
    mid = segments[1]
    milestones = doc.get("milestones")
    if not isinstance(milestones, dict):
        milestones = {}
    if len(segments) == 2:
        # save milestones.<new-id> <json> 新增里程碑: 必填 title/type/question
        if mid not in milestones:
            missing = [k for k in MILESTONE_REQUIRED
                       if not isinstance(value, dict) or k not in value]
            if missing:
                raise _SaveError(
                    "missing_required",
                    f"新增里程碑 {mid} 缺少必填字段: {', '.join(missing)}")
        return
    if len(segments) == 3:
        field = segments[2]
        if field == "status" and value not in STATUS_VALUES:
            raise _SaveError(
                "invalid_enum",
                f"非法 status 值 {json.dumps(value, ensure_ascii=False)}; "
                f"合法值: {', '.join(STATUS_VALUES)}")
        if field == "type" and value not in TYPE_VALUES:
            raise _SaveError(
                "invalid_enum",
                f"非法 type 值 {json.dumps(value, ensure_ascii=False)}; "
                f"合法值: {', '.join(TYPE_VALUES)}")
        if field == "blocked_by":
            if not isinstance(value, list) or not all(
                    isinstance(r, str) for r in value):
                raise _SaveError("invalid_value",
                                 "blocked_by 必须为里程碑 id 字符串数组")
            missing = [r for r in value if r not in milestones]
            if missing:
                raise _SaveError(
                    "invalid_reference",
                    f"blocked_by 引用不存在的里程碑: {', '.join(missing)}")


def _apply_milestone_defaults(doc, segments):
    """新增里程碑 (save milestones.<id> 整体写) 默认值: status 待处理,
    blocked_by [], artifacts [], close_summary null (BR-004)."""
    if len(segments) != 2 or segments[0] != "milestones":
        return
    milestones = doc.get("milestones")
    if not isinstance(milestones, dict):
        return
    m = milestones.get(segments[1])
    if not isinstance(m, dict):
        return
    # 每次调用新建默认值 dict, 避免跨里程碑共享可变 list
    for key, default in {"status": "待处理", "blocked_by": [],
                         "artifacts": [], "close_summary": None}.items():
        m.setdefault(key, default)


def _validate_milestone(mid, m):
    """单里程碑 schema 校验, 返回错误信息列表."""
    if not isinstance(m, dict):
        return [f"里程碑 {mid} 必须为对象"]
    errors = []
    missing = [k for k in ["title", "status", "type", "blocked_by", "question",
                           "artifacts", "close_summary"] if k not in m]
    if missing:
        errors.append(f"里程碑 {mid} 缺少字段: {', '.join(missing)}")
    for key in ("title", "question"):
        if key in m and not isinstance(m[key], str):
            errors.append(f"里程碑 {mid} {key} 必须为字符串")
    if "status" in m and m["status"] not in STATUS_VALUES:
        errors.append(f"里程碑 {mid} 非法 status 值 "
                      f"{json.dumps(m['status'], ensure_ascii=False)}; "
                      f"合法值: {', '.join(STATUS_VALUES)}")
    if "type" in m and m["type"] not in TYPE_VALUES:
        errors.append(f"里程碑 {mid} 非法 type 值 "
                      f"{json.dumps(m['type'], ensure_ascii=False)}; "
                      f"合法值: {', '.join(TYPE_VALUES)}")
    if "blocked_by" in m and (
            not isinstance(m["blocked_by"], list)
            or not all(isinstance(r, str) for r in m["blocked_by"])):
        errors.append(f"里程碑 {mid} blocked_by 必须为里程碑 id 字符串数组")
    if "artifacts" in m and (
            not isinstance(m["artifacts"], list)
            or not all(isinstance(a, str) for a in m["artifacts"])):
        errors.append(f"里程碑 {mid} artifacts 必须为字符串数组")
    if "close_summary" in m and m["close_summary"] is not None \
            and not isinstance(m["close_summary"], str):
        errors.append(f"里程碑 {mid} close_summary 必须为字符串或 null")
    return errors


def _find_cycle(milestones):
    """整文档视图 DFS 环检测 (含自环/间接环); 返回环路径或 None."""
    color = {}

    def deps(mid):
        m = milestones.get(mid)
        if not isinstance(m, dict) or not isinstance(m.get("blocked_by"), list):
            return []
        return [r for r in m["blocked_by"] if r in milestones]

    def dfs(node, trail):
        color[node] = 1
        for dep in deps(node):
            if color.get(dep) == 1:
                return trail[trail.index(dep):] + [dep]
            if color.get(dep, 0) == 0:
                found = dfs(dep, trail + [dep])
                if found:
                    return found
        color[node] = 2
        return None

    for mid in milestones:
        if color.get(mid, 0) == 0:
            found = dfs(mid, [mid])
            if found:
                return found
    return None


def _validate_document(doc):
    """整文档完整 schema 校验 (D007 兜底闸门), 返回错误信息列表."""
    if not isinstance(doc, dict):
        return ["文档必须为 JSON 对象"]
    errors = []
    unknown = [k for k in doc if k not in TOP_LEVEL_FIELDS]
    if unknown:
        errors.append(f"未知顶层字段: {', '.join(str(k) for k in unknown)}; "
                      f"合法顶层字段: {', '.join(TOP_LEVEL_FIELDS)}")
    missing_top = [k for k in TOP_LEVEL_FIELDS if k not in doc]
    if missing_top:
        errors.append(f"缺少顶层字段: {', '.join(missing_top)}")
    if "schema_version" in doc and doc["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version 必须为 {SCHEMA_VERSION}")
    for key in ("title", "destination"):
        if key in doc and not isinstance(doc[key], str):
            errors.append(f"{key} 必须为字符串")
    if "notes" in doc and not isinstance(doc["notes"], list):
        errors.append("notes 必须为数组")
    if "unknown_seas" in doc and (
            not isinstance(doc["unknown_seas"], list)
            or not all(isinstance(s, str) for s in doc["unknown_seas"])):
        errors.append("unknown_seas 必须为字符串数组")
    if "off_course" in doc and (
            not isinstance(doc["off_course"], list)
            or not all(isinstance(o, dict)
                       and isinstance(o.get("what"), str)
                       and isinstance(o.get("reason"), str)
                       for o in doc["off_course"])):
        errors.append("off_course 必须为 {what, reason} 对象数组")
    milestones = doc.get("milestones")
    if "milestones" in doc:
        if not isinstance(milestones, dict):
            errors.append("milestones 必须为对象")
        else:
            for mid, m in milestones.items():
                errors.extend(_validate_milestone(mid, m))
            for mid, m in milestones.items():
                if isinstance(m, dict) and isinstance(m.get("blocked_by"), list):
                    missing_ref = [r for r in m["blocked_by"]
                                   if isinstance(r, str) and r not in milestones]
                    if missing_ref:
                        errors.append(f"里程碑 {mid} blocked_by 引用不存在的里程碑: "
                                      f"{', '.join(missing_ref)}")
            cycle = _find_cycle(milestones)
            if cycle:
                errors.append(f"blocked_by 存在环: {' -> '.join(cycle)}")
    return errors


# ---------------------------------------------------------------------------
# Command cores
# ---------------------------------------------------------------------------

def run_save(file_str, path_str, content_str):
    file_path = Path(file_str)
    segments = path_str.split(".")
    if not path_str or any(s == "" for s in segments):
        return _err("save", "invalid_args", f"非法路径: {path_str!r}")
    value = _parse_content(content_str)
    with open(_lock_file_path(file_path), "w") as lock_fd:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        try:
            doc = _load_document(file_path)
            _fast_validate(doc, segments, value)
            _apply_write(doc, segments, value)
            _apply_milestone_defaults(doc, segments)
            problems = _validate_document(doc)
            if problems:
                raise _SaveError("validation_failed", "; ".join(problems))
            _atomic_write_json(file_path, doc)
        except _SaveError as e:
            return _err("save", e.code, e.error)
        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
    return _success("save", {"file": str(file_path), "path": path_str})


def run_delete(file_str):
    file_path = Path(file_str)
    with open(_lock_file_path(file_path), "w") as lock_fd:
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        try:
            if not file_path.exists():
                return _err("delete", "file_not_found", f"文件不存在: {file_path}")
            file_path.unlink()
        finally:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
    return _success("delete", {"file": str(file_path)})


def run_query(file_str, path_str):
    file_path = Path(file_str)
    if not file_path.exists():
        return _err("query", "file_not_found", f"文件不存在: {file_path}")
    try:
        doc = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return _err("query", "invalid_json", f"文件不是合法 JSON: {file_path} ({e})")
    try:
        value = _resolve_path(doc, path_str.split("."), path_str)
    except _SaveError as e:
        return _err("query", e.code, e.error)
    return _success("query",
                    {"file": str(file_path), "path": path_str, "value": value})


# ---------------------------------------------------------------------------
# CLI adapter (argv, JSON serialization, exit code)
# ---------------------------------------------------------------------------

USAGE = "Usage: roadmap.py <save|delete|query> <file> [path] [content]"


def _emit(obj):
    """Serialize one result object to stdout; return exit code."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0 if obj["success"] else 1


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    command = argv[0] if argv else "unknown"
    try:
        if command == "save":
            if len(argv) != 4:
                obj = _err("save", "invalid_args",
                           "Usage: roadmap.py save <file> <path> <content>")
            else:
                obj = run_save(argv[1], argv[2], argv[3])
        elif command == "delete":
            if len(argv) != 2:
                obj = _err("delete", "invalid_args", "Usage: roadmap.py delete <file>")
            else:
                obj = run_delete(argv[1])
        elif command == "query":
            if len(argv) != 3:
                obj = _err("query", "invalid_args",
                           "Usage: roadmap.py query <file> <path>")
            else:
                obj = run_query(argv[1], argv[2])
        elif command == "unknown":
            obj = _err(command, "invalid_args", USAGE)
        else:
            obj = _err(command, "invalid_args", f"Unknown command: {command}")
    except Exception as e:
        obj = _err(command, "internal_error", str(e))
    sys.exit(_emit(obj))


if __name__ == "__main__":
    main()
