"""Kiểm `cwp.preprocess.resample` và `cwp.preprocess.filter`.

Chạy:  pytest tests/test_resample.py -v

Không dùng dữ liệu thật — mọi chuỗi đều tự tạo, nhỏ và tính tay được, để khi test đỏ
thì biết ngay sai ở đâu.

Các cam kết được kiểm ở đây (docs/protocol.md mục 5, 6, 7, 8 và QĐ-008):
    - `to_grid`  : lưới tuyệt đối `floor(t/300)`, bucket rỗng để NaN, index liên tục
    - `apply_window` : cửa sổ toàn cục `[b0, b0 + n)`, ngoài cửa sổ trả rỗng
    - `interpolate_short` : nội suy TUYẾN TÍNH cụm NaN dài <= K, có neo hai phía;
      **không** ffill — ffill tạo đoạn phẳng làm autocorrelation tăng giả tạo, mà
      autocorrelation chính là đại lượng trung tâm của RQ3
    - `count_valid_rows` : `[t-max_lag, t]` và `t+h` đều không NaN
    - `judge` : bốn mã loại, xét đúng thứ tự protocol mục 6 bước 7
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from cwp.preprocess.filter import count_valid_rows, judge
from cwp.preprocess.resample import apply_window, interpolate_short, to_grid

ROOT = Path(__file__).resolve().parents[1]
PREPROCESS_YAML = ROOT / "config" / "preprocess.yaml"

GRID = 300          # giây mỗi bucket (protocol mục 5)
WINDOW_BUCKETS = 2304   # 8 ngày / 5 phút (protocol mục 7)
MAX_LAG = 24        # cửa sổ đặc trưng sâu nhất (protocol mục 8)


@pytest.fixture(scope="module")
def cfg():
    """Cấu hình thật của repo, nạp theo đường dẫn tuyệt đối nên không phụ thuộc CWD."""
    if not PREPROCESS_YAML.exists():
        pytest.skip(f"chưa có {PREPROCESS_YAML}")
    return yaml.safe_load(PREPROCESS_YAML.read_text(encoding="utf-8")) or {}


def chuoi_bien_thien(n: int, base: float = 50.0, buoc: float = 1.0) -> pd.Series:
    """Chuỗi 'lành': không NaN, trung bình cao, 7 giá trị phân biệt."""
    return pd.Series([base + (i % 7) * buoc for i in range(n)], dtype=float)


# ================================================================ to_grid

def test_to_grid_bucket_rong_la_nan_khong_tu_lap():
    """Bucket không có mẫu nào phải để NaN. Lấp ở đây là lấp lén (protocol mục 5)."""
    # Mẫu ở bucket 0 và bucket 2; bucket 1 hoàn toàn trống.
    s = to_grid([0, 600], [10.0, 30.0], grid=GRID)

    assert len(s) == 3
    assert s.iloc[0] == 10.0
    assert np.isnan(s.iloc[1]), "bucket rỗng bị lấp — không được tự điền giá trị"
    assert s.iloc[2] == 30.0


def test_to_grid_nhieu_bucket_rong_lien_tiep_deu_la_nan():
    """Lỗ hổng dài vẫn là NaN nguyên cụm; việc xử lý dành cho bước nội suy."""
    s = to_grid([0, 3000], [10.0, 20.0], grid=GRID)
    assert len(s) == 11
    assert s.iloc[1:10].isna().all()
    assert int(s.isna().sum()) == 9


def test_to_grid_index_lien_tuc_tu_min_toi_max():
    """Index phải chạy đủ từng bước 1, không nhảy cóc qua bucket rỗng."""
    times = [0, 300, 1800, 2100]     # bucket 0, 1, 6, 7 — hổng 2..5
    s = to_grid(times, [1.0, 2.0, 3.0, 4.0], grid=GRID)

    assert list(s.index) == list(range(0, 8))
    assert np.all(np.diff(s.index.to_numpy()) == 1), "index có bước nhảy > 1"
    assert s.index[0] == min(times) // GRID
    assert s.index[-1] == max(times) // GRID


def test_to_grid_dung_luoi_tuyet_doi_khong_danh_so_lai_tu_0():
    """`floor(t/300)` trên mốc thời gian thật, không đánh số lại từ điểm đầu chuỗi.

    Cửa sổ 8 ngày là TOÀN CỤC theo môi trường (protocol mục 7); nếu mỗi chuỗi tự
    đánh số từ 0 thì `b0` chung mất nghĩa và mọi chuỗi đều nằm trong cửa sổ.
    """
    t0 = 1375308176
    s = to_grid([t0, t0 + GRID], [10.0, 20.0], grid=GRID)
    assert s.index[0] == t0 // GRID == 4584360


def test_to_grid_lay_trung_binh_trong_mot_bucket():
    """Nhiều mẫu rơi cùng bucket thì lấy trung bình (protocol mục 5)."""
    s = to_grid([0, 100, 200, 300], [10.0, 20.0, 30.0, 99.0], grid=GRID)
    assert s.iloc[0] == 20.0     # (10 + 20 + 30) / 3
    assert s.iloc[1] == 99.0


def test_to_grid_bien_bucket_theo_floor():
    """t=299 vẫn thuộc bucket 0, t=300 mới sang bucket 1."""
    s = to_grid([299, 300], [1.0, 2.0], grid=GRID)
    assert list(s.index) == [0, 1]
    assert s.tolist() == [1.0, 2.0]


def test_to_grid_chuoi_rong_tra_series_rong():
    s = to_grid([], [], grid=GRID)
    assert len(s) == 0


# ============================================================ apply_window

def test_apply_window_chuoi_ngoai_cua_so_tra_ve_rong():
    """Chuỗi bắt đầu muộn, không giao với cửa sổ toàn cục -> rỗng.

    Đây là đường dẫn sinh ra mã loại `ngoai_cua_so` ở protocol mục 7.
    """
    s = pd.Series(np.arange(10, dtype=float), index=range(9000, 9010))
    out = apply_window(s, b0=0, n_buckets=WINDOW_BUCKETS)
    assert len(out) == 0
    assert isinstance(out, pd.Series)


def test_apply_window_chuoi_ngay_truoc_cua_so_cung_tra_ve_rong():
    """Nằm hoàn toàn phía trước cửa sổ cũng là ngoài cửa sổ."""
    s = pd.Series(np.arange(10, dtype=float), index=range(0, 10))
    out = apply_window(s, b0=5000, n_buckets=WINDOW_BUCKETS)
    assert len(out) == 0


def test_apply_window_chi_giu_phan_giao_voi_cua_so():
    """Chuỗi vắt qua mép cửa sổ: giữ phần trong, bỏ phần ngoài."""
    s = pd.Series(np.arange(20, dtype=float), index=range(95, 115))
    out = apply_window(s, b0=100, n_buckets=10)
    assert list(out.index) == list(range(100, 110))
    assert out.iloc[0] == 5.0


def test_apply_window_bien_trai_dong_bien_phai_mo():
    """Cửa sổ là `[b0, b0 + n)`: lấy b0, không lấy b0 + n."""
    s = pd.Series(np.arange(10, dtype=float), index=range(0, 10))
    out = apply_window(s, b0=2, n_buckets=3)
    assert list(out.index) == [2, 3, 4]


def test_apply_window_giu_nguyen_nan_trong_cua_so():
    """Cắt cửa sổ không được tiện tay bỏ NaN — lỗ hổng phải sang bước sau."""
    s = pd.Series([1.0, np.nan, np.nan, 4.0], index=range(0, 4))
    out = apply_window(s, b0=0, n_buckets=4)
    assert len(out) == 4
    assert int(out.isna().sum()) == 2


def test_apply_window_chuoi_rong_tra_rong():
    out = apply_window(pd.Series(dtype=float), b0=0, n_buckets=WINDOW_BUCKETS)
    assert len(out) == 0


# ======================================================= interpolate_short

def test_interpolate_short_cum_2_duoc_noi_suy_cum_3_giu_nguyen():
    """K = 2: cụm NaN dài 2 được nội suy, cụm dài 3 giữ nguyên NaN."""
    s = pd.Series([1.0, np.nan, np.nan, 4.0,
                   10.0, np.nan, np.nan, np.nan, 20.0])
    out, n_interp = interpolate_short(s, k=2)

    assert not out.iloc[1:3].isna().any(), "cụm dài 2 phải được nội suy"
    assert out.iloc[5:8].isna().all(), "cụm dài 3 phải giữ nguyên NaN"
    assert n_interp == 2, "chỉ đếm số điểm thực sự nội suy"


def test_interpolate_short_khong_tao_doan_phang_kieu_ffill():
    """Nội suy TUYẾN TÍNH, không ffill.

    Cụm 2 điểm giữa 1.0 và 4.0 phải ra 2.0 và 3.0. Nếu ra 1.0 và 1.0 thì đó là
    forward-fill — nó tạo đoạn phẳng làm autocorrelation tăng giả tạo, mà
    autocorrelation là đại lượng trung tâm của RQ3 (QĐ-008).
    """
    s = pd.Series([1.0, np.nan, np.nan, 4.0])
    out, n_interp = interpolate_short(s, k=2)

    assert out.tolist() == [1.0, 2.0, 3.0, 4.0]
    assert out.iloc[1] != out.iloc[0], "giá trị lặp lại điểm trái = ffill"
    assert n_interp == 2


def test_interpolate_short_noi_suy_dung_ca_khi_chuoi_di_xuong():
    """Nội suy phải theo đúng độ dốc, kể cả khi đoạn giảm."""
    s = pd.Series([4.0, np.nan, 2.0])
    out, _ = interpolate_short(s, k=2)
    assert out.tolist() == [4.0, 3.0, 2.0]


def test_interpolate_short_k0_khong_noi_suy_gi():
    """K = 0 là chế độ kiểm độ vững ở GĐ4: giữ nguyên mọi NaN."""
    s = pd.Series([1.0, np.nan, 3.0, np.nan, np.nan, 6.0])
    out, n_interp = interpolate_short(s, k=0)

    assert n_interp == 0
    assert out.isna().tolist() == s.isna().tolist()
    pd.testing.assert_series_equal(out, s)


def test_interpolate_short_nan_dau_va_cuoi_khong_bi_noi_suy():
    """Thiếu neo một phía thì không nội suy — ngoại suy là bịa dữ liệu."""
    s = pd.Series([np.nan, 2.0, 3.0, np.nan])
    out, n_interp = interpolate_short(s, k=2)

    assert np.isnan(out.iloc[0]), "NaN đầu chuỗi không có neo trái"
    assert np.isnan(out.iloc[-1]), "NaN cuối chuỗi không có neo phải"
    assert n_interp == 0


def test_interpolate_short_nan_dau_cuoi_ngan_van_khong_noi_suy_khi_k_lon():
    """Kể cả khi K rộng hơn cụm, cụm ở mép vẫn phải giữ NaN."""
    s = pd.Series([np.nan, np.nan, 5.0, 6.0, np.nan, np.nan])
    out, n_interp = interpolate_short(s, k=10)
    assert out.isna().tolist() == [True, True, False, False, True, True]
    assert n_interp == 0


def test_interpolate_short_cum_dai_bang_k_van_duoc_noi_suy():
    """Biên của K là `<=`: cụm dài đúng K vẫn nội suy, dài K+1 thì không."""
    bang_k = pd.Series([0.0, np.nan, np.nan, 3.0])
    hon_k = pd.Series([0.0, np.nan, np.nan, np.nan, 4.0])

    out_bang, n_bang = interpolate_short(bang_k, k=2)
    out_hon, n_hon = interpolate_short(hon_k, k=2)

    assert n_bang == 2 and not out_bang.isna().any()
    assert n_hon == 0 and out_hon.isna().sum() == 3


def test_interpolate_short_giu_index_va_ten_chuoi():
    """Index bucket và tên chuỗi phải sống sót qua bước nội suy."""
    s = pd.Series([1.0, np.nan, 3.0], index=[100, 101, 102], name="E2_2013-8_1")
    out, _ = interpolate_short(s, k=2)
    assert list(out.index) == [100, 101, 102]
    assert out.name == "E2_2013-8_1"


def test_interpolate_short_khong_sua_chuoi_goc():
    """Hàm trả chuỗi mới, không sửa tại chỗ — chuỗi gốc còn dùng để đối chiếu."""
    s = pd.Series([1.0, np.nan, np.nan, 4.0])
    truoc = s.copy()
    interpolate_short(s, k=2)
    pd.testing.assert_series_equal(s, truoc)


def test_interpolate_short_dem_dung_tren_nhieu_cum():
    """`n_interp` là số điểm được nội suy, dùng để báo tỉ lệ can thiệp."""
    s = pd.Series([1.0, np.nan, 3.0, np.nan, np.nan, 6.0,
                   np.nan, np.nan, np.nan, 10.0])
    out, n_interp = interpolate_short(s, k=2)
    assert n_interp == 3, "cụm 1 + cụm 2 được nội suy, cụm 3 thì không"
    assert int(out.isna().sum()) == 3


# ========================================================= count_valid_rows

def test_count_valid_rows_chuoi_sach_100_diem():
    """100 điểm sạch, max_lag=24, h=1 -> 75 dòng."""
    s = chuoi_bien_thien(100)
    assert count_valid_rows(s, max_lag=MAX_LAG, h=1) == 75


def test_count_valid_rows_mot_nan_o_giua():
    """Thêm 1 NaN ở index 50 -> còn 49 dòng.

    Mất 26: 25 dòng có NaN trong cửa sổ `[t-24, t]`, cộng 1 dòng có target trúng
    index 50. Đây chính là lý do bước nội suy lỗ hổng ngắn tồn tại (protocol mục 8).
    """
    s = chuoi_bien_thien(100)
    s.iloc[50] = np.nan
    assert count_valid_rows(s, max_lag=MAX_LAG, h=1) == 49


def test_count_valid_rows_horizon_lon_hon_mat_nhieu_dong_hon():
    """Cùng chuỗi sạch, h càng xa thì càng ít dòng: n - max_lag - h."""
    s = chuoi_bien_thien(100)
    assert count_valid_rows(s, max_lag=MAX_LAG, h=6) == 70
    assert count_valid_rows(s, max_lag=MAX_LAG, h=12) == 64


def test_count_valid_rows_nan_o_dau_chuoi_chi_hong_cua_so_dau():
    """NaN ở index 0 làm hỏng đúng 1 dòng (chỉ dòng t=24 chứa nó)."""
    s = chuoi_bien_thien(100)
    s.iloc[0] = np.nan
    assert count_valid_rows(s, max_lag=MAX_LAG, h=1) == 74


def test_count_valid_rows_chuoi_qua_ngan_tra_0():
    """Không đủ (max_lag + h + 1) điểm thì không có dòng nào hợp lệ."""
    assert count_valid_rows(chuoi_bien_thien(20), max_lag=MAX_LAG, h=1) == 0
    assert count_valid_rows(chuoi_bien_thien(25), max_lag=MAX_LAG, h=1) == 0
    assert count_valid_rows(chuoi_bien_thien(26), max_lag=MAX_LAG, h=1) == 1


def test_count_valid_rows_toan_nan_tra_0():
    s = pd.Series([np.nan] * 100)
    assert count_valid_rows(s, max_lag=MAX_LAG, h=1) == 0


def test_count_valid_rows_yeu_cau_ca_cua_so_lan_target():
    """Kiểm trực tiếp hai điều kiện của protocol mục 8 trên chuỗi tí hon."""
    # max_lag=2, h=1, n=6 -> t chạy 2,3,4 (3 dòng)
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    assert count_valid_rows(s, max_lag=2, h=1) == 3

    # NaN tại target của dòng t=4 (index 5) -> mất 1 dòng
    s_target = s.copy()
    s_target.iloc[5] = np.nan
    assert count_valid_rows(s_target, max_lag=2, h=1) == 2

    # NaN tại index 3 nằm trong cửa sổ của t=3,4 và là target của t=2 -> mất cả 3
    s_window = s.copy()
    s_window.iloc[3] = np.nan
    assert count_valid_rows(s_window, max_lag=2, h=1) == 0


# ==================================================================== judge

def test_judge_tra_dung_bon_ma_ly_do(cfg):
    """Bốn tình huống, bốn mã — theo protocol mục 6 bước 7."""
    truong_hop = {
        # 1. không có mẫu nào trong cửa sổ (chuỗi rỗng sau apply_window)
        "ngoai_cua_so": pd.Series([np.nan] * WINDOW_BUCKETS),
        # 2. CPU% trung bình < 1,0
        "gan_chet": chuoi_bien_thien(WINDOW_BUCKETS, base=0.1, buoc=0.01),
        # 3. chuỗi hằng, chỉ 1 giá trị phân biệt
        "hang": pd.Series([50.0] * WINDOW_BUCKETS),
        # 4. quá ngắn nên dưới 500 dòng hợp lệ ở h=12
        "it_dong": chuoi_bien_thien(200),
    }
    for ma_mong_doi, s in truong_hop.items():
        assert judge(s, cfg=cfg) == ma_mong_doi


def test_judge_giu_chuoi_lanh(cfg):
    """Chuỗi đủ dài, biến thiên, CPU% cao -> giữ lại (trả None)."""
    assert judge(chuoi_bien_thien(WINDOW_BUCKETS), cfg=cfg) is None


def test_judge_chuoi_rong_la_ngoai_cua_so(cfg):
    """`apply_window` trả rỗng thì lý do phải là `ngoai_cua_so`, không phải mã khác."""
    assert judge(pd.Series(dtype=float), cfg=cfg) == "ngoai_cua_so"


def test_judge_xet_dung_thu_tu_uu_tien(cfg):
    """Chuỗi vi phạm nhiều điều kiện phải mang mã ĐẦU TIÊN trong thứ tự protocol.

    Bốn lý do được báo cáo thành bốn cột tách riêng, nên thứ tự xét phải ổn định,
    nếu không cùng một tập dữ liệu sẽ cho hai bảng thống kê khác nhau.
    """
    # vừa gần chết vừa hằng vừa ngắn -> gan_chet (xét trước)
    assert judge(pd.Series([0.5] * 100), cfg=cfg) == "gan_chet"
    # vừa hằng vừa ngắn (nhưng CPU% cao) -> hang (xét trước it_dong)
    assert judge(pd.Series([50.0] * 100), cfg=cfg) == "hang"


def test_judge_bien_gan_chet_la_nho_hon_khong_phai_nho_hon_bang(cfg):
    """'trung bình DƯỚI 1,0' — đúng 1,0 thì giữ."""
    s = pd.Series([0.5, 1.0, 1.5] * (WINDOW_BUCKETS // 3))
    assert abs(s.mean() - 1.0) < 1e-12
    assert judge(s, cfg=cfg) is None


def test_judge_bien_hang_la_tu_2_gia_tri_tro_xuong(cfg):
    """'số giá trị phân biệt từ 2 trở xuống' -> 2 là hằng, 3 thì không."""
    hai_gia_tri = pd.Series([50.0, 60.0] * (WINDOW_BUCKETS // 2))
    ba_gia_tri = pd.Series([50.0, 60.0, 70.0] * (WINDOW_BUCKETS // 3))
    assert judge(hai_gia_tri, cfg=cfg) == "hang"
    assert judge(ba_gia_tri, cfg=cfg) is None


def test_judge_bien_it_dong_dung_500_dong(cfg):
    """Ngưỡng là 'dưới 500' ở h=12: đúng 500 thì giữ, 499 thì loại."""
    # n - max_lag - h = 536 - 24 - 12 = 500
    du_500 = chuoi_bien_thien(536)
    thieu_1 = chuoi_bien_thien(535)

    assert count_valid_rows(du_500, max_lag=MAX_LAG, h=12) == 500
    assert count_valid_rows(thieu_1, max_lag=MAX_LAG, h=12) == 499
    assert judge(du_500, cfg=cfg) is None
    assert judge(thieu_1, cfg=cfg) == "it_dong"


def test_judge_dem_it_dong_o_h12_khong_phai_h1(cfg):
    """Ngưỡng đếm ở h = 12. Nếu code đếm ở h = 1 thì chuỗi này sẽ lọt."""
    # h=1 -> 511 dòng (qua ngưỡng), h=12 -> 500... chọn n sao cho hai bên khác phía
    n = 535     # h=1 -> 510, h=12 -> 499
    s = chuoi_bien_thien(n)
    assert count_valid_rows(s, max_lag=MAX_LAG, h=1) == 510
    assert count_valid_rows(s, max_lag=MAX_LAG, h=12) == 499
    assert judge(s, cfg=cfg) == "it_dong"


def test_judge_nan_rai_rac_lam_chuoi_bi_loai_vi_it_dong(cfg):
    """NaN rải đều làm hỏng dòng huấn luyện dù chuỗi vẫn dài và vẫn biến thiên."""
    s = chuoi_bien_thien(WINDOW_BUCKETS)
    s.iloc[::20] = np.nan       # mỗi 20 điểm một NaN -> không cửa sổ 25 điểm nào sạch
    assert count_valid_rows(s, max_lag=MAX_LAG, h=12) == 0
    assert judge(s, cfg=cfg) == "it_dong"


# ============================================================ cấu hình gốc

def test_cau_hinh_khop_voi_protocol(cfg):
    """Ngưỡng nằm trong config, không chôn trong code — và không được trôi."""
    assert cfg.get("grid_seconds") == 300              # mục 5
    assert cfg.get("window", {}).get("days") == 8      # mục 7
    assert cfg.get("window", {}).get("origin") == "env_global"   # QĐ-008
    assert cfg.get("gap", {}).get("max_len") == 2      # mục 6 bước 6
    assert cfg.get("gap", {}).get("method") == "linear_interp"
    assert "ffill" not in str(cfg.get("gap", {})), "QĐ-008 cấm forward-fill"
    assert cfg.get("clip") == [0, 100]                 # mục 6 bước 1
    assert cfg.get("filter", {}).get("min_mean") == 1.0
    assert cfg.get("filter", {}).get("min_unique") == 3
    assert cfg.get("filter", {}).get("min_valid_rows_h12") == 500
    assert cfg.get("row_validity", {}).get("max_lag") == 24   # mục 8


def test_cua_so_8_ngay_dung_2304_bucket(cfg):
    """8 ngày / 5 phút = 2304 bucket — con số protocol mục 7 viết thẳng ra."""
    days = cfg["window"]["days"]
    grid = cfg["grid_seconds"]
    assert int(days * 86400 // grid) == WINDOW_BUCKETS
