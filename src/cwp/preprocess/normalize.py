"""Ba chế độ chuẩn hoá của Thí nghiệm B (protocol mục 14, QĐ-016).

    N0  giữ nguyên CPU%, thang 0–100
    N1  z-score từng chuỗi:  z = (y − mu) / sd
    N2  sai phân một bước:   d_t = y_t − y_{t−1}

Ba hàm công khai làm việc ở **mức một chuỗi đơn**, cố ý: chúng kiểm tay được và test
được mà không cần dữ liệu thật. Phần chạy trên bảng dài `data/processed/` xây **lên
trên** chúng, đừng viết song song — hai đường đi là hai chỗ để lệch nhau.

Ba điều dễ sai nhất, ghi ra đây vì cả ba đều **không làm chương trình báo lỗi**:

1. **`mu`/`sd` lấy trên cửa sổ train của CHÍNH chuỗi đó**, bucket `[0, 1612)` — không
   phải toàn chuỗi, không phải thống kê của môi trường nguồn (QĐ-016 điểm 1). Tính
   trên toàn chuỗi là **rò rỉ**: nó dùng thông tin của test để chuẩn hoá train, và kết
   quả sẽ đẹp bất thường.
2. **`sd = 0` thì N1 không xác định** — trả `NaN` để chỗ gọi đếm và báo. Không thay
   bằng 0, không cộng epsilon. Một chuỗi hằng thì z-score của nó vô nghĩa, che đi là
   bịa dữ liệu.
3. **Phải map ngược về thang CPU% gốc trước khi tính bất kỳ chỉ số nào** (mục 12).
   So MAE của z với MAE của CPU% là so hai đơn vị khác nhau.
"""

from __future__ import annotations

import numpy as np

# QĐ-013 điểm 1: train là bucket [0, 1612) tính theo offset so với b0 của môi trường.
# Ở mức một chuỗi đơn thì đó đúng là 1612 phần tử đầu của mảng.
TRAIN_END = 1612

MODES = ("N0", "N1", "N2")

__all__ = ["TRAIN_END", "MODES", "thong_ke_train", "bien_doi", "map_nguoc",
           "chuan_hoa_duoc"]


def _mang(y) -> np.ndarray:
    return np.asarray(y, dtype="float64")


def _kiem_mode(mode: str) -> str:
    m = str(mode).strip().upper()
    if m not in MODES:
        raise ValueError(f"Chế độ không hợp lệ: {mode!r}. Chỉ có {MODES}.")
    return m


# ------------------------------------------------------------ thống kê train

def thong_ke_train(y) -> tuple[float, float]:
    """`(mu, sd)` trên cửa sổ train `[0, 1612)` của chuỗi, `ddof = 1`.

    Bỏ qua `NaN` — lỗ hổng dài không nội suy vẫn còn sau QĐ-008, và chúng không được
    kéo `mu` về 0.

    Chuỗi có dưới 2 điểm hợp lệ trong cửa sổ train thì `sd` không định nghĩa được,
    trả `(nan, nan)`.
    """
    a = _mang(y)[:TRAIN_END]
    ok = np.isfinite(a)
    if int(ok.sum()) < 2:
        return float("nan"), float("nan")
    v = a[ok]
    return float(v.mean()), float(v.std(ddof=1))


def chuan_hoa_duoc(y) -> bool:
    """Chuỗi này có z-score xác định không — tức `sd > 0` trên cửa sổ train.

    Dùng để **đếm và báo cáo** số chuỗi bị loại ở N1, đừng dùng để lặng lẽ bỏ qua.
    """
    _, sd = thong_ke_train(y)
    return bool(np.isfinite(sd) and sd > 0.0)


# --------------------------------------------------------------- biến đổi

def bien_doi(y, mode: str) -> np.ndarray:
    """Đưa chuỗi `y` sang thang của `mode`. Trả mảng **cùng độ dài** với `y`.

    N2 làm phần tử đầu thành `NaN` — không có `y_{-1}` để trừ. Đó là `NaN` thật, không
    phải thiếu sót: luật dòng hợp lệ của mục 8 sẽ loại dòng đó, và nó nằm ngoài mọi
    cửa sổ đánh giá vì `max_lag = 24`.
    """
    m = _kiem_mode(mode)
    a = _mang(y)

    if m == "N0":
        return a.copy()

    if m == "N1":
        mu, sd = thong_ke_train(a)
        if not np.isfinite(sd) or sd == 0.0:
            # Không xác định. Trả NaN trọn chuỗi để chỗ gọi buộc phải xử lý.
            return np.full(a.shape, np.nan)
        return (a - mu) / sd

    # N2
    out = np.full(a.shape, np.nan)
    if a.size > 1:
        out[1:] = a[1:] - a[:-1]
    return out


# -------------------------------------------------------------- map ngược

def map_nguoc(yhat, y, mode: str) -> np.ndarray:
    """Đưa dự đoán `yhat` về **thang CPU% gốc**.

    Parameters
    ----------
    yhat : array-like
        Dự đoán ở thang của `mode`, **căn theo cùng chỉ số** với `y`: `yhat[t]` là dự
        đoán gắn với thời điểm gốc `t`.
    y : array-like
        Chuỗi CPU% **gốc, trọn vẹn** của chính chuỗi đó. N1 cần nó để lấy lại
        `mu`/`sd`; N2 cần nó làm **mốc neo** `y_t`.
    mode : str

    Công thức (QĐ-016 điểm 1):

        N0:  ŷ_gốc = ŷ
        N1:  ŷ_gốc = ŷ × sd + mu
        N2:  ŷ_gốc = y_t + Δ̂
    """
    m = _kiem_mode(mode)
    h = _mang(yhat)
    a = _mang(y)

    if m == "N0":
        return h.copy()

    if m == "N1":
        mu, sd = thong_ke_train(a)
        if not np.isfinite(sd) or sd == 0.0:
            return np.full(h.shape, np.nan)
        return h * sd + mu

    # N2: cộng lại mốc neo. Căn theo chỉ số nên hai mảng phải cùng độ dài.
    if h.shape != a.shape:
        raise ValueError(
            f"N2 cần `yhat` và `y` cùng độ dài để cộng mốc neo: "
            f"{h.shape} so với {a.shape}."
        )
    return a + h
