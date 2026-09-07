"""Tính số liệu tham chiếu cho cổng GĐ1.

Đây là bản hiện thực ĐỘC LẬP của protocol mục 5, 6, 7 do A viết, dùng làm thước đo
đối chiếu với kết quả của B. Hai bản hiện thực độc lập ra cùng con số là bằng chứng
mạnh; lệch nhau là dấu hiệu có lỗi ở một trong hai bên.

KHÔNG dùng tệp này thay cho `src/cwp/` của B. Nó cố tình viết thô, chậm, dễ đọc.

Chạy:
    python scripts/reference_gd1.py --env E1
    python scripts/reference_gd1.py --env E2
    python scripts/reference_gd1.py --env E3      # lâu, quét 9 GB hai lượt
    python scripts/reference_gd1.py --env all --out results/tables/reference_gd1.json
"""

import argparse
import glob
import json
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

GRID = 300                      # protocol mục 5
WINDOW_DAYS = 8                 # protocol mục 7
WINDOW_SEC = WINDOW_DAYS * 86400
CLIP = (0.0, 100.0)             # protocol mục 6.1
MIN_LEN = 2000                  # protocol mục 6.5
MAX_NAN = 0.20
MIN_MEAN = 1.0
MIN_UNIQUE = 3
FFILL_LIMIT = 3                 # protocol mục 6.6
SEED = 42
E3_SAMPLE_N = 500               # protocol mục 3
E3_STRATA = 5

BITBRAINS_SEP = ";\t"
BB_TARGET = "CPU usage [%]"
BB_TIME = "Timestamp [ms]"      # thực tế là giây, xem explain.md


def grid_series(times, values):
    """Căn về lưới 5 phút tuyệt đối. Bucket rỗng để NaN, không nội suy."""
    b = np.floor(np.asarray(times, dtype="float64") / GRID).astype("int64")
    s = pd.Series(np.asarray(values, dtype="float64")).groupby(b).mean()
    full = pd.RangeIndex(s.index.min(), s.index.max() + 1)
    return s.reindex(full)


def apply_window(s):
    """Giữ 8 ngày đầu tính từ điểm đầu tiên của chuỗi."""
    n = WINDOW_SEC // GRID
    return s.iloc[:n]


def judge(s):
    """Áp bốn điều kiện lọc, trả về tên điều kiện đầu tiên bị vi phạm hoặc None."""
    if len(s) < MIN_LEN:
        return "do_dai"
    if s.isna().mean() > MAX_NAN:
        return "nan"
    if s.mean(skipna=True) < MIN_MEAN:
        return "gan_chet"
    if s.nunique(dropna=True) < MIN_UNIQUE:
        return "hang"
    return None


def finalize(s):
    """ffill tối đa 3 bước, còn thiếu thì cắt chuỗi tại đó."""
    s = s.ffill(limit=FFILL_LIMIT)
    bad = s.isna()
    if bad.any():
        s = s.iloc[: int(np.argmax(bad.values))]
    return s


def summarize(name, kept, rejected, n_in, clipped_lo, clipped_hi, n_raw):
    pooled = pd.concat(kept) if kept else pd.Series(dtype="float64")
    lens = pd.Series([len(x) for x in kept]) if kept else pd.Series(dtype="int64")
    return {
        "env": name,
        "chuoi_vao": n_in,
        "loai_do_dai": rejected.get("do_dai", 0),
        "loai_nan": rejected.get("nan", 0),
        "loai_gan_chet": rejected.get("gan_chet", 0),
        "loai_hang": rejected.get("hang", 0),
        "chuoi_con_lai": len(kept),
        "ti_le_giu": round(len(kept) / n_in * 100, 2) if n_in else 0.0,
        "diem_du_lieu": int(lens.sum()) if len(lens) else 0,
        "do_dai_trung_vi": int(lens.median()) if len(lens) else 0,
        "mau_bi_clip_duoi": clipped_lo,
        "mau_bi_clip_tren": clipped_hi,
        "ti_le_clip_tren_pct": round(clipped_hi / n_raw * 100, 4) if n_raw else 0.0,
        "target_mean": round(float(pooled.mean()), 4) if len(pooled) else None,
        "target_p50": round(float(pooled.median()), 4) if len(pooled) else None,
        "target_std": round(float(pooled.std()), 4) if len(pooled) else None,
    }


