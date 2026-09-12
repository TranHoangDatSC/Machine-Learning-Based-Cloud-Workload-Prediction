"""GĐ4 Bước 4 — Thí nghiệm B: transfer xuyên môi trường (protocol mục 14).

    python scripts/run_transfer.py --all
    python scripts/run_transfer.py --cap E1:E3 --modes N0 --lich co --horizons 1
    python scripts/run_transfer.py --all --resume        # bỏ qua tổ hợp đã có

Sáu cặp × ba chế độ × hai biến thể lịch × ba horizon = **108 tổ hợp**, mỗi tổ hợp 8
model (3 baseline + 5 ML) × 5 chỉ số → 4.320 dòng `results/tables/transfer_gd4.csv`.

Sáu luật, chốt ở QĐ-016 và `brief-gd4-b.md` Bước 4:

1. **Train trên NGUỒN, test trên ĐÍCH.** Vùng huấn luyện là `[0, 1957)` của nguồn đã
   purge; chấm trên `[1957, 2304)` của đích, cùng luật purge. **Không** huấn luyện lại
   trên đích — đó mới là transfer.
2. **Siêu tham số dùng lại của GĐ3** theo từng môi trường **nguồn** (QĐ-016 điểm 3),
   đọc từ `results/tables/chosen_gd3.csv`. Không dò lại rolling-origin.
3. **Mọi chỉ số tính SAU KHI map ngược về thang CPU% gốc** (mục 14). So MAE của z với
   MAE của CPU% là so hai đơn vị khác nhau.
4. Chấm trên đúng tập test của đích.
5. **Ba baseline là mốc cố định của môi trường ĐÍCH**, giống nhau ở cả ba chế độ —
   lấy thẳng từ `results/tables/baselines_gd3.csv`, không tính lại (QĐ-016 điểm 4).
6. Đếm số lần chạm test, ghi vào `runs/<timestamp>/meta.json`.

**Một model dùng cho hai đích.** Model chỉ phụ thuộc `(nguồn, chế độ, lịch, h)`, nên
khớp **một lần** rồi dự đoán cho cả hai môi trường đích của nguồn đó. Không làm vậy
thì mất gấp đôi thời gian máy mà không đổi một con số nào.

Rào chắn: số kỳ vọng ở `gate-gd4.md` chỉ để đối chiếu **sau** khi chạy. Không sửa đầu
ra cho khớp; sai thì sửa cách hiện thực cho đúng QĐ-016.
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

from cwp.evaluation.metrics import (  # noqa: E402
    METRIC_NAMES, gop, mase_denominators_train, per_series_metrics,
)
from cwp.evaluation.splits import doc_b0, fit_mask, offset, split_masks  # noqa: E402
from cwp.evaluation.tang import bang_tang, doc_cau_hinh_tang  # noqa: E402
from cwp.features import FEATURE_COLS  # noqa: E402
from cwp.models.baselines import BASELINE_NAMES  # noqa: E402
from cwp.models.registry import ML_NAMES, REGISTRY, SEED, mau_con_phan_tang  # noqa: E402
from cwp.preprocess.normalize import MODES  # noqa: E402

ENVS = ("E1", "E2", "E3")
CAP = [("E1", "E2"), ("E2", "E1"), ("E1", "E3"),
       ("E3", "E1"), ("E2", "E3"), ("E3", "E2")]
HORIZONS = (1, 6, 12)
LICH = ("co", "khong")
CAL_COLS = ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
TEN_BANG = "transfer_gd4.csv"
COT = ["nguon", "dich", "mode", "lich", "h", "model", "metric",
       "p25", "p50", "p75", "iqr", "n_chuoi", "n_loai", "n_dong_test"]


# --------------------------------------------------------------------- nạp

def cot_dac_trung(lich: str) -> list[str]:
    """19 đặc trưng, hoặc 15 khi bỏ lịch — mục 8 đòi riêng biến thể này cho TN-B."""
    return FEATURE_COLS if lich == "co" else [c for c in FEATURE_COLS
                                              if c not in CAL_COLS]


def doc_ma_tran(env: str, mode: str, h: int, feat_dir: Path) -> pd.DataFrame:
    p = feat_dir / f"{env}_{mode}_h{h}.parquet"
    if not p.exists():
        raise SystemExit(f"Thiếu {p}. Chạy build_features.py --modes N0,N1,N2 trước.")
    return pd.read_parquet(p)


def bang_goc(env: str, proc_dir: Path) -> pd.Series:
    """`y` gốc theo `(series_id, bucket)` — dùng để map ngược N2 và lấy target thật."""
    d = pd.read_parquet(proc_dir / f"{env}.parquet",
                        columns=["series_id", "bucket", "y"])
    return d.set_index(["series_id", "bucket"])["y"]


def doc_sieu_tham_so(chosen: pd.DataFrame, env: str, h: int, model: str) -> dict:
    r = chosen[(chosen["env"] == env) & (chosen["h"] == h)
               & (chosen["model"] == model)]
    if r.empty:
        return {}
    v = r["sieu_tham_so"].iloc[0]
    return json.loads(v) if isinstance(v, str) and v.strip() else {}


# ------------------------------------------------------------ map ngược

def map_ve_cpu(yhat: np.ndarray, mode: str, sid: np.ndarray, buc: np.ndarray,
               y_goc: pd.Series, mu_sd: pd.DataFrame) -> np.ndarray:
    """Đưa dự đoán về thang CPU% gốc của môi trường ĐÍCH — luật 3.

    N1 dùng `mu`/`sd` của **chính chuỗi đích**, đúng QĐ-016 điểm 1. N2 cộng lại mốc
    neo `y_t` của chuỗi đích. Cả hai đều là thông tin của đích, không phải của nguồn —
    và đó là lý do RQ3 **không** được phát biểu là zero-shot.
    """
    if mode == "N0":
        return yhat
    if mode == "N1":
        mu = mu_sd["mu"].reindex(sid).to_numpy()
        sd = mu_sd["sd"].reindex(sid).to_numpy()
        return yhat * sd + mu
    # N2: ŷ_gốc = y_t + Δ̂
    neo = y_goc.reindex(pd.MultiIndex.from_arrays([sid, buc])).to_numpy()
    return neo + yhat


# ------------------------------------------------------------------ chạy

def khop_mot_model(ten: str, X_tr: np.ndarray, y_tr: np.ndarray,
                   tham_so: dict, tang_tr: np.ndarray | None):
    """Khớp một model ML trên dữ liệu nguồn. Trả `(model, n_dòng_dùng, giây)`."""
    spec = REGISTRY[ten]
    ix = np.arange(len(y_tr))
    if spec.mau_con is not None and tang_tr is not None:
        ix = mau_con_phan_tang(tang_tr, spec.mau_con, seed=SEED)
    t0 = time.time()
    mo_hinh = spec.dung(tham_so)
    mo_hinh.fit(X_tr[ix], y_tr[ix])
    return mo_hinh, len(ix), time.time() - t0


def dong_baseline(bl: pd.DataFrame, nguon: str, dich: str, mode: str,
                  lich: str, h: int) -> list[dict]:
    """Baseline của ĐÍCH, chép thẳng từ GĐ3 — luật 5, QĐ-016 điểm 4.

    Chép chứ không tính lại: baseline không học gì nên giá trị của nó ở GĐ4 phải bằng
    đúng GĐ3. Tính lại là mở ra khả năng hai con số lệch nhau mà không ai giải thích
    được.
    """
    r = bl[(bl["env"] == dich) & (bl["h"] == h) & (bl["split"] == "test")]
    out = []
    for _, x in r.iterrows():
        out.append({
            "nguon": nguon, "dich": dich, "mode": mode, "lich": lich, "h": h,
            "model": x["model"], "metric": x["metric"],
            "p25": x["p25"], "p50": x["p50"], "p75": x["p75"], "iqr": x["iqr"],
            "n_chuoi": x["n_chuoi"], "n_loai": x["n_loai"],
            "n_dong_test": x["n_dong_test"],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true", help="chạy trọn 108 tổ hợp")
    ap.add_argument("--cap", default=None, help="ví dụ E1:E3, ngăn nhiều cặp bằng dấu phẩy")
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--lich", default=",".join(LICH))
    ap.add_argument("--horizons", default=",".join(map(str, HORIZONS)))
    ap.add_argument("--models", default=",".join(ML_NAMES))
    ap.add_argument("--features", default="data/features")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--resume", action="store_true",
                    help="bỏ qua tổ hợp (nguồn, đích, mode, lịch, h) đã có trong bảng")
    a = ap.parse_args()

    feat_dir, proc_dir, tab = ROOT / a.features, ROOT / a.processed, ROOT / a.tables
    caps = CAP if (a.all or not a.cap) else [tuple(x.split(":")) for x in a.cap.split(",")]
    modes = [x.strip().upper() for x in a.modes.split(",")]
    lichs = [x.strip() for x in a.lich.split(",")]
    hs = [int(x) for x in a.horizons.split(",")]
    models = [x.strip() for x in a.models.split(",")]

    chosen = pd.read_csv(tab / "chosen_gd3.csv")
    bl = pd.read_csv(tab / "baselines_gd3.csv")
    nrm = pd.read_csv(tab / "normalize_gd4.csv")
    nrm = nrm[nrm["mode"] == "N1"].set_index(["env", "series_id"])

    b0 = {e: doc_b0(e, proc_dir) for e in ENVS}
    y_goc = {e: bang_goc(e, proc_dir) for e in ENVS}
    d_mase = {e: mase_denominators_train(
        pd.read_parquet(proc_dir / f"{e}.parquet"), b0[e]) for e in ENVS}
    # Tầng CV chỉ dùng để lấy mẫu con của SVR (QĐ-014 điểm 2) và để đếm tổng số chuỗi.
    # Ngưỡng tính lại từ `cv_gd2.csv` mỗi lần chạy, không hardcode — QĐ-012 điểm 1.
    st = doc_cau_hinh_tang()
    bt = bang_tang(pd.read_csv(tab / "cv_gd2.csv"),
                   envs=ENVS, n_strata=int(st.get("n_strata", 3)))
    tang = {e: bt[bt["env"] == e].set_index("series_id")["tang"] for e in ENVS}
    n_chuoi_tong = {e: int(tang[e].shape[0]) for e in ENVS}

    p_out = tab / TEN_BANG
    da_co = set()
    if a.resume and p_out.exists():
        cu = pd.read_csv(p_out)
        da_co = set(map(tuple, cu[["nguon", "dich", "mode", "lich", "h"]]
                        .drop_duplicates().to_numpy()))

    run_dir = ROOT / "runs" / (datetime.now().strftime("%Y%m%d-%H%M%S")
                               + "_transfer_gd4")
    (run_dir / "config").mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "config").glob("*.yaml"):
        shutil.copy2(f, run_dir / "config" / f.name)

    print("\nTHÍ NGHIỆM B — transfer xuyên môi trường (protocol mục 14)")
    print(f"cặp   : {', '.join(f'{x}→{y}' for x, y in caps)}")
    print(f"chế độ: {', '.join(modes)} · lịch: {', '.join(lichs)} · h: {hs}")
    print(f"model : {', '.join(models)} (+ {len(BASELINE_NAMES)} baseline chép từ GĐ3)")
    print(f"run   : {run_dir.relative_to(ROOT)}\n")

    t0 = time.time()
    cham_test = []
    dong_moi: list[dict] = []

    # Model chỉ phụ thuộc (nguồn, mode, lịch, h) -> khớp một lần, dùng cho mọi đích.
    nguon_can = sorted({n for n, _ in caps})
    for nguon in nguon_can:
        dich_cua_nguon = [d for n, d in caps if n == nguon]
        for mode in modes:
            for lich in lichs:
                cot = cot_dac_trung(lich)
                for h in hs:
                    can_lam = [(d) for d in dich_cua_nguon
                               if (nguon, d, mode, lich, h) not in da_co]
                    if not can_lam:
                        continue

                    Xs = doc_ma_tran(nguon, mode, h, feat_dir)
                    off_s = offset(Xs["bucket"].to_numpy(), b0[nguon])
                    fit_ix = fit_mask(off_s, h)
                    X_tr = Xs.loc[fit_ix, cot].to_numpy(dtype="float64")
                    y_tr = Xs.loc[fit_ix, "target"].to_numpy(dtype="float64")
                    tang_tr = tang[nguon].reindex(
                        Xs.loc[fit_ix, "series_id"]).to_numpy()
                    print(f"{nguon}→{','.join(can_lam)} {mode} lịch={lich} h={h}: "
                          f"train {len(y_tr):,} dòng")

                    for ten in models:
                        ts = doc_sieu_tham_so(chosen, nguon, h, ten)
                        mo_hinh, n_dung, giay = khop_mot_model(
                            ten, X_tr, y_tr, ts, tang_tr)
                        print(f"   {ten:6} {json.dumps(ts, separators=(',', ':')):32}"
                              f" n_tr={n_dung:>9,}  khớp {giay:6.1f}s", flush=True)

                        for dich in can_lam:
                            Xd = doc_ma_tran(dich, mode, h, feat_dir)
                            off_d = offset(Xd["bucket"].to_numpy(), b0[dich])
                            te = split_masks(off_d, h)["test"]
                            T = Xd.loc[te]
                            sid = T["series_id"].to_numpy()
                            buc = T["bucket"].to_numpy()

                            yhat = mo_hinh.predict(T[cot].to_numpy(dtype="float64"))
                            cham_test.append(f"{nguon}->{dich}_{mode}_{lich}_h{h}_{ten}")

                            yhat_cpu = map_ve_cpu(yhat, mode, sid, buc,
                                                  y_goc[dich], nrm.loc[dich])
                            y_that = y_goc[dich].reindex(
                                pd.MultiIndex.from_arrays([sid, buc + h])).to_numpy()

                            ps = per_series_metrics(sid, y_that, yhat_cpu,
                                                    d=d_mase[dich])
                            g = gop(ps, n_chuoi_tong=n_chuoi_tong[dich])
                            for _, r in g.iterrows():
                                dong_moi.append({
                                    "nguon": nguon, "dich": dich, "mode": mode,
                                    "lich": lich, "h": h, "model": ten,
                                    "metric": r["metric"], "p25": r["p25"],
                                    "p50": r["p50"], "p75": r["p75"], "iqr": r["iqr"],
                                    "n_chuoi": r["n_chuoi"], "n_loai": r["n_loai"],
                                    "n_dong_test": int(len(T)),
                                })

                    for dich in can_lam:
                        dong_moi += dong_baseline(bl, nguon, dich, mode, lich, h)

                    # Ghi ngay sau mỗi (nguồn, mode, lịch, h) để dừng giữa chừng
                    # không mất việc đã làm.
                    ghi(p_out, dong_moi)
                    dong_moi = []

    ghi(p_out, dong_moi)
    giay = time.time() - t0
    _meta(run_dir, tab, caps, modes, lichs, hs, models, cham_test, giay)
    print(f"\nXong {giay/60:.1f} phút. Chạm test {len(cham_test)} lần.")
    print(f"Đã ghi: {p_out}")
    print(f"Snapshot: {run_dir.relative_to(ROOT)}")
    return 0


def ghi(p: Path, dong: list[dict]) -> None:
    if not dong:
        return
    df = pd.DataFrame(dong)[COT]
    if p.exists():
        cu = pd.read_csv(p)
        khoa = ["nguon", "dich", "mode", "lich", "h", "model", "metric"]
        bo = cu.set_index(khoa).index.isin(df.set_index(khoa).index)
        df = pd.concat([cu[~bo], df], ignore_index=True)
    df.to_csv(p, index=False)


def _meta(run_dir, tab, caps, modes, lichs, hs, models, cham, giay) -> None:
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, cwd=str(ROOT)).stdout.strip()
    except Exception:
        git = ""
    import sklearn
    meta = {
        "buoc": "GĐ4 bước 4 — Thí nghiệm B, transfer xuyên môi trường",
        "ngay": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv[1:],
        "cap": [f"{a}->{b}" for a, b in caps],
        "modes": modes, "lich": lichs, "horizons": hs, "models": models,
        "seed": SEED,
        "sieu_tham_so": "dùng lại GĐ3 theo môi trường NGUỒN (QĐ-016 điểm 3)",
        "baseline": "chép từ baselines_gd3.csv, mốc cố định của ĐÍCH (QĐ-016 điểm 4)",
        "so_lan_cham_test": len(cham),
        "cham_test_chi_tiet": cham,
        "git": git,
        "host": platform.node(),
        "phien_ban": {"python": platform.python_version(),
                      "pandas": pd.__version__, "numpy": np.__version__,
                      "sklearn": sklearn.__version__},
        "giay": round(giay, 1),
    }
    (run_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    for t in (TEN_BANG,):
        if (tab / t).exists():
            shutil.copy2(tab / t, run_dir / t)


if __name__ == "__main__":
    sys.exit(main())
