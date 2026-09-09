"""Sinh ma trận đặc trưng cho ba môi trường × ba horizon (protocol mục 8, mục 10).

    python scripts/build_features.py --env all
    python scripts/build_features.py --env E2 --horizons 1

Đọc `data/processed/{env}.parquet`, gọi `cwp.features.make_feature_matrix`, ghi ra
`data/features/{env}_h{h}.parquet` — đúng 22 cột: `series_id`, `bucket`, 19 đặc
trưng, `target`.

Việc lọc dòng nằm trọn trong `cwp.features`, script này không lọc thêm gì. Nhắc lại
điều dễ làm sai nhất (QĐ-010): lọc theo **luật cửa sổ** `[t-24, t]` sạch NaN và
`t+h` không NaN, **không** bằng `dropna()` trên ma trận đặc trưng — `dropna` lỏng
hơn vì 19 đặc trưng chỉ chạm 15 trong 25 điểm của cửa sổ.

Cuối lệnh, script **đối chiếu** số dòng với `valid_rows_h*` trong
`data/catalog.parquet` và thoát 1 nếu lệch. Đối chiếu là để **báo**, không phải để
sửa: lệch một dòng nghĩa là hiện thực sai chứ không phải nhiễu, và chỗ cần sửa là
`src/cwp/features/`, không phải đầu ra.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

from cwp.features import MATRIX_COLS, make_feature_matrix

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
ENVS = ["E1", "E2", "E3"]
HORIZONS = [1, 6, 12]


def neo_catalog(cat: pd.DataFrame | None, env: str, h: int) -> int | None:
    """Số dòng hợp lệ mà GĐ1 đã chốt cho `env` ở horizon `h`, hoặc None nếu chưa có."""
    if cat is None:
        return None
    giu = cat[(cat["env"] == env) & cat["kept"]]
    cot = f"valid_rows_h{h}"
    if giu.empty or cot not in giu.columns:
        return None
    return int(giu[cot].sum())


def sinh_mot_moi_truong(env: str, horizons: list[int], proc_dir: Path,
                        out_dir: Path, cat: pd.DataFrame | None) -> list[dict]:
    """Sinh và ghi ma trận đặc trưng của một môi trường, trả về các dòng báo cáo."""
    nguon = proc_dir / f"{env}.parquet"
    if not nguon.exists():
        raise SystemExit(
            f"Thiếu {nguon}. Chạy tiền xử lý GĐ1 trước: "
            "python -m cwp.preprocess.build --env all"
        )

    t0 = time.time()
    df = pd.read_parquet(nguon)
    print(f"{env}: đọc {len(df):,} điểm, {df['series_id'].nunique()} chuỗi "
          f"({time.time() - t0:.1f}s)")

    # Gọi thẳng make_feature_matrix cho từng horizon, không tự sắp xếp trước. Nó tự
    # chuẩn hoá và tự kiểm lưới; làm hộ nó chỉ tiết kiệm ~0,2s mỗi môi trường và đổi
    # lại việc sản phẩm đi một đường khác với đường mà tests/test_features.py kiểm.
    bao_cao = []
    for h in horizons:
        t1 = time.time()
        X = make_feature_matrix(df, h=h)

        assert list(X.columns) == MATRIX_COLS, "schema lệch khỏi protocol mục 8"

        dich = out_dir / f"{env}_h{h}.parquet"
        X.to_parquet(dich, index=False)

        neo = neo_catalog(cat, env, h)
        bao_cao.append({
            "env": env,
            "h": h,
            "dong": len(X),
            "neo": neo,
            "lech": None if neo is None else len(X) - neo,
            "chuoi": X["series_id"].nunique(),
            "mb": dich.stat().st_size / 1024 / 1024,
            "giay": time.time() - t1,
        })
        print(f"  h={h:<2} → {dich.name:<16} {len(X):>10,} dòng  "
              f"{bao_cao[-1]['mb']:>6.1f} MB  ({bao_cao[-1]['giay']:.1f}s)")

    return bao_cao


def in_bang(bao_cao: list[dict], co_neo: bool) -> int:
    """In bảng số dòng, trả về số chỗ lệch so với neo GĐ1."""
    print()
    print("=" * 74)
    print("SỐ DÒNG MA TRẬN ĐẶC TRƯNG")
    print("=" * 74)

    if co_neo:
        print(f"{'':<4} {'h':>3} {'số dòng':>12} {'neo GĐ1':>12} {'lệch':>8} "
              f"{'chuỗi':>7} {'MB':>7}")
    else:
        print(f"{'':<4} {'h':>3} {'số dòng':>12} {'chuỗi':>7} {'MB':>7}")

    lech = 0
    for r in bao_cao:
        if co_neo and r["neo"] is not None:
            dau = "khớp" if r["lech"] == 0 else f"{r['lech']:+,}"
            lech += r["lech"] != 0
            print(f"{r['env']:<4} {r['h']:>3} {r['dong']:>12,} {r['neo']:>12,} "
                  f"{dau:>8} {r['chuoi']:>7} {r['mb']:>7.1f}")
        else:
            print(f"{r['env']:<4} {r['h']:>3} {r['dong']:>12,} "
                  f"{r['chuoi']:>7} {r['mb']:>7.1f}")

    print("=" * 74)
    return lech


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default="all", choices=ENVS + ["all"])
    ap.add_argument("--horizons", default=",".join(map(str, HORIZONS)),
                    help="danh sách horizon, ngăn bằng dấu phẩy (mặc định 1,6,12)")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--out", default="data/features")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    a = ap.parse_args()

    envs = ENVS if a.env == "all" else [a.env]
    horizons = [int(x) for x in a.horizons.split(",")]
    proc_dir = ROOT / a.processed
    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)

    cat_path = ROOT / a.catalog
    cat = pd.read_parquet(cat_path) if cat_path.exists() else None
    if cat is None:
        print(f"CẢNH BÁO: không thấy {cat_path}, bỏ qua bước đối chiếu neo GĐ1.")

    print()
    print(f"SINH ĐẶC TRƯNG — protocol mục 8, QĐ-010")
    print(f"nguồn : {proc_dir}")
    print(f"đích  : {out_dir}")
    print()

    t0 = time.time()
    bao_cao = []
    for env in envs:
        bao_cao += sinh_mot_moi_truong(env, horizons, proc_dir, out_dir, cat)

    lech = in_bang(bao_cao, co_neo=cat is not None)
    print(f"{len(bao_cao)} tệp, {time.time() - t0:.1f}s tổng.")

    if cat is None:
        return 0
    if lech:
        print()
        print(f"CHƯA ĐẠT — {lech}/{len(bao_cao)} tệp lệch so với neo GĐ1.")
        print("Lệch NHIỀU hơn: nghi lọc bằng dropna() thay luật cửa sổ, hoặc "
              "min_periods=1.")
        print("Lệch ÍT hơn  : nghi quên groupby(series_id), hoặc nhầm chỉ số t+h.")
        print("Sửa src/cwp/features/ cho đúng docs/protocol.md mục 8. "
              "KHÔNG sửa đầu ra cho khớp số.")
        return 1

    print("Mọi tệp khớp tuyệt đối với neo GĐ1 (catalog.parquet).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
