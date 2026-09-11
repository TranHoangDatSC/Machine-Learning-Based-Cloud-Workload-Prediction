"""Thước đo độc lập của cổng GĐ4 — ba chế độ chuẩn hoá (protocol mục 14, QĐ-016).

    python scripts/reference_gd4.py

Sinh `results/tables/reference_gd4.json`: neo cho `research-log/gate-gd4.md`.

Độc lập ở chỗ nào
-----------------

Bản này **chỉ đọc `data/processed/`** và **không import gì từ `src/cwp/`**. Nó tự dựng
lại ranh giới chia tập, luật dòng hợp lệ, ba phép biến đổi N0/N1/N2, phép map ngược,
và ba baseline — tất cả trên ma trận `(số chuỗi, 2304)` thay vì `groupby` trên bảng
dài. Nếu bản của B đi đường khác mà ra cùng số thì phép so đó kiểm chéo được cả hai.

> **Đừng đưa tệp này cho phiên đang viết `src/cwp/preprocess/normalize.py` đọc.**
> Ở GĐ3 tính độc lập đã yếu vì cùng một phiên viết cả hai bản, và `E1_830` cho thấy hậu
> quả thật: hai bản cùng sai một kiểu nên khớp nhau ở 378/405 ô mà vẫn cùng sai. Xem
> QĐ-014 điểm 3.

Neo gì được, neo gì không
-------------------------

Neo được là phần **tất định** — thứ không phụ thuộc seed, siêu tham số hay phiên bản
thư viện:

1. **Thống kê chuẩn hoá N1** của từng môi trường: trung vị `mu` và `sd` trên cửa sổ
   train, và số chuỗi có `sd = 0` (những chuỗi N1 không xác định).
2. **Ba bất biến của QĐ-016 điểm 5** — chỗ rẻ nhất để bắt lỗi chuẩn hoá, chạy được
   trước khi có bất kỳ model nào.
3. **Mốc "hằng số mức tải"** cho sáu cặp transfer: lấy mức tải trung bình của môi
   trường nguồn áp thẳng lên môi trường đích. Không model, không đặc trưng, không
   huấn luyện. Đây là con số mục 14 dùng để chứng minh rằng MAE của N0 thô **không nói
   lên điều gì** — một hằng số cũng đạt được.
4. **Số dòng hợp lệ** ở mỗi chế độ. N0 phải khớp tuyệt đối chín neo của GĐ2/GĐ3; N2
   mất thêm đúng một bucket đầu mỗi chuỗi vì sai phân.

Không neo được là kết quả model — cùng lý do đã ghi ở phụ lục `gate-gd3.md`.
"""

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
MODES = ["N0", "N1", "N2"]

W = 8 * 24 * 12                      # 2304 bucket, cửa sổ 8 ngày (mục 7)
N_TRAIN = int(W * 0.70)              # 1612
N_VAL = int(W * 0.15)                # 345
RANH = {"train": (0, N_TRAIN),
        "val": (N_TRAIN, N_TRAIN + N_VAL),
        "test": (N_TRAIN + N_VAL, W)}
MAX_LAG = 24                         # cửa sổ đặc trưng sâu nhất (mục 8)
SEASONAL_LAG = 288

CAP = [("E1", "E2"), ("E2", "E1"), ("E1", "E3"),
       ("E3", "E1"), ("E2", "E3"), ("E3", "E2")]


# ------------------------------------------------------------------ nạp dữ liệu

def nap(env: str) -> tuple[np.ndarray, list[str]]:
    """Ma trận `(số chuỗi, 2304)` của `y`, và danh sách `series_id` theo hàng.

    Cố ý **không** dùng `groupby`: một đường đi khác hẳn bản của B là điều làm phép so
    có giá trị.
    """
    df = pd.read_parquet(ROOT / "data" / "processed" / f"{env}.parquet",
                         columns=["series_id", "bucket", "y"])
    b0 = int(df["bucket"].min())
    ten = sorted(df["series_id"].unique())
    chi_so = {s: i for i, s in enumerate(ten)}

    Y = np.full((len(ten), W), np.nan)
    hang = df["series_id"].map(chi_so).to_numpy()
    cot = df["bucket"].to_numpy() - b0
    giu = (cot >= 0) & (cot < W)
    Y[hang[giu], cot[giu]] = df["y"].to_numpy()[giu]
    return Y, ten


# -------------------------------------------------------------- ba chế độ

