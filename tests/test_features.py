"""Kiểm `cwp.features` — bốn phép kiểm rò rỉ R1–R4 của `research-log/gate-gd2.md` mục 3.3.

Chạy:  pytest tests/test_features.py -v

Không dùng dữ liệu thật. Mọi chuỗi ở đây tự tạo, ngắn, tính tay được — test đỏ thì
biết ngay sai ở đâu, và không phụ thuộc việc `data/processed/` có mặt hay không.

Bốn cam kết của `docs/protocol.md` mục 8 (chốt thêm ở QĐ-008 và QĐ-010):

    R1  Không chạm tương lai. Đổi `y` từ `t+1` trở đi thì đặc trưng tại `t` không đổi.
    R2  Rolling loại điểm hiện tại: cửa sổ tại `t` là `[t-w, t-1]`, ddof = 1.
    R3  Không bắc cầu qua ranh giới chuỗi — mọi phép dịch đi qua `groupby(series_id)`.
    R4  Cửa sổ thiếu điểm hoặc dính NaN đều ra NaN. **Không** `min_periods=1`.

R1 là phép kiểm quyết định: nó bắt mọi dạng rò rỉ tương lai mà không cần biết bản
hiện thực làm thế nào — kể cả `center=True`, `interpolate` sau khi sinh đặc trưng,
hay `bfill`.

Test xanh chưa chứng minh được gì nếu nó không biết đỏ. Kết quả từng lần phá code có
chủ ý ghi ở `research-log/2026-09-09-gd2-dac-trung.md`.
"""

import numpy as np
import pandas as pd
import pytest

from cwp.features import (
    CALENDAR_COLS,
    FEATURE_COLS,
    MATRIX_COLS,
    ROLL_DDOF,
    build_feature_frame,
    day_of_week,
    hour_of_day,
    make_feature_matrix,
    prepare_input,
    valid_row_mask,
)

GRID = 300                      # giây mỗi bucket (protocol mục 5)
BUCKET_NGAY = 86400 // GRID     # 288 bucket = 24 giờ
MAX_LAG = 24                    # cửa sổ đặc trưng sâu nhất (protocol mục 8)

# bucket đầu của E1 trong sản phẩm GĐ1 — 2013-08-12T13:40:00Z, một thứ Hai thật.
# Dùng làm gốc thời gian cho chuỗi giả lập để đặc trưng lịch có nghĩa kiểm được.
B0 = 4587716


# ------------------------------------------------------------------ tiện ích

def bang(y, series_id="A", b0=B0):
    """Dựng bảng dài một chuỗi, đúng schema `data/processed/` (protocol mục 6b)."""
    y = np.asarray(y, dtype=float)
    return pd.DataFrame({
        "series_id": [series_id] * len(y),
        "bucket": np.arange(b0, b0 + len(y), dtype="int64"),
        "y": y,
    })


def noi(*bangs):
    """Nối nhiều chuỗi thành một bảng, đúng cách `data/processed/` xếp chúng."""
    return pd.concat(bangs, ignore_index=True)


def khung(df, h=1):
    """Ma trận 22 cột **chưa lọc** — còn nguyên các dòng NaN mà bộ lọc sẽ bỏ."""
    return build_feature_frame(prepare_input(df), h)


# ================================================== R1 — không chạm tương lai

@pytest.mark.parametrize("t", [24, 30, 45, 59])
def test_r1_thay_tuong_lai_bang_nan_dac_trung_tai_t_khong_doi(t):
    """R1. Xoá sạch tương lai thì đặc trưng tại `t` phải y nguyên.

    Đây là phép kiểm quyết định của cổng GĐ2: nó không giả định gì về cách hiện
    thực, nên bắt được mọi đường rò — `center=True`, nội suy sau khi sinh đặc trưng,
    `bfill`, hay một `shift(-1)` gõ nhầm dấu.
    """
    rng = np.random.default_rng(0)
    y = rng.uniform(1, 90, size=60)

    day_du = khung(bang(y))

    y_cut = y.copy()
    y_cut[t + 1:] = np.nan
    bi_cat = khung(bang(y_cut))

    pd.testing.assert_frame_equal(
        day_du.loc[:t, FEATURE_COLS],
        bi_cat.loc[:t, FEATURE_COLS],
        check_exact=False,
        obj=f"dac trung tai cac moc <= {t}",
    )


