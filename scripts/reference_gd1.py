"""Số liệu tham chiếu cho cổng GĐ1 — bản hiện thực độc lập của protocol mục 5-7.

Bản do A viết, dùng làm thước đo đối chiếu với kết quả của B. Hai bản hiện thực độc
lập ra cùng con số là bằng chứng mạnh; lệch nhau là dấu hiệu có lỗi ở một trong hai
bên. KHÔNG dùng tệp này thay cho `src/cwp/` của B.

Chính sách xử lý lỗ hổng theo QĐ-008 (K = 2). Đặt K = 0 để kiểm tra độ vững:
    python scripts/reference_gd1.py --env all --interp 0

Chạy:
    python scripts/reference_gd1.py --env E1
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

GRID = 300                  # protocol mục 5
WINDOW = 8 * 86400 // GRID  # protocol mục 7 -> 2304 điểm
CLIP = (0.0, 100.0)         # protocol mục 6
INTERP_MAX = 2              # QĐ-008: nội suy lỗ hổng <= 2 điểm
MAXLAG = 24                 # protocol mục 8, cửa sổ đặc trưng sâu nhất
HORIZONS = (1, 6, 12)       # protocol mục 10
MIN_ROWS = 500              # QĐ-008: ngưỡng thay cho "độ dài >= 2000"
MIN_MEAN = 1.0
MIN_UNIQUE = 3
SEED = 42
E3_SAMPLE_N, E3_STRATA = 500, 5

BB_SEP = ";\t"
BB_TARGET = "CPU usage [%]"
BB_TIME = "Timestamp [ms]"  # thực tế là giây, xem explain.md


def to_buckets(times, values):
    """Gộp về lưới 5 phút tuyệt đối. Chỉ số trả về là số hiệu bucket."""
    b = np.floor(np.asarray(times, dtype="float64") / GRID).astype("int64")
    return pd.Series(np.asarray(values, dtype="float64")).groupby(b).mean()


def window_series(s, b0):
    """Cắt về cửa sổ toàn cục [b0, b0 + WINDOW). Bucket rỗng để NaN."""
    return s.reindex(pd.RangeIndex(b0, b0 + WINDOW))


def interp_short(s, k):
    """Nội suy tuyến tính CHỈ những lỗ hổng dài <= k. Lỗ hổng dài hơn giữ NaN."""
    if k <= 0:
        return s, 0
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
    # Đếm điểm THỰC SỰ được nội suy, không đếm `keep`. `keep` gồm cả cụm ngắn chạm
    # mép cửa sổ, mà `limit_area="inside"` không lấp vì thiếu neo một phía — đếm
    # chúng là khai khống một can thiệp chưa xảy ra. Sai 24 điểm ở E3 (1.738 thay vì
    # 1.714, tức 0,167% thay vì 0,165%); E1 và E2 không có cụm nào như vậy nên không
    # lệch. Dữ liệu luôn đúng, chỉ con số báo cáo sai. Xem gate-gd1.md mục 5.5.
    return out, int(na.sum() - out.isna().to_numpy().sum())


def valid_rows(ok, h):
    """Dòng hợp lệ: cửa sổ [t-MAXLAG, t] và target t+h đều không NaN."""
    n = len(ok)
    if n <= MAXLAG + h:
        return 0
    v = np.ones(n, bool)
    for k in range(MAXLAG + 1):
        v[k:] &= ok[: n - k] if k else ok
    v[:MAXLAG] = False
    return int((v[: n - h] & ok[h:]).sum())


def judge(s_obs, s_use):
    """Áp bộ lọc chuỗi. Trả về lý do loại, hoặc None nếu giữ."""
    if s_obs.notna().sum() == 0:
        return "ngoai_cua_so"
    if s_obs.mean(skipna=True) < MIN_MEAN:
        return "gan_chet"
    if s_obs.nunique(dropna=True) < MIN_UNIQUE:
        return "hang"
    if valid_rows(~s_use.isna().values, max(HORIZONS)) < MIN_ROWS:
        return "it_dong"
    return None


def process(raw_series, name, n_in, clipped_hi, n_raw, interp_k):
    """raw_series: dict id -> Series theo bucket, chưa cắt cửa sổ."""
    b0 = min(int(s.index.min()) for s in raw_series.values())
    kept, rejected = [], {}
    interp_pts = total_pts = 0
    rows = {h: 0 for h in HORIZONS}

    for s in raw_series.values():
        w = window_series(s, b0)
        u, n_int = interp_short(w, interp_k)
        why = judge(w, u)
        if why:
            rejected[why] = rejected.get(why, 0) + 1
            continue
        kept.append(u)
        interp_pts += n_int
        total_pts += int(u.notna().sum())
        for h in HORIZONS:
            rows[h] += valid_rows(~u.isna().values, h)

    pooled = pd.concat(kept) if kept else pd.Series(dtype="float64")
    return {
        "env": name,
        "interp_k": interp_k,
        "chuoi_vao": n_in,
        "loai_ngoai_cua_so": rejected.get("ngoai_cua_so", 0),
        "loai_gan_chet": rejected.get("gan_chet", 0),
        "loai_hang": rejected.get("hang", 0),
        "loai_it_dong": rejected.get("it_dong", 0),
        "chuoi_con_lai": len(kept),
        "ti_le_giu_pct": round(len(kept) / n_in * 100, 2) if n_in else 0.0,
        "dong_h1": rows[1],
        "dong_h6": rows[6],
        "dong_h12": rows[12],
        "diem_noi_suy": interp_pts,
        "ti_le_noi_suy_pct": round(interp_pts / total_pts * 100, 3) if total_pts else 0.0,
        "mau_clip_tren_100": clipped_hi,
        "ti_le_clip_pct": round(clipped_hi / n_raw * 100, 4) if n_raw else 0.0,
        "target_mean": round(float(pooled.mean()), 4) if len(pooled) else None,
        "target_p50": round(float(pooled.median()), 4) if len(pooled) else None,
        "target_std": round(float(pooled.std()), 4) if len(pooled) else None,
    }


def run_bitbrains(name, pattern, interp_k):
    files = sorted(glob.glob(str(pattern)))
    series = {}
    hi = n_raw = 0
    for f in files:
        d = pd.read_csv(f, sep=BB_SEP, engine="python")
        if BB_TARGET not in d.columns or len(d) == 0:
            continue
        v = pd.to_numeric(d[BB_TARGET], errors="coerce")
        n_raw += int(v.notna().sum())
        hi += int((v > CLIP[1]).sum())
        series[Path(f).stem] = to_buckets(d[BB_TIME], v.clip(*CLIP))
    return process(series, name, len(files), hi, n_raw, interp_k)


def run_alibaba(interp_k):
    path = RAW / "Alibaba-Cluster-Trace" / "machine_usage.csv"
    cols = ["machine_id", "time_stamp", "cpu_util_percent"]

    # Danh sách máy ĐÃ ĐÓNG BĂNG (QĐ-009). Trước đây chọn mẫu ngay tại đây, nhưng
    # kết quả phụ thuộc thứ tự quét tệp nên A và B ra hai tập khác nhau — chỉ trùng
    # 56/500. Đọc danh sách cố định cũng bỏ được luôn lượt quét thứ nhất.
    from freeze_e3_sample import load_frozen
    chosen = set(load_frozen())
    print(f"  [E3] dùng danh sách đóng băng: {len(chosen)} máy", flush=True)

    parts = []
    for ch in pd.read_csv(path, names=cols, usecols=[0, 1, 2], chunksize=5_000_000):
        parts.append(ch[ch.machine_id.isin(chosen)])
    df = pd.concat(parts)

    series = {}
    hi = n_raw = 0
    for m, g in df.groupby("machine_id"):
        v = pd.to_numeric(g["cpu_util_percent"], errors="coerce")
        n_raw += int(v.notna().sum())
        hi += int((v > CLIP[1]).sum())
        series[m] = to_buckets(g["time_stamp"], v.clip(*CLIP))
    return process(series, "E3", len(chosen), hi, n_raw, interp_k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="all", choices=["E1", "E2", "E3", "all"])
    ap.add_argument("--interp", type=int, default=INTERP_MAX,
                    help="K của QĐ-008. 0 = không nội suy, dùng để kiểm tra độ vững.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    envs = {
        "E1": lambda: run_bitbrains(
            "E1", RAW / "Bitbrains-fastStorage" / "08-2013" / "*.csv", a.interp),
        "E2": lambda: run_bitbrains(
            "E2", RAW / "Bitbrains-Rnd" / "2013-8" / "*.csv", a.interp),
        "E3": lambda: run_alibaba(a.interp),
    }
    targets = ["E1", "E2", "E3"] if a.env == "all" else [a.env]
    out = []
    for e in targets:
        print(f"[{e}] đang chạy (K={a.interp})...", flush=True)
        out.append(envs[e]())
        print(f"[{e}] xong", flush=True)

    print()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if a.out:
        p = ROOT / a.out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nĐã ghi: " + str(p))


if __name__ == "__main__":
    main()
