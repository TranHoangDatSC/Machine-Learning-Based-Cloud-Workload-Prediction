"""Bốn đặc trưng lịch suy từ `bucket` (protocol mục 8, QĐ-010).

`bucket * 300` là **số giây**. Với E1 và E2 đó là epoch UTC thật; với E3 đó là giây
kể từ lúc bắt đầu trace Alibaba (`b0 = 0`), **không phải epoch** — `hour` của E3
mang nghĩa "giờ kể từ đầu trace", pha chưa biết, và `dow` không diễn giải được theo
lịch tuần.

QĐ-010 chốt: **công thức giống hệt nhau cho cả ba môi trường**, khác biệt duy nhất
là ý nghĩa. Nên ở đây không rẽ nhánh theo `env`, và tuyệt đối không bịa ngày bắt đầu
cho Alibaba. Chỗ phải nói ra sự khác biệt đó là log và mục Limitations, không phải
code.

Hai điều kiện ngầm mà cả bốn đặc trưng dựa vào:

- `bucket` là số hiệu **tuyệt đối** `floor(t / 300)`, không đánh số lại từ 0 theo
  từng chuỗi. Đánh số lại làm `hour_sin` vô nghĩa mà không báo lỗi gì.
- Gốc `dow`: epoch 1970-01-01 là thứ Năm, nên `((t // 86400) + 4) % 7` cho 0 là thứ
  Hai. Quy ước nào cũng được, miễn hai bản hiện thực dùng chung một gốc.
"""

import numpy as np
import pandas as pd

from cwp.features.spec import DOW_EPOCH_OFFSET, GRID_SECONDS


def bucket_to_seconds(bucket) -> np.ndarray:
    """Đổi số hiệu bucket sang giây. Epoch với E1/E2, giây-từ-đầu-trace với E3."""
    return np.asarray(bucket, dtype="int64") * GRID_SECONDS


def hour_of_day(bucket) -> np.ndarray:
    """Giờ trong ngày, 0–23. Với E3 là giờ kể từ đầu trace, pha chưa biết."""
    return (bucket_to_seconds(bucket) // 3600) % 24


def day_of_week(bucket) -> np.ndarray:
    """Thứ trong tuần, 0 = thứ Hai (QĐ-010). Với E3 thì không diễn giải được."""
    return ((bucket_to_seconds(bucket) // 86400) + DOW_EPOCH_OFFSET) % 7


def _sin_cos(gia_tri: np.ndarray, chu_ky: int) -> tuple[np.ndarray, np.ndarray]:
    """Mã hoá tuần hoàn: hai thời điểm cách nhau đúng một chu kỳ ra cùng một cặp."""
    goc = 2 * np.pi * gia_tri / chu_ky
    return np.sin(goc), np.cos(goc)


def add_calendar_features(df: pd.DataFrame, out: pd.DataFrame) -> pd.DataFrame:
    """Thêm `hour_sin, hour_cos, dow_sin, dow_cos` vào `out`.

    Parameters
    ----------
    df : pd.DataFrame
        Bảng dài có cột `bucket`.
    out : pd.DataFrame
        Bảng đích, cùng index với `df`. Bị sửa tại chỗ.

    Returns
    -------
    pd.DataFrame
        Chính `out`, để nối chuỗi lời gọi.
    """
    bucket = df["bucket"]
    out["hour_sin"], out["hour_cos"] = _sin_cos(hour_of_day(bucket), 24)
    out["dow_sin"], out["dow_cos"] = _sin_cos(day_of_week(bucket), 7)
    return out