@pytest.mark.parametrize("t", [24, 40])
def test_r1_thay_tuong_lai_bang_gia_tri_khac_dac_trung_tai_t_khong_doi(t):
    """R1 (biến thể). Thay tương lai bằng **giá trị khác**, không phải NaN.

    Bản NaN có một điểm mù: một phép tính bỏ qua NaN (`skipna` mặc định của pandas)
    vẫn cho kết quả cũ dù nó có chạm tương lai. Thay bằng số thật thì không còn chỗ
    nấp — chạm là lộ.
    """
    rng = np.random.default_rng(1)
    y = rng.uniform(1, 90, size=60)

    goc = khung(bang(y))

    y_khac = y.copy()
    y_khac[t + 1:] = 99.0 - y_khac[t + 1:]
    doi = khung(bang(y_khac))

    pd.testing.assert_frame_equal(
        goc.loc[:t, FEATURE_COLS],
        doi.loc[:t, FEATURE_COLS],
        check_exact=False,
        obj=f"dac trung tai cac moc <= {t}",
    )


def test_r1_target_thi_duoc_phep_doi_vi_no_khong_phai_dac_trung():
    """Đối chứng cho R1: `target` **phải** đổi khi tương lai đổi.

    Nếu không có phép kiểm này thì R1 vẫn xanh trên một hiện thực trả về bảng hằng
    số — xanh vì không tính gì cả, chứ không phải vì làm đúng.
    """
    y = np.arange(1, 61, dtype=float)
    goc = khung(bang(y), h=1)

    y_khac = y.copy()
    y_khac[30:] += 100.0
    doi = khung(bang(y_khac), h=1)

    assert goc.loc[29, "target"] != doi.loc[29, "target"]


# ========================================== R2 — rolling loại điểm hiện tại

def test_r2_roll_mean_6_tai_t6_la_trung_binh_y0_toi_y5():
    """R2. `y = [1..8]`: `roll_mean_6` tại `t=6` ra **3,5**, không phải 4,5.

    3,5 là trung bình `y[0..5]` — cửa sổ `[t-6, t-1]`. 4,5 là trung bình `y[1..6]`,
    tức cửa sổ `[t-5, t]` đã nuốt điểm hiện tại: dấu hiệu thiếu `.shift(1)`.
    """
    F = khung(bang([1, 2, 3, 4, 5, 6, 7, 8]))

    assert F.loc[6, "roll_mean_6"] == pytest.approx(3.5)
    assert F.loc[6, "roll_mean_6"] != pytest.approx(4.5)


def test_r2_roll_min_max_6_khong_chua_diem_hien_tai():
    """R2. Trên chuỗi tăng đều, biên trên của cửa sổ quá khứ đúng bằng `lag_1`."""
    F = khung(bang([1, 2, 3, 4, 5, 6, 7, 8]))

    assert F.loc[6, "roll_min_6"] == pytest.approx(1.0)
    assert F.loc[6, "roll_max_6"] == pytest.approx(6.0)   # y_6 = 7 nam NGOAI cua so
    assert F.loc[6, "roll_max_6"] == pytest.approx(F.loc[6, "lag_1"])


