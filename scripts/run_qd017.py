"""QĐ-017 — hai thí nghiệm bổ sung của GĐ4: D1 đường chéo, D2 máy giả.

    python scripts/run_qd017.py --thi-nghiem D1 --dry-run     # in kế hoạch, không chạy
    python scripts/run_qd017.py --thi-nghiem D1
    python scripts/run_qd017.py --thi-nghiem D2
    python scripts/run_qd017.py --thi-nghiem D1 --resume      # bỏ qua (cặp, mode, h, MODEL) đã có

| | Cặp | Lần khớp | Lần chạm test |
|---|---|---:|---:|
| D1 | E1→E1, E2→E2, E3→E3 | 135 | 135 |
| D2 | E1a→E1a, E1a→E1g, E1g→E1g, E1g→E1a | 90 | 180 |

Cả hai: chế độ N0, N1, N2 × h 1, 6, 12 × 5 model ML × lịch = co.

**Đi đúng đường code của GĐ4.** Khớp model, map ngược, đọc siêu tham số đều gọi thẳng
hàm của `run_transfer.py`, không chép lại. Lý do nằm ở QĐ-017 điểm 3: GĐ3 và GĐ4 lệch
nhau ở kiểu số và ở mẫu con SVR. Muốn `L_k = MAE(A→B) / MAE(B→B)` chỉ còn phần do
transfer thì tử và mẫu phải cùng một đường code.

Khác `run_transfer.py` ở ba chỗ, đều do QĐ-017 chốt:

1. Không chép baseline — D1, D2 không có phép kiểm nào dùng baseline.
2. Siêu tham số của E1a, E1g lấy từ **E1** (QĐ-017 điểm 5.5).
3. Tầng CV và `mu`/`sd` của E1a, E1g đọc từ `cv_qd017.csv`, `normalize_qd017.csv`.

Rào chắn (QĐ-017 điểm 6): không đọc số của D1, D2 trước khi `phan_tich_qd017.py` được
commit.
Mỗi tổ hợp chạy một lần.
"""

from __future__ import annotations

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
from cwp.models.registry import ML_NAMES, SEED  # noqa: E402

from run_transfer import (  # noqa: E402
    bang_goc, cot_dac_trung, doc_ma_tran, doc_sieu_tham_so, ghi, ghi_chuoi,
    khop_mot_model, map_ve_cpu,
)

THI_NGHIEM = {
    "D1": [("E1", "E1"), ("E2", "E2"), ("E3", "E3")],
    "D2": [("E1a", "E1a"), ("E1a", "E1g"), ("E1g", "E1g"), ("E1g", "E1a")],
}
MODES = ("N0", "N1", "N2")
HORIZONS = (1, 6, 12)
LICH = "co"
GOC = ("E1", "E2", "E3")
GIA = ("E1a", "E1g")
# QĐ-017 điểm 5.5: máy giả dùng siêu tham số của E1 ở GĐ3.
SIEU_THAM_SO_TU = {"E1": "E1", "E2": "E2", "E3": "E3", "E1a": "E1", "E1g": "E1"}
KHOA = ["nguon", "dich", "mode", "lich", "h", "model"]


def ten_bang(tn: str) -> tuple[str, str]:
    return f"qd017_{tn.lower()}.csv", f"qd017_{tn.lower()}_chuoi.csv"


