"""Kiểm `cwp.evaluation.metrics` — năm chỉ số của mục 12, chốt ở QĐ-013 điểm 3–5.

Chạy:  pytest tests/test_metrics.py -v

Mọi ca ở đây **tính tay được**. Đó là chủ ý: `gate-gd3.md` mục 4 xếp loại phép kiểm
"đáp án giải tích" là loại **không** phụ thuộc tính độc lập của thước đo, nên nó giữ
nguyên giá trị kể cả khi hai bản hiện thực cùng sai một kiểu.

Ba ca biên mà `brief-gd3-b.md` Bước 2 gọi đích danh:

    C5  `|y| + |ŷ| = 0`  -> SMAPE của số hạng đó bằng **0**
    C9  train phẳng      -> MASE là **NaN**, không phải vô cực
    C10 test hằng        -> R² là **NaN**

C9 và C10 kiểm bằng `isnan`, **không** bằng `not isfinite` — `inf` cũng không hữu
hạn, nên một bản chia cho 0 rồi trả `inf` sẽ lọt qua phép kiểm viết bằng `isfinite`,
rồi `inf` trôi vào trung vị và bôi đen cả cột (đính chính QĐ-014 điểm 3).
"""

from math import isnan, sqrt

import numpy as np
import pandas as pd
import pytest

from cwp.evaluation.metrics import (
    METRIC_NAMES,
    gop,
    mae,
    mase,
    mase_denominator,
    mase_denominators,
    mase_denominators_train,
    per_series_metrics,
    r2,
    rmse,
    smape,
)
from cwp.evaluation.splits import WINDOW_BUCKETS, bucket_bounds


# ------------------------------------------------------------- đáp án giải tích

def test_C1_mae_tinh_tay():
    assert mae([1.0, 2.0, 3.0], [1.0, 4.0, 0.0]) == pytest.approx((0 + 2 + 3) / 3)


def test_C2_rmse_tinh_tay():
    assert rmse([1.0, 2.0, 3.0], [1.0, 4.0, 0.0]) == pytest.approx(sqrt((0 + 4 + 9) / 3))


def test_C3_rmse_luon_khong_nho_hon_mae():
    """Bất đẳng thức Jensen — đúng với mọi cặp, kiểm trên 200 cặp ngẫu nhiên."""
    rng = np.random.default_rng(42)
    for _ in range(200):
        y = rng.normal(size=25) * 10
        yhat = y + rng.normal(size=25) * rng.uniform(0, 5)
        assert rmse(y, yhat) >= mae(y, yhat) - 1e-12


def test_C4_smape_tinh_tay():
    # |2-1| / ((2+1)/2) = 2/3 ; |4-6| / ((4+6)/2) = 2/5
    assert smape([2.0, 4.0], [1.0, 6.0]) == pytest.approx(100 * (2 / 3 + 2 / 5) / 2)


def test_C5_smape_khi_ca_hai_bang_0_thi_so_hang_bang_0():
    """Ca biên quan trọng nhất với E1 và E2 — rất nhiều điểm gần 0 (QĐ-013 điểm 4)."""
    assert smape([0.0, 0.0], [0.0, 0.0]) == pytest.approx(0.0)
    # Trộn một điểm 0/0 vào: nó kéo trung bình xuống chứ không làm cả chuỗi thành NaN.
    assert smape([0.0, 2.0], [0.0, 1.0]) == pytest.approx(100 * (0 + 2 / 3) / 2)


def test_C6_smape_nam_trong_khoang_0_200():
    rng = np.random.default_rng(7)
    for _ in range(200):
        y = np.abs(rng.normal(size=20) * 30)
        yhat = np.abs(rng.normal(size=20) * 30)
        assert 0.0 <= smape(y, yhat) <= 200.0


def test_C7_r2_cua_du_doan_hoan_hao_bang_1():
    y = [1.0, 5.0, 2.0, 8.0]
    assert r2(y, y) == pytest.approx(1.0)


def test_C8_r2_cua_du_doan_hang_bang_trung_binh_thi_bang_0():
    y = np.array([1.0, 5.0, 2.0, 8.0])
    assert r2(y, np.full_like(y, y.mean())) == pytest.approx(0.0)


def test_C8b_r2_cua_du_doan_hang_khac_trung_binh_tinh_tay():
    y = np.array([1.0, 3.0])          # mean = 2, SS_tot = 2
    yhat = np.array([0.0, 0.0])       # SS_res = 1 + 9 = 10
    assert r2(y, yhat) == pytest.approx(1 - 10 / 2)


