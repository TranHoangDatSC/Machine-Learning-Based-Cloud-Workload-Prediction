"""Kiểm `cwp.preprocess.normalize` — ba chế độ chuẩn hoá của mục 14 và QĐ-016.

Chạy:  pytest tests/test_normalize.py -v

Không dùng dữ liệu thật, tự tạo chuỗi nhỏ tính tay được.

**Vì sao bộ test này khác các giai đoạn trước.** GĐ2 sợ rò rỉ đặc trưng và GĐ3 sợ áp
lực để ML thắng naive — cả hai đều làm số **xấu đi** hoặc làm test **đỏ** khi sai.
Chuẩn hoá sai thì ngược lại: chương trình chạy trơn, không lỗi, và số liệu **đẹp lên**.
Nên phần lõi ở đây là **ba bất biến đúng vì toán học**, không phải vì hai bản khớp
nhau:

    naive ở N0  ==  naive ở N1 sau khi map ngược      (z-score là affine)
    ma6   ở N0  ==  ma6   ở N1 sau khi map ngược      (trung bình của z là z của trung bình)
    naive ở N0  ==  naive ở N2 với Δ̂ = 0              (ŷ = y_t + 0)

Cộng phép kiểm trực tiếp cho quy ước 1 của QĐ-016: đổi `y` ở vùng validation và test
thì `mu`, `sd` **không được đổi**.
"""

import numpy as np
import pytest

from cwp.preprocess.normalize import (
    MODES,
    TRAIN_END,
    bien_doi,
    chuan_hoa_duoc,
    map_nguoc,
    thong_ke_train,
)

W = 2304  # protocol mục 7, cửa sổ 8 ngày


