"""GĐ4 Bước 5 — đọc ma trận transfer, kiểm định, và trả lời RQ3.

    python scripts/fig_gd4_transfer.py --all

Đọc hai bảng của Bước 4:

    results/tables/transfer_gd4.csv     số gộp, 6 cặp × 3 chế độ × 2 lịch × 3 h
    results/tables/per_series_gd4.csv   theo từng chuỗi, biến thể lịch = co

cộng `per_series_gd3.csv` cho baseline naive theo chuỗi (mốc cố định của đích, cùng
cửa sổ test — QĐ-016 điểm 4).

Sinh:

    results/tables/transfer_vs_naive_gd4.csv     họ Q1 — mỗi model ML so với naive tại đích
    results/tables/transfer_che_do_gd4.csv       họ Q2 — N1 và N2 so với N0
    results/tables/transfer_bat_doi_xung_gd4.csv họ Q3 — chiều xuôi so với chiều ngược
    results/tables/transfer_chi_phi_gd4.csv      cái giá của transfer so với train ngay trên đích
    results/tables/transfer_n2_vs_n1_hau_kiem_gd4.csv  HẬU KIỂM cho Bước 6, xem hàm cùng tên
    results/figures/gd4/                         9 panel .png + một .pdf gộp

Kiểm định — khai báo TRƯỚC khi nhìn kết quả
-------------------------------------------

Ba câu hỏi được khai trong log ngày 2026-09-13, trước khi tệp per-series tồn tại.

| Họ | Câu hỏi | Phép kiểm | Họ Holm |
|---|---|---|---|
| Q1 | model ML có vượt naive tại đích không | Wilcoxon ghép cặp theo chuỗi | mỗi `(nguồn, đích, h)`: 15 phép (5 model × 3 chế độ) |
| Q2 | N1, N2 có tốt hơn N0 không | Wilcoxon ghép cặp theo chuỗi | mỗi `(nguồn, đích, h)`: 10 phép (5 model × 2 so sánh) |
| Q3 | transfer có bất đối xứng không | **Mann–Whitney U** | một họ duy nhất |

**Hướng kết luận lấy từ đúng đại lượng được kiểm định.** Q1, Q2 dùng trung vị của
**hiệu ghép cặp** theo chuỗi — không phải hiệu hai trung vị. Ở GĐ3 hai đại lượng này
ngược dấu nhau ở 8 cặp, và lấy nhầm thì bảng khẳng định sai chiều.

**Q3 không ghép cặp được**, vì E1→E3 chấm trên chuỗi E3 còn E3→E1 chấm trên chuỗi E1 —
hai tập chuỗi khác nhau. Log ngày 2026-09-13 ghi "Wilcoxon" cho cả ba câu; ở Q3 đó là
cách nói lỏng, phép kiểm đúng là Mann–Whitney. Đại lượng so là **tỉ số MAE model / MAE
naive tại đích theo từng chuỗi**, loại chuỗi có MAE naive bằng 0. Hướng lấy từ hệ số
**rank-biserial** suy từ chính thống kê U, để hướng và p đến từ cùng một phép tính.

`alpha = 0,05`.
"""

from __future__ import annotations

import argparse
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

import matplotlib  # noqa: E402

matplotlib.use("Agg")
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from scipy.stats import mannwhitneyu, wilcoxon  # noqa: E402

from cwp.viz.xuat import MUC, MUC_PHU, Panel, xuat_bo_hinh  # noqa: E402

ML = ["lr", "ridge", "rf", "xgb", "svr"]
MODES = ["N0", "N1", "N2"]
HS = [1, 6, 12]
CAP = [("E1", "E2"), ("E2", "E1"), ("E1", "E3"),
       ("E3", "E1"), ("E2", "E3"), ("E3", "E2")]
DOI_XUNG = [(("E1", "E3"), ("E3", "E1")), (("E2", "E3"), ("E3", "E2")),
            (("E1", "E2"), ("E2", "E1"))]
ALPHA = 0.05

