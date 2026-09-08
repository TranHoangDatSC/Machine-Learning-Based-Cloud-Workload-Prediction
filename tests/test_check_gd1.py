"""Kiểm chứng chính công cụ kiểm cổng.

Một công cụ kiểm phải chứng minh được nó phân biệt được đạt với trượt. Trong dự án
này `test_env.py` đã hai lần báo đạt trên môi trường hỏng, nên mọi công cụ cổng về
sau đều phải có test kiểu này.

Sinh catalog giả lập từ chính số liệu tham chiếu, rồi kiểm bốn tình huống:
    A. khớp tham chiếu          -> phải ĐẠT
    B. số dòng chỉ bằng 50%     -> phải TRƯỢT
    C. E2 thiếu tháng trong id  -> phải TRƯỢT  (bẫy Rnd trùng tên)
    D. thiếu cột bắt buộc       -> phải TRƯỢT
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
ENVS = ["E1", "E2", "E3"]


def load_refs():
    refs = {}
    for env in ENVS:
        f = REF_DIR / f"reference_{env}.json"
        if not f.exists():
            pytest.skip(f"chưa có {f.name} — chạy scripts/reference_gd1.py trước")
        d = json.loads(f.read_text(encoding="utf-8"))
        refs[env] = d[0] if isinstance(d, list) else d
    return refs


def build_catalog(refs, scale=1.0, break_e2_id=False, drop_col=None):
    rows = []
    for env, r in refs.items():
        n_keep = r["chuoi_con_lai"]
        per = int(r["dong_h12"] * scale) // max(n_keep, 1)
        pts = 2000
        n_int_tot = int(round(r["ti_le_noi_suy_pct"] / 100 * pts * n_keep))
        i = 0
        for k in range(n_keep):
            month_ok = env != "E2" or not break_e2_id
            sid = f"{env}_2013-8_{k}" if (env == "E2" and month_ok) else f"{env}_{k}"
            rows.append(dict(
                env=env, series_id=sid, kept=True, reject_reason="",
                n_points=pts,
                n_interp=(n_int_tot // n_keep) + (1 if k < n_int_tot % n_keep else 0),
                valid_rows_h1=per, valid_rows_h6=per, valid_rows_h12=per,
                mean=r["target_mean"], p50=r["target_p50"], std=r["target_std"],
                n_clipped=0))
            i += 1
        rej = {
            "ngoai_cua_so": r["loai_ngoai_cua_so"], "gan_chet": r["loai_gan_chet"],
            "hang": r["loai_hang"], "it_dong": r["loai_it_dong"],
        }
        for reason, cnt in rej.items():
            for _ in range(cnt):
                pre = f"{env}_2013-8" if env == "E2" else env
                rows.append(dict(
                    env=env, series_id=f"{pre}_rej{i}", kept=False,
                    reject_reason=reason, n_points=0, n_interp=0,
                    valid_rows_h1=0, valid_rows_h6=0, valid_rows_h12=0,
                    mean=0.0, p50=0.0, std=0.0, n_clipped=0))
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
