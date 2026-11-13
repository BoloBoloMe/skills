# 一次性统计脚本 (milestone-23): 解析 dependencyparser 输出的 cc.json 2.0, 提取门禁所需统计. 非产品实现.
import json
import sys
from collections import Counter

path = sys.argv[1]
d = json.load(open(path))

meta = d.get("meta", {})
print("== meta ==")
print("projectName:", meta.get("projectName"))
print("apiVersion:", meta.get("apiVersion"))
print("checksum:", meta.get("checksum"))

files_root = d["files"][0]

# 遍历树, 记录每个节点 id -> (类型, 路径)
nodes = {}  # id -> {"type","path"}
def walk(n, prefix):
    p = prefix + "/" + n["name"] if prefix else n["name"]
    nodes[n["id"]] = {"type": n.get("type"), "path": p, "children": n.get("children")}
    for c in n.get("children") or []:
        walk(c, p)
walk(files_root, "")
file_nodes = {i: v for i, v in nodes.items() if v["type"] == "File"}
folder_nodes = {i: v for i, v in nodes.items() if v["type"] == "Folder"}
print("== 树 ==")
print("File 节点总数:", len(file_nodes))
print("Folder 节点总数:", len(folder_nodes))

lenses = d.get("lenses", {})
dep = lenses.get("dependency", {})
dep_nodes = dep.get("nodes", {})
edges = dep.get("edges", [])
metrics = lenses.get("metrics", {}).get("attributes", {})

print("== dependency lens ==")
print("dependency.nodes 条数:", len(dep_nodes))
# 按 文件/目录 分开统计 level
def type_of(nid):
    t = nodes.get(nid, {}).get("type")
    if t == "File":
        return "file"
    if t == "Folder":
        return "folder"
    return "unknown"
lv_file = Counter()
lv_folder = Counter()
lv_unknown = 0
for nid, attrs in dep_nodes.items():
    t = type_of(nid)
    lvl = attrs.get("level")
    if t == "file":
        lv_file[lvl] += 1
    elif t == "folder":
        lv_folder[lvl] += 1
    else:
        lv_unknown += 1
print("level 取值 (文件):", dict(sorted(lv_file.items(), key=lambda kv: (kv[0] is None, kv[0]))))
print("level 取值 (目录):", dict(sorted(lv_folder.items(), key=lambda kv: (kv[0] is None, kv[0]))))
print("非文件非目录的 lens 节点:", lv_unknown)
print("level 种数 (文件):", len(lv_file), " (目录):", len(lv_folder))

# 覆盖分母
covered_files = sum(1 for nid in dep_nodes if type_of(nid) == "file")
print("dependency lens 覆盖的 File 节点:", covered_files, "/", len(file_nodes))
no_level_files = [i for i in file_nodes if i not in dep_nodes]
print("未进 dependency lens 的 File 节点数:", len(no_level_files))
if no_level_files[:5]:
    for i in no_level_files[:5]:
        print("  例:", file_nodes[i]["path"])

print("== 边 ==")
print("边总数 (dependency.edges):", len(edges))
cyc = sum(1 for e in edges if e.get("isCyclic"))
up = sum(1 for e in edges if e.get("isPointingUpwards"))
both = sum(1 for e in edges if e.get("isCyclic") and e.get("isPointingUpwards"))
print("isCyclic=true:", cyc)
print("isPointingUpwards=true:", up)
print("both:", both)
print("regular (无标志):", len(edges) - cyc - up + both)
# 边端点覆盖
endpoints = set()
for e in edges:
    endpoints.add(e["fromId"]); endpoints.add(e["toId"])
file_endpoints = {i for i in endpoints if type_of(i) == "file"}
print("出现在边上的 File 节点:", len(file_endpoints), "/", len(file_nodes))
isolated = len(file_nodes) - len(file_endpoints)
print("未出现在任何边上的 File 节点 (库内零依赖):", isolated, f"({isolated*100//max(1,len(file_nodes))}%)")

# metrics lens
print("== metrics lens ==")
print("metrics.attributes 覆盖节点数:", len(metrics))
mk = Counter()
for attrs in metrics.values():
    for k in attrs:
        mk[k] += 1
print("指标名 -> 出现文件数 (前 12):", dict(mk.most_common(12)))
rloc_files = sum(1 for a in metrics.values() if "rloc" in a)
print("含 rloc 的节点:", rloc_files)

# 边的 weight 分布
w = Counter(e.get("attributes", {}).get("dependencies") for e in edges)
print("边权 dependencies 分布 (前 10):", dict(sorted(w.items(), key=lambda kv: -kv[1])[:10]))

# 逻辑层 (leafEdges) 概况
le = dep.get("leafEdges", [])
print("== 逻辑层 ==")
print("leafEdges 总数:", len(le))
print("leaves 声明数:", sum(len(v) for v in dep.get("leaves", {}).values()))
print("namespaces 数:", len(dep.get("namespaces", {})))
ns_lv = Counter(v.get("level") for v in dep.get("namespaces", {}).values())
print("namespace level 分布:", dict(sorted(ns_lv.items(), key=lambda kv: (kv[0] is None, kv[0]))))
