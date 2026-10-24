# -*- coding: utf-8 -*-
"""生成自包含脚本：接触压入深度扫描（加载量级轴），复用 exp2b 的 run()"""
src = open(r"C:/Users/Admin/Desktop/返修_机制验证/_exp2b.py", encoding="utf8").read()

driver = '''

# ================= 驱动：接触压入深度（加载量级）扫描 =================
import sys as _sys, json as _json, time as _time
_sys.path.insert(0, "/tmp")
import _exp2b as E
import numpy as np
from multiprocessing import Pool

def run_pen(j):
    jj = dict(j)
    pen = jj.pop("pen")
    E.TOUCH = E.R_LINK + E.R_BALL - pen      # 越深 = 压得越紧 = 载荷越大
    return E.run(jj)

if __name__ == "__main__":
    t0 = _time.time()
    print("=== 阶段0 自由空间名义路径（3 档）===", flush=True)
    caps = Pool(3).map(E.run, [dict(member="base", S=s, ctrl="C1", ball=None, ton=0.0,
                                    c0off=(0, 0, 0), cap=True) for s in (1.0, 1.5, 2.5)])
    for c in caps:
        E.NOMINAL[c["S"]] = c["traj"]
        print("  S=%.1f k95=%.1f err=%.3f" % (c["S"], c["cond"], c["err"]), flush=True)

    jobs = []
    for pen in (0.002, 0.004, 0.006):
        for S in (1.0, 1.5, 2.5):
            for c in ("C1", "C2"):
                jobs.append(dict(member="pen%d" % round(pen * 1000), S=S, ctrl=c,
                                 ball="x", ton=0.0, c0off=(0, 0, 0), pen=pen))
    print("=== 阶段1 %d 次 ===" % len(jobs), flush=True)
    with Pool(6) as p:
        res = p.map(run_pen, jobs)

    print("\\n%-8s %-4s %-3s %8s %8s %8s %6s %9s %6s" %
          ("pen", "S", "ctl", "k95", "err", "p95", "sat%", "ncon/n", "penum"))
    print("-" * 70)
    for r in res:
        print("%-8s %-4.1f %-3s %8.1f %8.3f %8.3f %6.1f %9s %6s" % (
            r["member"], r["S"], r["ctrl"], r["cond"], r["err"], r["p95"], r["sat"],
            "%d/%d" % (r["nc"], r["n"]), "%.2f" % r["pen"] if r["nc"] else "-"))

    idx = {(r["member"], r["S"], r["ctrl"]): r for r in res}
    pairs = []
    for (mn, S, c), r1 in idx.items():
        if c != "C1":
            continue
        r2 = idx[(mn, S, "C2")]
        dl = 100 * (r1["err"] - r2["err"]) / r1["err"] if r1["err"] > 0 else float("nan")
        pairs.append([mn, S, r1["cond"], r1["sat"], r2["sat"], dl])
    pairs.sort(key=lambda x: (x[0], x[1]))
    print("\\n=== 配对 ===")
    print("%-8s %-4s %8s %7s %7s %9s  %s" % ("pen", "S", "k95", "satC1", "satC2", "D%", "gate"))
    ng = 0
    for q in pairs:
        on = (q[2] > 160.0) and (q[3] >= 1.0)
        hit = (on and q[5] > 0) or ((not on) and q[5] <= 0)
        ng += 1 if hit else 0
        print("%-8s %-4.1f %8.1f %7.1f %7.1f %+9.1f  %s" %
              (q[0], q[1], q[2], q[3], q[4], q[5], ("ON " if on else "off") + ("" if hit else "  <-- MISS")))
    print("\\n判据命中 %d / %d" % (ng, len(pairs)))
    print("PAIRS_JSON=" + _json.dumps([[q[0], q[1], round(q[2], 1), round(q[3], 1), round(q[5], 1)] for q in pairs]))
    print("=== 总耗时 %.0fs ===" % (_time.time() - t0), flush=True)
'''

head = "# -*- coding: utf-8 -*-\n_exp2b_src = r'''"
out = head + src + "'''\nopen('/tmp/_exp2b_pen.py','w',encoding='utf-8').write(_exp2b_src)\n" + driver.replace("import _exp2b as E", "import _exp2b_pen as E")
open(r"C:/Users/Admin/Desktop/返修_机制验证/_payload_pen.py", "w", encoding="utf8").write(out)
import ast; ast.parse(out); print("ok %d bytes" % len(out))
