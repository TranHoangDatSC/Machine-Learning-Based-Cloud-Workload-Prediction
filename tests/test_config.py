"""Ghim `config/*.yaml` với hằng số trong code — hai bên phải nói cùng một thứ.

Chạy:  pytest tests/test_config.py -v

Vì sao cần. Ngày 2026-09-09, đếm số tệp `.py` thực sự đọc từng config:

    preprocess.yaml   6 nơi đọc      -> điều khiển code thật
    datasets.yaml     4 nơi đọc      -> điều khiển code thật
    features.yaml     0 nơi đọc      -> mô tả thứ ĐÃ xây, mà không ai đọc
    split.yaml        0 nơi đọc      -> mô tả GĐ3, chưa xây, chưa cần đọc
    paths.yaml        0 nơi đọc      -> nt

`features.yaml` là trường hợp bất thường: nó mô tả bộ đặc trưng vừa xây xong nhưng
không nơi nào đọc, nên sửa nó không có tác dụng gì **và cũng không có cảnh báo gì**.
Ai thêm `48` vào `lags` sẽ tưởng mình vừa thêm một đặc trưng.

Hai lối thoát đều tệ hơn lối này:

- Để code đọc config thì 19 tên cột thành thứ sửa được ngoài `docs/decisions.md` —
  trái QĐ-010 và trái câu mở đầu `protocol.md`.
- Xoá config thì mất chỗ mô tả bộ đặc trưng bằng lời.

Nên: **code chốt ở `spec.py`, config là tài liệu, và tệp test này là người gác.** Sửa
một bên mà không sửa bên kia thì đỏ.

Ghim luôn `preprocess.yaml` ở hai chỗ mà tầng đặc trưng hardcode lại: `grid_seconds`
và `row_validity.max_lag`. Chỗ `max_lag` không phải giả định — `filter.py` và
`build.py` **thật sự đọc nó** để đếm `valid_rows_h*` trong `catalog.parquet`, tức là
neo của cổng GĐ2. Sửa config mà không sửa `spec.py` thì chín neo lệch.
"""

from pathlib import Path

import pytest
import yaml

from cwp.features import (
    CALENDAR_COLS,
    DIFF_COLS,
    FEATURE_COLS,
    GRID_SECONDS,
    LAG_COLS,
    MAX_LAG,
    ROLL_COLS,
    ROLL_DDOF,
)
from cwp.features.spec import DOW_EPOCH_OFFSET, LAGS, ROLL_STATS, ROLL_WINDOWS

ROOT = Path(__file__).resolve().parents[1]
FEATURES_YAML = ROOT / "config" / "features.yaml"
PREPROCESS_YAML = ROOT / "config" / "preprocess.yaml"