# Thang phân kỳ xanh <-> đỏ, xám trung tính ở giữa. Arm xanh lấy thẳng từ bậc 100–700
# của ramp tham chiếu; arm đỏ dựng khớp độ sáng OKLab từng bậc (lệch tối đa 0,009).
# Cả hai arm đơn điệu, điểm giữa sáng nhất. XANH = tốt hơn mốc, ĐỎ = tệ hơn mốc.
XANH = ["#0d366b", "#1c5cab", "#3987e5", "#86b6ef", "#cde2fb"]
DO = ["#6b0f0a", "#ad2418", "#e0493b", "#f2958b", "#fbd3ce"]
GIUA = "#f0efec"
CMAP = LinearSegmentedColormap.from_list("xanh_do", XANH + [GIUA] + DO[::-1])
TRAN_LOG2 = 3.0          # cắt màu ở 8 lần; con số thật vẫn in trong ô


def holm(p: np.ndarray) -> np.ndarray:
    """Holm–Bonferroni, giống hệt `fig_gd3_results.holm` để hai giai đoạn so được."""
    p = np.asarray(p, dtype="float64")
    n = len(p)
    out = np.empty(n)
    chay = 0.0
    for i, k in enumerate(np.argsort(p)):
        chay = max(chay, (n - i) * p[k])
        out[k] = min(chay, 1.0)
    return out


def ket_luan(co_y_nghia: bool, hieu: float, tot: str, te: str) -> str:
    if not co_y_nghia:
        return "không khác"
    return tot if hieu < 0 else te


# ------------------------------------------------------------------ nạp

def nap(tab: Path):
    t = pd.read_csv(tab / "transfer_gd4.csv")
    c = pd.read_csv(tab / "per_series_gd4.csv")
    b3 = pd.read_csv(tab / "per_series_gd3.csv")
    naive = b3[b3["model"] == "naive"][["env", "h", "series_id", "mae"]].rename(
        columns={"env": "dich", "mae": "mae_naive"})

    # Tự kiểm: trung vị naive theo chuỗi phải bằng đúng số gộp đã chép sang GĐ4.
    g = t[(t["model"] == "naive") & (t["metric"] == "mae")].groupby(["dich", "h"]).p50.first()
    for (d, h), v in g.items():
        m = float(naive[(naive["dich"] == d) & (naive["h"] == h)].mae_naive.median())
        if abs(m - v) > 1e-9:
            raise SystemExit(f"naive per-series lệch số gộp ở {d} h={h}: {m} ≠ {v}")
    return t, c, naive


# -------------------------------------------------------------- họ Q1

def q1_vs_naive(c: pd.DataFrame, naive: pd.DataFrame) -> pd.DataFrame:
    x = c.merge(naive, on=["dich", "h", "series_id"], how="inner")
    dong = []
    for (ng, di, md, h, m), g in x.groupby(["nguon", "dich", "mode", "h", "model"]):
        g = g[np.isfinite(g["mae"]) & np.isfinite(g["mae_naive"])]
        a, b = g["mae"].to_numpy(), g["mae_naive"].to_numpy()
        hieu = a - b
        _, p = (np.nan, 1.0) if np.allclose(hieu, 0) else wilcoxon(a, b)
        dong.append({
            "nguon": ng, "dich": di, "mode": md, "h": h, "model": m,
            "n_chuoi": len(g), "mae_p50": float(np.median(a)),
            "mae_p50_naive": float(np.median(b)),
            "ti_so_p50": float(np.median(a)) / float(np.median(b)),
            "hieu_p50": float(np.median(hieu)),          # trung vị CỦA HIỆU
            "n_tot_hon_naive": int((hieu < 0).sum()), "p": float(p),
        })
    out = pd.DataFrame(dong)
    out["p_holm"] = np.nan
    for _, idx in out.groupby(["nguon", "dich", "h"]).groups.items():
        out.loc[idx, "p_holm"] = holm(out.loc[idx, "p"].to_numpy())
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    out["ket_luan"] = [ket_luan(s, d, "tốt hơn naive", "tệ hơn naive")
                       for s, d in zip(out["co_y_nghia"], out["hieu_p50"])]
    return out