def bien_doi(Y: np.ndarray, mode: str) -> tuple[np.ndarray, dict]:
    """Chuỗi đã biến đổi, kèm tham số cần cho phép map ngược — QĐ-016 điểm 1.

    - `N0`: giữ nguyên.
    - `N1`: `(y − mu) / sd`, với `mu`, `sd` tính trên **cửa sổ train của chính chuỗi
      đó**, bucket `[0, 1612)`. Chuỗi có `sd = 0` thì N1 không xác định — đánh dấu và
      để nguyên `NaN`, không thay bằng 0, không thêm epsilon.
    - `N2`: `y_t − y_{t−1}`, nên bucket 0 của mỗi chuỗi thành `NaN`.
    """
    lo, hi = RANH["train"]
    if mode == "N0":
        return Y.copy(), {}
    if mode == "N1":
        tr = Y[:, lo:hi]
        mu = np.nanmean(tr, axis=1)
        sd = np.nanstd(tr, axis=1, ddof=1)
        xau = ~np.isfinite(sd) | (sd == 0)
        an_toan = np.where(xau, 1.0, sd)
        Z = (Y - mu[:, None]) / an_toan[:, None]
        Z[xau, :] = np.nan
        return Z, {"mu": mu, "sd": sd, "khong_xac_dinh": xau}
    if mode == "N2":
        D = np.full_like(Y, np.nan)
        D[:, 1:] = Y[:, 1:] - Y[:, :-1]
        return D, {}
    raise ValueError(f"Chế độ không rõ: {mode!r}")


def map_nguoc(yhat: np.ndarray, Y: np.ndarray, mode: str, tham: dict) -> np.ndarray:
    """Đưa dự đoán về **thang CPU% gốc** trước khi tính chỉ số (mục 14).

    `yhat` cùng hình dạng `(n, 2304)`, chỉ số cột là gốc dự đoán `t`; với N2 thì
    `yhat` là `Δ̂` nên cộng lại `y_t`.
    """
    if mode == "N0":
        return yhat
    if mode == "N1":
        return yhat * tham["sd"][:, None] + tham["mu"][:, None]
    if mode == "N2":
        return Y + yhat
    raise ValueError(f"Chế độ không rõ: {mode!r}")


# ------------------------------------------------------- luật dòng hợp lệ

def mat_na_hop_le(S: np.ndarray, h: int) -> np.ndarray:
    """Dòng tại `t` hợp lệ khi `[t−24, t]` sạch NaN **và** `t+h` không NaN (mục 8).

    Tính trên chuỗi **đã biến đổi** `S`, đúng QĐ-016 điểm 2.
    """
    n, m = S.shape
    sach = np.isfinite(S)
    # Cửa sổ 25 điểm sạch hoàn toàn: đếm dồn rồi so hiệu, không dùng rolling.
    dem = np.cumsum(sach.astype("int64"), axis=1)
    ok = np.zeros((n, m), dtype=bool)
    t = np.arange(MAX_LAG, m)
    tong = dem[:, t] - np.where(t - MAX_LAG - 1 >= 0, dem[:, t - MAX_LAG - 1], 0)
    ok[:, t] = tong == (MAX_LAG + 1)

    co_target = np.zeros((n, m), dtype=bool)
    co_target[:, : m - h] = sach[:, h:]
    return ok & co_target


def mat_na_tap(h: int, tap: str) -> np.ndarray:
    """Cột `t` thuộc `tap` khi cả `t` và `t+h` trong khoảng — QĐ-013 điểm 2."""
    lo, hi = RANH[tap]
    t = np.arange(W)
    return (t >= lo) & (t + h < hi)


# ---------------------------------------------------------------- baseline

def du_doan_baseline(S: np.ndarray, ten: str, mode: str) -> np.ndarray:
    """Ba baseline của mục 11, tính **trong không gian của chế độ đang dùng**.

    `naive` dưới N2 là `Δ̂ = 0` (QĐ-016 điểm 4), nên map ngược ra đúng persistence.
    """
    n, m = S.shape
    out = np.full((n, m), np.nan)
    if ten == "naive":
        out = np.zeros_like(S) if mode == "N2" else S.copy()
    elif ten == "ma6":
        cua_so = np.full((n, m), np.nan)
        cua_so[:, 6:] = np.nanmean(
            np.stack([S[:, 6 - k: m - k] for k in range(1, 7)], axis=0), axis=0)
        out = cua_so
    elif ten == "seasonal":
        out = np.full((n, m), np.nan)
        out[:, SEASONAL_LAG:] = S[:, : m - SEASONAL_LAG]
    else:
        raise ValueError(f"Baseline không rõ: {ten!r}")
    return out


# ------------------------------------------------------------------ chỉ số

def mae_theo_chuoi(y: np.ndarray, yhat: np.ndarray, dung: np.ndarray) -> np.ndarray:
    """MAE riêng từng chuỗi trên các ô `dung` — QĐ-013 điểm 5 gộp sau, không gộp trước."""
    sai = np.where(dung, np.abs(y - yhat), np.nan)
    with np.errstate(invalid="ignore"):
        return np.nanmean(sai, axis=1)


