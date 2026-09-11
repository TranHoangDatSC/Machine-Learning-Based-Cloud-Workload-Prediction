"""Phân tầng burstiness để **báo cáo** — QĐ-012, `docs/protocol.md` mục 13.

Ba tầng, chia bằng **tam phân vị của CV tính riêng trong từng môi trường**. Ngưỡng
không hardcode: chúng tính lại từ `results/tables/cv_gd2.csv` mỗi lần chạy, và cách
chia đọc từ `config/split.yaml` (`stratify.method`, `stratify.n_strata`).

Vì sao không dùng một ngưỡng tuyệt đối chung cho ba môi trường (QĐ-012 điểm 1), hai lý
do đo được:

- Tương quan giữa CV và mức tải **đổi dấu** giữa Bitbrains (ρ = +0,375 và +0,249) và
  Alibaba (ρ = −0,692), nên một ngưỡng chung sẽ chọn ra hai nhóm máy khác loại.
- Tam phân vị của E3 chỉ rộng 0,06 và nằm gọn trong tầng thấp nhất của E1.

CV là biến **báo cáo**, không phải đặc trưng — QĐ-012 điểm 2
------------------------------------------------------------

`cv_gd2.csv` tính CV trên **toàn bộ** cửa sổ 8 ngày, tức có cả phần rơi vào validation
và test. Dùng để nhóm chuỗi khi đọc bảng thì không sao. Dùng làm **đặc trưng**, làm
**trọng số huấn luyện**, hay làm **tiêu chí chọn model theo tầng** thì đó là rò rỉ —
khi ấy bắt buộc tính lại CV chỉ trên cửa sổ train.

Có đúng một chỗ trong GĐ3 mà tầng chạm vào phần huấn luyện: **mẫu con của SVR** phân
tầng theo ba tầng này (QĐ-014 điểm 2). Đó là lấy mẫu phân tầng để giữ tỉ lệ quần thể,
không phải dùng CV làm tín hiệu học — model không nhìn thấy nhãn tầng.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Nhãn ba tầng, theo thứ tự tăng dần của CV.
TEN_TANG = ("thap", "vua", "cao")


def doc_cau_hinh_tang(config_path: str | Path = "config/split.yaml") -> dict:
    """Đọc `stratify` từ `config/split.yaml`. Ngưỡng **không** nằm trong config."""
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    st = cfg.get("stratify", {})
    if st.get("method") != "percentile_within_env":
        raise ValueError(
            f"config/split.yaml: stratify.method = {st.get('method')!r}, "
            "QĐ-012 điểm 1 chốt 'percentile_within_env'."
        )
    return st


def nguong(cv: np.ndarray, n_strata: int = 3) -> list[float]:
    """`n_strata − 1` phân vị chia đều, tính **trong một môi trường**.

    Với `n_strata = 3` thì đây là tam phân vị: phân vị 33,33% và 66,67%.
    """
    if n_strata < 2:
        raise ValueError(f"n_strata phải >= 2, nhận {n_strata}.")
    q = [100.0 * i / n_strata for i in range(1, n_strata)]
    return [float(x) for x in np.percentile(np.asarray(cv, dtype="float64"), q)]


def gan_tang(
    cv_bang: pd.DataFrame, env: str, n_strata: int = 3,
) -> tuple[pd.Series, list[float]]:
    """Nhãn tầng của từng chuỗi trong một môi trường, kèm ngưỡng đã dùng.

    Parameters
    ----------
    cv_bang : pd.DataFrame
        `results/tables/cv_gd2.csv`, cần cột `series_id`, `env`, `cv`.
    env : str
        Mã môi trường.

    Returns
    -------
    (pd.Series, list[float])
        Series index `series_id`, giá trị là một trong `TEN_TANG`; và danh sách ngưỡng.
    """
    con = cv_bang[cv_bang["env"] == env]
    if con.empty:
        raise ValueError(f"cv_gd2.csv không có dòng nào của {env}.")
    v = con["cv"].to_numpy("float64")
    nguong_env = nguong(v, n_strata)
    chi_so = np.digitize(v, nguong_env)
    ten = list(TEN_TANG) if n_strata == 3 else [f"t{i}" for i in range(n_strata)]
    return (
        pd.Series([ten[i] for i in chi_so], index=con["series_id"].to_numpy(),
                  name="tang"),
        nguong_env,
    )


def bang_tang(
    cv_bang: pd.DataFrame, envs=("E1", "E2", "E3"), n_strata: int = 3,
) -> pd.DataFrame:
    """Bảng dài `series_id, env, tang, cv, ti_le_cham_chan` cho mọi môi trường.

    `ti_le_cham_chan` = `CV / √((100−m)/m)` lấy thẳng từ `cv_gd2.csv` — QĐ-012 điểm 3
    đòi mọi bảng phân tầng báo kèm cột này, để phân biệt một chuỗi ít bursty **do bản
    chất** với một chuỗi ít bursty **vì đã cụng trần thang đo**.
    """
    phan = []
    for env in envs:
        tang, _ = gan_tang(cv_bang, env, n_strata)
        con = cv_bang[cv_bang["env"] == env].set_index("series_id")
        phan.append(pd.DataFrame({
            "series_id": tang.index,
            "env": env,
            "tang": tang.to_numpy(),
            "cv": con.loc[tang.index, "cv"].to_numpy(),
            "ti_le_cham_chan": con.loc[tang.index, "ti_le_cham_chan"].to_numpy(),
        }))
    return pd.concat(phan, ignore_index=True)