# -------------------------------------------------------------- họ Q2

def q2_che_do(c: pd.DataFrame) -> pd.DataFrame:
    w = c.pivot_table(index=["nguon", "dich", "h", "model", "series_id"],
                      columns="mode", values="mae").reset_index()
    dong = []
    for (ng, di, h, m), g in w.groupby(["nguon", "dich", "h", "model"]):
        for md in ("N1", "N2"):
            s = g[["N0", md]].dropna()
            a, b = s[md].to_numpy(), s["N0"].to_numpy()
            hieu = a - b
            _, p = (np.nan, 1.0) if np.allclose(hieu, 0) else wilcoxon(a, b)
            dong.append({
                "nguon": ng, "dich": di, "h": h, "model": m, "so_sanh": f"{md}_vs_N0",
                "n_chuoi": len(s), "mae_p50_N0": float(np.median(b)),
                "mae_p50_Nk": float(np.median(a)),
                "hieu_p50": float(np.median(hieu)),
                "n_tot_hon_N0": int((hieu < 0).sum()), "p": float(p),
            })
    out = pd.DataFrame(dong)
    out["p_holm"] = np.nan
    for _, idx in out.groupby(["nguon", "dich", "h"]).groups.items():
        out.loc[idx, "p_holm"] = holm(out.loc[idx, "p"].to_numpy())
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    out["ket_luan"] = [ket_luan(s, d, "tốt hơn N0", "tệ hơn N0")
                       for s, d in zip(out["co_y_nghia"], out["hieu_p50"])]
    return out


# -------------------------------------------------------------- họ Q3

def q3_bat_doi_xung(c: pd.DataFrame, naive: pd.DataFrame) -> pd.DataFrame:
    x = c.merge(naive, on=["dich", "h", "series_id"], how="inner")
    x = x[x["mae_naive"] > 0].copy()
    x["ti_so"] = x["mae"] / x["mae_naive"]
    dong = []
    for (xuoi, nguoc) in DOI_XUNG:
        for md in MODES:
            for h in HS:
                for m in ML:
                    def lay(cp):
                        return x[(x["nguon"] == cp[0]) & (x["dich"] == cp[1])
                                 & (x["mode"] == md) & (x["h"] == h)
                                 & (x["model"] == m)]["ti_so"].to_numpy()
                    a, b = lay(xuoi), lay(nguoc)
                    u, p = mannwhitneyu(a, b, alternative="two-sided")
                    # rank-biserial suy từ CHÍNH U: < 0 nghĩa là chiều xuôi có tỉ số nhỏ hơn
                    rb = 1.0 - 2.0 * u / (len(a) * len(b))
                    dong.append({
                        "xuoi": f"{xuoi[0]}->{xuoi[1]}", "nguoc": f"{nguoc[0]}->{nguoc[1]}",
                        "mode": md, "h": h, "model": m,
                        "n_xuoi": len(a), "n_nguoc": len(b),
                        "ti_so_p50_xuoi": float(np.median(a)),
                        "ti_so_p50_nguoc": float(np.median(b)),
                        "rank_biserial": float(-rb), "p": float(p),
                    })
    out = pd.DataFrame(dong)
    out["p_holm"] = holm(out["p"].to_numpy())
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    out["ket_luan"] = [
        "không khác" if not s else ("chiều xuôi dễ hơn" if r < 0 else "chiều ngược dễ hơn")
        for s, r in zip(out["co_y_nghia"], out["rank_biserial"])]
    return out


# ------------------------------------- HẬU KIỂM cho Bước 6 — không khai trước