def run_bitbrains(name, pattern):
    files = sorted(glob.glob(str(pattern)))
    kept, rejected = [], {}
    lo = hi = n_raw = 0
    for f in files:
        d = pd.read_csv(f, sep=BITBRAINS_SEP, engine="python")
        if BB_TARGET not in d.columns or len(d) == 0:
            rejected["do_dai"] = rejected.get("do_dai", 0) + 1
            continue
        v = pd.to_numeric(d[BB_TARGET], errors="coerce")
        n_raw += int(v.notna().sum())
        lo += int((v < CLIP[0]).sum())
        hi += int((v > CLIP[1]).sum())
        v = v.clip(*CLIP)
        s = apply_window(grid_series(d[BB_TIME], v))
        why = judge(s)
        if why:
            rejected[why] = rejected.get(why, 0) + 1
        else:
            kept.append(finalize(s))
    return summarize(name, kept, rejected, len(files), lo, hi, n_raw)


def run_alibaba():
    path = RAW / "Alibaba-Cluster-Trace" / "machine_usage.csv"
    cols = ["machine_id", "time_stamp", "cpu_util_percent"]

    # Lượt 1 — trung bình CPU từng máy, để phân tầng
    tot, cnt = {}, {}
    for ch in pd.read_csv(path, names=cols, usecols=[0, 1, 2], chunksize=5_000_000):
        g = ch.groupby("machine_id")["cpu_util_percent"].agg(["sum", "count"])
        for m, r in g.iterrows():
            tot[m] = tot.get(m, 0.0) + r["sum"]
            cnt[m] = cnt.get(m, 0) + r["count"]
    means = pd.Series({m: tot[m] / cnt[m] for m in tot if cnt[m] > 0})
    print(f"  [E3] tổng số máy quét được: {len(means)}", flush=True)

    # Mẫu phân tầng 5 tầng x 100 máy, random_state=42
    strata = pd.qcut(means.rank(method="first"), E3_STRATA, labels=False)
    per = E3_SAMPLE_N // E3_STRATA
    chosen = []
    for k in range(E3_STRATA):
        pool = means.index[strata == k]
        chosen.extend(pd.Series(list(pool)).sample(per, random_state=SEED).tolist())
    chosen = set(chosen)
    print(f"  [E3] đã chọn {len(chosen)} máy", flush=True)

    # Lượt 2 — chỉ đọc các máy đã chọn
    parts = []
    for ch in pd.read_csv(path, names=cols, usecols=[0, 1, 2], chunksize=5_000_000):
        parts.append(ch[ch.machine_id.isin(chosen)])
    df = pd.concat(parts)

    kept, rejected = [], {}
    lo = hi = n_raw = 0
    for m, g in df.groupby("machine_id"):
        v = pd.to_numeric(g["cpu_util_percent"], errors="coerce")
        n_raw += int(v.notna().sum())
        lo += int((v < CLIP[0]).sum())
        hi += int((v > CLIP[1]).sum())
        v = v.clip(*CLIP)
        s = apply_window(grid_series(g["time_stamp"], v))
        why = judge(s)
        if why:
            rejected[why] = rejected.get(why, 0) + 1
        else:
            kept.append(finalize(s))
    return summarize("E3", kept, rejected, len(chosen), lo, hi, n_raw)


ENVS = {
    "E1": lambda: run_bitbrains("E1", RAW / "Bitbrains-fastStorage" / "08-2013" / "*.csv"),
    "E2": lambda: run_bitbrains("E2", RAW / "Bitbrains-Rnd" / "2013-8" / "*.csv"),
    "E3": run_alibaba,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="all", choices=["E1", "E2", "E3", "all"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    targets = ["E1", "E2", "E3"] if a.env == "all" else [a.env]
    out = []
    for e in targets:
        print(f"[{e}] đang chạy...", flush=True)
        out.append(ENVS[e]())
        print(f"[{e}] xong", flush=True)

    print()
    print(json.dumps(out, ensure_ascii=False, indent=2))

    if a.out:
        p = ROOT / a.out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nĐã ghi: {p}")


if __name__ == "__main__":
    main()
