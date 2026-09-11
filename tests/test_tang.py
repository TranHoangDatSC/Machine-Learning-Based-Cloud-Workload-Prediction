"""Kiểm `cwp.evaluation.tang` và luật lấy mẫu con của `cwp.models.registry`.

Chạy:  pytest tests/test_tang.py -v

Hai thứ được kiểm ở đây đều là chỗ QĐ-012 và QĐ-014 chốt bằng lời, nên dễ hiện thực
lệch mà không ai thấy:

    T1  Ngưỡng tầng là tam phân vị TRONG TỪNG môi trường, không phải ngưỡng chung.
    T2  Cách chia đọc từ config/split.yaml, và ngưỡng KHÔNG nằm trong config.
    T3  Mẫu con của SVR lấy trên DÒNG, phân tầng, giữ nguyên tỉ lệ ba tầng.
    T4  Mẫu con tất định theo seed 42, và giữ thứ tự thời gian (không shuffle).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from cwp.evaluation.tang import (
    TEN_TANG,
    bang_tang,
    doc_cau_hinh_tang,
    gan_tang,
    nguong,
)
from cwp.models.registry import REGISTRY, SEED, mau_con_phan_tang

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cv_gia():
    """Hai môi trường có thang CV khác hẳn nhau — đúng tình huống QĐ-012 điểm 1 nói tới.

    A là môi trường lớn, CV trải từ 1 đến 30. B nhỏ và nén trong [0,10; 0,15] — giống
    E3 thật, nơi tam phân vị chỉ rộng 0,06 và nằm gọn dưới tầng thấp nhất của E1. Một
    ngưỡng tuyệt đối chung sẽ dồn trọn B vào một tầng.
    """
    return pd.DataFrame({
        "series_id": [f"A{i}" for i in range(30)] + [f"B{i}" for i in range(6)],
        "env": ["A"] * 30 + ["B"] * 6,
        "cv": list(1.0 + np.arange(30)) + list(0.10 + np.arange(6) * 0.01),
        "ti_le_cham_chan": [0.1] * 30 + [0.9] * 6,
    })


# ---------------------------------------------------------------- T1, T2

def test_T1_nguong_la_tam_phan_vi_trong_tung_moi_truong(cv_gia):
    tang_a, ng_a = gan_tang(cv_gia, "A")
    tang_b, ng_b = gan_tang(cv_gia, "B")
    assert ng_a != ng_b, "hai môi trường phải có ngưỡng riêng"
    assert tang_a.value_counts().reindex(TEN_TANG).tolist() == [10, 10, 10]
    assert tang_b.value_counts().reindex(TEN_TANG).tolist() == [2, 2, 2]


def test_T1_nguong_chung_se_don_het_mot_moi_truong_vao_mot_tang(cv_gia):
    """Phép kiểm đối chứng: cho thấy cách làm sai thật sự cho kết quả khác."""
    chung = nguong(cv_gia["cv"].to_numpy())      # ngưỡng trên CẢ hai môi trường
    b = cv_gia[cv_gia["env"] == "B"]["cv"].to_numpy()
    assert len(set(np.digitize(b, chung))) == 1, "ca kiểm mất ý nghĩa nếu B không bị dồn"


def test_T1_tam_phan_vi_dung_cong_thuc():
    v = np.arange(300, dtype=float)
    assert nguong(v, 3) == pytest.approx(list(np.percentile(v, [100 / 3, 200 / 3])))


def test_T1_gan_tang_theo_thu_tu_tang_dan_cua_cv(cv_gia):
    tang, _ = gan_tang(cv_gia, "A")
    cv = cv_gia[cv_gia["env"] == "A"].set_index("series_id")["cv"]
    tb = pd.DataFrame({"cv": cv, "tang": tang}).groupby("tang", observed=True)["cv"].max()
    assert tb["thap"] < tb["vua"] < tb["cao"]


def test_T2_doc_cach_chia_tu_config_va_ngung_neu_khac(tmp_path):
    st = doc_cau_hinh_tang(ROOT / "config" / "split.yaml")
    assert st["method"] == "percentile_within_env"
    assert st["n_strata"] == 3
    assert st["report_column"] == "ti_le_cham_chan"

    xau = tmp_path / "split.yaml"
    xau.write_text("stratify:\n  method: absolute\n  n_strata: 3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="percentile_within_env"):
        doc_cau_hinh_tang(xau)


def test_T2_config_khong_chua_nguong_bang_so():
    """Ngưỡng phải tính lại từ dữ liệu; nằm trong config là hardcode (Bước 6)."""
    cfg = yaml.safe_load((ROOT / "config" / "split.yaml").read_text(encoding="utf-8"))
    st = cfg["stratify"]
    assert not any(isinstance(v, float) for v in st.values()), \
        "config/split.yaml: stratify không được chứa ngưỡng bằng số"


def test_bang_tang_giu_cot_ti_le_cham_chan(cv_gia):
    """QĐ-012 điểm 3: mọi bảng phân tầng phải báo kèm cột này."""
    b = bang_tang(cv_gia, envs=("A", "B"))
    assert set(b.columns) == {"series_id", "env", "tang", "cv", "ti_le_cham_chan"}
    assert len(b) == 36


# -------------------------------------------------------------------- T3, T4

def test_T3_mau_con_giu_nguyen_ti_le_ba_tang():
    tang = np.array(["thap"] * 6000 + ["vua"] * 3000 + ["cao"] * 1000)
    ix = mau_con_phan_tang(tang, 1000)
    assert len(ix) == 1000
    dem = pd.Series(tang[ix]).value_counts()
    assert dem["thap"] == 600 and dem["vua"] == 300 and dem["cao"] == 100


def test_T3_mau_con_lay_tren_dong_khong_bo_chuoi_nao():
    """QĐ-014 điểm 2: bỏ bớt chuỗi là đổi quần thể; bỏ bớt dòng thì không.

    Mỗi chuỗi có nhiều dòng nên mẫu 1.000 dòng vẫn chạm gần hết 100 chuỗi. Điều bắt
    buộc là hàm **không** nhận `series_id` và không có đường nào loại cả một chuỗi
    theo chủ ý.
    """
    assert "series_id" not in mau_con_phan_tang.__code__.co_varnames
    sid = np.repeat([f"S{i}" for i in range(100)], 100)
    tang = np.where(np.isin(sid, [f"S{i}" for i in range(33)]), "thap", "vua")
    ix = mau_con_phan_tang(tang, 1000)
    assert len(set(sid[ix])) > 90


def test_T4_mau_con_tat_dinh_theo_seed():
    tang = np.array(["thap"] * 500 + ["vua"] * 500)
    a = mau_con_phan_tang(tang, 200, seed=SEED)
    b = mau_con_phan_tang(tang, 200, seed=SEED)
    c = mau_con_phan_tang(tang, 200, seed=SEED + 1)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_T4_mau_con_giu_thu_tu_thoi_gian():
    tang = np.array(["thap"] * 500 + ["vua"] * 500)
    ix = mau_con_phan_tang(tang, 200)
    assert (np.diff(ix) > 0).all(), "chỉ số phải tăng dần — không shuffle (mục 9)"


def test_T4_mau_lon_hon_quan_the_thi_lay_het():
    tang = np.array(["thap"] * 10 + ["cao"] * 5)
    assert np.array_equal(mau_con_phan_tang(tang, 999), np.arange(15))


def test_chi_svr_lay_mau_con():
    """QĐ-014 điểm 2 chỉ cho phép SVR lấy mẫu con; sáu model kia chạy 100%."""
    assert REGISTRY["svr"].mau_con == 10_000
    for ten in ("lr", "ridge", "rf", "xgb"):
        assert REGISTRY[ten].mau_con is None


# ------------------------- T5: mẫu con SVR dùng chung cho cả ba horizon

def _nap_run_experiments():
    import importlib.util

    p = ROOT / "scripts" / "run_experiments.py"
    spec = importlib.util.spec_from_file_location("rx_gd3", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_T5_khoa_dong_la_song_anh():
    rx = _nap_run_experiments()
    ds = ["S0", "S1", "S2"]
    sid = np.array(["S2", "S0", "S2", "S1"])
    off = np.array([0, 2303, 1, 7])
    k = rx.khoa_dong(sid, off, ds)
    assert len(set(k.tolist())) == 4
    assert (k // 4096 == np.array([2, 0, 2, 1])).all()
    assert (k % 4096 == off).all()
    with pytest.raises(ValueError):
        rx.khoa_dong(np.array(["LA"]), np.array([0]), ds)


@pytest.mark.skipif(
    not (ROOT / "data" / "features" / "E2_h12.parquet").exists(),
    reason="cần sản phẩm GĐ2 trong data/features/",
)
def test_T5_mau_con_svr_dung_chung_cho_ba_horizon():
    """QĐ-014 điểm 2: *"cùng một mẫu con dùng cho cả ba horizon"*.

    Bản đầu rút mẫu riêng ở từng horizon và chỉ trùng **2,9%** giữa `h = 1` và `h = 6`
    — vùng train + val của `h = 12` ngắn hơn 11 bucket nên vị trí trong mảng lệch đi
    và cùng một seed vẫn cho hai tập khác hẳn. Đã sửa: rút một lần theo khoá
    `(series_id, offset)`, mỗi horizon lấy giao với dòng hợp lệ của chính nó.
    """
    rx = _nap_run_experiments()
    from cwp.evaluation.splits import doc_b0, fit_mask, offset
    from cwp.evaluation.tang import bang_tang

    env = "E2"
    cv = pd.read_csv(ROOT / "results" / "tables" / "cv_gd2.csv")
    tang = bang_tang(cv, envs=(env,)).set_index("series_id")["tang"]
    ds = sorted(pd.read_parquet(ROOT / "data" / "processed" / f"{env}.parquet",
                                columns=["series_id"])["series_id"].unique())
    b0 = doc_b0(env, ROOT / "data" / "processed")
    khoa = rx.khoa_mau_con_svr(env, ROOT / "data" / "features", b0, tang, ds, 2000)

    assert len(khoa) == 2000
    dung = {}
    for h in (1, 6, 12):
        X = pd.read_parquet(ROOT / "data" / "features" / f"{env}_h{h}.parquet",
                            columns=["series_id", "bucket"])
        off = offset(X["bucket"], b0)
        # Đúng đường đi của `run_experiments.py`: khoá mẫu GIAO với vùng train + val
        # của chính horizon đó. Vài dòng sát ranh giới bị luật purge lấy đi — ở E2
        # `h = 12` là 8 dòng — nên phép giao này không thừa.
        m = np.isin(rx.khoa_dong(X["series_id"].to_numpy(), off, ds), khoa)
        m &= fit_mask(off, h)
        dung[h] = set(rx.khoa_dong(X["series_id"].to_numpy()[m], off[m], ds).tolist())
        # Không dòng huấn luyện nào của SVR có target rơi vào test (L1 của gate mục 3.4).
        assert (off[m] + h < 1957).all()

    # h = 6 và h = 12 là TẬP CON của h = 1, không phải một mẫu khác.
    assert dung[6] <= dung[1] and dung[12] <= dung[1]
    assert len(dung[6]) / len(dung[1]) > 0.95
    assert len(dung[12]) / len(dung[1]) > 0.95
