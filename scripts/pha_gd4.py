"""GĐ4 Bước 3 — phá code kiểm ngược, trên DỮ LIỆU THẬT.

    python scripts/pha_gd4.py

Test xanh mà không chứng minh được nó biết đỏ thì chưa phải test. `pha_features.py`
và `pha_gd3.py` đã làm việc này cho GĐ2 và GĐ3; đây là bản của GĐ4.

**Hai lớp phá, vì GĐ4 có hai loại lỗi khác nhau.**

| Lớp | Phá gì | Ai phải bắt |
|---|---|---|
| **Q** — mã nguồn | `normalize.py`, `run_normalize_gd4.py` | `tests/test_normalize.py`, loại C, bất biến |
| **R** — ma trận | sinh lại `data/features/` bằng phép biến đổi hỏng | loại B của `check_gd4.py` |

Năm bản phá **Q1–Q5** là danh sách bắt buộc ở `brief-gd4-b.md` Bước 3. Ba bản
**R1–R3** là bổ sung: chúng là những lỗi N2 thật sự có thể xảy ra, và chính R1 đã lộ
ra rằng phép kiểm B3 bản đầu **thưởng cho đúng cái lỗi nó định bắt**.

Mỗi bản phá bị coi là *bị bắt* khi làm trượt thêm ít nhất một phép kiểm **mới** so với
vết nền — chặt hơn "đỏ là đạt", vì một bản phá chỉ tái hiện vết nền cũ thì không
chứng minh được gì.

Mọi thứ được khôi phục trong `finally`. Bảng thật và `data/features/` **không bị đụng
tới** sau khi chạy xong.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cwp.features import make_feature_matrix  # noqa: E402
from cwp.preprocess.normalize import bien_doi as bien_doi_chuan  # noqa: E402

ENVS = ("E1", "E2", "E3")
FEAT = ROOT / "data" / "features"
CHECKER = ROOT / "scripts" / "check_gd4.py"
NORMALIZE = ROOT / "src" / "cwp" / "preprocess" / "normalize.py"
HARNESS = ROOT / "scripts" / "run_normalize_gd4.py"
TABLES = ROOT / "results" / "tables"
H = 1                    # phá ở h=1 cho nhanh; các lỗi này không phụ thuộc horizon
CAL = ("hour_sin", "hour_cos", "dow_sin", "dow_cos")


# ============================================================ lớp Q — mã nguồn

@dataclass
class PhaNguon:
    ma: str
    ten: str
    tep: Path
    tim: str
    thay: str
    sinh_lai_bang: bool = False     # chạy lại run_normalize_gd4.py sau khi phá


Q = [
    PhaNguon(
        "Q1", "mu/sd tính trên TOÀN chuỗi thay vì cửa sổ train (RÒ RỈ)",
        NORMALIZE,
        "    a = _mang(y)[:TRAIN_END]",
        "    a = _mang(y)",
        sinh_lai_bang=True,
    ),
    PhaNguon(
        "Q2", "quên map ngược trước khi tính chỉ số",
        NORMALIZE,
        "        return h * sd + mu",
        "        return h.copy()",
        sinh_lai_bang=True,
    ),
    PhaNguon(
        "Q3", "áp mu/sd của chuỗi khác lên chuỗi đang xét",
        NORMALIZE,
        "    if m == \"N1\":\n        mu, sd = thong_ke_train(a)\n"
        "        if not np.isfinite(sd) or sd == 0.0:",
        "    if m == \"N1\":\n        mu, sd = thong_ke_train(np.roll(a, 137))\n"
        "        if not np.isfinite(sd) or sd == 0.0:",
        sinh_lai_bang=True,
    ),
    PhaNguon(
        "Q4", "naive ở N2 dùng Δ̂ = Δ_t thay vì 0",
        HARNESS,
        "    n2 = np.vstack([map_nguoc(np.zeros(W), Y[i], \"N2\") for i in range(n)])",
        "    n2 = np.vstack([map_nguoc(bien_doi(Y[i], \"N2\"), Y[i], \"N2\")\n"
        "                    for i in range(n)])",
        sinh_lai_bang=True,
    ),
]


# =========================================================== lớp R — ma trận

def r1_n2_bac_cau(Y):
    """N2 sai phân **vắt qua ranh giới chuỗi** — thiếu `groupby(series_id)`."""
    phang = Y.reshape(-1)
    d = np.full(phang.shape, np.nan)
    d[1:] = phang[1:] - phang[:-1]
    return d.reshape(Y.shape)


def r2_n2_sai_phan_tien(Y):
    """N2 dùng `y_{t+1} − y_t` thay vì `y_t − y_{t−1}` — **RÒ RỈ TƯƠNG LAI**."""
    out = np.full(Y.shape, np.nan)
    out[:, :-1] = Y[:, 1:] - Y[:, :-1]
    return out


def r3_n2_lap_diem_dau(Y):
    """N2 lấp điểm đầu bằng 0 thay vì để NaN — QĐ-016 cấm lấp."""
    out = np.full(Y.shape, np.nan)
    out[:, 1:] = Y[:, 1:] - Y[:, :-1]
    out[:, 0] = 0.0
    return out


@dataclass
class PhaMaTran:
    ma: str
    ten: str
    mode: str
    bien_doi: Callable | None = None      # phá cột y trước khi sinh đặc trưng
    sau_khi_sinh: Callable | None = None  # phá thẳng ma trận đã sinh


def q5_chuan_hoa_ca_lich(X: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá luôn 4 đặc trưng lịch — QĐ-016 điểm 2 nói phải GIỮ NGUYÊN.

    Chúng đã nằm trong `[−1, 1]` và không mang thang tải; z-score hoá chúng là bịa
    thêm một phép biến đổi mà giao thức không có.
    """
    X = X.copy()
    for c in CAL:
        m, s = X[c].mean(), X[c].std(ddof=1)
        X[c] = (X[c] - m) / s if s > 0 else X[c]
    return X