def hau_kiem_n2_vs_n1(c: pd.DataFrame) -> pd.DataFrame:
    """N2 so với N1 — **HẬU KIỂM**, KHÔNG thuộc ba họ Q1–Q3 đã khai trước.

    Đặt ra ở Bước 6 (điều kiện kích hoạt QĐ-004): *"kết luận RQ3 có đảo chiều khi bỏ
    E3 không"*. Q2 chỉ so từng chế độ với N0, nên không trả lời được câu "N1 hay N2
    tốt hơn" — mà đó chính là câu hỏi *thành phần nào của tín hiệu transfer được*.

    Ghi nhãn hậu kiểm để người đọc cân p-value đúng mức: phép kiểm này được chọn **sau
    khi** đã nhìn bảng Q2. Cùng quy tắc với Q2 — Wilcoxon ghép cặp, Holm trong mỗi
    `(nguồn, đích, h)`, hướng từ trung vị của hiệu.
    """
    w = c.pivot_table(index=["nguon", "dich", "h", "model", "series_id"],
                      columns="mode", values="mae").reset_index()
    dong = []
    for (ng, di, h, m), g in w.groupby(["nguon", "dich", "h", "model"]):
        s = g[["N1", "N2"]].dropna()
        hieu = (s["N2"] - s["N1"]).to_numpy()
        _, p = (np.nan, 1.0) if np.allclose(hieu, 0) else wilcoxon(s["N2"], s["N1"])
        dong.append({"nguon": ng, "dich": di, "h": h, "model": m, "n_chuoi": len(s),
                     "hieu_p50_N2_tru_N1": float(np.median(hieu)), "p": float(p)})
    out = pd.DataFrame(dong)
    out["p_holm"] = np.nan
    for _, idx in out.groupby(["nguon", "dich", "h"]).groups.items():
        out.loc[idx, "p_holm"] = holm(out.loc[idx, "p"].to_numpy())
    out["co_y_nghia"] = out["p_holm"] < ALPHA
    out["ket_luan"] = [ket_luan(s, d, "N2 tốt hơn N1", "N1 tốt hơn N2")
                       for s, d in zip(out["co_y_nghia"], out["hieu_p50_N2_tru_N1"])]
    bit = out["nguon"].isin(["E1", "E2"]) & out["dich"].isin(["E1", "E2"])
    out["nhom"] = np.where(bit, "chi Bitbrains",
                           np.where(out["nguon"] == "E3", "Alibaba->Bitbrains",
                                    "Bitbrains->Alibaba"))
    out["hau_kiem"] = True
    return out


# ------------------------------------------------------- cái giá transfer

def chi_phi_transfer(t: pd.DataFrame, tab: Path) -> pd.DataFrame:
    """MAE transfer / MAE của CÙNG model train ngay trên đích ở GĐ3.

    Vì sao cần bảng này ngoài Q1. GĐ3 cho thấy trên E1 và E2 **ngay cả model trong
    cùng môi trường cũng không vượt được naive** (0/15 và 2/15). Nên "transfer tệ hơn
    naive tại E1" không tách được lỗi của transfer khỏi độ khó cố hữu của E1. So với
    model trong cùng môi trường thì tách được: `1,00` là transfer không mất gì.

    **Giới hạn đọc:** GĐ3 chỉ chạy ở N0. Cột N0 vì thế là **cái giá thuần của
    transfer**; cột N1, N2 thì **trộn** cái giá transfer với hiệu ứng của chính phép
    chuẩn hoá, và không tách được nếu không có bản N1/N2 train ngay trên đích.
    """
    g3 = pd.read_csv(tab / "experiments_gd3.csv")
    trong = g3[(g3["metric"] == "mae") & (g3["split"] == "test")].set_index(
        ["env", "h", "model"])["p50"]
    m = t[(t["metric"] == "mae") & t["model"].isin(ML)].copy()
    m["mae_trong_moi_truong"] = [trong[(d, h, x)] for d, h, x in
                                 zip(m["dich"], m["h"], m["model"])]
    m["chi_phi"] = m["p50"] / m["mae_trong_moi_truong"]
    return m[["nguon", "dich", "mode", "lich", "h", "model", "p50",
              "mae_trong_moi_truong", "chi_phi"]].rename(columns={"p50": "mae_transfer"})


# ------------------------------------------------------------------ hình

def _nhan_cot():
    return [f"{md}\nh={h}" for md in MODES for h in HS]


