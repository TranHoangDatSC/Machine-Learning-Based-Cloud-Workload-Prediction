"""Kiểm `cwp.models.baselines` — ba baseline của `docs/protocol.md` mục 11.

Chạy:  pytest tests/test_baselines.py -v

Không dùng dữ liệu thật. Mọi chuỗi ở đây tự tạo và tính tay được.

Ba baseline **không có yếu tố ngẫu nhiên nào** — không seed, không siêu tham số,
không huấn luyện. `gate-gd3.md` mục 2.3 neo 27 con số MAE vào chúng, và phụ lục của
cổng nói rõ vì sao: mọi kết luận của GĐ3 đều có dạng *"model X tốt hơn naive bao
nhiêu"*, nên một baseline sai làm sai **toàn bộ** bảng kết quả mà không phép kiểm nào
khác bắt được.

Bốn cam kết được kiểm ở đây:

    N1  naive lấy đúng `y_t`, dựng từ `lag_1 + diff_1` — không lệch một bước.
    N2  ma6 lấy đúng trung bình 6 điểm **quá khứ**, không gồm điểm hiện tại.
    N3  seasonal lấy đúng `y_{t-288}` theo khoá `(series_id, bucket − 288)`, không
        bắc cầu sang chuỗi khác.
    N4  Thiếu `y_{t-288}` thì trả **NaN**, không ffill, không lấp bằng `y_t`.

N4 là chỗ `pha_gd3.py` P5 phá: lấp giá trị thiếu bằng ffill thì tỉ lệ dòng bỏ của E3
tụt từ 0,43% xuống 0%, và protocol mục 11 đòi xử lý **hiện** chứ không lặng lẽ.
"""

import numpy as np
import pandas as pd
import pytest

from cwp.features import make_feature_matrix
from cwp.models.baselines import (
    BASELINE_NAMES,
    MA_WINDOW,
    SEASONAL_LAG,
    du_doan,
    du_doan_ma6,
    du_doan_naive,
    du_doan_seasonal,
    y_hien_tai,
)

B0 = 4587716  # bucket đầu của E1 trong sản phẩm GĐ1


def bang(y, series_id="A", b0=B0):
    """Bảng dài một chuỗi, đúng schema `data/processed/` (protocol mục 6b)."""
    y = np.asarray(y, dtype=float)
    return pd.DataFrame({
        "series_id": [series_id] * len(y),
        "bucket": np.arange(b0, b0 + len(y), dtype="int64"),
        "y": y,
    })


@pytest.fixture
def chuoi_dai():
    """Một chuỗi 700 điểm, đủ dài để `t − 288` tồn tại ở phần đuôi."""
    rng = np.random.default_rng(0)
    return bang(np.abs(rng.normal(20, 5, size=700)))


# ------------------------------------------------------------------ N1 naive

def test_N1_y_hien_tai_dung_bang_y_tai_t():
    """`lag_1 + diff_1` phải dựng lại đúng `y_t`, không phải `y_{t-1}` hay `y_{t+1}`."""
    df = bang(np.arange(1, 60, dtype=float) * 1.7)
    X = make_feature_matrix(df, h=1)
    goc = df.set_index("bucket")["y"]
    mong_doi = goc.reindex(X["bucket"]).to_numpy()
    assert np.allclose(y_hien_tai(X), mong_doi, atol=1e-9)


def test_N1_naive_khong_lech_mot_buoc():
    """Lệch một bước là kiểu sai im lặng nhất: MAE vẫn ra số trông hợp lý."""
    df = bang(np.arange(1, 60, dtype=float) * 1.7)
    X = make_feature_matrix(df, h=1)
    yhat = du_doan_naive(X)
    assert np.allclose(yhat, X["lag_1"] + X["diff_1"], atol=0)
    # `y_t` phải KHÁC `lag_1`; nếu bằng nhau thì đã lấy nhầm một bước.
    assert not np.allclose(yhat, X["lag_1"].to_numpy())