def test_r2_roll_std_6_dung_ddof_1_theo_qd010():
    """R2. `roll_std_*` dùng `ddof = 1` — pandas mặc định 1, numpy mặc định 0."""
    F = khung(bang([1, 2, 3, 4, 5, 6, 7, 8]))
    qua_khu = np.array([1, 2, 3, 4, 5, 6], dtype=float)

    assert ROLL_DDOF == 1
    assert F.loc[6, "roll_std_6"] == pytest.approx(qua_khu.std(ddof=1))
    assert F.loc[6, "roll_std_6"] != pytest.approx(qua_khu.std(ddof=0))


def test_r2_cua_so_12_dung_cung_quy_uoc():
    """R2. Cửa sổ 12 không phải trường hợp riêng — cùng quy ước `[t-12, t-1]`."""
    F = khung(bang(np.arange(1, 21, dtype=float)))
    qua_khu = np.arange(1, 13, dtype=float)

    assert F.loc[12, "roll_mean_12"] == pytest.approx(qua_khu.mean())    # 6,5
    assert F.loc[12, "roll_std_12"] == pytest.approx(qua_khu.std(ddof=1))
    assert F.loc[12, "roll_min_12"] == pytest.approx(1.0)
    assert F.loc[12, "roll_max_12"] == pytest.approx(12.0)


def test_r2_diff_1_dung_y_t_va_do_la_dung_dac_ta():
    """`diff_1 = y_t - y_{t-1}`. `y_t` là đầu vào hợp lệ tại `t`, không phải rò rỉ."""
    F = khung(bang([1, 2, 4, 8, 16, 32, 64, 128]))

    assert F.loc[3, "diff_1"] == pytest.approx(8 - 4)
    assert np.isnan(F.loc[0, "diff_1"])


def test_r2_lag_lay_dung_diem_qua_khu():
    """Sáu lag của mục 8 lấy đúng `y_{t-k}`, không lệch một bước."""
    y = np.arange(100, 140, dtype=float)
    F = khung(bang(y))

    for k in (1, 2, 3, 6, 12, 24):
        assert F.loc[30, f"lag_{k}"] == pytest.approx(y[30 - k])


# ======================================= R3 — không bắc cầu qua ranh giới chuỗi

def hai_chuoi_tuong_phan(n=40, thap=1.0, cao=90.0):
    """Chuỗi A toàn giá trị nhỏ, chuỗi B toàn giá trị lớn, cùng khoảng bucket.

    Cùng khoảng bucket là đúng thực tế: cửa sổ 8 ngày của protocol mục 7 là **toàn
    cục theo môi trường**, nên mọi chuỗi phủ cùng một khoảng lịch.
    """
    return noi(bang([thap] * n, series_id="A"), bang([cao] * n, series_id="B"))


def test_r3_lag_24_dau_chuoi_sau_la_nan():
    """R3. 24 dòng đầu của **mỗi** chuỗi phải có `lag_24` là NaN.

    Thiếu `groupby(series_id)` thì dòng đầu chuỗi B mượn được đuôi chuỗi A và
    `lag_24` ở đó ra 1,0 thay vì NaN.
    """
    F = khung(hai_chuoi_tuong_phan())

    for sid in ("A", "B"):
        cua_chuoi = F[F["series_id"] == sid]
        lag24 = cua_chuoi["lag_24"].to_numpy()
        assert np.isnan(lag24[:MAX_LAG]).all(), f"chuoi {sid}: lag_24 ro qua ranh gioi"
        assert np.isfinite(lag24[MAX_LAG]), f"chuoi {sid}: dong thu 25 phai tinh duoc"


def test_r3_rolling_chuoi_sau_khong_mang_dau_vet_chuoi_truoc():
    """R3. Không giá trị rolling nào của chuỗi B được dính con số của chuỗi A."""
    F = khung(hai_chuoi_tuong_phan(thap=1.0, cao=90.0))
    B = F[F["series_id"] == "B"]

    for w in (6, 12):
        for stat in ("mean", "std", "min", "max"):
            v = B[f"roll_{stat}_{w}"].dropna().to_numpy()
            mong_doi = 0.0 if stat == "std" else 90.0
            assert np.allclose(v, mong_doi), (
                f"roll_{stat}_{w} cua chuoi B ra {np.unique(v)[:3]} — "
                "nghi lich su dang chay tu chuoi A sang"
            )