def _o_chu(ax, M, fmt, nguong_toi):
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            if not np.isfinite(v):
                continue
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=7.4,
                    color="#ffffff" if abs(nguong_toi(v)) > 0.62 else MUC)


def _khung(ax, M, nhan_hang, nhan_cot, ngan_nhom=None):
    ax.set_xticks(range(M.shape[1]), nhan_cot, fontsize=7.6, color=MUC_PHU)
    ax.set_yticks(range(M.shape[0]), nhan_hang, fontsize=8.2, color=MUC)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if ngan_nhom:
        for x in ngan_nhom:
            ax.axvline(x, color="#fcfcfb", lw=3)


def panel_ti_so(t: pd.DataFrame, model: str | None):
    """Tỉ số MAE / naive tại đích, lịch = co. `model=None` là trung vị qua 5 model."""
    mae = t[(t["metric"] == "mae") & (t["lich"] == "co")]
    naive = mae[mae["model"] == "naive"].groupby(["dich", "h"]).p50.first()

    def ve(ax):
        M = np.full((len(CAP), 9), np.nan)
        for i, (ng, di) in enumerate(CAP):
            for j, (md, h) in enumerate([(a, b) for a in MODES for b in HS]):
                s = mae[(mae["nguon"] == ng) & (mae["dich"] == di)
                        & (mae["mode"] == md) & (mae["h"] == h)]
                s = s[s["model"].isin(ML)] if model is None else s[s["model"] == model]
                if len(s):
                    M[i, j] = float(np.median(s["p50"])) / naive[(di, h)]
        L = np.log2(M)
        ax.imshow(np.clip(L, -TRAN_LOG2, TRAN_LOG2), cmap=CMAP, aspect="auto",
                  norm=TwoSlopeNorm(vmin=-TRAN_LOG2, vcenter=0, vmax=TRAN_LOG2))
        _o_chu(ax, M, lambda v: f"{v:.2f}" if v < 10 else f"{v:.0f}",
               lambda v: np.clip(np.log2(v), -3, 3) / 3)
        _khung(ax, M, [f"{a}→{b}" for a, b in CAP], _nhan_cot(), [2.5, 5.5])
    return ve


def panel_dem(bang: pd.DataFrame, cot_hang, cot_cot, gia_tri_cot, nhan_cot):
    """Ô = (số model tốt hơn có ý nghĩa) − (số model tệ hơn có ý nghĩa), dải [−5, 5]."""
    def ve(ax):
        M = np.zeros((len(CAP), len(gia_tri_cot)))
        for i, (ng, di) in enumerate(CAP):
            for j, cv in enumerate(gia_tri_cot):
                s = bang[(bang["nguon"] == ng) & (bang["dich"] == di) & cot_cot(bang, cv)]
                tot = int((s["co_y_nghia"] & (s["hieu_p50"] < 0)).sum())
                te = int((s["co_y_nghia"] & (s["hieu_p50"] > 0)).sum())
                M[i, j] = tot - te
        bien = np.arange(-5.5, 6.5, 1.0)
        # Đảo dấu để XANH = tốt hơn mốc, giống các panel tỉ số.
        ax.imshow(-M, cmap=CMAP, aspect="auto", norm=BoundaryNorm(bien, CMAP.N))
        _o_chu(ax, M, lambda v: f"{v:+.0f}" if v else "0", lambda v: v / 5)
        _khung(ax, M, [f"{a}→{b}" for a, b in CAP], nhan_cot,
               [2.5, 5.5] if len(gia_tri_cot) == 9 else None)
    return ve


