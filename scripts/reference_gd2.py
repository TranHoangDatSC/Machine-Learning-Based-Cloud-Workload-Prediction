"""Số liệu tham chiếu cho cổng GĐ2 — bản hiện thực độc lập của protocol mục 8.

Bản do A viết, dùng làm thước đo đối chiếu với `src/cwp/features/` của B. Hai bản
hiện thực độc lập ra cùng con số là bằng chứng mạnh; lệch nhau là dấu hiệu có lỗi ở
một trong hai bên — và GĐ1 đã cho thấy bên sai có thể là A. KHÔNG dùng tệp này thay
cho `src/cwp/` của B, và đừng đưa nó cho agent đang viết phần của B đọc.

Cố tình dùng cách tiếp cận khác B: mỗi môi trường được nạp thành **một ma trận
numpy 2 chiều `(số chuỗi, 2304)`** rồi dịch theo trục thời gian, thay vì
`groupby(series_id)` trên bảng dài. Ranh giới chuỗi khi đó là ranh giới hàng, nên
lỗi bắc cầu giữa hai chuỗi không thể xảy ra về mặt cấu trúc — độc lập cả về lối
nghĩ, không chỉ về dòng mã.

Chạy:
    python scripts/reference_gd2.py --env E1
    python scripts/reference_gd2.py --env all --out results/tables/reference_gd2.json

Đầu vào là `data/processed/` — sản phẩm GĐ1 đã kiểm chéo và khớp tuyệt đối, nên hai
bên xuất phát từ cùng một chỗ. Script chỉ đọc, không sửa gì.
"""

import argparse
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
PROC = ROOT / "data" / "processed"
CATALOG = ROOT / "data" / "catalog.parquet"

GRID = 300                   # protocol mục 5
WINDOW = 8 * 86400 // GRID   # protocol mục 7 -> 2304 bucket
MAXLAG = 24                  # protocol mục 8, cửa sổ đặc trưng sâu nhất
HORIZONS = (1, 6, 12)        # protocol mục 10

LAGS = (1, 2, 3, 6, 12, 24)          # protocol mục 8
ROLL_WINDOWS = (6, 12)               # protocol mục 8
ROLL_STATS = ("mean", "std", "min", "max")

# pandas `.rolling().std()` mặc định ddof=1. Chốt theo đó để hai bản so được với
# nhau; protocol mục 8 không nói, xem ghi chú "Quy ước chưa có trong protocol" ở
# cuối tệp.
DDOF = 1

# Lag để đo ACF. 288 bucket = 24 giờ, dùng để nhìn chu kỳ ngày.
ACF_LAGS = (1, 6, 12, 24, 288)

ENVS = ("E1", "E2", "E3")


# ------------------------------------------------------------------ nạp dữ liệu

def load_env(env):
    """Đọc một môi trường thành ma trận (n_series, WINDOW).

    Mỗi chuỗi giữ lại đều đã được `apply_window` đưa về đúng WINDOW bucket liên tục,
    nên bảng dài chia hết thành lưới chữ nhật. Nếu không chia hết thì sản phẩm GĐ1
    có vấn đề và phải dừng, không được đoán.
    """
    f = PROC / f"{env}.parquet"
    if not f.exists():
        raise FileNotFoundError(f"Không thấy {f}. Chạy `python -m cwp.preprocess.build --env all` trước.")

    df = pd.read_parquet(f, columns=["series_id", "bucket", "y"])
    df = df.sort_values(["series_id", "bucket"], kind="mergesort").reset_index(drop=True)

    ids = df["series_id"].to_numpy()
    uniq, first = np.unique(ids, return_index=True)
    series_ids = ids[np.sort(first)]          # giữ thứ tự xuất hiện
    n_series = len(series_ids)

    if len(df) != n_series * WINDOW:
        raise ValueError(
            f"{env}: {len(df)} dòng không chia hết thành {n_series} chuỗi x {WINDOW} bucket. "
            "Cửa sổ 8 ngày chưa được áp đều cho mọi chuỗi."
        )

    b = df["bucket"].to_numpy().reshape(n_series, WINDOW)
    if not np.all(b == b[0]):
        raise ValueError(f"{env}: các chuỗi không cùng dải bucket — cửa sổ phải TOÀN CỤC (protocol mục 7).")
    if not np.all(np.diff(b[0]) == 1):
        raise ValueError(f"{env}: bucket không liên tục từng bước 1.")

    Y = df["y"].to_numpy(dtype="float64").reshape(n_series, WINDOW)
    return series_ids, int(b[0, 0]), Y


# --------------------------------------------------------------- sinh đặc trưng

