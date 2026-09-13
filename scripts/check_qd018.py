"""Kiểm sản phẩm QĐ-018 — danh sách loại, và kết quả N1 độ nhạy khi đã có.

    python scripts/check_qd018.py

| Mục | Kiểm gì | Chặn phân tích? |
|---|---|---|
| K1 | danh sách loại dựng lại bằng `groupby` của pandas, không gọi `loai_n1_qd018.py`; 0 vi phạm Samuelson trong train; `mu`/`sd` trùng bảng chuẩn hoá | — |
| K2 | đủ 975 dòng kết quả | có |
| K3 | E1g làm nguồn (không loại chuỗi nào) trùng bản QĐ-017, lệch MAE ≤ 1e−9 | **có** — QĐ-018 điểm 6.2 |
| K4 | `n_dong` theo chuỗi trùng bản gốc ở mọi tổ hợp | **có** |
| K5 | dòng train dùng = dòng train gốc − đúng số dòng của chuỗi bị loại | **có** |
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
sys.path.insert(0, str(ROOT / "src"))

import check_qd017  # noqa: E402
from run_qd018 import CAP, HORIZONS, TEN_BANG, TEN_CHUOI, TEN_KHOP  # noqa: E402

OK, FAIL, WARN = check_qd017.OK, check_qd017.FAIL, check_qd017.WARN
ML = ("lr", "ridge", "rf", "xgb", "svr")
METRICS = ("mae", "rmse", "smape", "mase", "r2")
KHOA = ["nguon", "dich", "h", "model", "series_id"]


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
              else "ĐẠT — sản phẩm QĐ-018 hiện có khớp mọi phép kiểm.")
        print("=" * 70)
        return 1 if self.failed else 0


# ============================================================ K1

def k1(rep: Report, proc: Path, tab: Path, cfg: Path) -> None:
    g = "K1. Danh sách loại"
    khai = pd.read_csv(cfg)
    nrm = pd.concat([pd.read_csv(tab / "normalize_gd4.csv"),
                     pd.read_csv(tab / "normalize_qd017.csv")], ignore_index=True)
    nrm = nrm[nrm["mode"] == "N1"].set_index(["env", "series_id"])
    xau, vi_pham, lech_mu = [], 0, 0.0
    for env in ("E1", "E2", "E3", "E1a", "E1g"):
        d = pd.read_parquet(proc / f"{env}.parquet", columns=["series_id", "bucket", "y"])
        d["o"] = d["bucket"] - d["bucket"].min()
        tr = d[(d["o"] < 1612) & d["y"].notna()]
        st = tr.groupby("series_id")["y"].agg(n="count", mu="mean", sd="std")
        kh = d[(d["o"] < 1957) & d["y"].notna()].join(st, on="series_id")
        kh["z"] = (kh["y"] - kh["mu"]).abs() / kh["sd"]
        st["m_khop"] = kh.groupby("series_id")["z"].max()
        st["m_train"] = kh[kh["o"] < 1612].groupby("series_id")["z"].max()
        st["bien"] = (st["n"] - 1) / np.sqrt(st["n"])
        dung = st["sd"] > 0
        vi_pham += int((dung & (st["m_train"] > st["bien"] * (1 + 1e-12))).sum())
        tinh = set(st.index[dung & (st["m_khop"] > st["bien"])])
        co = set(khai.loc[khai["env"] == env, "series_id"])
        if tinh != co:
            xau.append(f"{env}: tính lại {sorted(tinh)} ≠ tệp {sorted(co)}")
        n = nrm.loc[env]
        lech_mu = max(lech_mu, float((st["mu"] - n["mu"].reindex(st.index)).abs().max()),
                      float((st["sd"] - n["sd"].reindex(st.index)).abs().max()))
    rep.add(g, "K1a — config/qd018_loai_n1.csv trùng bản dựng lại độc lập",
            FAIL if xau else OK, "; ".join(xau) or f"{len(khai)} dòng")
    rep.add(g, "K1b — 0 chuỗi vượt giới hạn Samuelson ngay trong cửa sổ train (định lý)",
            FAIL if vi_pham else OK, f"{vi_pham} vi phạm")
    rep.add(g, "K1c — mu/sd dùng cho luật trùng bảng chuẩn hoá N1",
            OK if lech_mu <= 1e-9 else FAIL, f"lệch tối đa {lech_mu:.1e}")


# ================================================ kết quả

def nap_goc(tab: Path) -> pd.DataFrame:
    """Dòng N1 theo chuỗi của bản QĐ-017 cho đúng 13 cặp của QĐ-018."""
    g4 = pd.read_csv(tab / "per_series_gd4.csv")
    g4 = g4[(g4["lich"] == "co") & (g4["mode"] == "N1")]
    d1 = pd.read_csv(tab / "qd017_d1_chuoi.csv")
    d2 = pd.read_csv(tab / "qd017_d2_chuoi.csv")
    x = pd.concat([g4, d1[d1["mode"] == "N1"], d2[d2["mode"] == "N1"]], ignore_index=True)
    cap = set(CAP)
    return x[[(n, d) in cap for n, d in zip(x["nguon"], x["dich"])]]


def k_ket_qua(rep: Report, tab: Path, feat: Path, proc: Path, cfg: Path) -> None:
    g = "K2–K5. Kết quả N1 độ nhạy"
    p, pc, pk = tab / TEN_BANG, tab / TEN_CHUOI, tab / TEN_KHOP
    if not p.exists():
        rep.add(g, f"{p.name} chưa có — bỏ qua", WARN)
        return
    t = pd.read_csv(p)
    mong = {(n, d, "N1", "co", h, m, me) for n, d in CAP for h in HORIZONS for m in ML
            for me in METRICS}
    co = set(map(tuple, t[["nguon", "dich", "mode", "lich", "h", "model", "metric"]].to_numpy()))
    rep.add(g, f"K2 — đủ {len(mong)} dòng, không thừa",
            OK if co == mong else FAIL, f"thiếu {len(mong - co)}, thừa {len(co - mong)}")

    moi = pd.read_csv(pc)
    goc = nap_goc(tab)
    j = moi.merge(goc, on=KHOA, suffixes=("", "_goc"), how="outer", indicator=True)
    thieu = int((j["_merge"] != "both").sum())

    e1g = j[(j["nguon"] == "E1g") & (j["_merge"] == "both")]
    l3 = float((e1g["mae"] - e1g["mae_goc"]).abs().max()) if len(e1g) else float("nan")
    rep.add(g, "K3 — E1g làm nguồn (0 chuỗi loại) trùng bản QĐ-017, lệch MAE ≤ 1e−9",
            OK if len(e1g) and l3 <= 1e-9 else FAIL, f"{len(e1g)} dòng, lệch tối đa {l3:.1e}")

    both = j[j["_merge"] == "both"]
    n_lech = int((both["n_dong"] != both["n_dong_goc"]).sum())
    rep.add(g, "K4 — n_dong theo chuỗi trùng bản gốc; mọi (cặp, h, model, chuỗi) có đủ hai bản",
            OK if n_lech == 0 and thieu == 0 else FAIL,
            f"{len(both):,} dòng ghép, lệch n_dong {n_lech}, không ghép được {thieu}")

    if not pk.exists():
        rep.add(g, "K5 — thiếu qd018_khop.csv", FAIL)
        return
    sys.path.insert(0, str(ROOT / "src"))
    from cwp.evaluation.splits import doc_b0, fit_mask, offset
    loai = pd.read_csv(cfg)
    k = pd.read_csv(pk)
    xau = []
    for r in k.itertuples():
        X = pd.read_parquet(feat / f"{r.nguon}_N1_h{r.h}.parquet", columns=["series_id", "bucket"])
        f = fit_mask(offset(X["bucket"].to_numpy(), doc_b0(r.nguon, proc)), int(r.h))
        bo = X["series_id"].isin(loai.loc[loai["env"] == r.nguon, "series_id"]).to_numpy()
        if int(f.sum()) != r.n_train_goc or int((f & ~bo).sum()) != r.n_train_dung:
            xau.append(f"{r.nguon} h{r.h}: ghi {r.n_train_goc}/{r.n_train_dung}, "
                       f"tính {int(f.sum())}/{int((f & ~bo).sum())}")
    du = len(k) == len({n for n, _ in CAP}) * len(HORIZONS)
    rep.add(g, "K5 — dòng train dùng = gốc − dòng của chuỗi bị loại (mọi nguồn, mọi h)",
            OK if du and not xau else FAIL, "; ".join(xau[:4]) or f"{len(k)} khối")


def chan_phan_tich(tab: Path | None = None) -> tuple[bool, list]:
    """Cho `phan_tich_qd018.py`: đúng khi K2–K5 đều đạt."""
    tab = tab or ROOT / "results" / "tables"
    rep = Report()
    k_ket_qua(rep, tab, ROOT / "data/features", ROOT / "data/processed",
              ROOT / "config" / "qd018_loai_n1.csv")
    rows = [r for r in rep.rows if r[1][:2] in ("K2", "K3", "K4", "K5")]
    return len(rows) == 4 and all(r[2] == OK for r in rows), rows


def main() -> int:
    tab, cfg = ROOT / "results" / "tables", ROOT / "config" / "qd018_loai_n1.csv"
    rep = Report()
    print("\nKIỂM SẢN PHẨM QĐ-018")
    k1(rep, ROOT / "data/processed", tab, cfg)
    k_ket_qua(rep, tab, ROOT / "data/features", ROOT / "data/processed", cfg)
    return rep.show()


if __name__ == "__main__":
    sys.exit(main())
