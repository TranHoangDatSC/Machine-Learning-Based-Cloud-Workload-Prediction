"""Kiểm độc lập cách dựng ma trận đặc trưng đã chuẩn hoá (QĐ-016, QĐ-019).

Viết lại TỪ ĐẶC TẢ, không đọc code dựng dữ liệu hay code kiểm cũ. Nguồn đặc tả duy nhất:
docs/protocol.md mục 5–9, 14 và docs/decisions.md QĐ-010, QĐ-013, QĐ-016, QĐ-019.

Bốn tính chất:

P1  N1 = z-score theo từng chuỗi, `mu`/`sd` tính trên cửa sổ train `[0, 1612)` (offset so với
    bucket nhỏ nhất của môi trường), ddof = 1, bỏ NaN.
    (a) bảng results/tables/normalize_gd4.csv khớp thống kê tính lại từ data/processed/;
    (b) ma trận N1 thật sự dựng bằng `mu`/`sd` đã khai: sinh lại 15 đặc trưng giá trị từ
        z = (y − mu)/sd rồi so từng ô, và giải ngược (mu, sd) từ `lag_1` cho từng chuỗi.
P2  Sai phân N2 không bắc cầu qua ranh giới hai chuỗi: không dòng nào chạm z[0] (offset ≤ 24),
    không dòng nào có t + h vượt cuối chuỗi, và 15 đặc trưng khớp sai phân tính TRONG chuỗi.
P3  Bốn đặc trưng lịch giống hệt nhau (so bit) giữa N0, N1, N2 tại cùng (series_id, bucket).
P4  target: N0 = y(t+h); N1 = z(t+h); N2 = y(t+h) − y(t). Kiểm cả data/features (mọi chế độ,
    mọi h) và data/features_qd019 (N2).

Mỗi tính chất P1–P4 có phép tự kiểm đột biến: làm hỏng có chủ ý một bản sao trong bộ nhớ và
đòi phép kiểm phải bắt được. Phép kiểm không thể trượt thì vô giá trị.

Script CHỈ ĐỌC. Không ghi gì vào data/ hay results/.

Chạy:  python scripts/kiem_doc_lap_qd016.py
"""

from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

warnings.filterwarnings("ignore", category=RuntimeWarning)

GOC = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]
HS = [1, 6, 12]
N_CUA_SO = 2304          # mục 7: cửa sổ 8 ngày, 2304 bucket 5 phút
N_TRAIN = 1612           # QĐ-013 điểm 1: train = offset [0, 1612)
LAGS = [1, 2, 3, 6, 12, 24]
COT_LAG = [f"lag_{k}" for k in LAGS]
COT_ROLL = [f"roll_{s}_{w}" for w in (6, 12) for s in ("mean", "std", "min", "max")]
COT_GIA_TRI = COT_LAG + COT_ROLL + ["diff_1"]      # 15 đặc trưng dẫn xuất từ chuỗi
COT_LICH = ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]

# Ngưỡng, áp trên lệch tương đối có sàn |a − b| / max(1, |b|) (xem do_lech).
# Lag, diff, min/max, target là phép chép/trừ một bước nên phải gần như bằng bit.
# roll_mean và roll_std đi qua tổng tích luỹ của bản dựng (có thể là cửa sổ trượt cộng/trừ),
# sai số làm tròn của phương sai nằm dưới căn nên có thể tới ~1e-8 × thang — nới cho roll_std.
TOL_CHAT = 1e-9
TOL_ROLL_STD = 1e-6
TOL_GIAI_NGUOC = 1e-6    # sai lệch tương đối khi giải ngược (mu, sd) từ lag_1


# ─────────────────────────────── tiện ích ───────────────────────────────

def nap_chuoi(env: str):
    """Đọc data/processed/{env}.parquet thành lưới Y (số chuỗi × 2304), NaN là lỗ hổng."""
    p = pd.read_parquet(GOC / "data" / "processed" / f"{env}.parquet",
                        columns=["series_id", "bucket", "y"])
    b0 = int(p["bucket"].min())
    ids = pd.unique(p["series_id"])
    s = pd.Categorical(p["series_id"], categories=ids).codes.astype(np.int64)
    off = p["bucket"].to_numpy(np.int64) - b0
    if off.min() < 0 or off.max() >= N_CUA_SO:
        raise SystemExit(f"{env}: bucket nằm ngoài cửa sổ [b0, b0+2304)")
    dem = np.bincount(s * N_CUA_SO + off, minlength=len(ids) * N_CUA_SO)
    if not (dem == 1).all():
        raise SystemExit(f"{env}: không phải mỗi chuỗi đủ đúng 2304 bucket liên tiếp từ b0")
    Y = np.full((len(ids), N_CUA_SO), np.nan)
    Y[s, off] = p["y"].to_numpy(np.float64)
    return list(ids), b0, Y


