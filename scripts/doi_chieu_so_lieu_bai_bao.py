"""Đối chiếu từng con số trong bản thảo bài báo với bảng kết quả gốc.

    python scripts/doi_chieu_so_lieu_bai_bao.py

Mỗi dòng: con số như bài báo ghi (đã làm tròn), giá trị tính lại từ `results/tables/`
hoặc `data/`, và kết luận khớp hay lệch khi làm tròn cùng số chữ số. Không ghi tệp nào.
Chạy lại mỗi khi bản thảo đổi số hoặc bảng kết quả được sinh lại.
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
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
T = ROOT / "results" / "tables"
P = ROOT / "data" / "processed"
ML = ["lr", "ridge", "rf", "xgb", "svr"]
BIT, ALI = ["E1", "E2"], ["E3"]

dong: list[tuple[str, str, float, float, int]] = []


def ghi(muc: str, cho: str, bai: float, that: float, nd: int = 2) -> None:
    dong.append((muc, cho, bai, float(that), nd))


def khoang(muc, cho, bai_lo, bai_hi, gia_tri, nd=2):
    v = np.asarray(list(gia_tri), dtype=float)
    ghi(muc + " (nhỏ nhất)", cho, bai_lo, v.min(), nd)
    ghi(muc + " (lớn nhất)", cho, bai_hi, v.max(), nd)


def main() -> int:
    cat = pd.read_parquet(ROOT / "data" / "catalog.parquet")
    desc = pd.read_csv(T / "describe_gd2.csv").set_index("env")
    acf = pd.read_csv(T / "acf_gd2.csv")
    for e, vao, loai in (("E1", 1250, 515), ("E2", 500, 198), ("E3", 500, 2)):
        c = cat[cat.env == e]
        ghi(f"{e} số chuỗi đưa vào", "Bảng 1", vao, len(c), 0)
        ghi(f"{e} số chuỗi bị loại", "Bảng 1", loai, int((~c.kept).sum()), 0)
    for e, giu in (("E1", 735), ("E2", 302), ("E3", 498)):
        ghi(f"{e} số chuỗi giữ lại", "Bảng 1", giu, int(cat[(cat.env == e) & cat.kept].shape[0]), 0)
    for e, v in (("E1", 1.78), ("E2", 1.77), ("E3", 37.83)):
        ghi(f"{e} trung vị CPU", "Bảng 1", v, desc.loc[e, "p50"])
    for e, a1, a288 in (("E1", .67, .13), ("E2", .64, .13), ("E3", .86, .60)):
        ghi(f"{e} tự tương quan bậc 1", "Bảng 1", a1, acf[(acf.env == e) & (acf.lag == 1)].acf_p50.iloc[0])
        ghi(f"{e} tự tương quan 24 giờ", "Bảng 1", a288, acf[(acf.env == e) & (acf.lag == 288)].acf_p50.iloc[0])
    for e, v in (("E1", 5.12), ("E2", 2.28), ("E3", 0.0)):
        ghi(f"{e} % điểm chạm trần", "Bảng 1", v, desc.loc[e, "pct_bang_100"])
    for e, v in (("E1", 41), ("E2", 40)):
        c = cat[cat.env == e]
        ghi(f"{e} % chuỗi bị lọc", "III.C", v, 100 * (~c.kept).mean(), 0)
    ghi("E3 % chuỗi bị lọc", "III.C", 0.4, 100 * (~cat[cat.env == "E3"].kept).mean(), 1)

    # ---- câu hỏi thứ nhất
    ex = pd.read_csv(T / "experiments_gd3.csv")
    ex = ex[(ex.metric == "mae") & (ex.model == "naive")].set_index(["env", "h"]).p50
    for e, vs in (("E1", (.408, .466, .449)), ("E2", (.414, .481, .465)), ("E3", (4.296, 6.509, 7.027))):
        for h, v in zip((1, 6, 12), vs):
            ghi(f"MAE naïve {e} h={h}", "Bảng 3", v, ex[(e, h)], 3)
    mv = pd.read_csv(T / "ml_vs_naive_gd3.csv")
    mv = mv[mv.model.isin(ML)]
    for e, v in (("E1", 0), ("E2", 2), ("E3", 11)):
        ghi(f"{e} số phép so ML vượt naïve (trên 15)", "Bảng 3", v, int(mv[mv.env == e].vuot_naive.sum()), 0)
    g3 = pd.read_csv(T / "per_series_gd3.csv")
    nv = g3[g3.model == "naive"][["env", "h", "series_id", "mae"]].rename(columns={"mae": "nv"})
    x = g3[g3.model.isin(ML)].merge(nv, on=["env", "h", "series_id"])
    x = x[x.nv > 0]
    x["ts"] = x.mae / x.nv
    med = x.groupby(["env", "h", "model"]).ts.median()
    khoang("lr, ridge trên VM: tỉ số với naïve", "IV.A", 1.30, 2.66,
           [med[(e, h, m)] for e in BIT for h in (1, 6, 12) for m in ("lr", "ridge")])
    khoang("ML trên E3: tỉ số với naïve", "IV.A (6 đến 16%)", 0.84, 0.94,
           [med[("E3", h, m)] for h in (1, 6, 12) for m in ML])

    # ---- câu hỏi thứ ba — bảng cuối (N1 QĐ-018, N2 QĐ-019)
    b = pd.read_csv(T / "qd019_t_d1b.csv")
    Lm = b.groupby(["nguon", "dich", "mode", "h"]).L_p50.median()
    bang6 = {("E1", "E2"): (1.004, .996, 1.001, 1.002, 1.000, .995, 1.033, .950, .894),
             ("E2", "E1"): (.974, 1.072, 1.081, 1.026, 1.075, 1.067, .970, 1.109, 1.214),
             ("E1", "E3"): (1.063, 1.059, 1.043, 1.032, 1.025, 1.096, 1.064, 1.016, .996),
             ("E2", "E3"): (1.070, 1.088, 1.070, 1.044, 1.042, 1.085, 1.054, 1.048, 1.009),
             ("E3", "E1"): (2.279, 3.320, 2.516, 1.096, 1.332, 1.435, 1.427, 1.820, 1.736),
             ("E3", "E2"): (2.216, 3.421, 3.422, 1.100, 1.175, 1.319, 1.586, 1.834, 1.618)}
    oc = [(m, h) for m in ("N0", "N1", "N2") for h in (1, 6, 12)]
    for (n, d), vs in bang6.items():
        for (m, h), v in zip(oc, vs):
            ghi(f"L {n}→{d} {m} h={h}", "Bảng 4", v, Lm[(n, d, m, h)], 3)
    cuoi = b.groupby(["nguon", "dich", "mode"]).L_p50.median()
    hinh4 = {("E1", "E2"): (1.001, 1.000, .986), ("E2", "E1"): (1.064, 1.063, 1.086),
             ("E1", "E3"): (1.059, 1.032, 1.032), ("E2", "E3"): (1.070, 1.044, 1.048),
             ("E3", "E1"): (2.516, 1.332, 1.588), ("E3", "E2"): (2.819, 1.235, 1.618)}
    for (n, d), vs in hinh4.items():
        for m, v in zip(("N0", "N1", "N2"), vs):
            ghi(f"Hình 4 {n}→{d} {m}", "Hình 4", v, cuoi[(n, d, m)], 3)
    khoang("E1→E2 N0, N1", "IV.C", 0.995, 1.004, [Lm[("E1", "E2", m, h)] for m in ("N0", "N1") for h in (1, 6, 12)], 3)
    khoang("E2→E1 N0, N1 ở h=6, 12", "IV.C", 1.07, 1.08, [Lm[("E2", "E1", m, h)] for m in ("N0", "N1") for h in (6, 12)])
    khoang("E2→E1 N2 ở h=6, 12", "IV.C", 1.11, 1.21, [Lm[("E2", "E1", "N2", h)] for h in (6, 12)])
    khoang("E1→E2 N2 ở h=6, 12", "IV.C", 0.89, 0.95, [Lm[("E1", "E2", "N2", h)] for h in (6, 12)])
    khoang("Alibaba→Bitbrains N0", "Tóm tắt, IV.C", 2.2, 3.4, [Lm[("E3", d, "N0", h)] for d in BIT for h in (1, 6, 12)], 1)
    khoang("Bitbrains→Alibaba N0 (4 đến 9%)", "IV.C", 1.04, 1.09, [Lm[(n, "E3", "N0", h)] for n in BIT for h in (1, 6, 12)])
    khoang("Alibaba→Bitbrains N1 (10 đến 44%)", "Tóm tắt, IV.C", 1.10, 1.44, [Lm[("E3", d, "N1", h)] for d in BIT for h in (1, 6, 12)])
    khoang("Alibaba→Bitbrains N1 h=12", "IV.C", 1.32, 1.44, [Lm[("E3", d, "N1", 12)] for d in BIT])
    khoang("Alibaba→Bitbrains N2 h=1", "IV.C", 1.43, 1.59, [Lm[("E3", d, "N2", 1)] for d in BIT])
    khoang("Alibaba→Bitbrains N2 h=6, 12", "IV.C", 1.62, 1.83, [Lm[("E3", d, "N2", h)] for d in BIT for h in (6, 12)])
    khoang("Bitbrains→Alibaba mọi chế độ", "IV.C", 0.996, 1.096, [Lm[(n, "E3", m, h)] for n in BIT for m in ("N0", "N1", "N2") for h in (1, 6, 12)], 3)
    khoang("E1↔E2 N0, N1 (không quá 8%)", "Tóm tắt", 0.97, 1.08, [Lm[(n, d, m, h)] for n, d in (("E1", "E2"), ("E2", "E1")) for m in ("N0", "N1") for h in (1, 6, 12)])

    c = pd.read_csv(T / "qd019_t_d1c.csv")
    for m, v in (("N0", 30), ("N1", 28), ("N2", 26)):
        k = c[(c["mode"] == m) & c.xuoi.isin(["E1->E3", "E2->E3"])]
        ghi(f"Alibaba→Bitbrains tốn hơn ở {m} (trên 30)", "IV.C", v, int((k.ket_luan == "ngược tốn hơn").sum()), 0)
    for m, v in (("N0", 11), ("N1", 12)):
        k = c[(c["mode"] == m) & (c.xuoi == "E1->E2")]
        ghi(f"E2→E1 tốn hơn E1→E2 ở {m} (trên 15)", "IV.C", v, int((k.ket_luan == "ngược tốn hơn").sum()), 0)
    a = pd.read_csv(T / "qd019_t_d1a.csv")
    for e, v in (("E1", 9), ("E2", 8)):
        k = a[(a.env == e) & (a.so_sanh == "N1_vs_N0")]
        ghi(f"{e}: N1 tốt hơn N0 trong môi trường (trên 15)", "IV.C", v, int((k.ket_luan == "Nk tốt hơn N0").sum()), 0)
    d2 = pd.read_csv(T / "qd019_t_d2.csv")
    k = d2[d2["mode"] == "N1"]
    ghi("Máy giả N1: gộp→đơn lẻ tốn hơn (trên 15)", "IV.C", 8, int((k.ket_luan == "ngược tốn hơn").sum()), 0)
    ghi("Máy giả N1: đơn lẻ→gộp tốn hơn (trên 15)", "IV.C", 6, int((k.ket_luan == "xuôi tốn hơn").sum()), 0)

    import fig_bo_sung as fb
    L, _, _ = fb.bang_L_cuoi()
    s = L[L["mode"] == "N0"].groupby(["nguon", "dich", "series_id"]).L.median()
    for d in BIT:
        ghi(f"p75 của L theo chuỗi E3→{d} N0 (trên 4)", "IV.C, Hình 5", 4.0, min(4.0, s.loc[("E3", d)].quantile(.75)), 1)
    cum = pd.read_csv(T / "bo_sung_cum.csv").groupby("env")[["acf_lag1", "acf_lag288"]].median()
    ghi("Máy giả tự tương quan bậc 1 (train)", "IV.C", 0.91, cum.loc["E1g", "acf_lag1"])
    ghi("E3 tự tương quan bậc 1 (train)", "IV.C", 0.85, cum.loc["E3", "acf_lag1"])
    ghi("Máy giả tự tương quan 24 giờ (train)", "IV.C", 0.03, cum.loc["E1g", "acf_lag288"])
    ghi("E3 tự tương quan 24 giờ (train)", "IV.C", 0.46, cum.loc["E3", "acf_lag288"])
    ghi("E1 / E2 dòng huấn luyện (2,4 lần)", "IV.C", 2.4, 1395851 / 573692, 1)

    # ---- hai lỗi
    loai = pd.read_csv(ROOT / "config" / "qd018_loai_n1.csv")
    for e, v in (("E1", 2), ("E2", 1), ("E3", 10)):
        ghi(f"Số chuỗi loại khỏi train N1 {e}", "IV.D", v, int((loai.env == e).sum()), 0)
    ghi("Máy đứng yên / quần thể E3 (%)", "IV.D", 2, 100 * 10 / 498, 0)
    e3 = loai[loai.env == "E3"]
    ghi("sd huấn luyện nhỏ nhất", "IV.D", 0.003, e3.sd.min(), 3)
    ghi("z lớn nhất", "IV.D", 30196, e3.max_abs_z_khop.max(), 0)
    d1 = pd.read_csv(T / "qd017_d1.csv")
    q18 = pd.read_csv(T / "qd018_n1.csv")
    p50 = lambda t, **k: float(t.query(" & ".join(f"{a} == @k['{a}']" for a in k)).p50.iloc[0])  # noqa: E731
    ghi("lr E3→E3 N1 h=12 trước", "Bảng 5", 42.83, p50(d1[d1.metric == "mae"], dich="E3", mode="N1", h=12, model="lr"))
    ghi("lr E3→E3 N1 h=12 sau", "Bảng 5", 6.19, p50(q18[q18.metric == "mae"], nguon="E3", dich="E3", h=12, model="lr"))
    ghi("lr E3→E3 N0 h=12", "Bảng 5", 6.43, p50(d1[d1.metric == "mae"], dich="E3", mode="N0", h=12, model="lr"))
    g4 = pd.read_csv(T / "per_series_gd4.csv")
    g4 = g4[(g4.lich == "co")]
    nvE1 = g3[(g3.env == "E1") & (g3.h == 12) & (g3.model == "naive")].mae.median()
    truoc = g4[(g4.nguon == "E3") & (g4.dich == "E1") & (g4["mode"] == "N1") & (g4.h == 12) & (g4.model == "xgb")].mae.median()
    c18 = pd.read_csv(T / "qd018_n1_chuoi.csv")
    sau = c18[(c18.nguon == "E3") & (c18.dich == "E1") & (c18.h == 12) & (c18.model == "xgb")].mae.median()
    ghi("xgb E3→E1 N1 h=12 / naïve trước", "Bảng 5", 60.6, truoc / nvE1, 1)
    ghi("xgb E3→E1 N1 h=12 / naïve sau", "Bảng 5", 1.59, sau / nvE1)
    b17 = pd.read_csv(T / "qd017_t_d1b.csv")
    b18 = pd.read_csv(T / "qd018_t_d1b.csv")
    for d, tr, sa in (("E1", 2.77, 1.33), ("E2", 3.79, 1.23)):
        ghi(f"L E3→{d} N1 trước", "Bảng 5", tr, b17[(b17.nguon == "E3") & (b17.dich == d) & (b17["mode"] == "N1")].L_p50.median())
        ghi(f"L E3→{d} N1 sau", "Bảng 5", sa, b18[(b18.nguon == "E3") & (b18.dich == d) & (b18["mode"] == "N1")].L_p50.median())
    nv3 = g3[g3.model == "naive"].groupby(["env", "h"]).mae.median()
    n2loi = d1[(d1.metric == "mae") & (d1["mode"] == "N2") & (d1.dich == "E3")]
    for h, v in ((6, 1.00), (12, 1.01)):
        ghi(f"E3 N2 bản sai / naïve h={h}", "IV.D", v, n2loi[n2loi.h == h].p50.median() / nv3[("E3", h)])
    q19 = pd.read_csv(T / "qd019_n2.csv")
    n2d = q19[(q19.metric == "mae") & (q19.nguon == "E3") & (q19.dich == "E3")]
    khoang("E3 N2 bản đúng tốt hơn naïve (7 đến 13%)", "IV.D", 0.87, 0.93,
           [n2d[n2d.h == h].p50.median() / nv3[("E3", h)] for h in (6, 12)])
    khoang("Alibaba→Bitbrains N2 bản sai h=6, 12 (khoảng 1,10)", "IV.D", 1.08, 1.13,
           [b17[(b17.nguon == "E3") & (b17.dich == d) & (b17["mode"] == "N2") & (b17.h == h)].L_p50.median()
            for d in BIT for h in (6, 12)])
    ghi("Sai lệch lớn nhất của ba bất biến (×1e-14)", "III", 4.3,
        pd.read_csv(T / "invariants_gd4.csv").lech_toi_da.max() * 1e14, 1)

    # ---- hằng số mức tải của E1 áp cho E3 (Giới thiệu)
    from cwp.evaluation.splits import doc_b0, offset, split_masks
    e1 = pd.read_parquet(P / "E1.parquet", columns=["bucket", "y"])
    hs = e1[offset(e1.bucket, doc_b0("E1")) < 1612].y.mean()
    X = pd.read_parquet(ROOT / "data" / "features" / "E3_N0_h1.parquet", columns=["series_id", "bucket", "target"])
    te = X[split_masks(offset(X.bucket, doc_b0("E3")), 1)["test"]]
    ghi("MAE hằng số E1 áp cho E3", "Giới thiệu", 28.24,
        te.assign(e=(te.target - hs).abs()).groupby("series_id").e.mean().median())

    # ---- in
    lech = 0
    print(f"\n{'mục':58} {'ở đâu':16} {'bài báo':>10} {'tính lại':>12}  kết luận")
    for muc, cho, bai, that, nd in dong:
        khop = round(that, nd) == round(bai, nd) or abs(that - bai) <= 0.5 * 10 ** (-nd) + 1e-12
        lech += not khop
        print(f"{muc:58} {cho:16} {bai:>10} {that:>12.4f}  {'khớp' if khop else 'LỆCH'}")
    print(f"\n{len(dong)} con số, {lech} lệch.")
    return 1 if lech else 0


if __name__ == "__main__":
    sys.exit(main())
