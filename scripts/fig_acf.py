"""ACF và PACF đại diện cho ba môi trường (GĐ2 Bước 6).

    python scripts/fig_acf.py --env all

Sinh `results/figures/fig_acf.{png,pdf}` và `results/tables/acf_gd2.csv`.

## Xử lý NaN — chỗ dễ sai nhất của bước này

Chuỗi đã căn lưới **còn NaN**: cụm dài hơn 2 điểm không được nội suy (QĐ-008), và
E3 thiếu tới 9,29% điểm. Hai cái bẫy:

1. `statsmodels.acf` và họ hàng **không nhận NaN**.
2. `dropna()` trước khi tính thì **co trục thời gian lại** — sau khi nén, "lag 1" có
   thể là hai điểm cách nhau 2 giờ thật, và ACF đo được sẽ cao giả tạo.

Cách làm ở đây: tương quan tại lag `k` tính **chỉ trên các cặp `(t, t+k)` mà cả hai
đều không NaN**, giữ nguyên khoảng cách thời gian thật. Không nén, không nội suy
thêm, không lấp. Tỉ lệ cặp bị bỏ ở mỗi lag được **báo cáo cùng con số**, ở panel (d)
và trong bảng CSV — với E3 nó lên tới 14,65% ở lag 288, và mọi phát biểu về chu kỳ
ngày của E3 phải đi kèm con số đó.

## "Đại diện" nghĩa là gì

**Trung vị của ACF từng chuỗi tại mỗi lag.** Không chọn tay một chuỗi đẹp.

Tính ACF riêng cho từng chuỗi (theo luật cặp ở trên), rồi lấy trung vị trên toàn bộ
chuỗi được giữ, từng lag một. Panel (a) vẽ kèm dải tứ phân vị p25–p75 để thấy độ
tản, vì một đường trung vị đơn độc không nói được các chuỗi có giống nhau hay không.

**Vì sao trung vị chứ không phải gộp toàn bộ điểm vào một dãy.** Gộp làm số nở lên
rất mạnh: đo được ACF lag 1 của E1 là **0,9586** khi gộp, so với **0,6674** khi lấy
trung vị theo chuỗi. Lý do là gộp trộn phương sai *giữa* các chuỗi vào tương quan —
một chuỗi quanh mức 80 và một chuỗi quanh mức 2 tự khắc tạo ra tương quan mạnh giữa
`y_t` và `y_{t+1}` chỉ vì mỗi chuỗi bám quanh mức riêng của nó. Con số đó đo sự khác
nhau giữa các máy, không đo động lực học theo thời gian.

PACF suy từ ACF bằng đệ quy **Durbin–Levinson**, chạy trên từng chuỗi rồi cũng lấy
trung vị — cùng một quy tắc gộp với ACF. `statsmodels` không nằm trong
`requirements.txt` (QĐ-007) nên đệ quy tự viết. Dãy ACF ước lượng theo cặp không bảo
đảm xác định dương, nên đệ quy có thể mất ổn định; chuỗi nào không chạy hết bậc thì
bị loại khỏi trung vị PACF và **số chuỗi bị loại được in ra**, không giấu.

Cuối lệnh, script đối chiếu ACF tại lag 1, 6, 12, 24, 288 và tỉ lệ cặp bị bỏ với
`results/tables/reference_gd2.json` — bản hiện thực độc lập của A — và thoát 1 nếu
lệch.
"""

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]

LAG_NGAN = 48        # 4 giờ — phạm vi phiếu giao việc yêu cầu
LAG_DAI = 300        # đủ phủ lag 288 = 24 giờ
LAG_NGAY = 288
LAG_GIO = 12
TOI_THIEU_CAP = 30   # dưới ngưỡng này thì tương quan của chuỗi đó vô nghĩa

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


def ma_tran(env: str, proc_dir: Path, cat: pd.DataFrame) -> np.ndarray:
    """Bảng dài → ma trận `(số chuỗi, số bucket)`, mỗi hàng một chuỗi.

    Dạng ma trận làm ranh giới chuỗi thành ranh giới hàng, nên không phép tính nào
    ở đây có thể vô tình bắc cầu từ chuỗi này sang chuỗi kia.
    """
    f = proc_dir / f"{env}.parquet"
    if not f.exists():
        raise SystemExit(f"Thiếu {f}. Chạy: python -m cwp.preprocess.build --env all")

    d = pd.read_parquet(f, columns=["series_id", "bucket", "y"])
    giu = set(cat[(cat["env"] == env) & cat["kept"]]["series_id"])
    if set(d["series_id"].unique()) != giu:
        raise SystemExit(
            f"{env}: data/processed/ không khớp catalog.kept — sinh lại cả hai bằng "
            "một lệnh: python -m cwp.preprocess.build --env all"
        )

    d = d.sort_values(["series_id", "bucket"], kind="stable")
    n = d["series_id"].nunique()
    T, du = divmod(len(d), n)
    if du:
        raise SystemExit(f"{env}: các chuỗi không cùng độ dài, không xếp được ma trận.")
    return d["y"].to_numpy().reshape(n, T)


