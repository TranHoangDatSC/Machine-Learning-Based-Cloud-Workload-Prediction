"""Thí nghiệm A: tám model × ba môi trường × ba horizon (protocol mục 9–13).

    python scripts/run_experiments.py --env all
    python scripts/run_experiments.py --env E2 --horizons 1 --models ridge,xgb

Tám model = ba baseline của mục 11 (`naive`, `ma6`, `seasonal`, đã có ở Bước 3) cộng
năm model ML (`lr`, `ridge`, `rf`, `xgb`, `svr`).

> `docs/protocol.md` mục 13 viết *"3 môi trường x 7 model x 3 horizon"*, nhưng mục 11
> liệt kê **tám** dòng model. Script này chạy cả tám và báo cả tám — thiếu một dòng thì
> bảng so sánh hụt, còn thừa thì chỉ tốn công. **Hỏi A** xem con số 7 ở mục 13 bỏ dòng
> nào, và sửa mục 13 hoặc mục 11 cho khớp nhau.

Ba điều bắt buộc, và chỗ nào trong tệp này bảo đảm chúng
--------------------------------------------------------

1. **Global model** (mục 11): một model học trên nhiều chuỗi của cùng một môi trường.
   Ma trận đưa vào `fit` gồm mọi chuỗi của môi trường đó, không nhóm theo `series_id`.

2. **Chọn siêu tham số CHỈ trên validation** (mục 9), bằng rolling-origin 5 fold của
   QĐ-014 điểm 1. Hàm `do_lua_chon()` không nhận mặt nạ test và không có đường nào
   chạm tới nó.

3. **Test chỉ chạm một lần** (mục 9, L2 của gate mục 3.4). Toàn bộ tệp này gọi
   `predict` trên dòng test ở **đúng một chỗ** — `cham_test()` — và mỗi lần gọi tăng
   một biến đếm ghi vào `runs/<...>/meta.json`. Biến đếm phải bằng đúng số tổ hợp
   `(env, h, model)` đã chạy. Lớn hơn là đã chạm test nhiều lần.

Đầu ra
------

    results/tables/experiments_gd3.csv   cùng khuôn cột với baselines_gd3.csv
    results/tables/per_series_gd3.csv    MAE... theo TỪNG chuỗi, cho Wilcoxon ở Bước 6
    results/tables/cv_search_gd3.csv     điểm validation của từng ứng viên, từng fold
    results/tables/chosen_gd3.csv        siêu tham số đã chốt, kèm thời gian chạy

Chạy lại được: mỗi tổ hợp `(env, h)` ghi ngay sau khi xong, và `--resume` bỏ qua tổ
hợp đã có trong tệp đầu ra. Một lần chạy đầy đủ mất khoảng ba giờ, phần lớn là RF.
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from cwp.evaluation.metrics import METRIC_NAMES, gop, mase_denominators_train, per_series_metrics
from cwp.evaluation.splits import doc_b0, fit_mask, fold_masks, offset, split_masks
from cwp.evaluation.tang import bang_tang, doc_cau_hinh_tang
from cwp.features import FEATURE_COLS
from cwp.models.baselines import BASELINE_NAMES, du_doan
from cwp.models.registry import ML_NAMES, REGISTRY, SEED, mau_con_phan_tang

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]
HORIZONS = [1, 6, 12]
MOI_MODEL = list(BASELINE_NAMES) + list(ML_NAMES)

TEP = {
    "ket_qua": "experiments_gd3.csv",
    "chuoi": "per_series_gd3.csv",
    "cv": "cv_search_gd3.csv",
    "chon": "chosen_gd3.csv",
}

# Biến đếm của cam kết số 3 ở đầu tệp. Chỉ `cham_test()` được tăng nó.
_SO_LAN_CHAM_TEST = {"n": 0, "chi_tiet": []}


def _git_commit() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "?"
    except Exception:
        return "?"


def _phien_ban() -> dict:
    ver = {"python": platform.python_version()}
    for ten in ("pandas", "numpy", "pyarrow", "scipy", "sklearn", "xgboost"):
        try:
            ver[ten] = __import__(ten).__version__
        except Exception:
            ver[ten] = "?"
    return ver


def mo_thu_muc_run() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    d = ROOT / "runs" / f"{ts}_experiments_gd3"
    (d / "config").mkdir(parents=True, exist_ok=True)
    for ten in ("split.yaml", "features.yaml", "preprocess.yaml", "paths.yaml"):
        nguon = ROOT / "config" / ten
        if nguon.exists():
            shutil.copy2(nguon, d / "config" / ten)
    return d


# ------------------------------------------------------------------ chấm điểm

def diem_validation(sid, y, yhat) -> float:
    """Điểm chọn siêu tham số: **MAE trung vị theo chuỗi** trên fold validation.

    Cùng cách gộp của QĐ-013 điểm 5, để tiêu chí chọn model và con số báo cáo nói
    cùng một thứ. Gộp mọi dòng vào một dãy rồi lấy MAE sẽ cho chuỗi tải cao quyết
    định siêu tham số của cả môi trường.
    """
    ps = per_series_metrics(sid, y, yhat)
    v = ps["mae"].to_numpy("float64")
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else float("nan")


def cham_test(mo_hinh, A_test, nhan: str) -> np.ndarray:
    """**Chỗ duy nhất** trong GĐ3 mà một model ML nhìn thấy dòng test (mục 9, L2)."""
    _SO_LAN_CHAM_TEST["n"] += 1
    _SO_LAN_CHAM_TEST["chi_tiet"].append(nhan)
    return mo_hinh.predict(A_test)


# ------------------------------------------------------- chọn siêu tham số

def do_lua_chon(spec, A, y, sid, off, h, mau_con_ix, log) -> tuple[dict, float]:
    """Rolling-origin 5 fold trên train + validation. **Không nhận mặt nạ test.**

    Trả về ứng viên tốt nhất và điểm trung bình của nó qua năm fold.
    """
    diem = []
    for i_cand, cand in enumerate(spec.luoi):
        theo_fold = []
        for i_fold, m in enumerate(fold_masks(off, h)):
            tr, va = m["train"], m["val"]
            if mau_con_ix is not None:
                tr = tr & mau_con_ix
            n_tr, n_va = int(tr.sum()), int(va.sum())
            if n_tr == 0 or n_va == 0:
                continue
            t0 = time.time()
            mo = spec.dung(cand).fit(A[tr], y[tr])
            d = diem_validation(sid[va], y[va], mo.predict(A[va]))
            theo_fold.append(d)
            log.append({
                "model": spec.ten, "ung_vien": json.dumps(cand, sort_keys=True),
                "fold": i_fold, "n_train": n_tr, "n_val": n_va,
                "mae_p50_val": d, "giay": round(time.time() - t0, 1),
            })
            print(f"      {spec.ten:6} cand{i_cand} fold{i_fold} "
                  f"n_tr={n_tr:>9,} MAE_val={d:.4f} ({time.time() - t0:.0f}s)")
        diem.append(float(np.mean(theo_fold)) if theo_fold else float("inf"))

    tot = int(np.argmin(diem))
    return spec.luoi[tot], diem[tot]


# ------------------------------------------------------------- một tổ hợp

def khoa_dong(sid, off, danh_sach_chuoi) -> np.ndarray:
    """Khoá `(series_id, offset)` gói thành một `int64` — **không phụ thuộc horizon**.

    `offset < 2304 < 4096` nên nhân 4096 rồi cộng là song ánh.
    """
    ma = pd.Categorical(sid, categories=danh_sach_chuoi).codes.astype("int64")
    if (ma < 0).any():
        raise ValueError("có series_id ngoài danh sách chuỗi của môi trường.")
    return ma * 4096 + np.asarray(off, dtype="int64")


def khoa_mau_con_svr(env, feat_dir, b0, tang_env, danh_sach_chuoi, n) -> np.ndarray:
    """Mẫu con của SVR, rút **một lần cho cả môi trường** — QĐ-014 điểm 2.

    Quyết định đòi *"cùng một mẫu con dùng cho cả ba horizon"*. Rút riêng ở từng
    horizon **không** thoả điều đó: vùng train + val của `h = 12` ngắn hơn của `h = 1`
    đúng 11 bucket, nên vị trí trong mảng lệch đi và cùng một seed vẫn cho hai tập
    khác hẳn nhau — đo được chỉ **2,9%** trùng giữa `h = 1` và `h = 6`, **1,6%** giữa
    `h = 1` và `h = 12`.

    Nên mẫu rút từ ma trận `h = 1` (vùng train + val rộng nhất), trả về **khoá**
    `(series_id, offset)`. Mỗi horizon sau đó lấy giao của khoá này với dòng hợp lệ
    của chính nó — số dòng thực dùng nhỏ hơn 10.000 một chút ở `h = 6` và `h = 12`,
    và con số đó được ghi vào `chosen_gd3.csv`.
    """
    X1 = pd.read_parquet(feat_dir / f"{env}_h1.parquet", columns=["series_id", "bucket"])
    off1 = offset(X1["bucket"], b0)
    vi_tri = np.flatnonzero(fit_mask(off1, 1))
    sid1 = X1["series_id"].to_numpy()[vi_tri]
    chon = mau_con_phan_tang(tang_env.reindex(sid1).to_numpy(), n, seed=SEED)
    return np.sort(khoa_dong(sid1[chon], off1[vi_tri[chon]], danh_sach_chuoi))


def chay_mot_to_hop(env, h, X, processed, d_mase, tang_env, n_chuoi_tong,
                    models, run_dir, khoa_mau=None,
                    danh_sach_chuoi=None) -> dict[str, pd.DataFrame]:
    b0 = doc_b0(env, ROOT / "data" / "processed")
    off = offset(X["bucket"], b0)
    mat_na = split_masks(off, h)
    m_test = mat_na["test"]
    m_fit = fit_mask(off, h)

    sid = X["series_id"].to_numpy()
    y = X["target"].to_numpy("float64")
    n_test = int(m_test.sum())

    dong_kq, dong_chuoi, dong_cv, dong_chon = [], [], [], []

    def ghi(model_ten, yhat_test, phu: dict):
        ps = per_series_metrics(sid[m_test], y[m_test], yhat_test, d=d_mase)
        for r in gop(ps, n_chuoi_tong=n_chuoi_tong).to_dict("records"):
            dong_kq.append({
                "env": env, "h": h, "model": model_ten, "split": "test", **r,
                "n_dong_dung": int(ps["n_dong"].sum()), "n_dong_test": n_test,
            })
        ps.insert(0, "model", model_ten)
        ps.insert(0, "h", h)
        ps.insert(0, "env", env)
        dong_chuoi.append(ps)
        dong_chon.append({"env": env, "h": h, "model": model_ten, **phu})

    # --- ba baseline: không học gì, không có siêu tham số, không chạm CV
    for ten in [m for m in models if m in BASELINE_NAMES]:
        t0 = time.time()
        yhat = du_doan(ten, X, processed)[m_test]
        ghi(ten, yhat, {"sieu_tham_so": "{}", "mae_p50_val": None,
                        "n_train_cuoi": 0, "giay": round(time.time() - t0, 1)})
        print(f"   {ten:8} baseline, không huấn luyện ({time.time() - t0:.1f}s)")

    ml = [m for m in models if m in ML_NAMES]
    if not ml:
        return _dong_thanh_bang(dong_kq, dong_chuoi, dong_cv, dong_chon, env, h)

    A = X[FEATURE_COLS].to_numpy("float32")

    for ten in ml:
        spec = REGISTRY[ten]
        t0 = time.time()

        # Mẫu con của SVR — QĐ-014 điểm 2: lấy trên DÒNG, cùng một mẫu cho ba horizon.
        mau_con_ix = None
        if spec.mau_con is not None:
            if khoa_mau is None:
                raise ValueError(f"{ten} cần mẫu con nhưng chưa rút khoá cho {env}.")
            mau_con_ix = np.isin(khoa_dong(sid, off, danh_sach_chuoi), khoa_mau)

        cand, diem = do_lua_chon(spec, A, y, sid, off, h, mau_con_ix, dong_cv)

        m_fit_ml = m_fit if mau_con_ix is None else (m_fit & mau_con_ix)
        n_fit = int(m_fit_ml.sum())
        t1 = time.time()
        mo = spec.dung(cand).fit(A[m_fit_ml], y[m_fit_ml])
        yhat = cham_test(mo, A[m_test], f"{env}_h{h}_{ten}")
        ghi(ten, yhat, {
            "sieu_tham_so": json.dumps(cand, sort_keys=True),
            "mae_p50_val": diem, "n_train_cuoi": n_fit,
            "giay": round(time.time() - t0, 1),
        })
        print(f"   {ten:8} chốt {cand}  MAE_val={diem:.4f}  "
              f"n_train_cuối={n_fit:,}  khớp cuối {time.time() - t1:.0f}s  "
              f"(tổng {time.time() - t0:.0f}s)")

    return _dong_thanh_bang(dong_kq, dong_chuoi, dong_cv, dong_chon, env, h)


def _dong_thanh_bang(kq, chuoi, cv, chon, env, h) -> dict[str, pd.DataFrame]:
    cv_df = pd.DataFrame(cv)
    if not cv_df.empty:
        cv_df.insert(0, "h", h)
        cv_df.insert(0, "env", env)
    return {
        "ket_qua": pd.DataFrame(kq),
        "chuoi": pd.concat(chuoi, ignore_index=True) if chuoi else pd.DataFrame(),
        "cv": cv_df,
        "chon": pd.DataFrame(chon),
    }


# ------------------------------------------------------------------- main

def _da_co(out_dir: Path, env: str, h: int) -> set[str]:
    """Tên các model đã có kết quả cho `(env, h)` — dùng cho `--resume`."""
    p = out_dir / TEP["ket_qua"]
    if not p.exists():
        return set()
    d = pd.read_csv(p)
    return set(d.loc[(d["env"] == env) & (d["h"] == h), "model"].unique())


def _noi_them(out_dir: Path, khoa: str, df: pd.DataFrame, env: str, h: int) -> None:
    """Ghi ngay sau mỗi tổ hợp; dòng cũ của cùng `(env, h, model)` bị thay, không nhân đôi."""
    if df.empty:
        return
    p = out_dir / TEP[khoa]
    if p.exists():
        cu = pd.read_csv(p)
        if "model" in cu.columns and "model" in df.columns:
            bo = (cu["env"] == env) & (cu["h"] == h) & cu["model"].isin(df["model"])
        else:
            bo = (cu["env"] == env) & (cu["h"] == h)
        df = pd.concat([cu[~bo], df], ignore_index=True)
    df.to_csv(p, index=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--horizons", default=",".join(map(str, HORIZONS)))
    ap.add_argument("--models", default=",".join(MOI_MODEL))
    ap.add_argument("--features", default="data/features")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--out", default="results/tables")
    ap.add_argument("--resume", action="store_true",
                    help="bỏ qua tổ hợp (env, h) đã có trong bảng kết quả")
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    horizons = [int(x) for x in a.horizons.split(",")]
    models = [m.strip() for m in a.models.split(",")]
    for m in models:
        if m not in MOI_MODEL:
            raise SystemExit(f"Model không rõ: {m!r}. Có: {MOI_MODEL}.")

    feat_dir, proc_dir = ROOT / a.features, ROOT / a.processed
    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = mo_thu_muc_run()

    st = doc_cau_hinh_tang(ROOT / "config" / "split.yaml")
    cv_bang = pd.read_csv(ROOT / "results" / "tables" / "cv_gd2.csv")
    tang_tat = bang_tang(cv_bang, envs=tuple(envs), n_strata=int(st["n_strata"]))

    print()
    print("THÍ NGHIỆM A — protocol mục 13, tám model của mục 11")
    print(f"model : {', '.join(models)}")
    print(f"run   : {run_dir.relative_to(ROOT)}")
    print(f"seed  : {SEED} (protocol mục 16)")
    print()

    t0 = time.time()
    for env in envs:
        processed = pd.read_parquet(proc_dir / f"{env}.parquet",
                                    columns=["series_id", "bucket", "y"])
        b0 = doc_b0(env, proc_dir)
        d_mase = mase_denominators_train(processed, b0)
        n_chuoi_tong = int(processed["series_id"].nunique())
        tang_env = tang_tat[tang_tat["env"] == env].set_index("series_id")["tang"]
        danh_sach_chuoi = sorted(processed["series_id"].unique())
        khoa_mau = None
        if any(REGISTRY[m].mau_con for m in models if m in ML_NAMES):
            khoa_mau = khoa_mau_con_svr(env, feat_dir, b0, tang_env, danh_sach_chuoi,
                                        REGISTRY["svr"].mau_con)
        print(f"{env}: {n_chuoi_tong} chuỗi, tầng "
              f"{tang_env.value_counts().reindex(['thap','vua','cao']).to_dict()}")

        for h in horizons:
            can_lam = models
            if a.resume:
                da = _da_co(out_dir, env, h)
                can_lam = [m for m in models if m not in da]
                if not can_lam:
                    print(f"  h={h:<2} bỏ qua — cả {len(models)} model đã có")
                    continue
                if len(can_lam) < len(models):
                    print(f"  h={h:<2} chạy tiếp {can_lam} (đã có {sorted(da)})")
            t1 = time.time()
            print(f"  h={h}")
            X = pd.read_parquet(feat_dir / f"{env}_h{h}.parquet")
            bang = chay_mot_to_hop(env, h, X, processed, d_mase, tang_env,
                                   n_chuoi_tong, can_lam, run_dir,
                                   khoa_mau=khoa_mau,
                                   danh_sach_chuoi=danh_sach_chuoi)
            for khoa, df in bang.items():
                _noi_them(out_dir, khoa, df, env, h)
            print(f"  h={h} xong ({time.time() - t1:.0f}s), đã ghi ra {out_dir.name}/")
            _ghi_meta(run_dir, out_dir, envs, horizons, models, t0)

    _ghi_meta(run_dir, out_dir, envs, horizons, models, t0)
    print()
    print(f"Chạm tập test {_SO_LAN_CHAM_TEST['n']} lần "
          f"= số tổ hợp (env, h, model ML) đã chạy — mục 9, L2 của gate mục 3.4.")
    print(f"Xong sau {(time.time() - t0) / 60:.1f} phút. "
          f"Bảng ở {out_dir}, snapshot ở {run_dir.relative_to(ROOT)}.")
    return 0


def _ghi_meta(run_dir, out_dir, envs, horizons, models, t0) -> None:
    for khoa, ten in TEP.items():
        p = out_dir / ten
        if p.exists():
            shutil.copy2(p, run_dir / ten)
    (run_dir / "meta.json").write_text(json.dumps({
        "buoc": "GĐ3 bước 5 — tám model × ba môi trường × ba horizon",
        "ngay": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv[1:],
        "env": envs, "horizons": horizons, "models": models,
        "seed": SEED,
        "luoi_sieu_tham_so": {t: REGISTRY[t].luoi for t in ML_NAMES},
        "mau_con": {t: REGISTRY[t].mau_con for t in ML_NAMES},
        "so_lan_cham_test": _SO_LAN_CHAM_TEST["n"],
        "cham_test_chi_tiet": _SO_LAN_CHAM_TEST["chi_tiet"],
        "git": _git_commit(), "host": platform.node(),
        "phien_ban": _phien_ban(),
        "giay": round(time.time() - t0, 1),
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
