"""Bảng ba baseline GĐ3 cho ba môi trường × ba horizon (protocol mục 11, 12).

    python scripts/run_baselines.py --env all
    python scripts/run_baselines.py --env E2 --horizons 1

Sinh đúng hai tệp theo hợp đồng tên tệp và tên cột ở QĐ-014 điểm 4:

    results/tables/splits_gd3.csv      env, h, split, n_dong
    results/tables/baselines_gd3.csv   env, h, model, split, metric, p25, p50, p75,
                                       iqr, n_chuoi, n_loai, n_dong_dung, n_dong_test

Kèm một thư mục `runs/<timestamp>_baselines_gd3/` chứa snapshot config, phiên bản thư
viện và bản sao hai bảng — protocol mục 16 đòi mọi số trong paper truy ngược được về
một thư mục `runs/` cụ thể.

**Script này không đối chiếu với con số nào.** Việc so với neo là của
`scripts/check_gd3.py`, và để nguyên ở một chỗ là có chủ ý: neo nằm trong script sinh
số thì lần sửa nào cũng có cám dỗ sửa neo thay vì sửa code. Ba baseline không có yếu
tố ngẫu nhiên nào, nên lệch một chữ số là có lỗi ở `src/`, không phải nhiễu.

Báo cáo trên **test** (mục 12). Bảng vẫn ghi thêm `train`/`val` để B tự theo dõi —
QĐ-014 đính chính điểm 2 cho phép, và `check_gd3.py` lọc `split == "test"` trước khi
so. Ghi thêm không phải là **chạm** vào test nhiều lần: baseline không học gì, không
chọn siêu tham số gì, nên không có gì để rò rỉ ngược.
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

from cwp.evaluation.metrics import (
    METRIC_NAMES,
    gop,
    mase_denominators_train,
    per_series_metrics,
)
from cwp.evaluation.splits import SPLIT_NAMES, doc_b0, offset, split_masks
from cwp.models.baselines import BASELINE_NAMES, du_doan

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]
HORIZONS = [1, 6, 12]

# Chỉ nạp cột thật sự cần: ma trận E1 h=1 có 1,65 triệu dòng × 22 cột.
COT_CAN = ["series_id", "bucket", "target", "lag_1", "diff_1", "roll_mean_6"]

CONFIG_SNAPSHOT = ["split.yaml", "features.yaml", "preprocess.yaml", "paths.yaml"]


def _git_commit() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "?"
    except Exception:
        return "?"


def _phien_ban() -> dict:
    ver = {"python": platform.python_version()}
    for ten in ("pandas", "numpy", "pyarrow", "scipy", "sklearn"):
        try:
            ver[ten] = __import__(ten).__version__
        except Exception:
            ver[ten] = "?"
    return ver


def mo_thu_muc_run(hau_to: str = "baselines_gd3") -> Path:
    """`runs/<timestamp>_<hậu tố>/` kèm snapshot config — protocol mục 16."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    d = ROOT / "runs" / f"{ts}_{hau_to}"
    (d / "config").mkdir(parents=True, exist_ok=True)
    for ten in CONFIG_SNAPSHOT:
        nguon = ROOT / "config" / ten
        if nguon.exists():
            shutil.copy2(nguon, d / "config" / ten)
    return d


def cham_mot_to_hop(env: str, h: int, X: pd.DataFrame, processed: pd.DataFrame,
                    d: pd.Series, splits: list[str],
                    n_chuoi_tong: int) -> tuple[list[dict], list[dict]]:
    """Năm chỉ số × ba baseline × các tập, cho một `(env, h)`.

    `n_chuoi_tong` là số chuỗi của **môi trường**, không phải số chuỗi có mặt trong
    tập đang chấm — xem docstring của `metrics.gop()`.
    """
    b0 = doc_b0(env, ROOT / "data" / "processed")
    off = offset(X["bucket"], b0)
    mat_na = split_masks(off, h)

    dong_split = [{"env": env, "h": h, "split": t, "n_dong": int(mat_na[t].sum())}
                  for t in SPLIT_NAMES]

    sid = X["series_id"].to_numpy()
    y = X["target"].to_numpy("float64")

    dong_bl = []
    for model in BASELINE_NAMES:
        yhat = du_doan(model, X, processed)
        for tap in splits:
            m = mat_na[tap]
            n_dong_tap = int(m.sum())
            ps = per_series_metrics(sid[m], y[m], yhat[m], d=d)
            n_dung = int(ps["n_dong"].sum())
            for r in gop(ps, n_chuoi_tong=n_chuoi_tong).to_dict("records"):
                dong_bl.append({
                    "env": env, "h": h, "model": model, "split": tap, **r,
                    "n_dong_dung": n_dung, "n_dong_test": n_dong_tap,
                })
    return dong_split, dong_bl


