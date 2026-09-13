"""Test cho QĐ-019 — target N2 đúng `y_{t+h} − y_t`.

Chạy:  pytest tests/test_qd019.py -v

Ca quan trọng nhất là `test_target_khong_phai_sai_phan_mot_buoc`: nó giữ đúng cái lỗi đã
lọt qua toàn bộ cổng GĐ4, vì bất biến `Δ̂ = 0` đúng với cả hai định nghĩa.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_qd019 as bq  # noqa: E402
import phan_tich_qd019 as p9  # noqa: E402
import run_qd019 as r9  # noqa: E402
from build_features import bien_doi_bang  # noqa: E402
from cwp.features import make_feature_matrix  # noqa: E402


def _bang(n_chuoi=3, n=120, seed=0):
    rng = np.random.default_rng(seed)
    dong = []
    for i in range(n_chuoi):
        y = np.cumsum(rng.normal(0, 1, n)) + 50
        dong.append(pd.DataFrame({"series_id": f"s{i}", "bucket": np.arange(n) + 1000, "y": y}))
    return pd.concat(dong, ignore_index=True)


def _tra(df, X, k):
    y = df.set_index(["series_id", "bucket"])["y"]
    return y.reindex(pd.MultiIndex.from_arrays([X.series_id, X.bucket + k])).to_numpy()


def test_target_la_y_t_cong_h_tru_y_t():
    df = _bang()
    for h in (1, 6, 12):
        X = bq.ma_tran_n2(df, h)
        assert np.allclose(X["target"].to_numpy(), _tra(df, X, h) - _tra(df, X, 0), atol=0)


def test_target_khong_phai_sai_phan_mot_buoc():
    """Bản GĐ4 cho target = y(t+h) − y(t+h−1). Ở h = 6 hai thứ phải khác nhau."""
    df = _bang()
    X = bq.ma_tran_n2(df, 6)
    mot_buoc = _tra(df, X, 6) - _tra(df, X, 5)
    assert not np.allclose(X["target"].to_numpy(), mot_buoc)


def test_h1_trung_ban_gd4():
    df = _bang()
    moi = bq.ma_tran_n2(df, 1).sort_values(["series_id", "bucket"]).reset_index(drop=True)
    cu = make_feature_matrix(bien_doi_bang(df, "N2"), h=1)
    cu = cu.sort_values(["series_id", "bucket"]).reset_index(drop=True)
    assert moi.equals(cu)


def test_dong_moi_la_tap_cha_va_dac_trung_trung():
    df = _bang()
    df.loc[(df.series_id == "s1") & (df.bucket == 1070), "y"] = np.nan   # y(t+h−1) NaN
    h = 6
    moi = bq.ma_tran_n2(df, h)
    cu = make_feature_matrix(bien_doi_bang(df, "N2"), h=h)
    j = cu.merge(moi, on=["series_id", "bucket"], how="left", suffixes=("_cu", ""), indicator=True)
    assert (j["_merge"] == "both").all()
    assert len(moi) > len(cu)
    assert np.array_equal(j["lag_1_cu"].to_numpy(), j["lag_1"].to_numpy())


def test_dong_them_dung_la_dong_y_t_cong_h_tru_1_nan():
    df = _bang(n_chuoi=1)
    df.loc[df.bucket == 1070, "y"] = np.nan
    h = 6
    moi = set(bq.ma_tran_n2(df, h)["bucket"])
    cu = set(make_feature_matrix(bien_doi_bang(df, "N2"), h=h)["bucket"])
    # t + h − 1 = 1070 → t = 1065; t + h = 1071 hữu hạn, cửa sổ [t−25, t] sạch.
    assert moi - cu == {1065}


def test_map_nguoc_ra_dung_y_t_cong_h_voi_target_that():
    """Model hoàn hảo (Δ̂ = target) phải cho lại đúng y(t+h) sau map ngược."""
    df = _bang()
    X = bq.ma_tran_n2(df, 12)
    yhat = _tra(df, X, 0) + X["target"].to_numpy()
    assert np.allclose(yhat, _tra(df, X, 12))


def test_ke_hoach_qd019_dung_so_khop_va_cham():
    v = r9.ke_hoach_qd019(["lr", "ridge", "rf", "xgb", "svr"], set())
    assert sum(len(x["model"]) for x in v) == 55
    assert sum(len(d) for x in v for d in x["model"].values()) == 140
    assert {x["h"] for x in v if x["nguon"] != "E1g"} == {6, 12}


def _ps(mode, h, mae, nguon="E3", dich="E1"):
    return pd.DataFrame({"nguon": nguon, "dich": dich, "mode": mode, "lich": "co", "h": h,
                         "model": "lr", "series_id": ["a", "b"], "n_dong": 10, "mae": mae})


def test_thay_chi_dung_mode_va_h_duoc_chon():
    goc = pd.concat([_ps("N2", 1, [1.0, 1.0]), _ps("N2", 6, [9.0, 9.0]),
                     _ps("N1", 6, [7.0, 7.0])], ignore_index=True)
    moi = pd.concat([_ps("N2", 6, [2.0, 2.0]), _ps("N2", 1, [5.0, 5.0])], ignore_index=True)
    x = p9.thay(goc, moi, "N2", (6, 12))
    assert x[(x["mode"] == "N2") & (x.h == 6)]["mae"].tolist() == [2.0, 2.0]
    assert x[(x["mode"] == "N2") & (x.h == 1)]["mae"].tolist() == [1.0, 1.0]
    assert x[x["mode"] == "N1"]["mae"].tolist() == [7.0, 7.0]
    assert len(x) == 6
