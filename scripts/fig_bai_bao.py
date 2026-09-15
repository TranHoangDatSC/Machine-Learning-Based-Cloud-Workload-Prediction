"""Hình cho bản thảo bài báo — khổ trang HJS (vùng chữ ~16,9 cm), in đen trắng vẫn đọc được.

    python scripts/fig_bai_bao.py

Ra `paper/figures/`:

    hinh1_quy-trinh.png          sơ đồ quy trình nghiên cứu
    hinh2_phan-phoi-cpu.png      ba histogram CPU% ghép một hình (từ fig_bo_sung B01–B03)
    hinh3_ti-so-naive.png        heatmap tỉ số MAE / naive (B08)
    hinh4_mat-mat-transfer.png   heatmap L cuối cùng của RQ3 (B09)
    hinh5_phan-bo-L.png          boxplot L theo chuỗi (B10)

Không số mới: hình 2–5 gọi đúng hàm vẽ của `fig_bo_sung.py`, chỉ đổi khổ và bố cục.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

import fig_bo_sung as fb  # noqa: E402
from cwp.viz.xuat import MUC, MUC_PHU, NEN  # noqa: E402

RA = ROOT / "paper" / "figures"
DPI = 300
CM = 1 / 2.54


def luu(fig, ten):
    RA.mkdir(parents=True, exist_ok=True)
    fig.savefig(RA / ten, dpi=DPI, facecolor=NEN, bbox_inches="tight")
    plt.close(fig)
    print(f"   {ten}")


# ----------------------------------------------------------- hình 1

def hinh_quy_trinh():
    fig, ax = plt.subplots(figsize=(16.5 * CM, 10.5 * CM), facecolor=NEN)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)
    ax.axis("off")
    NHAT, VUA, VIEN, NET = "#eef4fc", "#cde2fb", "#1c5cab", "#52514e"

    def hop(x, y, w, h, dau, than, nen=NHAT, vien=VIEN):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.0",
                                    facecolor=nen, edgecolor=vien, linewidth=0.9))
        ax.text(x + w / 2, y + h - 1.6, dau, ha="center", va="top", fontsize=6.6,
                color=MUC, fontweight="bold", linespacing=1.25)
        ax.text(x + w / 2, y + h - (7.0 if "\n" in dau else 4.6), than, ha="center", va="top",
                fontsize=5.8, color=MUC_PHU, linespacing=1.35)

    def mui(x1, y1, x2, y2, dau_mui=True):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>" if dau_mui else "-",
                                     mutation_scale=8, color=NET, linewidth=0.9,
                                     shrinkA=0, shrinkB=0))

    rong, cach = 22.6, 2.6
    cot = [0.8 + i * (rong + cach) for i in range(4)]
    hop(cot[0], 44, rong, 18, "1. Dữ liệu thô", "Bitbrains fastStorage\nBitbrains Rnd 2013-8\nAlibaba v2018")
    hop(cot[1], 44, rong, 18, "2. Tiền xử lý", "lưới 5 phút\ncửa sổ 8 ngày\nnội suy lỗ ≤ 10 phút\nlọc → 1.535 chuỗi")
    hop(cot[2], 44, rong, 18, "3. Đặc trưng", "19 đặc trưng quá khứ\nchia theo thời gian\nhuấn luyện, kiểm định,\nkiểm tra")
    hop(cot[3], 44, rong, 18, "4. Mô hình", "3 mô hình cơ sở\n5 mô hình học máy\ndự đoán trước\n5, 30, 60 phút")
    for i in range(3):
        mui(cot[i] + rong + 0.4, 53, cot[i + 1] - 0.4, 53)

    # Mô hình cấp cho cả hai thí nghiệm: xuống, rẽ ngang, rồi xuống từng nhánh.
    xg = cot[3] + rong / 2
    mui(xg, 43.6, xg, 39.5, dau_mui=False)
    mui(25, 39.5, xg, 39.5, dau_mui=False)
    mui(25, 39.5, 25, 35.4)
    mui(75, 39.5, 75, 35.4)

    hop(2, 17, 46, 18, "Thí nghiệm 1: trong từng môi trường\n(câu hỏi 1 và 2)",
        "8 mô hình × 3 môi trường × 3 tầm dự báo\nso với dự báo naïve trên từng máy\nkiểm định thống kê có hiệu chỉnh", VUA)
    hop(52, 17, 46, 18, "Thí nghiệm 2: giữa các môi trường\n(câu hỏi 3)",
        "6 cặp môi trường × 3 cách chuẩn hoá\nso với mô hình học ngay tại đích\nphần nào của tín hiệu dùng lại được?", VUA)

    hop(2, 1.5, 96, 11, "Kiểm tra xuyên suốt",
        "chống rò rỉ dữ liệu · tính chất toán học của phép chuẩn hoá\n"
        "đối chiếu giá trị cần dự đoán với dữ liệu gốc",
        nen="#f0efec", vien="#898781")
    luu(fig, "hinh1_quy-trinh.png")


# ------------------------------------------------------- hình 2–5

def hinh_phan_phoi():
    ps, _ = fb.panels_gd2()
    fig, axs = plt.subplots(1, 3, figsize=(17 * CM, 5.6 * CM), facecolor=NEN, sharey=True)
    for ax, p, e in zip(axs, ps[:3], fb.ENVS):
        ax.set_facecolor(NEN)
        p.ve(ax)
        ax.set_title(fb.TEN_ENV[e], fontsize=8.5, color=MUC, loc="left")
        ax.set_xlabel("CPU (%)", fontsize=8, color=MUC_PHU)
        ax.tick_params(labelsize=7.5)
        for t in ax.texts:
            t.set_fontsize(7.2)
    for ax in axs[1:]:
        ax.set_ylabel("")
    axs[0].set_ylabel("% số điểm dữ liệu", fontsize=8, color=MUC_PHU)
    fig.tight_layout(w_pad=1.2)
    luu(fig, "hinh2_phan-phoi-cpu.png")


def mot_panel(ham, ten_panel, ten_tep, figsize_cm):
    ps, _ = ham()
    p = next(x for x in ps if x.ten == ten_panel)
    fig, ax = plt.subplots(figsize=(figsize_cm[0] * CM, figsize_cm[1] * CM), facecolor=NEN)
    ax.set_facecolor(NEN)
    p.ve(ax)
    luu(fig, ten_tep)


def main() -> int:
    print("Hình bài báo →", RA.relative_to(ROOT))
    hinh_quy_trinh()
    hinh_phan_phoi()
    mot_panel(fb.panels_gd3, "B08_heatmap-ti-so-naive", "hinh3_ti-so-naive.png", (17, 9.5))
    mot_panel(fb.panels_gd4, "B09_heatmap-mat-mat-transfer", "hinh4_mat-mat-transfer.png", (13, 8.5))
    mot_panel(fb.panels_gd4, "B10_boxplot-mat-mat-transfer", "hinh5_phan-bo-L.png", (17, 9))
    return 0


if __name__ == "__main__":
    sys.exit(main())
