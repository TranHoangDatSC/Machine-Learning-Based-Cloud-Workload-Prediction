"""Bảng thống kê mô tả ba môi trường sau tiền xử lý (GĐ2 Bước 4).

    python scripts/describe_gd2.py --env all

Tính trên `data/processed/{env}.parquet`, chỉ các chuỗi được `catalog.parquet` đánh
`kept`, trong cửa sổ 8 ngày. Ghi ra `results/tables/describe_gd2.{csv,md}`.

**Quần thể được mô tả — QĐ-011 điểm 2.** Đây là **phân phối gộp của `y`**, gọi tên
là *"CPU% sau tiền xử lý"*. **Không phải** cột `target` của ma trận đặc trưng. Ba lý
do đã chốt: nó không phụ thuộc horizon nên một bảng dùng chung cho cả ba `h`; nó đã
được hai bản hiện thực độc lập kiểm chéo ở GĐ1 lệch 0,000%; và phần Dữ liệu của
paper mô tả dữ liệu chứ không mô tả một dẫn xuất theo `h`.

Thống kê của cột `target` là chuyện khác, thuộc phần Thiết lập thí nghiệm, và đã có
sẵn `target_mean_h1/h6/h12` trong `results/tables/reference_gd2.json`.

Hai cột ngoài danh sách của phiếu giao việc, thêm vì QĐ-011 và protocol mục 6 đòi:

- `pct_bang_100` — tỉ lệ điểm nằm đúng tại trần clip. QĐ-011 điểm 3: đây là kiểm
  duyệt, và nó bất đối xứng giữa đúng ba môi trường đang được đem so sánh.
- `pct_noi_suy` — protocol mục 6 liệt nó vào danh sách **bắt buộc báo cáo**, vì nội
  suy là can thiệp vào dữ liệu.

Cuối lệnh script đối chiếu mean/p50/std với ba cột đã biết trước ở
`research-log/gate-gd2.md` mục 2.2, và thoát 1 nếu lệch quá 2%. Đối chiếu là để
**báo**, không phải để sửa: lệch nghĩa là đọc sai tệp hoặc lọc nhầm, và chỗ cần sửa
là cách hiện thực chứ không phải đầu ra.
"""

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
ENVS = ["E1", "E2", "E3"]

# gate-gd2.md mục 2.2 — đã kiểm chéo giữa A và B ở GĐ1, lệch 0,000%.
# Chỉ để đối chiếu SAU khi tính. Không có dòng mã nào dưới đây đọc bảng này.
NEO = {
    "E1": {"mean": 13.6352, "p50": 1.7833, "std": 27.9530},
    "E2": {"mean": 9.2199, "p50": 1.7667, "std": 21.4265},
    "E3": {"mean": 38.0123, "p50": 37.8333, "std": 14.9522},
}
NGUONG = 0.02  # 2%, theo brief-gd2-b.md Bước 4

COT = [
    ("env", "Môi trường"),
    ("so_chuoi", "Số chuỗi"),
    ("so_diem", "Số điểm"),
    ("mean", "Trung bình"),
    ("std", "Độ lệch chuẩn"),
    ("min", "Nhỏ nhất"),
    ("p10", "p10"),
    ("p25", "p25"),
    ("p50", "Trung vị"),
    ("p75", "p75"),
    ("p90", "p90"),
    ("p95", "p95"),
    ("max", "Lớn nhất"),
    ("pct_nan", "Tỉ lệ NaN %"),
    ("pct_bang_100", "Điểm bằng 100 %"),
    ("pct_noi_suy", "Tỉ lệ nội suy %"),
]


