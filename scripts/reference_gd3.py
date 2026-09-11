"""Thước đo độc lập cho cổng GĐ3 — bản hiện thực của A.

    python scripts/reference_gd3.py --env all --out results/tables/reference_gd3.json

Sinh neo cứng cho GĐ3: ranh giới chia tập, ba baseline, mẫu số MASE, và tầng
burstiness. Bản hiện thực của B phải ra **cùng con số** ở mọi mục dưới đây.

> **ĐỪNG ĐƯA TỆP NÀY CHO AGENT ĐANG VIẾT `src/cwp/models/` HAY
> `src/cwp/evaluation/` ĐỌC.** Nếu cùng một người viết cả hai bản thì việc chúng
> khớp nhau không chứng minh gì. Đó là cơ chế đã bắt được mọi lỗi từ GĐ1 tới nay.

## Vì sao baseline làm được neo còn model thì không

Ba baseline ở protocol mục 11 **không có yếu tố ngẫu nhiên nào**: không seed, không
siêu tham số, không huấn luyện. Cho cùng dữ liệu và cùng quy ước thì chúng phải ra
cùng con số tới chữ số cuối. Lệch một chữ số là có lỗi ở một trong hai bên, không
phải nhiễu.

Model ML thì không có tính chất đó — kết quả phụ thuộc siêu tham số, seed, phiên bản
thư viện. Nên cổng GĐ3 **neo vào baseline và vào bộ máy đánh giá**, rồi tin rằng
model chạy trên cùng bộ máy đó là đúng. Neo được cái đo, không neo được cái học.

## Độc lập thế nào

Bản này **chỉ đọc `data/processed/`**, không đụng tới `data/features/`. Nó tự dựng
lại luật dòng hợp lệ, tự tính `y_t`, `roll_mean_6`, `y_{t-288}` từ `y` thô.

Nghĩa là nếu B tính baseline **từ `data/features/`** mà ra cùng số, thì phép so đó
kiểm chéo được **cả ma trận đặc trưng lẫn code baseline** cùng lúc — mạnh hơn là hai
bên cùng đọc một tệp trung gian.

Lối nghĩ cũng cố ý khác: nạp mỗi môi trường thành **một ma trận `(số chuỗi, 2304)`**
rồi thao tác theo cột, thay vì `groupby(series_id)` trên bảng dài.

## Năm quy ước — QĐ-013

1. Ranh giới chia theo **bucket**: train `[0, 1612)`, val `[1612, 1957)`,
   test `[1957, 2304)`.
2. Một dòng thuộc tập `S` khi **cả `t` và `t+h`** nằm trong `S`. Dòng vắt qua ranh
   giới bị loại.
3. Mẫu số MASE = trung bình `|y_t − y_{t−1}|` trên **train** của chính chuỗi đó, chỉ
   lấy cặp mà cả hai đầu không NaN. Không phụ thuộc horizon. `d = 0` thì loại chuỗi.
4. `SMAPE = 100 × mean(|y−ŷ| / ((|y|+|ŷ|)/2))`, số hạng `0/0` tính là **0**.
   `R² = 1 − SS_res/SS_tot`; `SS_tot = 0` thì loại chuỗi.
5. Gộp bằng **trung vị của chỉ số theo từng chuỗi**, kèm IQR. Không gộp mọi dòng vào
   một dãy rồi tính một chỉ số.
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
ENVS = ["E1", "E2", "E3"]
HORIZONS = [1, 6, 12]

W = 2304          # bucket trong cửa sổ 8 ngày (protocol mục 7)
MAX_LAG = 24      # cửa sổ đặc trưng sâu nhất (mục 8)
LAG_MUA = 288     # seasonal naive: cùng giờ hôm trước (mục 11)
MA_W = 6          # moving average, cửa sổ 6 (mục 11)

N_TRAIN = int(0.70 * W)              # 1612
N_VAL = int(0.15 * W)                # 345
RANH = {"train": (0, N_TRAIN),
        "val": (N_TRAIN, N_TRAIN + N_VAL),
        "test": (N_TRAIN + N_VAL, W)}


def nap_ma_tran(env: str, proc_dir: Path, cat: pd.DataFrame) -> np.ndarray:
    """`data/processed/{env}.parquet` → ma trận `(số chuỗi, 2304)`.

    Ranh giới chuỗi thành ranh giới hàng, nên không phép dịch nào ở đây có thể bắc
    cầu từ chuỗi này sang chuỗi kia.
    """
    f = proc_dir / f"{env}.parquet"
    if not f.exists():
        raise SystemExit(f"Thiếu {f}. Chạy: python -m cwp.preprocess.build --env all")

    d = pd.read_parquet(f, columns=["series_id", "bucket", "y"])
    giu = set(cat[(cat["env"] == env) & cat["kept"]]["series_id"])
    if set(d["series_id"].unique()) != giu:
        raise SystemExit(f"{env}: data/processed/ không khớp catalog.kept.")

    d = d.sort_values(["series_id", "bucket"], kind="stable")
    n = d["series_id"].nunique()
    T, du = divmod(len(d), n)
    if du or T != W:
        raise SystemExit(f"{env}: mỗi chuỗi phải đúng {W} bucket, đang là {T}.")
    return d["y"].to_numpy().reshape(n, W)


def mat_na_hop_le(Y: np.ndarray, h: int) -> np.ndarray:
    """Luật dòng hợp lệ của protocol mục 8, dựng lại độc lập.

    Dòng tại `t` hợp lệ khi mọi điểm trong `[t-24, t]` không NaN **và** `y[t+h]`
    không NaN. Không dùng `dropna` trên đặc trưng — hai thứ đó không tương đương
    (QĐ-010).
    """
    n, T = Y.shape
    co = np.isfinite(Y)
    # cumsum để hỏi "cả 25 điểm trong cửa sổ đều có" trong O(1) mỗi vị trí
    cs = np.concatenate([np.zeros((n, 1), dtype=np.int64), np.cumsum(co, axis=1)],
                        axis=1)
    m = np.zeros((n, T), dtype=bool)
    t = np.arange(MAX_LAG, T - h)
    du_cua_so = (cs[:, t + 1] - cs[:, t - MAX_LAG]) == (MAX_LAG + 1)
    m[:, t] = du_cua_so & co[:, t + h]
    return m


def du_doan_baseline(Y: np.ndarray, h: int) -> dict[str, np.ndarray]:
    """Ba baseline của mục 11, tính thẳng từ `y` thô.

    `roll_mean_6` tại `t` lấy trên `y[t-6 .. t-1]` — **không gồm điểm hiện tại**,
    đúng quy ước cửa sổ của mục 8.
    """
    n, T = Y.shape
    nan = np.full((n, T), np.nan)

    naive = nan.copy()
    naive[:, :] = Y                                   # ŷ = y_t

    ma = nan.copy()
    for t in range(MA_W, T):
        ma[:, t] = Y[:, t - MA_W:t].mean(axis=1)      # cửa sổ [t-6, t-1]

    mua = nan.copy()
    mua[:, LAG_MUA:] = Y[:, :T - LAG_MUA]             # ŷ = y_{t-288}

    return {"naive": naive, "ma6": ma, "seasonal": mua}


def mau_so_mase(Y: np.ndarray) -> np.ndarray:
    """Trung bình `|y_t − y_{t−1}|` trên phần train, mỗi chuỗi một số (QĐ-013 điểm 3)."""
    tr = Y[:, RANH["train"][0]:RANH["train"][1]]
    d = np.abs(np.diff(tr, axis=1))
    hop_le = np.isfinite(d)
    dem = hop_le.sum(axis=1)
    tong = np.where(hop_le, d, 0.0).sum(axis=1)
    return np.where(dem > 0, tong / np.maximum(dem, 1), np.nan)


def chi_so_theo_chuoi(y: np.ndarray, yhat: np.ndarray, m: np.ndarray,
                      d_mase: np.ndarray) -> dict[str, np.ndarray]:
    """Năm chỉ số của mục 12, tính RIÊNG cho từng chuỗi (QĐ-013 điểm 5)."""
    n = y.shape[0]
    ra = {k: np.full(n, np.nan) for k in ("mae", "rmse", "smape", "mase", "r2")}

    for i in range(n):
        s = m[i]
        if not s.any():
            continue
        a, b = y[i, s], yhat[i, s]
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() == 0:
            continue
        a, b = a[ok], b[ok]
        e = np.abs(a - b)

        ra["mae"][i] = e.mean()
        ra["rmse"][i] = np.sqrt(((a - b) ** 2).mean())

        mau = (np.abs(a) + np.abs(b)) / 2.0
        ra["smape"][i] = 100.0 * np.where(mau > 0, e / np.where(mau > 0, mau, 1), 0.0).mean()

        if np.isfinite(d_mase[i]) and d_mase[i] > 0:
            ra["mase"][i] = ra["mae"][i] / d_mase[i]

        # Chuỗi hằng nhận biết bằng `min == max`, KHÔNG bằng `sstot > 0`.
        # `sum((a − ā)²)` của 346 bản sao một số không biểu diễn được chính xác cho
        # ra 1,7e−29 chứ không phải 0, vì ā = sum/n không rơi đúng vào chính số đó.
        # (Con số 6,8e−29 ở bản chú thích đầu là của n = 347 — phép chẩn đoán lúc đó
        # cắt cửa sổ test mà quên purge. Hai giá trị khác nhau cho cùng một số 0 toán
        # học chính là lý do không được so với 0 bằng ngưỡng.)
        # Bản cũ vì thế chấm R² = 1,0 cho chuỗi hằng E1_830 — một điểm tuyệt đối cho
        # thứ mà naive đoán trúng tầm thường. B bắt được lỗi này khi đối chiếu; xem
        # research-log/2026-09-10-gd3-thi-nghiem-a.md và gate-gd3.md mục 5.
        if a.min() != a.max():
            sstot = ((a - a.mean()) ** 2).sum()
            ra["r2"][i] = 1.0 - ((a - b) ** 2).sum() / sstot

    return ra


def gop(v: np.ndarray) -> dict:
    """Trung vị kèm IQR trên tập chuỗi, và số chuỗi bị loại vì không xác định."""
    s = v[np.isfinite(v)]
    if len(s) == 0:
        return {"p50": None, "p25": None, "p75": None, "iqr": None,
                "n_chuoi": 0, "n_loai": int(len(v))}
    q = np.percentile(s, [25, 50, 75])
    return {"p50": round(float(q[1]), 6), "p25": round(float(q[0]), 6),
            "p75": round(float(q[2]), 6), "iqr": round(float(q[2] - q[0]), 6),
            "n_chuoi": int(len(s)), "n_loai": int(len(v) - len(s))}


def mot_moi_truong(env: str, proc_dir: Path, cat: pd.DataFrame,
                   cv: pd.DataFrame) -> dict:
    Y = nap_ma_tran(env, proc_dir, cat)
    n = Y.shape[0]
    d_mase = mau_so_mase(Y)

    ra = {
        "env": env,
        "n_chuoi": n,
        "n_bucket": W,
        "ranh_gioi": {k: list(v) for k, v in RANH.items()},
        "mase_mau_so_p50": round(float(np.nanmedian(d_mase)), 6),
        "mase_chuoi_bi_loai": int((~np.isfinite(d_mase) | (d_mase <= 0)).sum()),
        "so_dong": {}, "baseline": {},
    }

    for h in HORIZONS:
        hop_le = mat_na_hop_le(Y, h)
        du = du_doan_baseline(Y, h)
        t_all = np.arange(W)

        ra["so_dong"][f"h{h}"] = {"tong_hop_le": int(hop_le.sum())}
        for tap, (lo, hi) in RANH.items():
            # QĐ-013 điểm 2: cả t VÀ t+h phải trong cùng tập
            trong = (t_all >= lo) & (t_all < hi) & (t_all + h >= lo) & (t_all + h < hi)
            m = hop_le & trong[None, :]
            ra["so_dong"][f"h{h}"][tap] = int(m.sum())
            if tap != "test":
                continue

            y_that = np.full_like(Y, np.nan)
            y_that[:, : W - h] = Y[:, h:]          # target = y_{t+h}
            for ten, yhat in du.items():
                cs = chi_so_theo_chuoi(y_that, yhat, m, d_mase)
                # protocol mục 11: seasonal naive không xác định ở những dòng thiếu
                # y_{t-288}. Ghi ra SỐ DÒNG THỰC SỰ DÙNG chứ không lặng lẽ bỏ —
                # ba baseline phải được so trên nền biết rõ mỗi cái dùng bao nhiêu.
                dung = int((m & np.isfinite(yhat) & np.isfinite(y_that)).sum())
                co = int(m.sum())
                ra["baseline"].setdefault(ten, {})[f"h{h}"] = {
                    **{k: gop(v) for k, v in cs.items()},
                    "n_dong_dung": dung,
                    "n_dong_test": co,
                    "pct_bo": round(100.0 * (co - dung) / co, 4) if co else None,
                }

    # Tầng burstiness theo QĐ-012: tam phân vị CV TRONG từng môi trường
    c = cv[cv["env"] == env]["cv"].to_numpy()
    ng = np.percentile(c, [100 / 3, 200 / 3])
    ra["tang_burstiness"] = {
        "nguong": [round(float(ng[0]), 6), round(float(ng[1]), 6)],
        "so_chuoi": [int((c < ng[0]).sum()),
                     int(((c >= ng[0]) & (c < ng[1])).sum()),
                     int((c >= ng[1]).sum())],
    }
    return ra


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--cv", default="results/tables/cv_gd2.csv")
    ap.add_argument("--out", default="results/tables/reference_gd3.json")
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    cat = pd.read_parquet(ROOT / a.catalog)
    cv_path = ROOT / a.cv
    if not cv_path.exists():
        raise SystemExit(f"Thiếu {cv_path}. Chạy: python scripts/fig_burstiness.py --env all")
    cv = pd.read_csv(cv_path)

    print()
    print("THƯỚC ĐO ĐỘC LẬP GĐ3 — chỉ đọc data/processed/, không đụng data/features/")
    print(f"ranh giới bucket: train {RANH['train']}  val {RANH['val']}  test {RANH['test']}")
    print()

    ket = [mot_moi_truong(e, ROOT / a.processed, cat, cv) for e in envs]

    for r in ket:
        print(f"{r['env']}: {r['n_chuoi']} chuỗi | mẫu số MASE trung vị "
              f"{r['mase_mau_so_p50']:.4f} | {r['mase_chuoi_bi_loai']} chuỗi bị loại")
        for h in HORIZONS:
            s = r["so_dong"][f"h{h}"]
            print(f"   h={h:<2} dòng: train {s['train']:>8,}  val {s['val']:>7,}  "
                  f"test {s['test']:>7,}  (tổng hợp lệ {s['tong_hop_le']:>9,})")
        for ten in ("naive", "ma6", "seasonal"):
            v = [f"h{h}={r['baseline'][ten][f'h{h}']['mae']['p50']:.4f}" for h in HORIZONS]
            print(f"   MAE trung vị trên test — {ten:<9} " + "  ".join(v))
        t = r["tang_burstiness"]
        print(f"   tầng CV: ngưỡng {t['nguong']}, số chuỗi {t['so_chuoi']}")
        print()

    dich = ROOT / a.out
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_text(json.dumps(ket, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi: {dich.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
