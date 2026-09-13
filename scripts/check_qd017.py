"""Kiểm sản phẩm QĐ-017 — dữ liệu máy giả, và kết quả D1, D2 khi đã có.

    python scripts/check_qd017.py

Ba nhóm:

| Nhóm | Kiểm gì | Cần kết quả chạy? |
|---|---|---|
| **C** — dựng lại độc lập | nhóm, E1a, E1g, ma trận, `mu`/`sd`, CV | không |
| **B** — B2, B3, B11, B12 của `check_gd4.py` áp lên E1a, E1g | chế độ chuẩn hoá | không |
| **R** — kết quả | đủ khoá; `n_chuoi + n_loai`; **tái lập GĐ3** ở đường chéo N0 | có |

Nhóm C **không gọi** hàm nào của `build_qd017.py`: gộp bằng `groupby` của pandas thay vì
ma trận numpy, đếm dòng hợp lệ bằng tích luỹ thay vì `make_feature_matrix`. Thước đo mà
đi hỏi bản bị đo thì đo cái gì.

R3 là phép kiểm tái lập bắt buộc của QĐ-017 điểm 6.2, và là **phép duy nhất được đọc số
của D1 trước khi `phan_tich_qd017.py` chạy**. Số nó đọc là đường chéo N0, vốn đã biết
ở GĐ3.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_gd4  # noqa: E402

OK, FAIL, WARN = check_gd4.OK, check_gd4.FAIL, check_gd4.WARN
W, N_TRAIN, MAX_LAG = 2304, 1612, 24
HORIZONS, MODES = (1, 6, 12), ("N0", "N1", "N2")
ML = ("lr", "ridge", "rf", "xgb", "svr")
METRICS = ("mae", "rmse", "smape", "mase", "r2")
CAP = {"D1": [("E1", "E1"), ("E2", "E2"), ("E3", "E3")],
       "D2": [("E1a", "E1a"), ("E1a", "E1g"), ("E1g", "E1g"), ("E1g", "E1a")]}
# QĐ-017 điểm 6.2, đặt theo số đo trên đường chéo N0 (đã biết từ GĐ3). Cây ép float32
# bên trong nên trùng tuyệt đối; lr, ridge, svr lệch vì GĐ3 float32 còn GĐ4 float64 —
# đo được tối đa 5,4e-3, trung vị <= 5,5e-4. Bản nháp đặt 1e-3 cho mọi model là đoán.
NGUONG_CAY = 1e-9
NGUONG_TUYEN_TINH_MAX = 2e-2
NGUONG_TUYEN_TINH_P50 = 2e-3


class Report(check_gd4.Report):
    def show(self):
        cur = None
        for g, item, st, detail in self.rows:
            if g != cur:
                print(f"\n── {g}")
                cur = g
            print(f"  [{ {OK: '  ok  ', FAIL: ' TRƯỢT', WARN: ' cảnh báo'}[st] }] {item}")
            if detail:
                print(f"           {detail}")
        print("\n" + "=" * 70)
        print(f"CHƯA ĐẠT — {self.failed} mục trượt." if self.failed
              else "ĐẠT — sản phẩm QĐ-017 hiện có khớp mọi phép kiểm.")
        print("=" * 70)
        return 1 if self.failed else 0


def _dai(p: Path, cot=("series_id", "bucket", "y")) -> pd.DataFrame:
    return pd.read_parquet(p, columns=list(cot)).sort_values(["series_id", "bucket"])


# ================================================== C — dựng lại độc lập

def nhom_c(rep: Report, proc: Path, feat: Path, tab: Path, gop_p: Path) -> None:
    g = "C. Dựng lại độc lập"
    e1 = _dai(proc / "E1.parquet")
    ids = sorted(e1["series_id"].unique())

    # C1 — danh sách nhóm: đúng hạt giống, đúng cỡ, rời nhau, phủ kín E1.
    nh = pd.read_csv(gop_p, keep_default_na=False)
    hv = [ids[i] for i in np.random.default_rng(42).permutation(len(ids))]
    a = nh.loc[nh.env == "E1a", "vm"].tolist()
    gm = nh[nh.env == "E1g"]
    xau = []
    if a != hv[:368]:
        xau.append("E1a không phải 368 phần tử đầu của hoán vị")
    if gm["vm"].tolist() != hv[368:368 + 365]:
        xau.append("thành viên E1g không theo đúng thứ tự hoán vị")
    co = gm.groupby("series_id")["vm"].agg(["size", "nunique"])
    if len(co) != 73 or not ((co["size"] == 5) & (co["nunique"] == 5)).all():
        xau.append(f"{len(co)} nhóm, cỡ {sorted(co['size'].unique())}")
    if set(a) & set(gm["vm"]):
        xau.append("E1a và E1g chung VM")
    if sorted(nh["vm"]) != ids:
        xau.append("hợp các nửa không phủ đúng 735 VM của E1")
    rep.add(g, "C1 — config/qd017_gop.csv đúng hạt giống 42, 368 + 73×5 + 2, rời nhau",
            FAIL if xau else OK, "; ".join(xau))

    # C2 — E1a là bản sao tuyệt đối của E1 trên đúng 368 VM.
    ea = _dai(proc / "E1a.parquet")
    goc = e1[e1["series_id"].isin(a)]
    ok = (len(ea) == len(goc) == 368 * W
          and np.array_equal(ea["y"].to_numpy(), goc["y"].to_numpy(), equal_nan=True))
    rep.add(g, "C2 — E1a.parquet trùng tuyệt đối E1 trên 368 VM", OK if ok else FAIL)

    # C3 — E1g gộp lại bằng groupby: mean khi đủ 5 thành viên hữu hạn.
    m = e1.merge(gm.rename(columns={"series_id": "nhom"})[["nhom", "vm"]],
                 left_on="series_id", right_on="vm")
    q = m.groupby(["nhom", "bucket"])["y"].agg(["mean", "count"]).reset_index()
    q.loc[q["count"] < 5, "mean"] = np.nan
    q = q.sort_values(["nhom", "bucket"])
    eg = _dai(proc / "E1g.parquet")
    lech = np.abs(eg["y"].to_numpy() - q["mean"].to_numpy())
    cung_nan = np.array_equal(np.isnan(eg["y"].to_numpy()), np.isnan(q["mean"].to_numpy()))
    ok = len(eg) == 73 * W and cung_nan and float(np.nanmax(lech)) <= 1e-12
    rep.add(g, "C3 — E1g = trung bình chặt của 5 thành viên (NaN khi thiếu)",
            OK if ok else FAIL, f"lệch tối đa {np.nanmax(lech):.2e}, NaN trùng: {cung_nan}")

    # C4 — ma trận của E1a trùng tuyệt đối lát cắt tương ứng của E1, mọi chế độ.
    xau = []
    for mode in MODES:
        for h in HORIZONS:
            pa, pe = feat / f"E1a_{mode}_h{h}.parquet", feat / f"E1_{mode}_h{h}.parquet"
            if not (pa.exists() and pe.exists()):
                xau.append(f"thiếu {mode} h{h}")
                continue
            x = pd.read_parquet(pa).sort_values(["series_id", "bucket"]).reset_index(drop=True)
            y = pd.read_parquet(pe)
            y = (y[y["series_id"].isin(a)].sort_values(["series_id", "bucket"])
                 .reset_index(drop=True))
            if not x.equals(y):
                xau.append(f"{mode} h{h}")
    rep.add(g, "C4 — 9 ma trận E1a trùng tuyệt đối lát cắt E1 (N1 cùng mu/sd, N2 cùng sai phân)",
            FAIL if xau else OK, "; ".join(xau))

    # C5 — số dòng N0 của E1g theo luật cửa sổ, đếm bằng tích luỹ.
    Y = eg["y"].to_numpy().reshape(73, W)
    bad = (~np.isfinite(Y)).astype(int)
    cs = np.concatenate([np.zeros((73, 1), int), np.cumsum(bad, axis=1)], axis=1)
    xau = []
    for h in HORIZONS:
        t = np.arange(MAX_LAG, W - h)
        sach = (cs[:, t + 1] - cs[:, t - MAX_LAG]) == 0
        du = sach & np.isfinite(Y[:, t + h])
        mong = int(du.sum())
        p = feat / f"E1g_N0_h{h}.parquet"
        that = len(pd.read_parquet(p, columns=["bucket"])) if p.exists() else -1
        if that != mong:
            xau.append(f"h{h}: ma trận {that:,} ≠ luật cửa sổ {mong:,}")
    rep.add(g, "C5 — số dòng N0 của E1g khớp luật cửa sổ [t−24, t] và t+h",
            FAIL if xau else OK, "; ".join(xau))

    # C6 — mu/sd: E1a trùng normalize_gd4 của E1; E1g tính lại trên [0, 1612).
    nq = pd.read_csv(tab / "normalize_qd017.csv")
    ng = pd.read_csv(tab / "normalize_gd4.csv")
    n1q = nq[nq["mode"] == "N1"].set_index(["env", "series_id"])
    a1 = n1q.loc["E1a"].sort_index()
    e1n = ng[(ng["mode"] == "N1") & (ng["env"] == "E1")].set_index("series_id").loc[a1.index]
    ok_a = np.array_equal(a1[["mu", "sd"]].to_numpy(), e1n[["mu", "sd"]].to_numpy())
    g1 = n1q.loc["E1g"].sort_index()
    mu = np.nanmean(Y[:, :N_TRAIN], axis=1)
    sd = np.nanstd(Y[:, :N_TRAIN], axis=1, ddof=1)
    l_mu = float(np.max(np.abs(g1["mu"].to_numpy() - mu)))
    l_sd = float(np.max(np.abs(g1["sd"].to_numpy() - sd)))
    ok = ok_a and max(l_mu, l_sd) <= 1e-9
    rep.add(g, "C6 — mu/sd: E1a trùng E1 tuyệt đối; E1g khớp tính lại trên [0, 1612)",
            OK if ok else FAIL, f"E1a trùng: {ok_a}; E1g lệch mu {l_mu:.1e}, sd {l_sd:.1e}")

    # C7 — CV của E1a khớp cv_gd2 của E1. Ngưỡng 5e-6 chứ không chặt hơn: `cv_gd2.csv`
    # ghi làm tròn 6 chữ số thập phân (ví dụ `3.663241`), bản đầu đặt 1e-9 và báo oan
    # ở mức 5,0e-7 — đúng nửa đơn vị làm tròn.
    cq = pd.read_csv(tab / "cv_qd017.csv")
    c2 = pd.read_csv(tab / "cv_gd2.csv")
    x = cq[cq.env == "E1a"].set_index("series_id")["cv"].sort_index()
    y = c2[c2.env == "E1"].set_index("series_id")["cv"].loc[x.index]
    l = float(np.max(np.abs(x.to_numpy() - y.to_numpy())))
    rep.add(g, "C7 — CV của E1a khớp cv_gd2.csv của E1 (tệp đó làm tròn 6 chữ số)",
            OK if l <= 5e-6 else FAIL, f"lệch tối đa {l:.1e}")


# ================================================ B — phép kiểm của GĐ4

def nhom_b(rep: Report, feat: Path, tab: Path) -> None:
    """Gọi `check_gd4.loai_b_so_dong` với danh sách môi trường là E1a, E1g.

    B1 tự bỏ qua vì hai môi trường này không có neo catalog — C5 thay nó.
    """
    cu = check_gd4.ENVS
    check_gd4.ENVS = ["E1a", "E1g"]
    try:
        tam = Report()
        check_gd4.loai_b_so_dong(feat, pd.DataFrame(columns=["env", "kept"]), tam,
                                 pd.read_csv(tab / "normalize_qd017.csv"))
    finally:
        check_gd4.ENVS = cu
    for _, item, st, detail in tam.rows:
        # "B1 " có dấu cách: `startswith("B1")` nuốt luôn B11, B12 — đã xảy ra ở bản đầu.
        if item.startswith("B1 "):
            continue
        rep.add("B. Phép kiểm GĐ4 trên E1a, E1g", item, st, detail)


# ======================================================== R — kết quả

def nhom_r(rep: Report, tab: Path) -> None:
    for tn, caps in CAP.items():
        g = f"R. Kết quả {tn}"
        p = tab / f"qd017_{tn.lower()}.csv"
        pc = tab / f"qd017_{tn.lower()}_chuoi.csv"
        if not p.exists():
            rep.add(g, f"{p.name} chưa có — bỏ qua nhóm này", WARN)
            continue
        t = pd.read_csv(p)
        mong = {(n, d, m, "co", h, md, me) for n, d in caps for m in MODES
                for h in HORIZONS for md in ML for me in METRICS}
        co = set(map(tuple, t[["nguon", "dich", "mode", "lich", "h", "model", "metric"]]
                      .to_numpy()))
        thieu, thua = mong - co, co - mong
        rep.add(g, f"R1 — đủ {len(mong)} dòng, không thừa",
                OK if not thieu and not thua else (WARN if thieu and not thua else FAIL),
                f"thiếu {len(thieu)}, thừa {len(thua)}" if thieu or thua else "")

        tong = t.groupby("dich").apply(lambda x: set(x["n_chuoi"] + x["n_loai"]),
                                       include_groups=False)
        xau = [f"{d}: {sorted(v)}" for d, v in tong.items() if len(v) != 1]
        rep.add(g, "R2 — n_chuoi + n_loai không đổi trong mỗi đích", FAIL if xau else OK,
                "; ".join(xau))

        if tn != "D1" or not pc.exists():
            continue
        c = pd.read_csv(pc)
        c = c[c["mode"] == "N0"]
        g3 = pd.read_csv(tab / "per_series_gd3.csv")
        j = c.merge(g3, left_on=["dich", "h", "model", "series_id"],
                    right_on=["env", "h", "model", "series_id"], suffixes=("", "_gd3"))
        if j.empty:
            rep.add(g, "R3 — tái lập GĐ3: chưa có dòng N0 nào", WARN)
            continue
        j["rel"] = (j["mae"] - j["mae_gd3"]).abs() / j["mae_gd3"].abs().clip(lower=1e-12)
        kiem = j[(j["model"] != "svr") | (j["h"] == 1)]
        bao = j[(j["model"] == "svr") & (j["h"] != 1)]
        xau, chi_tiet = [], []
        n_lech_dong = int((j["n_dong"] != j["n_dong_gd3"]).sum())
        if n_lech_dong:
            xau.append(f"{n_lech_dong} chuỗi lệch n_dong — tập dòng test khác GĐ3")
        for (d, h, md), x in kiem.groupby(["dich", "h", "model"]):
            r, r50 = float(x["rel"].max()), float(x["rel"].median())
            if md in ("rf", "xgb"):
                if r > NGUONG_CAY:
                    xau.append(f"{d} h{h} {md}: tối đa {r:.1e} > {NGUONG_CAY:g}")
            elif r > NGUONG_TUYEN_TINH_MAX or r50 > NGUONG_TUYEN_TINH_P50:
                xau.append(f"{d} h{h} {md}: tối đa {r:.1e}, trung vị {r50:.1e}")
        cay = kiem[kiem["model"].isin(["rf", "xgb"])]["rel"]
        tt = kiem[~kiem["model"].isin(["rf", "xgb"])]["rel"]
        chi_tiet.append(f"{kiem.groupby(['dich', 'h', 'model']).ngroups} tổ hợp; "
                        f"cây tối đa {cay.max():.1e}; tuyến tính + svr h1 tối đa "
                        f"{tt.max():.1e}")
        if not bao.empty:
            chi_tiet.append(f"svr h6/h12 (chỉ báo, mẫu con khác): trung vị "
                            f"{bao['rel'].median():.1e}")
        rep.add(g, "R3 — đường chéo N0 tái lập per_series_gd3 (QĐ-017 điểm 6.2: cây "
                   "≤ 1e-9; lr, ridge, svr h1 tối đa ≤ 2e-2, trung vị ≤ 2e-3; n_dong trùng)",
                FAIL if xau else OK, "; ".join(xau[:6]) if xau else " · ".join(chi_tiet))


def main() -> int:
    proc, feat, tab = ROOT / "data/processed", ROOT / "data/features", ROOT / "results/tables"
    rep = Report()
    print("\nKIỂM SẢN PHẨM QĐ-017")
    nhom_c(rep, proc, feat, tab, ROOT / "config" / "qd017_gop.csv")
    nhom_b(rep, feat, tab)
    nhom_r(rep, tab)
    return rep.show()


if __name__ == "__main__":
    sys.exit(main())
