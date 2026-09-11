"""BẢN MỒI CỦA A — **ĐỪNG ĐỌC NẾU BẠN ĐANG VIẾT `normalize.py`.**

Đây là một bản `cwp/preprocess/normalize.py` **đúng**, chỉ tồn tại để
`tests/test_check_gd4.py` có cái cho loại C của `check_gd4.py` gọi trong thế giới giả
lập. Nó **không** nằm trong đường chạy của dự án và không được import từ `src/`.

Vì sao nó ở đây chứ không ở trong `tests/`: QĐ-014 ghi lại rằng
`tests/test_check_gd3.py` chứa sẵn một bản `metrics.py`, và nói thẳng *"nếu sau này
muốn siết, đưa bản mồi ấy ra một tệp riêng ngoài tests/"*. GĐ4 siết, vì ở đây bản mồi
là **trọn vẹn** thứ mà phiên hiện thực phải tự viết — đọc nó là mất luôn loại A của
cổng GĐ4.

Danh sách tệp phiên hiện thực không được đọc, ghi ở `brief-gd4-b.md` Bước 0.
"""

import numpy as np

N_TRAIN = 1612


def thong_ke_train(y):
    tr = np.asarray(y, dtype="float64")[:N_TRAIN]
    return float(np.nanmean(tr)), float(np.nanstd(tr, ddof=1))


def bien_doi(y, mode):
    y = np.asarray(y, dtype="float64")
    if mode == "N0":
        return y.copy()
    if mode == "N1":
        mu, sd = thong_ke_train(y)
        if not np.isfinite(sd) or sd == 0.0:
            return np.full_like(y, np.nan)
        return (y - mu) / sd
    if mode == "N2":
        d = np.full_like(y, np.nan)
        d[1:] = y[1:] - y[:-1]
        return d
    raise ValueError(mode)


def map_nguoc(yhat, y, mode):
    yhat = np.asarray(yhat, dtype="float64")
    y = np.asarray(y, dtype="float64")
    if mode == "N0":
        return yhat
    if mode == "N1":
        mu, sd = thong_ke_train(y)
        return yhat * sd + mu
    if mode == "N2":
        return y + yhat
    raise ValueError(mode)