def acf_theo_chuoi(X: np.ndarray, K: int) -> tuple[np.ndarray, np.ndarray]:
    """ACF từng chuỗi cho lag 1..K, và tỉ lệ cặp dùng được ở mỗi lag.

    Tương quan Pearson trên đúng những cặp `(t, t+k)` mà cả hai đầu đều không NaN.
    Trừ trung bình trước khi nhân (dạng đã căn tâm) thay vì dùng `E[x²] − E[x]²` —
    công thức sau mất chữ số khi chuỗi gần hằng.
    """
    n, T = X.shape
    acf = np.full((n, K + 1), np.nan)
    acf[:, 0] = 1.0
    ti_le = np.full(K + 1, np.nan)
    ti_le[0] = float(np.isfinite(X).mean())

    for k in range(1, K + 1):
        A, B = X[:, : T - k], X[:, k:]
        M = np.isfinite(A) & np.isfinite(B)
        ti_le[k] = float(M.mean())

        dem = M.sum(axis=1)
        an_toan = np.maximum(dem, 1)
        tb_a = np.where(M, A, 0.0).sum(axis=1) / an_toan
        tb_b = np.where(M, B, 0.0).sum(axis=1) / an_toan

        da = np.where(M, A - tb_a[:, None], 0.0)
        db = np.where(M, B - tb_b[:, None], 0.0)
        cov = (da * db).sum(axis=1)
        va = (da * da).sum(axis=1)
        vb = (db * db).sum(axis=1)

        du = (dem >= TOI_THIEU_CAP) & (va > 1e-12) & (vb > 1e-12)
        acf[du, k] = cov[du] / np.sqrt(va[du] * vb[du])

    return acf, ti_le


def durbin_levinson(rho: np.ndarray, K: int) -> np.ndarray:
    """PACF từ một dãy ACF. Trả NaN từ bậc đầu tiên mà đệ quy mất ổn định.

    Dãy ACF ước lượng theo cặp không bảo đảm xác định dương, nên phương sai dự báo
    có thể tụt về 0 hoặc `|phi| >= 1`. Khi đó dừng và trả NaN chứ không trả một con
    số vô nghĩa — chuỗi đó sẽ bị loại khỏi trung vị, và số bị loại được báo cáo.
    """
    phi = np.full(K + 1, np.nan)
    if not np.isfinite(rho[1: K + 1]).all():
        return phi

    a = np.zeros(K + 1)
    phi[1] = a[1] = rho[1]
    v = 1.0 - rho[1] ** 2

    for k in range(2, K + 1):
        if v <= 1e-10:
            return phi
        p = (rho[k] - np.dot(a[1:k], rho[k - 1: 0: -1])) / v
        if not np.isfinite(p) or abs(p) >= 1.0:
            return phi
        a[1:k] = a[1:k] - p * a[k - 1: 0: -1]
        a[k] = phi[k] = p
        v *= 1.0 - p * p

    return phi


def do_mot_moi_truong(env: str, X: np.ndarray) -> dict:
    acf, ti_le = acf_theo_chuoi(X, LAG_DAI)
    pacf = np.array([durbin_levinson(acf[i], LAG_NGAN) for i in range(len(X))])
    du_pacf = np.isfinite(pacf[:, LAG_NGAN])

    with np.errstate(invalid="ignore"):
        return {
            "env": env,
            "n_chuoi": len(X),
            "acf_p50": np.nanmedian(acf, axis=0),
            "acf_p25": np.nanpercentile(acf, 25, axis=0),
            "acf_p75": np.nanpercentile(acf, 75, axis=0),
            "pacf_p50": np.nanmedian(pacf[du_pacf], axis=0),
            "bo_cap_pct": 100.0 * (1.0 - ti_le),
            "n_cap_tb": float(np.isfinite(X).sum(axis=1).mean()),
            "n_pacf": int(du_pacf.sum()),
        }


