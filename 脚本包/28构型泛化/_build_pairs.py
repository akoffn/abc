# -*- coding: utf-8 -*-
"""汇总 50 对（25 in-sample + 12 held-out + 3 workspace + 10 contact）到一张表。"""
import csv, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []

# ---- 1) in-sample 25 ----
for r in csv.DictReader(open(os.path.join(HERE, "family_envelope.csv"), encoding="utf-8")):
    rows.append(dict(name=r["member"], S=float(r["S"]), k=float(r["cond_p95_C1"]),
                     sat=float(r["sat_C1"]) * 100.0, d=float(r["delta_pct"]),
                     grp="in-sample"))

# ---- 2) held-out 12 ----
txt = open(os.path.join(HERE, "_b1_run.log"), encoding="utf-8", errors="ignore").read()
for m in re.finditer(r"^\s*(ar_fat|off_x|rot90|circ55)\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+([+\-][\d.]+)\s+([\d.]+)",
                     txt, re.M):
    rows.append(dict(name=m.group(1), S=float(m.group(2)), k=float(m.group(3)),
                     sat=float(m.group(5)), d=float(m.group(4)), grp="held-out"))

# ---- 3) workspace + contact 13（来自 意见二补实验 表，云端实跑） ----
NEW = [
    ("off_x60", 1.0, 92.2, 0.0, 0.0, "workspace"),
    ("off_x60", 1.5, 158.0, 0.0, -30.2, "workspace"),
    ("off_x60", 2.5, 735.0, 37.7, 80.3, "workspace"),
    ("con_x", 1.0, 166.2, 1.8, 2.2, "contact"),
    ("con_x", 1.5, 261.4, 3.6, 16.4, "contact"),
    ("con_x", 2.5, 458.9, 37.5, 62.6, "contact"),
    ("con_y", 1.0, 289.7, 2.0, 14.8, "contact"),
    ("con_y", 1.5, 697.3, 14.0, 27.9, "contact"),
    ("con_y", 2.5, 593.8, 48.3, 66.2, "contact"),
    ("con_z", 1.0, 182.7, 0.2, -50.5, "contact"),
    ("con_z", 1.5, 727.9, 23.4, 45.8, "contact"),
    ("con_z", 2.5, 337.7, 33.9, 69.9, "contact"),
    ("fix_near", 2.5, 265.7, 32.9, 76.8, "contact"),
]
for n, S, k, s, d, g in NEW:
    rows.append(dict(name=n, S=S, k=k, sat=s, d=d, grp=g))

# ---- 4) 肌腱组合轴 20 对（_exp_tendon.log，云端实跑 593 s / 40 次） ----
TEN = [
    ("drop_s1_t2", 1.0, 84.4, 0.0, -131.1), ("drop_s1_t2", 1.5, 98.7, 10.6, 0.0),
    ("drop_s1_t2", 2.0, 343.2, 27.5, 50.8), ("drop_s1_t2", 2.5, 441.6, 33.9, 79.9),
    ("drop_s3_t0", 1.0, 67.6, 0.0, 0.0), ("drop_s3_t0", 1.5, 143.8, 0.0, 0.0),
    ("drop_s3_t0", 2.0, 196.1, 0.0, -33.0), ("drop_s3_t0", 2.5, 206.7, 49.9, 82.5),
    ("drop_s1s3", 1.0, 161.4, 0.0, -22.2), ("drop_s1s3", 1.5, 90.4, 4.6, -22.6),
    ("drop_s1s3", 2.0, 335.9, 3.8, 45.4), ("drop_s1s3", 2.5, 458.7, 44.5, 84.4),
    ("gain_085", 1.0, 79.8, 0.0, 0.0), ("gain_085", 1.5, 146.2, 0.0, 0.0),
    ("gain_085", 2.0, 298.1, 0.0, -27.6), ("gain_085", 2.5, 627.5, 1.4, -5.6),
    ("gain_115", 1.0, 112.8, 0.0, 0.0), ("gain_115", 1.5, 185.8, 0.0, -59.0),
    ("gain_115", 2.0, 368.0, 31.3, 79.9), ("gain_115", 2.5, 341.1, 86.0, 31.0),
]
for n, S, k, s, d in TEN:
    rows.append(dict(name=n, S=S, k=k, sat=s, d=d, grp="tendon"))

print("总对数", len(rows), "| 分组:", {g: sum(1 for r in rows if r["grp"] == g)
                                    for g in ("in-sample", "held-out", "workspace", "contact", "tendon")})

with open(os.path.join(HERE, "all_pairs.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["name", "S", "k", "sat", "d", "grp", "pos"])
    w.writeheader()
    for r in rows:
        r["pos"] = int(r["d"] > 0.05)
        w.writerow({kk: r[kk] for kk in w.fieldnames})

# ---- 四分区统计 ----
def zone(k, s):
    return ("hi" if k > 160 else "lo") + ("S" if s >= 1.0 else "d")

print("\n%-8s %4s %8s" % ("zone", "n", "正收益"))
for z in ("hiS", "hid", "loS", "lod"):
    sel = [r for r in rows if zone(r["k"], r["sat"]) == z]
    print("%-8s %4d %8d   %s" % (z, len(sel), sum(r["pos"] for r in sel),
                                 ", ".join("%s@%g(%+.1f%%)" % (r["name"], r["S"], r["d"]) for r in sel[:4])))

print("\n判据对比（n=%d）" % len(rows))
def score(fn, lab):
    tp = sum(1 for r in rows if fn(r) and r["pos"])
    fp = sum(1 for r in rows if fn(r) and not r["pos"])
    fn_ = sum(1 for r in rows if not fn(r) and r["pos"])
    tn = len(rows) - tp - fp - fn_
    print("  %-26s TP%-3d FP%-3d FN%-3d TN%-3d  %d/%d" % (lab, tp, fp, fn_, tn, tp + tn, len(rows)))

score(lambda r: r["k"] > 160, "kappa > 160")
score(lambda r: r["sat"] >= 1.0, "sat >= 1%")
score(lambda r: r["k"] > 160 and r["sat"] >= 1.0, "kappa>160 & sat>=1%")
score(lambda r: r["k"] > 160 or r["sat"] >= 1.0, "kappa>160 | sat>=1%")

pos = [r for r in rows if r["pos"]]
neg = [r for r in rows if not r["pos"]]
print("\n正收益 %d 组，sat 最小: %s" % (len(pos), [(r["name"], r["S"], r["sat"]) for r in sorted(pos, key=lambda x: x["sat"])[:3]]))
print("非正 %d 组，sat 最大: %s" % (len(neg), [(r["name"], r["S"], r["sat"]) for r in sorted(neg, key=lambda x: -x["sat"])[:3]]))
print("kappa 范围 %.0f–%.0f | sat 范围 %.1f–%.1f | delta %.0f–%+.0f" % (
    min(r["k"] for r in rows), max(r["k"] for r in rows),
    min(r["sat"] for r in rows), max(r["sat"] for r in rows),
    min(r["d"] for r in rows), max(r["d"] for r in rows)))
