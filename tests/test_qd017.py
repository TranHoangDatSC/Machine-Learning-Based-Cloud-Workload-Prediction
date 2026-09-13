"""Test cho QĐ-017 — chia nhóm, gộp chặt, kế hoạch resume, và HƯỚNG của phép kiểm.

Chạy:  pytest tests/test_qd017.py -v

Không test nào đọc dữ liệu thật hay kết quả D1, D2. Mọi dữ liệu dựng trong bộ nhớ.

Ba chỗ từng hỏng thật trong dự án, mỗi chỗ có ít nhất một test ở đây:

- `--resume` bỏ qua im lặng khi chỉ kiểm tới `h` (2026-09-12)
- hướng Wilcoxon lấy từ hiệu hai trung vị, đảo kết luận ở 8 cặp (GĐ3)
- bản nháp đầu của `phan_tich_qd017.bat_doi_xung` đảo nhãn Mann–Whitney (2026-09-13)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_qd017 as bq  # noqa: E402
import phan_tich_qd017 as pt  # noqa: E402
import run_qd017 as rq  # noqa: E402

W = 2304


# ---------------------------------------------------------------- chia nhóm

def _ids(n=735):
    return [f"E1_{i}" for i in range(1, n + 1)]


def test_chia_nhom_co_dung():
    nh = bq.chia_nhom(_ids())
    dem = nh["env"].value_counts()
    assert dem["E1a"] == 368 and dem["E1g"] == 365 and dem["bo"] == 2
    g = nh[nh.env == "E1g"].groupby("series_id")["vm"]
    assert g.ngroups == 73 and (g.size() == 5).all() and (g.nunique() == 5).all()


def test_chia_nhom_roi_nhau_va_phu_kin():
    nh = bq.chia_nhom(_ids())
    a = set(nh.loc[nh.env == "E1a", "vm"])
    g = set(nh.loc[nh.env == "E1g", "vm"])
    assert not a & g
    assert sorted(nh["vm"]) == sorted(_ids())


def test_chia_nhom_khong_phu_thuoc_thu_tu_dau_vao():
    ids = _ids()
    tron = list(np.random.default_rng(7).permutation(ids))
    assert bq.chia_nhom(ids).equals(bq.chia_nhom(tron))


def test_chia_nhom_doi_hat_giong_thi_doi():
    assert not bq.chia_nhom(_ids(), seed=42).equals(bq.chia_nhom(_ids(), seed=43))


def test_chia_nhom_tu_choi_trung():
    with pytest.raises(ValueError):
        bq.chia_nhom(["E1_1", "E1_1", "E1_2"])


# --------------------------------------------------------------------- gộp

def _e1_gia(n=10, seed=0):
    rng = np.random.default_rng(seed)
    dong = []
    for i in range(n):
        y = rng.uniform(0, 100, W)
        dong.append(pd.DataFrame({"env": "E1", "series_id": f"E1_{i}",
                                  "bucket": np.arange(W) + 1000, "y": y,
                                  "is_interp": False}))
    return pd.concat(dong, ignore_index=True)


def _nhom(thanh_vien):
    return pd.DataFrame([{"env": "E1g", "series_id": "E1g_00", "vm": v}
                         for v in thanh_vien], columns=["env", "series_id", "vm"])


def test_gop_la_trung_binh_khi_du_thanh_vien():
    e1 = _e1_gia()
    tv = [f"E1_{i}" for i in range(5)]
    g = bq.gop_nhom(e1, _nhom(tv))
    mong = e1[e1.series_id.isin(tv)].groupby("bucket")["y"].mean().to_numpy()
    assert np.allclose(g["y"].to_numpy(), mong, atol=1e-12)


def test_gop_chat_mot_thanh_vien_nan_thi_nan():
    e1 = _e1_gia()
    tv = [f"E1_{i}" for i in range(5)]
    e1.loc[(e1.series_id == "E1_3") & (e1.bucket == 1500), "y"] = np.nan
    g = bq.gop_nhom(e1, _nhom(tv)).set_index("bucket")["y"]
    assert np.isnan(g.loc[1500])
    assert np.isfinite(g.drop(1500)).all()


def test_gop_khong_dung_nanmean():
    """Bản phá: thay mean chặt bằng nanmean — điểm thiếu thành viên phải vẫn là NaN."""
    e1 = _e1_gia()
    tv = [f"E1_{i}" for i in range(5)]
    e1.loc[(e1.series_id == "E1_0") & (e1.bucket.between(1200, 1209)), "y"] = np.nan
    g = bq.gop_nhom(e1, _nhom(tv))
    assert int(g["y"].isna().sum()) == 10


def test_gop_giu_thang_0_100():
    g = bq.gop_nhom(_e1_gia(), _nhom([f"E1_{i}" for i in range(5)]))
    assert g["y"].between(0, 100).all()


# ---------------------------------------------------------- kế hoạch resume

def test_ke_hoach_day_du_khi_chua_co_gi():
    v = rq.ke_hoach(rq.THI_NGHIEM["D1"], ["N0", "N1", "N2"], [1, 6, 12],
                    ["lr", "ridge", "rf", "xgb", "svr"], set())
    assert sum(len(x["model"]) for x in v) == 135
    v2 = rq.ke_hoach(rq.THI_NGHIEM["D2"], ["N0", "N1", "N2"], [1, 6, 12],
                     ["lr", "ridge", "rf", "xgb", "svr"], set())
    assert sum(len(x["model"]) for x in v2) == 90
    assert sum(len(d) for x in v2 for d in x["model"].values()) == 180


def test_resume_kiem_toi_ten_model():
    """Ca 2026-09-12: có `lr` rồi thì `xgb` vẫn phải chạy."""
    da_co = {(e, e, m, "co", h, "lr") for e in ("E1", "E2", "E3")
             for m in ("N0", "N1", "N2") for h in (1, 6, 12)}
    v = rq.ke_hoach(rq.THI_NGHIEM["D1"], ["N0", "N1", "N2"], [1, 6, 12],
                    ["lr", "xgb"], da_co)
    assert sum(len(x["model"]) for x in v) == 27
    assert all(list(x["model"]) == ["xgb"] for x in v)


def test_resume_thieu_mot_dich_thi_chi_chay_dich_do():
    da_co = {("E1a", "E1a", "N1", "co", 6, "rf")}
    v = rq.ke_hoach([("E1a", "E1a"), ("E1a", "E1g")], ["N1"], [6], ["rf"], da_co)
    assert v == [{"nguon": "E1a", "mode": "N1", "h": 6, "model": {"rf": ["E1g"]}}]


def test_resume_du_het_thi_rong():
    da_co = {("E2", "E2", "N0", "co", 1, "lr")}
    assert rq.ke_hoach([("E2", "E2")], ["N0"], [1], ["lr"], da_co) == []


def test_sieu_tham_so_may_gia_lay_tu_e1():
    assert rq.SIEU_THAM_SO_TU["E1a"] == "E1" and rq.SIEU_THAM_SO_TU["E1g"] == "E1"


# ------------------------------------------------------------ hướng phép kiểm

def _L(nguon, dich, L, n=60, seed=0, mode="N1", h=1, model="lr"):
    rng = np.random.default_rng(seed)
    mae_cheo = rng.uniform(1, 2, n)
    return pd.DataFrame({"nguon": nguon, "dich": dich, "mode": mode, "h": h,
                         "model": model, "series_id": [f"s{i}" for i in range(n)],
                         "mae": mae_cheo * L * rng.uniform(0.95, 1.05, n),
                         "mae_cheo": mae_cheo})


def _du_to_hop(nguon, dich, L, seed):
    return pd.concat([_L(nguon, dich, L, seed=seed + 7 * i, mode=md, h=h, model=m)
                      for i, (md, h, m) in enumerate(
                          (md, h, m) for md in pt.MODES for h in pt.HS for m in pt.ML)],
                     ignore_index=True)


def test_bat_doi_xung_huong():
    """Chiều ngược có L gấp 3 lần -> nhãn phải là 'ngược tốn hơn', rb < 0."""
    x = pd.concat([_du_to_hop("E1a", "E1g", 1.0, 0), _du_to_hop("E1g", "E1a", 3.0, 1000)])
    x["L"] = x["mae"] / x["mae_cheo"]
    out = pt.bat_doi_xung(x, pt.DOI_XUNG_D2)
    assert len(out) == 45
    assert (out["ket_luan"] == "ngược tốn hơn").all()
    assert (out["rank_biserial"] < 0).all()
    assert out["huong_khop_trung_vi"].all()


def test_bat_doi_xung_huong_chieu_kia():
    x = pd.concat([_du_to_hop("E1a", "E1g", 3.0, 0), _du_to_hop("E1g", "E1a", 1.0, 1000)])
    x["L"] = x["mae"] / x["mae_cheo"]
    out = pt.bat_doi_xung(x, pt.DOI_XUNG_D2)
    assert (out["ket_luan"] == "xuôi tốn hơn").all()


def test_t_d1b_huong_va_ho_holm():
    x = pd.concat([_du_to_hop("E1", "E2", 1.3, 0)])
    x["L"] = x["mae"] / x["mae_cheo"]
    out = pt.t_d1b(x)
    assert len(out) == 45
    assert (out["ket_luan"] == "transfer tệ hơn đường chéo").all()
    assert out.groupby(["nguon", "dich", "h"]).size().eq(15).all()


def test_t_d1a_huong_lay_tu_trung_vi_cua_hieu():
    """Bẫy GĐ3: trung vị N1 nhỏ hơn trung vị N0, nhưng TỪNG chuỗi N1 lại lớn hơn N0.

    Chuỗi 0..29 có MAE nhỏ, chuỗi 30..59 lớn. N1 cộng 0,1 vào mọi chuỗi nhưng hoán vị
    mức giữa hai nửa sao cho hiệu hai trung vị âm còn trung vị của hiệu dương.
    """
    n = 61
    n0 = np.r_[np.full(30, 1.0), 5.0, np.full(30, 10.0)]
    n1 = n0 + 0.1
    n1[30] = 1.05                        # chuỗi giữa: đẩy trung vị N1 xuống dưới N0
    dong = []
    for md, v in (("N0", n0), ("N1", n1), ("N2", n0)):
        for h in pt.HS:
            for m in pt.ML:
                dong.append(pd.DataFrame({"nguon": "E1", "dich": "E1", "mode": md, "h": h,
                                          "model": m, "series_id": range(n), "mae": v}))
    cheo = pd.concat(dong, ignore_index=True)
    # Bẫy có thật: hiệu hai trung vị nói N1 tốt hơn, trung vị của hiệu nói N1 tệ hơn.
    assert np.median(n1) < np.median(n0) and np.median(n1 - n0) > 0
    out = pt.t_d1a(cheo)
    n1r = out[out.so_sanh == "N1_vs_N0"]
    assert (n1r["hieu_p50"] > 0).all()
    assert (n1r["ket_luan"] == "Nk tệ hơn N0").all()
    assert (out[out.so_sanh == "N2_vs_N0"]["ket_luan"] == "không khác").all()


def test_ghep_L_loai_mau_so_bang_0():
    chuyen = pd.DataFrame({"nguon": "E3", "dich": "E1", "mode": "N0", "h": 1,
                           "model": "lr", "series_id": ["a", "b"], "mae": [2.0, 3.0]})
    cheo = pd.DataFrame({"nguon": "E1", "dich": "E1", "mode": "N0", "h": 1,
                         "model": "lr", "series_id": ["a", "b"], "mae": [1.0, 0.0]})
    L = pt.ghep_L(chuyen, cheo).set_index("series_id")["L"]
    assert L["a"] == 2.0 and np.isnan(L["b"])


def test_ghep_L_bo_duong_cheo_khoi_tu_so():
    x = pd.DataFrame({"nguon": ["E1", "E3"], "dich": "E1", "mode": "N0", "h": 1,
                      "model": "lr", "series_id": "a", "mae": [1.0, 2.0]})
    L = pt.ghep_L(x, x[x.nguon == "E1"])
    assert list(L["nguon"]) == ["E3"]


# ------------------------------------------------------------------ luật đọc

@pytest.mark.parametrize("nguoc, xuoi, mong", [
    (10, 0, "tái hiện"), (15, 0, "tái hiện"),
    (10, 1, "không kết luận"), (9, 0, "không kết luận"), (4, 0, "không kết luận"),
    (3, 0, "không tái hiện"), (0, 12, "không tái hiện"),
])
def test_luat_doc_d2(nguoc, xuoi, mong):
    assert pt.doc_d2(nguoc, xuoi) == mong


def test_du_doan_chua_co_ket_qua():
    dd = pt.du_doan(None, None, None, None)
    assert list(dd["ma"]) == [f"P{i}" for i in range(1, 8)]
    assert (dd["ket_qua"] == "chưa có").all()
