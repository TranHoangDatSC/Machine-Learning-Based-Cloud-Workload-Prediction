"""Tên và thứ tự 19 đặc trưng — chốt theo QĐ-010, không phải gợi ý.

`docs/protocol.md` mục 8 và `docs/decisions.md` QĐ-010. `scripts/check_gd2.py` so
đúng từng tên cột, nên đặt tên khác là trượt cổng chứ không phải khác biệt phong
cách. `config/features.yaml` mô tả cùng bộ này bằng lời; bản chốt là tệp này.

Thừa hay thiếu một đặc trưng là **đổi giao thức** (`docs/research-plan.md`, quy tắc
phối hợp 1), không phải việc của bước hiện thực.
"""

# Lưới thời gian 5 phút (protocol mục 5). `bucket * GRID_SECONDS` là số giây.
GRID_SECONDS = 300

# Cửa sổ đặc trưng sâu nhất, dùng cho luật dòng hợp lệ ở mục 8 (QĐ-008).
MAX_LAG = 24

LAGS = (1, 2, 3, 6, 12, 24)
ROLL_WINDOWS = (6, 12)
ROLL_STATS = ("mean", "std", "min", "max")

# QĐ-010: ddof = 1 cho roll_std_*. pandas mặc định 1, numpy mặc định 0 — hai bản
# hiện thực sẽ ra số khác nhau nếu không chốt.
ROLL_DDOF = 1

# QĐ-010: epoch 1970-01-01 là thứ Năm, nên ((t // 86400) + 4) % 7 cho 0 là thứ Hai.
DOW_EPOCH_OFFSET = 4

LAG_COLS = [f"lag_{k}" for k in LAGS]
ROLL_COLS = [f"roll_{stat}_{w}" for w in ROLL_WINDOWS for stat in ROLL_STATS]
DIFF_COLS = ["diff_1"]
CALENDAR_COLS = ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]

FEATURE_COLS = LAG_COLS + ROLL_COLS + DIFF_COLS + CALENDAR_COLS

ID_COLS = ["series_id", "bucket"]
TARGET_COL = "target"

# Schema tệp data/features/{env}_h{h}.parquet — đúng 22 cột, không thừa cột nào.
MATRIX_COLS = ID_COLS + FEATURE_COLS + [TARGET_COL]

# Cột bắt buộc của bảng đầu vào data/processed/{env}.parquet (protocol mục 6b).
INPUT_COLS = ["series_id", "bucket", "y"]

assert len(FEATURE_COLS) == 19, "protocol mục 8 chốt đúng 19 đặc trưng"
assert len(MATRIX_COLS) == 22, "19 đặc trưng + series_id + bucket + target"
