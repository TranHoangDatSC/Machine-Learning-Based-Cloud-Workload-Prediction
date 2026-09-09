"""Kiểm chứng chính công cụ kiểm cổng GĐ2.

Một công cụ kiểm phải chứng minh được nó phân biệt được đạt với trượt. Trong dự án
này `test_env.py` đã hai lần báo đạt trên môi trường hỏng, nên mọi công cụ cổng về
sau đều phải có test kiểu này — xem `tests/test_check_gd1.py` và
`research-log/gate-gd2.md` mục 0.

Dựng một thế giới giả lập tí hon trong `tmp_path`: ba môi trường, mỗi môi trường vài
chuỗi × 2304 bucket, có NaN rải rác. Sinh ma trận đặc trưng ĐÚNG bằng
`scripts/reference_gd2.py`, rồi phá theo bảy kiểu và kiểm `check_gd2.py` bắt được
từng kiểu:

    A. đúng hết                          -> phải ĐẠT
    B. quên .shift(1) ở rolling          -> phải TRƯỢT  (R2)
    C. min_periods=1                     -> phải TRƯỢT  (R4, còn NaN)
    D. lag bắc cầu qua ranh giới chuỗi   -> phải TRƯỢT  (R3)
    E. dropna thay cho luật cửa sổ       -> phải TRƯỢT  (R4, thừa dòng)
    F. thêm một đặc trưng ngoài mục 8    -> phải TRƯỢT  (schema)
    G. lịch suy từ bucket đánh số lại    -> phải TRƯỢT  (bẫy múi giờ)
    H. roll_std dùng ddof=0              -> phải TRƯỢT  (vân tay, QĐ-010)

Kiểu E là kiểu nguy hiểm nhất và là kiểu chính A đã mắc khi viết bản tham chiếu:
`dropna()` lỏng hơn luật `[t-24, t]` vì 19 đặc trưng chỉ chạm 15 điểm trong cửa sổ.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_gd2.py"
REFERENCE = ROOT / "scripts" / "reference_gd2.py"

WINDOW = 2304
MAXLAG = 24
HORIZONS = (1, 6, 12)
ENVS = ("E1", "E2", "E3")
N_SERIES = 3

# b0 giả lập: E1, E2 là epoch thật; E3 bắt đầu từ 0 như Alibaba (QĐ-010).
B0 = {"E1": 4587716, "E2": 4584360, "E3": 0}


@pytest.fixture(scope="module")
def ref_mod():
    """Nạp `reference_gd2.py` như một module để dùng lại phần sinh đặc trưng."""
    if not REFERENCE.exists():
        pytest.skip("chưa có scripts/reference_gd2.py")
    spec = importlib.util.spec_from_file_location("ref_gd2", REFERENCE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sinh_Y(env, seed=42):
    """Chuỗi giả lập: nền tuần hoàn cộng nhiễu, rắc vài cụm NaN đủ kiểu."""
    rng = np.random.default_rng(seed + hash(env) % 1000)
    t = np.arange(WINDOW)
    Y = np.empty((N_SERIES, WINDOW))
    for i in range(N_SERIES):
        Y[i] = 40 + 15 * np.sin(2 * np.pi * t / 288 + i) + rng.normal(0, 3, WINDOW)
    Y = np.clip(Y, 0, 100)

    # NaN: một cụm dài ở giữa, một điểm lẻ, và một cụm ở gần mép.
    Y[0, 700:706] = np.nan
    Y[1, 1500] = np.nan
    Y[2, 300:302] = np.nan
    # Điểm nằm trong [t-23, t-13] của một số dòng nhưng không đặc trưng nào dùng —
    # đây chính là chỗ `dropna` và luật cửa sổ tách nhau ra.
    Y[0, 1000] = np.nan
    return Y


def khung_dac_trung(ref, env, Y, h, feats=None, mask=None):
    """Gộp đặc trưng + định danh + target thành bảng đúng schema của cổng."""
    b0 = B0[env]
    if feats is None:
        feats = ref.build_features(Y, b0, "auto")
    if mask is None:
        mask, tgt = ref.valid_mask(feats, Y, h)
    else:
        _, tgt = ref.valid_mask(feats, Y, h)

    sid = np.repeat([f"{env}_{i}" for i in range(Y.shape[0])], WINDOW).reshape(Y.shape)
    buc = np.tile(np.arange(b0, b0 + WINDOW), (Y.shape[0], 1))

    data = {"series_id": sid[mask], "bucket": buc[mask]}
    for k, v in feats.items():
        data[k] = np.asarray(v)[mask]
    data["target"] = tgt[mask]
    return pd.DataFrame(data)


def dung_the_gioi(ref, tmp, phá=None):
    """Sinh catalog, tham chiếu và 9 ma trận đặc trưng cho ba môi trường giả lập.

    `phá` là hàm (env, Y, feats, mask, h) -> (feats, mask) để tiêm lỗi.
    """
    feat_dir = tmp / "features"
    ref_dir = tmp / "tables"
    feat_dir.mkdir(parents=True, exist_ok=True)
    ref_dir.mkdir(parents=True, exist_ok=True)

    cat_rows = []
    refs = []
    for env in ENVS:
        Y = sinh_Y(env)
        b0 = B0[env]
        feats_ok = ref.build_features(Y, b0, "auto")

        # Tham chiếu của A luôn sinh từ bản ĐÚNG — nó là thước đo, không bị phá.
        fstats = {}
        m1_ok, _ = ref.valid_mask(feats_ok, Y, 1)
        for name, v in feats_ok.items():
            sel = np.asarray(v)[m1_ok]
            fstats[name] = {"mean": round(float(sel.mean()), 6),
                            "std": round(float(sel.std(ddof=1)), 6),
                            "nan_pct_toan_luoi": 0.0}
        r = {"env": env, "b0": b0, "n_series": Y.shape[0],
             "moc_lich_that": b0 * 300 >= 1_000_000_000,
             "n_dac_trung": len(feats_ok), "dac_trung": fstats}

        for h in HORIZONS:
            m_ok, _ = ref.valid_mask(feats_ok, Y, h)
            r[f"dong_h{h}"] = int(m_ok.sum())

            feats, mask = feats_ok, m_ok
            if phá is not None:
                feats, mask = phá(env, Y, dict(feats_ok), m_ok.copy(), h, ref)
            khung_dac_trung(ref, env, Y, h, feats, mask).to_parquet(
                feat_dir / f"{env}_h{h}.parquet", index=False)

        refs.append(r)

        # Catalog: neo cứng lấy từ bản ĐÚNG, giống hệt vai trò của GĐ1.
        for i in range(Y.shape[0]):
            row = {"env": env, "series_id": f"{env}_{i}", "kept": True}
            for h in HORIZONS:
                mh, _ = ref.valid_mask(feats_ok, Y, h)
                row[f"valid_rows_h{h}"] = int(mh[i].sum())
            cat_rows.append(row)

    pd.DataFrame(cat_rows).to_parquet(tmp / "catalog.parquet", index=False)
    (ref_dir / "reference_gd2.json").write_text(
        json.dumps(refs, ensure_ascii=False, indent=2), encoding="utf-8")
    return feat_dir, tmp / "catalog.parquet", ref_dir


def chay_checker(feat_dir, cat_path, ref_dir):
    r = subprocess.run(
        [sys.executable, str(CHECKER), "--features", str(feat_dir),
         "--catalog", str(cat_path), "--ref", str(ref_dir)],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ============================================================== A. đúng hết

def test_ma_tran_dung_thi_dat(ref_mod, tmp_path):
    """Không có lỗi nào thì checker phải cho qua. Nếu mục này đỏ, mọi mục dưới vô nghĩa."""
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path))
    assert rc == 0, f"ma trận đúng mà checker báo trượt:\n{out}"
    assert "ĐẠT" in out


# ====================================================== B–H. bảy kiểu phá

def test_quen_shift_1_thi_truot(ref_mod, tmp_path):
    """R2: cửa sổ rolling gồm cả điểm hiện tại -> y_t luôn nằm trong biên."""
    def phá(env, Y, feats, mask, h, ref):
        for w in (6, 12):
            feats[f"roll_min_{w}"] = np.minimum(feats[f"roll_min_{w}"], Y)
            feats[f"roll_max_{w}"] = np.maximum(feats[f"roll_max_{w}"], Y)
        return feats, mask

    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path, phá))
    assert rc == 1, f"quên .shift(1) mà checker vẫn cho qua:\n{out}"
    assert "loại điểm hiện tại" in out


def test_giu_dong_chua_du_24_bucket_lich_su_thi_truot(ref_mod, tmp_path):
    """R4 + R3: `min_periods=1` rồi lấp NaN -> giữ cả dòng chưa đủ lịch sử.

    Lưu ý về `min_periods=1` một mình: dưới luật cửa sổ `[t-24, t]` nó KHÔNG đổi số
    dòng nào, vì `lag_24` vẫn là NaN nên dòng vẫn bị loại. Nó chỉ gây hại khi đi kèm
    lọc bằng `dropna` (xem kịch bản E) hoặc khi đặc trưng bị lấp như ở đây. Ghi ra để
    ai đọc test không tưởng `min_periods` tự nó vô hại.
    """
    def phá(env, Y, feats, mask, h, ref):
        m = mask.copy()
        m[:, 12:MAXLAG] = True       # có vài điểm lịch sử, chưa đủ 24
        for k, v in feats.items():
            a = np.asarray(v, dtype="float64").copy()
            a[np.isnan(a) & m] = 0.0
            feats[k] = a
        return feats, m

    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path, phá))
    assert rc == 1, f"dòng thiếu lịch sử mà checker vẫn cho qua:\n{out}"
    assert "lịch sử riêng" in out or "số dòng" in out


def test_lag_bac_cau_qua_ranh_gioi_chuoi_thi_truot(ref_mod, tmp_path):
    """R3: chuỗi thứ hai trở đi mượn lịch sử của chuỗi trước -> có dòng ngay tại b0."""
    def phá(env, Y, feats, mask, h, ref):
        m = mask.copy()
        m[1:, :MAXLAG] = True        # các chuỗi sau sinh dòng ở sát đầu cửa sổ
        for k, v in feats.items():   # lấp giá trị để không còn NaN
            a = np.asarray(v, dtype="float64").copy()
            bad = np.isnan(a) & m
            a[bad] = 0.0
            feats[k] = a
        return feats, m

    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path, phá))
    assert rc == 1, f"lag bắc cầu qua chuỗi mà checker vẫn cho qua:\n{out}"
    assert "lịch sử riêng" in out or "ranh giới" in out


def test_dropna_thay_cho_luat_cua_so_thi_truot(ref_mod, tmp_path):
    """R4, kiểu nguy hiểm nhất: `dropna` lỏng hơn luật `[t-24, t]`.

    19 đặc trưng chỉ chạm 15 điểm trong cửa sổ; các điểm `t-23`..`t-13` không đặc
    trưng nào dùng nhưng protocol vẫn đòi. Chính A đã mắc lỗi này (QĐ-010).
    """
    def phá(env, Y, feats, mask, h, ref):
        ok = np.ones_like(mask)
        for v in feats.values():
            ok &= np.isfinite(np.asarray(v, dtype="float64"))
        ok &= np.isfinite(Y)
        tgt = np.full_like(Y, np.nan)
        if h < Y.shape[1]:
            tgt[:, :-h] = Y[:, h:]
        return feats, ok & np.isfinite(tgt)

    feat_dir, cat, ref_dir = dung_the_gioi(ref_mod, tmp_path, phá)
    n_dropna = len(pd.read_parquet(feat_dir / "E1_h1.parquet"))
    n_luat = int(pd.read_parquet(cat).query("env == 'E1'")["valid_rows_h1"].sum())
    assert n_dropna > n_luat, ("dữ liệu giả lập chưa tách được hai định nghĩa — "
                               "cần NaN nằm trong khoảng t-23..t-13")

    rc, out = chay_checker(feat_dir, cat, ref_dir)
    assert rc == 1, f"dropna thay luật cửa sổ mà checker vẫn cho qua:\n{out}"
    assert "dropna" in out


def test_them_dac_trung_ngoai_protocol_thi_truot(ref_mod, tmp_path):
    """Thừa một cột là đổi giao thức — B không được đổi giao thức."""
    feat_dir, cat, ref_dir = dung_the_gioi(ref_mod, tmp_path)
    f = feat_dir / "E1_h1.parquet"
    df = pd.read_parquet(f)
    df["lag_48"] = df["lag_24"]
    df.to_parquet(f, index=False)

    rc, out = chay_checker(feat_dir, cat, ref_dir)
    assert rc == 1, f"đặc trưng thừa mà checker vẫn cho qua:\n{out}"
    assert "lag_48" in out


def test_lich_suy_tu_bucket_danh_so_lai_thi_truot(ref_mod, tmp_path):
    """Bẫy múi giờ: đánh số bucket lại từ 0 làm hour_sin vô nghĩa mà không báo lỗi."""
    feat_dir, cat, ref_dir = dung_the_gioi(ref_mod, tmp_path)
    f = feat_dir / "E1_h1.parquet"
    df = pd.read_parquet(f)
    t = (df["bucket"].to_numpy() - B0["E1"]) * 300      # đánh số lại từ 0
    df["hour_sin"] = np.sin(2 * np.pi * ((t // 3600) % 24) / 24)
    df["hour_cos"] = np.cos(2 * np.pi * ((t // 3600) % 24) / 24)
    df.to_parquet(f, index=False)

    rc, out = chay_checker(feat_dir, cat, ref_dir)
    assert rc == 1, f"lịch sai gốc mà checker vẫn cho qua:\n{out}"
    assert "lịch" in out


def test_roll_std_sai_ddof_thi_truot(ref_mod, tmp_path):
    """QĐ-010 chốt ddof=1. numpy mặc định 0 — hai bên đều 'đúng' mà ra số khác nhau."""
    feat_dir, cat, ref_dir = dung_the_gioi(ref_mod, tmp_path)
    f = feat_dir / "E1_h1.parquet"
    df = pd.read_parquet(f)
    df["roll_std_6"] = df["roll_std_6"] * np.sqrt(5 / 6)     # ddof=1 -> ddof=0
    df["roll_std_12"] = df["roll_std_12"] * np.sqrt(11 / 12)
    df.to_parquet(f, index=False)

    rc, out = chay_checker(feat_dir, cat, ref_dir)
    assert rc == 1, f"sai ddof mà checker vẫn cho qua:\n{out}"
    assert "ddof" in out


# ============================================== trạng thái chưa làm xong

def test_chua_co_ma_tran_thi_bao_thieu_khong_no(ref_mod, tmp_path):
    """B chưa làm là trạng thái bình thường: báo thiếu, không đổ vỡ."""
    feat_dir, cat, ref_dir = dung_the_gioi(ref_mod, tmp_path)
    for p in feat_dir.glob("*.parquet"):
        p.unlink()
    rc, out = chay_checker(feat_dir, cat, ref_dir)
    assert rc == 1
    assert "BÌNH THƯỜNG" in out
    assert "TIẾN ĐỘ GĐ2" in out