def test_r3_dac_trung_khong_doi_khi_them_chuoi_khac_vao_bang():
    """R3 (mạnh hơn). Thêm một chuỗi lạ vào bảng không được làm đổi chuỗi cũ.

    Đây là dạng tổng quát của R3: đặc trưng của một chuỗi chỉ phụ thuộc chính nó
    (protocol mục 8 câu đầu), nên bảng có thêm ai vào cũng không ảnh hưởng.
    """
    rng = np.random.default_rng(2)
    A = bang(rng.uniform(1, 90, size=50), series_id="A")
    B = bang(rng.uniform(1, 90, size=50), series_id="B")

    mot_minh = khung(A)
    cung_nhau = khung(noi(A, B))
    cua_A = cung_nhau[cung_nhau["series_id"] == "A"].reset_index(drop=True)

    pd.testing.assert_frame_equal(mot_minh[MATRIX_COLS], cua_A[MATRIX_COLS])


def test_r3_target_khong_bac_cau_sang_chuoi_sau():
    """R3. `target` cuối chuỗi A phải là NaN, không được lấy đầu chuỗi B."""
    F = khung(hai_chuoi_tuong_phan(n=40), h=6)
    A = F[F["series_id"] == "A"]

    assert A["target"].tail(6).isna().all()


# ============================== R4 — cửa sổ thiếu điểm ra NaN, không min_periods=1

def test_r4_sau_dong_dau_moi_chuoi_roll_mean_6_la_nan():
    """R4. Sáu dòng đầu mỗi chuỗi NaN, dòng thứ bảy mới có giá trị.

    `min_periods=1` sẽ cho dòng đầu tiên một con số tính trên 0 điểm quá khứ — hoặc
    tệ hơn, trên 1 điểm — và không báo lỗi gì.
    """
    F = khung(hai_chuoi_tuong_phan(n=40))

    for sid in ("A", "B"):
        v = F.loc[F["series_id"] == sid, "roll_mean_6"].to_numpy()
        assert np.isnan(v[:6]).all(), f"chuoi {sid}: cua so chua du 6 diem ma da ra so"
        assert np.isfinite(v[6]), f"chuoi {sid}: dong thu 7 phai tinh duoc"


def test_r4_muoi_hai_dong_dau_roll_mean_12_la_nan():
    """R4. Cùng luật cho cửa sổ 12."""
    F = khung(bang(np.arange(1, 31, dtype=float)))
    v = F["roll_mean_12"].to_numpy()

    assert np.isnan(v[:12]).all()
    assert np.isfinite(v[12])


def test_r4_chuoi_ngan_hon_cua_so_thi_moi_rolling_deu_nan():
    """R4. Chuỗi 3 điểm không đủ cho bất kỳ cửa sổ nào — tất cả phải NaN."""
    F = khung(bang([10.0, 20.0, 30.0]))

    for w in (6, 12):
        for stat in ("mean", "std", "min", "max"):
            assert F[f"roll_{stat}_{w}"].isna().all()


def test_r4_nan_trong_cua_so_lam_hong_ca_cua_so():
    """R4. Một NaN trong cửa sổ thì cả cửa sổ ra NaN, không được bỏ qua nó.

    pandas `rolling` mặc định đếm điểm **không NaN**; nếu ai đó hạ `min_periods`
    xuống thì cửa sổ dính NaN sẽ lặng lẽ trả về trung bình của phần còn lại.
    """
    y = np.arange(1, 21, dtype=float)
    y[3] = np.nan
    F = khung(bang(y))

    # Cua so tai t=7 la [t-6, t-1] = vi tri 1..6, co chua vi tri 3.
    assert np.isnan(F.loc[7, "roll_mean_6"])
    # Cua so tai t=10 la vi tri 4..9, da qua khoi diem NaN.
    assert np.isfinite(F.loc[10, "roll_mean_6"])


