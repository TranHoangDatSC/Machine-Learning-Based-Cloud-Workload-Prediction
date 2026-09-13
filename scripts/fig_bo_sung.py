"""Hình bổ sung dạng quen thuộc: histogram, boxplot, heatmap có ghi số, phân cụm k-means.

    python scripts/fig_bo_sung.py              # vẽ hết
    python scripts/fig_bo_sung.py --phan gd3   # chỉ một phần: gd2 | gd3 | gd4 | cum

Không thêm kết quả mới nào. Mọi con số lấy từ bảng đã có của GĐ2–GĐ4 và QĐ-017, QĐ-018;
hình chỉ trình bày lại chúng bằng dạng hình quen thuộc hơn ECDF và heatmap tỉ số log.
Riêng phần **phân cụm là mô tả**: không khai trước, không phải kiểm định, không dùng
làm bằng chứng cho kết luận nào.

Ra `results/figures/bo_sung/` — mỗi hình một `.png`, cộng `bo-sung_hinh-quen-thuoc.pdf`
có trang hướng dẫn đọc. Bảng phụ của phân cụm: `results/tables/bo_sung_cum.csv`.

Màu (skill dataviz, đã chạy validator):

- ba môi trường: xanh `#2a78d6`, cam `#eb6834`, xanh ngọc `#1baf7a` — ba slot đầu của bảng
  tham chiếu, qua kiểm tra **mọi cặp** (CVD ΔE 9,2). Xanh ngọc dưới 3:1 so với nền nên
  hình nào dùng nó cũng có chú giải chữ.
- horizon và chế độ chuẩn hoá (có thứ tự): một hue xanh, sáng → đậm, qua kiểm `--ordinal`.
- heatmap tỉ số: xanh ↔ xám ↔ đỏ, trục log2, tâm ở 1 — dưới 1 là tốt hơn mốc.
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
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from cwp.viz.xuat import MUC, MUC_PHU, NEN, Panel, chu_giai_duoi, xuat_bo_hinh  # noqa: E402

TAB = ROOT / "results" / "tables"
PROC = ROOT / "data" / "processed"
RA = ROOT / "results" / "figures" / "bo_sung"

ENVS = ["E1", "E2", "E3"]
TEN_ENV = {"E1": "E1 Bitbrains fastStorage", "E2": "E2 Bitbrains Rnd",
           "E3": "E3 Alibaba (máy vật lý)"}
MAU_ENV = {"E1": "#2a78d6", "E2": "#eb6834", "E3": "#1baf7a"}
THU_TU = ["#86b6ef", "#2a78d6", "#104281"]          # ordinal: sáng → đậm
MO = "#898781"
LUOI = "#e1e0d9"
TRUC = "#c3c2b7"
XAM_NEN = "#d6d5cf"
XANH = ["#0d366b", "#1c5cab", "#3987e5", "#86b6ef", "#cde2fb"]
DO = ["#6b0f0a", "#ad2418", "#e0493b", "#f2958b", "#fbd3ce"]
CMAP = LinearSegmentedColormap.from_list("xanh_do", XANH + ["#f0efec"] + DO[::-1])
ML = ["lr", "ridge", "rf", "xgb", "svr"]
HS = [1, 6, 12]
TEN_H = {1: "h = 1 (5 phút)", 6: "h = 6 (30 phút)", 12: "h = 12 (1 giờ)"}


def khung(ax, xlabel="", ylabel="", luoi_y=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(TRUC)
    ax.tick_params(colors=MUC_PHU, labelsize=8.5, length=3, color=TRUC)
    ax.set_xlabel(xlabel, fontsize=9, color=MUC_PHU)
    ax.set_ylabel(ylabel, fontsize=9, color=MUC_PHU)
    if luoi_y:
        ax.grid(axis="y", color=LUOI, linewidth=0.6)
        ax.set_axisbelow(True)


def truc_ti_so(ax, lo, hi):
    """Trục log cho tỉ số, vạch ở các mốc đọc được thay vì 10^x."""
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    moc = [v for v in (0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10, 20, 30, 50) if lo <= v <= hi]
    ax.set_yticks(moc)
    ax.set_yticklabels([f"{v:g}".replace(".", ",") for v in moc])
    ax.minorticks_off()
    ax.axhline(1.0, color=MUC_PHU, linewidth=1.0, linestyle=(0, (4, 3)), zorder=2)


def gioi_han_truc(mang: list[np.ndarray]) -> tuple[float, float]:
    """Trục log vừa đủ chứa râu p5–p95 của mọi hộp. Cố định một khoảng cho mọi môi
    trường làm hộp `lr` của E1 bị cắt ở bản đầu."""
    v = [a for a in mang if len(a)]
    lo = min(float(np.percentile(a, 5)) for a in v) / 1.05
    hi = max(float(np.percentile(a, 95)) for a in v) * 1.05
    return (max([m for m in (0.1, 0.25, 0.5, 0.75) if m <= lo], default=0.1),
            min([m for m in (1.5, 2, 3, 5, 10, 20, 30, 50) if m >= hi], default=50))


def so_vn(v, nd=2):
    return f"{v:.{nd}f}".replace(".", ",")


# ================================================================ GĐ2

def panels_gd2() -> tuple[list[Panel], dict]:
    y = {e: pd.read_parquet(PROC / f"{e}.parquet", columns=["y"])["y"].dropna().to_numpy()
         for e in ENVS}
    cv = pd.read_csv(TAB / "cv_gd2.csv")
    bins = np.arange(0, 102, 2)
    ps, cap = [], {}

    for i, e in enumerate(ENVS, start=1):
        def ve(ax, e=e):
            w = np.full(len(y[e]), 100.0 / len(y[e]))
            ax.hist(y[e], bins=bins, weights=w, color=MAU_ENV[e], edgecolor=NEN,
                    linewidth=0.6)
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 100)
            tv = float(np.median(y[e]))
            ax.axvline(tv, color=MUC, linewidth=1.0, linestyle=(0, (4, 3)))
            ax.text(tv + 1.5, 92, f"trung vị {so_vn(tv)}%", fontsize=8.5, color=MUC)
            khung(ax, "CPU (%) — mỗi cột rộng 2 điểm phần trăm", "% số điểm dữ liệu")
        ten = f"B0{i}_histogram-cpu-{e}"
        ps.append(Panel(ten, f"Phân phối CPU% sau tiền xử lý — {TEN_ENV[e]}", (7.2, 4.0), ve))
        cap[ten] = ("Histogram mọi điểm 5 phút của mọi chuỗi trong cửa sổ 8 ngày. Trục tung cố "
                    "định 0–100% ở cả ba hình để so trực tiếp. Bitbrains dồn gần hết vào vài cột "
                    "đầu, Alibaba trải rộng hơn: đó là lệch mức tải mà QĐ-005 và chế độ N1 xử lý. "
                    "Cột cuối 98–100% là trần 100 của thang đo (QĐ-011), không phải lỗi vẽ.")

    def ve_cv(ax):
        b = np.logspace(-2, 1.3, 40)
        for e in ENVS:
            v = cv.loc[cv["env"] == e, "cv"].dropna()
            v = v[v > 0]
            ax.hist(v, bins=b, weights=np.full(len(v), 100.0 / len(v)), histtype="step",
                    linewidth=2.0, color=MAU_ENV[e], label=TEN_ENV[e])
        ax.set_xscale("log")
        ax.set_xticks([0.01, 0.1, 1, 10])
        ax.set_xticklabels(["0,01", "0,1", "1", "10"])
        khung(ax, "CV = độ lệch chuẩn / trung bình của mỗi chuỗi (trục log)", "% số chuỗi")
        chu_giai_duoi(ax, ncol=3)
    ps.append(Panel("B04_histogram-cv", "Hệ số biến thiên CV của từng chuỗi, theo môi trường",
                    (7.2, 4.2), ve_cv))
    cap["B04_histogram-cv"] = ("Mỗi chuỗi đóng góp một giá trị CV. Cùng dữ liệu với hình ECDF "
                               "08 của GĐ2, vẽ lại dạng histogram. CV cao nghĩa là chuỗi giật "
                               "mạnh so với mức tải trung bình của nó.")
    return ps, cap


# ================================================================ GĐ3

def panels_gd3() -> tuple[list[Panel], dict]:
    p = pd.read_csv(TAB / "per_series_gd3.csv")
    nv = p[p["model"] == "naive"][["env", "h", "series_id", "mae"]].rename(columns={"mae": "nv"})
    x = p[p["model"] != "naive"].merge(nv, on=["env", "h", "series_id"])
    x = x[(x["nv"] > 0) & np.isfinite(x["mae"])]
    x["ts"] = x["mae"] / x["nv"]
    mods = ["ma6", "seasonal"] + ML
    ps, cap = [], {}

    for i, e in enumerate(ENVS, start=5):
        def ve(ax, e=e):
            rong = 0.26
            tat_ca = []
            for j, h in enumerate(HS):
                data = [x[(x.env == e) & (x.h == h) & (x.model == m)]["ts"].to_numpy() for m in mods]
                tat_ca += data
                vt = np.arange(len(mods)) + (j - 1) * rong
                bp = ax.boxplot(data, positions=vt, widths=rong * 0.86, patch_artist=True,
                                showfliers=False, whis=(5, 95), medianprops=dict(color=MUC, linewidth=1.2),
                                whiskerprops=dict(color=MO, linewidth=0.9),
                                capprops=dict(color=MO, linewidth=0.9))
                for b in bp["boxes"]:
                    b.set(facecolor=THU_TU[j], edgecolor=NEN, linewidth=0.8)
            ax.set_xticks(np.arange(len(mods)))
            ax.set_xticklabels(mods)
            ax.axvline(1.5, color=LUOI, linewidth=1.0)
            truc_ti_so(ax, *gioi_han_truc(tat_ca))
            khung(ax, "baseline (trái vạch) · model ML (phải vạch)", "MAE model / MAE naive (log)")
            ax.legend(handles=[Patch(facecolor=THU_TU[j], label=TEN_H[h]) for j, h in enumerate(HS)],
                      loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False,
                      fontsize=8.2, labelcolor=MUC_PHU)
        ten = f"B0{i}_boxplot-ti-so-naive-{e}"
        ps.append(Panel(ten, f"Tỉ số MAE so với naive theo từng chuỗi — {TEN_ENV[e]}", (8.2, 4.4), ve))
        cap[ten] = ("Mỗi hộp là phân phối theo chuỗi của MAE model chia MAE naive trên cùng chuỗi, "
                    "tập test. Vạch đậm giữa hộp là trung vị; hộp là p25–p75; râu là p5–p95; "
                    "không vẽ điểm ngoại lai. Đường đứt ở 1: dưới đường là tốt hơn naive.")

    def ve_hm(ax):
        cot = [(e, h) for e in ENVS for h in HS]
        M = np.array([[float(np.median(x[(x.env == e) & (x.h == h) & (x.model == m)]["ts"]))
                       for e, h in cot] for m in mods])
        _heatmap(ax, M, mods, [f"{e}\nh={h}" for e, h in cot], tran=1.0)
        for k in (3, 6):
            ax.axvline(k - 0.5, color=NEN, linewidth=3)
        ax.axhline(1.5, color=NEN, linewidth=3)
    ps.append(Panel("B08_heatmap-ti-so-naive", "Trung vị tỉ số MAE / naive — model × môi trường × horizon",
                    (8.2, 4.6), ve_hm))
    cap["B08_heatmap-ti-so-naive"] = ("Mỗi ô là trung vị của tỉ số theo chuỗi — đúng vạch giữa hộp "
                                      "ở ba hình boxplot trước. Xanh: tốt hơn naive; đỏ: tệ hơn; xám: "
                                      "ngang. Màu cắt ở 0,5 và 2, số ghi trong ô là số thật. Kiểm "
                                      "định Wilcoxon nằm ở wilcoxon_gd3.csv, hình này không thay nó.")
    return ps, cap


def _heatmap(ax, M, hang, cot, tran=2.0, nd=2):
    L = np.log2(np.clip(M, 2.0 ** -tran, 2.0 ** tran))
    ax.imshow(L, cmap=CMAP, norm=TwoSlopeNorm(0, -tran, tran), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            sang = abs(L[i, j]) < 0.55 * tran
            ax.text(j, i, so_vn(M[i, j], nd), ha="center", va="center", fontsize=8.5,
                    color=MUC if sang else "#ffffff")
    ax.set_xticks(range(len(cot)))
    ax.set_xticklabels(cot, fontsize=8.5, color=MUC_PHU)
    ax.set_yticks(range(len(hang)))
    ax.set_yticklabels(hang, fontsize=8.5, color=MUC_PHU)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)


# ================================================================ GĐ4

def bang_L_cuoi() -> tuple[pd.DataFrame, pd.DataFrame]:
    """`L` theo chuỗi cho 6 cặp × 3 chế độ; N1 là bản độ nhạy QĐ-018 (QĐ-018 điểm 4)."""
    import phan_tich_qd017 as pt
    import phan_tich_qd018 as pq
    g4 = pd.read_csv(TAB / "per_series_gd4.csv")
    g4 = g4[g4["lich"] == "co"]
    d1 = pd.read_csv(TAB / "qd017_d1_chuoi.csv").query("nguon == dich")
    moi = pd.read_csv(TAB / "qd018_n1_chuoi.csv")
    m_cheo, m_chuyen, _ = pq.tach_moi(moi)
    L = pt.ghep_L(pq.thay_n1(g4, m_chuyen), pq.thay_n1(d1, m_cheo))
    b = pd.concat([pd.read_csv(TAB / "qd017_t_d1b.csv").query("mode != 'N1'"),
                   pd.read_csv(TAB / "qd018_t_d1b.csv").query("mode == 'N1'")])
    return L, b


CAP_THU_TU = [("E1", "E2"), ("E2", "E1"), ("E1", "E3"), ("E2", "E3"), ("E3", "E1"), ("E3", "E2")]


def panels_gd4() -> tuple[list[Panel], dict]:
    L, b = bang_L_cuoi()
    ps, cap = [], {}

    def ve_hm(ax):
        M = np.array([[float(b[(b.nguon == n) & (b.dich == d) & (b["mode"] == md)]["L_p50"].median())
                       for md in ("N0", "N1", "N2")] for n, d in CAP_THU_TU])
        _heatmap(ax, M, [f"{n} → {d}" for n, d in CAP_THU_TU],
                 ["N0 — CPU% thô", "N1 — z-score", "N2 — sai phân"], tran=2.0, nd=3)
        ax.axhline(1.5, color=NEN, linewidth=3)
    ps.append(Panel("B09_heatmap-mat-mat-transfer", "Mất mát do transfer L — cặp môi trường × chế độ chuẩn hoá",
                    (6.4, 4.4), ve_hm))
    cap["B09_heatmap-mat-mat-transfer"] = (
        "L = MAE khi train ở nguồn rồi dự đoán đích, chia MAE của cùng model train ngay trên đích, "
        "cùng chế độ. L = 1: transfer không mất gì; 1,3: tệ hơn 30%. Mỗi ô là trung vị qua 5 model "
        "× 3 horizon — đúng bảng gate-gd4.md mục 5.4. Hai hàng trên (E1 ↔ E2) là kết quả chính; "
        "bốn hàng dưới là phân tích bổ sung. Cột N1 là bản độ nhạy QĐ-018.")

    s = (L.groupby(["nguon", "dich", "mode", "series_id"])["L"].median().reset_index())

    def ve_box(ax):
        rong = 0.26
        for j, md in enumerate(("N0", "N1", "N2")):
            data = [s[(s.nguon == n) & (s.dich == d) & (s["mode"] == md)]["L"].dropna().to_numpy()
                    for n, d in CAP_THU_TU]
            vt = np.arange(len(CAP_THU_TU)) + (j - 1) * rong
            bp = ax.boxplot(data, positions=vt, widths=rong * 0.86, patch_artist=True,
                            showfliers=False, whis=(5, 95), medianprops=dict(color=MUC, linewidth=1.2),
                            whiskerprops=dict(color=MO, linewidth=0.9), capprops=dict(color=MO, linewidth=0.9))
            for bx in bp["boxes"]:
                bx.set(facecolor=THU_TU[j], edgecolor=NEN, linewidth=0.8)
        ax.set_xticks(range(len(CAP_THU_TU)))
        ax.set_xticklabels([f"{n}→{d}" for n, d in CAP_THU_TU])
        ax.axvline(1.5, color=LUOI, linewidth=1.0)
        truc_ti_so(ax, 0.5, 10)
        khung(ax, "chính (trái vạch) · bổ sung (phải vạch)", "L theo chuỗi (log)")
        ax.legend(handles=[Patch(facecolor=THU_TU[j], label=t) for j, t in
                           enumerate(["N0 — CPU% thô", "N1 — z-score", "N2 — sai phân"])],
                  loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False,
                  fontsize=8.2, labelcolor=MUC_PHU)
    ps.append(Panel("B10_boxplot-mat-mat-transfer", "Phân phối L theo chuỗi — cặp môi trường × chế độ",
                    (8.2, 4.4), ve_box))
    cap["B10_boxplot-mat-mat-transfer"] = (
        "Mỗi chuỗi đích một giá trị: trung vị L của chuỗi đó qua 5 model × 3 horizon. Hộp p25–p75, "
        "râu p5–p95, không vẽ ngoại lai. Hình cho thấy độ phân tán mà bảng trung vị ở B09 che đi. "
        "Kiểm định nằm ở qd017_t_d1b.csv, qd018_t_d1b.csv.")
    return ps, cap


# ============================================================ phân cụm

def dac_trung_mo_ta(env: str) -> pd.DataFrame:
    """Bốn đại lượng mô tả mỗi chuỗi, **chỉ trên cửa sổ train** `[0, 1612)`."""
    d = (pd.read_parquet(PROC / f"{env}.parquet", columns=["series_id", "bucket", "y"])
         .sort_values(["series_id", "bucket"]))
    ids = d["series_id"].drop_duplicates().to_numpy()
    Y = d["y"].to_numpy("float64").reshape(len(ids), 2304)[:, :1612]
    mu = np.nanmean(Y, axis=1)
    sd = np.nanstd(Y, axis=1, ddof=1)
    D = Y - mu[:, None]

    def acf(k):
        a, c = D[:, :-k], D[:, k:]
        ok = np.isfinite(a) & np.isfinite(c)
        tu = np.where(ok, a * c, 0).sum(axis=1)
        mau = np.where(np.isfinite(D), D ** 2, 0).sum(axis=1)
        return tu / np.where(mau > 0, mau, np.nan)

    return pd.DataFrame({"env": env, "series_id": ids, "log_muc_tai": np.log10(mu + 0.01),
                         "log_cv": np.log10(np.clip(sd / np.maximum(mu, 1e-3), 1e-3, None)),
                         "acf_lag1": acf(1), "acf_lag288": acf(288)})


COT_CUM = ["log_muc_tai", "log_cv", "acf_lag1", "acf_lag288"]


def panels_cum() -> tuple[list[Panel], dict]:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    goc = pd.concat([dac_trung_mo_ta(e) for e in ENVS], ignore_index=True).dropna(subset=COT_CUM)
    gia = dac_trung_mo_ta("E1g").dropna(subset=COT_CUM)
    sc = StandardScaler().fit(goc[COT_CUM])
    Z = sc.transform(goc[COT_CUM])
    km = KMeans(n_clusters=3, n_init=20, random_state=42).fit(Z)
    pca = PCA(n_components=2, random_state=42).fit(Z)
    goc[["pc1", "pc2"]] = pca.transform(Z)
    goc["cum"] = km.labels_
    Zg = sc.transform(gia[COT_CUM])
    gia[["pc1", "pc2"]] = pca.transform(Zg)
    gia["cum"] = km.predict(Zg)
    # Tên trơn. Bản đầu gắn "đa số E1" cho hai cụm khác nhau vì E1 và E2 chia nhau cùng
    # các cụm — nhãn đó gợi ý sai rằng hai cụm là cùng một thứ.
    ten_cum = {c: f"cụm {c + 1}" for c in range(3)}
    pd.concat([goc, gia], ignore_index=True).to_csv(TAB / "bo_sung_cum.csv", index=False)
    ev = pca.explained_variance_ratio_
    ps, cap = [], {}

    def ve_env(ax):
        for e in ENVS:
            g = goc[goc.env == e]
            ax.scatter(g.pc1, g.pc2, s=14, color=MAU_ENV[e], alpha=0.6, edgecolors=NEN,
                       linewidths=0.3, label=TEN_ENV[e])
        khung(ax, f"thành phần chính 1 ({so_vn(100 * ev[0], 0)}% phương sai)",
              f"thành phần chính 2 ({so_vn(100 * ev[1], 0)}%)", luoi_y=False)
        chu_giai_duoi(ax, ncol=3)
    ps.append(Panel("B11_pca-theo-moi-truong", "Bản đồ chuỗi theo 4 đặc trưng mô tả — tô màu theo môi trường",
                    (7.2, 5.0), ve_env))
    cap["B11_pca-theo-moi-truong"] = (
        "Mỗi điểm là một chuỗi. Bốn đặc trưng tính trên cửa sổ train: log mức tải, log CV, ACF lag 1, "
        "ACF lag 288 (một ngày). Chuẩn hoá rồi chiếu PCA xuống 2 chiều chỉ để nhìn. Mô tả, không "
        "kiểm định.")

    def ve_bang(ax):
        ct = pd.crosstab(goc["cum"], goc["env"], normalize="columns").reindex(columns=ENVS) * 100
        M = ct.to_numpy()
        ax.imshow(M, cmap=LinearSegmentedColormap.from_list("xanh", ["#fcfcfb", "#cde2fb", "#3987e5", "#0d366b"]),
                  vmin=0, vmax=100, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, f"{so_vn(M[i, j], 1)}%", ha="center", va="center", fontsize=9,
                        color="#ffffff" if M[i, j] > 55 else MUC)
        ax.set_xticks(range(3))
        ax.set_xticklabels([TEN_ENV[e] for e in ENVS], fontsize=8.5, color=MUC_PHU)
        ax.set_yticks(range(3))
        ax.set_yticklabels([ten_cum[c] for c in ct.index], fontsize=8.5, color=MUC_PHU)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
    ps.append(Panel("B12_kmeans-bang-cheo", "k-means 3 cụm: mỗi môi trường rơi vào cụm nào (% số chuỗi)",
                    (6.8, 3.6), ve_bang))
    cap["B12_kmeans-bang-cheo"] = (
        "Mỗi cột cộng lại 100%. k = 3 chọn bằng số môi trường, không dò; n_init = 20, random_state = 42. "
        "Nếu mỗi môi trường gần như nằm trọn một cụm thì bốn đặc trưng mô tả đủ tách ba môi trường. "
        "Bảng số ở results/tables/bo_sung_cum.csv.")

    tl = gia["cum"].map(ten_cum).value_counts()

    def ve_gia(ax):
        ax.scatter(goc.pc1, goc.pc2, s=12, color=XAM_NEN, alpha=0.7, edgecolors="none",
                   label="E1, E2, E3 (nền)")
        # E1 và E2 có trung vị gần trùng nhau: một nhãn chung, không đè chữ.
        for nhan, nhom in (("E1 + E2", ["E1", "E2"]), ("E3", ["E3"])):
            g = goc[goc.env.isin(nhom)]
            ax.text(g.pc1.median(), g.pc2.median(), nhan, fontsize=10, color=MUC,
                    fontweight="bold", ha="center", va="center",
                    bbox=dict(facecolor=NEN, edgecolor="none", alpha=0.85, pad=1.5))
        ax.scatter(gia.pc1, gia.pc2, s=26, color=MUC, marker="D", edgecolors=NEN, linewidths=0.5,
                   label="E1g — máy giả, gộp 5 VM của E1")
        khung(ax, f"thành phần chính 1 ({so_vn(100 * ev[0], 0)}%)", f"thành phần chính 2 ({so_vn(100 * ev[1], 0)}%)",
              luoi_y=False)
        chu_giai_duoi(ax, ncol=2)
    ps.append(Panel("B13_pca-may-gia", "Máy giả E1g nằm ở đâu trên bản đồ chuỗi", (7.2, 5.0), ve_gia))
    cap["B13_pca-may-gia"] = (
        "Cùng bản đồ B11. Nhãn đặt ở trung vị của nhóm (E1 và E2 gần trùng nên chung một nhãn). E1g được chiếu bằng đúng "
        "phép chuẩn hoá và PCA học trên E1–E3, không học lại. Gán cụm của 73 máy giả: "
        + "; ".join(f"{k}: {v}" for k, v in tl.items()) + ". Mô tả, không kiểm định.")
    return ps, cap


# ==================================================================== chạy

PHAN = {"gd2": panels_gd2, "gd3": panels_gd3, "gd4": panels_gd4, "cum": panels_cum}

HUONG_DAN = [
    ("Histogram (B01–B04)", "Cột càng cao thì càng nhiều điểm dữ liệu rơi vào khoảng đó. Trục tung "
     "là phần trăm, nên ba môi trường có số chuỗi khác nhau vẫn so được."),
    ("Boxplot (B05–B07, B10)", "Mỗi hộp tóm tắt một phân phối: vạch giữa là trung vị, thân hộp chứa "
     "50% giá trị ở giữa (p25–p75), râu kéo tới p5 và p95. Trục tung là tỉ số trên thang log, nên "
     "0,5 và 2 cách đường 1 một khoảng bằng nhau: tốt gấp đôi và tệ gấp đôi trông cân xứng."),
    ("Heatmap (B08, B09, B12)", "Mỗi ô ghi số thật. Màu chỉ để mắt bắt nhanh: xanh là tốt hơn mốc 1, "
     "đỏ là tệ hơn, xám là ngang. Màu dừng ở một mức trần, còn số trong ô thì không."),
    ("Phân cụm (B11–B13)", "k-means gom các chuỗi giống nhau theo bốn đặc trưng mô tả. PCA chỉ để vẽ "
     "bốn chiều lên mặt phẳng. Phần này là mô tả, không khai trước, không dùng làm bằng chứng."),
    ("Hình này không thay gì", "Mọi kết luận của bài vẫn dựa trên kiểm định đã khai trong "
     "docs/decisions.md. Các hình ở đây trình bày lại cùng số liệu bằng dạng quen thuộc hơn."),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--phan", default="all", choices=["all", *PHAN])
    a = ap.parse_args()
    chon = list(PHAN) if a.phan == "all" else [a.phan]
    ps, cap = [], {}
    for k in chon:
        p, c = PHAN[k]()
        ps += p
        cap.update(c)
        print(f"{k}: {len(p)} hình")
    anh, pdf = xuat_bo_hinh(ps, RA, "bo-sung_hinh-quen-thuoc.pdf" if a.phan == "all"
                            else f"bo-sung_{a.phan}.pdf",
                            tieu_de="Hình bổ sung — dạng quen thuộc",
                            phu="Trình bày lại số liệu GĐ2–GĐ4 bằng histogram, boxplot, heatmap có "
                                "ghi số và phân cụm. Không có kết quả mới.",
                            dien_giai=HUONG_DAN, chu_thich=cap)
    print(f"Đã ghi {len(anh)} ảnh vào {RA.relative_to(ROOT)} và {pdf.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
