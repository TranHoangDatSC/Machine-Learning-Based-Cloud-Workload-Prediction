"""Chia train/validation/test theo bucket, và rolling-origin 5 fold (mục 9, QĐ-013, QĐ-014).

Đầu vào là ma trận đặc trưng `data/features/{env}_h{h}.parquet` (22 cột, có
`series_id` và `bucket`) cùng horizon `h`. Đầu ra là **mặt nạ bool** hoặc **chỉ số**
— không bản sao dữ liệu, vì ma trận E1 h=1 đã 1,65 triệu dòng và mỗi lần sao chép
là một lần có thể sao chép nhầm.

Bốn quy ước, và lý do từng cái tồn tại
--------------------------------------

**1. Ranh giới tính theo bucket, không theo số dòng** (QĐ-013 điểm 1). Cửa sổ 8 ngày
là toàn cục theo môi trường (mục 7) nên ranh giới bucket là một lát cắt thời gian
*giống hệt nhau ở mọi chuỗi*. Chia theo số dòng hợp lệ thì chuỗi nhiều NaN sẽ có
test bắt đầu muộn hơn, và "chia theo thời gian" không còn đúng nghĩa.

**2. Một dòng thuộc tập `S` khi cả `t` VÀ `t+h` nằm trong `S`** (QĐ-013 điểm 2).
Dòng vắt qua ranh giới bị **loại**. Đây là chống rò rỉ, không phải thẩm mỹ: gán theo
`t` thôi thì dòng cuối tập train có target `y_{t+h}` rơi vào validation hoặc test,
và huấn luyện trên nó là cho model nhìn thấy nhãn của tập đánh giá.

**3. Tuyệt đối không shuffle** (mục 9). Mọi hàm ở đây làm việc trên trục bucket; không
chỗ nào gọi tới bộ sinh số ngẫu nhiên.

**4. Rolling-origin 5 fold, expanding** (QĐ-014 điểm 1). Luật purge ở điểm 2 áp
**trong từng fold**, và test `[1957, 2304)` không fold nào chạm tới.

Về `b0` — chỗ dễ sai nhất khi dùng module này
---------------------------------------------

Offset tính so với `b0` = bucket **nhỏ nhất của môi trường** (mục 7), đọc từ
`data/processed/{env}.parquet`. **Không** lấy `min(bucket)` của ma trận đặc trưng:
24 dòng đầu mỗi chuỗi không hợp lệ nên bucket nhỏ nhất ở đó là `b0 + 24`, và lấy
nhầm sẽ đẩy cả ba ranh giới đi 24 bucket mà không có gì báo lỗi. Vì vậy `b0` là
tham số **bắt buộc**; dùng `doc_b0()` để lấy đúng.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# Cửa sổ 8 ngày trên lưới 5 phút (protocol mục 7): 8 * 24 * 12 = 2304 bucket.
WINDOW_BUCKETS = 8 * 24 * 12

# QĐ-013 điểm 1. floor(0,70 * 2304) = 1612, floor(0,15 * 2304) = 345, còn lại là test.
TRAIN_FRAC = 0.70
VAL_FRAC = 0.15
N_TRAIN = int(WINDOW_BUCKETS * TRAIN_FRAC)
N_VAL = int(WINDOW_BUCKETS * VAL_FRAC)

# QĐ-014 điểm 1. Vùng validation rộng 345 bucket, chia 5 được 69 bucket mỗi fold.
N_FOLDS = 5

SPLIT_NAMES = ("train", "val", "test")
NHAN_LOAI = "loai"  # dòng vắt qua ranh giới, không thuộc tập nào

assert N_TRAIN == 1612, "QĐ-013 điểm 1 chốt train = [0, 1612)"
assert N_VAL == 345, "QĐ-013 điểm 1 chốt validation rộng 345 bucket"
assert N_VAL % N_FOLDS == 0, "QĐ-014 điểm 1 chia đều 345 bucket cho 5 fold"


def bucket_bounds() -> dict[str, tuple[int, int]]:
    """Ba ranh giới theo offset so với `b0`, nửa mở `[lo, hi)` — QĐ-013 điểm 1.

    Returns
    -------
    dict[str, tuple[int, int]]
        `{"train": (0, 1612), "val": (1612, 1957), "test": (1957, 2304)}`.
    """
    return {
        "train": (0, N_TRAIN),
        "val": (N_TRAIN, N_TRAIN + N_VAL),
        "test": (N_TRAIN + N_VAL, WINDOW_BUCKETS),
    }


def fold_bounds(n_splits: int = N_FOLDS) -> list[dict[str, tuple[int, int]]]:
    """Ranh giới của rolling-origin, **expanding** — QĐ-014 điểm 1.

    Train của fold `i` là `[0, bien[i])`, validation là `[bien[i], bien[i+1])`, với
    `bien` chia đều vùng validation. Train của fold sau chứa trọn train của fold
    trước; validation của fold nào cũng nằm **sau** train của chính nó.

    Parameters
    ----------
    n_splits : int, optional
        Số fold, mặc định 5 (`config/split.yaml: cv.n_splits`).

    Returns
    -------
    list[dict[str, tuple[int, int]]]
        Mỗi phần tử có khoá `train` và `val`. Với mặc định, biên là
        `1612, 1681, 1750, 1819, 1888, 1957`.
    """
    lo, hi = bucket_bounds()["val"]
    rong = hi - lo
    if rong % n_splits:
        raise ValueError(
            f"Vùng validation rộng {rong} bucket không chia hết cho {n_splits} fold."
        )
    buoc = rong // n_splits
    bien = [lo + i * buoc for i in range(n_splits + 1)]
    return [{"train": (0, bien[i]), "val": (bien[i], bien[i + 1])}
            for i in range(n_splits)]


def doc_b0(env: str, processed_dir: str | Path = "data/processed") -> int:
    """`b0` của môi trường: bucket nhỏ nhất trên **toàn bộ** chuỗi (mục 7).

    Đọc `data/processed/{env}.parquet` chứ không đọc ma trận đặc trưng — xem phần
    đầu tệp về lý do.
    """
    p = Path(processed_dir) / f"{env}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"Thiếu {p}; cần sản phẩm GĐ1 để biết b0 của {env}.")
    return int(pd.read_parquet(p, columns=["bucket"])["bucket"].min())


def offset(bucket: pd.Series | np.ndarray, b0: int) -> np.ndarray:
    """Offset của bucket so với `b0`, kiểu `int64`.

    Không kẹp và không lọc: giá trị ngoài `[0, 2304)` để nguyên cho phía gọi thấy.
    """
    return np.asarray(bucket, dtype="int64") - int(b0)


def _trong_khoang(off: np.ndarray, h: int, lo: int, hi: int) -> np.ndarray:
    """Luật QĐ-013 điểm 2: `lo <= t` **và** `t + h < hi`.

    `t < hi` suy ra được từ `t + h < hi` với `h >= 0`, và `t + h >= lo` suy ra từ
    `t >= lo` — nên hai bất đẳng thức này là đủ và không thừa.
    """
    return (off >= lo) & (off + h < hi)


def split_masks(off: np.ndarray, h: int) -> dict[str, np.ndarray]:
    """Ba mặt nạ bool cho `train`, `val`, `test` — đã purge dòng vắt ranh giới.

    Parameters
    ----------
    off : np.ndarray
        Offset gốc dự đoán `t`, lấy từ `offset()`.
    h : int
        Horizon tính bằng bucket (protocol mục 10 dùng 1, 6, 12).

    Returns
    -------
    dict[str, np.ndarray]
        Ba mặt nạ **rời nhau**; dòng không thuộc mặt nạ nào là dòng bị purge.
    """
    if h < 1:
        raise ValueError(f"Horizon phải >= 1, nhận {h}.")
    off = np.asarray(off, dtype="int64")
    return {ten: _trong_khoang(off, h, lo, hi)
            for ten, (lo, hi) in bucket_bounds().items()}


def mask_khoang(off: np.ndarray, h: int, lo: int, hi: int) -> np.ndarray:
    """Mặt nạ cho một khoảng bucket tuỳ ý, vẫn áp luật purge của QĐ-013 điểm 2.

    Dùng cho vùng huấn luyện không phải một trong ba tập chuẩn — ví dụ train + val.
    """
    if h < 1:
        raise ValueError(f"Horizon phải >= 1, nhận {h}.")
    return _trong_khoang(np.asarray(off, dtype="int64"), h, int(lo), int(hi))


def fit_mask(off: np.ndarray, h: int) -> np.ndarray:
    """Vùng huấn luyện của model **cuối cùng**: train + validation, `[0, 1957)`.

    QĐ-014 điểm 1: *"Expanding cũng khớp với cách model cuối cùng được huấn luyện —
    trên toàn bộ train + validation."* Luật purge vẫn áp, nên `t + h < 1957` và
    không dòng nào có target rơi vào test.
    """
    return mask_khoang(off, h, 0, N_TRAIN + N_VAL)


def fold_masks(off: np.ndarray, h: int,
               n_splits: int = N_FOLDS) -> list[dict[str, np.ndarray]]:
    """Mặt nạ train/val của từng fold rolling-origin — QĐ-014 điểm 1.

    Luật purge áp **trong từng fold**: dòng thuộc train của fold khi cả `t` và `t+h`
    nằm trong khoảng train của fold đó, tương tự cho validation.
    """
    if h < 1:
        raise ValueError(f"Horizon phải >= 1, nhận {h}.")
    off = np.asarray(off, dtype="int64")
    return [{ten: _trong_khoang(off, h, lo, hi) for ten, (lo, hi) in bien.items()}
            for bien in fold_bounds(n_splits)]


def gan_nhan(off: np.ndarray, h: int) -> np.ndarray:
    """Nhãn tập của từng dòng: `train | val | test | loai`.

    Tiện cho việc đếm và cho báo cáo; phần tính toán nên dùng `split_masks()` để
    khỏi so chuỗi ký tự trên hàng triệu dòng.
    """
    mn = split_masks(off, h)
    nhan = np.full(len(np.asarray(off)), NHAN_LOAI, dtype=object)
    for ten in SPLIT_NAMES:
        nhan[mn[ten]] = ten
    return nhan


def split_indices(off: np.ndarray, h: int) -> dict[str, np.ndarray]:
    """Như `split_masks()` nhưng trả về chỉ số vị trí, cho phía cần `iloc`."""
    return {ten: np.flatnonzero(m) for ten, m in split_masks(off, h).items()}


def dem_dong(off: np.ndarray, h: int) -> dict[str, int]:
    """Số dòng mỗi tập, kèm `loai` — đối chiếu với `gate-gd3.md` mục 2.2."""
    mn = split_masks(off, h)
    dem = {ten: int(m.sum()) for ten, m in mn.items()}
    dem[NHAN_LOAI] = int(len(np.asarray(off)) - sum(dem.values()))
    return dem