def in_bang_mae(bl: pd.DataFrame) -> None:
    """MAE trung vị trên test — bảng mà `gate-gd3.md` mục 2.3 neo vào."""
    t = bl[(bl["split"] == "test") & (bl["metric"] == "mae")]
    b = t.pivot_table(index=["env", "h"], columns="model", values="p50")
    print()
    print("=" * 74)
    print("MAE TRUNG VỊ THEO CHUỖI, TRÊN TEST — protocol mục 12, QĐ-013 điểm 5")
    print("=" * 74)
    print(f"{'env':<5}{'h':>3}   {'naive':>10}{'ma6':>12}{'seasonal':>12}")
    for (env, h), r in b.iterrows():
        print(f"{env:<5}{h:>3}   {r['naive']:>10.4f}{r['ma6']:>12.4f}"
              f"{r['seasonal']:>12.4f}")
    print("=" * 74)


def in_bang_dong(sp: pd.DataFrame, bl: pd.DataFrame, catalog: pd.DataFrame | None) -> None:
    """Số dòng mỗi tập, kèm phép kiểm tự thân `n_chuỗi × 2 × h` của gate mục 2.2."""
    print()
    print("=" * 88)
    print("SỐ DÒNG MỖI TẬP, VÀ PHÉP KIỂM TỰ THÂN (mất = hợp_lệ − tổng ba tập)")
    print("=" * 88)
    print(f"{'env':<5}{'h':>3} {'train':>11}{'val':>10}{'test':>10}"
          f"{'hợp lệ':>11}{'mất':>8}{'trần 2h·n':>11}  ")
    w = sp.pivot_table(index=["env", "h"], columns="split", values="n_dong")
    for (env, h), r in w.iterrows():
        tong = int(r["train"] + r["val"] + r["test"])
        if catalog is None:
            print(f"{env:<5}{h:>3} {int(r['train']):>11,}{int(r['val']):>10,}"
                  f"{int(r['test']):>10,}")
            continue
        giu = catalog[(catalog["env"] == env) & catalog["kept"]]
        hop_le = int(giu[f"valid_rows_h{h}"].sum())
        n_chuoi = int(len(giu))
        mat, tran = hop_le - tong, n_chuoi * 2 * h
        dau = "ok" if 1 <= mat <= tran else "SAI"
        print(f"{env:<5}{h:>3} {int(r['train']):>11,}{int(r['val']):>10,}"
              f"{int(r['test']):>10,}{hop_le:>11,}{mat:>8,}{tran:>11,}  {dau}")
    print("=" * 88)
    print("mất = 0 nghĩa là QUÊN PURGE, tức rò rỉ (QĐ-013 điểm 2). Trần là "
          "n_chuỗi × 2 × h;")
    print("dữ liệu thật mất ít hơn trần vì NaN gần ranh giới đã lấy trước một phần.")

    print()
    print("TỈ LỆ DÒNG BỊ BỎ TRÊN TEST — protocol mục 11 đòi xử lý hiện, không lặng lẽ")
    t = bl[(bl["split"] == "test") & (bl["metric"] == "mae")].copy()
    t["bo"] = 100.0 * (1 - t["n_dong_dung"] / t["n_dong_test"])
    p = t.pivot_table(index=["env", "h"], columns="model", values="bo")
    print(f"{'env':<5}{'h':>3}   {'naive':>10}{'ma6':>12}{'seasonal':>12}")
    for (env, h), r in p.iterrows():
        print(f"{env:<5}{h:>3}   {r['naive']:>9.4f}%{r['ma6']:>11.4f}%"
              f"{r['seasonal']:>11.4f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--horizons", default=",".join(map(str, HORIZONS)))
    ap.add_argument("--splits", default="train,val,test",
                    help="tập để chấm; neo của cổng chỉ đọc test")
    ap.add_argument("--features", default="data/features")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--out", default="results/tables")
    ap.add_argument("--no-snapshot", action="store_true",
                    help="không sinh thư mục runs/ — chỉ dùng cho scripts/pha_gd3.py")
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    horizons = [int(x) for x in a.horizons.split(",")]
    splits = [s.strip() for s in a.splits.split(",")]
    for s in splits:
        if s not in SPLIT_NAMES:
            raise SystemExit(f"Tập không rõ: {s!r}. Có: {SPLIT_NAMES}.")

    feat_dir, proc_dir = ROOT / a.features, ROOT / a.processed
    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = None if a.no_snapshot else mo_thu_muc_run()

    cat_path = ROOT / "data" / "catalog.parquet"
    catalog = pd.read_parquet(cat_path) if cat_path.exists() else None

    print()
    print("BA BASELINE GĐ3 — protocol mục 11, chỉ số mục 12, quy ước QĐ-013")
    print(f"đặc trưng : {feat_dir}")
    print(f"gốc       : {proc_dir}   (seasonal naive nối ngược về đây)")
    print(f"run       : "
          f"{run_dir.relative_to(ROOT) if run_dir else '(bỏ qua, --no-snapshot)'}")
    print()

    t0 = time.time()
    dong_split, dong_bl = [], []
    for env in envs:
        t1 = time.time()
        processed = pd.read_parquet(proc_dir / f"{env}.parquet",
                                    columns=["series_id", "bucket", "y"])
        b0 = doc_b0(env, proc_dir)
        n_chuoi_tong = int(processed["series_id"].nunique())
        d = mase_denominators_train(processed, b0)
        print(f"{env}: b0 = {b0:,}, {processed['series_id'].nunique()} chuỗi, "
              f"mẫu số MASE trung vị {float(d.median()):.4f} "
              f"({int((d == 0).sum())} chuỗi có d = 0)")

        for h in horizons:
            X = pd.read_parquet(feat_dir / f"{env}_h{h}.parquet", columns=COT_CAN)
            s, b = cham_mot_to_hop(env, h, X, processed, d, splits, n_chuoi_tong)
            dong_split += s
            dong_bl += b
            n = {r["split"]: r["n_dong"] for r in s}
            print(f"  h={h:<2} train {n['train']:>10,}  val {n['val']:>9,}  "
                  f"test {n['test']:>9,}   ({time.time() - t1:.1f}s)")

    sp = pd.DataFrame(dong_split)
    bl = pd.DataFrame(dong_bl)[
        ["env", "h", "model", "split", "metric", "p25", "p50", "p75", "iqr",
         "n_chuoi", "n_loai", "n_dong_dung", "n_dong_test"]
    ]
    bl["metric"] = pd.Categorical(bl["metric"], categories=METRIC_NAMES, ordered=True)
    bl = bl.sort_values(["env", "h", "model", "split", "metric"]).reset_index(drop=True)

    sp.to_csv(out_dir / "splits_gd3.csv", index=False)
    bl.to_csv(out_dir / "baselines_gd3.csv", index=False)

    in_bang_dong(sp, bl, catalog)
    in_bang_mae(bl)

    if run_dir is not None:
        luu_snapshot(run_dir, out_dir, envs, horizons, splits, t0)

    print()
    print(f"Ghi {out_dir / 'splits_gd3.csv'} ({len(sp)} dòng) và "
          f"{out_dir / 'baselines_gd3.csv'} ({len(bl)} dòng).")
    print(f"({time.time() - t0:.1f}s tổng)  Đối chiếu với neo: "
          "python scripts/check_gd3.py")
    return 0


def luu_snapshot(run_dir: Path, out_dir: Path, envs, horizons, splits,
                 t0: float) -> None:
    """Bản sao hai bảng kèm `meta.json` — protocol mục 16."""
    for f in ("splits_gd3.csv", "baselines_gd3.csv"):
        shutil.copy2(out_dir / f, run_dir / f)
    (run_dir / "meta.json").write_text(json.dumps({
        "buoc": "GĐ3 bước 3 — ba baseline",
        "ngay": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv[1:],
        "env": envs, "horizons": horizons, "splits": splits,
        "seed": "không dùng — ba baseline không có yếu tố ngẫu nhiên",
        "git": _git_commit(), "host": platform.node(),
        "phien_ban": _phien_ban(),
        "giay": round(time.time() - t0, 1),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Snapshot: {run_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
