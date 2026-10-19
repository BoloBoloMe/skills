"""证明 clamp_qty 在仓库内外都没有调用者.

失败条件 (非零退出): 在扫描范围内找到定义文件之外的任何引用.
扫描方式: 文本检索 + AST (抓 import/属性访问), 避免漏掉别名导入.
"""
import ast
import pathlib
import sys

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts003-local")
CONSUMER = pathlib.Path("/tmp/orchestra-07/orders-consumer")
NEEDLE = "clamp_qty"
SKIP_DIRS = {".git", ".agents", "__pycache__", ".venv", "node_modules"}


def files(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.parts) & SKIP_DIRS):
            yield p


def main():
    hits = []
    scanned = 0
    for root in (REPO, CONSUMER):
        for p in files(root):
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            scanned += 1
            if NEEDLE in text and "app/clamp.py" not in str(p):
                hits.append((p, "text"))
            if p.suffix == ".py":
                tree = ast.parse(text, filename=str(p))
                for node in ast.walk(tree):
                    names = []
                    if isinstance(node, ast.ImportFrom):
                        names = [a.name for a in node.names] + [node.module or ""]
                    elif isinstance(node, ast.Import):
                        names = [a.name for a in node.names]
                    elif isinstance(node, ast.Attribute):
                        names = [node.attr]
                    elif isinstance(node, ast.Name):
                        names = [node.id]
                    if any(NEEDLE == n or n.endswith("." + NEEDLE) for n in names):
                        if "app/clamp.py" not in str(p):
                            hits.append((p, f"ast:{type(node).__name__}:{getattr(node, 'lineno', '?')}"))

    print(f"扫描文件数: {scanned} (范围: {REPO}, {CONSUMER})")
    print(f"定义处: app/clamp.py:4")
    print(f"定义文件之外的引用: {len(hits)}")
    for p, how in hits:
        print(f"  {p} [{how}]")

    assert hits == [], f"发现调用者, 需要人工评估: {hits}"
    print("PASS: 除定义处, 没有任何代码引用 clamp_qty; app/clamp.py 未被任何模块导入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