# ================================= Đặc trưng lịch — tuần hoàn và gốc thời gian

def test_lich_cach_nhau_dung_24_gio_thi_hour_sin_bang_nhau():
    """Mã hoá sin/cos phải tuần hoàn đúng: cách nhau 288 bucket là cùng một giờ."""
    n = 3 * BUCKET_NGAY
    F = khung(bang(np.ones(n)))

    for t in (0, 17, 100):
        assert F.loc[t, "hour_sin"] == pytest.approx(F.loc[t + BUCKET_NGAY, "hour_sin"])
        assert F.loc[t, "hour_cos"] == pytest.approx(F.loc[t + BUCKET_NGAY, "hour_cos"])


def test_lich_cach_nhau_dung_7_ngay_thi_dow_sin_bang_nhau():
    """`dow` tuần hoàn theo tuần: cách nhau 2016 bucket là cùng thứ."""
    b = np.array([B0, B0 + 7 * BUCKET_NGAY, B0 + 14 * BUCKET_NGAY], dtype="int64")

    assert len(set(day_of_week(b))) == 1


def test_lich_cach_nhau_12_gio_thi_hour_cos_khac_nhau():
    """Đối chứng: không phải mốc nào cũng bằng nhau, nếu không thì test trên vô nghĩa."""
    F = khung(bang(np.ones(2 * BUCKET_NGAY)))
    nua_ngay = BUCKET_NGAY // 2

    assert F.loc[0, "hour_cos"] != pytest.approx(F.loc[nua_ngay, "hour_cos"])


def test_lich_suy_tu_bucket_tuyet_doi_khong_danh_so_lai_tu_0():
    """Bẫy `gate-gd2.md` mục 3.4: bucket phải là số hiệu tuyệt đối `floor(t/300)`.

    Đánh số lại từ 0 theo từng chuỗi làm `hour_sin` vô nghĩa mà không báo lỗi gì.
    Kiểm bằng cách đối chiếu với giờ thật của mốc E1: 2013-08-12T13:40:00Z.
    """
    F = khung(bang(np.ones(10), b0=B0))

    assert hour_of_day(np.array([B0]))[0] == 13
    assert F.loc[0, "hour_sin"] == pytest.approx(np.sin(2 * np.pi * 13 / 24))
    # Neu bucket bi danh so lai tu 0 thi gio se la 0 va hour_sin bang 0.
    assert F.loc[0, "hour_sin"] != pytest.approx(0.0)


def test_lich_goc_dow_dung_cong_thuc_chot_o_qd010():
    """Gốc `dow` là `((t // 86400) + 4) % 7` — công thức chốt, `check_gd2.py` so đúng nó.

    Ghi lại đây điều công thức thực sự cho ra, vì QĐ-010 chú thích "0 là thứ Hai"
    trong khi số đo nói khác: 1970-01-01 (thứ Năm) ra 4, và mốc đầu của E1
    2013-08-12 (thứ Hai thật) ra 1. Tức **0 là Chủ Nhật**. Chỉ là nhãn diễn giải,
    không đổi con số nào — nhưng đọc nhãn sai thì phần bàn về chu kỳ tuần trong paper
    lệch đi một ngày. Đã báo A.
    """
    assert day_of_week(np.array([0]))[0] == 4                   # 1970-01-01, thu Nam
    assert day_of_week(np.array([B0]))[0] == 1                  # 2013-08-12, thu Hai
    assert day_of_week(np.array([B0 - BUCKET_NGAY]))[0] == 0    # Chu Nhat


