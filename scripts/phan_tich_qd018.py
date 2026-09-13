"""QĐ-018 — phân tích độ nhạy N1. VIẾT VÀ COMMIT TRƯỚC KHI CÓ KẾT QUẢ.

    python scripts/phan_tich_qd018.py

Thay **mọi dòng N1** của ba bảng theo chuỗi (`per_series_gd4.csv` lịch = co,
`qd017_d1_chuoi.csv`, `qd017_d2_chuoi.csv`) bằng số của `qd018_n1_chuoi.csv`, giữ nguyên
N0 và N2. Chạy lại **đúng** T-D1a, T-D1b, T-D1c, T-D2 bằng hàm của `phan_tich_qd017.py`.
Chấm lại P1–P7 và chấm S1–S5 của QĐ-018 điểm 5.

Sinh `results/tables/qd018_t_d1a.csv`, `_t_d1b.csv`, `_t_d1c.csv`, `_t_d2.csv`,
`qd018_du_doan.csv`, và `qd018_so_sanh.csv` — bản gốc cạnh bản độ nhạy.

Chặn cứng: K2–K5 của `check_qd018.py` phải đạt (QĐ-018 điểm 6.2).
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

KHOA_TO_HOP = ["nguon", "dich", "h", "model"]


def thay_n1(goc: pd.DataFrame, moi: pd.DataFrame) -> pd.DataFrame:
    """Bỏ dòng N1 của `goc` ở những `(nguồn, đích, h, model)` mà `moi` có, rồi nối `moi`.

    Chỉ đụng dòng N1. Tổ hợp `moi` không có thì `goc` giữ nguyên — nhưng QĐ-018 chạy đủ
    mọi tổ hợp N1 của ba bảng, và K2 của `check_qd018.py` đảm bảo điều đó.
    """
    m = moi[moi["mode"] == "N1"]
    to_hop = set(map(tuple, m[KHOA_TO_HOP].drop_duplicates().to_numpy()))
    n1 = goc["mode"] == "N1"
    trung = np.array([tuple(r) in to_hop for r in goc[KHOA_TO_HOP].to_numpy()], dtype=bool)
    con = goc[~(n1 & trung)]
    cot = [c for c in goc.columns if c in m.columns]
    return pd.concat([con, m[cot]], ignore_index=True)


def cham_s(a, b, dd: pd.DataFrame, dd_goc: pd.DataFrame) -> pd.DataFrame:
    """S1–S5 của QĐ-018 điểm 5."""
    def tv(ng, di):
        return float(b[(b.nguon == ng) & (b.dich == di) & (b["mode"] == "N1")]["L_p50"].median())

    k1 = int(pt.dem(a, env="E3", so_sanh="N1_vs_N0").get("Nk tệ hơn N0", 0))
    s2 = {f"{n}->{d}": tv(n, d) for n, d in (("E3", "E1"), ("E3", "E2"))}
    s3 = {f"{n}->{d}": tv(n, d) for n, d in (("E1", "E3"), ("E2", "E3"))}
    kq = dd.set_index("ma")["ket_qua"]
    kg = dd_goc.set_index("ma")["ket_qua"]
    dong = [
        ("S1", "T-D1a E3: N1 tệ hơn N0 ở ≤ 7/15 phép", f"{k1}/15", k1 <= 7),
        ("S2", "T-D1b E3→E1, E3→E2 ở N1: trung vị L < 1,5",
         ", ".join(f"{k} {v:.3f}" for k, v in s2.items()), all(v < 1.5 for v in s2.values())),
        ("S3", "T-D1b E1→E3, E2→E3 ở N1: trung vị L ≥ 0,95",
         ", ".join(f"{k} {v:.3f}" for k, v in s3.items()), all(v >= 0.95 for v in s3.values())),
        ("S4", "P5 vẫn đúng dưới bản độ nhạy", f"P5 = {kq['P5']}", kq["P5"] == "đúng"),
        ("S5", "P1, P3 giữ nguyên chấm", f"P1 {kg['P1']}→{kq['P1']}, P3 {kg['P3']}→{kq['P3']}",
         kq["P1"] == kg["P1"] and kq["P3"] == kg["P3"]),
    ]
    return pd.DataFrame([{"ma": m, "du_doan": n, "so_do": s, "ket_qua": "đúng" if d else "sai"}
                         for m, n, s, d in dong])


def so_sanh(tab: Path, a, b, c, d2) -> pd.DataFrame:
    """Bảng cạnh nhau cho mọi con số N1 đã báo ở QĐ-017."""
    ga = pd.read_csv(tab / "qd017_t_d1a.csv")
    gb = pd.read_csv(tab / "qd017_t_d1b.csv")
    gc = pd.read_csv(tab / "qd017_t_d1c.csv")
    gd = pd.read_csv(tab / "qd017_t_d2.csv")
    dong = []
    for (ng, di), x in b[b["mode"] == "N1"].groupby(["nguon", "dich"]):
        y = gb[(gb["mode"] == "N1") & (gb.nguon == ng) & (gb.dich == di)]
        dong.append({"bang": "T-D1b", "nhom": f"{ng}->{di}", "chi_so": "trung vị L_p50",
                     "goc": float(y["L_p50"].median()), "do_nhay": float(x["L_p50"].median())})
    for env in ("E1", "E2", "E3"):
        for kl in ("Nk tốt hơn N0", "Nk tệ hơn N0", "không khác"):
            dong.append({"bang": "T-D1a", "nhom": f"{env} N1_vs_N0", "chi_so": kl,
                         "goc": int(pt.dem(ga, env=env, so_sanh="N1_vs_N0").get(kl, 0)),
                         "do_nhay": int(pt.dem(a, env=env, so_sanh="N1_vs_N0").get(kl, 0))})
    for bang, g, m in (("T-D1c", gc, c), ("T-D2", gd, d2)):
        for xu in sorted(m["xuoi"].unique()):
            for kl in ("xuôi tốn hơn", "ngược tốn hơn", "không khác"):
                dong.append({"bang": bang, "nhom": f"{xu} N1", "chi_so": kl,
                             "goc": int(pt.dem(g, xuoi=xu, mode="N1").get(kl, 0)),
                             "do_nhay": int(pt.dem(m, xuoi=xu, mode="N1").get(kl, 0))})
    return pd.DataFrame(dong)


def main() -> int:
    import check_qd018

    tab = ROOT / "results" / "tables"
    print("\nPHÂN TÍCH QĐ-018 — N1 độ nhạy")
    dat, rows = check_qd018.chan_phan_tich(tab)
    for r in rows:
        print(f"  [{r[2]}] {r[1]}  {r[3]}")
    if not dat:
        print("DỪNG — K2–K5 chưa đạt (QĐ-018 điểm 6.2). Chạy check_qd018.py để xem chi tiết.")
        return 1

    moi = pd.read_csv(tab / "qd018_n1_chuoi.csv")
    g4 = pd.read_csv(tab / "per_series_gd4.csv")
    g4 = g4[g4["lich"] == "co"]
    d1 = pd.read_csv(tab / "qd017_d1_chuoi.csv").query("nguon == dich")
    d2 = pd.read_csv(tab / "qd017_d2_chuoi.csv")

    cheo = thay_n1(d1, moi[moi["nguon"] == moi["dich"]])
    chuyen = thay_n1(g4, moi[moi["nguon"] != moi["dich"]])
    d2s = thay_n1(d2, moi[moi["nguon"].isin(["E1a", "E1g"])])

    a = pt.t_d1a(cheo)
    L = pt.ghep_L(chuyen, cheo)
    b = pt.t_d1b(L)
    c = pt.bat_doi_xung(L, pt.DOI_XUNG_D1)
    d2t = pt.bat_doi_xung(pt.ghep_L(d2s, d2s.query("nguon == dich")), pt.DOI_XUNG_D2)
    for ten, df in (("t_d1a", a), ("t_d1b", b), ("t_d1c", c), ("t_d2", d2t)):
        df.to_csv(tab / f"qd018_{ten}.csv", index=False)

    dd = pt.du_doan(a, b, c, d2t)
    dd_goc = pd.read_csv(tab / "qd017_du_doan.csv")
    s = cham_s(a, b, dd, dd_goc)
    ra = pd.concat([dd.assign(ban="độ nhạy QĐ-018"), s.assign(ban="dự đoán QĐ-018")],
                   ignore_index=True)
    ra.to_csv(tab / "qd018_du_doan.csv", index=False)
    ss = so_sanh(tab, a, b, c, d2t)
    ss.to_csv(tab / "qd018_so_sanh.csv", index=False)

    print("\nBẢN GỐC (QĐ-017) CẠNH BẢN ĐỘ NHẠY (QĐ-018) — chỉ dòng N1")
    print(ss.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\nP1–P7 CHẤM LẠI (P2, P4, P6 không dính N1)")
    g = dd_goc.set_index("ma")
    for r in dd.itertuples():
        doi = "" if g.loc[r.ma, "ket_qua"] == r.ket_qua else "   ← ĐỔI CHẤM"
        print(f"  {r.ma} gốc [{g.loc[r.ma, 'ket_qua']:^7}] độ nhạy [{r.ket_qua:^7}] "
              f"{r.du_doan}{doi}")
        if r.so_do:
            print(f"               {r.so_do}")
    print("\nDỰ ĐOÁN QĐ-018")
    for r in s.itertuples():
        print(f"  {r.ma} [{r.ket_qua:^5}] {r.du_doan}\n               {r.so_do}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