def doc_ma_tran(duong: Path, cot=None) -> pd.DataFrame:
    return pd.read_parquet(duong, columns=cot)


def vi_tri(df: pd.DataFrame, ids, b0):
    """(chỉ số chuỗi, offset) cho từng dòng ma trận; -1 nếu series_id lạ."""
    s = pd.Categorical(df["series_id"], categories=ids).codes.astype(np.int64)
    off = df["bucket"].to_numpy(np.int64) - b0
    hop_le = (s >= 0) & (off >= 0) & (off < N_CUA_SO)
    return s, off, hop_le


def lay(luoi: np.ndarray, s, off, hop_le):
    """Lấy luoi[s, off]; vị trí không hợp lệ trả NaN."""
    out = np.full(len(s), np.nan)
    out[hop_le] = luoi[s[hop_le], off[hop_le]]
    return out


def do_lech(thuc: np.ndarray, ky_vong: np.ndarray) -> np.ndarray:
    """Lệch "tương đối có sàn" |a − b| / max(1, |b|) cho từng ô.

    Dùng sàn 1 thay vì ngưỡng tuyệt đối: N1 có chuỗi `sd` rất nhỏ (E3_m_618, E3_m_94) nên z lên
    tới ~2·10⁴, và sai số làm tròn ở chữ số cuối khi đó đã là ~4·10⁻¹⁰ tuyệt đối.
    NaN ở cả hai coi là bằng (0); NaN một bên là lệch vô cùng."""
    thuc = np.asarray(thuc, dtype=np.float64)
    ky_vong = np.asarray(ky_vong, dtype=np.float64)
    nan_a, nan_b = np.isnan(thuc), np.isnan(ky_vong)
    lech = np.abs(thuc - ky_vong) / np.maximum(1.0, np.abs(ky_vong))
    lech[nan_a & nan_b] = 0.0
    lech[nan_a ^ nan_b] = np.inf
    return lech


def so_o(thuc: np.ndarray, ky_vong: np.ndarray):
    """So từng ô. Trả (số ô khác bit, lệch tuyệt đối lớn nhất, lệch tương-đối-có-sàn lớn nhất)."""
    thuc = np.asarray(thuc, dtype=np.float64)
    ky_vong = np.asarray(ky_vong, dtype=np.float64)
    nan_a, nan_b = np.isnan(thuc), np.isnan(ky_vong)
    ca_hai = nan_a & nan_b
    khac_bit = int((~(thuc == ky_vong) & ~ca_hai).sum())
    lech_tuyet_doi = np.abs(thuc - ky_vong)
    lech_tuyet_doi[ca_hai] = 0.0
    lech_tuyet_doi[nan_a ^ nan_b] = np.inf
    lech = do_lech(thuc, ky_vong)
    if not lech.size:
        return khac_bit, 0.0, 0.0
    return khac_bit, float(lech_tuyet_doi.max()), float(lech.max())


def luoi_dac_trung(Z: np.ndarray) -> dict:
    """Sinh 15 đặc trưng giá trị trên lưới (chuỗi × thời điểm) theo mục 8, từng chuỗi riêng.

    lag_k(t) = Z[t−k]; roll_*_w(t) trên đúng Z[t−w .. t−1], dính NaN thì NaN, std ddof=1;
    diff_1(t) = Z[t] − Z[t−1]. Vì là lưới 2 chiều theo chuỗi nên không thể chảy qua chuỗi khác.
    """
    S, T = Z.shape
    g = {}
    for k in LAGS:
        a = np.full((S, T), np.nan)
        a[:, k:] = Z[:, :-k]
        g[f"lag_{k}"] = a
    for w in (6, 12):
        cua_so = sliding_window_view(Z, w, axis=1)[:, : T - w, :]  # cửa sổ i = Z[i..i+w−1] → t = i+w
        for ten, ham in (("mean", lambda x: x.mean(axis=2)),
                         ("std", lambda x: x.std(axis=2, ddof=1)),
                         ("min", lambda x: x.min(axis=2)),
                         ("max", lambda x: x.max(axis=2))):
            a = np.full((S, T), np.nan)
            a[:, w:] = ham(cua_so)
            g[f"roll_{ten}_{w}"] = a
    d = np.full((S, T), np.nan)
    d[:, 1:] = Z[:, 1:] - Z[:, :-1]
    g["diff_1"] = d
    return g


def sai_phan_trong_chuoi(Y: np.ndarray) -> np.ndarray:
    Z = np.full_like(Y, np.nan)
    Z[:, 1:] = Y[:, 1:] - Y[:, :-1]      # z[0] không xác định: NaN
    return Z