# --------------------------------------------------------------- đối chiếu

def doi_chieu(do: dict[str, dict], ref_path: Path) -> int:
    """So ACF và tỉ lệ cặp bị bỏ với bản hiện thực độc lập của A."""
    if not ref_path.exists():
        print(f"\nCẢNH BÁO: thiếu {ref_path}, bỏ qua đối chiếu.")
        return 0
    ref = {r["env"]: r for r in pd.read_json(ref_path).to_dict("records")}

    print()
    print("─" * 78)
    print("ĐỐI CHIẾU với reference_gd2.json — bản hiện thực độc lập của A")
    print("─" * 78)
    print(f"{'':<4} {'lag':>4} {'ACF B':>9} {'ACF A':>9} {'lệch':>9}   "
          f"{'bỏ cặp B':>9} {'bỏ cặp A':>9}")

    lech = 0
    for env in ENVS:
        d, r = do[env], ref.get(env, {})
        for k in (1, 6, 12, 24, LAG_NGAY):
            kb, ka = f"acf_lag_{k}", f"acf_lag_{k}_bo_cap_pct"
            if kb not in r:
                continue
            b_acf = round(float(d["acf_p50"][k]), 4)
            b_bo = round(float(d["bo_cap_pct"][k]), 4)
            d_acf = abs(b_acf - r[kb])
            d_bo = abs(b_bo - r[ka])
            xau = d_acf > 5e-4 or d_bo > 5e-4
            lech += xau
            print(f"{env:<4} {k:>4} {b_acf:>9.4f} {r[kb]:>9.4f} {d_acf:>9.4f}   "
                  f"{b_bo:>8.4f}% {r[ka]:>8.4f}%{'  ← LỆCH' if xau else ''}")
    return lech


# ------------------------------------------------------------------- vẽ

