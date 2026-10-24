# -*- coding: utf-8 -*-
import csv, math, io, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

CSV = r"""name,S,k,sat,d,grp,pos
base,1.0,99.38204231776432,0.0,0.0,in-sample,0
scale_s,1.5,105.02861021971633,0.0,-99.21806438472937,in-sample,0
ar_thin,1.5,120.09490238606799,0.0,-68.98287870263614,in-sample,0
base,1.5,141.15911927646624,0.0,-41.27232476074408,in-sample,0
scale_s,2.0,188.80938801562542,0.0,-57.10159940514657,in-sample,0
k3,1.5,197.24889280279567,0.0,-24.706401346959918,in-sample,0
ar_thin,2.0,223.08901823156725,0.0,-57.006572924507665,in-sample,0
base,2.0,313.7637524474154,0.0,-49.48641484258674,in-sample,0
off_z,2.0,327.52197064510904,87.97595190380761,82.91210151889824,in-sample,1
scale_s,2.5,343.4151723396445,4.208416833667335,44.26881986020479,in-sample,1
scale_l,1.5,354.56353768903153,0.0,-63.29531715978548,in-sample,0
k3,2.0,417.4949655415092,0.0,-63.546192072208726,in-sample,0
ar_thin,2.5,456.16495685061454,21.442885771543086,77.01953507675869,in-sample,1
off_z,2.5,462.76421241314995,76.15230460921843,82.90952019420567,in-sample,1
tilt45,1.5,475.782351657865,0.0,-44.46334270771506,in-sample,0
tilt90,1.5,511.8419399465499,0.0,-46.970013929336105,in-sample,0
scale_l,2.5,512.2534118699026,62.925851703406806,75.860288404076,in-sample,1
k3,2.5,577.1626420512717,20.04008016032064,62.684019612266965,in-sample,1
base,2.5,638.949172684271,23.847695390781563,71.30203277588438,in-sample,1
off_z,1.5,728.6269310262604,16.432865731462925,54.61855733388538,in-sample,1
tilt45,2.0,814.6662233644828,15.030060120240481,29.09126439727882,in-sample,1
scale_l,2.0,983.3818568170743,17.635270541082164,48.12330810251266,in-sample,1
tilt90,2.0,1096.774728418814,26.252505010020037,50.18058354696942,in-sample,1
tilt45,2.5,1336.4284106886469,39.278557114228455,50.08195701072908,in-sample,1
tilt90,2.5,1844.089638624768,49.899799599198396,56.865432868493606,in-sample,1
ar_fat,1.5,239.5,0.0,-73.0,held-out,0
ar_fat,2.0,662.4,3.2,3.1,held-out,1
ar_fat,2.5,805.1,48.3,75.7,held-out,1
off_x,1.5,122.8,0.0,-4.0,held-out,0
off_x,2.0,193.7,0.0,-63.7,held-out,0
off_x,2.5,413.4,14.0,58.7,held-out,1
rot90,1.5,238.4,0.0,-49.3,held-out,0
rot90,2.0,509.1,12.8,49.6,held-out,1
rot90,2.5,884.3,46.5,79.5,held-out,1
circ55,1.5,123.1,2.4,36.0,held-out,1
circ55,2.0,291.1,11.0,69.9,held-out,1
circ55,2.5,625.9,46.3,85.7,held-out,1
off_x60,1.0,92.2,0.0,0.0,workspace,0
off_x60,1.5,158.0,0.0,-30.2,workspace,0
off_x60,2.5,735.0,37.7,80.3,workspace,1
con_x,1.0,166.2,1.8,2.2,contact,1
con_x,1.5,261.4,3.6,16.4,contact,1
con_x,2.5,458.9,37.5,62.6,contact,1
con_y,1.0,289.7,2.0,14.8,contact,1
con_y,1.5,697.3,14.0,27.9,contact,1
con_y,2.5,593.8,48.3,66.2,contact,1
con_z,1.0,182.7,0.2,-50.5,contact,0
con_z,1.5,727.9,23.4,45.8,contact,1
con_z,2.5,337.7,33.9,69.9,contact,1
fix_near,2.5,265.7,32.9,76.8,contact,1
drop_s1_t2,1.0,84.4,0.0,-131.1,tendon,0
drop_s1_t2,1.5,98.7,10.6,0.0,tendon,0
drop_s1_t2,2.0,343.2,27.5,50.8,tendon,1
drop_s1_t2,2.5,441.6,33.9,79.9,tendon,1
drop_s3_t0,1.0,67.6,0.0,0.0,tendon,0
drop_s3_t0,1.5,143.8,0.0,0.0,tendon,0
drop_s3_t0,2.0,196.1,0.0,-33.0,tendon,0
drop_s3_t0,2.5,206.7,49.9,82.5,tendon,1
drop_s1s3,1.0,161.4,0.0,-22.2,tendon,0
drop_s1s3,1.5,90.4,4.6,-22.6,tendon,0
drop_s1s3,2.0,335.9,3.8,45.4,tendon,1
drop_s1s3,2.5,458.7,44.5,84.4,tendon,1
gain_085,1.0,79.8,0.0,0.0,tendon,0
gain_085,1.5,146.2,0.0,0.0,tendon,0
gain_085,2.0,298.1,0.0,-27.6,tendon,0
gain_085,2.5,627.5,1.4,-5.6,tendon,0
gain_115,1.0,112.8,0.0,0.0,tendon,0
gain_115,1.5,185.8,0.0,-59.0,tendon,0
gain_115,2.0,368.0,31.3,79.9,tendon,1
gain_115,2.5,341.1,86.0,31.0,tendon,1
ws_xm60,1.0,548.5,0.0,-8.4,workspace2,0
ws_xm60,1.5,1609.5,0.0,-22.4,workspace2,0
ws_xm60,2.5,336.4,27.9,35.0,workspace2,1
ws_yp60,1.0,672.1,0.0,-58.1,workspace2,0
ws_yp60,1.5,1144.7,31.3,60.2,workspace2,1
ws_yp60,2.5,365.9,84.0,80.2,workspace2,1
ws_zm60,1.0,35.7,0.0,0.0,workspace2,0
ws_zm60,1.5,40.7,0.0,0.0,workspace2,0
ws_zm60,2.5,54.3,0.0,0.0,workspace2,0
pen2,1.0,120.4,0.6,0.0,loading,0
pen2,1.5,192.3,4.2,18.2,loading,1
pen2,2.5,1028.3,44.1,64.2,loading,1
pen4,1.0,119.4,3.4,6.0,loading,1
pen4,1.5,277.6,8.6,24.6,loading,1
pen4,2.5,718.8,43.7,61.5,loading,1
pen6,1.0,126.8,1.2,1.5,loading,1
pen6,1.5,385.9,9.4,16.5,loading,1
pen6,2.5,846.4,46.1,57.1,loading,1"""
rows = list(csv.DictReader(io.StringIO(CSV)))
for r in rows:
    r["sat"] = float(r["sat"]); r["d"] = float(r["d"]); r["k"] = float(r["k"]); r["pos"] = int(r["pos"])
