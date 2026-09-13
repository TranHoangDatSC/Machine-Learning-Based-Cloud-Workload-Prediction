"""QĐ-018 — chạy lại N1, loại chuỗi đứng yên khỏi TẬP HUẤN LUYỆN, giữ nguyên tập chấm.

    python scripts/run_qd018.py --dry-run
    python scripts/run_qd018.py
    python scripts/run_qd018.py --resume

75 lần khớp, 195 lần chạm test (QĐ-018 điểm 2). Mọi luật khác giữ nguyên QĐ-017: cùng
đường code GĐ4, cùng siêu tham số, cùng map ngược, cùng tập test.

Khác đúng một chỗ: dòng train của chuỗi có tên trong `config/qd018_loai_n1.csv` (cùng
môi trường nguồn) bị bỏ **trước** khi rút mẫu con SVR và trước khi khớp. Số dòng train
gốc, số dòng thực dùng và số chuỗi bị loại ghi vào `results/tables/qd018_khop.csv`, để
`check_qd018.py` đối chiếu.

Đầu ra: `results/tables/qd018_n1.csv`, `qd018_n1_chuoi.csv` — cùng schema bảng QĐ-017.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
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
MODE = "N1"
HORIZONS = (1, 6, 12)
TEN_BANG, TEN_CHUOI, TEN_KHOP = "qd018_n1.csv", "qd018_n1_chuoi.csv", "qd018_khop.csv"


def doc_loai(p: Path) -> dict[str, set[str]]:
    d = pd.read_csv(p)
    return {e: set(g["series_id"]) for e, g in d.groupby("env")}


def mat_na_train(sid: np.ndarray, fit_ix: np.ndarray, loai: set[str]) -> np.ndarray:
    """Vùng khớp trừ dòng của chuỗi bị loại — QĐ-018 điểm 1. Tập chấm không đi qua đây."""
    return np.asarray(fit_ix, dtype=bool) & ~np.isin(sid, list(loai))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--horizons", default=",".join(map(str, HORIZONS)))
    ap.add_argument("--models", default=",".join(ML_NAMES))
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--nguon", default=None, help="chỉ chạy các nguồn này, ví dụ E1g,E3")
    a = ap.parse_args()
    hs = [int(x) for x in a.horizons.split(",")]
    models = [x.strip() for x in a.models.split(",")]
    feat_dir, proc_dir, tab = ROOT / "data/features", ROOT / "data/processed", ROOT / a.tables
    p_out, p_chuoi, p_khop = tab / TEN_BANG, tab / TEN_CHUOI, tab / TEN_KHOP
    loai = doc_loai(ROOT / "config" / "qd018_loai_n1.csv")
    caps = CAP if not a.nguon else [c for c in CAP if c[0] in a.nguon.split(",")]

    da_co: set[tuple] = set()
    if a.resume and p_out.exists():
        da_co = set(map(tuple, pd.read_csv(p_out)[rq.KHOA].drop_duplicates().to_numpy()))
    viec = rq.ke_hoach(caps, [MODE], hs, models, da_co)
    n_khop = sum(len(v["model"]) for v in viec)
    n_cham = sum(len(d) for v in viec for d in v["model"].values())
    print(f"\nQĐ-018 — N1, loại chuỗi đứng yên khỏi tập train · h {hs} · model {models}")
    print("loại: " + " · ".join(f"{e} {len(loai.get(e, set()))}" for e in
                                sorted({n for n, _ in CAP})))
    print(f"kế hoạch: {n_khop} lần khớp, {n_cham} lần chạm test")
    if a.dry_run:
        for v in viec:
            print(f"   {v['nguon']:4} h={v['h']:<2} "
                  + " ".join(f"{m}→{'+'.join(d)}" for m, d in v["model"].items()))
        return 0
    if not viec:
        print("Không còn gì để chạy.")
        return 0

    envs = sorted({e for c in CAP for e in c})
    chosen = pd.read_csv(tab / "chosen_gd3.csv")
    nrm = pd.concat([pd.read_csv(tab / "normalize_gd4.csv"),
                     pd.read_csv(tab / "normalize_qd017.csv")], ignore_index=True)
    nrm = nrm[nrm["mode"] == "N1"].set_index(["env", "series_id"])
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

    run_dir = ROOT / "runs" / (datetime.now().strftime("%Y%m%d-%H%M%S") + "_qd018_N1")
    (run_dir / "config").mkdir(parents=True, exist_ok=True)
    for f in list((ROOT / "config").glob("*.yaml")) + [ROOT / "config" / "qd018_loai_n1.csv"]:
        shutil.copy2(f, run_dir / "config" / f.name)
    print(f"run: {run_dir.relative_to(ROOT)}\n")

    t0 = time.time()
    cham: list[str] = []
    for v in viec:
        nguon, h = v["nguon"], v["h"]
        cot = cot_dac_trung(rq.LICH)
        Xs = doc_ma_tran(nguon, MODE, h, feat_dir)
        sid_s = Xs["series_id"].to_numpy()
        fit_goc = fit_mask(offset(Xs["bucket"].to_numpy(), b0[nguon]), h)
        fit_ix = mat_na_train(sid_s, fit_goc, loai.get(nguon, set()))
        X_tr = Xs.loc[fit_ix, cot].to_numpy(dtype="float64")
        y_tr = Xs.loc[fit_ix, "target"].to_numpy(dtype="float64")
        tang_tr = tang[nguon].reindex(sid_s[fit_ix]).to_numpy()
        if pd.isna(tang_tr).any():
            raise SystemExit(f"{nguon}: có chuỗi không gán được tầng CV")
        khop_dong = [{"nguon": nguon, "h": h, "n_train_goc": int(fit_goc.sum()),
                      "n_train_dung": int(fit_ix.sum()),
                      "n_chuoi_loai": len(loai.get(nguon, set()))}]
        del Xs
        print(f"{nguon} N1 h={h}: train {int(fit_ix.sum()):,} dòng "
              f"(gốc {int(fit_goc.sum()):,}, loại {len(loai.get(nguon, set()))} chuỗi)")

        dong, chuoi = [], []
        for ten, dichs in v["model"].items():
            ts = doc_sieu_tham_so(chosen, rq.SIEU_THAM_SO_TU[nguon], h, ten)
            mo_hinh, n_dung, giay = khop_mot_model(ten, X_tr, y_tr, ts, tang_tr)
            print(f"   {ten:6} {json.dumps(ts, separators=(',', ':')):32}"
                  f" n_tr={n_dung:>9,}  khớp {giay:6.1f}s", flush=True)
            for dich in dichs:
                Xd = doc_ma_tran(dich, MODE, h, feat_dir)
                te = split_masks(offset(Xd["bucket"].to_numpy(), b0[dich]), h)["test"]
                T = Xd.loc[te]
                sid, buc = T["series_id"].to_numpy(), T["bucket"].to_numpy()
                yhat = mo_hinh.predict(T[cot].to_numpy(dtype="float64"))
                cham.append(f"{nguon}->{dich}_N1_h{h}_{ten}")
                yhat_cpu = map_ve_cpu(yhat, MODE, sid, buc, y_goc[dich], nrm.loc[dich])
                y_that = y_goc[dich].reindex(pd.MultiIndex.from_arrays([sid, buc + h])).to_numpy()
                ps = per_series_metrics(sid, y_that, yhat_cpu, d=d_mase[dich])
                khoa = {"nguon": nguon, "dich": dich, "mode": MODE, "lich": rq.LICH,
                        "h": h, "model": ten}
                chuoi.append(ps.assign(**khoa))
                for r in gop(ps, n_chuoi_tong=n_chuoi_tong[dich]).to_dict("records"):
                    dong.append({**khoa, **r, "n_dong_test": int(len(T))})
        ghi(p_out, dong)
        ghi_chuoi(p_chuoi, chuoi)
        ghi_khop(p_khop, khop_dong)

    giay = time.time() - t0
    meta = {"buoc": "QĐ-018 — N1 độ nhạy", "argv": sys.argv[1:], "so_lan_cham_test": len(cham),
            "cham_test_chi_tiet": cham, "loai": {k: sorted(v) for k, v in loai.items()},
            "giay": round(giay, 1)}
    try:
        import subprocess
        meta["git"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True, cwd=str(ROOT)).stdout.strip()
    except Exception:
        meta["git"] = ""
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    for p in (p_out, p_chuoi, p_khop):
        if p.exists():
            shutil.copy2(p, run_dir / p.name)
    print(f"\nXong {giay / 60:.1f} phút. Chạm test {len(cham)} lần.")
    print(f"Đã ghi: {p_out}, {p_chuoi}, {p_khop}")
    return 0


def ghi_khop(p: Path, dong: list[dict]) -> None:
    df = pd.DataFrame(dong)
    if p.exists():
        cu = pd.read_csv(p)
        bo = cu.set_index(["nguon", "h"]).index.isin(df.set_index(["nguon", "h"]).index)
        df = pd.concat([cu[~bo], df], ignore_index=True)
    df.to_csv(p, index=False)


if __name__ == "__main__":
    sys.exit(main())