def test_N1_naive_tren_chuoi_hang_bang_dung_hang_so():
    df = bang(np.full(60, 3.25))
    X = make_feature_matrix(df, h=1)
    assert np.allclose(du_doan_naive(X), 3.25)


def test_N1_thieu_cot_thi_bao_loi():
    with pytest.raises(ValueError, match="lag_1|diff_1"):
        du_doan_naive(pd.DataFrame({"roll_mean_6": [1.0]}))


# -------------------------------------------------------------------- N2 ma6

def test_N2_ma6_la_trung_binh_sau_diem_qua_khu():
    """Cửa sổ `[t-6, t-1]`, **không** gồm `y_t` (protocol mục 8 và mục 11 trùng nhau)."""
    y = np.arange(1, 60, dtype=float)
    df = bang(y)
    X = make_feature_matrix(df, h=1)
    yhat = du_doan_ma6(X)
    goc = df.set_index("bucket")["y"]
    for i, b in enumerate(X["bucket"].to_numpy()[:5]):
        cua_so = goc.loc[b - MA_WINDOW: b - 1].to_numpy()
        assert len(cua_so) == MA_WINDOW
        assert yhat[i] == pytest.approx(cua_so.mean())


def test_N2_ma6_khong_nuot_diem_hien_tai():
    """Nếu cửa sổ lỡ gồm `y_t` thì trên chuỗi tăng đều, ma6 sẽ lệch đúng 0,5 đơn vị."""
    df = bang(np.arange(1, 60, dtype=float))
    X = make_feature_matrix(df, h=1)
    dung = du_doan_ma6(X)
    sai = dung + 0.5  # đúng thứ mà cửa sổ [t-5, t] sẽ cho
    assert not np.allclose(dung, sai)
    assert np.allclose(dung, y_hien_tai(X) - 3.5)  # trung bình 6 điểm trước t


def test_N2_ma6_chinh_la_roll_mean_6(chuoi_dai):
    X = make_feature_matrix(chuoi_dai, h=6)
    assert np.array_equal(du_doan_ma6(X), X["roll_mean_6"].to_numpy())


# --------------------------------------------------------------- N3/N4 seasonal

def test_N3_seasonal_lay_dung_y_cua_288_bucket_truoc(chuoi_dai):
    X = make_feature_matrix(chuoi_dai, h=1)
    yhat = du_doan_seasonal(X, chuoi_dai)
    goc = chuoi_dai.set_index("bucket")["y"]
    co = X["bucket"].to_numpy() - SEASONAL_LAG >= chuoi_dai["bucket"].min()
    mong_doi = goc.reindex(X["bucket"].to_numpy() - SEASONAL_LAG).to_numpy()
    assert np.array_equal(yhat[co], mong_doi[co])


def test_N3_seasonal_khong_bac_cau_sang_chuoi_khac():
    """Hai chuỗi cùng dải bucket, giá trị khác hẳn nhau — nối sai khoá thì lộ ngay."""
    rng = np.random.default_rng(1)
    a = bang(rng.uniform(0, 1, 400), series_id="A")
    b = bang(rng.uniform(90, 100, 400), series_id="B")
    df = pd.concat([a, b], ignore_index=True)
    X = make_feature_matrix(df, h=1)
    yhat = du_doan_seasonal(X, df)
    la_a = (X["series_id"] == "A").to_numpy()
    co = np.isfinite(yhat)
    assert (yhat[la_a & co] < 1.0).all(), "chuỗi A nhận giá trị của chuỗi B"
    assert (yhat[~la_a & co] > 90.0).all(), "chuỗi B nhận giá trị của chuỗi A"


