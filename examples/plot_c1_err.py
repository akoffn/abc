import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    d = np.load(path)
    return d["ts"], d["errs"]


def summarize(name, ts, errs):
    mean = float(np.mean(errs))
    mx = float(np.max(errs))
    p50 = float(np.percentile(errs, 50))
    p95 = float(np.percentile(errs, 95))
    p99 = float(np.percentile(errs, 99))
    n_over_10 = int(np.sum(errs > 10.0))
    n_over_20 = int(np.sum(errs > 20.0))

    print("=== %s ===" % name)
    print("  n_samples = %d" % len(errs))
    print("  mean      = %.3f mm" % mean)
    print("  max       = %.3f mm" % mx)
    print("  p50       = %.3f mm" % p50)
    print("  p95       = %.3f mm" % p95)
    print("  p99       = %.3f mm" % p99)
    print("  >10mm     = %d (%.1f%%)" % (n_over_10, 100.0*n_over_10/len(errs)))
    print("  >20mm     = %d (%.1f%%)" % (n_over_20, 100.0*n_over_20/len(errs)))
    ratio = mean / max(p50, 1e-9)
    print("  mean/p50  = %.2f   (<1.5 持续偏高, >2.0 尖峰主导)" % ratio)


def main(paths):
    fig, axes = plt.subplots(len(paths), 1, figsize=(12, 3 * len(paths)),
                             sharex=False)
    if len(paths) == 1:
        axes = [axes]

    for ax, path in zip(axes, paths):
        ts, errs = load(path)
        summarize(path, ts, errs)
        ax.plot(ts, errs, lw=0.8)
        ax.axhline(10.0, color="orange", ls="--", lw=0.6)
        ax.axhline(20.0, color="red", ls="--", lw=0.6)
        ax.set_ylabel("err (mm)")
        ax.set_title(path, fontsize=9)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("t (s)")
    plt.tight_layout()
    plt.savefig("c1_err_timeseries.png", dpi=130)
    print("\n[saved] c1_err_timeseries.png")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        paths = [
            "results_official_dt/S2.00.npz",
            "results_official_dt/S2.10.npz",
            "results_official_dt/S2.20.npz",
            "results_official_dt/S2.50.npz",
        ]
    else:
        paths = sys.argv[1:]
    main(paths)