def trung_vi(v: np.ndarray) -> float | None:
    s = v[np.isfinite(v)]
    return None if s.size == 0 else round(float(np.median(s)), 6)


# ------------------------------------------------------------------- chạy

def do_mot_moi_truong(env: str) -> dict:
    Y, ten = nap(env)
    ra = {"env": env, "n_chuoi": len(ten), "n_bucket": W,
          "ranh_gioi": {k: list(v) for k, v in RANH.items()}}

    # 1. Thống kê chuẩn hoá N1
    _, tham = bien_doi(Y, "N1")
    ra["n1"] = {
        "mu_p50": round(float(np.nanmedian(tham["mu"])), 6),
        "sd_p50": round(float(np.nanmedian(tham["sd"])), 6),
        "n_chuoi_sd_bang_0": int(tham["khong_xac_dinh"].sum()),
    }

    # 2. Số dòng hợp lệ mỗi chế độ
    ra["so_dong"] = {}
    for mode in MODES:
        S, _ = bien_doi(Y, mode)
        ra["so_dong"][mode] = {}
        for h in HORIZONS:
            hl = mat_na_hop_le(S, h)
            ra["so_dong"][mode][f"h{h}"] = {
                tap: int((hl & mat_na_tap(h, tap)).sum()) for tap in RANH
            }

    # 3. Ba bất biến của QĐ-016 điểm 5, đo trên tập test
    ra["bat_bien"] = bat_bien(Y)

    # 4. Ba baseline trên test, thang CPU% gốc — phải trùng bảng GĐ3
    S0, _ = bien_doi(Y, "N0")
    hl = {h: mat_na_hop_le(S0, h) for h in HORIZONS}
    ra["baseline_test"] = {}
    for bl in ("naive", "ma6", "seasonal"):
        ra["baseline_test"][bl] = {}
        for h in HORIZONS:
            dung = hl[h] & mat_na_tap(h, "test")
            yhat = du_doan_baseline(S0, bl, "N0")
            tgt = np.full_like(S0, np.nan)
            tgt[:, : W - h] = S0[:, h:]
            d = dung & np.isfinite(yhat) & np.isfinite(tgt)
            ra["baseline_test"][bl][f"h{h}"] = {
                "mae_p50": trung_vi(mae_theo_chuoi(tgt, yhat, d)),
                "n_dong_dung": int(d.sum()),
                "n_dong_test": int(dung.sum()),
            }
    return ra


def bat_bien(Y: np.ndarray) -> dict:
    """Ba đẳng thức của QĐ-016 điểm 5, đo trên tập test ở `h = 1`.

    Chúng phải trùng tới ít nhất 9 chữ số thập phân. Đây là phép kiểm **không cần
    tham chiếu** — nó đúng vì toán học, không vì hai bản khớp nhau.
    """
    h = 1
    S0, _ = bien_doi(Y, "N0")
    hl = mat_na_hop_le(S0, h)
    tgt = np.full_like(S0, np.nan)
    tgt[:, : W - h] = S0[:, h:]

    Z, tham1 = bien_doi(Y, "N1")
    D, _ = bien_doi(Y, "N2")
    hl_z = mat_na_hop_le(Z, h)
    hl_d = mat_na_hop_le(D, h)
    chung = hl & hl_z & hl_d & mat_na_tap(h, "test")

    ket = {}
    for ten in ("naive", "ma6"):
        goc = du_doan_baseline(S0, ten, "N0")
        qua_z = map_nguoc(du_doan_baseline(Z, ten, "N1"), Y, "N1", tham1)
        d = chung & np.isfinite(goc) & np.isfinite(qua_z)
        ket[f"{ten}_N0_vs_N1"] = float(np.nanmax(np.abs(goc - qua_z)[d]))

    goc = du_doan_baseline(S0, "naive", "N0")
    qua_d = map_nguoc(du_doan_baseline(D, "naive", "N2"), Y, "N2", {})
    d = chung & np.isfinite(goc) & np.isfinite(qua_d)
    ket["naive_N0_vs_N2"] = float(np.nanmax(np.abs(goc - qua_d)[d]))
    ket["so_o_da_so"] = int(chung.sum())
    return ket