# ----------------------------------------------------------------- chạy

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--figures", default="results/figures/gd4")
    a = ap.parse_args()
    tab, fig_dir = ROOT / a.tables, ROOT / a.figures
    fig_dir.mkdir(parents=True, exist_ok=True)

    t, c, naive = nap(tab)
    q1 = q1_vs_naive(c, naive)
    q2 = q2_che_do(c)
    q3 = q3_bat_doi_xung(c, naive)
    q1.to_csv(tab / "transfer_vs_naive_gd4.csv", index=False)
    q2.to_csv(tab / "transfer_che_do_gd4.csv", index=False)
    q3.to_csv(tab / "transfer_bat_doi_xung_gd4.csv", index=False)
    cp = chi_phi_transfer(t, tab)
    cp.to_csv(tab / "transfer_chi_phi_gd4.csv", index=False)
    hk = hau_kiem_n2_vs_n1(c)
    hk.to_csv(tab / "transfer_n2_vs_n1_hau_kiem_gd4.csv", index=False)

    print("\nGĐ4 Bước 5 — kiểm định transfer (lịch = co)\n")
    for ten, b in (("Q1 model ML so với naive tại đích", q1),
                   ("Q2 N1/N2 so với N0", q2), ("Q3 chiều xuôi so với chiều ngược", q3)):
        print(f"{ten}: {len(b)} phép kiểm")
        print("   " + b["ket_luan"].value_counts().to_string().replace("\n", "\n   "))

    panels = [Panel("01_ti-so-voi-naive-trung-vi-5-model",
                    "MAE transfer chia cho MAE naive tại đích — trung vị qua 5 model ML",
                    (7.6, 4.6), panel_ti_so(t, None))]
    for i, m in enumerate(ML, start=2):
        panels.append(Panel(f"{i:02d}_ti-so-voi-naive-{m}",
                            f"MAE transfer chia cho MAE naive tại đích — {m}",
                            (7.6, 4.6), panel_ti_so(t, m)))
    panels.append(Panel(
        "07_kiem-dinh-ml-vs-naive",
        "Số model tốt hơn naive trừ số model tệ hơn naive (Wilcoxon + Holm)",
        (7.6, 4.6),
        panel_dem(q1, None, lambda b, cv: (b["mode"] == cv[0]) & (b["h"] == cv[1]),
                  [(md, h) for md in MODES for h in HS], _nhan_cot())))
    for k, md in ((8, "N1"), (9, "N2")):
        panels.append(Panel(
            f"{k:02d}_kiem-dinh-{md.lower()}-vs-n0",
            f"Số model {md} tốt hơn N0 trừ số model tệ hơn N0 (Wilcoxon + Holm)",
            (5.2, 4.6),
            panel_dem(q2, None,
                      lambda b, cv, md=md: (b["so_sanh"] == f"{md}_vs_N0") & (b["h"] == cv),
                      HS, [f"h={h}" for h in HS])))

    anh, pdf = xuat_bo_hinh(
        panels, fig_dir, "gd4_transfer.pdf",
        tieu_de="GĐ4 — Thí nghiệm B, transfer xuyên môi trường",
        phu="Biến thể lịch = co. Xanh: tốt hơn mốc. Đỏ: tệ hơn mốc. Xám: ngang mốc.",
        dien_giai=[
            ("Đọc panel 01–06", "Ô là MAE của model transfer chia MAE của naive trên chính "
             "môi trường đích. Dưới 1 là transfer thắng một mốc không cần học gì. Màu cắt "
             "ở 8 lần; con số trong ô là giá trị thật."),
            ("Đọc panel 07–09", "Ô là số model tốt hơn mốc có ý nghĩa trừ số model tệ hơn "
             "có ý nghĩa, dải −5 tới +5. Hướng lấy từ trung vị của hiệu ghép cặp theo chuỗi."),
        ],
    )
    print("\nCái giá transfer (lịch = co), trung vị qua 5 model — 1,00 là không mất gì:")
    tom = (cp[cp["lich"] == "co"].groupby(["nguon", "dich", "mode"])["chi_phi"]
           .median().unstack("mode").round(2))
    print("   " + tom.to_string().replace("\n", "\n   "))
    print("\nHẬU KIỂM (Bước 6, không khai trước) — N2 so với N1:")
    print("   " + hk.groupby("nhom")["ket_luan"].value_counts().unstack(fill_value=0)
          .to_string().replace("\n", "\n   "))
    print(f"\nĐã ghi 5 bảng vào {tab.relative_to(ROOT)}")
    print(f"Đã ghi {len(anh)} hình và {pdf.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
