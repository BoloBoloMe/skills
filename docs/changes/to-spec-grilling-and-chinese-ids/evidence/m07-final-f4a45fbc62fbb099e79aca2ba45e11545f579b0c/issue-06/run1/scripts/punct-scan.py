import sys
bad = {"\u3001": "U+3001", "\u2014": "U+2014"}
total = 0
for f in sys.argv[1:]:
    for n, line in enumerate(open(f, encoding="utf-8"), 1):
        for ch in bad:
            c = line.count(ch)
            if c:
                total += c
                print(f"{f}:{n}: {bad[ch]} x{c}: {line.rstrip()}")
print("TOTAL", total)
