"""Test của chính `scripts/check_gd4.py` — bài học số 2 của `gate-gd4.md` mục 0.

Chạy:  pytest tests/test_check_gd4.py -v

Công cụ kiểm mà không có test của chính nó thì không ai biết nó **biết đỏ** hay không.
`check_gd1.py`, `check_gd2.py`, `check_gd3.py` đều có tệp tương đương; đây là tệp của
GĐ4.

Cách làm: dựng một **thế giới giả lập** hoàn chỉnh trong `tmp_path` — cây nguồn có
`cwp/preprocess/normalize.py`, tham chiếu, catalog, 27 ma trận đặc trưng, ba bảng của
B — rồi **phá mười sáu kiểu** và xác nhận công cụ bắt được từng kiểu.

Thế giới giả lập cố ý dùng số **nhỏ** (100 dòng mỗi tổ hợp thay vì 1,6 triệu): công cụ
chỉ đọc `metadata.num_rows` và các bảng CSV, nên kích thước thật không cần thiết, còn
test thì chạy trong vài giây.

> **Bản mồi đã được tách ra khỏi `tests/` — 2026-09-11.** Loại C cần một bản
> `normalize.py` đúng để gọi trong thế giới giả lập. Ở GĐ3, bản mồi tương đương nằm
> ngay trong `tests/test_check_gd3.py`, và QĐ-014 ghi lại điểm yếu đó kèm cách sửa:
> *"nếu sau này muốn siết, đưa bản mồi ấy ra một tệp riêng ngoài tests/"*.
>
> GĐ4 siết, vì ở đây bản mồi là **trọn vẹn** thứ mà phiên hiện thực phải tự viết. Nó
> nằm ở `scripts/_moi_normalize_gd4.py`, có banner cảnh báo, và có tên trong danh sách
> "không được đọc" ở `brief-gd4-b.md` Bước 0.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_gd4.py"

ENVS = ["E1", "E2", "E3"]
MODES = ["N0", "N1", "N2"]
HORIZONS = [1, 6, 12]
LICH = ["co", "khong"]
CAP = [("E1", "E2"), ("E2", "E1"), ("E1", "E3"),
       ("E3", "E1"), ("E2", "E3"), ("E3", "E2")]
BASELINE = ["naive", "ma6", "seasonal"]
ML = ["lr", "xgb"]
METRICS = ["mae", "rmse", "smape", "mase", "r2"]

N_CHUOI = {"E1": 4, "E2": 3, "E3": 5}
NEO = 100           # số dòng hợp lệ mỗi (env, h), dùng chung cho gọn
MAT_N2_E3 = 2       # E3 mất 2 dòng ở N2 vì sai phân chạm lỗ hổng


# ------------------------------------------------------------ bản mồi normalize

# Bản mồi cho loại C nằm ở `scripts/_moi_normalize_gd4.py` — ngoài `tests/` có
# chủ ý, xem banner trong tệp đó và QĐ-014.
MOI_NORMALIZE = (ROOT / "scripts" / "_moi_normalize_gd4.py").read_text(
    encoding="utf-8")


# ------------------------------------------------------------- dựng thế giới

def _viet_nguon(goc: Path, noi_dung: str = MOI_NORMALIZE) -> None:
    d = goc / "cwp" / "preprocess"
    d.mkdir(parents=True, exist_ok=True)
    (goc / "cwp" / "__init__.py").write_text("", encoding="utf-8")
    (d / "__init__.py").write_text("", encoding="utf-8")
    (d / "normalize.py").write_text(noi_dung, encoding="utf-8")


def _viet_features(feat: Path) -> None:
    feat.mkdir(parents=True, exist_ok=True)
    for env in ENVS:
        for mode in MODES:
            for h in HORIZONS:
                n = NEO
                if mode == "N2" and env == "E3":
                    n -= MAT_N2_E3
                pd.DataFrame({"x": np.zeros(n)}).to_parquet(
                    feat / f"{env}_{mode}_h{h}.parquet", index=False)


def _viet_catalog(p: Path) -> None:
    dong = []
    for env, n in N_CHUOI.items():
        for i in range(n):
            dong.append({"env": env, "series_id": f"{env}_{i}", "kept": True,
                         **{f"valid_rows_h{h}": NEO // n + (i < NEO % n)
                            for h in HORIZONS}})
    pd.DataFrame(dong).to_parquet(p, index=False)


def _tham_chieu(p: Path) -> None:
    mt = []
    for env in ENVS:
        so_dong = {}
        for mode in MODES:
            n = NEO - (MAT_N2_E3 if (mode == "N2" and env == "E3") else 0)
            so_dong[mode] = {f"h{h}": {"train": n - 30, "val": 15, "test": 15}
                             for h in HORIZONS}
        mt.append({
            "env": env, "n_chuoi": N_CHUOI[env], "n_bucket": 2304,
            "n1": {"mu_p50": 10.0, "sd_p50": 2.0, "n_chuoi_sd_bang_0": 0},
            "so_dong": so_dong,
            "bat_bien": {"naive_N0_vs_N1": 1e-14, "ma6_N0_vs_N1": 1e-14,
                         "naive_N0_vs_N2": 0.0},
        })
    p.write_text(json.dumps({"moi_truong": mt, "moc_hang_so": []},
                            ensure_ascii=False), encoding="utf-8")


def _bang_normalize() -> pd.DataFrame:
    dong = []
    for env, n in N_CHUOI.items():
        # mu, sd đối xứng quanh 10,0 và 2,0 để trung vị khớp tham chiếu.
        lech = np.linspace(-1, 1, n)
        for i in range(n):
            for mode in MODES:
                dong.append({"env": env, "mode": mode, "series_id": f"{env}_{i}",
                             "mu": 10.0 + lech[i], "sd": 2.0 + lech[i] / 10,
                             "n_dong_train": 1612})
    return pd.DataFrame(dong)


def _bang_invariants() -> pd.DataFrame:
    dong = []
    for env in ENVS:
        for ten, v in (("naive_N0_vs_N1", 1e-14), ("ma6_N0_vs_N1", 1e-14),
                       ("naive_N0_vs_N2", 0.0)):
            dong.append({"env": env, "bat_bien": ten, "lech_toi_da": v,
                         "nguong": 1e-9 if v else 0.0, "dat": True})
    return pd.DataFrame(dong)


def _bang_transfer() -> pd.DataFrame:
    dong = []
    for nguon, dich in CAP:
        for mode in MODES:
            for lich in LICH:
                for h in HORIZONS:
                    for model in BASELINE + ML:
                        # Baseline giống nhau ở cả ba chế độ (QĐ-016 điểm 4);
                        # model ML thì đổi theo chế độ.
                        lech = (float(BASELINE.index(model)) if model in BASELINE
                                else 0.1 * MODES.index(mode))
                        for me in METRICS:
                            goc = {"mae": 1.0, "rmse": 2.0, "smape": 20.0,
                                   "mase": 1.1, "r2": 0.3}[me]
                            # R² phải ở lại dưới 1 — B7 sẽ bắt nếu fixture sai.
                            p50 = goc - 0.05 * lech if me == "r2" else goc + lech
                            dong.append({
                                "nguon": nguon, "dich": dich, "mode": mode,
                                "lich": lich, "h": h, "model": model, "metric": me,
                                "p25": p50 - 0.5, "p50": p50, "p75": p50 + 0.5,
                                "iqr": 1.0, "n_chuoi": N_CHUOI[dich],
                                "n_loai": 0, "n_dong_test": 15,
                            })
    return pd.DataFrame(dong)


@pytest.fixture
def the_gioi(tmp_path):
    """Thế giới giả lập ĐÚNG. Mọi ca phá đều xuất phát từ đây."""
    tab = tmp_path / "tables"
    feat = tmp_path / "features"
    src = tmp_path / "src"
    tab.mkdir()
    _viet_nguon(src)
    _viet_features(feat)
    _viet_catalog(tmp_path / "catalog.parquet")
    _tham_chieu(tab / "reference_gd4.json")
    _bang_normalize().to_csv(tab / "normalize_gd4.csv", index=False)
    _bang_invariants().to_csv(tab / "invariants_gd4.csv", index=False)
    _bang_transfer().to_csv(tab / "transfer_gd4.csv", index=False)
    return {"goc": tmp_path, "tab": tab, "feat": feat, "src": src}


def chay(tg) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(CHECKER),
         "--tables", str(tg["tab"]),
         "--catalog", str(tg["goc"] / "catalog.parquet"),
         "--features", str(tg["feat"]),
         "--src", str(tg["src"])],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.returncode, r.stdout + r.stderr


# ------------------------------------------------------------------ hai ca XANH

def test_the_gioi_dung_thi_DAT(the_gioi):
    ma, out = chay(the_gioi)
    assert ma == 0, f"thế giới đúng mà công cụ báo trượt:\n{out}"
    assert "ĐẠT" in out


def test_bang_transfer_co_them_model_la_van_DAT(the_gioi):
    """B được phép báo thêm model ngoài bộ bắt buộc — công cụ không được báo oan."""
    p = the_gioi["tab"] / "transfer_gd4.csv"
    tr = pd.read_csv(p)
    them = tr[tr["model"] == "lr"].copy()
    them["model"] = "lstm"
    pd.concat([tr, them], ignore_index=True).to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma == 0, f"thêm model mà báo trượt:\n{out}"


# ---------------------------------------------------- phá LOẠI C — normalize.py

def _pha_nguon(tg, tim: str, thay: str):
    p = tg["src"] / "cwp" / "preprocess" / "normalize.py"
    s = p.read_text(encoding="utf-8")
    assert tim in s, "vết phá đã cũ so với bản mồi"
    p.write_text(s.replace(tim, thay, 1), encoding="utf-8")


def test_pha_mu_sd_tren_toan_chuoi_thi_C2_do(the_gioi):
    """Kiểu nguy hiểm nhất của GĐ4: nó **làm số đẹp lên**, không báo lỗi."""
    _pha_nguon(the_gioi, 'tr = np.asarray(y, dtype="float64")[:N_TRAIN]',
               'tr = np.asarray(y, dtype="float64")')
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "C2" in out and "KHÔNG đổi" in out


def test_pha_quen_map_nguoc_thi_C3_do(the_gioi):
    _pha_nguon(the_gioi, "        return yhat * sd + mu", "        return yhat")
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "C3" in out


def test_pha_chuoi_phang_tra_0_thay_vi_NaN_thi_C6_do(the_gioi):
    _pha_nguon(the_gioi, "            return np.full_like(y, np.nan)",
               "            return np.zeros_like(y)")
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "C6" in out


def test_pha_N2_bac_cau_qua_diem_dau_thi_C7_do(the_gioi):
    _pha_nguon(the_gioi, "    d = np.full_like(y, np.nan)\n        d[1:]",
               "    d = np.zeros_like(y)\n        d[1:]")
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "C7" in out


def test_thieu_module_normalize_thi_bao_TRUOT_khi_B_da_nop(the_gioi):
    (the_gioi["src"] / "cwp" / "preprocess" / "normalize.py").unlink()
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "import được" in out


# ------------------------------------------------------ phá LOẠI A và LOẠI B

def test_pha_N1_lech_N0_thi_B2_do(the_gioi):
    """z-score không được sinh thêm NaN khi `sd > 0`."""
    pd.DataFrame({"x": np.zeros(NEO - 7)}).to_parquet(
        the_gioi["feat"] / "E1_N1_h6.parquet", index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "B2" in out


def test_pha_N0_lech_neo_catalog_thi_B1_do(the_gioi):
    """Thêm chế độ mà đổi cả số dòng N0 nghĩa là đường sinh đặc trưng đã đổi."""
    for mode in MODES:
        pd.DataFrame({"x": np.zeros(NEO + 5)}).to_parquet(
            the_gioi["feat"] / f"E2_{mode}_h1.parquet", index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "B1" in out


def test_pha_N2_mat_dong_o_E1_thi_B3_do(the_gioi):
    """E1 mất dòng ở N2 nghĩa là sai phân bắc cầu qua ranh giới chuỗi."""
    pd.DataFrame({"x": np.zeros(NEO - 3)}).to_parquet(
        the_gioi["feat"] / "E1_N2_h1.parquet", index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "B3" in out


def test_pha_baseline_khac_nhau_giua_ba_che_do_thi_B10_do(the_gioi):
    """QĐ-016 điểm 4: baseline là mốc cố định của đích, không đổi theo chế độ."""
    p = the_gioi["tab"] / "transfer_gd4.csv"
    tr = pd.read_csv(p)
    m = (tr["model"] == "naive") & (tr["mode"] == "N1")
    tr.loc[m, "p50"] = tr.loc[m, "p50"] + 0.3
    tr.to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "B10" in out


def test_pha_thieu_to_hop_thi_B4_do(the_gioi):
    p = the_gioi["tab"] / "transfer_gd4.csv"
    tr = pd.read_csv(p)
    tr[~((tr["mode"] == "N2") & (tr["lich"] == "khong"))].to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "B4" in out


def test_pha_rmse_nho_hon_mae_thi_B5_do(the_gioi):
    p = the_gioi["tab"] / "transfer_gd4.csv"
    tr = pd.read_csv(p)
    tr.loc[tr["metric"] == "rmse", "p50"] = 0.01
    tr.to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "B5" in out


def test_pha_bat_bien_vuot_nguong_thi_loai_A_do(the_gioi):
    p = the_gioi["tab"] / "invariants_gd4.csv"
    iv = pd.read_csv(p)
    iv.loc[iv["bat_bien"] == "ma6_N0_vs_N1", "lech_toi_da"] = 1e-3
    iv.to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "ba bất biến" in out


def test_pha_bat_bien_N2_khac_0_thi_loai_A_do(the_gioi):
    """`naive` dưới N2 phải bằng 0 **tuyệt đối** — `y_t + 0` không mất bit nào."""
    p = the_gioi["tab"] / "invariants_gd4.csv"
    iv = pd.read_csv(p)
    iv.loc[iv["bat_bien"] == "naive_N0_vs_N2", "lech_toi_da"] = 1e-15
    iv.to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0


def test_pha_thong_ke_N1_lech_tham_chieu_thi_loai_A_do(the_gioi):
    p = the_gioi["tab"] / "normalize_gd4.csv"
    nz = pd.read_csv(p)
    nz.loc[nz["mode"] == "N1", "sd"] = nz.loc[nz["mode"] == "N1", "sd"] * 1.5
    nz.to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "sd" in out


def test_pha_co_chuoi_sd_bang_0_thi_loai_A_do(the_gioi):
    """Tham chiếu nói 0 chuỗi `sd = 0`; có chuỗi nào bằng 0 là tính sai cửa sổ."""
    p = the_gioi["tab"] / "normalize_gd4.csv"
    nz = pd.read_csv(p)
    i = nz.index[(nz["env"] == "E1") & (nz["mode"] == "N1")][0]
    nz.loc[i, "sd"] = 0.0
    nz.to_csv(p, index=False)
    ma, out = chay(the_gioi)
    assert ma != 0


# ------------------------------------------------- trạng thái B chưa bắt đầu

def test_B_chua_bat_dau_thi_bao_thieu_chu_khong_do_vo(the_gioi):
    for ten in ("normalize_gd4.csv", "invariants_gd4.csv", "transfer_gd4.csv"):
        (the_gioi["tab"] / ten).unlink()
    ma, out = chay(the_gioi)
    assert ma != 0
    assert "Traceback" not in out
    assert "TIẾN ĐỘ GĐ4" in out
    assert "BÌNH THƯỜNG" in out