def so_dac_trung(df, s, off, hop_le, g) -> dict:
    """So 15 cột giá trị với lưới g. Trả chỉ số theo nhóm và cờ đạt."""
    kq = {"khac_bit": 0, "lech_chat": 0.0, "lech_roll_std": 0.0, "lech_roll_mean": 0.0}
    dat = True
    for c in COT_GIA_TRI:
        kb, _, lm = so_o(df[c].to_numpy(), lay(g[c], s, off, hop_le))   # lm: lệch tương đối có sàn
        kq["khac_bit"] += kb
        if c.startswith("roll_std"):
            kq["lech_roll_std"] = max(kq["lech_roll_std"], lm)
            dat &= lm <= TOL_ROLL_STD
        elif c.startswith("roll_mean"):
            kq["lech_roll_mean"] = max(kq["lech_roll_mean"], lm)
            dat &= lm <= TOL_CHAT
        else:
            kq["lech_chat"] = max(kq["lech_chat"], lm)
            dat &= lm <= TOL_CHAT
    kq["dat"] = bool(dat)
    return kq


def luoi_lich(b0: int, n_chuoi: int) -> dict:
    """Công thức lịch QĐ-010 (chỉ dùng làm thông tin bổ sung, không thuộc P3)."""
    t = (np.arange(N_CUA_SO, dtype=np.int64) + b0) * 300
    gio = (t // 3600) % 24
    thu = ((t // 86400) + 4) % 7
    v = {"hour_sin": np.sin(2 * np.pi * gio / 24), "hour_cos": np.cos(2 * np.pi * gio / 24),
         "dow_sin": np.sin(2 * np.pi * thu / 7), "dow_cos": np.cos(2 * np.pi * thu / 7)}
    return {k: np.broadcast_to(a, (n_chuoi, N_CUA_SO)) for k, a in v.items()}


# ─────────────────────────────── P1 ───────────────────────────────

def thong_ke_train(Y):
    x = Y[:, :N_TRAIN]
    return np.nanmean(x, axis=1), np.nanstd(x, axis=1, ddof=1), np.isfinite(x).sum(axis=1)


def kiem_p1_bang(ids, mu_bang, sd_bang, mu_ref, sd_ref):
    """So `mu`, `sd` khai trong bảng với thống kê train tính lại."""
    thieu = int(np.isnan(mu_bang).sum() + np.isnan(sd_bang).sum())
    lech_mu = np.abs(mu_bang - mu_ref)
    lech_sd = np.abs(sd_bang - sd_ref) / np.abs(sd_ref)
    lech_mu_tuong_doi = lech_mu / np.maximum(1.0, np.abs(mu_ref))
    so_sai = int(((lech_mu_tuong_doi > TOL_CHAT) | (lech_sd > TOL_CHAT) | np.isnan(lech_mu)
                  | np.isnan(lech_sd)).sum())
    return {"n_chuoi": len(ids), "thieu": thieu, "chuoi_sai": so_sai,
            "lech_mu_max": float(np.nanmax(lech_mu)), "lech_sd_tdoi_max": float(np.nanmax(lech_sd)),
            "dat": thieu == 0 and so_sai == 0}


def giai_nguoc_mu_sd(df, s, off, hop_le, Y, n_chuoi):
    """Hồi quy y[t−1] = mu + sd·lag_1 theo từng chuỗi → (mu_hat, sd_hat)."""
    x = lay(Y, s, off - 1, hop_le & (off >= 1))
    z = df["lag_1"].to_numpy(np.float64)
    m = np.isfinite(x) & np.isfinite(z) & hop_le
    ss = s[m]
    x, z = x[m], z[m]
    n = np.bincount(ss, minlength=n_chuoi).astype(float)
    mx = np.bincount(ss, x, n_chuoi) / n
    mz = np.bincount(ss, z, n_chuoi) / n
    cov = np.bincount(ss, (x - mx[ss]) * (z - mz[ss]), n_chuoi)
    var = np.bincount(ss, (z - mz[ss]) ** 2, n_chuoi)
    sd_hat = cov / var
    mu_hat = mx - sd_hat * mz
    return mu_hat, sd_hat


def kiem_p1_ma_tran(df, ids, b0, Y, mu_bang, sd_bang, g_n1, mu_toan, sd_toan):
    s, off, hop_le = vi_tri(df, ids, b0)
    kq = so_dac_trung(df, s, off, hop_le, g_n1)
    mu_hat, sd_hat = giai_nguoc_mu_sd(df, s, off, hop_le, Y, len(ids))
    khop_bang = (np.abs(mu_hat - mu_bang) <= TOL_GIAI_NGUOC * sd_bang) & \
                (np.abs(sd_hat - sd_bang) <= TOL_GIAI_NGUOC * sd_bang)
    khop_toan = (np.abs(mu_hat - mu_toan) <= TOL_GIAI_NGUOC * sd_toan) & \
                (np.abs(sd_hat - sd_toan) <= TOL_GIAI_NGUOC * sd_toan)
    kq["dong_la"] = int((~hop_le).sum())
    kq["chuoi_khop_bang"] = int(khop_bang.sum())
    kq["chuoi_khop_tk_toan_chuoi"] = int(khop_toan.sum())
    kq["lech_mu_giai_nguoc"] = float(np.nanmax(np.abs(mu_hat - mu_bang) / sd_bang))
    kq["dat"] = kq["dat"] and kq["dong_la"] == 0 and kq["chuoi_khop_bang"] == len(ids)
    return kq


def dot_bien_chuan_hoa_lai(df, ids, mu_cu, sd_cu, mu_moi, sd_moi):
    """Bản sao ma trận N1 như thể dựng bằng (mu_moi, sd_moi) thay cho (mu_cu, sd_cu)."""
    d = df.copy()
    s = pd.Categorical(d["series_id"], categories=ids).codes
    a_cu, b_cu, a_moi, b_moi = mu_cu[s], sd_cu[s], mu_moi[s], sd_moi[s]
    for c in COT_LAG + ["roll_mean_6", "roll_min_6", "roll_max_6",
                        "roll_mean_12", "roll_min_12", "roll_max_12", "target"]:
        d[c] = (d[c].to_numpy() * b_cu + a_cu - a_moi) / b_moi
    for c in ["roll_std_6", "roll_std_12", "diff_1"]:
        d[c] = d[c].to_numpy() * b_cu / b_moi
    return d


# ─────────────────────────────── P2 ───────────────────────────────

def kiem_p2(df, ids, b0, h, g_n2):
    s, off, hop_le = vi_tri(df, ids, b0)
    kq = so_dac_trung(df, s, off, hop_le, g_n2)
    kq["dong_cham_z0"] = int((hop_le & (off <= 24)).sum())        # lag_24 tại t ≤ 24 dùng z[≤0]
    kq["dong_vuot_cuoi"] = int((hop_le & (off + h > N_CUA_SO - 1)).sum())
    kq["dong_la"] = int((~hop_le).sum())
    kq["offset_nho_nhat"] = int(off[hop_le].min()) if hop_le.any() else -1
    kq["dat"] = (kq["dat"] and kq["dong_cham_z0"] == 0 and kq["dong_vuot_cuoi"] == 0
                 and kq["dong_la"] == 0)
    return kq


def dot_bien_bac_cau(df, ids, b0, Y, h, lich, kieu_target):
    """Bản sao ma trận N2 như thể sai phân tính trên mảng nối các chuỗi (không groupby):
    z[0] của chuỗi i = y_i[0] − y_{i−1}[2303]. Dòng t = 24 khi đó thành 'hợp lệ' và xuất hiện."""
    Zb = sai_phan_trong_chuoi(Y)
    Zb[1:, 0] = Y[1:, 0] - Y[:-1, N_CUA_SO - 1]
    gb = luoi_dac_trung(Zb)
    t = 24
    ok = np.isfinite(Zb[:, : t + 1]).all(axis=1) & np.isfinite(Y[:, t + h])
    si = np.nonzero(ok)[0]
    moi = {"series_id": [ids[i] for i in si], "bucket": np.full(len(si), b0 + t, dtype=np.int64)}
    for c in COT_GIA_TRI:
        moi[c] = gb[c][si, t]
    for c in COT_LICH:
        moi[c] = lich[c][si, t]
    moi["target"] = (Y[si, t + h] - Y[si, t]) if kieu_target == "qd019" else Zb[si, t + h]
    return pd.concat([df, pd.DataFrame(moi)[df.columns]], ignore_index=True), len(si)


# ─────────────────────────────── P3 ───────────────────────────────

def luoi_tu_ma_tran(df, ids, b0, cot):
    s, off, hop_le = vi_tri(df, ids, b0)
    co = np.zeros((len(ids), N_CUA_SO), dtype=bool)
    co[s[hop_le], off[hop_le]] = True
    out = {}
    for c in cot:
        a = np.full((len(ids), N_CUA_SO), np.nan)
        a[s[hop_le], off[hop_le]] = df[c].to_numpy(np.float64)[hop_le]
        out[c] = a
    return co, out


def kiem_p3(luoi_a, luoi_b):
    (co_a, a), (co_b, b) = luoi_a, luoi_b
    chung = co_a & co_b
    khac = 0
    lech = 0.0
    for c in COT_LICH:
        x, y = a[c][chung], b[c][chung]
        kb = int((x.view(np.uint64) != y.view(np.uint64)).sum())    # so BIT, kể cả NaN
        khac += kb
        if x.size:
            lech = max(lech, float(np.nanmax(np.abs(x - y))) if kb else 0.0)
    return {"so_khoa_chung": int(chung.sum()), "o_khac_bit": khac, "lech_max": lech,
            "dat": khac == 0 and chung.sum() > 0}


# ─────────────────────────────── P4 ───────────────────────────────

def target_ky_vong(che_do, Y, s, off, h, hop_le, mu, sd):
    tr = lay(Y, s, off + h, hop_le & (off + h < N_CUA_SO))
    if che_do == "N0":
        return tr
    if che_do == "N1":
        m = np.where(hop_le, s, 0)
        return (tr - mu[m]) / sd[m]
    return tr - lay(Y, s, off, hop_le)                      # N2: y(t+h) − y(t)


def kiem_p4(df, che_do, ids, b0, Y, h, mu, sd):
    s, off, hop_le = vi_tri(df, ids, b0)
    ky_vong = target_ky_vong(che_do, Y, s, off, h, hop_le, mu, sd)
    kb, lm_abs, lm = so_o(df["target"].to_numpy(), ky_vong)
    thuc = df["target"].to_numpy(np.float64)
    n_vuot = int((~(do_lech(thuc, ky_vong) <= TOL_CHAT)).sum())
    kq = {"so_dong": len(df), "khac_bit": kb, "dong_lech_vuot_tol": n_vuot, "lech_max": lm_abs,
          "lech_tdoi_max": lm, "dat": n_vuot == 0}
    if che_do == "N2":
        # chẩn đoán: có khớp định nghĩa lỗi y(t+h) − y(t+h−1) không
        cu = lay(Y, s, off + h, hop_le & (off + h < N_CUA_SO)) - \
            lay(Y, s, off + h - 1, hop_le & (off + h - 1 < N_CUA_SO))
        kq["dong_khop_dinh_nghia_cu"] = int((np.abs(thuc - cu) <= TOL_CHAT).sum())
    return kq


# ─────────────────────── luật dòng hợp lệ (thông tin) ───────────────────────

def mat_na_hop_le(F: np.ndarray, sau: int, F_target: np.ndarray, h: int) -> np.ndarray:
    """Dòng t hợp lệ khi F sạch trên [t−sau, t] và F_target[t+h]."""
    S, T = F.shape
    c = np.zeros((S, T + 1), dtype=np.int32)
    c[:, 1:] = np.cumsum(F, axis=1)
    ok = np.zeros((S, T), dtype=bool)
    t = np.arange(sau, T - h)
    ok[:, t] = ((c[:, t + 1] - c[:, t - sau]) == sau + 1) & F_target[:, t + h]
    return ok


def so_tap_dong(co, ok):
    return {"thieu": int((ok & ~co).sum()), "thua": int((co & ~ok).sum())}


# ─────────────────────────────── chạy ───────────────────────────────

BANG = []
DOT_BIEN = []


def ghi(tinh_chat, env, che_do, h, nguon, kq, chi_so):
    BANG.append({"tính chất": tinh_chat, "env": env, "chế độ": che_do, "h": h, "nguồn": nguon,
                 "chỉ số": chi_so, "kết quả": "PASS" if kq["dat"] else "FAIL"})


def ghi_dot_bien(ten, env, kq_dot_bien, mo_ta):
    bat = not kq_dot_bien["dat"]
    DOT_BIEN.append({"đột biến": ten, "env": env, "chi tiết": mo_ta,
                     "kết quả": "BẮT ĐƯỢC" if bat else "KHÔNG BẮT ĐƯỢC"})


def main():
    t_bat_dau = time.time()
    bang_chuan = pd.read_csv(GOC / "results" / "tables" / "normalize_gd4.csv")
    H_DOT_BIEN = 6
    THONG_TIN = []

    for env in ENVS:
        t0 = time.time()
        ids, b0, Y = nap_chuoi(env)
        n = len(ids)
        mu_tr, sd_tr, n_tr = thong_ke_train(Y)
        mu_toan, sd_toan = np.nanmean(Y, axis=1), np.nanstd(Y, axis=1, ddof=1)

        # ── P1a: bảng
        b = bang_chuan[bang_chuan["env"] == env]
        bn1 = b[b["mode"] == "N1"].set_index("series_id")
        thua_bang = sorted(set(bn1.index) ^ set(ids))
        mu_bang = bn1["mu"].reindex(ids).to_numpy(np.float64)
        sd_bang = bn1["sd"].reindex(ids).to_numpy(np.float64)
        kq = kiem_p1_bang(ids, mu_bang, sd_bang, mu_tr, sd_tr)
        n0n2_co_so = int(b[b["mode"] != "N1"][["mu", "sd"]].notna().to_numpy().sum())
        kq["dat"] = kq["dat"] and not thua_bang and n0n2_co_so == 0
        khac_toan = int((np.abs(mu_toan - mu_tr) > 1e-6 * sd_tr).sum())
        ghi("P1a bảng", env, "N1", "-", "normalize_gd4.csv", kq,
            f"{n} chuỗi; lệch|mu|max={kq['lech_mu_max']:.2e}; lệch sd tương đối max="
            f"{kq['lech_sd_tdoi_max']:.2e}; chuỗi sai={kq['chuoi_sai']}; id lệch tập={len(thua_bang)}; "
            f"ô mu/sd có số ở N0/N2={n0n2_co_so}; (chuỗi có mu toàn chuỗi ≠ mu train: {khac_toan})")
        n_dong = bn1["n_dong_train"].reindex(ids).to_numpy()
        THONG_TIN.append(f"{env}: n_dong_train == số điểm y hữu hạn trong train ở "
                         f"{int((n_dong == n_tr).sum())}/{n} chuỗi (cột này không có trong đặc tả)")

        # đột biến P1a
        ghi_dot_bien("P1a: mu/sd toàn chuỗi", env, kiem_p1_bang(ids, mu_toan, sd_toan, mu_tr, sd_tr),
                     "thay bảng bằng thống kê toàn 2304 bucket")
        ghi_dot_bien("P1a: ddof=0", env,
                     kiem_p1_bang(ids, mu_tr, np.nanstd(Y[:, :N_TRAIN], axis=1, ddof=0), mu_tr, sd_tr),
                     "sd tính với ddof=0")
        ghi_dot_bien("P1a: tráo chuỗi", env,
                     kiem_p1_bang(ids, np.roll(mu_tr, 1), np.roll(sd_tr, 1), mu_tr, sd_tr),
                     "gán mu/sd của chuỗi liền trước")

        # lưới đặc trưng chuẩn cho N1 (từ mu/sd đã khai) và N2 (sai phân trong chuỗi)
        g_n1 = luoi_dac_trung((Y - mu_bang[:, None]) / sd_bang[:, None])
        Z2 = sai_phan_trong_chuoi(Y)
        g_n2 = luoi_dac_trung(Z2)
        lich = luoi_lich(b0, n)
        F_y, F_z = np.isfinite(Y), np.isfinite(Z2)

        for h in HS:
            dfs = {m: doc_ma_tran(GOC / "data" / "features" / f"{env}_{m}_h{h}.parquet")
                   for m in ("N0", "N1", "N2")}
            dfs["N2q"] = doc_ma_tran(GOC / "data" / "features_qd019" / f"{env}_N2_h{h}.parquet")

            # ── P1b: ma trận N1
            kq = kiem_p1_ma_tran(dfs["N1"], ids, b0, Y, mu_bang, sd_bang, g_n1, mu_toan, sd_toan)
            ghi("P1b ma trận", env, "N1", h, "features", kq,
                f"{len(dfs['N1'])} dòng; ô khác bit={kq['khac_bit']}; lệch tđ lag/diff/min/max="
                f"{kq['lech_chat']:.1e}; roll_mean={kq['lech_roll_mean']:.1e}; roll_std="
                f"{kq['lech_roll_std']:.1e}; giải ngược khớp bảng {kq['chuoi_khop_bang']}/{n} "
                f"(khớp tk toàn chuỗi {kq['chuoi_khop_tk_toan_chuoi']}); lệch mu giải ngược/sd="
                f"{kq['lech_mu_giai_nguoc']:.1e}")
            if h == H_DOT_BIEN:
                d = dot_bien_chuan_hoa_lai(dfs["N1"], ids, mu_bang, sd_bang, mu_toan, sd_toan)
                k2 = kiem_p1_ma_tran(d, ids, b0, Y, mu_bang, sd_bang, g_n1, mu_toan, sd_toan)
                ghi_dot_bien("P1b: N1 dựng bằng tk toàn chuỗi", env, k2,
                             f"h={h}; giải ngược khớp bảng {k2['chuoi_khop_bang']}/{n}, khớp toàn chuỗi "
                             f"{k2['chuoi_khop_tk_toan_chuoi']}/{n}; lệch ô max={k2['lech_chat']:.1e}")
                d = dot_bien_chuan_hoa_lai(dfs["N1"], ids, mu_bang, sd_bang,
                                           np.roll(mu_bang, 1), np.roll(sd_bang, 1))
                k2 = kiem_p1_ma_tran(d, ids, b0, Y, mu_bang, sd_bang, g_n1, mu_toan, sd_toan)
                ghi_dot_bien("P1b: N1 dựng bằng tk chuỗi khác", env, k2,
                             f"h={h}; giải ngược khớp bảng {k2['chuoi_khop_bang']}/{n}; "
                             f"lệch ô max={k2['lech_chat']:.1e}")

            # ── P2: N2 cũ và N2 QĐ-019
            for khoa, nguon, kieu in (("N2", "features", "cu"), ("N2q", "features_qd019", "qd019")):
                kq = kiem_p2(dfs[khoa], ids, b0, h, g_n2)
                ghi("P2 không bắc cầu", env, "N2", h, nguon, kq,
                    f"{len(dfs[khoa])} dòng; offset nhỏ nhất={kq['offset_nho_nhat']}; dòng chạm z[0]="
                    f"{kq['dong_cham_z0']}; dòng t+h vượt cuối={kq['dong_vuot_cuoi']}; ô khác bit="
                    f"{kq['khac_bit']}; lệch tđ lag/diff/min/max={kq['lech_chat']:.1e}; roll_mean="
                    f"{kq['lech_roll_mean']:.1e}; roll_std={kq['lech_roll_std']:.1e}")
                if h == H_DOT_BIEN:
                    d, n_them = dot_bien_bac_cau(dfs[khoa], ids, b0, Y, h, lich, kieu)
                    k2 = kiem_p2(d, ids, b0, h, g_n2)
                    ghi_dot_bien(f"P2: sai phân bắc cầu ({nguon})", env, k2,
                                 f"h={h}; thêm {n_them} dòng t=24 có lag_24 bắc cầu; phép kiểm thấy "
                                 f"dòng chạm z[0]={k2['dong_cham_z0']}, ô khác bit={k2['khac_bit']}")

            # ── P3: lịch
            luoi = {m: luoi_tu_ma_tran(dfs[m], ids, b0, COT_LICH) for m in dfs}
            for m in ("N1", "N2", "N2q"):
                kq = kiem_p3(luoi["N0"], luoi[m])
                ten = {"N1": "N0 vs N1", "N2": "N0 vs N2", "N2q": "N0 vs N2(qd019)"}[m]
                ghi("P3 lịch", env, ten, h, "features" if m != "N2q" else "features+qd019", kq,
                    f"khoá chung={kq['so_khoa_chung']}; ô khác bit={kq['o_khac_bit']}")
            # N1 và N2 phủ cùng khoá? (N2 bắt đầu muộn 1 bucket nên có phần không chung)
            for m in ("N0", "N1", "N2", "N2q"):
                co, a = luoi[m]
                lm = max(float(np.nanmax(np.abs(a[c][co] - lich[c][co]))) for c in COT_LICH)
                THONG_TIN.append(f"{env} h={h} {m}: lệch lịch so với công thức QĐ-010 "
                                 f"(giờ nguyên UTC, dow=((t//86400)+4)%7) max={lm:.1e}")
            if h == H_DOT_BIEN:
                # (a) chuẩn hoá nhầm cả cột lịch ở N1
                d = dfs["N1"].copy()
                sc = pd.Categorical(d["series_id"], categories=ids).codes
                for c in COT_LICH:
                    d[c] = (d[c].to_numpy() - mu_bang[sc]) / sd_bang[sc]
                k2 = kiem_p3(luoi["N0"], luoi_tu_ma_tran(d, ids, b0, COT_LICH))
                ghi_dot_bien("P3: z-score nhầm cột lịch N1", env, k2,
                             f"h={h}; ô khác bit={k2['o_khac_bit']}")
                # (b) nhân cột lịch N2 với 1 + 1e-6
                d = dfs["N2"].copy()
                for c in COT_LICH:
                    d[c] = d[c].to_numpy() * (1 + 1e-6)
                k2 = kiem_p3(luoi["N0"], luoi_tu_ma_tran(d, ids, b0, COT_LICH))
                ghi_dot_bien("P3: nhân lịch N2 ×(1+1e-6)", env, k2,
                             f"h={h}; ô khác bit={k2['o_khac_bit']}, lệch max={k2['lech_max']:.1e}")
                # (c) lịch N2 lệch một bucket (lấy của t−1)
                d = dfs["N2q"].copy()
                s_, off_, hl_ = vi_tri(d, ids, b0)
                for c in COT_LICH:
                    d[c] = lay(lich[c], s_, off_ - 1, hl_ & (off_ >= 1))
                k2 = kiem_p3(luoi["N0"], luoi_tu_ma_tran(d, ids, b0, COT_LICH))
                ghi_dot_bien("P3: lịch N2(qd019) trễ 1 bucket", env, k2,
                             f"h={h}; ô khác bit={k2['o_khac_bit']}")

            # ── P4: target
            for khoa, che_do, nguon in (("N0", "N0", "features"), ("N1", "N1", "features"),
                                        ("N2", "N2", "features"), ("N2q", "N2", "features_qd019")):
                kq = kiem_p4(dfs[khoa], che_do, ids, b0, Y, h, mu_bang, sd_bang)
                them = (f"; dòng khớp định nghĩa cũ y(t+h)−y(t+h−1)={kq['dong_khop_dinh_nghia_cu']}"
                        if che_do == "N2" else "")
                ghi("P4 target", env, che_do, h, nguon, kq,
                    f"{kq['so_dong']} dòng; khác bit={kq['khac_bit']}; lệch tđ>1e-9={kq['dong_lech_vuot_tol']}; "
                    f"lệch max={kq['lech_max']:.2e} (tđ {kq['lech_tdoi_max']:.1e}){them}")
            if h == H_DOT_BIEN:
                d = dfs["N0"].copy()
                s_, off_, hl_ = vi_tri(d, ids, b0)
                d["target"] = lay(Y, s_, off_ + h - 1, hl_)
                k2 = kiem_p4(d, "N0", ids, b0, Y, h, mu_bang, sd_bang)
                ghi_dot_bien("P4: target N0 = y(t+h−1)", env, k2,
                             f"h={h}; dòng lệch={k2['dong_lech_vuot_tol']}")

            # ── thông tin: tập dòng so với luật dòng hợp lệ
            ok_y = mat_na_hop_le(F_y, 24, F_y, h)
            ok_z = mat_na_hop_le(F_z, 24, F_z, h)
            ok_q = mat_na_hop_le(F_y, 25, F_y, h)
            for m, ok, luat in (("N0", ok_y, "y sạch [t−24,t] & y(t+h)"),
                                ("N1", ok_y, "y sạch [t−24,t] & y(t+h)"),
                                ("N2", ok_z, "z sạch [t−24,t] & z(t+h) (luật cũ)"),
                                ("N2q", ok_q, "y sạch [t−25,t] & y(t+h) (QĐ-019)")):
                tt = so_tap_dong(luoi[m][0], ok)
                THONG_TIN.append(f"{env} h={h} {m}: tập dòng so với luật '{luat}': "
                                 f"thiếu {tt['thieu']}, thừa {tt['thua']}")
            del dfs, luoi
        print(f"  … xong {env} trong {time.time() - t0:.0f} s", flush=True)
        del g_n1, g_n2, Y

    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 220)
    pd.set_option("display.max_rows", 500)
    bang = pd.DataFrame(BANG)
    print("\n" + "=" * 100)
    print("KIỂM ĐỘC LẬP QĐ-016 / QĐ-019 — BẢNG PASS/FAIL")
    print("=" * 100)
    for tc, nhom in bang.groupby("tính chất", sort=False):
        print(f"\n── {tc}")
        print(nhom.drop(columns="tính chất").to_string(index=False))

    print("\n" + "=" * 100)
    print("TỰ KIỂM ĐỘT BIẾN (phải BẮT ĐƯỢC tất cả)")
    print("=" * 100)
    db = pd.DataFrame(DOT_BIEN)
    print(db.to_string(index=False))

    print("\n── Thông tin bổ sung (không tính vào PASS/FAIL)")
    for dong in THONG_TIN:
        print("  " + dong)

    print("\n" + "=" * 100)
    print("TỔNG KẾT")
    for tc, nhom in bang.groupby(bang["tính chất"].str.slice(0, 2), sort=False):
        n_fail = int((nhom["kết quả"] == "FAIL").sum())
        print(f"  {tc}: {len(nhom) - n_fail}/{len(nhom)} PASS"
              + ("" if n_fail == 0 else "  ← FAIL: " + ", ".join(
                  f"{r.env}/{r['chế độ']}/h{r.h}/{r['nguồn']}" for _, r in nhom[nhom['kết quả'] == 'FAIL'].iterrows())))
    n_db_truot = int((db["kết quả"] != "BẮT ĐƯỢC").sum())
    print(f"  Đột biến: {len(db) - n_db_truot}/{len(db)} bắt được")
    print(f"  Thời gian: {time.time() - t_bat_dau:.0f} s")
    return 0 if (bang["kết quả"] == "PASS").all() and n_db_truot == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
