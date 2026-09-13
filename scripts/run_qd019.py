"""QĐ-019 — chạy lại N2 ở h = 6, 12 với ma trận target đúng.

    python scripts/run_qd019.py --dry-run
    python scripts/run_qd019.py
    python scripts/run_qd019.py --resume

50 lần khớp, 130 lần chạm test cho 13 cặp × h ∈ {6, 12}; cộng E1g → E1g, E1a ở h = 1 làm
phép kiểm tất định (5 lần khớp, 10 lần chạm). Mọi luật khác giữ nguyên QĐ-017: cùng
đường code GĐ4, cùng siêu tham số, cùng map ngược `y_t + Δ̂`, cùng tập test.

Khác đúng một chỗ: đọc ma trận từ `data/features_qd019/` (sinh bởi `build_qd019.py`).

Đầu ra: `results/tables/qd019_n2.csv`, `qd019_n2_chuoi.csv`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from cwp.evaluation.metrics import gop, mase_denominators_train, per_series_metrics  # noqa: E402
from cwp.evaluation.splits import doc_b0, fit_mask, offset, split_masks  # noqa: E402
from cwp.evaluation.tang import bang_tang, doc_cau_hinh_tang  # noqa: E402
from cwp.models.registry import ML_NAMES  # noqa: E402

import run_qd017 as rq  # noqa: E402
from run_transfer import (  # noqa: E402
    bang_goc, cot_dac_trung, doc_ma_tran, doc_sieu_tham_so, ghi, ghi_chuoi,
    khop_mot_model, map_ve_cpu,
)

CAP = [("E1", "E1"), ("E1", "E2"), ("E1", "E3"),
       ("E2", "E2"), ("E2", "E1"), ("E2", "E3"),
       ("E3", "E3"), ("E3", "E1"), ("E3", "E2"),
       ("E1a", "E1a"), ("E1a", "E1g"),
       ("E1g", "E1g"), ("E1g", "E1a")]
CAP_KIEM = [("E1g", "E1g"), ("E1g", "E1a")]
MODE = "N2"
FEAT = ROOT / "data" / "features_qd019"
TEN_BANG, TEN_CHUOI = "qd019_n2.csv", "qd019_n2_chuoi.csv"


def ke_hoach_qd019(models, da_co) -> list[dict]:
    """h = 6, 12 cho 13 cặp, rồi h = 1 cho hai cặp kiểm tất định."""
    return (rq.ke_hoach(CAP, [MODE], [6, 12], models, da_co)
            + rq.ke_hoach(CAP_KIEM, [MODE], [1], models, da_co))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", default=",".join(ML_NAMES))
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tables", default="results/tables")
    a = ap.parse_args()
    models = [x.strip() for x in a.models.split(",")]
    proc_dir, tab = ROOT / "data/processed", ROOT / a.tables
    p_out, p_chuoi = tab / TEN_BANG, tab / TEN_CHUOI

    da_co: set[tuple] = set()
    if a.resume and p_out.exists():
        da_co = set(map(tuple, pd.read_csv(p_out)[rq.KHOA].drop_duplicates().to_numpy()))
    viec = ke_hoach_qd019(models, da_co)
    n_khop = sum(len(v["model"]) for v in viec)
    n_cham = sum(len(d) for v in viec for d in v["model"].values())
    print(f"\nQĐ-019 — N2 target y(t+h) − y(t) · ma trận {FEAT.relative_to(ROOT)}")
    print(f"kế hoạch: {n_khop} lần khớp, {n_cham} lần chạm test")
    if a.dry_run:
        for v in viec:
            print(f"   {v['nguon']:4} h={v['h']:<2} "
                  + " ".join(f"{m}→{'+'.join(d)}" for m, d in v["model"].items()))
        return 0
    if not viec:
        print("Không còn gì để chạy.")
        return 0
    if not FEAT.exists():
        raise SystemExit(f"Thiếu {FEAT}. Chạy build_qd019.py rồi check_qd019.py trước.")

    envs = sorted({e for c in CAP for e in c})
    chosen = pd.read_csv(tab / "chosen_gd3.csv")
    ns = int(doc_cau_hinh_tang(ROOT / "config" / "split.yaml").get("n_strata", 3))
    bt = pd.concat([bang_tang(pd.read_csv(tab / "cv_gd2.csv"), envs=rq.GOC, n_strata=ns),
                    bang_tang(pd.read_csv(tab / "cv_qd017.csv"), envs=rq.GIA, n_strata=ns)],
                   ignore_index=True)
    b0 = {e: doc_b0(e, proc_dir) for e in envs}
    y_goc = {e: bang_goc(e, proc_dir) for e in envs}
    d_mase = {e: mase_denominators_train(pd.read_parquet(proc_dir / f"{e}.parquet"), b0[e])
              for e in envs}
    tang = {e: bt[bt["env"] == e].set_index("series_id")["tang"] for e in envs}
    n_chuoi_tong = {e: int(tang[e].shape[0]) for e in envs}

    run_dir = ROOT / "runs" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "_qd019_N2")
    (run_dir / "config").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "config").glob("*.yaml"):
        shutil.copy2(f, run_dir / "config" / f.name)
    print(f"run: {run_dir.relative_to(ROOT)}\n")

    t0 = time.time()
    cham: list[str] = []
    for v in viec:
        nguon, h = v["nguon"], v["h"]
        cot = cot_dac_trung(rq.LICH)
        Xs = doc_ma_tran(nguon, MODE, h, FEAT)
        fit_ix = fit_mask(offset(Xs["bucket"].to_numpy(), b0[nguon]), h)
        X_tr = Xs.loc[fit_ix, cot].to_numpy(dtype="float64")
        y_tr = Xs.loc[fit_ix, "target"].to_numpy(dtype="float64")
        tang_tr = tang[nguon].reindex(Xs.loc[fit_ix, "series_id"]).to_numpy()
        if pd.isna(tang_tr).any():
            raise SystemExit(f"{nguon}: có chuỗi không gán được tầng CV")
        del Xs
        print(f"{nguon} N2 h={h}: train {len(y_tr):,} dòng")

        dong, chuoi = [], []
        for ten, dichs in v["model"].items():
            ts = doc_sieu_tham_so(chosen, rq.SIEU_THAM_SO_TU[nguon], h, ten)
            mo_hinh, n_dung, giay = khop_mot_model(ten, X_tr, y_tr, ts, tang_tr)
            print(f"   {ten:6} {json.dumps(ts, separators=(',', ':')):32}"
                  f" n_tr={n_dung:>9,}  khớp {giay:6.1f}s", flush=True)
            for dich in dichs:
                Xd = doc_ma_tran(dich, MODE, h, FEAT)
                te = split_masks(offset(Xd["bucket"].to_numpy(), b0[dich]), h)["test"]
                T = Xd.loc[te]
                sid, buc = T["series_id"].to_numpy(), T["bucket"].to_numpy()
                yhat = mo_hinh.predict(T[cot].to_numpy(dtype="float64"))
                cham.append(f"{nguon}->{dich}_N2_h{h}_{ten}")
                # N2 map ngược không cần mu/sd: truyền khung rỗng.
                yhat_cpu = map_ve_cpu(yhat, MODE, sid, buc, y_goc[dich], pd.DataFrame())
                y_that = y_goc[dich].reindex(pd.MultiIndex.from_arrays([sid, buc + h])).to_numpy()
                ps = per_series_metrics(sid, y_that, yhat_cpu, d=d_mase[dich])
                khoa = {"nguon": nguon, "dich": dich, "mode": MODE, "lich": rq.LICH,
                        "h": h, "model": ten}
                chuoi.append(ps.assign(**khoa))
                for r in gop(ps, n_chuoi_tong=n_chuoi_tong[dich]).to_dict("records"):
                    dong.append({**khoa, **r, "n_dong_test": int(len(T))})
        ghi(p_out, dong)
        ghi_chuoi(p_chuoi, chuoi)

    giay = time.time() - t0
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             cwd=str(ROOT)).stdout.strip()
    except Exception:
        git = ""
    meta = {"buoc": "QĐ-019 — N2 target đúng", "argv": sys.argv[1:],
            "so_lan_cham_test": len(cham), "cham_test_chi_tiet": cham, "git": git,
            "ma_tran": str(FEAT.relative_to(ROOT)), "giay": round(giay, 1)}
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    for p in (p_out, p_chuoi):
        if p.exists():
            shutil.copy2(p, run_dir / p.name)
    print(f"\nXong {giay / 60:.1f} phút. Chạm test {len(cham)} lần.")
    print(f"Đã ghi: {p_out}, {p_chuoi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
