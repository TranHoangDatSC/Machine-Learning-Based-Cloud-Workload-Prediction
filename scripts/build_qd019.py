"""QĐ-019 — sinh lại ma trận N2 với target đúng `y_{t+h} − y_t`.

    python scripts/build_qd019.py

Ra `data/features_qd019/{env}_N2_h{h}.parquet` cho E1, E2, E3, E1a, E1g × h ∈ {1, 6, 12}.
**Không ghi đè** `data/features/` — sản phẩm GĐ4 đã nghiệm thu giữ nguyên.

Khác ma trận N2 của GĐ4 đúng hai chỗ (QĐ-019 điểm 1):

1. `target` = `y_{t+h} − y_t` lấy từ chuỗi **gốc**. Bản GĐ4 dịch chuỗi **đã sai phân** đi
   `h` bước nên ra `y_{t+h} − y_{t+h−1}`, và map ngược `y_t + Δ̂` chỉ đúng khi h = 1.
2. Dòng hợp lệ: `z` sạch trên `[t−24, t]` và `y_{t+h}` hữu hạn. Bản GĐ4 đòi thêm
   `y_{t+h−1}` (vì target cũ cần nó), nên tập dòng mới là tập cha của tập cũ.

19 cột đặc trưng sinh bằng **đúng** `build_feature_frame` của GĐ2 trên chuỗi sai phân —
không viết lại, để trên dòng chung chúng trùng tuyệt đối bản cũ (K3 của `check_qd019.py`).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from cwp.features import MATRIX_COLS  # noqa: E402
from cwp.features.matrix import build_feature_frame, prepare_input  # noqa: E402
from cwp.features.spec import MAX_LAG  # noqa: E402

from build_features import bien_doi_bang  # noqa: E402

ENVS = ("E1", "E2", "E3", "E1a", "E1g")
HORIZONS = (1, 6, 12)
RA = ROOT / "data" / "features_qd019"


def ma_tran_n2(df_goc: pd.DataFrame, h: int, max_lag: int = MAX_LAG) -> pd.DataFrame:
    """Ma trận N2 đúng định nghĩa QĐ-019 cho một môi trường, một horizon."""
    if h < 1:
        raise ValueError(f"Horizon phải >= 1, nhận {h}.")
    goc = prepare_input(df_goc)                      # sắp (series_id, bucket), index chạy
    z = prepare_input(bien_doi_bang(goc, "N2"))      # cùng thứ tự: cả hai sắp ổn định
    if not (np.array_equal(goc["series_id"].to_numpy(), z["series_id"].to_numpy())
            and np.array_equal(goc["bucket"].to_numpy(), z["bucket"].to_numpy())):
        raise ValueError("chuỗi gốc và chuỗi sai phân lệch thứ tự dòng")

    khung = build_feature_frame(z, h)
    sid = goc["series_id"]
    y = goc["y"].astype("float64")
    khung["target"] = (y.groupby(sid, sort=False).shift(-h) - y).to_numpy()

    # Cửa sổ [t − max_lag, t] của z sạch NaN — cùng cách tính với
    # `cwp.features.matrix.valid_row_mask`, chỉ khác điều kiện target.
    co_nan = z["y"].isna().astype("float64")
    cua_so = (co_nan.groupby(z["series_id"], sort=False).rolling(max_lag + 1).max()
              .droplevel(0).reindex(z.index))
    hop_le = cua_so.eq(0.0) & khung["target"].notna()
    return khung.loc[hop_le, MATRIX_COLS].reset_index(drop=True)


def main() -> int:
    RA.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"\nQĐ-019 — ma trận N2 với target y(t+h) − y(t) → {RA.relative_to(ROOT)}")
    for env in ENVS:
        df = pd.read_parquet(ROOT / "data" / "processed" / f"{env}.parquet")
        for h in HORIZONS:
            X = ma_tran_n2(df, h)
            X.to_parquet(RA / f"{env}_N2_h{h}.parquet", index=False)
            cu = ROOT / "data" / "features" / f"{env}_N2_h{h}.parquet"
            n_cu = len(pd.read_parquet(cu, columns=["bucket"])) if cu.exists() else None
            them = "" if n_cu is None else f"  (bản GĐ4 {n_cu:,}, thêm {len(X) - n_cu:+,})"
            print(f"   {env:4} h={h:<2} {len(X):>10,} dòng{them}")
    print(f"Xong {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