def khung_truc(ax, ten_panel, tieu_de, *, xlabel, ylabel):
    ax.grid(True, color="#e6e5e0", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for c in ("top", "right"):
        ax.spines[c].set_visible(False)
    for c in ("left", "bottom"):
        ax.spines[c].set_color("#d4d3ce")
    ax.tick_params(colors=MUC_PHU, labelsize=8, length=3)
    ax.set_xlabel(xlabel, fontsize=9, color=MUC_PHU)
    ax.set_ylabel(ylabel, fontsize=9, color=MUC_PHU)
    ax.set_title(f"{ten_panel}  {tieu_de}", fontsize=9.5, color=MUC,
                 loc="left", pad=8)


def ve(do: dict[str, dict], out_dir: Path, dpi: int, *, kem_doc: bool) -> Path:
    """Dựng hình. `kem_doc=True` dùng tiêu đề diễn giải, để duyệt cổng và dán vào log.

    Bản paper (`kem_doc=False`) dùng tiêu đề **mô tả thuần**: trong một bài báo, kết
    luận thuộc về caption và phần bàn luận, không thuộc về tiêu đề trục. Một panel
    đặt tên là "kiểm chu kỳ ngày" đã khẳng định trước điều đang cần chứng minh.
    """
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(12.0, 8.2), facecolor=NEN)
    gs = GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.19,
                  left=0.062, right=0.985, top=0.865, bottom=0.075)
    ax_a = fig.add_subplot(gs[0, 0], facecolor=NEN)
    ax_b = fig.add_subplot(gs[0, 1], facecolor=NEN)
    ax_c = fig.add_subplot(gs[1, 0], facecolor=NEN)
    ax_d = fig.add_subplot(gs[1, 1], facecolor=NEN)

    lag_n = np.arange(1, LAG_NGAN + 1)
    lag_d = np.arange(1, LAG_DAI + 1)

    # (a) ACF ngắn hạn, kèm dải tứ phân vị
    for env in ENVS:
        d = do[env]
        ax_a.fill_between(lag_n, d["acf_p25"][1:LAG_NGAN + 1],
                          d["acf_p75"][1:LAG_NGAN + 1],
                          color=MAU[env], alpha=0.13, linewidth=0, zorder=2)
        ax_a.plot(lag_n, d["acf_p50"][1:LAG_NGAN + 1], color=MAU[env],
                  linestyle=NET[env], linewidth=1.8, label=NHAN[env], zorder=3)
    for g in range(LAG_GIO, LAG_NGAN + 1, LAG_GIO):
        ax_a.axvline(g, color=MUC_MO, linewidth=0.7, linestyle=":", zorder=1)
    ax_a.axhline(0, color=MUC_MO, linewidth=0.8, zorder=1)
    khung_truc(ax_a, "(a)", "ACF, lag 1–48 (4 giờ) — trung vị và dải p25–p75",
               xlabel="lag (bucket 5 phút)", ylabel="Tự tương quan")
    ax_a.set_xlim(0, LAG_NGAN + 1)
    # Đặt ở đáy phải: đỉnh trái là chỗ chú giải đứng, còn dưới y = 0,05 ở nửa phải
    # thì không đường nào và không dải nào chạm tới.
    ax_a.text(LAG_NGAN, ax_a.get_ylim()[0], "vạch chấm: bội số 12 bucket (1 giờ) ",
              fontsize=7.5, color=MUC_MO, va="bottom", ha="right")

    # (b) PACF
    for env in ENVS:
        ax_b.plot(lag_n, do[env]["pacf_p50"][1:LAG_NGAN + 1], color=MAU[env],
                  linestyle=NET[env], linewidth=1.8, zorder=3)
    ax_b.axhline(0, color=MUC_MO, linewidth=0.8, zorder=1)
    khung_truc(ax_b, "(b)", "PACF, lag 1–48 — trung vị theo chuỗi",
               xlabel="lag (bucket 5 phút)", ylabel="Tự tương quan riêng phần")
    ax_b.set_xlim(0, LAG_NGAN + 1)

    # (c) ACF dài hạn — chu kỳ ngày lộ ra hay không
    for env in ENVS:
        ax_c.plot(lag_d, do[env]["acf_p50"][1:LAG_DAI + 1], color=MAU[env],
                  linestyle=NET[env], linewidth=1.6, zorder=3)
    ax_c.axvline(LAG_NGAY, color=MUC_MO, linewidth=0.9, linestyle="--", zorder=1)
    ax_c.axhline(0, color=MUC_MO, linewidth=0.8, zorder=1)
    khung_truc(ax_c, "(c)", ("ACF tới lag 300 — kiểm chu kỳ ngày tại lag 288"
                             if kem_doc else "ACF, lag 1–300"),
               xlabel="lag (bucket 5 phút)", ylabel="Tự tương quan")
    ax_c.set_xlim(0, LAG_DAI)
    for env in ENVS:
        v = do[env]["acf_p50"][LAG_NGAY]
        ax_c.plot([LAG_NGAY], [v], marker="o", markersize=5, color=MAU[env],
                  markeredgecolor=NEN, markeredgewidth=1.2, zorder=4)
    ax_c.annotate(
        f"lag 288 = 24 giờ\nE3 {do['E3']['acf_p50'][LAG_NGAY]:.4f}  ·  "
        f"E1 {do['E1']['acf_p50'][LAG_NGAY]:.4f}  ·  "
        f"E2 {do['E2']['acf_p50'][LAG_NGAY]:.4f}",
        xy=(LAG_NGAY, do["E3"]["acf_p50"][LAG_NGAY]),
        xytext=(150, 0.80), textcoords="data", fontsize=8, color=MUC_PHU,
        ha="left", va="center",
        arrowprops=dict(arrowstyle="->", color=MUC_MO, linewidth=0.9,
                        connectionstyle="arc3,rad=-0.2"),
        bbox=dict(boxstyle="round,pad=0.4", facecolor=NEN, edgecolor="#d4d3ce",
                  linewidth=0.7), zorder=5)

    # (d) tỉ lệ cặp bị bỏ
    for env in ENVS:
        ax_d.plot(lag_d, do[env]["bo_cap_pct"][1:LAG_DAI + 1], color=MAU[env],
                  linestyle=NET[env], linewidth=1.8, zorder=3)
    ax_d.axvline(LAG_NGAY, color=MUC_MO, linewidth=0.9, linestyle="--", zorder=1)
    khung_truc(ax_d, "(d)", "Tỉ lệ cặp (t, t+k) bị bỏ vì có NaN",
               xlabel="lag (bucket 5 phút)", ylabel="% cặp bị bỏ")
    ax_d.set_xlim(0, LAG_DAI)
    ax_d.set_ylim(bottom=0)
    # Nhãn ghi giá trị tại lag 288 thì phải đặt ĐÚNG tại lag 288 — đặt ở mép phải
    # (lag 300) sẽ khiến người đọc gán con số cho sai điểm.
    for env in ENVS:
        ax_d.annotate(f"{do[env]['bo_cap_pct'][LAG_NGAY]:.2f}%",
                      xy=(LAG_NGAY, do[env]["bo_cap_pct"][LAG_NGAY]),
                      xytext=(-6, 4), textcoords="offset points",
                      fontsize=8, color=MAU[env], ha="right", va="bottom")

    fig.suptitle("Cấu trúc phụ thuộc thời gian — ACF và PACF ba môi trường",
                 fontsize=13, color=MUC, x=0.062, ha="left", y=0.965)
    fig.text(0.062, 0.918,
             "Trung vị trên toàn bộ chuỗi được giữ, từng lag một. Tương quan tại lag "
             "k chỉ dùng các cặp (t, t+k) mà cả hai đều không NaN — không nén trục "
             "thời gian.",
             fontsize=9, color=MUC_PHU, ha="left")
    ax_a.legend(loc="upper right", fontsize=8.2, frameon=True, framealpha=1.0,
                edgecolor="#d4d3ce", facecolor=NEN, borderpad=0.6,
                labelcolor=MUC_PHU)

    ten = "fig_acf" if kem_doc else "fig_acf_paper"
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
    out_dir = ROOT / a.out
    tab_dir = ROOT / a.tables
    out_dir.mkdir(parents=True, exist_ok=True)
    tab_dir.mkdir(parents=True, exist_ok=True)

    cat = pd.read_parquet(ROOT / a.catalog)
    do = {}
    for env in envs:
        X = ma_tran(env, ROOT / a.processed, cat)
        d = do_mot_moi_truong(env, X)
        do[env] = d
        print(f"{env}: {d['n_chuoi']} chuỗi, trung bình {d['n_cap_tb']:.0f} điểm "
              f"không NaN mỗi chuỗi | PACF chạy hết bậc {LAG_NGAN} ở "
              f"{d['n_pacf']}/{d['n_chuoi']} chuỗi "
              f"({d['n_chuoi'] - d['n_pacf']} chuỗi bị loại khỏi trung vị PACF)")

    hang = []
    for env in envs:
        d = do[env]
        for k in range(0, LAG_DAI + 1):
            hang.append({
                "env": env, "lag": k,
                "acf_p50": round(float(d["acf_p50"][k]), 6),
                "acf_p25": round(float(d["acf_p25"][k]), 6),
                "acf_p75": round(float(d["acf_p75"][k]), 6),
                "pacf_p50": (round(float(d["pacf_p50"][k]), 6)
                             if k <= LAG_NGAN else np.nan),
                "bo_cap_pct": round(float(d["bo_cap_pct"][k]), 6),
            })
    csv_path = tab_dir / "acf_gd2.csv"
    pd.DataFrame(hang).to_csv(csv_path, index=False, encoding="utf-8")

    print()
    for env in envs:
        d = do[env]
        print(f"{env}  ACF: " + "  ".join(
            f"lag{k}={d['acf_p50'][k]:.4f}" for k in (1, 6, 12, 24, LAG_NGAY)))
        print(f"{'':4}bỏ cặp: " + "  ".join(
            f"lag{k}={d['bo_cap_pct'][k]:.2f}%" for k in (1, 6, 12, 24, LAG_NGAY)))

    ve(do, out_dir, a.dpi, kem_doc=True)
    ve(do, out_dir, a.dpi, kem_doc=False)
    print()
    for ten in ("fig_acf", "fig_acf_paper"):
        for duoi in ("png", "pdf"):
            print(f"Đã ghi: {(out_dir / f'{ten}.{duoi}').relative_to(ROOT)}")
    print(f"Đã ghi: {csv_path.relative_to(ROOT)}")
    print("\nfig_acf       — tiêu đề diễn giải, để duyệt cổng và dán vào log")
    print("fig_acf_paper — tiêu đề mô tả thuần, đứng độc lập, để dán vào paper")

    if a.env != "all":
        print("\n(Chạy --env all để đối chiếu đủ ba môi trường với tham chiếu của A.)")
        return 0

    lech = doi_chieu(do, tab_dir / "reference_gd2.json")
    print()
    if lech:
        print(f"CHƯA ĐẠT — {lech} chỉ số lệch khỏi tham chiếu của A.")
        print("Sửa cách hiện thực cho đúng đặc tả, KHÔNG sửa đầu ra cho khớp số.")
        return 1
    print("Mọi chỉ số khớp tham chiếu độc lập của A.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
