"""Kiểm sản phẩm QĐ-019 — ma trận N2 target đúng, và kết quả chạy lại khi đã có.

    python scripts/check_qd019.py

| Mục | Kiểm gì | Chặn |
|---|---|---|
| K1 | `target` == `y_{t+h} − y_t` tra thẳng từ `data/processed/`, lệch **0** | chạy |
| K2 | h = 1 trùng tuyệt đối ma trận N2 của GĐ4 | chạy |
| K3 | dòng GĐ4 ⊆ dòng mới; 19 cột đặc trưng trùng tuyệt đối trên dòng chung | chạy |
| K4 | số dòng khớp luật `y` sạch trên `[t−25, t]` và `y_{t+h}` hữu hạn, đếm bằng numpy | chạy |
| R1 | đủ khoá kết quả | phân tích |
| R2 | E1g h = 1 trùng QĐ-017, lệch MAE ≤ 1e−9 | phân tích |
| R3 | `n_dong` theo chuỗi không nhỏ hơn bản lỗi | phân tích |

K1 là phép kiểm mà GĐ4 thiếu: bất biến `Δ̂ = 0` của QĐ-016 đúng với **cả** định nghĩa sai,
nên chỉ so target với chuỗi gốc bằng một đường tính khác mới bắt được lỗi.
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

import check_qd017  # noqa: E402

OK, FAIL, WARN = check_qd017.OK, check_qd017.FAIL, check_qd017.WARN
ENVS = ("E1", "E2", "E3", "E1a", "E1g")
HS = (1, 6, 12)
W, LAG = 2304, 24
ML = ("lr", "ridge", "rf", "xgb", "svr")
METRICS = ("mae", "rmse", "smape", "mase", "r2")
CAP = [("E1", "E1"), ("E1", "E2"), ("E1", "E3"), ("E2", "E2"), ("E2", "E1"), ("E2", "E3"),
       ("E3", "E3"), ("E3", "E1"), ("E3", "E2"), ("E1a", "E1a"), ("E1a", "E1g"),
       ("E1g", "E1g"), ("E1g", "E1a")]
CAP_KIEM = [("E1g", "E1g"), ("E1g", "E1a")]
DAC_TRUNG = ["lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24",
             "roll_mean_6", "roll_std_6", "roll_min_6", "roll_max_6",
             "roll_mean_12", "roll_std_12", "roll_min_12", "roll_max_12",
             "diff_1", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]


class Report(check_qd017.Report):
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
              else "ĐẠT — sản phẩm QĐ-019 hiện có khớp mọi phép kiểm.")
        print("=" * 70)
        return 1 if self.failed else 0


def nhom_k(rep: Report, moi_dir: Path, cu_dir: Path, proc: Path) -> None:
    g = "K. Ma trận N2 target đúng"
    k1, k2, k3, k4 = [], [], [], []
    for env in ENVS:
        d = pd.read_parquet(proc / f"{env}.parquet", columns=["series_id", "bucket", "y"])
        y = d.set_index(["series_id", "bucket"])["y"]
        ds = d.sort_values(["series_id", "bucket"])
        Y = ds["y"].to_numpy("float64").reshape(-1, W)
        bad = (~np.isfinite(Y)).astype(int)
        cs = np.concatenate([np.zeros((len(Y), 1), int), np.cumsum(bad, axis=1)], axis=1)
        for h in HS:
            M = pd.read_parquet(moi_dir / f"{env}_N2_h{h}.parquet")
            # K1 — tra bằng MultiIndex, không dùng groupby.shift như bản dựng.
            yt = y.reindex(pd.MultiIndex.from_arrays([M.series_id, M.bucket])).to_numpy()
            yh = y.reindex(pd.MultiIndex.from_arrays([M.series_id, M.bucket + h])).to_numpy()
            lech = np.abs(M["target"].to_numpy() - (yh - yt))
            if not np.isfinite(lech).all() or float(lech.max()) != 0.0:
                k1.append(f"{env} h{h}: {np.nanmax(lech):.1e}")
            C = pd.read_parquet(cu_dir / f"{env}_N2_h{h}.parquet")
            if h == 1:
                a = M.sort_values(["series_id", "bucket"]).reset_index(drop=True)
                b = C.sort_values(["series_id", "bucket"]).reset_index(drop=True)
                if not a.equals(b):
                    k2.append(f"{env}")
            j = C.merge(M, on=["series_id", "bucket"], how="left", suffixes=("_cu", ""),
                        indicator=True)
            if (j["_merge"] != "both").any():
                k3.append(f"{env} h{h}: {(j['_merge'] != 'both').sum()} dòng cũ mất")
            elif not all(np.array_equal(j[c + "_cu"].to_numpy(), j[c].to_numpy()) for c in DAC_TRUNG):
                k3.append(f"{env} h{h}: đặc trưng lệch")
            t = np.arange(LAG + 1, W - h)
            sach = (cs[:, t + 1] - cs[:, t - LAG - 1]) == 0
            mong = int((sach & np.isfinite(Y[:, t + h])).sum())
            if mong != len(M):
                k4.append(f"{env} h{h}: ma trận {len(M):,} ≠ luật {mong:,}")
    rep.add(g, "K1 — target == y(t+h) − y(t) tra từ data/processed, lệch 0 (15 ma trận)",
            FAIL if k1 else OK, "; ".join(k1))
    rep.add(g, "K2 — h = 1 trùng tuyệt đối ma trận N2 của GĐ4 (5 môi trường)",
            FAIL if k2 else OK, "; ".join(k2))
    rep.add(g, "K3 — dòng GĐ4 ⊆ dòng mới; 19 đặc trưng trùng tuyệt đối trên dòng chung",
            FAIL if k3 else OK, "; ".join(k3))
    rep.add(g, "K4 — số dòng khớp luật y sạch [t−25, t] và y(t+h) hữu hạn",
            FAIL if k4 else OK, "; ".join(k4))


def nap_loi(tab: Path) -> pd.DataFrame:
    """Dòng N2 theo chuỗi của bản lỗi cho đúng các cặp và horizon của QĐ-019."""
    g4 = pd.read_csv(tab / "per_series_gd4.csv")
    g4 = g4[(g4["lich"] == "co") & (g4["mode"] == "N2")]
    d1 = pd.read_csv(tab / "qd017_d1_chuoi.csv")
    d2 = pd.read_csv(tab / "qd017_d2_chuoi.csv")
    x = pd.concat([g4, d1[d1["mode"] == "N2"], d2[d2["mode"] == "N2"]], ignore_index=True)
    return x


def nhom_r(rep: Report, tab: Path) -> None:
    g = "R. Kết quả chạy lại"
    p, pc = tab / "qd019_n2.csv", tab / "qd019_n2_chuoi.csv"
    if not p.exists():
        rep.add(g, f"{p.name} chưa có — bỏ qua", WARN)
        return
    t = pd.read_csv(p)
    mong = ({(n, d, "N2", "co", h, m, me) for n, d in CAP for h in (6, 12) for m in ML
             for me in METRICS}
            | {(n, d, "N2", "co", 1, m, me) for n, d in CAP_KIEM for m in ML for me in METRICS})
    co = set(map(tuple, t[["nguon", "dich", "mode", "lich", "h", "model", "metric"]].to_numpy()))
    rep.add(g, f"R1 — đủ {len(mong)} dòng, không thừa", OK if co == mong else FAIL,
            f"thiếu {len(mong - co)}, thừa {len(co - mong)}")
    moi = pd.read_csv(pc)
    loi = nap_loi(tab)
    k = ["nguon", "dich", "h", "model", "series_id"]
    j = moi.merge(loi, on=k, suffixes=("", "_loi"), how="left")
    e = j[(j.h == 1)]
    l2 = float((e["mae"] - e["mae_loi"]).abs().max()) if len(e) else float("nan")
    rep.add(g, "R2 — E1g h = 1 (đầu vào trùng tuyệt đối) trùng QĐ-017, lệch MAE ≤ 1e−9",
            OK if len(e) and l2 <= 1e-9 else FAIL, f"{len(e)} dòng, lệch tối đa {l2:.1e}")
    h2 = j[j.h != 1]
    thieu = int(h2["n_dong_loi"].isna().sum())
    nho = int((h2["n_dong"] < h2["n_dong_loi"]).sum())
    rep.add(g, "R3 — n_dong theo chuỗi không nhỏ hơn bản lỗi; mọi chuỗi có mặt ở bản lỗi",
            OK if thieu == 0 and nho == 0 else FAIL,
            f"{len(h2):,} dòng, nhỏ hơn {nho}, không ghép được {thieu}; "
            f"tổng dòng thêm {int((h2['n_dong'] - h2['n_dong_loi']).sum()):,}")


def chan_phan_tich(tab: Path | None = None) -> tuple[bool, list]:
    tab = tab or ROOT / "results" / "tables"
    rep = Report()
    nhom_r(rep, tab)
    rows = [r for r in rep.rows if r[1][:2] in ("R1", "R2", "R3")]
    return len(rows) == 3 and all(r[2] == OK for r in rows), rows


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bo-k", action="store_true", help="bỏ nhóm K (chậm, ~2 phút)")
    a = ap.parse_args()
    rep = Report()
    print("\nKIỂM SẢN PHẨM QĐ-019")
    if not a.bo_k:
        nhom_k(rep, ROOT / "data/features_qd019", ROOT / "data/features", ROOT / "data/processed")
    nhom_r(rep, ROOT / "results" / "tables")
    return rep.show()


if __name__ == "__main__":
    sys.exit(main())
