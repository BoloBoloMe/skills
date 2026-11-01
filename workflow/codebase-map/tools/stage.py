#!/usr/bin/env python3
"""把构建产物与数据副本铺进服务根 (D023/D024), m21 只做铺设, 不起服务 (v1 服务属 milestone-26).

用法:
  python3 stage.py frontend [--serve-root DIR] [--dist DIR]
      把最近一次构建的前端产物复制到服务根 (index.html 落在服务根顶层, 数据副本同目录, F014).
  python3 stage.py data <cc.json> [--serve-root DIR] [--name 库名]
      复制一份 cc.json 到服务根, 键名 <库名>-<8 位路径哈希>.cc.json (D023), 打印可书签 URL 的
      相对地址 ?file=<键>. 重跑同一库覆盖同一键 (同名库不再互相覆盖).

默认: --serve-root ~/.agents/codebase-map/serve-root; frontend 的 --dist 取
~/.agents/codebase-map/cache/src/visualization/dist/bundler/browser (build-zh.sh 的产物位).
路径哈希 = sha256(realpath(源文件或库目录)) 的前 8 位十六进制.
"""

import argparse
import hashlib
import os
import shutil
import sys

DEFAULT_SERVE_ROOT = os.path.expanduser("~/.agents/codebase-map/serve-root")
DEFAULT_DIST = os.path.expanduser("~/.agents/codebase-map/cache/src/visualization/dist/bundler/browser")


def data_key(path, name):
    real = os.path.realpath(path)
    base = name or os.path.basename(real)
    for ext in (".cc.json", ".json"):
        if base.endswith(ext):
            base = base[: -len(ext)]
            break
    digest = hashlib.sha256(real.encode()).hexdigest()[:8]
    return "%s-%s.cc.json" % (base, digest)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_front = sub.add_parser("frontend", help="铺前端产物到服务根")
    p_front.add_argument("--serve-root", default=DEFAULT_SERVE_ROOT)
    p_front.add_argument("--dist", default=DEFAULT_DIST)

    p_data = sub.add_parser("data", help="铺一份数据副本到服务根")
    p_data.add_argument("ccjson", help="权威 cc.json 路径 (v1 约定: <库>/.codebase-map/cc.json)")
    p_data.add_argument("--serve-root", default=DEFAULT_SERVE_ROOT)
    p_data.add_argument("--name", default=None, help="键里的库名, 默认取文件名去扩展名")

    args = ap.parse_args()
    os.makedirs(args.serve_root, exist_ok=True)

    if args.cmd == "frontend":
        if not os.path.isfile(os.path.join(args.dist, "index.html")):
            print("FATAL: %s 里没有 index.html, 先跑 build-zh.sh" % args.dist, file=sys.stderr)
            return 2
        for entry in os.listdir(args.dist):
            src = os.path.join(args.dist, entry)
            dst = os.path.join(args.serve_root, entry)
            if os.path.isdir(src):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        print("前端产物已铺到: %s" % args.serve_root)
        print("验证: 任一静态服务指向该目录即可, 例: python3 -m http.server 8090 -d %s" % args.serve_root)
        return 0

    src = args.ccjson
    if not os.path.isfile(src):
        print("FATAL: 文件不存在: %s" % src, file=sys.stderr)
        return 2
    key = data_key(src, args.name)
    dst = os.path.join(args.serve_root, key)
    shutil.copy2(src, dst)
    print("数据副本: %s" % dst)
    print("页面地址: ?file=%s (与前端产物同目录, 满足 F014 同源同目录)" % key)
    return 0


if __name__ == "__main__":
    sys.exit(main())
