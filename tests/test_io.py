"""Kiểm `cwp.io.bitbrains` và `cwp.io.alibaba`.

Chạy:  pytest tests/test_io.py -v

Bốn điều kiện bắt buộc của bước 7 (xem docs/brief-gd1-b.md):
    - `load_raw` trả đúng 2 cột `time_s` (int64) và `cpu_pct` (float64)
    - `time_s` nằm trong 1.3e9 .. 1.5e9, tức là GIÂY chứ không phải mili-giây
    - `make_series_id` cho E2 luôn chứa tháng, khớp `^E2_\\d{4}-\\d+_`
    - tên cột đọc ra không còn ký tự tab hay khoảng trắng thừa

Test nào cần dữ liệu thật chỉ dùng `data/raw/Bitbrains-Rnd/2013-8/1.csv` và
`pytest.skip` khi chưa tải, để bộ test vẫn chạy được trên máy chưa có dữ liệu.

**E3 không đọc tệp 9 GB.** Mọi test của `cwp.io.alibaba` chạy trên CSV tự tạo trong
`tmp_path`. Prompt gốc yêu cầu kiểm `sample_machines`, nhưng hàm đó đã bị xoá theo
QĐ-009 (nó chỉnh mẫu cho khớp `gan_chet == 1` của bản tham chiếu); phần chọn máy nay
là `load_machines_frozen()` đọc `config/e3_machines.txt`, nên đó là thứ được kiểm ở
đây — kèm một test chặn việc lấy mẫu tại chỗ quay lại module.
"""

import re
from pathlib import Path

import pandas as pd
import pytest
import yaml

from cwp.io import alibaba, bitbrains

ROOT = Path(__file__).resolve().parents[1]
E2_CSV = ROOT / "data" / "raw" / "Bitbrains-Rnd" / "2013-8" / "1.csv"
DATASETS_YAML = ROOT / "config" / "datasets.yaml"
FROZEN_TXT = ROOT / "config" / "e3_machines.txt"

# 1.3e9 ~ 2011-03, 1.5e9 ~ 2017-07. Bitbrains thu năm 2013 nên rơi gọn vào giữa;
# nếu cột bị hiểu là mili-giây thì giá trị sẽ cỡ 1.37e12, lệch ba bậc.
TIME_MIN = 1.3e9
TIME_MAX = 1.5e9

E2_ID_RE = re.compile(r"^E2_\d{4}-\d+_")


# --------------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def cfg():
    """Cấu hình thật của repo, nạp theo đường dẫn tuyệt đối nên không phụ thuộc CWD."""
    if not DATASETS_YAML.exists():
        pytest.skip(f"chưa có {DATASETS_YAML}")
    return yaml.safe_load(DATASETS_YAML.read_text(encoding="utf-8")) or {}


@pytest.fixture(scope="module")
def e2_file():
    """Tệp E2 thật; bỏ qua test nếu máy chưa tải dữ liệu thô."""
    if not E2_CSV.exists():
        pytest.skip(f"chưa tải dữ liệu thô: {E2_CSV}")
    return E2_CSV


@pytest.fixture(scope="module")
def e2_df(e2_file, cfg):
    return bitbrains.load_raw(e2_file, cfg=cfg, env="E2")


