"""QĐ-017 — phân tích D1, D2 đúng như đã khai. VIẾT VÀ COMMIT TRƯỚC KHI CÓ KẾT QUẢ.

    python scripts/phan_tich_qd017.py

Đọc:

    results/tables/qd017_d1_chuoi.csv   đường chéo E1→E1, E2→E2, E3→E3
    results/tables/qd017_d2_chuoi.csv   E1a ↔ E1g
    results/tables/per_series_gd4.csv   transfer GĐ4, lịch = co

Sinh `results/tables/qd017_t_d1a.csv`, `_t_d1b.csv`, `_t_d1c.csv`, `_t_d2.csv`, và
`qd017_du_doan.csv` — một dòng mỗi dự đoán P1–P7, kèm số đo và kết luận **theo đúng luật
đã khai**.

Mọi ngưỡng, họ Holm và luật đọc đều chép từ `docs/decisions.md` QĐ-017 điểm 4 và 5.
Script này **không có tham số nào để chỉnh** ngưỡng. Muốn đổi thì phải có QĐ mới, và kết
quả cũ vẫn báo cáo.

Chặn cứng (QĐ-017 điểm 6.2): không phân tích D1 nếu R3 của `check_qd017.py` trượt, tức
đường chéo N0 không tái lập được GĐ3. Không phân tích một thí nghiệm khi bảng của nó
chưa đủ khoá.

Quy ước hướng, giữ nguyên GĐ3/GĐ4:

- Wilcoxon: hướng lấy từ **trung vị của hiệu** ghép cặp theo chuỗi, không từ hiệu hai
  trung vị. Lần GĐ3 làm ngược, kết luận đảo ở 8 cặp.
- Mann–Whitney: `rb = 2U/(n₁n₂) − 1` với `U` của mẫu chiều xuôi. `rb > 0` nghĩa là
  chiều xuôi có `L` lớn hơn, tức **chiều xuôi tốn hơn**.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from fig_gd4_transfer import holm  # noqa: E402

ALPHA = 0.05
ML = ["lr", "ridge", "rf", "xgb", "svr"]
MODES = ["N0", "N1", "N2"]
HS = [1, 6, 12]
BIT, ALI = ("E1", "E2"), ("E3",)
DOI_XUNG_D1 = [(("E1", "E3"), ("E3", "E1")), (("E2", "E3"), ("E3", "E2")),
               (("E1", "E2"), ("E2", "E1"))]
DOI_XUNG_D2 = [(("E1a", "E1g"), ("E1g", "E1a"))]   # xuôi = đơn lẻ → gộp


# ------------------------------------------------------------------ phép kiểm

def wilcoxon_hop(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """`(trung vị của hiệu a − b, p)`; hiệu toàn 0 thì p = 1."""
    hieu = a - b
    if len(hieu) == 0:
        return float("nan"), float("nan")
    if np.allclose(hieu, 0):
        return 0.0, 1.0
    return float(np.median(hieu)), float(wilcoxon(a, b).pvalue)


def huong(co_y_nghia: bool, hieu: float, am: str, duong: str) -> str:
    if not co_y_nghia:
        return "không khác"
    if hieu < 0:
        return am
    if hieu > 0:
        return duong
    return "có ý nghĩa, trung vị hiệu = 0"


def holm_theo(df: pd.DataFrame, nhom: list[str] | None) -> pd.Series:
    out = pd.Series(np.nan, index=df.index)
    groups = df.groupby(nhom).groups.items() if nhom else [(None, df.index)]
    for _, idx in groups:
        out.loc[idx] = holm(df.loc[idx, "p"].to_numpy())
    return out


def t_d1a(cheo: pd.DataFrame) -> pd.DataFrame:
    """Trong môi trường: N1, N2 so với N0. Họ Holm mỗi `(env, h)`: 10 phép."""
    w = cheo.pivot_table(index=["dich", "h", "model", "series_id"], columns="mode",
                         values="mae").reset_index()
    dong = []
    for (env, h, m), g in w.groupby(["dich", "h", "model"]):
        for md in ("N1", "N2"):
            s = g[["N0", md]].dropna()
            hieu, p = wilcoxon_hop(s[md].to_numpy(), s["N0"].to_numpy())
            dong.append({"env": env, "h": h, "model": m, "so_sanh": f"{md}_vs_N0",
                         "n_chuoi": len(s), "hieu_p50": hieu, "p": p})
    out = pd.DataFrame(dong)
    out["p_holm"] = holm_theo(out, ["env", "h"])
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    out["ket_luan"] = [huong(s, d, "Nk tốt hơn N0", "Nk tệ hơn N0")
                       for s, d in zip(out["co_y_nghia"], out["hieu_p50"])]
    return out


def ghep_L(chuyen: pd.DataFrame, cheo: pd.DataFrame) -> pd.DataFrame:
    """Ghép MAE transfer với MAE đường chéo **cùng đích, chế độ, h, model, chuỗi**.

    `L = mae / mae_cheo`. Chuỗi có `mae_cheo` bằng 0 hoặc không hữu hạn bị loại khỏi
    `L` (tỉ số vô nghĩa) nhưng vẫn giữ trong cột `mae` cho T-D1b.
    """
    c = cheo[["dich", "mode", "h", "model", "series_id", "mae"]].rename(
        columns={"mae": "mae_cheo"})
    x = chuyen[["nguon", "dich", "mode", "h", "model", "series_id", "mae"]].merge(
        c, on=["dich", "mode", "h", "model", "series_id"], how="inner")
    x = x[x["nguon"] != x["dich"]].copy()
    hop_le = np.isfinite(x["mae_cheo"]) & (x["mae_cheo"] > 0) & np.isfinite(x["mae"])
    x["L"] = np.where(hop_le, x["mae"] / x["mae_cheo"].where(hop_le, 1.0), np.nan)
    return x


def t_d1b(L: pd.DataFrame) -> pd.DataFrame:
    """Transfer có mất gì: MAE(A→B,k) vs MAE(B→B,k). Họ mỗi `(nguồn, đích, h)`: 15 phép."""
    dong = []
    for (ng, di, md, h, m), g in L.groupby(["nguon", "dich", "mode", "h", "model"]):
        s = g[np.isfinite(g["mae"]) & np.isfinite(g["mae_cheo"])]
        hieu, p = wilcoxon_hop(s["mae"].to_numpy(), s["mae_cheo"].to_numpy())
        dong.append({"nguon": ng, "dich": di, "mode": md, "h": h, "model": m,
                     "n_chuoi": len(s), "L_p50": float(np.nanmedian(g["L"])),
                     "hieu_p50": hieu, "p": p})
    out = pd.DataFrame(dong)
    out["p_holm"] = holm_theo(out, ["nguon", "dich", "h"])
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    out["ket_luan"] = [huong(s, d, "transfer tốt hơn đường chéo", "transfer tệ hơn đường chéo")
                       for s, d in zip(out["co_y_nghia"], out["hieu_p50"])]
    return out


def bat_doi_xung(L: pd.DataFrame, doi_xung) -> pd.DataFrame:
    """Mann–Whitney trên `L` theo chuỗi, chiều xuôi vs ngược. Holm trên CẢ bảng."""
    dong = []
    for xuoi, nguoc in doi_xung:
        for md in MODES:
            for h in HS:
                for m in ML:
                    def lay(cp):
                        v = L[(L["nguon"] == cp[0]) & (L["dich"] == cp[1]) & (L["mode"] == md)
                              & (L["h"] == h) & (L["model"] == m)]["L"].to_numpy()
                        return v[np.isfinite(v)]
                    a, b = lay(xuoi), lay(nguoc)
                    if len(a) == 0 or len(b) == 0:
                        continue
                    u, p = mannwhitneyu(a, b, alternative="two-sided")
                    dong.append({"xuoi": f"{xuoi[0]}->{xuoi[1]}",
                                 "nguoc": f"{nguoc[0]}->{nguoc[1]}", "mode": md, "h": h,
                                 "model": m, "n_xuoi": len(a), "n_nguoc": len(b),
                                 "L_p50_xuoi": float(np.median(a)),
                                 "L_p50_nguoc": float(np.median(b)),
                                 "rank_biserial": 2.0 * float(u) / (len(a) * len(b)) - 1.0,
                                 "p": float(p)})
    out = pd.DataFrame(dong)
    out["p_holm"] = holm_theo(out, None)
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    # rb < 0: chiều xuôi có L nhỏ hơn -> ngược tốn hơn. Bản nháp đầu truyền `-r` và đảo
    # nhãn; tests/test_qd017.py::test_bat_doi_xung_huong giữ ca này.
    out["ket_luan"] = [huong(s, r, "ngược tốn hơn", "xuôi tốn hơn")
                       for s, r in zip(out["co_y_nghia"], out["rank_biserial"])]
    out["huong_khop_trung_vi"] = (np.sign(out["rank_biserial"])
                                  == np.sign(out["L_p50_xuoi"] - out["L_p50_nguoc"]))
    return out


# ------------------------------------------------------------ luật đọc

def doc_d2(n_nguoc_ton: int, n_xuoi_ton: int) -> str:
    """Luật đọc T-D2 ở N1 — QĐ-017 điểm 5, trên 15 phép."""
    if n_nguoc_ton >= 10 and n_xuoi_ton == 0:
        return "tái hiện"
    if n_nguoc_ton <= 3:
        return "không tái hiện"
    return "không kết luận"


def dem(df: pd.DataFrame, **loc) -> pd.Series:
    x = df
    for k, v in loc.items():
        x = x[x[k].isin(v)] if isinstance(v, (list, tuple, set)) else x[x[k] == v]
    return x["ket_luan"].value_counts()


def du_doan(a: pd.DataFrame | None, b: pd.DataFrame | None, c: pd.DataFrame | None,
            d2: pd.DataFrame | None) -> pd.DataFrame:
    dong = []

    def them(ma, noi_dung, so_do, dat):
        dong.append({"ma": ma, "du_doan": noi_dung, "so_do": so_do,
                     "ket_qua": "chưa có" if dat is None else ("đúng" if dat else "sai")})

    if a is not None:
        n = {e: int(dem(a, env=e, so_sanh="N1_vs_N0").get("Nk tốt hơn N0", 0)) for e in BIT}
        them("P1", "E1, E2: N1 tốt hơn N0 ở ≥ 8/15 phép, mỗi môi trường",
             f"E1 {n['E1']}/15, E2 {n['E2']}/15", all(v >= 8 for v in n.values()))
        k = int(dem(a, env="E3", so_sanh="N2_vs_N0").get("Nk tệ hơn N0", 0))
        them("P2", "E3: N2 tệ hơn N0 ở ≥ 8/15 phép", f"{k}/15", k >= 8)
    else:
        them("P1", "E1, E2: N1 tốt hơn N0 ở ≥ 8/15 phép", "", None)
        them("P2", "E3: N2 tệ hơn N0 ở ≥ 8/15 phép", "", None)

    if b is not None:
        def tv(ng, di, md):
            return float(b[(b.nguon == ng) & (b.dich == di) & (b["mode"] == md)]["L_p50"].median())
        v3 = {f"{n}->{d}": tv(n, d, "N1") for n, d in (("E1", "E2"), ("E2", "E1"))}
        them("P3", "E1↔E2 ở N1: trung vị L trong [0,95; 1,10], cả hai chiều",
             ", ".join(f"{k} {x:.3f}" for k, x in v3.items()),
             all(0.95 <= x <= 1.10 for x in v3.values()))
        v4 = {f"{n}->{d}": tv(n, d, "N2") for n, d in
              (("E1", "E3"), ("E3", "E1"), ("E2", "E3"), ("E3", "E2"))}
        them("P4", "Bitbrains↔Alibaba ở N2: trung vị L trong [0,95; 1,25], cả 4 cặp",
             ", ".join(f"{k} {x:.3f}" for k, x in v4.items()),
             all(0.95 <= x <= 1.25 for x in v4.values()))
    else:
        them("P3", "E1↔E2 ở N1: trung vị L trong [0,95; 1,10]", "", None)
        them("P4", "Bitbrains↔Alibaba ở N2: trung vị L trong [0,95; 1,25]", "", None)

    if c is not None:
        ba = ["E1->E3", "E2->E3"]
        k5 = dem(c, xuoi=ba, mode="N1")
        n5 = int(k5.get("ngược tốn hơn", 0))
        them("P5", "N1: Alibaba→Bitbrains tốn hơn ở ≥ 20/30 phép", f"{n5}/30", n5 >= 20)
        k6 = dem(c, xuoi=ba, mode="N2")
        x6, y6 = int(k6.get("xuôi tốn hơn", 0)), int(k6.get("ngược tốn hơn", 0))
        them("P6", "N2: không chiều nào thắng quá 20/30 phép",
             f"xuôi tốn hơn {x6}, ngược tốn hơn {y6}", x6 <= 20 and y6 <= 20)
    else:
        them("P5", "N1: Alibaba→Bitbrains tốn hơn ở ≥ 20/30 phép", "", None)
        them("P6", "N2: không chiều nào thắng quá 20/30 phép", "", None)

    if d2 is not None:
        k = dem(d2, mode="N1")
        ng, xu = int(k.get("ngược tốn hơn", 0)), int(k.get("xuôi tốn hơn", 0))
        kl = doc_d2(ng, xu)
        them("P7", "D2 ở N1: tái hiện (gộp→đơn lẻ tốn hơn ≥ 10/15, 0 phép ngược lại)",
             f"gộp→đơn lẻ tốn hơn {ng}/15, đơn lẻ→gộp tốn hơn {xu}/15 → {kl}",
             kl == "tái hiện")
    else:
        them("P7", "D2 ở N1: tái hiện", "", None)
    return pd.DataFrame(dong)


# -------------------------------------------------------------------- chạy

def _du_khoa(p: Path, caps) -> bool:
    if not p.exists():
        return False
    t = pd.read_csv(p, usecols=["nguon", "dich", "mode", "h", "model"]).drop_duplicates()
    co = set(map(tuple, t.to_numpy()))
    return all((n, d, md, h, m) in co for n, d in caps for md in MODES for h in HS for m in ML)


def main() -> int:
    import check_qd017

    tab = ROOT / "results" / "tables"
    p1, p2 = tab / "qd017_d1_chuoi.csv", tab / "qd017_d2_chuoi.csv"
    co_d1 = _du_khoa(p1, check_qd017.CAP["D1"])
    co_d2 = _du_khoa(p2, check_qd017.CAP["D2"])
    print("\nPHÂN TÍCH QĐ-017")
    print(f"D1: {'đủ khoá' if co_d1 else 'CHƯA ĐỦ — bỏ qua'} · "
          f"D2: {'đủ khoá' if co_d2 else 'CHƯA ĐỦ — bỏ qua'}")

    if co_d1:
        rep = check_qd017.Report()
        check_qd017.nhom_r(rep, tab)
        r3 = [r for r in rep.rows if r[1].startswith("R3")]
        if not r3 or r3[0][2] != check_qd017.OK:
            print("DỪNG — R3 (tái lập GĐ3 ở đường chéo N0) chưa đạt. QĐ-017 điểm 6.2 cấm "
                  "phân tích D1. Chạy check_qd017.py để xem chi tiết.")
            return 1
        print(f"R3 đạt: {r3[0][3]}")

    a = b = c = d2 = None
    if co_d1:
        cheo = pd.read_csv(p1).query("nguon == dich")
        g4 = pd.read_csv(tab / "per_series_gd4.csv")
        g4 = g4[g4["lich"] == "co"]
        a = t_d1a(cheo)
        L = ghep_L(g4, cheo)
        b = t_d1b(L)
        c = bat_doi_xung(L, DOI_XUNG_D1)
        for ten, df in (("t_d1a", a), ("t_d1b", b), ("t_d1c", c)):
            df.to_csv(tab / f"qd017_{ten}.csv", index=False)
        print(f"\nT-D1a — {len(a)} phép")
        print(a.groupby(["env", "so_sanh"])["ket_luan"].value_counts().unstack(fill_value=0))
        print(f"\nT-D1b — {len(b)} phép; trung vị L qua model và h")
        print(b.pivot_table(index=["nguon", "dich"], columns="mode", values="L_p50",
                            aggfunc="median").round(3))
        print(b.groupby(["nguon", "dich", "mode"])["ket_luan"].value_counts()
              .unstack(fill_value=0))
        print(f"\nT-D1c — {len(c)} phép; hướng rank-biserial khớp trung vị ở "
              f"{int(c.loc[c.co_y_nghia, 'huong_khop_trung_vi'].sum())}/{int(c.co_y_nghia.sum())} "
              "phép có ý nghĩa")
        print(c.groupby(["xuoi", "mode"])["ket_luan"].value_counts().unstack(fill_value=0))

    if co_d2:
        L2 = ghep_L(pd.read_csv(p2), pd.read_csv(p2).query("nguon == dich"))
        d2 = bat_doi_xung(L2, DOI_XUNG_D2)
        d2.to_csv(tab / "qd017_t_d2.csv", index=False)
        print(f"\nT-D2 — {len(d2)} phép (xuôi = E1a→E1g, đơn lẻ → gộp)")
        print(d2.groupby("mode")["ket_luan"].value_counts().unstack(fill_value=0))
        print(d2.groupby("mode")[["L_p50_xuoi", "L_p50_nguoc"]].median().round(3))

    dd = du_doan(a, b, c, d2)
    dd.to_csv(tab / "qd017_du_doan.csv", index=False)
    print("\nDỰ ĐOÁN ĐÃ KHAI (QĐ-017)")
    for r in dd.itertuples():
        print(f"  {r.ma} [{r.ket_qua:^7}] {r.du_doan}")
        if r.so_do:
            print(f"               {r.so_do}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