def test_N4_thieu_y_cua_288_buoc_truoc_thi_tra_NaN():
    """288 bucket đầu mỗi chuỗi không có `y_{t-288}` — phải là NaN, không được lấp."""
    df = bang(np.arange(1, 400, dtype=float))
    X = make_feature_matrix(df, h=1)
    yhat = du_doan_seasonal(X, df)
    som = X["bucket"].to_numpy() - SEASONAL_LAG < df["bucket"].min()
    assert som.any(), "ca kiểm không có ý nghĩa nếu mọi dòng đều đủ lịch sử"
    assert np.isnan(yhat[som]).all()
    # Và cụ thể: KHÔNG được bằng `y_t` (lấp bằng persistence) hay bằng điểm đầu chuỗi.
    assert not np.allclose(yhat[som], y_hien_tai(X)[som], equal_nan=True)


def test_N4_diem_NaN_trong_processed_cung_ra_NaN():
    """`y_{t-288}` tồn tại nhưng là NaN thì cũng phải trả NaN, không ffill."""
    y = np.arange(1, 700, dtype=float)
    y[300] = np.nan
    df = bang(y)
    X = make_feature_matrix(df, h=1)
    yhat = du_doan_seasonal(X, df)
    dich = df["bucket"].iloc[300] + SEASONAL_LAG
    vi_tri = X.index[X["bucket"] == dich]
    if len(vi_tri):  # dòng đó có thể đã bị luật mục 8 loại; chỉ kiểm khi nó còn
        assert np.isnan(yhat[vi_tri[0]])


def test_N4_khong_lam_doi_luat_dong_hop_le():
    """Seasonal naive **không** được siết luật dòng hợp lệ thành `t >= b0 + 288`.

    protocol mục 11 cấm thẳng: làm thế sẽ đổi cả chín neo số dòng của GĐ1 và GĐ2.
    """
    df = bang(np.arange(1, 400, dtype=float))
    truoc = len(make_feature_matrix(df, h=1))
    du_doan_seasonal(make_feature_matrix(df, h=1), df)
    assert len(make_feature_matrix(df, h=1)) == truoc


def test_N4_khong_them_lag_288_vao_bo_dac_trung():
    """Bộ đặc trưng vẫn đúng 19 cột + 3; thêm `lag_288` là đổi giao thức (mục 11)."""
    df = bang(np.arange(1, 700, dtype=float))
    X = make_feature_matrix(df, h=1)
    assert len(X.columns) == 22
    assert not [c for c in X.columns if "288" in c]


# ------------------------------------------------------------------ hợp đồng

def test_du_doan_goi_dung_ba_baseline(chuoi_dai):
    X = make_feature_matrix(chuoi_dai, h=1)
    assert BASELINE_NAMES == ("naive", "ma6", "seasonal")
    assert np.array_equal(du_doan("naive", X, chuoi_dai), du_doan_naive(X))
    assert np.array_equal(du_doan("ma6", X, chuoi_dai), du_doan_ma6(X))
    assert np.array_equal(du_doan("seasonal", X, chuoi_dai),
                          du_doan_seasonal(X, chuoi_dai), equal_nan=True)


def test_seasonal_thieu_processed_thi_bao_loi_chu_khong_doan_bua(chuoi_dai):
    X = make_feature_matrix(chuoi_dai, h=1)
    with pytest.raises(ValueError, match="lag_288|processed"):
        du_doan("seasonal", X)


def test_ten_baseline_la_thi_bao_loi(chuoi_dai):
    X = make_feature_matrix(chuoi_dai, h=1)
    with pytest.raises(ValueError):
        du_doan("arima", X)


def test_khong_baseline_nao_dung_toi_random_state():
    """Không seed, không siêu tham số — phụ lục `gate-gd3.md` neo vào đúng điều này."""
    import inspect
    import io
    import tokenize

    import cwp.models.baselines as m

    ma = " ".join(
        tok.string
        for tok in tokenize.generate_tokens(io.StringIO(inspect.getsource(m)).readline)
        if tok.type not in (tokenize.COMMENT, tokenize.STRING)
    )
    for tu in ("random", "seed", "fit", "shuffle"):
        assert tu not in ma, f"baselines.py khong duoc dung {tu!r} (muc 11)"