def moc_hang_so(do: dict[str, dict], Ys: dict[str, np.ndarray]) -> list[dict]:
    """Mốc "hằng số mức tải" cho sáu cặp — mục 14, con số 26,90 của E1→E3.

    Lấy **mức tải trung bình trên cửa sổ train của môi trường NGUỒN** làm dự đoán
    hằng, áp lên tập test của môi trường ĐÍCH. Không model, không đặc trưng, không
    huấn luyện. Nếu N0 thô cho MAE quanh con số này thì nó **không nói lên điều gì**.
    """
    lo, hi = RANH["train"]
    h = 1
    ra = []
    for nguon, dich in CAP:
        Yd = Ys[dich]
        hop_le = mat_na_hop_le(Yd, h)
        tgt = np.full_like(Yd, np.nan)
        tgt[:, : W - h] = Yd[:, h:]

        dong = {"nguon": nguon, "dich": dich}
        # Hai CƠ SỞ khác nhau, và mục 14 dùng cơ sở thứ hai. Báo cả hai để không ai
        # phải đoán vì sao hai con số không khớp — xem ghi chú ở mục 14.
        for ten_cs, c, m in [
            ("gd4", float(np.nanmean(Ys[nguon][:, lo:hi])),
             hop_le & mat_na_tap(h, "test")),
            ("muc14_cu", float(np.nanmean(Ys[nguon])), hop_le),
        ]:
            d = m & np.isfinite(tgt)
            mae_hang = trung_vi(mae_theo_chuoi(tgt, np.full_like(Yd, c), d))
            mae_naive = trung_vi(mae_theo_chuoi(tgt, Yd, d & np.isfinite(Yd)))
            dong[ten_cs] = {
                "hang_so": round(c, 6),
                "mae_p50_hang_so": mae_hang,
                "mae_p50_naive_tai_dich": mae_naive,
                "lan_te_hon_naive": None if not (mae_hang and mae_naive)
                else round(mae_hang / mae_naive, 3),
            }
        ra.append(dong)
    return ra


def main() -> int:
    print()
    print("THƯỚC ĐO GĐ4 — protocol mục 14, QĐ-016. Chỉ đọc data/processed/.")
    print(f"ranh giới bucket: train {RANH['train']}  val {RANH['val']}  "
          f"test {RANH['test']}")
    print()

    do, Ys = {}, {}
    for env in ENVS:
        Y, _ = nap(env)
        Ys[env] = Y
        do[env] = do_mot_moi_truong(env)
        r = do[env]
        print(f"{env}: {r['n_chuoi']} chuỗi | N1 mu_p50 {r['n1']['mu_p50']:.4f}  "
              f"sd_p50 {r['n1']['sd_p50']:.4f}  "
              f"sd=0 ở {r['n1']['n_chuoi_sd_bang_0']} chuỗi")
        b = r["bat_bien"]
        print(f"   bất biến (lệch tối đa, phải ~0): naive N0/N1 "
              f"{b['naive_N0_vs_N1']:.2e}  ma6 N0/N1 {b['ma6_N0_vs_N1']:.2e}  "
              f"naive N0/N2 {b['naive_N0_vs_N2']:.2e}")
        for h in HORIZONS:
            sd = r["so_dong"]
            print(f"   h={h:<2} số dòng test — N0 {sd['N0'][f'h{h}']['test']:>7,}  "
                  f"N1 {sd['N1'][f'h{h}']['test']:>7,}  "
                  f"N2 {sd['N2'][f'h{h}']['test']:>7,}")

    moc = moc_hang_so(do, Ys)
    print()
    print("MỐC HẰNG SỐ MỨC TẢI — mục 14, h=1, MAE trung vị trên test của môi trường đích")
    print("cơ sở GĐ4: hằng số lấy trên cửa sổ TRAIN của nguồn, chấm trên TEST của đích")
    print(f"{'cặp':<12}{'hằng số':>10}{'MAE hằng':>11}{'MAE naive':>11}{'tệ hơn':>9}")
    for m in moc:
        g = m["gd4"]
        print(f"{m['nguon']+'→'+m['dich']:<12}{g['hang_so']:>10.2f}"
              f"{g['mae_p50_hang_so']:>11.4f}{g['mae_p50_naive_tai_dich']:>11.4f}"
              f"{g['lan_te_hon_naive']:>8.2f}×")
    e13 = next(m for m in moc if (m["nguon"], m["dich"]) == ("E1", "E3"))
    print()
    print("Đối chiếu với con số ở protocol mục 14 — HAI CƠ SỞ KHÁC NHAU:")
    print(f"   cơ sở mục 14 (hằng số trên TOÀN cửa sổ, chấm trên MỌI dòng hợp lệ): "
          f"E1→E3 = {e13['muc14_cu']['mae_p50_hang_so']:.4f}, "
          f"naive {e13['muc14_cu']['mae_p50_naive_tai_dich']:.4f}")
    print(f"   cơ sở GĐ4 (QĐ-016, train → test)                                : "
          f"E1→E3 = {e13['gd4']['mae_p50_hang_so']:.4f}, "
          f"naive {e13['gd4']['mae_p50_naive_tai_dich']:.4f}")
    print("   Lập luận không đổi, và mạnh hơn một chút ở cơ sở GĐ4.")

    dich = ROOT / "results" / "tables" / "reference_gd4.json"
    dich.write_text(json.dumps({"moi_truong": list(do.values()), "moc_hang_so": moc},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"Ghi {dich.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