def mo_ta_mot_moi_truong(env: str, proc_dir: Path, cat: pd.DataFrame) -> dict:
    """Một dòng thống kê cho một môi trường."""
    f = proc_dir / f"{env}.parquet"
    if not f.exists():
        raise SystemExit(
            f"Thiếu {f}. Chạy tiền xử lý GĐ1 trước: "
            "python -m cwp.preprocess.build --env all"
        )

    d = pd.read_parquet(f, columns=["series_id", "y", "is_interp"])
    giu = set(cat[(cat["env"] == env) & cat["kept"]]["series_id"])
    co = set(d["series_id"].unique())

    # Hợp đồng GĐ1 → GĐ2: data/processed/ chỉ chứa chuỗi được giữ. Kiểm chứ không
    # lặng lẽ lọc — lệch ở đây nghĩa là hai sản phẩm của GĐ1 không nhất quán với
    # nhau, và mọi con số dưới đây sẽ mô tả một quần thể không ai định nghĩa.
    if co != giu:
        thua, thieu = sorted(co - giu)[:3], sorted(giu - co)[:3]
        raise SystemExit(
            f"{env}: data/processed/ không khớp catalog.kept — "
            f"thừa {len(co - giu)} chuỗi {thua}, thiếu {len(giu - co)} chuỗi {thieu}. "
            "Sinh lại cả hai bằng một lệnh: python -m cwp.preprocess.build --env all"
        )

    y = d["y"].to_numpy()
    sach = y[~np.isnan(y)]
    # p10 và p90 ngoài danh sách của phiếu: bảng "quần thể thô" trong
    # docs/data-card.md dùng p10/p25/p50/p75/p90, nên thiếu hai phân vị này thì
    # không so được hai quần thể với nhau từng dòng một.
    q = np.percentile(sach, [10, 25, 50, 75, 90, 95])

    return {
        "env": env,
        "so_chuoi": len(giu),
        "so_diem": len(d),
        "mean": round(float(sach.mean()), 4),
        "std": round(float(sach.std(ddof=1)), 4),
        "min": round(float(sach.min()), 4),
        "p10": round(float(q[0]), 4),
        "p25": round(float(q[1]), 4),
        "p50": round(float(q[2]), 4),
        "p75": round(float(q[3]), 4),
        "p90": round(float(q[4]), 4),
        "p95": round(float(q[5]), 4),
        "max": round(float(sach.max()), 4),
        "pct_nan": round(100 * float(np.isnan(y).mean()), 4),
        "pct_bang_100": round(100 * float((sach >= 100).mean()), 4),
        "pct_noi_suy": round(100 * int(d["is_interp"].sum()) / len(sach), 4),
    }


def ghi_markdown(df: pd.DataFrame, dich: Path) -> None:
    """Bảng xoay ngang, một cột mỗi môi trường — dạng đọc được trong paper."""
    t = df.set_index("env").T
    dong = [
        "# CPU% sau tiền xử lý — thống kê mô tả",
        "",
        "Sinh bằng `python scripts/describe_gd2.py --env all`. Không sửa tay.",
        "",
        "Quần thể: mọi điểm `y` không NaN của các chuỗi được giữ, trong cửa sổ 8 ngày",
        "(QĐ-011 điểm 2). **Không phải** cột `target` của ma trận đặc trưng — thống kê",
        "của cột đó ở `results/tables/reference_gd2.json`, khoá `target_mean_h*`.",
        "",
        "| Chỉ số | " + " | ".join(t.columns) + " |",
        "|---|" + "---:|" * len(t.columns),
    ]
    nhan = dict(COT)
    for khoa in t.index:
        gia_tri = []
        for env in t.columns:
            v = t.loc[khoa, env]
            gia_tri.append(f"{int(v):,}" if khoa in ("so_chuoi", "so_diem")
                           else f"{v:.4f}")
        dong.append(f"| {nhan.get(khoa, khoa)} | " + " | ".join(gia_tri) + " |")

    dong += [
        "",
        "Ba điều phải đọc kèm bảng này:",
        "",
        "1. **Hiệu ứng chọn lọc.** Bộ lọc `gan_chet` bỏ 36,3% chuỗi E1 và 39,4% chuỗi",
        "   E2 nhưng chỉ 0,4% chuỗi E3, và cắt gần như hoàn toàn ở đuôi dưới. Trung",
        "   bình CPU% của E1 vì thế tăng từ 6,75 (quần thể thô) lên giá trị ở bảng",
        "   này. Phát biểu phải nói trên quần thể đã lọc, không nói trên \"Bitbrains\".",
        "2. **Trần 100 là kiểm duyệt, và bất đối xứng.** Xem dòng *Điểm bằng 100 %*:",
        "   E1 và E2 có, E3 không. Phân vị 95 của E1 chính là trần.",
        "3. **E3 thiếu nhiều hơn hẳn.** Xem dòng *Tỉ lệ NaN %*.",
        "",
        "Chi tiết: `docs/data-card.md` mục *Sau tiền xử lý*, và QĐ-011.",
        "",
    ]
    dich.write_text("\n".join(dong), encoding="utf-8")


