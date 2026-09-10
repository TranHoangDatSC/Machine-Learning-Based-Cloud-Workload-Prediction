"""Kiểm chứng chính công cụ kiểm cổng GĐ3.

Bài học số 2 của dự án: `test_env.py` từng báo 12/12 trên một môi trường hỏng hoàn
toàn vì nó chỉ đọc metadata chứ không import. Từ đó mọi công cụ cổng đều phải có test
kiểu này — xem `tests/test_check_gd1.py`, `tests/test_check_gd2.py`, và
`research-log/gate-gd3.md` mục 0.

Dựng một thế giới giả lập trong `tmp_path`: ba môi trường × 3 chuỗi × 2304 bucket, có
NaN rải rác đúng chỗ hiểm. Tham chiếu của A sinh bằng chính `scripts/reference_gd3.py`
(nó là thước đo, không bao giờ bị phá). Hai bảng của B sinh bằng `mo_phong_B` — một
đường tính riêng, có công tắc để tiêm lỗi. Rồi kiểm `check_gd3.py` bắt được từng kiểu:

    A. đúng hết                              -> phải ĐẠT
    B. gán tập theo `t`, quên `t+h`          -> phải TRƯỢT  (B1 + loại A số dòng)
    C. mẫu số MASE tính trên test            -> phải TRƯỢT  (loại A, cột mase)
    D. gộp bằng trung bình thay vì trung vị  -> phải TRƯỢT  (loại A, 45 chỉ số p50)
    E. seasonal naive lấp giá trị thiếu      -> phải TRƯỢT  (loại A, n_dong_dung)
    F. thêm đặc trưng ngoài mục 8            -> phải TRƯỢT  (B7)
    G. RMSE < MAE                            -> phải TRƯỢT  (B2)
    H. SMAPE(0,0) trả NaN                    -> phải TRƯỢT  (C5)
    I. MASE khi d=0 trả `inf`                -> phải TRƯỢT  (C9)

Kiểu E là kiểu nguy hiểm nhất ở GĐ3: lấp giá trị thiếu làm seasonal naive **trông**
tốt hơn thật, và không phép kiểm nào khác thấy — số dòng vẫn đúng, chỉ số vẫn nằm
trong khoảng hợp lệ. Chỉ `n_dong_dung` tố cáo được.

Kiểu H và I là loại C: chúng không quan tâm hai bản có khớp nhau không. Đó là lý do
loại C tồn tại (QĐ-014 điểm 3) — ở GĐ3 tính độc lập yếu hơn GĐ1/GĐ2.

## Ghi chú về `METRICS_DUNG`

Tệp này có sẵn một bản `metrics.py` để loại C có cái mà gọi. Nó **không phải sản phẩm
nộp của GĐ3** và cố ý viết vụng. Năm công thức ấy đã được QĐ-013 điểm 4 đặc tả bằng
lời tới từng ca biên, nên chép chúng ra code không phải chỗ lỗi ẩn náu — lỗi ẩn ở chỗ
*áp dụng*: lấy dòng nào, mẫu số tính trên tập nào, gộp thế nào. Những chỗ đó vẫn được
bảo vệ nguyên vẹn.
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
CHECKER = ROOT / "scripts" / "check_gd3.py"
REFERENCE = ROOT / "scripts" / "reference_gd3.py"

W = 2304
ENVS = ("E1", "E2", "E3")
HORIZONS = (1, 6, 12)
N_SERIES = 3

# Lệch seed cố định cho từng môi trường. KHÔNG dùng `hash(env)`: Python ngẫu nhiên hoá
# hash của str theo từng tiến trình (PYTHONHASHSEED), nên thế giới giả lập sẽ khác nhau
# mỗi lần chạy — một test đỏ sẽ không tái lập được để mà chẩn đoán.
LECH_SEED = {"E1": 0, "E2": 137, "E3": 291}

MATRIX_COLS = [
    "series_id", "bucket",
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24",
    "roll_mean_6", "roll_std_6", "roll_min_6", "roll_max_6",
    "roll_mean_12", "roll_std_12", "roll_min_12", "roll_max_12",
    "diff_1", "hour_sin", "hour_cos", "dow_sin", "dow_cos", "target",
]

METRICS_DUNG = '''"""Moi cho tests/test_check_gd3.py. KHONG phai san pham nop cua GD3."""
import numpy as np


def mae(y, yhat):
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(yhat, float))))


def rmse(y, yhat):
    return float(np.sqrt(np.mean(
        (np.asarray(y, float) - np.asarray(yhat, float)) ** 2)))


def smape(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    mau = (np.abs(y) + np.abs(yhat)) / 2.0
    t = np.where(mau > 0, np.abs(y - yhat) / np.where(mau > 0, mau, 1.0), 0.0)
    return float(100.0 * t.mean())


def mase(y, yhat, d):
    d = float(d)
    if not np.isfinite(d) or d <= 0:
        return float("nan")
    return mae(y, yhat) / d


def r2(y, yhat):
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    sstot = float(((y - y.mean()) ** 2).sum())
    if sstot <= 0:
        return float("nan")
    return 1.0 - float(((y - yhat) ** 2).sum()) / sstot
'''

# Hai biến thể hỏng, mỗi cái phá đúng một quy ước của QĐ-013 điểm 4.
METRICS_SMAPE_NAN = METRICS_DUNG.replace(
    "    t = np.where(mau > 0, np.abs(y - yhat) / np.where(mau > 0, mau, 1.0), 0.0)",
    "    with np.errstate(invalid='ignore', divide='ignore'):\n"
    "        t = np.abs(y - yhat) / mau")

METRICS_MASE_INF = METRICS_DUNG.replace(
    "    d = float(d)\n"
    "    if not np.isfinite(d) or d <= 0:\n"
    "        return float(\"nan\")\n"
    "    return mae(y, yhat) / d",
    "    return float(np.float64(mae(y, yhat)) / np.float64(d))")

assert METRICS_SMAPE_NAN != METRICS_DUNG and METRICS_MASE_INF != METRICS_DUNG


@pytest.fixture(scope="module")
def ref_mod():
    """Nạp `reference_gd3.py` như một module — nó là thước đo, dùng lại nguyên vẹn."""
    if not REFERENCE.exists():
        pytest.skip("chưa có scripts/reference_gd3.py")
    spec = importlib.util.spec_from_file_location("ref_gd3", REFERENCE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sinh_Y(env: str, seed: int = 42) -> np.ndarray:
    """Ba chuỗi tuần hoàn + nhiễu, NaN đặt có chủ đích.

    Hai ràng buộc khi chọn chỗ đặt NaN:

    - **Tránh xa hai ranh giới** 1612 và 1957 (ít nhất 24+12 bucket), để mọi dòng sát
      ranh giới đều hợp lệ. Có thế cận trên của B1 mới thực sự bị chạm, và kiểu phá
      "quên purge" mới lộ ra thành mất 0 dòng.
    - **Có một NaN rơi vào [1669, 2015]**, vì seasonal naive tại `t` đọc `y[t−288]` mà
      test là [1957, 2304). Không có nó thì `n_dong_dung == n_dong_test` ở cả ba
      baseline, và kiểu phá E (lấp giá trị thiếu) không tách ra khỏi bản đúng.
    """
    rng = np.random.default_rng(seed + LECH_SEED[env])
    t = np.arange(W)
    Y = np.empty((N_SERIES, W))
    for i in range(N_SERIES):
        Y[i] = 40 + 15 * np.sin(2 * np.pi * t / 288 + i) + rng.normal(0, 3, W)
    Y = np.clip(Y, 0, 100)

    Y[0, 700:706] = np.nan
    Y[1, 1500] = np.nan
    Y[2, 300:302] = np.nan
    Y[0, 1700] = np.nan          # -> seasonal naive vô định tại t = 1988 (trong test)
    Y[1, 2100] = np.nan
    return Y


def gop_B(ref, v: np.ndarray, kieu):
    """Gộp theo chuỗi. `kieu == "gop_trung_binh"` thay trung vị bằng trung bình."""
    r = ref.gop(v)
    if kieu == "gop_trung_binh":
        s = v[np.isfinite(v)]
        r = dict(r, p50=round(float(s.mean()), 6) if len(s) else None)
    return r


def mo_phong_B(ref, env: str, Y: np.ndarray, kieu=None):
    """Đường tính của 'B': từ Y sinh hai bảng đúng hợp đồng QĐ-014 điểm 4."""
    d = ref.mau_so_mase(Y)
    if kieu == "mase_tren_test":
        lo, hi = ref.RANH["test"]
        dd = np.abs(np.diff(Y[:, lo:hi], axis=1))
        ok = np.isfinite(dd)
        dem = ok.sum(axis=1)
        d = np.where(dem > 0,
                     np.where(ok, dd, 0.0).sum(axis=1) / np.maximum(dem, 1), np.nan)

    sp, bl = [], []
    t_all = np.arange(W)
    for h in HORIZONS:
        hop_le = ref.mat_na_hop_le(Y, h)
        du = ref.du_doan_baseline(Y, h)
        if kieu == "seasonal_ffill":
            s = du["seasonal"].copy()
            idx = np.where(np.isfinite(s), t_all[None, :], 0)
            np.maximum.accumulate(idx, axis=1, out=idx)
            du["seasonal"] = np.take_along_axis(s, idx, axis=1)

        y_that = np.full_like(Y, np.nan)
        y_that[:, : W - h] = Y[:, h:]

        for tap, (lo, hi) in ref.RANH.items():
            if kieu == "quen_purge":
                trong = (t_all >= lo) & (t_all < hi)          # bỏ điều kiện t+h
            else:
                trong = ((t_all >= lo) & (t_all < hi)
                         & (t_all + h >= lo) & (t_all + h < hi))
            m = hop_le & trong[None, :]
            sp.append({"env": env, "h": h, "split": tap, "n_dong": int(m.sum())})
            if tap != "test":
                continue

            co = int(m.sum())
            for ten, yhat in du.items():
                cs = ref.chi_so_theo_chuoi(y_that, yhat, m, d)
                dung = int((m & np.isfinite(yhat) & np.isfinite(y_that)).sum())
                for k, v in cs.items():
                    bl.append({"env": env, "h": h, "model": ten, "split": "test",
                               "metric": k, **gop_B(ref, v, kieu),
                               "n_dong_dung": dung, "n_dong_test": co})
    return sp, bl


def dung_the_gioi(ref, tmp: Path, kieu=None, metrics_src=METRICS_DUNG,
                  them_train_val=False):
    """Sinh trọn bộ: processed, catalog, cv, tham chiếu A, hai bảng B, đặc trưng, src."""
    proc, tab, feat = tmp / "processed", tmp / "tables", tmp / "features"
    src = tmp / "src"
    for d in (proc, tab, feat):
        d.mkdir(parents=True, exist_ok=True)

    cat_rows, cv_rows, Ys = [], [], {}
    for env in ENVS:
        Y = Ys[env] = sinh_Y(env)
        ids = [f"{env}_{i}" for i in range(N_SERIES)]
        pd.DataFrame({
            "series_id": np.repeat(ids, W),
            "bucket": np.tile(np.arange(W), N_SERIES),
            "y": Y.reshape(-1),
        }).to_parquet(proc / f"{env}.parquet", index=False)

        for i, sid in enumerate(ids):
            row = {"env": env, "series_id": sid, "kept": True}
            for h in HORIZONS:
                row[f"valid_rows_h{h}"] = int(ref.mat_na_hop_le(Y, h)[i].sum())
            cat_rows.append(row)
            cv_rows.append({"env": env, "series_id": sid,
                            "cv": float(np.nanstd(Y[i], ddof=1) / np.nanmean(Y[i]))})

    cat_path = tmp / "catalog.parquet"
    cat = pd.DataFrame(cat_rows)
    cat.to_parquet(cat_path, index=False)
    cv = pd.DataFrame(cv_rows)
    cv.to_csv(tab / "cv_gd2.csv", index=False)

    # Tham chiếu của A: luôn sinh từ bản ĐÚNG, y như vai trò của nó ở GĐ1/GĐ2.
    (tab / "reference_gd3.json").write_text(
        json.dumps([ref.mot_moi_truong(e, proc, cat, cv) for e in ENVS],
                   ensure_ascii=False, indent=2), encoding="utf-8")

    sp, bl = [], []
    for env in ENVS:
        a, b = mo_phong_B(ref, env, Ys[env], kieu)
        sp += a
        bl += b
    if them_train_val:
        # B được phép báo thêm train/val để tự theo dõi — checker phải lọc, không lẫn.
        #
        # Chép nguyên giá trị chứ không bịa số khác: B4 (R² ≤ 1) và B5 (p25 ≤ p50 ≤
        # p75) quét MỌI split, và quét thế là đúng — hai bất đẳng thức ấy phải giữ ở
        # bất kỳ tập nào. Bịa số ở đây sẽ làm chúng đỏ và che mất thứ cần đo.
        for r in list(bl):
            for tap in ("train", "val"):
                bl.append(dict(r, split=tap))
    pd.DataFrame(sp).to_csv(tab / "splits_gd3.csv", index=False)
    pd.DataFrame(bl).to_csv(tab / "baselines_gd3.csv", index=False)

    # Ma trận đặc trưng: chỉ cần đúng schema, B7 đọc schema chứ không đọc dữ liệu.
    khung = pd.DataFrame({c: (["s"] * 2 if c == "series_id" else [0.0, 1.0])
                          for c in MATRIX_COLS})
    for env in ENVS:
        for h in HORIZONS:
            khung.to_parquet(feat / f"{env}_h{h}.parquet", index=False)

    (src / "cwp" / "evaluation").mkdir(parents=True, exist_ok=True)
    (src / "cwp" / "__init__.py").write_text("", encoding="utf-8")
    (src / "cwp" / "evaluation" / "__init__.py").write_text("", encoding="utf-8")
    (src / "cwp" / "evaluation" / "metrics.py").write_text(metrics_src, encoding="utf-8")

    return tab, cat_path, feat, src


def chay_checker(tab, cat_path, feat, src):
    r = subprocess.run(
        [sys.executable, str(CHECKER), "--tables", str(tab), "--catalog", str(cat_path),
         "--features", str(feat), "--src", str(src)],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ================================================================ A. đúng hết

def test_the_gioi_dung_thi_dat(ref_mod, tmp_path):
    """Không lỗi nào thì phải ĐẠT. Mục này đỏ là mọi mục dưới vô nghĩa."""
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path))
    assert rc == 0, f"thế giới đúng mà checker báo trượt:\n{out}"
    assert "ĐẠT" in out


def test_bao_them_train_val_van_dat(ref_mod, tmp_path):
    """Cột `split` có trong hợp đồng: B báo thêm train/val không được làm checker rối.

    Không lọc theo split thì mỗi tổ hợp có ba dòng và checker báo nhầm "thiếu dòng" —
    một cách trượt oan rất khó chẩn đoán.
    """
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path, them_train_val=True))
    assert rc == 0, f"dòng train/val phụ làm checker trượt oan:\n{out}"


# ========================================================== B–I. các kiểu phá

def test_quen_purge_thi_truot(ref_mod, tmp_path):
    """QĐ-013 điểm 2: dòng vắt ranh giới phải bị loại. Quên là RÒ RỈ."""
    tab, cat, feat, src = dung_the_gioi(ref_mod, tmp_path, kieu="quen_purge")
    sp = pd.read_csv(tab / "splits_gd3.csv")
    ref = json.loads((tab / "reference_gd3.json").read_text(encoding="utf-8"))
    tong_B = int(sp[(sp.env == "E1") & (sp.h == 12)]["n_dong"].sum())
    tong_A = sum(ref[0]["so_dong"]["h12"][k] for k in ("train", "val", "test"))
    assert tong_B > tong_A, "thế giới giả lập chưa tách được hai luật gán tập"

    rc, out = chay_checker(tab, cat, feat, src)
    assert rc == 1, f"quên purge mà checker vẫn cho qua:\n{out}"
    assert "purge" in out and "RÒ RỈ" in out


def test_mau_so_mase_tinh_tren_test_thi_truot(ref_mod, tmp_path):
    """QĐ-013 điểm 3: mẫu số MASE lấy trên **train**. Lấy trên test là nhìn trộm."""
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path, kieu="mase_tren_test"))
    assert rc == 1, f"mẫu số MASE sai tập mà checker vẫn cho qua:\n{out}"
    assert "mase" in out


def test_gop_bang_trung_binh_thi_truot(ref_mod, tmp_path):
    """QĐ-013 điểm 5: gộp bằng trung vị theo chuỗi, không phải trung bình."""
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path, kieu="gop_trung_binh"))
    assert rc == 1, f"gộp bằng trung bình mà checker vẫn cho qua:\n{out}"
    assert "45 chỉ số p50" in out


def test_seasonal_lap_gia_tri_thieu_thi_truot(ref_mod, tmp_path):
    """Kiểu hiểm nhất: lấp `y_{t−288}` thiếu làm seasonal naive đẹp lên trong im lặng.

    Số dòng không đổi, chỉ số vẫn nằm trong mọi khoảng hợp lệ. Chỉ `n_dong_dung` lộ.
    """
    tab, cat, feat, src = dung_the_gioi(ref_mod, tmp_path, kieu="seasonal_ffill")
    bl = pd.read_csv(tab / "baselines_gd3.csv")
    r = bl[(bl.env == "E1") & (bl.h == 1) & (bl.model == "seasonal")
           & (bl.metric == "mae")].iloc[0]
    assert r["n_dong_dung"] == r["n_dong_test"], "kiểu phá chưa thực sự lấp hết"

    rc, out = chay_checker(tab, cat, feat, src)
    assert rc == 1, f"lấp giá trị thiếu mà checker vẫn cho qua:\n{out}"
    assert "lặng lẽ lấp" in out


def test_them_dac_trung_ngoai_muc_8_thi_truot(ref_mod, tmp_path):
    """Thêm một cột vào ma trận đặc trưng là đổi giao thức — B không được đổi."""
    tab, cat, feat, src = dung_the_gioi(ref_mod, tmp_path)
    f = feat / "E1_h1.parquet"
    df = pd.read_parquet(f)
    df["lag_48"] = df["lag_24"]
    df.to_parquet(f, index=False)

    rc, out = chay_checker(tab, cat, feat, src)
    assert rc == 1, f"đặc trưng thừa mà checker vẫn cho qua:\n{out}"
    assert "lag_48" in out and "ĐỔI GIAO THỨC" in out


def test_rmse_nho_hon_mae_thi_truot(ref_mod, tmp_path):
    """B2: bất đẳng thức Jensen. Số nào phá được nó là số bịa, không cần tham chiếu."""
    tab, cat, feat, src = dung_the_gioi(ref_mod, tmp_path)
    f = tab / "baselines_gd3.csv"
    bl = pd.read_csv(f)
    sel = (bl.env == "E2") & (bl.h == 6) & (bl.model == "naive") & (bl.metric == "rmse")
    bl.loc[sel, ["p25", "p50", "p75"]] = 0.001
    bl.to_csv(f, index=False)

    rc, out = chay_checker(tab, cat, feat, src)
    assert rc == 1, f"RMSE < MAE mà checker vẫn cho qua:\n{out}"
    assert "B2" in out


def test_smape_khong_xu_ly_0_tren_0_thi_truot(ref_mod, tmp_path):
    """Loại C: `0/0` trong SMAPE phải tính là 0 (QĐ-013 điểm 4), không phải NaN.

    Phép kiểm này không quan tâm hai bản có khớp nhau không — đó là điểm mấu chốt khi
    tính độc lập yếu đi (QĐ-014 điểm 3).
    """
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path,
                                          metrics_src=METRICS_SMAPE_NAN))
    assert rc == 1, f"SMAPE(0,0) trả NaN mà checker vẫn cho qua:\n{out}"
    assert "SMAPE khi y = ŷ = 0" in out


def test_mase_chia_cho_0_ra_vo_cuc_thi_truot(ref_mod, tmp_path):
    """Loại C: `d = 0` phải cho NaN (loại chuỗi), không phải `inf`.

    `inf` là bẫy riêng: nó cũng không hữu hạn, nên phép kiểm viết bằng `isfinite` sẽ
    cho qua — rồi `inf` trôi vào trung vị và bôi đen cả cột.
    """
    rc, out = chay_checker(*dung_the_gioi(ref_mod, tmp_path,
                                          metrics_src=METRICS_MASE_INF))
    assert rc == 1, f"MASE trả inf mà checker vẫn cho qua:\n{out}"
    assert "MASE khi d = 0" in out and "inf" in out


# ============================================== trạng thái B chưa làm xong

def test_chua_co_bang_thi_bao_thieu_khong_no(ref_mod, tmp_path):
    """B chưa làm là trạng thái bình thường: báo thiếu, in tiến độ, không đổ vỡ."""
    tab, cat, feat, src = dung_the_gioi(ref_mod, tmp_path)
    for n in ("splits_gd3.csv", "baselines_gd3.csv"):
        (tab / n).unlink()
    rc, out = chay_checker(tab, cat, feat, src)
    assert rc == 1
    assert "BÌNH THƯỜNG" in out
    assert "TIẾN ĐỘ GĐ3" in out


def test_chua_co_metrics_thi_chi_canh_bao_khi_chua_nop_bang(ref_mod, tmp_path):
    """Thiếu `metrics.py` lúc B chưa nộp bảng là đang làm dở, không phải trượt.

    Nộp bảng rồi mà vẫn thiếu module thì ngược lại: bảng phải sinh ra từ chính module
    đó, nên thiếu là trượt thật.
    """
    tab, cat, feat, src = dung_the_gioi(ref_mod, tmp_path)
    (src / "cwp" / "evaluation" / "metrics.py").unlink()

    rc_co_bang, out_co_bang = chay_checker(tab, cat, feat, src)
    assert rc_co_bang == 1 and "TRƯỢT] import được" in out_co_bang, out_co_bang

    for n in ("splits_gd3.csv", "baselines_gd3.csv"):
        (tab / n).unlink()
    rc, out = chay_checker(tab, cat, feat, src)
    assert "cảnh báo] import được" in out, out
    assert "BÌNH THƯỜNG" in out
