"""QĐ-019 — bảng cuối cùng của RQ3. VIẾT VÀ COMMIT TRƯỚC KHI CÓ KẾT QUẢ.

    python scripts/phan_tich_qd019.py

Ba bảng theo chuỗi được thay theo thứ tự QĐ-019 điểm 3:

1. dòng N1 ← `qd018_n1_chuoi.csv` (QĐ-018)
2. dòng N2 ở h ∈ {6, 12} ← `qd019_n2_chuoi.csv` (QĐ-019)

rồi chạy lại đúng T-D1a, T-D1b, T-D1c, T-D2 và chấm P1–P7, U1–U2.

Sinh `results/tables/qd019_t_d1a.csv`, `_t_d1b.csv`, `_t_d1c.csv`, `_t_d2.csv`,
`qd019_du_doan.csv`, `qd019_so_sanh.csv` (bản lỗi cạnh bản sửa), và
`qd019_bang_cuoi_L.csv` — trung vị `L` cặp × chế độ dùng cho bài báo.

Chặn cứng: R1–R3 của `check_qd019.py`.
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

import phan_tich_qd017 as pt  # noqa: E402
import phan_tich_qd018 as pq  # noqa: E402

TAB = ROOT / "results" / "tables"
KHOA = ["nguon", "dich", "h", "model"]
GOC = ["E1", "E2", "E3"]


def thay(goc: pd.DataFrame, moi: pd.DataFrame, mode: str, hs: tuple[int, ...]) -> pd.DataFrame:
    """Bỏ dòng `mode` ở các `(nguồn, đích, h, model)` mà `moi` có (chỉ h trong `hs`), nối `moi`."""
    m = moi[(moi["mode"] == mode) & moi["h"].isin(hs)]
    to_hop = set(map(tuple, m[KHOA].drop_duplicates().to_numpy()))
    trung = np.array([tuple(r) in to_hop for r in goc[KHOA].to_numpy()], dtype=bool)
    con = goc[~((goc["mode"] == mode).to_numpy() & trung)]
    cot = [c for c in goc.columns if c in m.columns]
    return pd.concat([con, m[cot]], ignore_index=True)


def tach(moi: pd.DataFrame):
    """Chia dòng mới cho ba bảng — cùng cách `phan_tich_qd018.tach_moi`."""
    return pq.tach_moi(moi)


def bang_cuoi() -> dict[str, pd.DataFrame]:
    g4 = pd.read_csv(TAB / "per_series_gd4.csv")
    g4 = g4[g4["lich"] == "co"]
    d1 = pd.read_csv(TAB / "qd017_d1_chuoi.csv").query("nguon == dich")
    d2 = pd.read_csv(TAB / "qd017_d2_chuoi.csv")
    c18, t18, g18 = tach(pd.read_csv(TAB / "qd018_n1_chuoi.csv"))
    c19, t19, g19 = tach(pd.read_csv(TAB / "qd019_n2_chuoi.csv"))
    cheo = thay(thay(d1, c18, "N1", (1, 6, 12)), c19, "N2", (6, 12))
    chuyen = thay(thay(g4, t18, "N1", (1, 6, 12)), t19, "N2", (6, 12))
    d2s = thay(thay(d2, g18, "N1", (1, 6, 12)), g19, "N2", (6, 12))
    return {"cheo": cheo, "chuyen": chuyen, "d2": d2s}


def cham_u(cheo: pd.DataFrame) -> pd.DataFrame:
    """U1–U2: MAE N2 / MAE naive trong môi trường, trung vị qua 5 model."""
    g3 = pd.read_csv(TAB / "per_series_gd3.csv")
    nv = g3[g3["model"] == "naive"].groupby(["env", "h"])["mae"].median()
    n2 = cheo[cheo["mode"] == "N2"].groupby(["dich", "h", "model"])["mae"].median()
    ts = {(e, h): float(np.median([n2[(e, h, m)] for m in pt.ML])) / float(nv[(e, h)])
          for e in GOC for h in (6, 12)}
    u1 = ts[("E3", 6)] < 0.98 and ts[("E3", 12)] < 0.98
    u2 = all(any(not (0.98 <= ts[(e, h)] <= 1.02) for h in (6, 12)) for e in GOC)
    so = ", ".join(f"{e} h{h} {v:.3f}" for (e, h), v in ts.items())
    return pd.DataFrame([
        {"ma": "U1", "du_doan": "E3: trung vị MAE N2 / naive < 0,98 ở h = 6 và h = 12",
         "so_do": f"E3 h6 {ts[('E3', 6)]:.3f}, h12 {ts[('E3', 12)]:.3f}",
         "ket_qua": "đúng" if u1 else "sai"},
        {"ma": "U2", "du_doan": "mỗi môi trường rời dải [0,98; 1,02] ở ít nhất một horizon",
         "so_do": so, "ket_qua": "đúng" if u2 else "sai"},
    ])


def main() -> int:
    import check_qd019

    print("\nPHÂN TÍCH QĐ-019 — bảng cuối cùng của RQ3")
    dat, rows = check_qd019.chan_phan_tich(TAB)
    for r in rows:
        print(f"  [{r[2]}] {r[1]}  {r[3]}")
    if not dat:
        print("DỪNG — R1–R3 chưa đạt (QĐ-019 điểm 5.3). Chạy check_qd019.py --bo-k.")
        return 1

    b = bang_cuoi()
    a = pt.t_d1a(b["cheo"])
    L = pt.ghep_L(b["chuyen"], b["cheo"])
    t1b = pt.t_d1b(L)
    t1c = pt.bat_doi_xung(L, pt.DOI_XUNG_D1)
    t2 = pt.bat_doi_xung(pt.ghep_L(b["d2"], b["d2"].query("nguon == dich")), pt.DOI_XUNG_D2)
    for ten, df in (("t_d1a", a), ("t_d1b", t1b), ("t_d1c", t1c), ("t_d2", t2)):
        df.to_csv(TAB / f"qd019_{ten}.csv", index=False)

    dd = pt.du_doan(a, t1b, t1c, t2)
    u = cham_u(b["cheo"])
    pd.concat([dd.assign(ban="cuối cùng QĐ-019"), u.assign(ban="dự đoán QĐ-019")],
              ignore_index=True).to_csv(TAB / "qd019_du_doan.csv", index=False)

    cuoi = t1b.pivot_table(index=["nguon", "dich"], columns="mode", values="L_p50",
                           aggfunc="median")
    cuoi.to_csv(TAB / "qd019_bang_cuoi_L.csv")
    cu = pd.read_csv(TAB / "qd018_t_d1b.csv")
    cu = pd.concat([pd.read_csv(TAB / "qd017_t_d1b.csv").query("mode != 'N1'"),
                    cu.query("mode == 'N1'")])
    ss = []
    for (ng, di), x in t1b.groupby(["nguon", "dich"]):
        for h in (6, 12):
            y = cu[(cu.nguon == ng) & (cu.dich == di) & (cu["mode"] == "N2") & (cu.h == h)]
            z = x[(x["mode"] == "N2") & (x.h == h)]
            ss.append({"bang": "T-D1b", "nhom": f"{ng}->{di} N2 h{h}", "chi_so": "trung vị L_p50",
                       "ban_loi": float(y["L_p50"].median()), "ban_sua": float(z["L_p50"].median())})
    ga = pd.read_csv(TAB / "qd018_t_d1a.csv")
    gc = pd.read_csv(TAB / "qd018_t_d1c.csv")
    gd = pd.read_csv(TAB / "qd018_t_d2.csv")
    for env in GOC:
        for kl in ("Nk tốt hơn N0", "Nk tệ hơn N0", "không khác"):
            ss.append({"bang": "T-D1a", "nhom": f"{env} N2_vs_N0", "chi_so": kl,
                       "ban_loi": int(pt.dem(ga[ga.env.isin(GOC)], env=env, so_sanh="N2_vs_N0").get(kl, 0)),
                       "ban_sua": int(pt.dem(a, env=env, so_sanh="N2_vs_N0").get(kl, 0))})
    for bang, g, m in (("T-D1c", gc, t1c), ("T-D2", gd, t2)):
        for xu in sorted(m["xuoi"].unique()):
            for kl in ("xuôi tốn hơn", "ngược tốn hơn", "không khác"):
                ss.append({"bang": bang, "nhom": f"{xu} N2", "chi_so": kl,
                           "ban_loi": int(pt.dem(g, xuoi=xu, mode="N2").get(kl, 0)),
                           "ban_sua": int(pt.dem(m, xuoi=xu, mode="N2").get(kl, 0))})
    ss = pd.DataFrame(ss)
    ss.to_csv(TAB / "qd019_so_sanh.csv", index=False)

    print("\nBẢN LỖI CẠNH BẢN SỬA — chỉ dòng N2")
    print(ss.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\nBẢNG CUỐI — trung vị L qua 5 model × 3 horizon (N1: QĐ-018, N2 h6/12: QĐ-019)")
    print(cuoi.round(3))
    g18 = pd.read_csv(TAB / "qd018_du_doan.csv").query("ma.str.startswith('P')").set_index("ma")
    print("\nP1–P7 CHẤM LẠI TRÊN BẢNG CUỐI")
    for r in dd.itertuples():
        truoc = g18.loc[r.ma, "ket_qua"]
        doi = "" if truoc == r.ket_qua else "   ← ĐỔI CHẤM"
        print(f"  {r.ma} trước [{truoc:^7}] cuối [{r.ket_qua:^7}] {r.du_doan}{doi}")
        if r.so_do:
            print(f"               {r.so_do}")
    print("\nDỰ ĐOÁN QĐ-019")
    for r in u.itertuples():
        print(f"  {r.ma} [{r.ket_qua:^5}] {r.du_doan}\n               {r.so_do}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
