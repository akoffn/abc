# -*- coding: utf-8 -*-
"""解析 _ws2.log 的 PAIRS_JSON，写入 all_pairs.csv（去重 ws_xp60，只补三个新方向），并重算总账"""
import json, csv, re, shutil, os
log = open("_ws2.log", encoding="utf8", errors="ignore").read()
m = re.search(r"PAIRS_JSON=(\[\[.*?\]\])", log, re.S)
assert m, "日志里没有 PAIRS_JSON"
rows = json.loads(m.group(1))
print("从云端收到 %d 对" % len(rows))

# 复现性对照：ws_xp60 vs 已有 off_x60
old = {(r["name"], float(r["S"])): r for r in csv.DictReader(open("all_pairs.csv", encoding="utf8"))}
print("\n[复现性] +60 mm x 方向 重跑 vs 原记录")
for tag, S, k, s, d in rows:
    if tag != "ws_xp60": continue
    o = old.get(("off_x60", float(S)))
    if o:
        print("  S=%.1f  k95 %.1f→%.1f | sat %.1f→%.1f | Δ %+.1f→%+.1f" %
              (S, float(o["k"]), k, float(o["sat"]), s, float(o["d"]), d))

NEW = {"ws_xm60": "ws_xm60", "ws_yp60": "ws_yp60", "ws_zm60": "ws_zm60"}
add = [(tag, S, k, s, d) for tag, S, k, s, d in rows if tag in NEW]
print("\n新增 %d 对（三个新方向）" % len(add))

shutil.copy2("all_pairs.csv", "_bak_all_pairs.csv")
with open("all_pairs.csv", "a", newline="", encoding="utf8") as f:
    w = csv.writer(f)
    for tag, S, k, s, d in add:
        w.writerow([tag, S, k, s, d, "workspace2", 1 if d > 0 else 0])
print("已追加到 all_pairs.csv")