def _shift_right(Y, k):
    """Giá trị tại t-k. Cột đầu thiếu lịch sử thì để NaN, không lấy từ chuỗi khác."""
    out = np.full_like(Y, np.nan)
    if k < Y.shape[1]:
        out[:, k:] = Y[:, :-k]
    return out


def _rolling_past(Y, w, stat):
    """Thống kê trên đúng w điểm QUÁ KHỨ y[t-w] .. y[t-1], KHÔNG gồm y[t].

    protocol mục 8: "Mọi thống kê rolling tính chỉ trên quá khứ, không bao gồm điểm
    hiện tại." Cửa sổ thiếu điểm hoặc dính NaN đều ra NaN — không có min_periods=1.
    """
    n, m = Y.shape
    out = np.full((n, m), np.nan)
    if w >= m:
        return out

    # sw[i, j] = Y[i, j : j+w]; vị trí t dùng cửa sổ bắt đầu ở j = t-w.
    sw = np.lib.stride_tricks.sliding_window_view(Y, w, axis=1)[:, : m - w]

    # Chia khối theo chuỗi để không dựng mảng tạm quá lớn trên E1 (735 x 2298 x 12).
    step = max(1, 4_000_000 // (sw.shape[1] * w))
    for s in range(0, n, step):
        blk = sw[s : s + step]
        if stat == "mean":
            val = blk.mean(axis=2)
        elif stat == "std":
            val = blk.std(axis=2, ddof=DDOF)
        elif stat == "min":
            val = blk.min(axis=2)
        elif stat == "max":
            val = blk.max(axis=2)
        else:
            raise ValueError(stat)
        out[s : s + step, w:] = val
    return out


def _calendar(b0, n_series, mode):
    """Bốn đặc trưng lịch, mã hoá sin/cos (protocol mục 8).

    `bucket * 300` là epoch giây với E1 và E2. Với E3 thì KHÔNG — Alibaba ghi giây
    kể từ lúc bắt đầu trace (b0 = 0), không mang thông tin ngày thật. Xem
    `research-log/gate-gd2.md` mục 6; QĐ-010 chưa chốt nên đây là bản tạm.
    """
    if mode == "none":
        return {}

    t = (b0 + np.arange(WINDOW, dtype="int64")) * GRID
    hour = (t // 3600) % 24
    dow = ((t // 86400) + 4) % 7          # epoch 1970-01-01 là thứ Năm -> 4

    row = {
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "dow_sin": np.sin(2 * np.pi * dow / 7),
        "dow_cos": np.cos(2 * np.pi * dow / 7),
    }
    # Cửa sổ là toàn cục nên mọi chuỗi trong một môi trường có cùng trục lịch.
    return {k: np.broadcast_to(v, (n_series, WINDOW)) for k, v in row.items()}


def build_features(Y, b0, calendar_mode):
    """19 đặc trưng theo protocol mục 8. Không thừa, không thiếu."""
    feats = {}
    for k in LAGS:
        feats[f"lag_{k}"] = _shift_right(Y, k)
    for w in ROLL_WINDOWS:
        for stat in ROLL_STATS:
            feats[f"roll_{stat}_{w}"] = _rolling_past(Y, w, stat)
    feats["diff_1"] = Y - _shift_right(Y, 1)
    feats.update(_calendar(b0, Y.shape[0], calendar_mode))
    return feats


# ---------------------------------------------------------------- dòng hợp lệ

def valid_mask(feats, Y, h):
    """Dòng hợp lệ theo protocol mục 8: TOÀN BỘ [t-24, t] và target t+h không NaN.

    **Không phải `dropna` trên ma trận đặc trưng.** Hai thứ đó khác nhau, và khác
    theo hướng nguy hiểm: 19 đặc trưng chỉ chạm 15 điểm trong cửa sổ — `t-24`,
    `t-12..t-1`, và `t`. Các điểm `t-23` đến `t-13` không đặc trưng nào dùng, nhưng
    protocol vẫn đòi chúng không NaN. Nên `dropna` LỎNG HƠN luật, và giữ lại những
    dòng mà luật đã loại: đo trên bản GĐ1 là thừa 1.513 dòng ở E2 h=1 và 7.461 dòng
    ở E3 h=1. E1 tình cờ khớp nên lỗi này không lộ ra nếu chỉ thử một môi trường.

    Luật của protocol chặt hơn và đó là chủ ý — xem mục 8, "một điểm NaN đơn lẻ làm
    hỏng 25 dòng". Bản này theo luật, rồi kiểm ngược rằng mọi dòng hợp lệ đều tính
    được đủ 19 đặc trưng.
    """
    n, m = Y.shape
    ok = np.isfinite(Y)

    # Cửa sổ [t-MAXLAG, t] sạch hoàn toàn, tính bằng cumsum -> O(n*m).
    cs = np.pad(np.cumsum(ok, axis=1), ((0, 0), (1, 0)))
    win = np.zeros((n, m), dtype=bool)
    t = np.arange(MAXLAG, m)
    win[:, t] = (cs[:, t + 1] - cs[:, t - MAXLAG]) == (MAXLAG + 1)

    tgt = np.full_like(Y, np.nan)
    if h < m:
        tgt[:, :-h] = Y[:, h:]
    mask = win & np.isfinite(tgt)

    # Kiểm ngược: luật cửa sổ phải KÉO THEO đủ đặc trưng. Chiều ngược lại thì không.
    feat_ok = np.ones((n, m), dtype=bool)
    for v in feats.values():
        feat_ok &= np.isfinite(v)
    thieu = int((mask & ~feat_ok).sum())
    if thieu:
        raise ValueError(
            f"{thieu} dòng hợp lệ theo protocol nhưng thiếu đặc trưng — "
            "cửa sổ đặc trưng đã vượt quá 24 bước, đặc tả và hiện thực lệch nhau."
        )
    return mask, tgt


# ------------------------------------------------------------------- ACF và CV

def acf_pairwise(Y, lag):
    """Tương quan tại độ trễ `lag`, loại theo CẶP (t, t+lag).

    Không dropna trước rồi mới tính: bỏ NaN kiểu đó CO TRỤC THỜI GIAN lại, khiến
    "lag 1" có thể là hai điểm cách nhau hàng giờ. Xem gate-gd2.md mục 3.4.

    Trả về (trung vị hệ số theo chuỗi, tỉ lệ % cặp bị bỏ).
    """
    a, b = Y[:, :-lag], Y[:, lag:]
    m = np.isfinite(a) & np.isfinite(b)
    n = m.sum(axis=1)

    av = np.where(m, a, 0.0)
    bv = np.where(m, b, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        sa, sb = av.sum(1), bv.sum(1)
        ma, mb = sa / n, sb / n
        ca = np.where(m, a - ma[:, None], 0.0)
        cb = np.where(m, b - mb[:, None], 0.0)
        cov = (ca * cb).sum(1)
        r = cov / np.sqrt((ca * ca).sum(1) * (cb * cb).sum(1))

    r = r[np.isfinite(r) & (n >= 2)]
    bo = 100.0 * (1.0 - m.sum() / m.size)
    return (float(np.median(r)) if len(r) else None), round(float(bo), 4)


def cv_per_series(Y):
    """Hệ số biến thiên từng chuỗi. Báo trung vị và IQR, không báo trung bình.

    Bộ lọc `gan_chet` đã bỏ mọi chuỗi mean < 1,0 nên CV bị chặn, nhưng một chuỗi
    mean 1,01 vẫn kéo trung bình đi rất xa.
    """
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.nanmean(Y, axis=1)
        sd = np.nanstd(Y, axis=1, ddof=DDOF)
        cv = sd / mu
    cv = cv[np.isfinite(cv)]
    q25, q50, q75 = np.percentile(cv, [25, 50, 75])
    return {
        "cv_p25": round(float(q25), 4),
        "cv_p50": round(float(q50), 4),
        "cv_p75": round(float(q75), 4),
        "cv_iqr": round(float(q75 - q25), 4),
    }


# ----------------------------------------------------------------------- chạy

def process(env, calendar_mode):
    series_ids, b0, Y = load_env(env)
    n_series = len(series_ids)
    feats = build_features(Y, b0, calendar_mode)

    rows = {}
    target_mean = {}
    masks = {}
    for h in HORIZONS:
        m, tgt = valid_mask(feats, Y, h)
        masks[h] = m
        rows[f"dong_h{h}"] = int(m.sum())
        target_mean[f"target_mean_h{h}"] = round(float(tgt[m].mean()), 4) if m.any() else None

    # Vân tay từng đặc trưng, lấy trên tập dòng hợp lệ của h=1.
    m1 = masks[1]
    fstats = {}
    for name, v in feats.items():
        sel = v[m1]
        fstats[name] = {
            "mean": round(float(sel.mean()), 6),
            "std": round(float(sel.std(ddof=DDOF)), 6),
            "nan_pct_toan_luoi": round(float(100.0 * (~np.isfinite(v)).mean()), 4),
        }

    acf = {}
    for lag in ACF_LAGS:
        r, bo = acf_pairwise(Y, lag)
        acf[f"acf_lag_{lag}"] = None if r is None else round(r, 4)
        acf[f"acf_lag_{lag}_bo_cap_pct"] = bo

    out = {
        "env": env,
        "n_series": n_series,
        "n_bucket_moi_chuoi": WINDOW,
        "b0": b0,
        "calendar_mode": calendar_mode,
        "moc_lich_that": b0 * GRID >= 1_000_000_000,
        "n_dac_trung": len(feats),
        "ten_dac_trung": sorted(feats),
        **rows,
        **target_mean,
        **cv_per_series(Y),
        **acf,
        "dac_trung": fstats,
    }
    return out


def doi_chieu_catalog(res):
    """Neo cứng: số dòng phải khớp TUYỆT ĐỐI với `valid_rows_h*` của B.

    Hai bên tính trên cùng `data/processed/`, nên lệch một dòng là có lỗi chứ không
    phải nhiễu. Đây là phép kiểm mạnh nhất của cổng GĐ2 (gate-gd2.md mục 2.1).
    """
    if not CATALOG.exists():
        print("  (bỏ qua đối chiếu: chưa có data/catalog.parquet)")
        return True
    cat = pd.read_parquet(CATALOG)
    ok_all = True
    for r in res:
        k = cat[(cat["env"] == r["env"]) & cat["kept"]]
        for h in HORIZONS:
            a, b = r[f"dong_h{h}"], int(k[f"valid_rows_h{h}"].sum())
            ok = a == b
            ok_all &= ok
            print(f"  [{'  ok  ' if ok else 'LỆCH!'}] {r['env']} dòng h={h:<2}: A={a:>9,}  B={b:>9,}")
        if len(k) != r["n_series"]:
            ok_all = False
            print(f"  [LỆCH!] {r['env']} số chuỗi: A={r['n_series']}  B={len(k)}")
    return ok_all


def main():
    ap = argparse.ArgumentParser(description="Tham chiếu GĐ2 — protocol mục 8.")
    ap.add_argument("--env", choices=[*ENVS, "all"], default="all")
    ap.add_argument("--out", type=str, default=None, help="Ghi JSON ra đường dẫn này.")
    ap.add_argument(
        "--calendar",
        choices=["auto", "none"],
        default="auto",
        help="auto: sinh đủ 19 đặc trưng. none: bỏ 4 đặc trưng lịch, còn 15 — dùng khi "
             "muốn con số không phụ thuộc QĐ-010.",
    )
    a = ap.parse_args()

    envs = list(ENVS) if a.env == "all" else [a.env]
    res = []
    for e in envs:
        print(f"[{e}] đang chạy...", flush=True)
        r = process(e, a.calendar)
        res.append(r)
        print(f"  {r['n_series']} chuỗi · {r['n_dac_trung']} đặc trưng · "
              f"h=1 {r['dong_h1']:,} · h=6 {r['dong_h6']:,} · h=12 {r['dong_h12']:,}")
        if not r["moc_lich_that"] and a.calendar != "none":
            print(f"  [ CẢNH BÁO ] {e}: b0={r['b0']} -> bucket KHÔNG phải epoch thật. "
                  "Bốn đặc trưng lịch chỉ là giờ kể từ lúc bắt đầu trace, pha chưa "
                  "biết, `dow` không diễn giải được. Chờ QĐ-010.")

    print("\n── Đối chiếu neo cứng với catalog.parquet")
    ok = doi_chieu_catalog(res)
    print("\n" + ("=" * 66))
    print("KHỚP — số dòng đặc trưng bằng đúng dòng hợp lệ của GĐ1."
          if ok else
          "LỆCH — dừng lại truy nguyên trước khi dùng bảng này làm tham chiếu.")
    print("=" * 66)

    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Đã ghi: {p}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Quy ước chưa có trong protocol, chốt tạm ở tệp này — A cần đưa vào mục 8:
#
# 1. `ddof` của rolling std và của CV. pandas `.rolling().std()` mặc định ddof=1,
#    `numpy.std` mặc định ddof=0. Hai bản hiện thực đều "đúng" mà ra số khác nhau.
#    Chốt ddof=1 theo pandas vì B gần như chắc chắn dùng pandas.
#
# 2. Thứ Năm là gốc của `dow`. epoch 1970-01-01 rơi vào thứ Năm nên
#    `((t // 86400) + 4) % 7` cho 0 = thứ Hai. Quy ước nào cũng được, miễn hai bên
#    dùng chung một quy ước; ghi ra để khỏi phải đoán.
#
# 3. Cụm NaN chạm mép cửa sổ không được nội suy (đã đúng ở GĐ1, xem gate-gd1.md
#    mục 5.5). Không ngoại suy ở mép để hai bên khớp.