def ke_hoach(caps, modes, hs, models, da_co: set[tuple]) -> list[dict]:
    """Danh sách việc phải làm, mỗi phần tử một lần nạp ma trận nguồn.

    `da_co` là tập khoá `(nguồn, đích, mode, lịch, h, model)`. Kiểm **tới tên model**:
    `run_transfer.py` bản đầu chỉ kiểm tới `h`, và `--resume` đã bỏ qua im lặng ba model
    ngày 2026-09-12. `tests/test_qd017.py` giữ ca đó.
    """
    viec = []
    for nguon in sorted({n for n, _ in caps}):
        dich_cua = [d for n, d in caps if n == nguon]
        for mode in modes:
            for h in hs:
                can = {}
                for m in models:
                    thieu = [d for d in dich_cua
                             if (nguon, d, mode, LICH, h, m) not in da_co]
                    if thieu:
                        can[m] = thieu
                if can:
                    viec.append({"nguon": nguon, "mode": mode, "h": h, "model": can})
    return viec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--thi-nghiem", required=True, choices=sorted(THI_NGHIEM))
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--horizons", default=",".join(map(str, HORIZONS)))
    ap.add_argument("--models", default=",".join(ML_NAMES))
    ap.add_argument("--features", default="data/features")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="in kế hoạch rồi thoát")
    a = ap.parse_args()

    tn = a.thi_nghiem
    caps = THI_NGHIEM[tn]
    modes = [x.strip().upper() for x in a.modes.split(",")]
    hs = [int(x) for x in a.horizons.split(",")]
    models = [x.strip() for x in a.models.split(",")]
    la = [m for m in models if m not in ML_NAMES] + [m for m in modes if m not in MODES]
    if la:
        raise SystemExit(f"Không hợp lệ: {la}")

    feat_dir, proc_dir, tab = ROOT / a.features, ROOT / a.processed, ROOT / a.tables
    p_out, p_chuoi = (tab / t for t in ten_bang(tn))
    da_co: set[tuple] = set()
    if a.resume and p_out.exists():
        da_co = set(map(tuple, pd.read_csv(p_out)[KHOA].drop_duplicates().to_numpy()))

    viec = ke_hoach(caps, modes, hs, models, da_co)
    n_khop = sum(len(v["model"]) for v in viec)
    n_cham = sum(len(d) for v in viec for d in v["model"].values())
    print(f"\nQĐ-017 {tn} — {', '.join(f'{x}→{y}' for x, y in caps)}")
    print(f"chế độ {modes} · h {hs} · model {models} · lịch = {LICH}")
    print(f"kế hoạch: {n_khop} lần khớp, {n_cham} lần chạm test"
          + (f" (resume: bỏ qua {len(da_co)} khoá đã có)" if a.resume else ""))
    if a.dry_run:
        for v in viec:
            print(f"   {v['nguon']:4} {v['mode']} h={v['h']:<2} "
                  + " ".join(f"{m}→{'+'.join(d)}" for m, d in v["model"].items()))
        return 0
    if not viec:
        print("Không còn gì để chạy.")
        return 0

    envs = sorted({e for c in caps for e in c})
    chosen = pd.read_csv(tab / "chosen_gd3.csv")
    nrm = pd.concat([pd.read_csv(tab / "normalize_gd4.csv")]
                    + ([pd.read_csv(tab / "normalize_qd017.csv")]
                       if any(e in GIA for e in envs) else []), ignore_index=True)
    nrm = nrm[nrm["mode"] == "N1"].set_index(["env", "series_id"])
    st = doc_cau_hinh_tang(ROOT / "config" / "split.yaml")
    ns = int(st.get("n_strata", 3))
    phan_tang = []
    if any(e in GOC for e in envs):
        phan_tang.append(bang_tang(pd.read_csv(tab / "cv_gd2.csv"), envs=GOC, n_strata=ns))
    if any(e in GIA for e in envs):
        phan_tang.append(bang_tang(pd.read_csv(tab / "cv_qd017.csv"), envs=GIA, n_strata=ns))
    bt = pd.concat(phan_tang, ignore_index=True)

    b0 = {e: doc_b0(e, proc_dir) for e in envs}
    y_goc = {e: bang_goc(e, proc_dir) for e in envs}
    d_mase = {e: mase_denominators_train(pd.read_parquet(proc_dir / f"{e}.parquet"), b0[e])
              for e in envs}
    tang = {e: bt[bt["env"] == e].set_index("series_id")["tang"] for e in envs}
    n_chuoi_tong = {e: int(tang[e].shape[0]) for e in envs}

    run_dir = ROOT / "runs" / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"_qd017_{tn}")
    (run_dir / "config").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "config").glob("*.yaml"):
        shutil.copy2(f, run_dir / "config" / f.name)
    print(f"run: {run_dir.relative_to(ROOT)}\n")

    t0 = time.time()
    cham_test: list[str] = []
    for v in viec:
        nguon, mode, h = v["nguon"], v["mode"], v["h"]
        cot = cot_dac_trung(LICH)
        Xs = doc_ma_tran(nguon, mode, h, feat_dir)
        fit_ix = fit_mask(offset(Xs["bucket"].to_numpy(), b0[nguon]), h)
        X_tr = Xs.loc[fit_ix, cot].to_numpy(dtype="float64")
        y_tr = Xs.loc[fit_ix, "target"].to_numpy(dtype="float64")
        tang_tr = tang[nguon].reindex(Xs.loc[fit_ix, "series_id"]).to_numpy()
        if pd.isna(tang_tr).any():
            raise SystemExit(f"{nguon}: có chuỗi không gán được tầng CV")
        del Xs
        print(f"{nguon} {mode} h={h}: train {len(y_tr):,} dòng")

        dong, chuoi = [], []
        for ten, dichs in v["model"].items():
            ts = doc_sieu_tham_so(chosen, SIEU_THAM_SO_TU[nguon], h, ten)
            mo_hinh, n_dung, giay = khop_mot_model(ten, X_tr, y_tr, ts, tang_tr)
            print(f"   {ten:6} {json.dumps(ts, separators=(',', ':')):32}"
                  f" n_tr={n_dung:>9,}  khớp {giay:6.1f}s", flush=True)
            for dich in dichs:
                Xd = doc_ma_tran(dich, mode, h, feat_dir)
                te = split_masks(offset(Xd["bucket"].to_numpy(), b0[dich]), h)["test"]
                T = Xd.loc[te]
                sid, buc = T["series_id"].to_numpy(), T["bucket"].to_numpy()
                yhat = mo_hinh.predict(T[cot].to_numpy(dtype="float64"))
                cham_test.append(f"{nguon}->{dich}_{mode}_h{h}_{ten}")
                yhat_cpu = map_ve_cpu(yhat, mode, sid, buc, y_goc[dich], nrm.loc[dich])
                y_that = y_goc[dich].reindex(
                    pd.MultiIndex.from_arrays([sid, buc + h])).to_numpy()
                ps = per_series_metrics(sid, y_that, yhat_cpu, d=d_mase[dich])
                khoa = {"nguon": nguon, "dich": dich, "mode": mode, "lich": LICH,
                        "h": h, "model": ten}
                chuoi.append(ps.assign(**khoa))
                for r in gop(ps, n_chuoi_tong=n_chuoi_tong[dich]).to_dict("records"):
                    dong.append({**khoa, **r, "n_dong_test": int(len(T))})
        # Ghi sau mỗi (nguồn, mode, h): dừng giữa chừng không mất việc đã làm.
        ghi(p_out, dong)
        ghi_chuoi(p_chuoi, chuoi)

    giay = time.time() - t0
    _meta(run_dir, tab, tn, caps, modes, hs, models, cham_test, giay, p_out, p_chuoi)
    print(f"\nXong {giay / 60:.1f} phút. Chạm test {len(cham_test)} lần.")
    print(f"Đã ghi: {p_out}, {p_chuoi}")
    return 0


def _meta(run_dir, tab, tn, caps, modes, hs, models, cham, giay, p_out, p_chuoi) -> None:
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, cwd=str(ROOT)).stdout.strip()
    except Exception:
        git = ""
    import sklearn
    meta = {
        "buoc": f"QĐ-017 {tn}",
        "ngay": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv[1:], "cap": [f"{x}->{y}" for x, y in caps],
        "modes": modes, "horizons": hs, "models": models, "lich": LICH, "seed": SEED,
        "sieu_tham_so": SIEU_THAM_SO_TU,
        "so_lan_cham_test": len(cham), "cham_test_chi_tiet": cham,
        "git": git, "host": platform.node(),
        "phien_ban": {"python": platform.python_version(), "pandas": pd.__version__,
                      "numpy": np.__version__, "sklearn": sklearn.__version__},
        "giay": round(giay, 1),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    for p in (p_out, p_chuoi):
        if p.exists():
            shutil.copy2(p, run_dir / p.name)


if __name__ == "__main__":
    sys.exit(main())
