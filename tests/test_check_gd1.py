"""Kiểm chứng chính công cụ kiểm cổng.

Một công cụ kiểm phải chứng minh được nó phân biệt được đạt với trượt. Trong dự án
này `test_env.py` đã hai lần báo đạt trên môi trường hỏng, nên mọi công cụ cổng về
sau đều phải có test kiểu này.

Sinh catalog giả lập từ chính số liệu tham chiếu, rồi kiểm năm tình huống:
    A. khớp tham chiếu               -> phải ĐẠT
    B. số dòng chỉ bằng 50%          -> phải TRƯỢT
    C. E2 thiếu tháng trong id       -> phải TRƯỢT  (bẫy Rnd trùng tên)
    D. thiếu cột bắt buộc            -> phải TRƯỢT
    E. không có data/processed/      -> phải ĐẠT   (luồng của A, thư mục bị gitignore)
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
REF_DIR = ROOT / "results" / "tables"
CHECKER = ROOT / "scripts" / "check_gd1.py"
FROZEN = ROOT / "config" / "e3_machines.txt"
ENVS = ["E1", "E2", "E3"]


def frozen_machines():
    """500 máy E3 đã đóng băng (QĐ-009). Catalog giả lập phải dùng đúng danh sách
    này, nếu không checker sẽ đánh trượt — và đánh trượt như vậy là đúng."""
    if not FROZEN.exists():
        pytest.skip("chưa có config/e3_machines.txt")
    return [ln.strip() for ln in FROZEN.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]


def load_refs():
    refs = {}
    for env in ENVS:
        f = REF_DIR / f"reference_{env}.json"
        if not f.exists():
            pytest.skip(f"chưa có {f.name} — chạy scripts/reference_gd1.py trước")
        d = json.loads(f.read_text(encoding="utf-8"))
        refs[env] = d[0] if isinstance(d, list) else d
    return refs


def build_catalog(refs, scale=1.0, break_e2_id=False, drop_col=None,
                  hosts=None, stamps=None):
    """hosts/stamps: dict env -> giá trị, để giả lập catalog khảm nhiều máy."""
    rows = []
    e3_ids = frozen_machines()
    for env, r in refs.items():
        n_keep = r["chuoi_con_lai"]
        per = int(r["dong_h12"] * scale) // max(n_keep, 1)
        pts = 2000
        n_int_tot = int(round(r["ti_le_noi_suy_pct"] / 100 * pts * n_keep))
        i = 0
        for k in range(n_keep):
            month_ok = env != "E2" or not break_e2_id
            if env == "E3":
                sid = f"E3_{e3_ids[k]}"
            elif env == "E2" and month_ok:
                sid = f"E2_2013-8_{k}"
            else:
                sid = f"{env}_{k}"
            rows.append(dict(
                env=env, series_id=sid, kept=True, reject_reason="",
                n_points=pts,
                n_interp=(n_int_tot // n_keep) + (1 if k < n_int_tot % n_keep else 0),
                valid_rows_h1=per, valid_rows_h6=per, valid_rows_h12=per,
                mean=r["target_mean"], p50=r["target_p50"], std=r["target_std"],
                n_clipped=0,
                built_on=(hosts or {}).get(env, "may-A"),
                built_at=(stamps or {}).get(env, "2026-09-08T22:00:00")))
            i += 1
        rej = {
            "ngoai_cua_so": r["loai_ngoai_cua_so"], "gan_chet": r["loai_gan_chet"],
            "hang": r["loai_hang"], "it_dong": r["loai_it_dong"],
        }
        for reason, cnt in rej.items():
            for _ in range(cnt):
                if env == "E3":
                    sid_r = f"E3_{e3_ids[i]}"      # vẫn nằm trong danh sách đóng băng
                else:
                    pre = f"{env}_2013-8" if env == "E2" else env
                    sid_r = f"{pre}_rej{i}"
                rows.append(dict(
                    env=env, series_id=sid_r, kept=False,
                    reject_reason=reason, n_points=0, n_interp=0,
                    valid_rows_h1=0, valid_rows_h6=0, valid_rows_h12=0,
                    mean=0.0, p50=0.0, std=0.0, n_clipped=0,
                    built_on=(hosts or {}).get(env, "may-A"),
                    built_at=(stamps or {}).get(env, "2026-09-08T22:00:00")))
                i += 1
    df = pd.DataFrame(rows)
    return df.drop(columns=[drop_col]) if drop_col else df


def write_processed(d):
    d.mkdir(parents=True, exist_ok=True)
    for env in ENVS:
        n = 200
        pd.DataFrame(dict(
            env=env, series_id=[f"{env}_0"] * n, bucket=np.arange(n),
            y=np.linspace(1, 50, n), is_interp=[False] * n,
        )).to_parquet(d / f"{env}.parquet")


def run_checker(cat_path, proc_dir):
    r = subprocess.run(
        [sys.executable, str(CHECKER), "--catalog", str(cat_path),
         "--processed", str(proc_dir), "--ref", "results/tables"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    return r.returncode, (r.stdout or "")


@pytest.fixture
def env(tmp_path):
    refs = load_refs()
    proc = tmp_path / "processed"
    write_processed(proc)
    return refs, tmp_path, proc


def test_catalog_khop_thi_dat(env):
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    build_catalog(refs).to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 0, f"catalog khớp mà checker báo trượt:\n{out}"


def test_thieu_dong_thi_truot(env):
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    build_catalog(refs, scale=0.5).to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 1, "số dòng chỉ bằng 50% mà checker vẫn cho qua"
    assert "Dòng hợp lệ h=12" in out


def test_bay_rnd_trung_ten(env):
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    build_catalog(refs, break_e2_id=True).to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 1, "E2 thiếu tháng trong series_id mà checker vẫn cho qua"
    assert "bẫy Rnd" in out


def test_thieu_cot_bat_buoc(env):
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    build_catalog(refs, drop_col="n_interp").to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 1, "thiếu cột bắt buộc mà checker vẫn cho qua"
    assert "n_interp" in out


def test_catalog_kham_nhieu_may_thi_truot(env):
    """Dòng E1 do máy B tính, dòng E2 do máy A tính -> phải TRƯỢT.

    Tình huống này đã xảy ra thật ngày 2026-09-08 và không có gì phát hiện được.
    """
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    build_catalog(refs, hosts={"E1": "may-B", "E2": "may-A", "E3": "may-A"}).to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 1, "catalog khảm từ hai máy mà checker vẫn cho qua"
    assert "khảm" in out


def test_cung_may_khac_thoi_diem_chi_canh_bao(env):
    """Cùng một máy, chạy từng env vào các lúc khác nhau -> CẢNH BÁO, không trượt."""
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    build_catalog(refs, stamps={"E1": "2026-09-08T10:00:00",
                                "E2": "2026-09-08T14:00:00",
                                "E3": "2026-09-08T18:00:00"}).to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 0, f"cùng máy khác thời điểm không nên đánh trượt:\n{out}"
    assert "một lần chạy" in out.lower()


def test_e3_sai_danh_sach_may_thi_truot(env):
    """E3 dùng máy ngoài danh sách đóng băng -> phải TRƯỢT (QĐ-009).

    Ngày 2026-09-09 A và B tự chọn mẫu riêng, chỉ trùng 56/500, mà thống kê gộp vẫn
    lệch dưới 0,05% nên không có gì phát hiện được.
    """
    refs, tmp, proc = env
    p = tmp / "catalog.parquet"
    cat = build_catalog(refs)
    m = cat.env == "E3"
    cat.loc[m, "series_id"] = [f"E3_may_la_{i}" for i in range(int(m.sum()))]
    cat.to_parquet(p)
    rc, out = run_checker(p, proc)
    assert rc == 1, "E3 dùng máy ngoài danh sách đóng băng mà checker vẫn cho qua"
    assert "đóng băng" in out


def test_luong_cua_A_khong_co_processed(env):
    """A pull catalog của B về nhưng data/processed/ bị gitignore nên không có.

    Trường hợp này phải vẫn ĐẠT — nếu không A không bao giờ nghiệm thu được trên
    máy mình.
    """
    refs, tmp, _ = env
    p = tmp / "catalog.parquet"
    build_catalog(refs).to_parquet(p)
    empty = tmp / "khong_co_processed"
    empty.mkdir()
    rc, out = run_checker(p, empty)
    assert rc == 0, f"thiếu data/processed/ mà bị đánh trượt:\n{out}"
    assert "gitignore" in out