def test_C9_mase_khi_mau_so_bang_0_tra_NaN_khong_phai_inf():
    """Train phẳng hoàn toàn thì `d = 0` và MASE **không xác định** (QĐ-013 điểm 3)."""
    gia_tri = mase([1.0, 2.0], [1.5, 2.5], d=0.0)
    assert isnan(gia_tri), f"phải là NaN, nhận {gia_tri}"
    assert isnan(mase([1.0, 2.0], [1.5, 2.5], d=float("nan")))


def test_C10_r2_khi_target_hang_tra_NaN_khong_phai_inf():
    gia_tri = r2([3.0, 3.0, 3.0], [1.0, 2.0, 3.0])
    assert isnan(gia_tri), f"phải là NaN, nhận {gia_tri}"


def test_C11_mase_bang_mae_chia_d():
    assert mase([1.0, 2.0, 3.0], [1.0, 4.0, 0.0], d=2.5) == pytest.approx((5 / 3) / 2.5)


# ------------------------------------------------------------- mẫu số của MASE

def test_mau_so_mase_tinh_tay():
    # |2-1| + |5-2| + |1-5| = 1 + 3 + 4, chia 3
    assert mase_denominator([1.0, 2.0, 5.0, 1.0]) == pytest.approx(8 / 3)


def test_mau_so_mase_bo_dung_cap_dinh_NaN():
    """Cặp `(t-1, t)` chỉ được tính khi **cả hai** đầu không NaN (QĐ-013 điểm 3)."""
    # y = [1, 2, NaN, 6]: cặp hợp lệ chỉ có (1,2) -> d = 1
    assert mase_denominator([1.0, 2.0, np.nan, 6.0]) == pytest.approx(1.0)


def test_mau_so_mase_chuoi_phang_bang_0():
    assert mase_denominator([4.0, 4.0, 4.0]) == 0.0


def test_mau_so_mase_khong_du_cap_thi_NaN():
    assert isnan(mase_denominator([1.0]))
    assert isnan(mase_denominator([1.0, np.nan, 3.0, np.nan, 5.0]))


def test_mau_so_mase_chi_tinh_tren_train_khong_phai_test():
    """Chỗ P3 của `pha_gd3.py` phá: mẫu số tính nhầm trên test thì số đổi hẳn."""
    df = pd.DataFrame({
        "series_id": ["A"] * 6,
        "bucket": range(6),
        "y": [1.0, 2.0, 3.0, 100.0, 0.0, 100.0],
    })
    train = np.array([True, True, True, False, False, False])
    d = mase_denominators(df, train)
    assert d["A"] == pytest.approx(1.0)          # train: |2-1|, |3-2|
    assert mase_denominator(df["y"].to_numpy()[~train]) == pytest.approx(100.0)


def test_mau_so_mase_khong_phu_thuoc_horizon():
    """Cùng một `d` dùng cho cả h = 1, 6, 12 — nên MASE ba horizon so được với nhau."""
    df = pd.DataFrame({"series_id": ["A"] * 40, "bucket": range(40),
                       "y": np.arange(40, dtype=float) ** 1.3})
    train = np.arange(40) < 30
    d = mase_denominators(df, train)["A"]
    # Hàm không nhận tham số horizon nào cả; đây là phép kiểm chữ ký, cố ý.
    assert "h" not in mase_denominators.__code__.co_varnames
    assert d > 0


# -------------------------------------------------------- chỉ số theo từng chuỗi

@pytest.fixture
def hai_chuoi():
    """Hai chuỗi tính tay được, một chuỗi lỗi đều và một chuỗi dự đoán hoàn hảo."""
    return pd.DataFrame({
        "series_id": ["A"] * 4 + ["B"] * 4,
        "y":    [1.0, 2.0, 3.0, 4.0, 10.0, 20.0, 30.0, 40.0],
        "yhat": [2.0, 3.0, 4.0, 5.0, 10.0, 20.0, 30.0, 40.0],
    })


def test_per_series_tach_dung_tung_chuoi(hai_chuoi):
    ps = per_series_metrics(hai_chuoi["series_id"], hai_chuoi["y"], hai_chuoi["yhat"])
    assert list(ps.columns) == ["series_id", "n_dong", *METRIC_NAMES]
    a = ps.set_index("series_id").loc["A"]
    b = ps.set_index("series_id").loc["B"]
    assert a["mae"] == pytest.approx(1.0) and a["rmse"] == pytest.approx(1.0)
    assert b["mae"] == pytest.approx(0.0) and b["r2"] == pytest.approx(1.0)
    assert a["n_dong"] == 4 and b["n_dong"] == 4


def test_per_series_bo_dong_co_NaN_va_bao_so_dong_con_lai():
    """Seasonal naive thiếu `y_{t-288}` thì dòng đó bị bỏ, và `n_dong` phải nói ra."""
    ps = per_series_metrics(
        ["A"] * 4, [1.0, 2.0, 3.0, 4.0], [1.0, np.nan, 3.0, 5.0],
    )
    assert int(ps.loc[0, "n_dong"]) == 3
    assert ps.loc[0, "mae"] == pytest.approx(1 / 3)


