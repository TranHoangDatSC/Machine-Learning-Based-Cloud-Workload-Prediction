"""Kiểm `cwp.evaluation.splits` — bốn phép kiểm rò rỉ L1–L4 của `gate-gd3.md` mục 3.4.

Chạy:  pytest tests/test_splits.py -v

Không dùng dữ liệu thật. Offset ở đây là mảng `arange` tính tay được; test đỏ thì
biết ngay sai ở đâu, và không phụ thuộc `data/features/` có mặt hay không.

Bốn cam kết của `docs/protocol.md` mục 9 (chốt thêm ở QĐ-013 và QĐ-014):

    S1  Ranh giới theo BUCKET: train [0, 1612), val [1612, 1957), test [1957, 2304).
    S2  Purge: dòng thuộc tập S khi cả `t` VÀ `t+h` trong S. Vắt ranh giới thì loại.
    S3  Rolling-origin expanding 5 fold, biên 1612/1681/1750/1819/1888/1957, và
        không fold nào chạm test.
    S4  Không shuffle — thứ tự dòng không ảnh hưởng nhãn của dòng đó.

Ba phép kiểm mà `brief-gd3-b.md` Bước 1 gọi đích danh là `test_L1_*`,
`test_L3_train_fold_ket_thuc_truoc_val_fold` và `test_L3_khong_fold_nao_cham_test`.
S2 là điều khiến L1 xanh; bỏ purge thì L1 đỏ.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from cwp.evaluation.splits import (
    N_FOLDS,
    N_TRAIN,
    N_VAL,
    NHAN_LOAI,
    SPLIT_NAMES,
    WINDOW_BUCKETS,
    bucket_bounds,
    dem_dong,
    fit_mask,
    fold_bounds,
    fold_masks,
    gan_nhan,
    mask_khoang,
    offset,
    split_indices,
    split_masks,
)

HORIZONS = [1, 6, 12]
B0 = 4587716  # bucket đầu của E1 trong sản phẩm GĐ1; giá trị cụ thể không quan trọng
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def off_day():
    """Toàn bộ 2304 offset, không thiếu dòng nào — trường hợp dễ tính tay nhất."""
    return np.arange(WINDOW_BUCKETS, dtype="int64")


# --------------------------------------------------------------- S1 ranh giới

def test_S1_ba_ranh_gioi_khop_QD013():
    assert bucket_bounds() == {
        "train": (0, 1612), "val": (1612, 1957), "test": (1957, 2304)
    }


def test_S1_ba_tap_phu_kin_cua_so_va_khong_chong_nhau():
    b = bucket_bounds()
    assert b["train"][0] == 0 and b["test"][1] == WINDOW_BUCKETS
    assert b["train"][1] == b["val"][0]
    assert b["val"][1] == b["test"][0]
    assert (b["train"][1] - b["train"][0]) == N_TRAIN == 1612
    assert (b["val"][1] - b["val"][0]) == N_VAL == 345
    assert (b["test"][1] - b["test"][0]) == 347


def test_S1_offset_tru_dung_b0():
    bucket = pd.Series([B0, B0 + 1, B0 + 2303], dtype="int64")
    assert offset(bucket, B0).tolist() == [0, 1, 2303]


# ------------------------------------------------------- L1 / S2 purge, rò rỉ

@pytest.mark.parametrize("h", HORIZONS)
def test_L1_moi_dong_train_co_target_van_trong_train(off_day, h):
    """L1 của `gate-gd3.md` mục 3.4 — phép kiểm quan trọng nhất của Bước 1.

    Với mọi dòng train thì `t + h < 1612`. Gán tập theo `t` thôi mà quên `t+h` thì
    phép kiểm này đỏ, và đó chính là kiểu rò rỉ QĐ-013 điểm 2 chặn.
    """
    m = split_masks(off_day, h)["train"]
    t = off_day[m]
    assert t.size > 0
    assert (t + h < N_TRAIN).all()
    assert t.max() == N_TRAIN - 1 - h  # sát ranh giới, không hơn


@pytest.mark.parametrize("h", HORIZONS)
@pytest.mark.parametrize("tap", SPLIT_NAMES)
def test_S2_ca_t_va_t_cong_h_nam_trong_cung_tap(off_day, h, tap):
    lo, hi = bucket_bounds()[tap]
    t = off_day[split_masks(off_day, h)[tap]]
    assert (t >= lo).all()
    assert (t + h < hi).all()


@pytest.mark.parametrize("h", HORIZONS)
def test_S2_ba_tap_roi_nhau(off_day, h):
    m = split_masks(off_day, h)
    tong = m["train"].astype(int) + m["val"].astype(int) + m["test"].astype(int)
    assert tong.max() <= 1


@pytest.mark.parametrize("h", HORIZONS)
def test_S2_so_dong_bi_purge_dung_bang_2h_khi_khong_thieu_dong(off_day, h):
    """Chuỗi đủ 2304 offset thì mỗi ranh giới nuốt đúng `h` dòng, hai ranh giới là `2h`.

    Đây là dạng vi mô của phép kiểm tự thân ở `gate-gd3.md` mục 2.2
    (`n_chuỗi × 2 × h`). Trên dữ liệu thật số này nhỏ hơn vì NaN đã lấy trước một ít.
    """
    dem = dem_dong(off_day, h)
    # `h` offset cuối cửa sổ vốn không có target thật; ở đây chúng cũng rơi ra ngoài.
    assert dem[NHAN_LOAI] == 3 * h
    assert sum(dem[t] for t in SPLIT_NAMES) == WINDOW_BUCKETS - 3 * h


def test_S2_quen_purge_thi_khac_han_ket_qua_dung(off_day):
    """Bản gán-theo-`t` (sai) và bản đúng phải khác nhau — nếu không, test vô nghĩa."""
    h = 12
    dung = split_masks(off_day, h)["train"]
    sai = off_day < N_TRAIN  # gán theo `t` thôi, đúng kiểu QĐ-013 điểm 2 cấm
    assert sai.sum() - dung.sum() == h
    assert (off_day[sai].max() + h) >= N_TRAIN  # bản sai thật sự rò rỉ


# --------------------------------------------------- L3 / S3 rolling-origin

def test_S3_bien_fold_khop_QD014():
    fb = fold_bounds()
    bien = [f["train"][1] for f in fb] + [fb[-1]["val"][1]]
    assert bien == [1612, 1681, 1750, 1819, 1888, 1957]


def test_S3_expanding_khong_phai_sliding():
    fb = fold_bounds()
    assert all(f["train"][0] == 0 for f in fb)
    do_dai = [f["train"][1] - f["train"][0] for f in fb]
    assert do_dai == sorted(do_dai) and len(set(do_dai)) == N_FOLDS


@pytest.mark.parametrize("h", HORIZONS)
def test_L3_train_fold_ket_thuc_truoc_val_fold(off_day, h):
    """L3 — với mọi fold, `max(t + h)` của train nhỏ hơn `min(t)` của validation."""
    for i, m in enumerate(fold_masks(off_day, h)):
        t_tr, t_va = off_day[m["train"]], off_day[m["val"]]
        assert t_tr.size > 0 and t_va.size > 0, f"fold {i} rong"
        assert (t_tr + h).max() < t_va.min()


@pytest.mark.parametrize("h", HORIZONS)
def test_L3_khong_fold_nao_cham_test(off_day, h):
    """L3 — không dòng nào của bất kỳ fold nào có `t >= 1957`. Test sạch tuyệt đối."""
    test_lo = bucket_bounds()["test"][0]
    for i, m in enumerate(fold_masks(off_day, h)):
        for ten in ("train", "val"):
            t = off_day[m[ten]]
            assert (t < test_lo).all(), f"fold {i} {ten} cham test"
            assert (t + h < test_lo).all(), f"fold {i} {ten} co target roi vao test"


@pytest.mark.parametrize("h", HORIZONS)
def test_L3_val_cua_nam_fold_phu_kin_vung_validation(off_day, h):
    """Năm vùng validation rời nhau, hợp lại đúng bằng `[1612, 1957)` trừ phần purge."""
    fm = fold_masks(off_day, h)
    tong = np.sum([m["val"].astype(int) for m in fm], axis=0)
    assert tong.max() <= 1
    lo, hi = bucket_bounds()["val"]
    trong_vung = (off_day >= lo) & (off_day < hi)
    # Mỗi fold nuốt `h` dòng ở cuối vùng val của nó, 5 fold là 5h.
    assert tong.sum() == int(trong_vung.sum()) - N_FOLDS * h


@pytest.mark.parametrize("h", HORIZONS)
def test_L3_train_fold_sau_chua_tron_train_fold_truoc(off_day, h):
    fm = fold_masks(off_day, h)
    for truoc, sau in zip(fm, fm[1:]):
        assert (truoc["train"] & ~sau["train"]).sum() == 0


# ----------------------------------------------------------- S4 không shuffle

@pytest.mark.parametrize("h", HORIZONS)
def test_S4_thu_tu_dong_khong_doi_nhan(off_day, h):
    """Đảo thứ tự dòng rồi gán lại: nhãn đi theo dòng, không theo vị trí."""
    rng = np.random.default_rng(0)
    hoan_vi = rng.permutation(len(off_day))
    goc = gan_nhan(off_day, h)
    dao = gan_nhan(off_day[hoan_vi], h)
    assert (dao == goc[hoan_vi]).all()


def test_S4_khong_dung_toi_random_state():
    """Đọc mã nguồn: không nơi nào trong `splits.py` gọi bộ sinh số ngẫu nhiên.

    Chỉ soi phần **mã thật** — bỏ chú thích và chuỗi ký tự, vì docstring của chính
    module có nhắc chữ "shuffle" để giải thích mục 9.
    """
    import io
    import tokenize

    p = ROOT / "src" / "cwp" / "evaluation" / "splits.py"
    ma = " ".join(
        tok.string
        for tok in tokenize.generate_tokens(io.StringIO(p.read_text("utf-8")).readline)
        if tok.type not in (tokenize.COMMENT, tokenize.STRING)
    )
    for tu in ("random", "shuffle", "sample", "permutation"):
        assert tu not in ma, f"splits.py khong duoc dung {tu!r} (muc 9)"


# ----------------------------------------------------- tiện ích và hợp đồng

@pytest.mark.parametrize("h", HORIZONS)
def test_chi_so_va_mat_na_noi_cung_mot_dieu(off_day, h):
    mn, ix = split_masks(off_day, h), split_indices(off_day, h)
    for ten in SPLIT_NAMES:
        assert np.array_equal(np.flatnonzero(mn[ten]), ix[ten])


@pytest.mark.parametrize("h", HORIZONS)
def test_dong_thieu_giua_chung_khong_pha_ranh_gioi(h):
    """Bỏ hẳn 200 offset giữa tập train: ranh giới không đổi, chỉ số dòng đổi."""
    off = np.setdiff1d(np.arange(WINDOW_BUCKETS), np.arange(500, 700))
    t = off[split_masks(off, h)["train"]]
    assert (t + h < N_TRAIN).all()
    assert not ((t >= 500) & (t < 700)).any()


def test_horizon_khong_hop_le_thi_bao_loi(off_day):
    for xau in (0, -1):
        with pytest.raises(ValueError):
            split_masks(off_day, xau)
        with pytest.raises(ValueError):
            fold_masks(off_day, xau)


def test_ghim_config_split_yaml():
    """`config/split.yaml` là tài liệu, `splits.py` là bản chốt — test này gác hai bên.

    Cùng lý do đã ghi ở `tests/test_config.py`: sửa một bên mà không sửa bên kia thì
    đỏ, thay vì lặng lẽ nói hai thứ khác nhau.
    """
    cfg = yaml.safe_load((ROOT / "config" / "split.yaml").read_text(encoding="utf-8"))
    fb = fold_bounds()
    assert cfg["shuffle"] is False
    assert cfg["boundary"] == "bucket"
    assert cfg["purge_straddling"] is True
    assert cfg["train"] == pytest.approx(0.70)
    assert cfg["val"] == pytest.approx(0.15)
    assert cfg["cv"]["mode"] == "expanding"
    assert cfg["cv"]["n_splits"] == N_FOLDS
    assert cfg["cv"]["val_bucket_per_fold"] == N_VAL // N_FOLDS
    assert cfg["cv"]["bien_fold"] == [f["train"][1] for f in fb] + [fb[-1]["val"][1]]
    assert cfg["horizons"] == HORIZONS


@pytest.mark.parametrize("h", HORIZONS)
def test_L3_vung_huan_luyen_cuoi_khong_cham_test(off_day, h):
    """Model cuối học trên train + val; target của nó vẫn phải nằm trước test."""
    test_lo = bucket_bounds()["test"][0]
    t = off_day[fit_mask(off_day, h)]
    assert t.size > 0
    assert (t + h < test_lo).all()
    assert t.max() == test_lo - 1 - h
    # Và nó phải chứa trọn train + val đã purge theo từng tập.
    mn = split_masks(off_day, h)
    assert ((mn["train"] | mn["val"]) & ~fit_mask(off_day, h)).sum() == 0


@pytest.mark.parametrize("h", HORIZONS)
def test_mask_khoang_ap_dung_luat_purge(off_day, h):
    m = mask_khoang(off_day, h, 100, 200)
    t = off_day[m]
    assert t.min() == 100 and t.max() == 200 - 1 - h
