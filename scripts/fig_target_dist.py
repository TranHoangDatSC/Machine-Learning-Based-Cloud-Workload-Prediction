"""Hình phân phối CPU% ba môi trường — điều kiện qua cổng GĐ2 (Bước 5).

    python scripts/fig_target_dist.py

Sinh `results/figures/fig_target_dist.{png,pdf}` và tệp caption đi kèm.

**Quần thể vẽ — QĐ-011 điểm 2.** Phân phối gộp của `y` trên các chuỗi được giữ,
trong cửa sổ 8 ngày. **Không phải** cột `target` của ma trận đặc trưng.

**Vì sao ECDF chứ không phải histogram hay KDE.** Trung vị của E1 và E2 dưới 2%,
của E3 gần 38%. Trên một trục mật độ tuyến tính chung thì toàn bộ khối lượng của
E1/E2 rơi vào cột đầu tiên và hình không nói được gì — đúng cảnh báo ở phiếu giao
việc. ECDF gỡ được vì trục tung là xác suất tích luỹ: **mỗi đường bắt buộc đi từ 0
lên 1**, nên không môi trường nào bị nén. Kèm theo ba lợi thế:

- Không phải chọn độ rộng bin, nên không có tham số nào để vô tình chỉnh cho hình
  đẹp lên.
- Khối 5,12% điểm nằm đúng tại trần 100 của E1 hiện thành một **bước nhảy thẳng
  đứng ở mép phải** — kiểm duyệt do clip trở nên nhìn thấy được thay vì bị giấu
  trong cột cuối của histogram (QĐ-011 điểm 3).
- Đọc thẳng được phân vị: cắt ngang tại 0,5 ra trung vị.

Hai panel vì chúng trả lời hai câu khác nhau. Panel (a) trục tuyến tính trả lời câu
của RQ3: ba môi trường nằm ở ba mức tải khác nhau. Panel (b) trục symlog phóng to
vùng dưới 1% nơi trung vị của E1/E2 thực sự nằm — trên trục tuyến tính vùng đó dồn
hết vào vài pixel sát trục tung.

**Không dùng trục phụ (hai thang y).** Đó là lỗi biểu đồ phổ biến nhất: hai thang
khác nhau trên cùng một hình cho phép đặt hai đường cạnh nhau ở bất kỳ vị trí tương
đối nào, nên hình nói được điều mà dữ liệu không nói.

Bảng phân vị đọc từ `results/tables/describe_gd2.csv` (Bước 4) chứ không tính lại —
một nguồn sự thật, hình và bảng của paper không thể lệch nhau. Script kiểm chéo
trung vị suy từ ECDF với `p50` trong bảng đó.
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

NHAN = {
    "E1": "E1 — Bitbrains fastStorage (VM)",
    "E2": "E2 — Bitbrains Rnd 2013-8 (VM)",
    "E3": "E3 — Alibaba v2018 (máy vật lý)",
}

# Ba khe categorical đầu tiên của bảng màu tham chiếu, dùng đúng thứ tự, không xoay
# vòng. Đã chạy validator: qua cả sáu phép kiểm trên nền sáng — dải độ sáng, sàn
# chroma, tách màu cho người mù màu (ΔE 9,2 deutan ở cặp xấu nhất), sàn thị lực
# thường (ΔE 27,6). Một cảnh báo tương phản ở màu aqua, đã bù bằng nhãn trực tiếp
# và bảng phân vị.
MAU = {"E1": "#2a78d6", "E2": "#eb6834", "E3": "#1baf7a"}

# Mã hoá thứ hai ngoài màu: hình sẽ được in đen trắng, và người mù màu đọc nét.
NET = {"E1": "-", "E2": "--", "E3": "-."}

MUC = "#0b0b0b"
MUC_PHU = "#52514e"
MUC_MO = "#8a8a85"
NEN = "#fcfcfb"


def nap_du_lieu(proc_dir: Path, cat: pd.DataFrame) -> dict[str, np.ndarray]:
    """Mảng `y` đã sắp xếp, chỉ chuỗi được giữ, mỗi môi trường một mảng."""
    ra = {}
    for env in ENVS:
        f = proc_dir / f"{env}.parquet"
        if not f.exists():
            raise SystemExit(
                f"Thiếu {f}. Chạy: python -m cwp.preprocess.build --env all"
            )
        d = pd.read_parquet(f, columns=["series_id", "y"])
        giu = set(cat[(cat["env"] == env) & cat["kept"]]["series_id"])
        if set(d["series_id"].unique()) != giu:
            raise SystemExit(
                f"{env}: data/processed/ không khớp catalog.kept — sinh lại cả hai "
                "bằng một lệnh: python -m cwp.preprocess.build --env all"
            )
        y = d["y"].to_numpy()
        ra[env] = np.sort(y[~np.isnan(y)])
    return ra


def luoi_x() -> np.ndarray:
    """Lưới hoành độ để lượng giá ECDF.

    Gộp một lưới tuyến tính, một lưới log (để vùng dưới 1% không bị thưa), và hai
    điểm sát trần — thiếu chúng thì bước nhảy tại 100 bị nội suy thành đường xiên
    và trông như một cái đuôi mượt thay vì một khối bị kiểm duyệt.
    """
    return np.unique(np.concatenate([
        np.linspace(0.0, 100.0, 2001),
        np.geomspace(0.005, 100.0, 900),
        [100.0 - 1e-9, 100.0],
    ]))


def ecdf(ys: np.ndarray, xs: np.ndarray) -> np.ndarray:
    """F(x) = tỉ lệ điểm <= x. Tính chính xác bằng tìm kiếm nhị phân, không xấp xỉ."""
    return np.searchsorted(ys, xs, side="right") / len(ys)


def _so_gon(v, _pos=None) -> str:
    """3.0 → 3, 0.5 → 0,5. Trục symlog mặc định in đuôi .0 thừa."""
    return (f"{v:g}").replace(".", ",")


def ve_panel(ax, xs, duong, *, symlog: bool, ten_panel: str, tieu_de: str):
    for env in ENVS:
        ax.plot(xs, duong[env], color=MAU[env], linestyle=NET[env], linewidth=1.8,
                solid_capstyle="round", label=NHAN[env], zorder=3)

    ax.axhline(0.5, color=MUC_MO, linewidth=0.8, linestyle=":", zorder=1)
    # Nhãn đặt bên TRÁI: mép phải là chỗ hộp chú thích trần đứng, để bên đó thì
    # hai thứ chồng lên nhau.
    ax.text(0.012, 0.505, "trung vị", transform=ax.get_yaxis_transform(),
            ha="left", va="bottom", fontsize=7.5, color=MUC_MO)

    ax.set_ylim(-0.02, 1.02)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("Tỉ lệ điểm tích luỹ", fontsize=9, color=MUC_PHU)
    ax.set_xlabel("CPU% (thang 0–100)", fontsize=9, color=MUC_PHU)

    if symlog:
        ax.set_xscale("symlog", linthresh=1.0, linscale=0.6)
        ax.set_xlim(0, 100)
        ax.set_xticks([0, 0.5, 1, 3, 10, 30, 100])
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(_so_gon))
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    else:
        ax.set_xlim(-1, 103)
        ax.set_xticks([0, 20, 40, 60, 80, 100])

    ax.grid(True, color="#e6e5e0", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for canh in ("top", "right"):
        ax.spines[canh].set_visible(False)
    for canh in ("left", "bottom"):
        ax.spines[canh].set_color("#d4d3ce")
    ax.tick_params(colors=MUC_PHU, labelsize=8, length=3)
    ax.set_title(f"{ten_panel}  {tieu_de}", fontsize=9.5, color=MUC,
                 loc="left", pad=8)


def chu_thich_tran(ax, duong, xs):
    """Chỉ vào bước nhảy tại trần 100 — QĐ-011 điểm 3 đòi hình phải nói ra chỗ này."""
    i_truoc = int(np.searchsorted(xs, 100.0 - 1e-9))
    tran = {e: 1.0 - duong[e][i_truoc] for e in ENVS}

    ax.annotate(
        f"Trần clip 100: {tran['E1']:.2%} điểm của E1\n"
        f"và {tran['E2']:.2%} của E2 dồn vào đây.\nE3 không chạm trần.",
        # Đặt ở vùng trống thật: với x > 60 thì cả ba đường đều nằm trên y = 0,9,
        # còn chú giải chiếm y < 0,25. Dải giữa hoàn toàn rỗng, và mũi tên đi lên
        # thẳng nên không cắt qua đường nào.
        xy=(100, 1 - tran["E1"] / 2), xycoords="data",
        xytext=(59, 0.46), textcoords="data",
        fontsize=8, color=MUC_PHU, ha="left", va="center",
        arrowprops=dict(arrowstyle="->", color=MUC_MO, linewidth=0.9,
                        connectionstyle="arc3,rad=0.22"),
        bbox=dict(boxstyle="round,pad=0.45", facecolor=NEN,
                  edgecolor="#d4d3ce", linewidth=0.7),
        zorder=5,
    )
    return tran


def ve_bang(ax, bang: pd.DataFrame, ten_panel: str = ""):
    """Bảng phân vị — người đọc lấy được con số mà không phải đoán từ hình."""
    ax.axis("off")
    hang = [("p10", "p10"), ("p25", "p25"), ("p50", "Trung vị"), ("p75", "p75"),
            ("p90", "p90"), ("p95", "p95"), ("mean", "Trung bình"),
            ("std", "Độ lệch chuẩn"), ("pct_bang_100", "% điểm = 100"),
            ("pct_nan", "% điểm thiếu")]

    o = [[f"{bang.loc[e, khoa]:,.2f}" for e in ENVS] for khoa, _ in hang]
    t = ax.table(cellText=o, rowLabels=[n for _, n in hang], colLabels=ENVS,
                 cellLoc="right", rowLoc="right", loc="center",
                 colWidths=[0.21] * 3)
    t.auto_set_font_size(False)
    t.set_fontsize(8)
    t.scale(1, 1.32)

    for (r, c), o_ in t.get_celld().items():
        o_.set_edgecolor("#e6e5e0")
        o_.set_linewidth(0.6)
        if r == 0:  # hàng tiêu đề: chấm màu mang định danh, chữ vẫn là mực
            o_.set_facecolor("#f2f1ec")
            o_.get_text().set_color(MAU[ENVS[c]] if c >= 0 else MUC)
            o_.get_text().set_fontweight("bold")
        else:
            o_.get_text().set_color(MUC if hang[r - 1][0] == "p50" else MUC_PHU)
            if hang[r - 1][0] == "p50":
                o_.get_text().set_fontweight("bold")
    # Bản paper để bảng ở cột hẹp thứ ba, tiêu đề dài sẽ tràn khỏi mép hình.
    tieu_de = (f"{ten_panel}  Bảng phân vị" if ten_panel
               else "Bảng phân vị — CPU% sau tiền xử lý")
    ax.set_title(tieu_de, fontsize=9.5, color=MUC, loc="left", pad=12)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--out", default="results/figures")
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()

    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)

    bang_path = ROOT / a.tables / "describe_gd2.csv"
    if not bang_path.exists():
        raise SystemExit(
            f"Thiếu {bang_path}. Chạy Bước 4 trước: "
            "python scripts/describe_gd2.py --env all"
        )
    bang = pd.read_csv(bang_path).set_index("env")

    cat = pd.read_parquet(ROOT / a.catalog)
    print("Đang nạp data/processed/ …")
    du_lieu = nap_du_lieu(ROOT / a.processed, cat)
    for e in ENVS:
        print(f"  {e}: {len(du_lieu[e]):,} điểm không NaN")

    xs = luoi_x()
    duong = {e: ecdf(du_lieu[e], xs) for e in ENVS}

    # Khoá vòng: trung vị suy từ ECDF phải khớp p50 của bảng Bước 4. Lệch nghĩa là
    # hình và bảng trong paper đang mô tả hai quần thể khác nhau.
    print("\nĐối chiếu trung vị suy từ ECDF với describe_gd2.csv:")
    lech = 0
    for e in ENVS:
        tu_ecdf = float(xs[np.searchsorted(duong[e], 0.5, side="left")])
        tu_bang = float(bang.loc[e, "p50"])
        xau = abs(tu_ecdf - tu_bang) > 0.06   # bước lưới quanh vùng đó
        lech += xau
        print(f"  {e}: ECDF {tu_ecdf:7.4f}   bảng {tu_bang:7.4f}"
              f"{'   ← LỆCH' if xau else ''}")
    if lech:
        print("\nCHƯA ĐẠT — hình và bảng không mô tả cùng một quần thể.")
        return 1

    plt.rcParams["font.family"] = "DejaVu Sans"

    fig_full, tran = ve_hinh(bang, xs, duong, kem_doc=True)
    fig_paper, _ = ve_hinh(bang, xs, duong, kem_doc=False)

    ra = []
    for ten, f in (("fig_target_dist", fig_full), ("fig_target_dist_paper", fig_paper)):
        for duoi in ("png", "pdf"):
            p = out_dir / f"{ten}.{duoi}"
            f.savefig(p, dpi=a.dpi, facecolor=NEN)
            ra.append(p)
        plt.close(f)

    cap = out_dir / "fig_target_dist.caption.md"
    cap.write_text(caption(bang, tran), encoding="utf-8")
    ra.append(cap)

    print()
    for p in ra:
        print(f"Đã ghi: {p.relative_to(ROOT)}")
    print("\nfig_target_dist       — kèm panel (c) hướng dẫn đọc, để A duyệt cổng")
    print("fig_target_dist_paper — bản sạch không có chữ trong hình, để đưa vào paper")
    print("\nA duyệt bằng mắt: mở hình, kiểm cả ba đường đọc được và không đường "
          "nào bị ép sát mép.")
    return 0


def ve_hinh(bang, xs, duong, *, kem_doc: bool):
    """Dựng hình. `kem_doc=True` thêm panel (c) hướng dẫn đọc.

    Hai bản vì hai người đọc khác nhau. Bản có panel (c) để A duyệt cổng và để dán
    vào log — người đọc cần biết phải nhìn gì. Bản không có để đưa vào paper: chữ
    nằm trong hình là chỗ của caption LaTeX, không phải của tệp ảnh, và một khối
    văn xuôi in cứng trong hình thì không sửa được khi câu chữ của bài đổi.
    """
    if kem_doc:
        fig = plt.figure(figsize=(11.0, 7.8), facecolor=NEN)
        gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 0.72],
                      width_ratios=[1.18, 0.82], hspace=0.46, wspace=0.20,
                      left=0.065, right=0.985, top=0.855, bottom=0.075)
        ax1 = fig.add_subplot(gs[0, 0], facecolor=NEN)
        ax2 = fig.add_subplot(gs[0, 1], facecolor=NEN)
        ax_doc = fig.add_subplot(gs[1, 0], facecolor=NEN)
        ax_bang = fig.add_subplot(gs[1, 1], facecolor=NEN)
        y_tieu_de, y_phu = 0.963, 0.912
    else:
        fig = plt.figure(figsize=(12.4, 4.5), facecolor=NEN)
        gs = GridSpec(1, 3, figure=fig, width_ratios=[1.0, 1.0, 0.62],
                      wspace=0.24, left=0.055, right=0.99, top=0.76, bottom=0.135)
        ax1 = fig.add_subplot(gs[0, 0], facecolor=NEN)
        ax2 = fig.add_subplot(gs[0, 1], facecolor=NEN)
        ax_doc = None
        ax_bang = fig.add_subplot(gs[0, 2], facecolor=NEN)
        y_tieu_de, y_phu = 0.945, 0.865

    # Bản duyệt cổng dùng tiêu đề diễn giải; bản paper dùng tiêu đề mô tả thuần.
    # Trong paper, diễn giải thuộc về caption chứ không thuộc về hình — một tiêu đề
    # khẳng định kết luận ngay trên trục là thứ người phản biện sẽ hỏi.
    ve_panel(ax1, xs, duong, symlog=False, ten_panel="(a)",
             tieu_de=("Trục tuyến tính — ba mức tải tách hẳn nhau" if kem_doc
                      else "ECDF, trục tuyến tính"))
    ve_panel(ax2, xs, duong, symlog=True, ten_panel="(b)",
             tieu_de=("Trục symlog — phóng to vùng dưới 1%" if kem_doc
                      else "ECDF, trục symlog"))
    tran = chu_thich_tran(ax1, duong, xs)
    ve_bang(ax_bang, bang, ten_panel="(c)" if not kem_doc else "")

    if ax_doc is not None:
        ve_huong_dan(ax_doc, bang, tran)

    x_le = 0.065 if kem_doc else 0.055
    fig.suptitle("Phân phối CPU% của ba môi trường sau tiền xử lý",
                 fontsize=13, color=MUC, x=x_le, ha="left", y=y_tieu_de)
    # Bản paper không nhắc mã quyết định nội bộ — người đọc paper không biết QĐ-011
    # là gì, và một hình phải tự đứng được.
    phu = ("Hàm phân phối tích luỹ thực nghiệm (ECDF). Gộp mọi điểm không NaN của "
           "chuỗi được giữ, trong cửa sổ 8 ngày (QĐ-011 điểm 2)." if kem_doc else
           "Hàm phân phối tích luỹ thực nghiệm (ECDF), gộp mọi điểm quan sát của các "
           "chuỗi còn lại sau bộ lọc, trong cửa sổ 8 ngày.")
    fig.text(x_le, y_phu, phu, fontsize=9, color=MUC_PHU, ha="left")

    ax1.legend(loc="lower right", fontsize=8.2, frameon=True, framealpha=1.0,
               edgecolor="#d4d3ce", facecolor=NEN, borderpad=0.6,
               labelcolor=MUC_PHU)
    return fig, tran


def ve_huong_dan(ax, bang, tran):
    """Panel (c) — ba điều phải đọc ra từ hình, ngắt dòng theo bề rộng thật."""
    import textwrap

    ax.axis("off")
    ax.set_title("(c)  Đọc gì từ hình này", fontsize=9.5, color=MUC,
                 loc="left", pad=12)

    doan = [
        ("Mức tải lệch nhau — tiền đề của RQ3.",
         f"Trung vị {bang.loc['E1','p50']:.2f}% (E1) và "
         f"{bang.loc['E2','p50']:.2f}% (E2) so với {bang.loc['E3','p50']:.2f}% (E3). "
         "Ba đường gần như không giao nhau ở panel (a). Transfer thô giữa hai vùng "
         "này sẽ đo chênh lệch mức tải chứ không đo khả năng khái quát — đó là lý do "
         "TN-B chạy ba chế độ chuẩn hoá N0/N1/N2 (QĐ-005)."),
        ("Trần 100 là kiểm duyệt, và bất đối xứng.",
         f"{tran['E1']:.2%} điểm của E1 và {tran['E2']:.2%} của E2 nằm đúng tại 100; "
         "E3 là 0%. Phân vị 95 của E1 chính là trần. Một phần của kết luận “E3 "
         "dễ dự đoán hơn” đến từ chỗ này, không chỉ từ hiệu ứng tổng hợp ở mức "
         "máy vật lý (QĐ-004, QĐ-011)."),
        ("Quần thể là chuỗi ĐÃ LỌC.",
         "Bộ lọc gan_chet bỏ 36,3% chuỗi E1 và 39,4% chuỗi E2 nhưng chỉ 0,4% chuỗi "
         "E3, và cắt gần như hoàn toàn ở đuôi dưới. Hình mô tả phần VM còn hoạt "
         "động, không mô tả “Bitbrains” nói chung."),
    ]

    y = 0.99
    for dau, than in doan:
        ax.text(0, y, dau, fontsize=8.3, color=MUC, va="top", ha="left",
                fontweight="bold", transform=ax.transAxes)
        y -= 0.085
        chu = textwrap.fill(than, width=86)
        ax.text(0, y, chu, fontsize=8.1, color=MUC_PHU, va="top", ha="left",
                linespacing=1.45, transform=ax.transAxes)
        y -= 0.075 * (chu.count("\n") + 1) + 0.055


def caption(bang: pd.DataFrame, tran: dict) -> str:
    return f"""# Caption — hình phân phối CPU%