def test_lich_khong_re_nhanh_theo_moi_truong():
    """QĐ-010: E3 dùng **cùng công thức**, chỉ khác ý nghĩa. Không bịa ngày cho Alibaba.

    Kiểm bằng hai chuỗi cùng chỉ số bucket nhưng khác `series_id`: đặc trưng lịch
    phải trùng khít. Nếu ai đó thêm nhánh theo môi trường thì chuỗi mang gốc
    `b0 = 0` kiểu E3 sẽ được xử lý khác và phép so này đỏ.
    """
    e3 = khung(bang(np.ones(10), series_id="E3_m_1", b0=0))
    gia_lap = khung(bang(np.ones(10), series_id="E1_1", b0=0))

    pd.testing.assert_frame_equal(gia_lap[CALENDAR_COLS], e3[CALENDAR_COLS])
    assert hour_of_day(np.array([0]))[0] == 0


# ============================== Luật dòng hợp lệ — khác `dropna`, và đó là chủ ý

def test_luat_cua_so_chat_hon_dropna_dung_11_diem():
    """QĐ-010: `dropna()` trên ma trận đặc trưng **lỏng hơn** luật `[t-24, t]`.

    19 đặc trưng chỉ chạm 15 điểm trong cửa sổ (`t-24`, `t-12..t-1`, `t`); các điểm
    `t-23` đến `t-13` — đúng **11** điểm — không đặc trưng nào dùng. Nên một NaN đơn
    lẻ làm hỏng 25 dòng theo luật, nhưng chỉ 14 dòng theo `dropna`.

    Chênh lệch 11 dòng ở đây không phải con số phải nhắm tới, nó là hệ quả số học
    của chính đặc tả — và là lý do E2 h=1 thừa 1.513 dòng nếu lọc bằng `dropna`.
    """
    y = np.arange(60, dtype=float) + 1.0
    y[20] = np.nan
    df = prepare_input(bang(y))

    theo_luat = int(valid_row_mask(df, h=1).sum())
    theo_dropna = int(build_feature_frame(df, h=1).dropna().shape[0])

    assert theo_dropna - theo_luat == 11


def test_luat_cua_so_doi_hoi_ca_25_diem_khong_nan():
    """Dòng tại `t` chỉ hợp lệ khi cả `[t-24, t]` sạch NaN (protocol mục 8, QĐ-008)."""
    y = np.ones(60)
    y[30] = np.nan
    df = prepare_input(bang(y))
    m = valid_row_mask(df, h=1).to_numpy()

    assert not m[30], "dong co y_t la NaN ma van hop le"
    assert not m[54], "t=54 con thay NaN o t-24, phai bi loai"
    assert m[55], "t=55 da ra khoi cua so chua NaN, phai hop le"
    assert not m[:MAX_LAG].any(), "24 dong dau chuoi chua du lich su"


def test_luat_cua_so_doi_hoi_target_khong_nan():
    """Điều kiện thứ hai: `y` tại `t+h` không NaN. Horizon lớn thì mất nhiều dòng hơn."""
    df = prepare_input(bang(np.ones(60)))
    n = {h: int(valid_row_mask(df, h=h).sum()) for h in (1, 6, 12)}

    assert n[1] == 60 - MAX_LAG - 1
    assert n[6] == n[1] - 5
    assert n[12] == n[1] - 11


def test_make_feature_matrix_loc_theo_luat_cua_so_chu_khong_phai_dropna():
    """`make_feature_matrix` phải **dùng** luật cửa sổ, không chỉ có sẵn nó ở đâu đó.

    Hai test trên gọi thẳng `valid_row_mask` nên vẫn xanh dù bộ lọc thật bị đổi
    thành `dropna()`. Lỗ hổng đó chỉ có neo số dòng của `check_gd2.py` bịt được, mà
    neo thì cần `data/processed/`. Phép kiểm này bịt tại chỗ, trên dữ liệu giả lập.
    """
    y = np.arange(60, dtype=float) + 1.0
    y[20] = np.nan
    df = bang(y)

    theo_luat = int(valid_row_mask(prepare_input(df), h=1).sum())
    X = make_feature_matrix(df, h=1)

    assert len(X) == theo_luat
    assert len(X) == int(build_feature_frame(prepare_input(df), h=1).dropna().shape[0]) - 11


