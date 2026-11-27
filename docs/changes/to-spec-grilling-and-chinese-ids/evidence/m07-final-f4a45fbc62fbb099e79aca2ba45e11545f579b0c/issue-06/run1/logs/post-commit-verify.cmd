git rev-parse HEAD; git status --porcelain | wc -c; sha256sum <5 文件>; git show HEAD:<5 文件> | sha256sum; git show --name-only --format= HEAD