def test_per_series_mase_dung_mau_so_cua_dung_chuoi_do(hai_chuoi):
    d = pd.Series({"A": 2.0, "B": 5.0})
    ps = per_series_metrics(
        hai_chuoi["series_id"], hai_chuoi["y"], hai_chuoi["yhat"], d=d
    ).set_index("series_id")
    assert ps.loc["A", "mase"] == pytest.approx(1.0 / 2.0)
    assert ps.loc["B", "mase"] == pytest.approx(0.0 / 5.0)


def test_per_series_chuoi_co_d_bang_0_thi_mase_NaN(hai_chuoi):
    ps = per_series_metrics(
        hai_chuoi["series_id"], hai_chuoi["y"], hai_chuoi["yhat"],
        d=pd.Series({"A": 0.0, "B": 5.0}),
    ).set_index("series_id")
    assert isnan(ps.loc["A", "mase"])
    assert np.isfinite(ps.loc["B", "mase"])


def test_per_series_chuoi_target_hang_thi_r2_NaN():
    ps = per_series_metrics(["A"] * 3, [7.0, 7.0, 7.0], [7.0, 8.0, 6.0])
    assert isnan(ps.loc[0, "r2"])


# ------------------------------------------------------------------- gộp

def test_gop_lay_trung_vi_khong_lay_trung_binh():
    """Chỗ P4 của `pha_gd3.py` phá. Ba giá trị lệch nặng: trung vị 1, trung bình 34."""
    ps = pd.DataFrame({
        "series_id": list("ABC"), "n_dong": [3, 3, 3],
        "mae": [0.0, 1.0, 101.0], "rmse": [0.0, 1.0, 101.0],
        "smape": [0.0, 1.0, 101.0], "mase": [0.0, 1.0, 101.0], "r2": [0.0, 1.0, -101.0],
    })
    g = gop(ps).set_index("metric")
    assert g.loc["mae", "p50"] == pytest.approx(1.0)
    assert g.loc["mae", "p50"] != pytest.approx(34.0)


def test_gop_iqr_bang_p75_tru_p25():
    ps = pd.DataFrame({
        "series_id": list("ABCD"), "n_dong": [1] * 4,
        "mae": [1.0, 2.0, 3.0, 4.0], "rmse": [1.0, 2.0, 3.0, 4.0],
        "smape": [1.0, 2.0, 3.0, 4.0], "mase": [1.0, 2.0, 3.0, 4.0],
        "r2": [1.0, 2.0, 3.0, 4.0],
    })
    g = gop(ps).set_index("metric")
    for m in METRIC_NAMES:
        assert g.loc[m, "iqr"] == pytest.approx(g.loc[m, "p75"] - g.loc[m, "p25"])
        assert g.loc[m, "p25"] <= g.loc[m, "p50"] <= g.loc[m, "p75"]


def test_gop_dem_dung_so_chuoi_bi_loai():
    """Chuỗi có MASE hoặc R² không xác định bị loại khỏi phần gộp **và được đếm**."""
    ps = pd.DataFrame({
        "series_id": list("ABCD"), "n_dong": [1] * 4,
        "mae": [1.0, 2.0, 3.0, 4.0], "rmse": [1.0, 2.0, 3.0, 4.0],
        "smape": [1.0, 2.0, 3.0, 4.0],
        "mase": [1.0, np.nan, 3.0, np.nan], "r2": [1.0, 2.0, np.nan, 4.0],
    })
    g = gop(ps).set_index("metric")
    assert (g.loc["mae", "n_chuoi"], g.loc["mae", "n_loai"]) == (4, 0)
    assert (g.loc["mase", "n_chuoi"], g.loc["mase", "n_loai"]) == (2, 2)
    assert (g.loc["r2", "n_chuoi"], g.loc["r2", "n_loai"]) == (3, 1)


def test_gop_khong_de_inf_troi_vao_trung_vi():
    """Nếu một bản nào đó lỡ trả `inf`, phần gộp vẫn phải loại nó — không bôi đen cột."""
    ps = pd.DataFrame({
        "series_id": list("ABC"), "n_dong": [1] * 3,
        "mae": [1.0, 2.0, 3.0], "rmse": [1.0, 2.0, 3.0], "smape": [1.0, 2.0, 3.0],
        "mase": [1.0, np.inf, 3.0], "r2": [1.0, 2.0, 3.0],
    })
    g = gop(ps).set_index("metric")
    assert np.isfinite(g.loc["mase", "p50"])
    assert g.loc["mase", "p50"] == pytest.approx(2.0)


