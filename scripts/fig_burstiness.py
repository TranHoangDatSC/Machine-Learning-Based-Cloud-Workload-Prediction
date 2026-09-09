"""Burstiness — hệ số biến thiên CV của từng chuỗi, ba môi trường (GĐ2 Bước 7).

    python scripts/fig_burstiness.py --env all

Sinh `results/figures/fig_burstiness.{png,pdf}`, `results/tables/cv_gd2.csv`
(một dòng mỗi chuỗi, dùng lại được để phân tầng ở GĐ3) và `cv_gd2_summary.csv`.

## Định nghĩa

`CV = std / mean` của từng chuỗi, tính trên **mọi điểm không NaN** trong cửa sổ 8
ngày, `ddof = 1` theo QĐ-010. Quy ước này khớp bản hiện thực độc lập của A đến bốn
chữ số thập phân ở cả 12 chỉ số (3 môi trường × p25/p50/p75/IQR).

Lưu ý một chỗ không đồng nhất trong dự án: `catalog.mean` và `catalog.std` tính
**chỉ trên điểm quan sát thật** (protocol mục 6b), còn CV ở đây tính trên **cả điểm
nội suy**. Chênh lệch nằm ở chữ số thập phân thứ tư vì tỉ lệ nội suy dưới 0,17%, và
quy ước của A là quy ước được chốt. Ghi ra để sau này không ai tưởng là lỗi.

## Vì sao trung vị và IQR, không phải trung bình

Bộ lọc `gan_chet` đã bỏ mọi chuỗi có mean dưới 1,0 nên CV không nổ. Nhưng một chuỗi
mean 1,01 vẫn kéo trung bình đi rất xa: đo được **trung bình CV cao hơn trung vị
+46% (E1), +76% (E2), +17% (E3)**. Báo cáo trung bình sẽ nói sai về môi trường nào
bursty hơn.

## Bốn panel

- (a) ECDF của CV, trục hoành log — phân phối đầy đủ, thấy được cả chồng lấn.
- (b) **CV so với mức tải trung bình của chuỗi.** Đây là phép kiểm quyết định cho
  câu hỏi phân tầng ở GĐ3: nếu CV chỉ là mức tải trá hình thì phân tầng theo CV
  chẳng khác gì phân tầng theo mức tải, và RQ3 mất khả năng quy trách nhiệm.
- (c) Trung vị và IQR — đúng thứ phiếu giao việc đòi báo cáo.
- (d) Bảng số.
"""

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]

NHAN = {
    "E1": "E1 — Bitbrains fastStorage (VM)",
    "E2": "E2 — Bitbrains Rnd 2013-8 (VM)",
    "E3": "E3 — Alibaba v2018 (máy vật lý)",
}
MAU = {"E1": "#2a78d6", "E2": "#eb6834", "E3": "#1baf7a"}
NET = {"E1": "-", "E2": "--", "E3": "-."}

MUC = "#0b0b0b"
MUC_PHU = "#52514e"
MUC_MO = "#8a8a85"
NEN = "#fcfcfb"


def do_cv(env: str, proc_dir: Path, cat: pd.DataFrame) -> pd.DataFrame:
    """Một dòng mỗi chuỗi: CV, mean, std, số điểm không NaN."""
    f = proc_dir / f"{env}.parquet"
    if not f.exists():
        raise SystemExit(f"Thiếu {f}. Chạy: python -m cwp.preprocess.build --env all")

    d = pd.read_parquet(f, columns=["series_id", "y"])
    giu = set(cat[(cat["env"] == env) & cat["kept"]]["series_id"])
    if set(d["series_id"].unique()) != giu:
        raise SystemExit(
            f"{env}: data/processed/ không khớp catalog.kept — sinh lại cả hai bằng "
            "một lệnh: python -m cwp.preprocess.build --env all"
        )

    g = d.groupby("series_id")["y"]
    out = pd.DataFrame({
        "env": env,
        "mean": g.mean(),
        "std": g.std(ddof=1),          # QĐ-010 chốt ddof = 1
        "n_diem": g.count(),
    }).reset_index()
    out["cv"] = out["std"] / out["mean"]

    # CPU% bị chặn trong [0, 100], nên một biến có trung bình m không thể có phương
    # sai vượt m(100 − m) — cực đại đạt được bởi phân phối hai điểm ở 0 và 100. Suy
    # ra CV <= sqrt((100 − m)/m). Đây là chặn của THANG ĐO, không phải của dữ liệu,
    # và nó siết rất chặt ở vùng tải cao: m = 40 thì CV không thể vượt 1,22.
    # So CV thô giữa các môi trường có mức tải lệch nhau 20 lần là so hai đại lượng
    # bị chặn khác nhau, nên phải kèm tỉ lệ chạm chặn.
    out["cv_chan"] = np.sqrt((100.0 - out["mean"]) / out["mean"])
    out["ti_le_cham_chan"] = out["cv"] / out["cv_chan"]
    return out