def test_ma_tran_da_loc_khong_con_nan_va_dung_22_cot():
    """Chiều thuận của R4: dòng nào đã qua luật thì tính được đủ 19 đặc trưng."""
    rng = np.random.default_rng(3)
    y = rng.uniform(1, 90, size=200)
    y[[40, 41, 120]] = np.nan
    X = make_feature_matrix(
        noi(bang(y, series_id="A"), bang(y[::-1], series_id="B")), h=6
    )

    assert list(X.columns) == MATRIX_COLS
    assert X.shape[1] == 22
    assert len(FEATURE_COLS) == 19
    assert not X[FEATURE_COLS + ["target"]].isna().any().any()


def test_ma_tran_khong_giu_cot_thua_cua_bang_goc():
    """`env` và `is_interp` không được lọt vào ma trận — mục 3.2 đếm đúng 22 cột."""
    df = bang(np.ones(60))
    df["env"] = "E1"
    df["is_interp"] = False
    X = make_feature_matrix(df, h=1)

    assert "env" not in X.columns
    assert "is_interp" not in X.columns


# ============================================== Lưới thời gian phải nguyên vẹn

def test_luoi_thung_thi_bao_loi_chu_khong_di_tiep():
    """Bảng đã bị lọc NaN từ trước làm `lag_1` thành khoảng cách 2 giờ thật.

    Lag và rolling ở đây tính theo vị trí dòng; điều đó chỉ trùng với khoảng cách
    thời gian khi lưới liên tục. Cùng loại bẫy mà `gate-gd2.md` mục 3.4 cảnh báo cho
    ACF, nên chặn ngay ở cửa vào.
    """
    thung = pd.DataFrame({
        "series_id": ["A"] * 3,
        "bucket": [B0, B0 + 1, B0 + 3],
        "y": [1.0, 2.0, 3.0],
    })

    with pytest.raises(ValueError, match="thủng"):
        prepare_input(thung)


def test_thieu_cot_bat_buoc_thi_bao_loi():
    """Thiếu `y` hoặc `series_id` là sai schema mục 6b, phải nói ra chứ đừng đoán."""
    with pytest.raises(ValueError, match="thiếu cột"):
        prepare_input(pd.DataFrame({"series_id": ["A"], "bucket": [B0]}))


def test_bang_dau_vao_khong_bi_sua_tai_cho():
    """Sinh đặc trưng không được đụng vào bảng của người gọi."""
    df = bang(np.arange(60, dtype=float))
    truoc = df.copy()
    make_feature_matrix(df, h=1)

    pd.testing.assert_frame_equal(df, truoc)


def test_thu_tu_dong_dau_vao_khong_doi_ket_qua():
    """Kết quả phải phụ thuộc dữ liệu, không phụ thuộc cách tệp xếp dòng."""
    rng = np.random.default_rng(4)
    df = noi(bang(rng.uniform(1, 90, 60), series_id="A"),
             bang(rng.uniform(1, 90, 60), series_id="B"))
    xao = df.sample(frac=1.0, random_state=7).reset_index(drop=True)

    pd.testing.assert_frame_equal(make_feature_matrix(df, h=1),
                                  make_feature_matrix(xao, h=1))


def test_horizon_khong_hop_le_thi_bao_loi():
    """Horizon phải >= 1. `h = 0` là dự đoán chính điểm hiện tại — vô nghĩa."""
    df = bang(np.ones(60))

    for h in (0, -1):
        with pytest.raises(ValueError, match="Horizon"):
            make_feature_matrix(df, h=h)
