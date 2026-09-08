"""So sánh các phương án xử lý lỗ hổng dữ liệu, phục vụ QĐ-008.

Chạy:
    python scripts/gap_policy_eval.py

Đo trên mẫu của cả ba môi trường, cho mỗi phương án:
  - số dòng huấn luyện hợp lệ còn lại (h=1 và h=12)
  - số chuỗi/đoạn giữ được
  - phân phối target của phần GIỮ so với phần BỎ (kiểm thiên lệch chọn mẫu)

Phương án:
  P0  luật hiện hành  : ffill(3) rồi cắt tại lỗ hổng đầu tiên còn lại
  P1  che theo dòng   : giữ nguyên chuỗi, bỏ dòng có cửa sổ chạm NaN
  P2  cắt đoạn        : tách tại mọi lỗ hổng, giữ đoạn đủ dài
  P3  nội suy ngắn + cắt đoạn : nội suy tuyến tính lỗ hổng <= K, rồi như P2
"""

import glob
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

GRID = 300
WINDOW = 8 * 86400 // GRID       # 2304
MAXLAG = 24                       # cửa sổ đặc trưng sâu nhất, protocol mục 8
INTERP_MAX = 2                    # P3: nội suy lỗ hổng tối đa 2 điểm (10 phút)
MIN_SEG = 288                     # P2/P3: đoạn tối thiểu 1 ngày
SEED = 42


def grid_series(times, values):
    b = np.floor(np.asarray(times, dtype="float64") / GRID).astype("int64")
    s = pd.Series(np.asarray(values, dtype="float64")).groupby(b).mean()
    s = s.reindex(pd.RangeIndex(s.index.min(), s.index.max() + 1))
    return s.iloc[:WINDOW]


def gap_runs(na):
    """Độ dài các cụm NaN liên tiếp."""
    runs, c = [], 0
    for x in na:
        if x:
            c += 1
        elif c:
            runs.append(c)
            c = 0
    if c:
        runs.append(c)
    return runs


def rows_from_mask(ok, h):
    """Số dòng hợp lệ: cửa sổ [t-MAXLAG, t] và target t+h đều không NaN."""
    n = len(ok)
    if n <= MAXLAG + h:
        return 0, np.zeros(n, bool)
    valid = np.ones(n, bool)
    for k in range(MAXLAG + 1):
        valid[k:] &= ok[: n - k] if k else ok
    valid[:MAXLAG] = False
    sel = np.zeros(n, bool)
    sel[: n - h] = valid[: n - h] & ok[h:]
    return int(sel.sum()), sel


def segments(ok, min_len):
    """Các đoạn liên tục không NaN, dài >= min_len. Trả về list (start, stop)."""
    out, start = [], None
    for i, x in enumerate(ok):
        if x and start is None:
            start = i
        elif not x and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    if start is not None and len(ok) - start >= min_len:
        out.append((start, len(ok)))
    return out


def interp_short(s, k):
    """Nội suy tuyến tính chỉ những lỗ hổng dài <= k. Lỗ hổng dài hơn giữ NaN."""
    filled = s.interpolate(method="linear", limit=k, limit_area="inside")
    na = s.isna().values
    keep = np.zeros(len(s), bool)
    i = 0
    while i < len(s):
        if na[i]:
            j = i
            while j < len(s) and na[j]:
                j += 1
            if j - i <= k:
                keep[i:j] = True
            i = j
        else:
            i += 1
    out = s.copy()
    out.values[keep] = filled.values[keep]
    return out


