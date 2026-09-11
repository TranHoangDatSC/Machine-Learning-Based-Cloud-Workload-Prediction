"""Ba baseline của `docs/protocol.md` mục 11 — mốc mà mọi con số GĐ3 so vào.

    naive           ŷ = y_t
    moving average  ŷ = trung bình y[t-6 .. t-1], cửa sổ 6, KHÔNG gồm điểm hiện tại
    seasonal naive  ŷ = y_{t-288}   (cùng giờ hôm trước)

**Không có yếu tố ngẫu nhiên nào** — không seed, không siêu tham số, không huấn
luyện. `research-plan.md` viết *"Chạy baseline trước tiên. Mọi con số về sau so với
nó."* Nên lệch một chữ số ở đây là **có lỗi**, không phải nhiễu, và một baseline sai
làm sai toàn bộ bảng kết quả mà không phép kiểm nào khác bắt được.

Hai cái đầu lấy thẳng từ ma trận đặc trưng
------------------------------------------

`y_t = lag_1 + diff_1` (vì `diff_1 = y_t − y_{t−1}` và `lag_1 = y_{t−1}`), còn moving
average **chính là** `roll_mean_6` — mục 8 đã chốt rolling chỉ tính trên quá khứ,
không gồm điểm hiện tại, đúng định nghĩa baseline này cần.

Lấy từ ma trận đặc trưng chứ không tính lại từ `data/processed/` là có chủ ý: khi con
số khớp thước đo của A (bản chỉ đọc `data/processed/`), phép so đó kiểm chéo được
**cả ma trận đặc trưng lẫn code baseline** cùng lúc (`gate-gd3.md` mục 1).

Cái thứ ba phải nối ngược về `data/processed/`
----------------------------------------------

`ŷ = y_{t-288}` **không tính được từ `data/features/`**: bộ 19 đặc trưng sâu nhất chỉ
tới `lag_24`. Nối theo khoá `(series_id, bucket − 288)`.

Ba điều protocol mục 11 cấm, ghi lại vì cả ba đều là cám dỗ có thật:

- **Không** thêm `lag_288` vào bộ đặc trưng — thêm một đặc trưng ngoài mục 8 là đổi
  giao thức, và không model nào cần nó, chỉ baseline này cần.
- **Không** siết luật dòng hợp lệ thành `t >= b0 + 288` — làm thế sẽ đổi cả chín neo
  số dòng đã kiểm chéo ở GĐ1 và GĐ2.
- Dòng không có `y_{t-288}` thì trả **NaN** và để phía gọi **báo tỉ lệ ra**. Không
  `ffill`, không lấp bằng `y_t`, không lặng lẽ bỏ.

Phần thiếu nằm gần như trọn trong train (288 bucket đầu mỗi chuỗi rơi vào 12,5% đầu
cửa sổ). Trên test — nơi mọi con số của paper được tính — chỉ E3 thiếu, khoảng 0,43%.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Cùng giờ hôm trước trên lưới 5 phút: 24 * 12 = 288 bucket (protocol mục 11).
SEASONAL_LAG = 288

# Cửa sổ của moving average (protocol mục 11), trùng với `roll_mean_6` của mục 8.
MA_WINDOW = 6

BASELINE_NAMES = ("naive", "ma6", "seasonal")


def y_hien_tai(X: pd.DataFrame) -> np.ndarray:
    """`y_t` dựng lại từ ma trận đặc trưng: `lag_1 + diff_1`.

    Không đọc `data/processed/` — nếu ma trận đặc trưng sai thì baseline phải sai
    theo, để phép so với thước đo của A bắt được.
    """
    thieu = [c for c in ("lag_1", "diff_1") if c not in X.columns]
    if thieu:
        raise ValueError(f"Ma trận đặc trưng thiếu cột {thieu} (protocol mục 8).")
    return (X["lag_1"].to_numpy("float64") + X["diff_1"].to_numpy("float64"))


def du_doan_naive(X: pd.DataFrame) -> np.ndarray:
    """`ŷ = y_t` — persistence. Mốc bắt buộc của mục 11."""
    return y_hien_tai(X)


def du_doan_ma6(X: pd.DataFrame) -> np.ndarray:
    """`ŷ` = trung bình `y[t-6 .. t-1]`, tức đúng cột `roll_mean_6` của mục 8.

    Cửa sổ **không** gồm điểm hiện tại — đó là quy ước rolling của mục 8, và cũng là
    định nghĩa moving average ở mục 11. Hai chỗ trùng nhau nên không cần tính lại.
    """
    if "roll_mean_6" not in X.columns:
        raise ValueError("Ma trận đặc trưng thiếu cột roll_mean_6 (protocol mục 8).")
    return X["roll_mean_6"].to_numpy("float64")


def du_doan_seasonal(
    X: pd.DataFrame, processed: pd.DataFrame, lag: int = SEASONAL_LAG
) -> np.ndarray:
    """`ŷ = y_{t-288}`, nối ngược về `data/processed/` theo `(series_id, bucket − lag)`.

    Parameters
    ----------
    X : pd.DataFrame
        Ma trận đặc trưng, cần `series_id` và `bucket`.
    processed : pd.DataFrame
        Bảng dài `data/processed/{env}.parquet`, cần `series_id`, `bucket`, `y`.
    lag : int, optional
        Mặc định 288 bucket = 24 giờ.

    Returns
    -------
    np.ndarray
        `NaN` ở dòng không có `y_{t-lag}` — hoặc vì `t − lag` nằm trước đầu cửa sổ,
        hoặc vì chính điểm đó là `NaN` trong `data/processed/`. **Không lấp.**
    """
    for c in ("series_id", "bucket"):
        if c not in X.columns:
            raise ValueError(f"Ma trận đặc trưng thiếu cột {c}.")
    for c in ("series_id", "bucket", "y"):
        if c not in processed.columns:
            raise ValueError(f"Bảng data/processed/ thiếu cột {c} (mục 6b).")

    tra_cuu = processed.set_index(["series_id", "bucket"])["y"]
    if not tra_cuu.index.is_unique:
        raise ValueError("data/processed/ có khoá (series_id, bucket) trùng lặp.")

    khoa = pd.MultiIndex.from_arrays(
        [X["series_id"].to_numpy(), X["bucket"].to_numpy("int64") - lag]
    )
    return tra_cuu.reindex(khoa).to_numpy("float64")


def du_doan(
    ten: str, X: pd.DataFrame, processed: pd.DataFrame | None = None
) -> np.ndarray:
    """Gọi baseline theo tên. `seasonal` bắt buộc có `processed`."""
    if ten == "naive":
        return du_doan_naive(X)
    if ten == "ma6":
        return du_doan_ma6(X)
    if ten == "seasonal":
        if processed is None:
            raise ValueError(
                "seasonal naive cần data/processed/ — bộ 19 đặc trưng không có lag_288 "
                "và protocol mục 11 cấm thêm vào."
            )
        return du_doan_seasonal(X, processed)
    raise ValueError(f"Baseline không rõ: {ten!r}. Có: {BASELINE_NAMES}.")
