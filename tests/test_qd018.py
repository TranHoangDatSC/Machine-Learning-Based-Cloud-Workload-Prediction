"""Test cho QĐ-018 — giới hạn Samuelson, luật loại, lọc tập train, và thay dòng N1.

Chạy:  pytest tests/test_qd018.py -v

Không đọc dữ liệu thật hay kết quả. Bốn điều phải giữ:

- giới hạn Samuelson đúng là **định lý**: không mẫu nào vượt, kể cả mẫu có ngoại lai
- luật **không nhìn test**: đổi `y` từ bucket 1957 trở đi không đổi danh sách loại
- lọc chỉ đụng **tập train**, không đụng tập chấm
- `thay_n1` chỉ thay dòng N1, giữ nguyên N0 và N2
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import loai_n1_qd018 as ln  # noqa: E402
import phan_tich_qd018 as pq  # noqa: E402
import run_qd018 as r8  # noqa: E402

W = 2304


def _z_max(x):
    x = x[np.isfinite(x)]
    return np.max(np.abs(x - x.mean()) / x.std(ddof=1))


@pytest.mark.parametrize("seed", range(5))
def test_samuelson_la_dinh_ly_voi_mau_ngau_nhien(seed):
    rng = np.random.default_rng(seed)
    for n in (2, 3, 10, 1612):
        x = rng.standard_cauchy(n)          # đuôi rất dày
        assert _z_max(x) <= ln.bien_samuelson(n) * (1 + 1e-12)


def test_samuelson_dat_dau_bang_voi_mot_ngoai_lai():
    """Một điểm khác, n−1 điểm bằng nhau: |z| chạm đúng (n−1)/√n."""
    n = 1612
    x = np.zeros(n)
    x[0] = 1.0
    assert _z_max(x) == pytest.approx(ln.bien_samuelson(n), rel=1e-12)


def _Y(n_chuoi=4, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(50, 5, (n_chuoi, W))


def test_luat_bat_may_dung_yen_roi_chay_o_validation():
    Y = _Y()
    Y[1, :1612] = 0.0
    Y[1, :1612:7] = 0.01                     # gần hằng, sd > 0
    Y[1, 1612:] = 40.0
    df, vp = ln.xet_moi_truong("E3", [f"s{i}" for i in range(4)], Y)
    assert vp == 0
    assert df.set_index("series_id")["loai"].to_dict() == {"s0": False, "s1": True,
                                                         "s2": False, "s3": False}


def test_luat_khong_nhin_test():
    Y = _Y()
    ids = [f"s{i}" for i in range(4)]
    a, _ = ln.xet_moi_truong("E1", ids, Y)
    Y2 = Y.copy()
    Y2[:, 1957:] = 1e6                        # phá hẳn vùng test
    b, _ = ln.xet_moi_truong("E1", ids, Y2)
    assert a["loai"].equals(b["loai"])
    assert np.allclose(a["max_abs_z_khop"], b["max_abs_z_khop"])


def test_luat_bo_qua_chuoi_sd_bang_0():
    Y = _Y()
    Y[2, :1612] = 3.0
    df, vp = ln.xet_moi_truong("E1", [f"s{i}" for i in range(4)], Y)
    assert vp == 0 and not df.loc[2, "loai"]


def test_mat_na_train_chi_bo_chuoi_bi_loai():
    sid = np.array(["a", "a", "b", "b", "c"])
    fit = np.array([True, False, True, True, True])
    m = r8.mat_na_train(sid, fit, {"b"})
    assert m.tolist() == [True, False, False, False, True]
    assert r8.mat_na_train(sid, fit, set()).tolist() == fit.tolist()


def test_ke_hoach_qd018_du_75_khop_195_cham():
    import run_qd017 as rq
    v = rq.ke_hoach(r8.CAP, ["N1"], [1, 6, 12], ["lr", "ridge", "rf", "xgb", "svr"], set())
    assert sum(len(x["model"]) for x in v) == 75
    assert sum(len(d) for x in v for d in x["model"].values()) == 195


def _bang(mode, mae, nguon="E3", dich="E1"):
    return pd.DataFrame({"nguon": nguon, "dich": dich, "mode": mode, "lich": "co", "h": 1,
                         "model": "lr", "series_id": ["x", "y"], "n_dong": 10,
                         "mae": mae})


def test_thay_n1_chi_thay_dong_n1():
    goc = pd.concat([_bang("N0", [1.0, 2.0]), _bang("N1", [9.0, 9.0]),
                     _bang("N2", [3.0, 4.0])], ignore_index=True)
    moi = _bang("N1", [1.5, 2.5])
    x = pq.thay_n1(goc, moi).sort_values(["mode", "series_id"])
    assert x[x["mode"] == "N1"]["mae"].tolist() == [1.5, 2.5]
    assert x[x["mode"] == "N0"]["mae"].tolist() == [1.0, 2.0]
    assert x[x["mode"] == "N2"]["mae"].tolist() == [3.0, 4.0]
    assert len(x) == 6


def test_tach_moi_khong_cho_may_gia_lot_vao_d1():
    """Ca 2026-09-14: E1a→E1a lọt vào bảng đường chéo D1 vì chỉ lọc nguồn == đích."""
    moi = pd.concat([_bang("N1", [1.0, 1.0], "E1", "E1"), _bang("N1", [1.0, 1.0], "E3", "E1"),
                     _bang("N1", [1.0, 1.0], "E1a", "E1a"), _bang("N1", [1.0, 1.0], "E1g", "E1a")],
                    ignore_index=True)
    cheo, chuyen, d2 = pq.tach_moi(moi)
    assert set(zip(cheo.nguon, cheo.dich)) == {("E1", "E1")}
    assert set(zip(chuyen.nguon, chuyen.dich)) == {("E3", "E1")}
    assert set(zip(d2.nguon, d2.dich)) == {("E1a", "E1a"), ("E1g", "E1a")}


def test_thay_n1_giu_to_hop_moi_khong_co():
    goc = pd.concat([_bang("N1", [9.0, 9.0]), _bang("N1", [7.0, 7.0], dich="E2")],
                    ignore_index=True)
    x = pq.thay_n1(goc, _bang("N1", [1.0, 1.0]))
    assert x[x["dich"] == "E2"]["mae"].tolist() == [7.0, 7.0]
    assert x[x["dich"] == "E1"]["mae"].tolist() == [1.0, 1.0]