def doc(path: Path) -> dict:
    if not path.exists():
        pytest.skip(f"chưa có {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@pytest.fixture(scope="module")
def feat():
    return doc(FEATURES_YAML)


@pytest.fixture(scope="module")
def prep():
    return doc(PREPROCESS_YAML)


# ===================================================== config/features.yaml

def test_lags_khop_spec(feat):
    assert list(feat["lags"]) == list(LAGS)


def test_rolling_windows_va_stats_khop_spec(feat):
    assert list(feat["rolling_windows"]) == list(ROLL_WINDOWS)
    assert list(feat["rolling_stats"]) == list(ROLL_STATS)


def test_calendar_khop_spec(feat):
    assert list(feat["calendar"]) == CALENDAR_COLS


def test_diff_bat_va_spec_co_dung_mot_cot_sai_phan(feat):
    assert feat["diff"] is True
    assert DIFF_COLS == ["diff_1"]


def test_shift_before_rolling_phai_bat(feat):
    """Tắt nó đi là vi phạm protocol mục 8, không phải một lựa chọn cấu hình.

    Cửa sổ rolling *phải* loại điểm hiện tại. Nếu về sau ai đó muốn một biến thể
    không shift thì đó là đổi giao thức, phải qua `docs/decisions.md`.
    """
    assert feat["shift_before_rolling"] is True


def test_ba_quy_uoc_qd010_khop_spec(feat):
    """`ddof`, gốc `dow`, `grid_seconds` — ba thứ đã làm A và B ra số khác nhau."""
    assert feat["rolling_ddof"] == ROLL_DDOF == 1
    assert feat["dow_epoch_offset"] == DOW_EPOCH_OFFSET == 4
    assert feat["grid_seconds"] == GRID_SECONDS == 300


def test_max_lag_khop_spec(feat):
    assert feat["max_lag"] == MAX_LAG


def test_ten_19_cot_suy_tu_config_khop_spec():
    """Phép kiểm mạnh nhất ở đây: dựng lại 19 tên cột **từ config** rồi so với spec.

    Bảy test trên so từng khoá một. Test này so kết quả cuối cùng, nên nó bắt được
    cả những cách lệch mà bảy test kia bỏ sót — ví dụ đổi thứ tự, hoặc đổi quy tắc
    ghép tên từ `roll_mean_6` sang `rolling_mean_6`.
    """
    cfg = doc(FEATURES_YAML)

    tu_config = [f"lag_{k}" for k in cfg["lags"]]
    tu_config += [f"roll_{s}_{w}"
                  for w in cfg["rolling_windows"]
                  for s in cfg["rolling_stats"]]
    if cfg["diff"]:
        tu_config += ["diff_1"]
    tu_config += list(cfg["calendar"])

    assert tu_config == FEATURE_COLS
    assert len(tu_config) == 19


def test_config_khong_co_khoa_la(feat):
    """Thêm khoá vào config mà code không biết là thêm một lời hứa suông.

    Ai đó viết `lags_extra: [48]` vào đây sẽ tưởng mình vừa đổi được hành vi. Không
    có gì xảy ra và không có gì báo — trừ test này.
    """
    mong_doi = {
        "lags", "rolling_windows", "rolling_stats", "diff", "calendar",
        "shift_before_rolling", "rolling_ddof", "dow_epoch_offset",
        "grid_seconds", "max_lag",
    }
    thua = set(feat) - mong_doi
    thieu = mong_doi - set(feat)

    assert not thua, (
        f"khoá {sorted(thua)} có trong config nhưng không nơi nào dùng — "
        "thêm vào spec.py và vào test này, hoặc bỏ khỏi config"
    )
    assert not thieu, f"config thiếu khoá {sorted(thieu)}"


# =================================================== config/preprocess.yaml

def test_grid_seconds_hai_config_bang_nhau(prep, feat):
    """Lưới 5 phút là một, dù nó xuất hiện ở hai tệp config và một hằng số."""
    assert prep["grid_seconds"] == feat["grid_seconds"] == GRID_SECONDS


def test_max_lag_cua_tien_xu_ly_bang_max_lag_cua_dac_trung(prep):
    """Neo của cổng GĐ2 phụ thuộc khoá này — đây không phải trùng hợp cần giữ.

    `filter.py` và `build.py` đọc `row_validity.max_lag` để đếm `valid_rows_h*` ghi
    vào `catalog.parquet`. Tầng đặc trưng thì hardcode `MAX_LAG`. Hai số phải bằng
    nhau, nếu không thì chín neo của `check_gd2.py` lệch mà không ai biết vì sao.
    """
    assert prep["row_validity"]["max_lag"] == MAX_LAG


def test_require_full_window_phai_bat(prep):
    """Luật dòng hợp lệ mục 8 đòi cả `[t-24, t]` sạch NaN, không phải chỉ 15 điểm."""
    assert prep["row_validity"]["require_full_window"] is True


def test_so_dac_trung_dung_19_o_ca_ba_nguon():
    """protocol mục 8 chốt đúng 19 — đếm lại từ ba nhóm cột đã tách sẵn."""
    assert len(LAG_COLS) == 6
    assert len(ROLL_COLS) == 8
    assert len(DIFF_COLS) == 1
    assert len(CALENDAR_COLS) == 4
    assert len(FEATURE_COLS) == 19