Sinh bằng `python scripts/fig_target_dist.py`. Không sửa tay.

## Caption ngắn (đặt dưới hình trong paper)

> **Hình 1. Phân phối CPU% của ba môi trường sau tiền xử lý.** Hàm phân phối tích
> luỹ thực nghiệm (ECDF) trên (a) trục tuyến tính và (b) trục symlog. Trung vị là
> {bang.loc['E1','p50']:.2f}% (E1), {bang.loc['E2','p50']:.2f}% (E2) và
> {bang.loc['E3','p50']:.2f}% (E3). Bước nhảy thẳng đứng tại 100 là hệ quả của bước
> clip: {tran['E1']:.2%} điểm của E1 và {tran['E2']:.2%} của E2 nằm đúng tại trần,
> E3 không có điểm nào. Quần thể là các chuỗi còn lại sau bộ lọc ở protocol mục 6
> bước 7, không phải toàn bộ trace.

## Vì sao chọn ECDF — trả lời yêu cầu của phiếu giao việc

Vấn đề: trung vị của E1 và E2 dưới 2%, của E3 gần 38%. Trên một trục **mật độ**
tuyến tính chung, toàn bộ khối lượng của E1/E2 rơi vào cột đầu tiên và hình không
nói được gì.

Ba phương án phiếu nêu là ECDF, log1p, và trục phụ. Chọn **ECDF**:

| Phương án | Vì sao chọn hay bỏ |
|---|---|
| **ECDF** | Trục tung là xác suất tích luỹ nên **mỗi đường bắt buộc đi từ 0 lên 1** — không môi trường nào bị nén, kể cả khi mức tải lệch 20 lần. Không có tham số bin để vô tình chỉnh. Đọc thẳng được phân vị. Khối bị kiểm duyệt tại trần hiện thành bước nhảy nhìn thấy được |
| log1p | Đọc được cả ba, nhưng bóp méo khoảng cách giữa các mức tải — mà chênh lệch mức tải chính là điều hình này phải cho thấy |
| Trục phụ | **Loại.** Hai thang y trên một hình cho phép đặt hai đường cạnh nhau ở bất kỳ vị trí tương đối nào, nên hình nói được điều dữ liệu không nói |

Hai panel vì chúng trả lời hai câu khác nhau. Panel (a) trục tuyến tính trả lời câu
của RQ3 — ba môi trường ở ba mức tải khác nhau. Panel (b) trục symlog phóng to vùng
dưới 1%, nơi trung vị của E1/E2 thực sự nằm; trên trục tuyến tính vùng đó chỉ chiếm
vài pixel sát trục tung.

## Ghi chú kỹ thuật

- Quần thể: gộp mọi điểm `y` không NaN của các chuỗi được giữ, trong cửa sổ 8 ngày.
  **Không phải** cột `target` của ma trận đặc trưng — xem QĐ-011 điểm 2.
- Bảng phân vị đọc từ `results/tables/describe_gd2.csv`, không tính lại. Script kiểm
  chéo trung vị suy từ ECDF với `p50` trong bảng đó, lệch quá bước lưới thì thoát 1.
- Màu lấy ba khe categorical đầu của bảng màu tham chiếu, đúng thứ tự. Đã chạy
  validator: qua cả sáu phép kiểm trên nền sáng, ΔE deutan 9,2 ở cặp xấu nhất. Kèm
  mã hoá thứ hai bằng kiểu nét (liền / đứt / gạch-chấm) để hình đọc được khi in đen
  trắng và khi người đọc mù màu.
"""


if __name__ == "__main__":
    sys.exit(main())