def write_bitbrains_csv(path: Path, rows, sep=";\t", header=None) -> Path:
    """Ghi một CSV kiểu Bitbrains: header có ngoặc vuông, phân tách `;` + tab."""
    cols = header or ["Timestamp [ms]", "CPU cores", "CPU usage [%]"]
    lines = [sep.join(cols)]
    lines += [sep.join(str(v) for v in r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ============================================================== E1/E2: load_raw

def test_load_raw_tra_dung_hai_cot(e2_df):
    """Đúng 2 cột, đúng tên, đúng dtype — không mang theo cột nào của tệp gốc."""
    assert list(e2_df.columns) == ["time_s", "cpu_pct"]
    assert e2_df["time_s"].dtype == "int64"
    assert e2_df["cpu_pct"].dtype == "float64"
    assert len(e2_df) > 0, "tệp thật mà đọc ra rỗng thì có gì đó sai"


def test_time_s_la_giay_khong_phai_mili_giay(e2_df):
    """Header ghi [ms] nhưng giá trị là giây. Không nhân, không chia 1000."""
    tmin = int(e2_df["time_s"].min())
    tmax = int(e2_df["time_s"].max())
    assert TIME_MIN <= tmin <= TIME_MAX, f"time_s nhỏ nhất = {tmin}, ngoài dải giây"
    assert TIME_MIN <= tmax <= TIME_MAX, f"time_s lớn nhất = {tmax}, ngoài dải giây"


def test_load_raw_khong_nhan_chia_1000(tmp_path):
    """Giá trị timestamp phải giữ nguyên từng con số, không quy đổi đơn vị."""
    src = write_bitbrains_csv(
        tmp_path / "vm.csv",
        [(1375308176, 2, 12.5), (1375308476, 2, 11.5)],
    )
    df = bitbrains.load_raw(src, cfg={}, env="E2")
    assert df["time_s"].tolist() == [1375308176, 1375308476]
    assert df["cpu_pct"].tolist() == [12.5, 11.5]


def test_ten_cot_doc_ra_khong_con_tab_hay_khoang_trang(e2_file, cfg):
    """Bitbrains ngăn cách bằng `;` + tab nên tên cột rất dễ dính `\\t` ở đầu.

    Ép `sep=";"` để header của tệp thật giữ lại tab, rồi kiểm `load_raw` vẫn nhận ra
    cột — tức là bước chuẩn hoá tên cột có thật, không phải may nhờ sep khớp sẵn.
    """
    e2 = dict(cfg.get("E2", {}))
    e2["sep"] = ";"
    df = bitbrains.load_raw(e2_file, cfg={"E2": e2}, env="E2")

    assert list(df.columns) == ["time_s", "cpu_pct"]
    assert len(df) > 0
    for c in df.columns:
        assert "\t" not in c and c == c.strip()


def test_ten_cot_thua_khoang_trang_van_doc_duoc(tmp_path):
    """Header có tab và khoảng trắng thừa vẫn phải khớp tên cột khai trong config."""
    src = write_bitbrains_csv(
        tmp_path / "vm.csv",
        [(1375308176, 2, 12.5)],
        header=["  Timestamp [ms] ", "CPU cores", "\tCPU usage [%]  "],
    )
    df = bitbrains.load_raw(src, cfg={}, env="E2")
    assert list(df.columns) == ["time_s", "cpu_pct"]
    assert df["time_s"].tolist() == [1375308176]
    assert df["cpu_pct"].tolist() == [12.5]


def test_load_raw_bo_dong_khong_doc_duoc_thanh_so(tmp_path):
    """Dòng có ô hỏng bị loại, phần còn lại giữ nguyên dtype."""
    src = write_bitbrains_csv(
        tmp_path / "vm.csv",
        [(1375308176, 2, 12.5), (1375308476, 2, "NA"), (1375308776, 2, 13.0)],
    )
    df = bitbrains.load_raw(src, cfg={}, env="E2")
    assert len(df) == 2
    assert df["time_s"].tolist() == [1375308176, 1375308776]
    assert df["time_s"].dtype == "int64"
    assert df["cpu_pct"].dtype == "float64"


def test_load_raw_khong_con_dong_hop_le_van_dung_dtype(tmp_path):
    """Khung rỗng vẫn phải đúng schema, để chỗ gọi không phải kiểm đặc biệt."""
    src = write_bitbrains_csv(tmp_path / "vm.csv", [(1375308176, 2, "NA")])
    df = bitbrains.load_raw(src, cfg={}, env="E2")
    assert len(df) == 0
    assert list(df.columns) == ["time_s", "cpu_pct"]
    assert df["time_s"].dtype == "int64"
    assert df["cpu_pct"].dtype == "float64"


def test_load_raw_lay_dung_cau_hinh_cua_moi_truong(tmp_path):
    """`env` phải chọn đúng nhánh config.

    Bản cũ viết `cfg.get("E1") or cfg.get("E2")` nên luôn lấy E1; lỗi đó ẩn được vì
    E1 và E2 tình cờ cùng `sep`. Ở đây hai môi trường khai `sep` khác nhau, nên đọc
    E2 bằng cấu hình E1 sẽ hỏng ngay.
    """
    src = tmp_path / "vm.csv"
    src.write_text(
        "Timestamp [ms],CPU usage [%]\n1375308176,12.5\n", encoding="utf-8"
    )
    cfg_hai_moi_truong = {
        "E1": {"sep": ";\t", "time_col": "Timestamp [ms]", "target": "CPU usage [%]"},
        "E2": {"sep": ",", "time_col": "Timestamp [ms]", "target": "CPU usage [%]"},
    }
    df = bitbrains.load_raw(src, cfg=cfg_hai_moi_truong, env="E2")
    assert df["time_s"].tolist() == [1375308176]

    with pytest.raises(KeyError):
        bitbrains.load_raw(src, cfg=cfg_hai_moi_truong, env="E1")


def test_load_raw_bao_loi_khi_thieu_cot(tmp_path):
    """Thiếu cột đích thì phải nổ, không được im lặng trả khung rỗng."""
    src = tmp_path / "vm.csv"
    src.write_text(
        "Timestamp [ms];\tMemory usage [KB]\n1375308176;\t8.0\n", encoding="utf-8"
    )
    with pytest.raises(KeyError):
        bitbrains.load_raw(src, cfg={}, env="E2")


# ======================================================== E1/E2: make_series_id

@pytest.mark.parametrize("month", ["2013-7", "2013-8", "2013-9"])
@pytest.mark.parametrize("path", ["1.csv", "data/raw/Bitbrains-Rnd/2013-8/137.csv"])
def test_make_series_id_e2_luon_chua_thang(month, path):
    """E2 bắt buộc mang tháng trong id — tên file lặp giữa ba tháng (QĐ-003)."""
    sid = bitbrains.make_series_id("E2", path, month=month)
    assert E2_ID_RE.match(sid), f"{sid!r} không khớp ^E2_\\d{{4}}-\\d+_"
    assert month in sid


def test_make_series_id_e2_phan_biet_file_trung_ten_giua_cac_thang():
    """`1.csv` của 2013-7 và 2013-8 là hai chuỗi khác nhau."""
    a = bitbrains.make_series_id(
        "E2", "data/raw/Bitbrains-Rnd/2013-7/1.csv", month="2013-7"
    )
    b = bitbrains.make_series_id(
        "E2", "data/raw/Bitbrains-Rnd/2013-8/1.csv", month="2013-8"
    )
    assert a != b
    assert E2_ID_RE.match(a) and E2_ID_RE.match(b)


def test_make_series_id_e2_thieu_thang_thi_bao_loi():
    """Không có tháng thì phải dừng, không được sinh id thiếu tháng."""
    with pytest.raises(ValueError):
        bitbrains.make_series_id("E2", "1.csv")
    with pytest.raises(ValueError):
        bitbrains.make_series_id("E2", "1.csv", month="")


def test_make_series_id_e1_khong_can_thang():
    """E1 chỉ có một tháng nên id không mang tháng, và không được lẫn với E2."""
    sid = bitbrains.make_series_id(
        "E1", "data/raw/Bitbrains-fastStorage/08-2013/137.csv"
    )
    assert sid == "E1_137"
    assert not E2_ID_RE.match(sid)


def test_make_series_id_tu_choi_moi_truong_la():
    """E3 không đi qua module này; tên môi trường lạ phải bị chặn."""
    for env in ["E3", "E0", ""]:
        with pytest.raises(ValueError):
            bitbrains.make_series_id(env, "1.csv", month="2013-8")


# =================================================== E3: chọn máy và nạp dữ liệu
# Toàn bộ phần này chạy trên CSV tự tạo. Không đụng tới machine_usage.csv (9 GB).

def write_alibaba_csv(path: Path, machines, n_points=4, start=1000, step=10) -> Path:
    """CSV kiểu machine_usage.csv: 9 cột, KHÔNG header."""
    lines = []
    for i, m in enumerate(machines):
        for t in range(n_points):
            lines.append(
                f"{m},{start + t * step},{10.0 + i},{20.0},{0},{0},{1},{2},{3}"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


E3_CFG = {
    "columns": alibaba.DEFAULT_COLUMNS,
    "time_col": "time_stamp",
    "target": "cpu_util_percent",
}


def test_khong_con_ham_lay_mau_tai_cho():
    """QĐ-009: tập máy E3 đã đóng băng, không lấy mẫu lại trong code.

    `sample_machines` từng thay máy trong mẫu cho tới khi khớp `gan_chet == 1` của
    bản tham chiếu. Test này chặn nó — hay bất kỳ hàm lấy mẫu nào — quay lại module.
    """
    assert not hasattr(alibaba, "sample_machines")
    assert alibaba.__all__ == [
        "machine_means",
        "load_machines_frozen",
        "load_machines",
    ]


def test_load_machines_frozen_doc_dung_thu_tu_va_bo_chu_thich(tmp_path):
    """Bỏ dòng chú thích và dòng trắng, giữ nguyên thứ tự trong tệp."""
    p = tmp_path / "e3.txt"
    p.write_text("# chú thích\n#\nm_100\n\n  m_2  \nm_33\n", encoding="utf-8")
    assert alibaba.load_machines_frozen(p) == ["m_100", "m_2", "m_33"]


def test_load_machines_frozen_thieu_tep_thi_bao_loi(tmp_path):
    """Thiếu danh sách đóng băng phải nổ rõ ràng, không âm thầm trả rỗng."""
    with pytest.raises(FileNotFoundError):
        alibaba.load_machines_frozen(tmp_path / "khong-ton-tai.txt")


def test_danh_sach_dong_bang_cua_repo_du_500_may_khong_trung():
    """Danh sách thật trong repo: đúng 500 máy, không trùng lặp."""
    if not FROZEN_TXT.exists():
        pytest.skip("chưa có config/e3_machines.txt")
    machines = alibaba.load_machines_frozen(FROZEN_TXT)
    assert len(machines) == 500
    assert len(set(machines)) == 500


def test_cau_hinh_e3_khop_voi_ten_cot_mac_dinh(cfg):
    """config/datasets.yaml và DEFAULT_COLUMNS không được trôi khỏi nhau."""
    e3 = cfg.get("E3", {})
    assert e3.get("columns") == alibaba.DEFAULT_COLUMNS
    assert e3.get("time_col") == "time_stamp"
    assert e3.get("target") == "cpu_util_percent"
    assert e3.get("header") is False, "machine_usage.csv không có header"


def test_load_machines_chi_giu_may_da_chon(tmp_path):
    """Lọc đúng tập máy, trả đúng 3 cột."""
    src = write_alibaba_csv(tmp_path / "usage.csv", ["m_1", "m_2", "m_3"], n_points=4)
    df = alibaba.load_machines(src, ["m_1", "m_3"], chunksize=5, cfg=E3_CFG)

    assert list(df.columns) == ["machine_id", "time_stamp", "cpu_util_percent"]
    assert set(df["machine_id"].unique()) == {"m_1", "m_3"}
    assert len(df) == 8, "mỗi máy 4 điểm, không được rơi dòng nào"


def test_load_machines_khong_phu_thuoc_chunksize(tmp_path):
    """Ranh giới chunk không được làm rơi dòng: mọi chunksize cho cùng kết quả."""
    src = write_alibaba_csv(
        tmp_path / "usage.csv", [f"m_{i}" for i in range(6)], n_points=5
    )
    chon = ["m_0", "m_3", "m_5"]
    goc = alibaba.load_machines(src, chon, chunksize=1000, cfg=E3_CFG)

    for size in (1, 2, 7, 13):
        khac = alibaba.load_machines(src, chon, chunksize=size, cfg=E3_CFG)
        pd.testing.assert_frame_equal(goc, khac)
    assert len(goc) == 15


def test_load_machines_nhan_ca_list_va_set(tmp_path):
    """Danh sách hay tập hợp đều cho cùng kết quả."""
    src = write_alibaba_csv(tmp_path / "usage.csv", ["m_1", "m_2"], n_points=3)
    a = alibaba.load_machines(src, ["m_2"], chunksize=4, cfg=E3_CFG)
    b = alibaba.load_machines(src, {"m_2"}, chunksize=4, cfg=E3_CFG)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 3


def test_load_machines_khong_khop_may_nao_tra_khung_rong_dung_cot(tmp_path):
    """Không khớp máy nào vẫn trả đủ 3 cột, để chỗ gọi không vỡ."""
    src = write_alibaba_csv(tmp_path / "usage.csv", ["m_1"], n_points=3)
    df = alibaba.load_machines(src, ["khong_ton_tai"], chunksize=2, cfg=E3_CFG)
    assert len(df) == 0
    assert list(df.columns) == ["machine_id", "time_stamp", "cpu_util_percent"]
