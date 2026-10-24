# -*- coding: utf-8 -*-
"""生成云端可一次粘贴的自包含脚本 _run_ws2.py：内嵌 exp2b 源码 + 四向位移驱动"""
src = open(r"C:/Users/Admin/Desktop/返修_机制验证/_exp2b.py", encoding="utf8").read()

driver = '''

# ================= 驱动：工作空间四向 60 mm 位移 =================
import sys as _sys, json as _json, time as _time
_sys.path.insert(0, "/tmp")
import _exp2b as E
import numpy as np
from multiprocessing import Pool

DIRS = [
    ("ws_xp60", ( 0.060, 0.000, 0.000)),
    ("ws_xm60", (-0.060, 0.000, 0.000)),
    ("ws_yp60", ( 0.000, 0.060, 0.000)),
    ("ws_zm60", ( 0.000, 0.000,-0.060)),
]
jobs = []
for tag, off in DIRS:
    for S in (1.0, 1.5, 2.5):
        for c in ("C1", "C2"):
            jobs.append(dict(member=tag, S=S, ctrl=c, ball=None, ton=0.0, c0off=off))

print("=== 工作空间四向位移：%d 次仿真（6 进程）===" % len(jobs), flush=True)
t0 = _time.time()
with Pool(6) as p:
    res = p.map(E.run, jobs)

print("\\n%-10s %-4s %-3s %8s %8s %8s %6s" %
      ("member", "S", "ctl", "k95", "err", "p95", "sat%"))
print("-" * 56)
for r in res:
    print("%-10s %-4.1f %-3s %8.1f %8.3f %8.3f %6.1f" %
          (r["member"], r["S"], r["ctrl"], r["cond"], r["err"], r["p95"], r["sat"]))

idx = {(r["member"], r["S"], r["ctrl"]): r for r in res}
pairs = []
for (mn, S, c), r1 in idx.items():
    if c != "C1":
        continue
    r2 = idx[(mn, S, "C2")]
    dl = 100 * (r1["err"] - r2["err"]) / r1["err"] if r1["err"] > 0 else float("nan")
    pairs.append([mn, S, r1["cond"], r1["sat"], r2["sat"], r1["err"], r2["err"], dl])
pairs.sort(key=lambda x: (x[0], x[1]))

print("\\n=== 配对 Δ% = (C1-C2)/C1 ===")
print("%-10s %-4s %8s %7s %7s %8s %8s %8s  %s" %
      ("member", "S", "k95", "satC1", "satC2", "errC1", "errC2", "D%", "gate"))
print("-" * 84)
ng = 0
for q in pairs:
    on = (q[2] > 160.0) and (q[3] >= 1.0)
    hit = (on and q[7] > 0) or ((not on) and q[7] <= 0)
    ng += 1 if hit else 0
    print("%-10s %-4.1f %8.1f %7.1f %7.1f %8.3f %8.3f %+8.1f  %s" %
          (q[0], q[1], q[2], q[3], q[4], q[5], q[6], q[7],
           ("ON " if on else "off") + ("" if hit else "  <-- MISS")))
print("\\n判据命中 %d / %d" % (ng, len(pairs)))
_json.dump(pairs, open("/tmp/ws2.json", "w"))
print("PAIRS_JSON=" + _json.dumps([[q[0], q[1], round(q[2], 1), round(q[3], 1), round(q[7], 1)]
                                   for q in pairs]))
print("=== 总耗时 %.0fs ===" % (_time.time() - t0), flush=True)
'''

head = "# -*- coding: utf-8 -*-\n# 自包含：先把 exp2b 源码落到 /tmp，再 import（避免常量抄错）\n_exp2b_src = r'''" 
out = head + src + "'''\nopen('/tmp/_exp2b.py','w',encoding='utf-8').write(_exp2b_src)\n" + driver
p = r"C:/Users/Admin/Desktop/返修_机制验证/_run_ws2.py"
open(p, "w", encoding="utf8").write(out)
import ast
ast.parse(out)
print("生成 OK, %d bytes" % len(out))