KUP = 160.0

plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
                     "mathtext.fontset": "dejavuserif", "font.size": 8})
fig, ax = plt.subplots(figsize=(3.35, 2.0), dpi=300)
fig.subplots_adjust(left=0.175, right=0.985, top=0.965, bottom=0.175)

def tx(s):
    return math.log10(max(s, 0.0) + 0.1)

x1 = tx(1.0)
ax.axvspan(x1, tx(90), color="#f2f2f2", zorder=0)
ax.axvline(x1, ls=(0, (4, 2)), lw=0.8, color="#1a1a1a", zorder=1)
ax.axhline(0, lw=0.8, color="#1a1a1a", zorder=1)

HI, LO = "#b3261e", "#1f4e79"
jz = 0
for r in rows:
    x = tx(r["sat"])
    if r["sat"] < 0.05:
        x += ((jz % 9) - 4) * 0.010
        jz += 1
    col = HI if r["k"] > KUP else LO
    if r["pos"]:
        ax.plot([x], [r["d"]], "o", ms=2.4, mfc=col, mec=col, mew=0.4, zorder=3)
    else:
        ax.plot([x], [r["d"]], "o", ms=2.2, mfc="none", mec=col, mew=0.85, zorder=3)

ax.set_xlim(tx(0) - 0.13, tx(90))
ax.set_ylim(-140, 92)
ticks = [0, 0.2, 1, 2, 5, 10, 20, 50]
ax.set_xticks([tx(t) for t in ticks])
ax.set_xticklabels(["0", "0.2", "1", "2", "5", "10", "20", "50"])
ax.set_yticks([-120, -80, -40, 0, 40, 80])
ax.set_yticklabels(["\u2212120", "\u221280", "\u221240", "0", "+40", "+80"])
ax.set_xlabel("sustained saturation ratio (%)", labelpad=2)
ax.set_ylabel("error reduction \u0394 (%)", labelpad=1)
ax.tick_params(width=0.6, length=2.6, pad=1.6)
for s in ax.spines.values():
    s.set_linewidth(0.8)
ax.text(x1 + 0.05, 86, "1%", fontsize=7.4, va="top")

h = [Line2D([], [], marker="o", ls="none", ms=2.6, mfc=HI, mec=HI, label="\u03ba>160"),
     Line2D([], [], marker="o", ls="none", ms=2.4, mfc="none", mec=LO, mew=0.9, label="\u03ba\u2264160")]
ax.legend(handles=h, loc="upper left", frameon=False, fontsize=7.2,
          handletextpad=0.45, borderpad=0.05, labelspacing=0.22,
          bbox_to_anchor=(0.012, 0.995))
ax.text(0.016, 0.845, "filled: gain\nhollow: none", transform=ax.transAxes,
        fontsize=6.3, va="top", linespacing=1.30)

out = "/tmp/fig5_criterion_plane.png"
fig.savefig(out, dpi=300)
print("saved", out, os.path.getsize(out))
lo = [r for r in rows if r["sat"] < 1.0]; hi = [r for r in rows if r["sat"] >= 1.0]
print("left %d / pos %d | right %d / pos %d" % (len(lo), sum(r["pos"] for r in lo), len(hi), sum(r["pos"] for r in hi)))
import base64
print("PNG_B64_BEGIN")
print(base64.b64encode(open(out, "rb").read()).decode())
print("PNG_B64_END")
