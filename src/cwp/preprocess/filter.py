"""Lọc chuỗi và đếm số dòng huấn luyện hợp lệ (protocol mục 6 bước 7, mục 8)."""

from pathlib import Path
import numpy as np
import pandas as pd
import yaml


def _load_preprocess_config(cfg_path: str | Path | None = None) -> dict:
    """Tải cấu hình tiền xử lý từ file yaml."""
    if cfg_path is not None:
        path = Path(cfg_path)
    else:
        path = Path("config/preprocess.yaml")
        if not path.exists():
            path = Path(__file__).resolve().parents[3] / "config" / "preprocess.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def count_valid_rows(
    s: pd.Series,
    max_lag: int | None = None,
    h: int = 1,
    cfg: dict | None = None,
) -> int:
    """Đếm số dòng huấn luyện hợp lệ theo định nghĩa ở protocol mục 8.

    Dòng tại thời điểm t hợp lệ khi:
    - Mọi điểm trong cửa sổ [t - max_lag, t] không phải NaN.
    - Điểm mục tiêu tại t + h không phải NaN.

    Parameters
    ----------
    s : pd.Series
        Chuỗi dữ liệu (đã căn lưới và nội suy).
    max_lag : int, optional
        Cửa sổ đặc trưng sâu nhất (mặc định lấy từ row_validity.max_lag trong config).
    h : int, default=1
        Horizon dự đoán (ví dụ 1, 6, 12).
    cfg : dict, optional
        Cấu hình tiền xử lý.

    Returns
    -------
    int
        Số dòng huấn luyện hợp lệ.
    """
    if max_lag is None:
        if cfg is None:
            cfg = _load_preprocess_config()
        max_lag = cfg.get("row_validity", {}).get("max_lag", 24)

    arr = s.to_numpy(dtype=float)
    n = len(arr)

    # Cần ít nhất (max_lag + 1) điểm cho đặc trưng và h điểm cho target
    if n < max_lag + h + 1:
        return 0

    is_valid = ~np.isnan(arr)
    w = max_lag + 1

    # Dùng cumsum để kiểm tra toàn bộ cửa sổ [t - max_lag, t] không chứa NaN O(N)
    cs = np.pad(np.cumsum(is_valid.astype(int)), (1, 0), "constant")
    t = np.arange(max_lag, n - h)

    window_ok = (cs[t + 1] - cs[t - max_lag]) == w
    target_ok = is_valid[t + h]

    return int(np.sum(window_ok & target_ok))


def judge(s: pd.Series, cfg: dict | None = None) -> str | None:
    """Đánh giá và trả về lý do loại chuỗi, hoặc None nếu chuỗi được giữ.

    Các mã lý do theo thứ tự xét trong protocol mục 6 bước 7:
    1. 'ngoai_cua_so': Không có mẫu nào nằm trong cửa sổ.
    2. 'gan_chet': CPU% trung bình < min_mean.
    3. 'hang': Số giá trị phân biệt < min_unique.
    4. 'it_dong': Số dòng huấn luyện hợp lệ ở h=12 < min_valid_rows_h12.

    Parameters
    ----------
    s : pd.Series
        Chuỗi dữ liệu cần kiểm tra.
    cfg : dict, optional
        Cấu hình tiền xử lý (mặc định nạp từ config/preprocess.yaml).

    Returns
    -------
    str hoặc None
        Mã lý do loại ('ngoai_cua_so', 'gan_chet', 'hang', 'it_dong') hoặc None nếu hợp lệ.
    """
    if cfg is None:
        cfg = _load_preprocess_config()

    flt_cfg = cfg.get("filter", {})
    min_mean = flt_cfg.get("min_mean", 1.0)
    min_unique = flt_cfg.get("min_unique", 3)
    min_valid_h12 = flt_cfg.get("min_valid_rows_h12", 500)
    max_lag = cfg.get("row_validity", {}).get("max_lag", 24)

    clean = s.dropna()

    # 1. ngoai_cua_so
    if clean.empty:
        return "ngoai_cua_so"

    # 2. gan_chet
    if clean.mean() < min_mean:
        return "gan_chet"

    # 3. hang
    if clean.nunique() < min_unique:
        return "hang"

    # 4. it_dong (tính tại h=12)
    valid_rows_h12 = count_valid_rows(s, max_lag=max_lag, h=12, cfg=cfg)
    if valid_rows_h12 < min_valid_h12:
        return "it_dong"

    return None


__all__ = ["count_valid_rows", "judge"]