def evaluate(series_list, label):
    agg = {p: dict(rows1=0, rows12=0, units=0) for p in ("P0", "P1", "P2", "P3")}
    kept_vals, dropped_vals = [], []
    all_runs, na_ratios = [], []

    for s in series_list:
        na = s.isna().values
        ok = ~na
        na_ratios.append(na.mean())
        all_runs.extend(gap_runs(na))

        # P0 — luật hiện hành
        f = s.ffill(limit=3)
        bad = f.isna().values
        cut = int(np.argmax(bad)) if bad.any() else len(s)
        if cut > MAXLAG + 12:
            agg["P0"]["rows1"] += cut - MAXLAG - 1
            agg["P0"]["rows12"] += cut - MAXLAG - 12
            agg["P0"]["units"] += 1

        # P1 — che theo dòng
        r1, sel1 = rows_from_mask(ok, 1)
        r12, _ = rows_from_mask(ok, 12)
        agg["P1"]["rows1"] += r1
        agg["P1"]["rows12"] += r12
        agg["P1"]["units"] += 1 if r12 > 0 else 0
        if r1:
            kept_vals.append(s.values[sel1])
            dropped_vals.append(s.values[~sel1 & ok])

        # P2 — cắt đoạn
        for a, b in segments(ok, MIN_SEG):
            L = b - a
            agg["P2"]["rows1"] += max(0, L - MAXLAG - 1)
            agg["P2"]["rows12"] += max(0, L - MAXLAG - 12)
            agg["P2"]["units"] += 1

        # P3 — nội suy ngắn rồi cắt đoạn
        s3 = interp_short(s, INTERP_MAX)
        for a, b in segments(~s3.isna().values, MIN_SEG):
            L = b - a
            agg["P3"]["rows1"] += max(0, L - MAXLAG - 1)
            agg["P3"]["rows12"] += max(0, L - MAXLAG - 12)
            agg["P3"]["units"] += 1

    runs = pd.Series(all_runs, dtype="float64")
    print(f"===== {label}  ({len(series_list)} chuỗi) =====")
    print(f"  NaN trung vị {np.median(na_ratios)*100:6.2f}%   "
          f"số cụm lỗ hổng {len(runs)}")
    if len(runs):
        print(f"  Độ dài cụm lỗ hổng: trung vị {runs.median():.0f}  "
              f"p90 {runs.quantile(.9):.0f}  max {runs.max():.0f}  "
              f"| cụm <= {INTERP_MAX} điểm chiếm {(runs <= INTERP_MAX).mean()*100:.1f}%")
    print()
    base = agg["P1"]["rows12"] or 1
    print(f"  {'phương án':<34}{'dòng h=1':>12}{'dòng h=12':>12}{'đơn vị':>9}{'so P1':>9}")
    names = {
        "P0": "P0 ffill(3) + cắt  (hiện hành)",
        "P1": "P1 che theo dòng",
        "P2": f"P2 cắt đoạn (>= {MIN_SEG})",
        "P3": f"P3 nội suy <= {INTERP_MAX} + cắt đoạn",
    }
    for p in ("P0", "P1", "P2", "P3"):
        a = agg[p]
        print(f"  {names[p]:<34}{a['rows1']:>12,}{a['rows12']:>12,}"
              f"{a['units']:>9}{a['rows12']/base*100:>8.0f}%")
    print()

    if kept_vals:
        k = np.concatenate(kept_vals)
        d = np.concatenate([x for x in dropped_vals if len(x)]) if any(
            len(x) for x in dropped_vals) else np.array([])
        print(f"  Thiên lệch chọn mẫu (P1): CPU% trung vị "
              f"giữ {np.median(k):.2f}  vs  bỏ "
              f"{np.median(d):.2f}" if len(d) else
              f"  Thiên lệch chọn mẫu (P1): không có dòng nào bị bỏ")
    print()
    return agg


def load_bitbrains(pattern, n):
    random.seed(SEED)
    fs = sorted(glob.glob(str(pattern)))
    out = []
    for f in random.sample(fs, min(n, len(fs))):
        d = pd.read_csv(f, sep=";\t", engine="python")
        if "CPU usage [%]" not in d.columns:
            continue
        v = pd.to_numeric(d["CPU usage [%]"], errors="coerce").clip(0, 100)
        s = grid_series(d["Timestamp [ms]"], v)
        if s.mean(skipna=True) >= 1.0 and s.nunique(dropna=True) >= 3:
            out.append(s)
    return out


def load_alibaba(n_rows=6_000_000):
    path = RAW / "Alibaba-Cluster-Trace" / "machine_usage.csv"
    df = pd.read_csv(path, names=["m", "t", "c"], usecols=[0, 1, 2],
                     nrows=n_rows).dropna()
    out = []
    for m, g in df.groupby("m"):
        s = grid_series(g["t"], g["c"].clip(0, 100))
        if len(s) >= 500 and s.mean(skipna=True) >= 1.0 and s.nunique(dropna=True) >= 3:
            out.append(s)
    return out


if __name__ == "__main__":
    evaluate(load_bitbrains(RAW / "Bitbrains-fastStorage" / "08-2013" / "*.csv", 120), "E1")
    evaluate(load_bitbrains(RAW / "Bitbrains-Rnd" / "2013-8" / "*.csv", 120), "E2")
    evaluate(load_alibaba(), "E3")