R = [
    PhaMaTran("Q5", "chuẩn hoá cả 4 đặc trưng lịch", "N1", sau_khi_sinh=q5_chuan_hoa_ca_lich),
    PhaMaTran("R1", "N2 bắc cầu qua ranh giới chuỗi", "N2", bien_doi=r1_n2_bac_cau),
    PhaMaTran("R2", "N2 sai phân TIẾN (rò rỉ tương lai)", "N2", bien_doi=r2_n2_sai_phan_tien),
    PhaMaTran("R3", "N2 lấp điểm đầu bằng 0", "N2", bien_doi=r3_n2_lap_diem_dau),
]


# ------------------------------------------------------------------- chạy

def nap(env: str):
    d = pd.read_parquet(ROOT / "data" / "processed" / f"{env}.parquet")
    d = d.sort_values(["series_id", "bucket"], kind="mergesort").reset_index(drop=True)
    n = d["series_id"].nunique()
    return d, d["y"].to_numpy(dtype="float64").reshape(n, len(d) // n)


def chay(lenh: list[str]) -> tuple[int, str]:
    r = subprocess.run(lenh, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(ROOT))
    return r.returncode, r.stdout + r.stderr


def nhan_truot() -> set[str]:
    """Tập nhãn các phép kiểm của `check_gd4.py` đang TRƯỢT."""
    _, out = chay([sys.executable, str(CHECKER)])
    return {d.split("]", 1)[1].strip() for d in out.splitlines() if "TRƯỢT]" in d}


def test_normalize_do() -> bool:
    ma, _ = chay([sys.executable, "-m", "pytest", "tests/test_normalize.py", "-q"])
    return ma != 0


def main() -> int:
    if not FEAT.exists():
        raise SystemExit("Chưa có data/features/. Chạy build_features.py --modes trước.")

    print("\nGĐ4 Bước 3 — phá code kiểm ngược trên dữ liệu thật\n")
    nen = nhan_truot()
    print(f"Vết nền: {len(nen)} phép kiểm trượt sẵn"
          + (f" — {sorted(nen)}" if nen else ""))
    print("Mỗi bản phá phải làm trượt thêm ít nhất một phép kiểm MỚI, "
          "hoặc làm đỏ tests/test_normalize.py.\n")

    tmp = Path(tempfile.mkdtemp(prefix="pha_gd4_"))
    ket: list[tuple[str, str, bool, list[str]]] = []
    try:
        # ---------------- lớp Q: phá mã nguồn
        for p in Q:
            goc = p.tep.read_text(encoding="utf-8")
            if p.tim not in goc:
                print(f"  [BỎ QUA] {p.ma} — không tìm thấy neo trong {p.tep.name}")
                continue
            bang_goc = {}
            try:
                p.tep.write_text(goc.replace(p.tim, p.thay, 1), encoding="utf-8")
                if p.sinh_lai_bang:
                    for t in ("invariants_gd4.csv", "normalize_gd4.csv"):
                        shutil.copy2(TABLES / t, tmp / t)
                        bang_goc[t] = TABLES / t
                    chay([sys.executable, str(HARNESS)])
                bat = []
                if test_normalize_do():
                    bat.append("tests/test_normalize.py")
                bat += sorted(nhan_truot() - nen)
            finally:
                p.tep.write_text(goc, encoding="utf-8")
                for t, dich in bang_goc.items():
                    shutil.copy2(tmp / t, dich)
            ket.append((p.ma, p.ten, bool(bat), bat))

        # ---------------- lớp R: phá ma trận đặc trưng
        for m in R:
            goc_files = {}
            try:
                for env in ENVS:
                    f = FEAT / f"{env}_{m.mode}_h{H}.parquet"
                    shutil.copy2(f, tmp / f.name)
                    goc_files[env] = f
                    d, Y = nap(env)
                    # Áp ĐÚNG phép biến đổi của chế độ trước, rồi mới phá — nếu không
                    # thì bản phá vô tình thành "quên áp chế độ", tức đo nhầm thứ.
                    if m.bien_doi is not None:
                        d = d.copy()
                        d["y"] = m.bien_doi(Y).reshape(-1)
                    elif m.mode != "N0":
                        d = d.copy()
                        d["y"] = np.vstack(
                            [bien_doi_chuan(Y[i], m.mode) for i in range(Y.shape[0])]
                        ).reshape(-1)
                    X = make_feature_matrix(d, h=H)
                    if m.sau_khi_sinh is not None:
                        X = m.sau_khi_sinh(X)
                    X.to_parquet(f, index=False)
                bat = sorted(nhan_truot() - nen)
            finally:
                for env, f in goc_files.items():
                    shutil.copy2(tmp / f.name, f)
            ket.append((m.ma, m.ten, bool(bat), bat))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for ma, ten, bi_bat, bat in ket:
        print(f"  [{'BỊ BẮT' if bi_bat else 'LỌT!!'}] {ma} {ten}")
        for b in bat:
            print(f"           ↳ {b[:94]}")
        if not bat:
            print("           ↳ không phép kiểm nào mới trượt")

    sau = nhan_truot()
    print(f"\nKhôi phục: {'nguyên trạng' if sau == nen else 'LỆCH vết nền — kiểm tay!'}")

    lot = [f"{ma} {ten}" for ma, ten, b, _ in ket if not b]
    print("\n" + "=" * 70)
    if not lot and sau == nen:
        print(f"ĐẠT — cả {len(ket)} bản phá đều bị bắt, mã nguồn và dữ liệu về nguyên trạng.")
    else:
        print(f"CHƯA ĐẠT — {len(lot)} bản phá LỌT:")
        for x in lot:
            print(f"  · {x}")
    print("=" * 70)
    return 0 if (not lot and sau == nen) else 1


if __name__ == "__main__":
    sys.exit(main())