def test_gop_moi_chuoi_mot_phieu_bang_nhau():
    """QĐ-013 điểm 5: chuỗi tải cao không được chi phối con số gộp.

    Chuỗi B có 1.000 dòng và sai số 100, chuỗi A và C mỗi cái 3 dòng sai số 1. Gộp
    theo chuỗi cho trung vị 1; gộp mọi dòng vào một dãy sẽ cho ~99,7.
    """
    sid = ["A"] * 3 + ["B"] * 1000 + ["C"] * 3
    y = np.concatenate([np.zeros(3), np.zeros(1000), np.zeros(3)])
    yhat = np.concatenate([np.ones(3), np.full(1000, 100.0), np.ones(3)])
    g = gop(per_series_metrics(sid, y, yhat)).set_index("metric")
    assert g.loc["mae", "p50"] == pytest.approx(1.0)


# --------------------------------- hai ca đã bắt được lỗi thật, ngày 2026-09-10

def test_C10b_chuoi_hang_o_gia_tri_khong_bieu_dien_duoc_van_phai_NaN():
    """Ca thật đã làm lệch 27 ô của bảng E1 — xem log GĐ3 ngày 2026-09-10.

    `E1_830` có target hằng đúng `1,1333333333333333` ở cả 346 dòng test. `SS_tot`
    bằng 0 về mặt toán học, nhưng `sum((y − ȳ)²)` cho `1,7e-29` vì `ȳ = sum/n` không
    rơi đúng vào giá trị đó. Bản kiểm `ss_tot == 0` để chuỗi lọt vào phần gộp với
    `R² = 1,0` và kéo lệch trung vị.

    Điều kiện đúng là `min == max` — đặc trưng chính xác của `SS_tot = 0`, không phụ
    thuộc thứ tự cộng dồn.
    """
    c = 1.1333333333333333
    y = np.full(346, c)
    assert float(((y - y.mean()) ** 2).sum()) > 0.0     # cái bẫy còn nguyên đó
    assert isnan(r2(y, y)), "chuỗi test hằng thì R² phải NaN dù tổng bình phương > 0"

    ps = per_series_metrics(["A"] * 346, y, y)
    assert isnan(ps.loc[0, "r2"])


def test_n_loai_dem_ca_chuoi_vang_mat_khoi_tap_dang_cham():
    """`n_chuoi + n_loai` = tổng số chuỗi của **môi trường**, không phải số chuỗi có mặt.

    `E3_m_2848` không có dòng hợp lệ nào trên test; nếu mẫu số là số chuỗi có mặt thì
    nó biến mất khỏi cả hai cột và bảng nói dối rằng E3 có 497 chuỗi.
    """
    ps = per_series_metrics(["A"] * 3 + ["B"] * 3, [1.0, 2.0, 3.0] * 2,
                            [1.0, 2.5, 3.0] * 2)
    g = gop(ps, n_chuoi_tong=4).set_index("metric")
    assert (g.loc["mae", "n_chuoi"], g.loc["mae", "n_loai"]) == (2, 2)
    g2 = gop(ps).set_index("metric")
    assert (g2.loc["mae", "n_chuoi"], g2.loc["mae", "n_loai"]) == (2, 0)
    with pytest.raises(ValueError):
        gop(ps, n_chuoi_tong=1)


def test_mau_so_mase_train_lay_dung_vung_train_cua_cua_so():
    """Chỗ P3 của `pha_gd3.py` phá: `d` phải lấy trên `[0, 1612)`, không phải test.

    Chuỗi dựng cho train phẳng hai giá trị (`d = 1`) và test nhảy 50 đơn vị mỗi bước
    (`d = 50`), nên hai cách cho hai con số không thể nhầm lẫn.
    """
    b0 = 1_000_000
    lo, hi = bucket_bounds()["train"]
    y = np.zeros(WINDOW_BUCKETS)
    y[lo:hi] = np.tile([0.0, 1.0], (hi - lo) // 2)          # train: |Δ| = 1
    y[hi:] = np.arange(WINDOW_BUCKETS - hi) * 50.0          # sau train: |Δ| = 50
    df = pd.DataFrame({
        "series_id": ["A"] * WINDOW_BUCKETS,
        "bucket": np.arange(b0, b0 + WINDOW_BUCKETS, dtype="int64"),
        "y": y,
    })
    d = mase_denominators_train(df, b0)
    assert d["A"] == pytest.approx(1.0), "d phải tính trên train"
    assert d["A"] != pytest.approx(50.0)
    # Không nhận horizon: cùng một `d` cho cả h = 1, 6, 12 (QĐ-013 điểm 3).
    assert "h" not in mase_denominators_train.__code__.co_varnames