def chuoi_mau(seed: int = 42, n: int = W) -> np.ndarray:
    """Chuỗi giả lập: nền tuần hoàn ngày + nhiễu, kẹp về thang CPU% 0–100."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    y = 40 + 15 * np.sin(2 * np.pi * t / 288) + rng.normal(0, 3, n)
    return np.clip(y, 0.0, 100.0)


def naive(y: np.ndarray) -> np.ndarray:
    """Persistence: dự đoán tại `t` là chính `y_t`. Căn theo chỉ số gốc."""
    return np.asarray(y, dtype="float64").copy()


def ma6(y: np.ndarray) -> np.ndarray:
    """Trung bình 6 điểm quá khứ `y[t-5..t]`. Thiếu điểm thì NaN."""
    a = np.asarray(y, dtype="float64")
    out = np.full(a.shape, np.nan)
    for i in range(5, a.size):
        out[i] = a[i - 5 : i + 1].mean()
    return out


# ======================================================= ba bất biến bắt buộc

def test_bat_bien_1_naive_N0_bang_naive_N1_sau_map_nguoc():
    """z-score là phép affine, nên persistence không đổi khi đi vòng qua N1."""
    y = chuoi_mau()
    goc = naive(y)
    z = bien_doi(y, "N1")
    qua_n1 = map_nguoc(naive(z), y, "N1")

    lech = np.nanmax(np.abs(goc - qua_n1))
    assert lech < 1e-9, f"naive N0 và N1 lệch {lech:.3e}, phải dưới 1e-9"


def test_bat_bien_2_ma6_N0_bang_ma6_N1_sau_map_nguoc():
    """Trung bình của z bằng z của trung bình — vẫn là affine."""
    y = chuoi_mau()
    goc = ma6(y)
    z = bien_doi(y, "N1")
    qua_n1 = map_nguoc(ma6(z), y, "N1")

    lech = np.nanmax(np.abs(goc - qua_n1))
    assert lech < 1e-9, f"ma6 N0 và N1 lệch {lech:.3e}, phải dưới 1e-9"


def test_bat_bien_3_naive_N0_bang_N2_voi_delta_hat_bang_0():
    """`ŷ = y_t + 0` đúng bằng persistence. Phép cộng đúng thì lệch phải BẰNG 0."""
    y = chuoi_mau()
    goc = naive(y)
    qua_n2 = map_nguoc(np.zeros_like(y), y, "N2")

    assert np.array_equal(goc, qua_n2), "N2 với Δ̂ = 0 phải trùng naive TUYỆT ĐỐI"
    assert float(np.nanmax(np.abs(goc - qua_n2))) == 0.0


# ============================ quy ước 1 của QĐ-016 — cửa sổ train, không phải toàn chuỗi

def test_mu_sd_chi_tinh_tren_cua_so_train():
    """Đổi `y` ở bucket ≥ 1612 thì `mu`, `sd` KHÔNG được đổi.

    Đây là phép kiểm trực tiếp cho chỗ dễ sai nhất của GĐ4. Tính `mu`/`sd` trên toàn
    chuỗi là rò rỉ — nó dùng thông tin của validation và test để chuẩn hoá, và nó
    **không làm chương trình báo lỗi**, chỉ làm kết quả đẹp bất thường.
    """
    y = chuoi_mau()
    mu0, sd0 = thong_ke_train(y)

    doi = y.copy()
    doi[TRAIN_END:] = 999.0          # phá tan vùng val + test
    mu1, sd1 = thong_ke_train(doi)

    assert mu0 == mu1, f"mu đổi khi sửa vùng ngoài train: {mu0} -> {mu1}"
    assert sd0 == sd1, f"sd đổi khi sửa vùng ngoài train: {sd0} -> {sd1}"


def test_toan_chuoi_cho_mu_sd_KHAC_cua_so_train():
    """Phép kiểm ngược: nếu hai cách cho cùng số thì test trên vô nghĩa."""
    y = chuoi_mau()
    mu_train, sd_train = thong_ke_train(y)
    mu_toan = float(np.nanmean(y))
    sd_toan = float(np.nanstd(y, ddof=1))

    assert not np.isclose(mu_train, mu_toan) or not np.isclose(sd_train, sd_toan), (
        "Chuỗi mẫu này không phân biệt được hai cách tính — đổi chuỗi mẫu đi, "
        "nếu không test cửa sổ train chẳng chứng minh gì"
    )


def test_z_score_tren_cua_so_train_co_trung_binh_0_do_lech_1():
    """Kiểm định nghĩa: z của phần train phải có mean ≈ 0, sd ≈ 1."""
    y = chuoi_mau()
    z = bien_doi(y, "N1")
    tr = z[:TRAIN_END]

    assert abs(float(np.nanmean(tr))) < 1e-12
    assert abs(float(np.nanstd(tr, ddof=1)) - 1.0) < 1e-12


# ================================================= sd = 0, chuỗi hằng

def test_chuoi_hang_thi_N1_khong_xac_dinh_va_KHONG_bi_lap():
    """`sd = 0` phải ra NaN — không thay bằng 0, không cộng epsilon (QĐ-016)."""
    y = np.full(W, 7.5)
    mu, sd = thong_ke_train(y)

    assert mu == 7.5 and sd == 0.0
    assert chuan_hoa_duoc(y) is False

    z = bien_doi(y, "N1")
    assert np.isnan(z).all(), "chuỗi hằng phải cho NaN trọn vẹn, không phải 0"
    assert not (z == 0).any(), "thay sd=0 bằng epsilon hoặc bằng 0 là bịa dữ liệu"


def test_chuoi_binh_thuong_thi_chuan_hoa_duoc():
    assert chuan_hoa_duoc(chuoi_mau()) is True


# =========================================================== N2 và sai phân

def test_N2_la_sai_phan_mot_buoc_va_diem_dau_la_NaN():
    y = np.array([1.0, 3.0, 6.0, 10.0])
    d = bien_doi(y, "N2")

    assert np.isnan(d[0]), "không có y_{-1} nên điểm đầu phải là NaN"
    assert d[1:].tolist() == [2.0, 3.0, 4.0]


def test_N2_map_nguoc_cong_lai_dung_moc_neo():
    y = np.array([10.0, 12.0, 9.0, 15.0])
    delta = np.array([0.5, -1.0, 2.0, 0.0])
    assert map_nguoc(delta, y, "N2").tolist() == [10.5, 11.0, 11.0, 15.0]


def test_N2_doi_dai_khac_nhau_thi_bao_loi():
    """Căn theo chỉ số, nên lệch độ dài là lỗi lập trình — phải nổ, đừng broadcast."""
    with pytest.raises(ValueError):
        map_nguoc(np.zeros(3), np.zeros(4), "N2")


# ================================================================ N0 và chung

def test_N0_khong_doi_gi_ca():
    y = chuoi_mau()
    assert np.array_equal(bien_doi(y, "N0"), y)
    assert np.array_equal(map_nguoc(y, y, "N0"), y)


def test_bien_doi_giu_nguyen_do_dai_o_ca_ba_che_do():
    y = chuoi_mau()
    for m in MODES:
        assert bien_doi(y, m).shape == y.shape


def test_khong_sua_chuoi_goc():
    """Ba hàm phải trả mảng mới — chuỗi gốc còn dùng để map ngược."""
    y = chuoi_mau()
    truoc = y.copy()
    for m in MODES:
        bien_doi(y, m)
        map_nguoc(np.zeros_like(y), y, m)
    assert np.array_equal(y, truoc)


def test_che_do_la_thi_bao_loi():
    y = chuoi_mau()
    # `"n0 "` KHÔNG nằm ở đây: khoảng trắng thừa được strip, xem test kế tiếp.
    for xau in ["N3", "", "z-score", "N", "0"]:
        with pytest.raises(ValueError):
            bien_doi(y, xau)
        with pytest.raises(ValueError):
            map_nguoc(y, y, xau)


def test_ten_che_do_khong_phan_biet_hoa_thuong():
    y = chuoi_mau()
    assert np.array_equal(bien_doi(y, "n1"), bien_doi(y, "N1"))


# ============================================== NaN trong chuỗi, QĐ-008 còn lỗ hổng

def test_NaN_trong_train_khong_keo_mu_ve_0():
    """Lỗ hổng dài không nội suy vẫn còn sau QĐ-008 — phải bỏ qua, không coi là 0."""
    y = chuoi_mau()
    y[100:110] = np.nan
    mu, sd = thong_ke_train(y)

    sach = y[:TRAIN_END][np.isfinite(y[:TRAIN_END])]
    assert abs(mu - float(sach.mean())) < 1e-12
    assert abs(sd - float(sach.std(ddof=1))) < 1e-12


def test_train_duoi_hai_diem_hop_le_thi_tra_NaN():
    y = np.full(W, np.nan)
    y[0] = 5.0
    mu, sd = thong_ke_train(y)
    assert np.isnan(mu) and np.isnan(sd)
    assert chuan_hoa_duoc(y) is False


def test_bat_bien_van_dung_khi_chuoi_co_NaN():
    """Ba bất biến phải sống sót qua lỗ hổng, vì dữ liệu thật có lỗ hổng."""
    y = chuoi_mau()
    y[500:503] = np.nan
    y[1800] = np.nan

    z = bien_doi(y, "N1")
    lech = np.nanmax(np.abs(naive(y) - map_nguoc(naive(z), y, "N1")))
    assert lech < 1e-9

    qua_n2 = map_nguoc(np.zeros_like(y), y, "N2")
    assert np.array_equal(np.isnan(qua_n2), np.isnan(y))
    ok = np.isfinite(y)
    assert np.array_equal(qua_n2[ok], y[ok])