def tom_tat(cv: pd.DataFrame) -> dict:
    v = cv["cv"].dropna().to_numpy()
    q = np.percentile(v, [5, 25, 50, 75, 95])
    rho, p = spearmanr(cv["cv"], cv["mean"])
    return {
        "env": cv["env"].iloc[0],
        "n_chuoi": len(v),
        "cv_p5": q[0], "cv_p25": q[1], "cv_p50": q[2], "cv_p75": q[3], "cv_p95": q[4],
        "cv_iqr": q[3] - q[1],
        "cv_iqr_tren_p50": (q[3] - q[1]) / q[2],
        "cv_min": v.min(), "cv_max": v.max(),
        "cv_trung_binh": v.mean(),
        "tb_lech_p50_pct": 100.0 * (v.mean() / q[2] - 1.0),
        "spearman_cv_mean": rho,
        "spearman_p": p,
        "cham_chan_p50": float(cv["ti_le_cham_chan"].median()),
        "sat_chan_pct": 100.0 * float((cv["ti_le_cham_chan"] >= 0.8).mean()),
        "vi_pham_chan": int((cv["ti_le_cham_chan"] > 1.0001).sum()),
    }


def doi_chieu(tt: pd.DataFrame, ref_path: Path) -> int:
    if not ref_path.exists():
        print(f"\nCẢNH BÁO: thiếu {ref_path}, bỏ qua đối chiếu.")
        return 0
    ref = {r["env"]: r for r in pd.read_json(ref_path).to_dict("records")}

    print()
    print("─" * 70)
    print("ĐỐI CHIẾU với reference_gd2.json — bản hiện thực độc lập của A")
    print("─" * 70)
    print(f"{'':<4} {'chỉ số':<10} {'B':>10} {'A':>10} {'lệch':>10}")
    lech = 0
    for _, r in tt.iterrows():
        a = ref.get(r["env"], {})
        for k in ("cv_p25", "cv_p50", "cv_p75", "cv_iqr"):
            if k not in a:
                continue
            b = round(float(r[k]), 4)
            d = abs(b - a[k])
            xau = d > 5e-5
            lech += xau
            print(f"{r['env']:<4} {k:<10} {b:>10.4f} {a[k]:>10.4f} {d:>10.5f}"
                  f"{'  ← LỆCH' if xau else ''}")
    return lech


# ------------------------------------------------------------------- vẽ

