import re, sys, os, glob, fnmatch
repo = "/tmp/i06base"
docdir = repo + "/docs/changes/to-spec-grilling-and-chinese-ids"
arch = docdir + "/evidence/m07-1bc15f612c10aa6e68e33587a01cd2de1ede2fe4"
ev = "/home/bolo/evidence/to-spec-grilling-and-chinese-ids"
search_roots = [repo + "/workflow", repo + "/general", docdir, repo + "/pi", arch,
                ev + "/issue-01", ev + "/issue-02", ev + "/issue-03", ev + "/integration"]
index = None
def build_index():
    global index
    index = set()
    for root in search_roots:
        for dp, dn, fn in os.walk(root):
            rel = os.path.relpath(dp, root)
            if rel != ".":
                index.add(rel + "/")
            for name in fn:
                index.add(os.path.join(rel, name) if rel != "." else name)
def expand(t):
    m = re.search(r"\{([^{}]+)\}", t)
    if not m: return [t]
    out = []
    for alt in m.group(1).split(","):
        out += expand(t[:m.start()] + alt + t[m.end():])
    return out
def find_suffix(t):
    if index is None: build_index()
    pats = [t.rstrip("/") + "/", t]
    for p in pats:
        for x in index:
            if x == p or x.endswith("/" + p) or fnmatch.fnmatchcase(x, p) or fnmatch.fnmatchcase(x, "*/" + p):
                return p
    return None
files = sys.argv[1:]
tok_re = re.compile(r"`([^`]+)`")
bad = []
for f in files:
    text = open(f, encoding="utf-8").read()
    bases = [os.path.dirname(os.path.abspath(f)), repo, docdir, docdir + "/issues", arch,
             ev + "/issue-01", ev + "/issue-02", ev + "/issue-03",
             arch + "/issue-01", arch + "/issue-02", arch + "/issue-02/check1", arch + "/issue-03", arch + "/integration/run1",
             ev + "/issue-06/run1"]
    seen = set()
    for m in tok_re.finditer(text):
        t = m.group(1).strip()
        if t in seen: continue
        seen.add(t)
        if " " in t or not re.match(r"^[\w./~*{}<>,-]+$", t):
            print(f"SKIP(命令/占位符) {os.path.basename(f)}: {t}"); continue
        if t.startswith("http"):
            print(f"SKIP(URL) {os.path.basename(f)}: {t}"); continue
        alts = []
        for a in expand(t):
            alts += glob.glob(a) if a.startswith("/") else [a]
            if a.startswith("/"):
                continue
            for b in bases:
                p = os.path.join(b, a)
                alts += glob.glob(p) if any(c in a for c in "*?[") else ([p] if os.path.exists(p) else [])
        alts = [a for a in alts if os.path.exists(a)]
        if alts:
            print(f"OK {os.path.basename(f)}: {t} -> {os.path.relpath(alts[0], repo)}")
            continue
        suf = None
        for a in expand(t):
            suf = suf or find_suffix(a)
        if suf:
            print(f"OK(证据/仓库内按名命中) {os.path.basename(f)}: {t} -> .../{suf}")
        else:
            bad.append((os.path.basename(f), t))
            print(f"UNRESOLVED {os.path.basename(f)}: {t}")
print("UNRESOLVED_COUNT", len(bad))