def doi_chieu(df: pd.DataFrame) -> int:
    """So mean/p50/std với ba cột đã biết trước ở gate-gd2.md mục 2.2."""
    print()
    print("─" * 70)
    print("ĐỐI CHIẾU với gate-gd2.md mục 2.2 (ngưỡng 2%)")
    print("─" * 70)
    print(f"{'':<4} {'chỉ số':<8} {'đo được':>12} {'neo':>12} {'lệch':>9}")

    lech = 0
    for _, r in df.iterrows():
        neo = NEO.get(r["env"])
        if neo is None:
            continue
        for k in ("mean", "p50", "std"):
            got, want = float(r[k]), neo[k]
            rel = abs(got - want) / abs(want) if want else 0.0
            xau = rel > NGUONG
            lech += xau
            print(f"{r['env']:<4} {k:<8} {got:>12.4f} {want:>12.4f} "
                  f"{rel:>8.4%}{' ← LỆCH' if xau else ''}")
    return lech


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--out", default="results/tables")
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    proc_dir = ROOT / a.processed
    cat_path = ROOT / a.catalog
    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if not cat_path.exists():
        raise SystemExit(f"Thiếu {cat_path} — cần catalog để biết chuỗi nào được giữ.")
    cat = pd.read_parquet(cat_path)

    print()
    print("THỐNG KÊ MÔ TẢ — CPU% sau tiền xử lý (QĐ-011 điểm 2)")
    print(f"nguồn : {proc_dir}  (chỉ chuỗi catalog.kept)")
    print(f"đích  : {out_dir}")
    print()

    df = pd.DataFrame([mo_ta_mot_moi_truong(e, proc_dir, cat) for e in envs])

    nhan = dict(COT)
    t = df.set_index("env").T
    print(f"{'':<20}" + "".join(f"{c:>14}" for c in t.columns))
    for khoa in t.index:
        v = [f"{int(t.loc[khoa, c]):,}" if khoa in ("so_chuoi", "so_diem")
             else f"{t.loc[khoa, c]:.4f}" for c in t.columns]
        print(f"{nhan.get(khoa, khoa):<20}" + "".join(f"{x:>14}" for x in v))

    # Chạy từng môi trường ghi ra tên khác. Nếu không, `--env E2` sẽ lặng lẽ ghi đè
    # bảng ba môi trường bằng một dòng duy nhất, và tệp trong results/tables/ trở
    # thành thứ không ai biết được sinh bằng lệnh nào — đúng loại lỗi mà cột
    # `built_on`/`built_at` của catalog sinh ra để chặn (protocol mục 6b).
    hau_to = "" if a.env == "all" else f"_{a.env}"
    csv_path = out_dir / f"describe_gd2{hau_to}.csv"
    md_path = out_dir / f"describe_gd2{hau_to}.md"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    ghi_markdown(df, md_path)
    print()
    print(f"Đã ghi: {csv_path.relative_to(ROOT)}")
    print(f"Đã ghi: {md_path.relative_to(ROOT)}")

    if a.env != "all":
        print()
        print("Đây là bảng MỘT môi trường, dùng để soi nhanh khi đang làm.")
        print("Bảng chuẩn cho data card và paper là describe_gd2.csv/.md, "
              "chỉ sinh bằng --env all.")
        return 0

    lech = doi_chieu(df)
    print()
    if lech:
        print(f"CHƯA ĐẠT — {lech} chỉ số lệch quá {NGUONG:.0%}.")
        print("Nghi đọc sai tệp hoặc lọc nhầm quần thể. Sửa cách hiện thực, "
              "KHÔNG sửa đầu ra cho khớp số.")
        return 1
    print("Cả 9 chỉ số khớp neo trong ngưỡng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