def khung(ax, ten, tieu_de, *, xlabel, ylabel):
    ax.grid(True, color="#e6e5e0", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for c in ("top", "right"):
        ax.spines[c].set_visible(False)
    for c in ("left", "bottom"):
        ax.spines[c].set_color("#d4d3ce")
    ax.tick_params(colors=MUC_PHU, labelsize=8, length=3)
    ax.set_xlabel(xlabel, fontsize=9, color=MUC_PHU)
    ax.set_ylabel(ylabel, fontsize=9, color=MUC_PHU)
    ax.set_title(f"{ten}  {tieu_de}", fontsize=9.5, color=MUC, loc="left", pad=8)


def ve(cv: dict, tt: pd.DataFrame, out_dir: Path, dpi: int, *, kem_doc: bool) -> Path:
    """Dựng hình. `kem_doc=True` dùng tiêu đề diễn giải, để duyệt cổng và dán vào log.

    Bản paper (`kem_doc=False`) dùng tiêu đề **mô tả thuần**. Một panel đặt tên là
    "CV có phải mức tải trá hình?" là câu hỏi nghiên cứu, không phải nhãn trục; trong
    bài báo nó thuộc về caption và phần bàn luận.
    """
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(12.0, 8.4), facecolor=NEN)
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 0.85],
                  hspace=0.44, wspace=0.20,
                  left=0.065, right=0.985, top=0.862, bottom=0.075)
    ax_a = fig.add_subplot(gs[0, 0], facecolor=NEN)
    ax_b = fig.add_subplot(gs[0, 1], facecolor=NEN)
    ax_c = fig.add_subplot(gs[1, 0], facecolor=NEN)
    ax_d = fig.add_subplot(gs[1, 1], facecolor=NEN)
    s = tt.set_index("env")

    # (a) ECDF của CV
    for env in ENVS:
        v = np.sort(cv[env]["cv"].dropna().to_numpy())
        ax_a.step(v, np.arange(1, len(v) + 1) / len(v), where="post",
                  color=MAU[env], linestyle=NET[env], linewidth=1.8,
                  label=NHAN[env], zorder=3)
    ax_a.axhline(0.5, color=MUC_MO, linewidth=0.8, linestyle=":", zorder=1)
    ax_a.set_xscale("log")
    ax_a.set_xlim(0.03, 10)
    ax_a.set_ylim(-0.02, 1.02)
    ax_a.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax_a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    khung(ax_a, "(a)", ("ECDF của CV — trục log, thấy được cả chồng lấn" if kem_doc
                        else "ECDF của hệ số biến thiên CV (trục log)"),
          xlabel="CV = std / mean của chuỗi", ylabel="Tỉ lệ chuỗi tích luỹ")
    ax_a.text(0.034, 0.52, "trung vị", fontsize=7.5, color=MUC_MO, va="bottom")
    ax_a.legend(loc="lower right", fontsize=8.2, frameon=True, framealpha=1.0,
                edgecolor="#d4d3ce", facecolor=NEN, borderpad=0.6,
                labelcolor=MUC_PHU)

    # (b) CV so với mức tải — phép kiểm confound cho GĐ3
    for env in ENVS:
        c = cv[env]
        ax_b.scatter(c["mean"], c["cv"], s=7, color=MAU[env], alpha=0.42,
                     linewidths=0, zorder=3)
    # Chặn của thang đo, không phải của dữ liệu. Rìa chéo ở góc phải chính là nó.
    m = np.geomspace(1.0, 99.0, 400)
    ax_b.plot(m, np.sqrt((100.0 - m) / m), color=MUC, linewidth=1.1,
              linestyle=(0, (5, 2)), zorder=4)
    # Vùng phía TRÊN đường chặn rỗng theo định nghĩa, nên đặt chú thích ở đó thì
    # không đè lên điểm nào.
    ax_b.text(26, 4.2, "chặn CV = √((100−m)/m)\ndo thang đo 0–100,\nkhông phải do dữ liệu",
              fontsize=7.8, color=MUC, ha="left", va="center", linespacing=1.4,
              bbox=dict(boxstyle="round,pad=0.4", facecolor=NEN,
                        edgecolor="#d4d3ce", linewidth=0.7), zorder=5)
    ax_b.set_xscale("log")
    ax_b.set_yscale("log")
    khung(ax_b, "(b)", ("CV so với mức tải — CV có phải mức tải trá hình?" if kem_doc
                        else "CV so với CPU% trung bình của chuỗi"),
          xlabel="CPU% trung bình của chuỗi", ylabel="CV")
    for f in ("x", "y"):
        getattr(ax_b, f"{f}axis").set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
        getattr(ax_b, f"{f}axis").set_minor_formatter(matplotlib.ticker.NullFormatter())
    chu = "\n".join(
        f"{e}: Spearman ρ = {s.loc[e, 'spearman_cv_mean']:+.3f}" for e in ENVS)
    ax_b.text(0.02, 0.03, chu, transform=ax_b.transAxes, fontsize=8.2,
              color=MUC_PHU, va="bottom", ha="left",
              bbox=dict(boxstyle="round,pad=0.45", facecolor=NEN,
                        edgecolor="#d4d3ce", linewidth=0.7))

    # (c) trung vị và IQR — đúng thứ phiếu đòi báo cáo
    for i, env in enumerate(ENVS):
        y = len(ENVS) - 1 - i
        r = s.loc[env]
        ax_c.plot([r["cv_p5"], r["cv_p95"]], [y, y], color=MAU[env],
                  linewidth=1.2, alpha=0.55, zorder=2)
        ax_c.plot([r["cv_p25"], r["cv_p75"]], [y, y], color=MAU[env],
                  linewidth=9, solid_capstyle="butt", alpha=0.85, zorder=3)
        ax_c.plot([r["cv_p50"]], [y], marker="|", markersize=16,
                  markeredgewidth=2.4, color=NEN, zorder=4)
        ax_c.text(r["cv_p95"] * 1.12, y, f"  trung vị {r['cv_p50']:.3f}  ·  "
                  f"IQR {r['cv_iqr']:.3f}", fontsize=8.2, color=MUC_PHU,
                  va="center", ha="left")
    ax_c.set_yticks(range(len(ENVS)))
    ax_c.set_yticklabels(ENVS[::-1], fontsize=9)
    ax_c.set_ylim(-0.6, len(ENVS) - 0.4)
    ax_c.set_xscale("log")
    ax_c.set_xlim(0.05, 22)
    ax_c.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax_c.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    khung(ax_c, "(c)", "Trung vị và IQR — thanh đậm là p25–p75, vạch mảnh p5–p95",
          xlabel="CV (trục log)", ylabel="")

    # (d) bảng
    ax_d.axis("off")
    hang = [("n_chuoi", "Số chuỗi", "{:,.0f}"), ("cv_p25", "p25", "{:.4f}"),
            ("cv_p50", "Trung vị", "{:.4f}"), ("cv_p75", "p75", "{:.4f}"),
            ("cv_iqr", "IQR", "{:.4f}"),
            ("cv_iqr_tren_p50", "IQR / trung vị", "{:.2f}"),
            ("cv_trung_binh", "Trung bình", "{:.4f}"),
            ("tb_lech_p50_pct", "TB lệch trung vị %", "{:+.0f}"),
            ("cv_max", "Lớn nhất", "{:.2f}"),
            ("spearman_cv_mean", "ρ(CV, mức tải)", "{:+.3f}"),
            ("cham_chan_p50", "CV / chặn, trung vị", "{:.3f}"),
            ("sat_chan_pct", "% chuỗi sát chặn", "{:.1f}")]
    o = [[f.format(s.loc[e, k]) for e in ENVS] for k, _, f in hang]
    t = ax_d.table(cellText=o, rowLabels=[n for _, n, _ in hang], colLabels=ENVS,
                   cellLoc="right", rowLoc="right", loc="center",
                   colWidths=[0.2] * 3)
    t.auto_set_font_size(False)
    t.set_fontsize(8)
    t.scale(1, 1.36)
    nhan_manh = {"cv_p50", "cv_iqr", "spearman_cv_mean", "cham_chan_p50"}
    for (r, c), o_ in t.get_celld().items():
        o_.set_edgecolor("#e6e5e0")
        o_.set_linewidth(0.6)
        if r == 0:
            o_.set_facecolor("#f2f1ec")
            o_.get_text().set_color(MAU[ENVS[c]] if c >= 0 else MUC)
            o_.get_text().set_fontweight("bold")
        else:
            manh = hang[r - 1][0] in nhan_manh
            o_.get_text().set_color(MUC if manh else MUC_PHU)
            if manh:
                o_.get_text().set_fontweight("bold")
    ax_d.set_title("(d)  Bảng số", fontsize=9.5, color=MUC, loc="left", pad=12)

    fig.suptitle("Burstiness — hệ số biến thiên CV của từng chuỗi",
                 fontsize=13, color=MUC, x=0.065, ha="left", y=0.963)
    phu = ("CV = std / mean của chuỗi, ddof = 1, trên mọi điểm không NaN trong cửa "
           "sổ 8 ngày. Trung vị và IQR, không phải trung bình — xem dòng "
           "\"TB lệch trung vị\"." if kem_doc else
           "CV = std / mean của từng chuỗi (ddof = 1), tính trên mọi điểm quan sát "
           "trong cửa sổ 8 ngày, cho các chuỗi còn lại sau bộ lọc.")
    fig.text(0.065, 0.915, phu, fontsize=9, color=MUC_PHU, ha="left")

    ten = "fig_burstiness" if kem_doc else "fig_burstiness_paper"
    png = out_dir / f"{ten}.png"
    fig.savefig(png, dpi=dpi, facecolor=NEN)
    fig.savefig(out_dir / f"{ten}.pdf", facecolor=NEN)
    plt.close(fig)
    return png


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--out", default="results/figures")
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    out_dir, tab_dir = ROOT / a.out, ROOT / a.tables
    out_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)

    cat = pd.read_parquet(ROOT / a.catalog)
    cv = {e: do_cv(e, ROOT / a.processed, cat) for e in envs}
    tt = pd.DataFrame([tom_tat(cv[e]) for e in envs])

    hau_to = "" if a.env == "all" else f"_{a.env}"
    p_chuoi = tab_dir / f"cv_gd2{hau_to}.csv"
    p_tom = tab_dir / f"cv_gd2_summary{hau_to}.csv"
    pd.concat(cv.values(), ignore_index=True).round(6).to_csv(
        p_chuoi, index=False, encoding="utf-8")
    tt.round(6).to_csv(p_tom, index=False, encoding="utf-8")

    print()
    print("BURSTINESS — CV = std/mean từng chuỗi (ddof = 1, QĐ-010)")
    print()
    s = tt.set_index("env")
    print(f"{'':<22}" + "".join(f"{e:>13}" for e in envs))
    for k, n, f in (("n_chuoi", "Số chuỗi", "{:,.0f}"), ("cv_p25", "p25", "{:.4f}"),
                    ("cv_p50", "Trung vị", "{:.4f}"), ("cv_p75", "p75", "{:.4f}"),
                    ("cv_iqr", "IQR", "{:.4f}"),
                    ("cv_iqr_tren_p50", "IQR / trung vị", "{:.2f}"),
                    ("cv_trung_binh", "Trung bình", "{:.4f}"),
                    ("tb_lech_p50_pct", "TB lệch trung vị %", "{:+.0f}"),
                    ("spearman_cv_mean", "ρ(CV, mức tải)", "{:+.3f}"),
                    ("cham_chan_p50", "CV / chặn, trung vị", "{:.3f}"),
                    ("sat_chan_pct", "% chuỗi sát chặn", "{:.1f}"),
                    ("vi_pham_chan", "Chuỗi vượt chặn", "{:.0f}")):
        print(f"{n:<22}" + "".join(f"{f.format(s.loc[e, k]):>13}" for e in envs))

    if len(envs) == len(ENVS):
        lo, hi = s.loc["E3", "cv_p25"], s.loc["E3", "cv_p75"]
        print(f"\nChồng lấn với IQR của E3 [{lo:.4f}, {hi:.4f}]:")
        for e in ("E1", "E2"):
            v = cv[e]["cv"].to_numpy()
            print(f"  {e}: {((v >= lo) & (v <= hi)).mean():.1%} trong khoảng | "
                  f"{(v > hi).mean():.1%} trên | {(v < lo).mean():.1%} dưới")

    ve(cv, tt, out_dir, a.dpi, kem_doc=True)
    ve(cv, tt, out_dir, a.dpi, kem_doc=False)
    print()
    for ten in ("fig_burstiness", "fig_burstiness_paper"):
        for duoi in ("png", "pdf"):
            print(f"Đã ghi: {(out_dir / f'{ten}.{duoi}').relative_to(ROOT)}")
    print(f"Đã ghi: {p_chuoi.relative_to(ROOT)}")
    print(f"Đã ghi: {p_tom.relative_to(ROOT)}")

    if a.env != "all":
        print("\n(Chạy --env all để đối chiếu đủ ba môi trường với tham chiếu của A.)")
        return 0

    lech = doi_chieu(tt, tab_dir / "reference_gd2.json")
    print()
    if lech:
        print(f"CHƯA ĐẠT — {lech} chỉ số lệch khỏi tham chiếu của A.")
        print("Sửa cách hiện thực cho đúng đặc tả, KHÔNG sửa đầu ra cho khớp số.")
        return 1
    print("Cả 12 chỉ số CV khớp tham chiếu độc lập của A.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
