"""Sinh danh sách 500 máy Alibaba cố định cho E3.

Vì sao cần đóng băng
--------------------
protocol mục 3 ghi "lấy ngẫu nhiên 100 máy mỗi tầng, random_state = 42". Chưa đủ.
`.sample()` chọn theo VỊ TRÍ, mà vị trí phụ thuộc THỨ TỰ danh sách máy — thứ tự đó
lại phụ thuộc cách hiện thực xây bảng trung bình.

Ngày 2026-09-09, A và B chạy hai bản hiện thực đều đúng đặc tả nhưng chỉ trùng nhau
56/500 máy. Thống kê gộp vẫn lệch dưới 0,05% (phép phân tầng làm đúng việc của nó),
nhưng hai bên đang đo hai quần thể khác nhau nên không kiểm chứng được lẫn nhau.

Cách chuẩn hoá ở đây
--------------------
1. Sắp xếp theo `machine_id` — thứ tự canonical, không phụ thuộc thứ tự quét tệp
2. Xếp tầng theo rank của CPU trung bình, 5 tầng
3. Lấy 100 máy mỗi tầng, random_state = 42
4. Ghi ra tệp đã sắp xếp, commit vào repo

Từ đó mọi lần chạy trên mọi máy đều dùng đúng một tập, và người đọc paper dựng lại
được. Xem decisions.md QĐ-009.

    python scripts/freeze_e3_sample.py
"""

import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "Alibaba-Cluster-Trace" / "machine_usage.csv"
OUT = ROOT / "config" / "e3_machines.txt"

SEED = 42
STRATA = 5
N_TOTAL = 500
COLS = ["machine_id", "time_stamp", "cpu_util_percent"]


def machine_means(path, chunksize=5_000_000):
    """CPU trung bình từng máy. Một lượt quét."""
    tot, cnt = {}, {}
    for ch in pd.read_csv(path, names=COLS, usecols=[0, 1, 2], chunksize=chunksize):
        g = ch.groupby("machine_id")["cpu_util_percent"].agg(["sum", "count"])
        for m, r in g.iterrows():
            tot[m] = tot.get(m, 0.0) + r["sum"]
            cnt[m] = cnt.get(m, 0) + r["count"]
    return pd.Series({m: tot[m] / cnt[m] for m in tot if cnt[m] > 0})


def choose(means):
    """Chọn mẫu phân tầng theo thứ tự canonical."""
    means = means.sort_index()                       # <- mấu chốt
    strata = pd.qcut(means.rank(method="first"), STRATA, labels=False)
    per = N_TOTAL // STRATA
    chosen = []
    for k in range(STRATA):
        pool = means.index[strata == k]
        chosen.extend(pd.Series(list(pool)).sample(per, random_state=SEED).tolist())
    return sorted(chosen)


def main():
    if not SRC.exists():
        print(f"Không thấy {SRC}")
        return 1

    print("Quét toàn bộ machine_usage.csv để tính CPU trung bình từng máy...")
    means = machine_means(SRC)
    print(f"  {len(means)} máy")

    chosen = choose(means)
    sel = means.loc[chosen]
    print(f"  đã chọn {len(chosen)} máy")
    print(f"  CPU trung bình của mẫu : {sel.mean():.4f}")
    print(f"  CPU trung bình toàn bộ : {means.mean():.4f}")
    print(f"  lệch                   : {abs(sel.mean() - means.mean()):.4f} điểm")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "# 500 máy Alibaba dùng cho E3 — ĐÃ ĐÓNG BĂNG, xem decisions.md QĐ-009",
        "#",
        "# Sinh bởi: scripts/freeze_e3_sample.py",
        "# Quy tắc : sort theo machine_id -> xếp tầng theo rank CPU trung bình,",
        "#           5 tầng x 100 máy, random_state = 42",
        "#",
        "# KHÔNG sinh lại tệp này. Mọi lần chạy E3 phải đọc đúng danh sách ở đây,",
        "# nếu không A và B sẽ đo hai quần thể khác nhau.",
        "",
    ]
    OUT.write_text("\n".join(header + chosen) + "\n", encoding="utf-8")
    print(f"\nĐã ghi {OUT}")
    return 0


def load_frozen(path=OUT):
    """Đọc danh sách đã đóng băng. Dùng bởi reference_gd1.py và build.py."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Không thấy {path}. Chạy scripts/freeze_e3_sample.py, "
            "hoặc git pull nếu tệp đã được commit.")
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
