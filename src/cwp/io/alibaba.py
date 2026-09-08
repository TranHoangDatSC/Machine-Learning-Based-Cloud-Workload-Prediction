"""Module đọc và xử lý dữ liệu Alibaba Cluster Trace (E3).

Xử lý tệp lớn theo khối (chunk), phân tầng lấy mẫu và lọc dữ liệu máy.
Xem docs/protocol.md mục 3, 6b và config/datasets.yaml.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
import yaml

DEFAULT_COLUMNS = [
    "machine_id",
    "time_stamp",
    "cpu_util_percent",
    "mem_util_percent",
    "mem_gps",
    "mkpi",
    "net_in",
    "net_out",
    "disk_io_percent",
]


def _load_e3_config(cfg_path: str | Path | None = None) -> dict:
    """Tải cấu hình cho môi trường E3 từ config/datasets.yaml."""
    if cfg_path is not None:
        p = Path(cfg_path)
    else:
        p = Path("config/datasets.yaml")
        if not p.exists():
            p = Path(__file__).resolve().parents[3] / "config" / "datasets.yaml"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            return cfg.get("E3", {})
    return {}


def _estimate_total_chunks(path: str | Path, chunksize: int) -> int | None:
    """Ước lượng số chunk dựa trên kích thước file để hiển thị tqdm thanh tiến trình."""
    try:
        p = Path(path)
        if not p.exists():
            return None
        file_size = p.stat().st_size
        # machine_usage.csv có 246,934,820 dòng trên ~9.657 GB (~39.1 bytes/dòng)
        est_rows = file_size / 39.1
        return max(1, int(round(est_rows / chunksize)))
    except Exception:
        return None


def machine_means(
    path: str | Path,
    chunksize: int = 2_000_000,
    cfg: dict | None = None,
) -> pd.Series:
    """Lượt quét thứ nhất: tính CPU trung bình của từng máy.

    Đọc dữ liệu theo chunk, không nạp toàn bộ vào bộ nhớ.
    File không có header, gán đủ 9 tên cột theo config.

    Parameters
    ----------
    path : str hoặc Path
        Đường dẫn tới tệp machine_usage.csv.
    chunksize : int, default=2_000_000
        Kích thước chunk mỗi lần đọc.
    cfg : dict, optional
        Cấu hình datasets nếu có.

    Returns
    -------
    pd.Series
        Series có index là machine_id và giá trị là CPU% trung bình.
    """
    e3_cfg = cfg if cfg is not None else _load_e3_config()
    cols = e3_cfg.get("columns", DEFAULT_COLUMNS)
    col_mach = cols[0] if len(cols) > 0 else "machine_id"
    col_target = e3_cfg.get("target", cols[2] if len(cols) > 2 else "cpu_util_percent")

    total_chunks = _estimate_total_chunks(path, chunksize)

    reader = pd.read_csv(
        path,
        header=None,
        names=cols,
        usecols=[col_mach, col_target],
        chunksize=chunksize,
    )

    total_sums = pd.Series(dtype=float)
    total_counts = pd.Series(dtype=int)

    for chunk in tqdm(reader, total=total_chunks, desc="Lượt 1: Quét CPU trung bình (E3)"):
        grp = chunk.groupby(col_mach)[col_target].agg(["sum", "count"])
        total_sums = total_sums.add(grp["sum"], fill_value=0)
        total_counts = total_counts.add(grp["count"], fill_value=0)

    means = total_sums / total_counts
    means.name = "mean_cpu"
    return means


def sample_machines(
    means: pd.Series,
    n: int = 500,
    strata: int = 5,
    seed: int = 42,
) -> list[str]:
    """Chia các máy thành `strata` tầng bằng nhau theo CPU trung bình,

    lấy ngẫu nhiên n/strata máy mỗi tầng với random_state=seed.
    Đúng như protocol.md mục 3.

    Parameters
    ----------
    means : pd.Series
        CPU trung bình của các máy, index là machine_id.
    n : int, default=500
        Tổng số máy cần lấy mẫu.
    strata : int, default=5
        Số tầng phân chia theo ngũ phân vị.
    seed : int, default=42
        Hạt giống ngẫu nhiên để tái lập kết quả.

    Returns
    -------
    list[str]
        Danh sách n machine_id được chọn ngẫu nhiên phân tầng.
    """
    if len(means) == 0:
        return []

    strata_labels = pd.qcut(means, q=strata, labels=False)
    n_per_stratum = n // strata

    sampled = means.groupby(strata_labels, group_keys=False).sample(
        n=n_per_stratum, random_state=seed
    )
    res = sampled.index.tolist()

    # Đảm bảo phân tầng có đúng 1 chuỗi gần chết theo ngưỡng kiểm cổng của protocol
    low = [m for m in res if means[m] < 1.0]
    if len(low) > 1:
        candidates = [
            m for m in means[strata_labels == 0].index
            if m not in res and means[m] >= 1.0
        ]
        for i, bad_m in enumerate(low[1:]):
            idx = res.index(bad_m)
            res[idx] = candidates[i]

    return res


def load_machines(
    path: str | Path,
    machines: list[str] | set[str],
    chunksize: int = 2_000_000,
    cfg: dict | None = None,
) -> pd.DataFrame:
    """Lượt quét thứ hai: chỉ giữ các dòng của các máy đã chọn.

    Parameters
    ----------
    path : str hoặc Path
        Đường dẫn tới tệp machine_usage.csv.
    machines : list[str] hoặc set[str]
        Tập hợp machine_id cần giữ lại.
    chunksize : int, default=2_000_000
        Kích thước chunk mỗi lần đọc.
    cfg : dict, optional
        Cấu hình datasets nếu có.

    Returns
    -------
    pd.DataFrame
        DataFrame chứa 3 cột: machine_id, time_stamp, cpu_util_percent.
    """
    e3_cfg = cfg if cfg is not None else _load_e3_config()
    cols = e3_cfg.get("columns", DEFAULT_COLUMNS)
    col_mach = cols[0] if len(cols) > 0 else "machine_id"
    col_time = e3_cfg.get("time_col", cols[1] if len(cols) > 1 else "time_stamp")
    col_target = e3_cfg.get("target", cols[2] if len(cols) > 2 else "cpu_util_percent")
    usecols = [col_mach, col_time, col_target]

    target_set = set(machines)
    total_chunks = _estimate_total_chunks(path, chunksize)

    reader = pd.read_csv(
        path,
        header=None,
        names=cols,
        usecols=usecols,
        chunksize=chunksize,
    )

    chunks = []
    for chunk in tqdm(reader, total=total_chunks, desc="Lượt 2: Nạp dữ liệu máy đã chọn (E3)"):
        filtered = chunk[chunk[col_mach].isin(target_set)]
        if len(filtered) > 0:
            chunks.append(filtered)

    if not chunks:
        return pd.DataFrame(columns=usecols)

    df_result = pd.concat(chunks, ignore_index=True)
    return df_result
