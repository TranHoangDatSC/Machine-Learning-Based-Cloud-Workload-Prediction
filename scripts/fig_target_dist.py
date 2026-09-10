"""Hình phân phối CPU% ba môi trường — điều kiện qua cổng GĐ2 (Bước 5).

    python scripts/fig_target_dist.py

Sinh vào `results/figures/gd2/`: ba tệp `.png` **mỗi tệp đúng một hình**
(`01_ecdf-truc-tuyen-tinh`, `02_ecdf-truc-symlog`, `03_bang-phan-vi`),
`gd2_phan-phoi-cpu.pdf` gộp cả ba kèm trang diễn giải, và
`fig_target_dist.caption.md`.

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

from cwp.viz import xuat

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


def ve_panel(ax, xs, duong, *, symlog: bool, tieu_de: str | None = None):
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
    if tieu_de:
        ax.set_title(tieu_de, fontsize=9.5, color=MUC, loc="left", pad=8)


def chu_thich_tran(ax, duong, xs):
    """Chỉ vào bước nhảy tại trần 100 — QĐ-011 điểm 3 đòi hình phải nói ra chỗ này."""
    i_truoc = int(np.searchsorted(xs, 100.0 - 1e-9))
    tran = {e: 1.0 - duong[e][i_truoc] for e in ENVS}

    ax.annotate(
        f"Trần clip 100: {tran['E1']:.2%} điểm của E1\n"
        f"và {tran['E2']:.2%} của E2 dồn vào đây.\nE3 không chạm trần.",
        # Vùng trống thật khi panel đứng một mình: với x > 60 cả ba đường đều trên
        # y = 0,9, còn chú giải chiếm y < 0,25. Đặt tâm hộp ở 0,38 để nó không đè lên
        # đường trung vị y = 0,5 — ở tỉ lệ khung rộng hơn thì 0,46 là vừa chạm.
        xy=(100, 1 - tran["E1"] / 2), xycoords="data",
        xytext=(62, 0.38), textcoords="data",
        fontsize=8, color=MUC_PHU, ha="left", va="center",
        arrowprops=dict(arrowstyle="->", color=MUC_MO, linewidth=0.9,
                        connectionstyle="arc3,rad=0.22"),
        bbox=dict(boxstyle="round,pad=0.45", facecolor=NEN,
                  edgecolor="#d4d3ce", linewidth=0.7),
        zorder=5,
    )
    return tran


def ve_bang(ax, bang: pd.DataFrame):
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



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--out", default="results/figures/gd2")
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

    # Vẽ một lần vào axes tạm để lấy tỉ lệ chạm trần, dùng cho caption và diễn giải.
    tam = plt.figure()
    tran = chu_thich_tran(tam.add_subplot(), duong, xs)
    plt.close(tam)

    panels = [
        xuat.Panel("01_ecdf-truc-tuyen-tinh", "ECDF phân phối CPU%, trục tuyến tính",
                   (7.0, 4.8), lambda ax: _ve_a(ax, xs, duong)),
        xuat.Panel("02_ecdf-truc-symlog", "ECDF phân phối CPU%, trục symlog",
                   (7.0, 4.8), lambda ax: _ve_b(ax, xs, duong)),
        xuat.Panel("03_bang-phan-vi", "Bảng phân vị CPU% sau tiền xử lý",
                   (6.2, 4.4), lambda ax: ve_bang(ax, bang)),
    ]

    anh, pdf = xuat.xuat_bo_hinh(
        panels, out_dir, "gd2_phan-phoi-cpu.pdf",
        tieu_de="Phân phối CPU% của ba môi trường sau tiền xử lý",
        phu=("Hàm phân phối tích luỹ thực nghiệm (ECDF), gộp mọi điểm quan sát của "
             "các chuỗi còn lại sau bộ lọc, trong cửa sổ 8 ngày. Sinh bằng "
             "`python scripts/fig_target_dist.py` — không sửa tay tệp ảnh nào."),
        dien_giai=dien_giai(bang, tran),
        chu_thich=chu_thich_panel(bang, tran),
        dpi=a.dpi)

    cap = out_dir / "fig_target_dist.caption.md"
    cap.write_text(caption(bang, tran), encoding="utf-8")

    print()
    for p in list(anh) + [pdf, cap]:
        print(f"Đã ghi: {p.relative_to(ROOT)}")
    print("\nMỗi .png chứa đúng MỘT hình, tiêu đề mô tả thuần — dán thẳng vào bài.")
    print("Tệp .pdf gộp cả ba hình và phần diễn giải — để đọc và để duyệt.")
    print("\nA duyệt bằng mắt: mở hình, kiểm cả ba đường đọc được và không đường "
          "nào bị ép sát mép.")
    return 0


def _ve_a(ax, xs, duong):
    """Panel ECDF tuyến tính, kèm chú thích trần — trần là một phần của kết quả."""
    ve_panel(ax, xs, duong, symlog=False)
    chu_thich_tran(ax, duong, xs)
    xuat.chu_giai_duoi(ax)


def _ve_b(ax, xs, duong):
    """Panel ECDF symlog. Đứng một mình nên phải tự mang chú giải."""
    ve_panel(ax, xs, duong, symlog=True)
    xuat.chu_giai_duoi(ax)


def dien_giai(bang, tran) -> list[tuple[str, str]]:
    """Trang diễn giải của PDF — thứ trước đây nằm trong panel (c) của ảnh ghép."""
    return [
        ("Đọc hình này thế nào",
         "Trục tung là tỉ lệ tích luỹ: tại hoành độ x, đường của một môi trường cho "
         "biết bao nhiêu phần trăm số điểm của môi trường đó có CPU% nhỏ hơn hoặc "
         "bằng x. Cắt ngang tại 0,5 sẽ ra trung vị. Đường càng dịch sang phải thì "
         "môi trường càng chạy ở mức tải cao."),
        ("Vì sao ECDF chứ không phải histogram",
         "Trung vị của E1 và E2 dưới 2%, của E3 gần 38%. Trên một trục mật độ tuyến "
         "tính chung, toàn bộ khối lượng của E1/E2 rơi vào cột đầu tiên và hình "
         "không nói được gì. ECDF gỡ được vì trục tung là xác suất tích luỹ nên mỗi "
         "đường bắt buộc đi từ 0 lên 1 — không môi trường nào bị nén. Kèm ba lợi "
         "thế: không phải chọn độ rộng bin nên không có tham số nào để vô tình "
         "chỉnh; khối điểm bị kẹp ở trần hiện thành một bước nhảy nhìn thấy được; "
         "và đọc thẳng được phân vị."),
        ("Vì sao có hai trục",
         "Hình 1 dùng trục tuyến tính, trả lời câu hỏi của RQ3: ba môi trường nằm ở "
         "ba mức tải khác nhau. Hình 2 dùng trục symlog để phóng to vùng dưới 1%, "
         "nơi trung vị của E1 và E2 thực sự nằm; trên trục tuyến tính vùng đó chỉ "
         "chiếm vài pixel sát trục tung. Symlog là trục log nhưng vẫn hiển thị được "
         "giá trị 0, nhờ một đoạn tuyến tính quanh gốc."),
        ("Không dùng trục phụ",
         "Hai thang y trên cùng một hình cho phép đặt hai đường cạnh nhau ở bất kỳ "
         "vị trí tương đối nào, nên hình sẽ nói được điều mà dữ liệu không nói. Đây "
         "là lỗi biểu đồ bị phê bình nhiều nhất, và bộ hình này không dùng nó ở đâu."),
        ("Ba điều phải đọc ra",
         f"Một, mức tải lệch nhau — trung vị {bang.loc['E1','p50']:.2f}% (E1) và "
         f"{bang.loc['E2','p50']:.2f}% (E2) so với {bang.loc['E3','p50']:.2f}% (E3); "
         "ba đường gần như không giao nhau. Hai, trần 100 là kiểm duyệt và nó bất "
         f"đối xứng: {tran['E1']:.2%} điểm của E1 và {tran['E2']:.2%} của E2 nằm "
         "đúng tại 100 trong khi E3 là 0%, và phân vị 95 của E1 chính là trần. Ba, "
         "quần thể là các chuỗi ĐÃ LỌC — bộ lọc bỏ 36,3% chuỗi E1 và 39,4% chuỗi E2 "
         "nhưng chỉ 0,4% chuỗi E3, và cắt gần như hoàn toàn ở đuôi dưới, nên hình mô "
         "tả phần VM còn hoạt động chứ không mô tả Bitbrains nói chung."),
    ]


def chu_thich_panel(bang, tran) -> dict[str, str]:
    return {
        "01_ecdf-truc-tuyen-tinh":
            "Ba mức tải tách hẳn nhau. Bước nhảy thẳng đứng ở mép phải là hệ quả của "
            f"bước clip: {tran['E1']:.2%} điểm của E1 và {tran['E2']:.2%} của E2 nằm "
            "đúng tại trần 100, E3 không có điểm nào.",
        "02_ecdf-truc-symlog":
            "Cùng dữ liệu, trục hoành symlog để phóng to vùng dưới 1%. E1 và E2 gần "
            "trùng nhau trên toàn dải; E3 tách hẳn sang phải.",
        "03_bang-phan-vi":
            "Số liệu sinh bằng `python scripts/describe_gd2.py --env all`, đọc từ "
            "`results/tables/describe_gd2.csv` chứ không tính lại — hình và bảng của "
            "bài báo vì thế không thể lệch nhau.",
    }


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
