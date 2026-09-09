"""Kiểm cổng GĐ2 tự động.

Đối chiếu ma trận đặc trưng của B với `results/tables/reference_gd2.json` do A sinh
độc lập, và với neo cứng `valid_rows_h*` trong `data/catalog.parquet` đã chốt ở GĐ1.
Theo danh sách ở research-log/gate-gd2.md mục 3.

B chạy trước khi báo xong. A chạy khi nghiệm thu. Cùng một lệnh, cùng một kết quả.

    python scripts/check_gd2.py
    python scripts/check_gd2.py --features data/features --ref results/tables

Thoát 0 nếu ĐẠT, 1 nếu chưa. Không sửa gì, chỉ đọc.

Kiểm được bằng máy: mục 3.2 (đủ 19 đặc trưng, đúng tên), R2 (rolling loại điểm hiện
tại), R3 (không bắc cầu qua ranh giới chuỗi), R4 (số dòng khớp neo), bẫy múi giờ.
KHÔNG kiểm được ở đây: R1 (đổi tương lai, đặc trưng không đổi) nằm ở
`tests/test_features.py` vì cần gọi lại hàm sinh đặc trưng; và hình phân phối target
thì A duyệt bằng mắt.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

OK, FAIL, WARN = "ok", "fail", "warn"
ENVS = ["E1", "E2", "E3"]
HORIZONS = [1, 6, 12]
GRID = 300
WINDOW = 8 * 86400 // GRID
MAXLAG = 24

# protocol mục 8, tên cột chốt theo QĐ-010
LAG_COLS = [f"lag_{k}" for k in (1, 2, 3, 6, 12, 24)]
ROLL_COLS = [f"roll_{s}_{w}" for w in (6, 12) for s in ("mean", "std", "min", "max")]
CAL_COLS = ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
FEATURES = LAG_COLS + ROLL_COLS + ["diff_1"] + CAL_COLS
ID_COLS = ["series_id", "bucket"]
TARGET = "target"

assert len(FEATURES) == 19

# Vân tay đặc trưng so ở mức chặt: hai bên tính trên cùng dữ liệu, cùng quy ước, nên
# chỉ được lệch do làm tròn của tệp tham chiếu (6 chữ số thập phân).
ATOL, RTOL = 1e-6, 1e-6


class Report:
    def __init__(self):
        self.rows = []
        self.failed = 0

    def add(self, group, item, status, detail=""):
        self.rows.append((group, item, status, detail))
        if status == FAIL:
            self.failed += 1

    def show(self):
        cur = None
        for group, item, status, detail in self.rows:
            if group != cur:
                print(f"\n── {group}")
                cur = group
            mark = {OK: "  ok  ", FAIL: " TRƯỢT", WARN: " cảnh báo"}[status]
            print(f"  [{mark}] {item}")
            if detail:
                print(f"           {detail}")
        print()
        print("=" * 66)
        if self.failed:
            print(f"CHƯA ĐẠT — {self.failed} mục trượt. Xem chi tiết bên trên.")
        else:
            print("ĐẠT — bộ đặc trưng GĐ2 khớp protocol mục 8, không phát hiện rò rỉ.")
        print("=" * 66)
        return 1 if self.failed else 0


def close(a, b):
    return abs(a - b) <= ATOL + RTOL * abs(b)


# ------------------------------------------------------------------ mục 3.2

def check_schema(df, env, h, rep):
    """Đúng 19 đặc trưng, không thừa không thiếu, cộng cột định danh và target."""
    g = "1. Schema ma trận đặc trưng"
    tag = f"{env} h={h}"
    cols = list(df.columns)
    want = set(FEATURES) | set(ID_COLS) | {TARGET}

    thieu = [c for c in want if c not in cols]
    thua = [c for c in cols if c not in want]

    if thieu:
        rep.add(g, f"{tag}: đủ cột bắt buộc", FAIL, f"thiếu {thieu}")
        return False
    rep.add(g, f"{tag}: đủ 19 đặc trưng + {ID_COLS} + {TARGET}", OK)

    if thua:
        rep.add(g, f"{tag}: không có đặc trưng ngoài protocol", FAIL,
                f"thừa {thua} — thêm đặc trưng là đổi giao thức, xem "
                "docs/research-plan.md quy tắc phối hợp 1")
        return False
    rep.add(g, f"{tag}: không có đặc trưng ngoài protocol mục 8", OK)
    return True


# ------------------------------------------------------------------- mục 3.3

def check_rows(df, env, h, cat, rep):
    """R4 — số dòng khớp TUYỆT ĐỐI neo cứng của GĐ1."""
    g = "2. R4 — số dòng khớp neo GĐ1"
    k = cat[(cat["env"] == env) & cat["kept"]]
    want = int(k[f"valid_rows_h{h}"].sum())
    got = len(df)
    if got == want:
        rep.add(g, f"{env} h={h}: {got:,} dòng", OK)
        return True

    thua = got - want
    if thua > 0:
        goi_y = ("lọc bằng dropna() trên đặc trưng thay vì luật cửa sổ [t-24, t] "
                 "(QĐ-010), hoặc min_periods=1")
    else:
        goi_y = "quên groupby(series_id), hoặc nhầm chỉ số target t+h"
    rep.add(g, f"{env} h={h}: số dòng", FAIL,
            f"B={got:,}  neo={want:,}  lệch {thua:+,} — nghi {goi_y}")
    return False


def check_no_nan(df, env, h, rep):
    """Dòng đã lọc thì không được còn NaN ở bất kỳ đặc trưng nào."""
    g = "2. R4 — số dòng khớp neo GĐ1"
    bad = [c for c in FEATURES + [TARGET] if df[c].isna().any()]
    if bad:
        rep.add(g, f"{env} h={h}: không còn NaN sau khi lọc", FAIL,
                f"còn NaN ở {bad[:5]}{'...' if len(bad) > 5 else ''}")
        return False
    rep.add(g, f"{env} h={h}: không còn NaN sau khi lọc", OK)
    return True


def check_boundary(df, env, ref, rep):
    """R3 — không bắc cầu qua ranh giới chuỗi.

    Cửa sổ 8 ngày là toàn cục nên mọi chuỗi cùng bắt đầu ở `b0` (protocol mục 7).
    Dòng hợp lệ sớm nhất của **mỗi** chuỗi vì thế không thể sớm hơn `b0 + 24`: cần
    đủ 24 bucket lịch sử ngay trong chuỗi đó.

    Nếu lag và rolling tính xuyên ranh giới chuỗi, chuỗi thứ hai trở đi sẽ mượn được
    lịch sử từ đuôi chuỗi trước và sinh ra dòng ngay tại `b0` — đúng thứ phép kiểm
    này bắt.
    """
    g = "3. R3 — ranh giới chuỗi"
    b0 = ref.get("b0")
    if b0 is None:
        rep.add(g, f"{env}: có b0 trong tham chiếu", FAIL, "reference_gd2.json thiếu b0")
        return False

    som_nhat_cho_phep = int(b0) + MAXLAG
    dau = df.groupby("series_id")["bucket"].min()
    vi_pham = dau[dau < som_nhat_cho_phep]

    if len(vi_pham):
        rep.add(g, f"{env}: mọi chuỗi có đủ {MAXLAG} bucket lịch sử riêng", FAIL,
                f"{len(vi_pham)} chuỗi có dòng sớm hơn bucket {som_nhat_cho_phep} "
                f"(sớm nhất {int(vi_pham.min())}) — nghi thiếu groupby(series_id), "
                "lịch sử đang chảy từ chuỗi trước sang")
        return False

    rep.add(g, f"{env}: {len(dau)} chuỗi, chuỗi nào cũng đủ {MAXLAG} bucket lịch sử riêng", OK)
    return True


def check_rolling_convention(df, env, h, rep):
    """R2 — rolling loại điểm hiện tại, và min/max phải bao được lag.

    Không tính lại rolling từ y (ma trận đã lọc không còn đủ lịch sử), mà kiểm các
    bất biến đại số bắt buộc đúng nếu cửa sổ là [t-w, t-1]:

      - roll_min_6 <= lag_1 <= roll_max_6   (lag_1 nằm TRONG cửa sổ quá khứ)
      - roll_min_6 <= roll_mean_6 <= roll_max_6
      - cửa sổ 12 bao cửa sổ 6: roll_min_12 <= roll_min_6, roll_max_12 >= roll_max_6

    Nếu B quên `.shift(1)` thì cửa sổ thành [t-w+1, t], vẫn thoả ba bất biến trên
    nhưng sẽ chứa y_t — bắt bằng `diff_1` ở kiểm kế tiếp.
    """
    g = "4. R2 — quy ước cửa sổ rolling"
    tag = f"{env} h={h}"
    eps = 1e-9
    kiem = [
        ("lag_1 nằm trong [roll_min_6, roll_max_6]",
         (df["roll_min_6"] <= df["lag_1"] + eps) & (df["lag_1"] <= df["roll_max_6"] + eps)),
        ("roll_mean_6 nằm trong [min, max]",
         (df["roll_min_6"] <= df["roll_mean_6"] + eps) & (df["roll_mean_6"] <= df["roll_max_6"] + eps)),
        ("cửa sổ 12 bao cửa sổ 6",
         (df["roll_min_12"] <= df["roll_min_6"] + eps) & (df["roll_max_12"] >= df["roll_max_6"] - eps)),
    ]
    ok_all = True
    for ten, m in kiem:
        n_bad = int((~m).sum())
        if n_bad:
            rep.add(g, f"{tag}: {ten}", FAIL, f"{n_bad:,} dòng vi phạm")
            ok_all = False
    if ok_all:
        rep.add(g, f"{tag}: ba bất biến cửa sổ rolling", OK)
    return ok_all


def check_shift_one(df, env, h, rep):
    """R2 (tiếp) — cửa sổ rolling KHÔNG được chứa y_t.

    `y_t = lag_1 + diff_1` tính lại được từ chính ma trận. Nếu B quên `.shift(1)`,
    cửa sổ 6 thành [t-5, t] nên luôn chứa y_t, tức
    `roll_min_6 <= y_t <= roll_max_6` đúng với MỌI dòng. Làm đúng thì bất đẳng thức
    đó bị phá ở một tỉ lệ đáng kể — y_t nằm ngoài biên quá khứ mỗi khi chuỗi vừa lập
    đỉnh hoặc đáy mới.
    """
    g = "4. R2 — quy ước cửa sổ rolling"
    tag = f"{env} h={h}"
    y_t = df["lag_1"] + df["diff_1"]
    eps = 1e-9
    trong = ((df["roll_min_6"] - eps <= y_t) & (y_t <= df["roll_max_6"] + eps))
    ti_le = float(trong.mean())

    # Đo trên bản tham chiếu: làm ĐÚNG ra 78,9% (E1), 78,2% (E2), 66,1% (E3);
    # quên `.shift(1)` ra đúng 100,0000% ở cả ba. Ngưỡng đặt giữa hai vùng đó.
    if ti_le > 0.999:
        rep.add(g, f"{tag}: cửa sổ rolling loại điểm hiện tại", FAIL,
                f"y_t nằm trong [roll_min_6, roll_max_6] ở {ti_le:.4%} số dòng — "
                "dấu hiệu quên .shift(1), cửa sổ đang là [t-5, t]")
        return False
    rep.add(g, f"{tag}: cửa sổ rolling loại điểm hiện tại "
               f"(y_t lọt biên quá khứ {ti_le:.2%})", OK)
    return True


# ------------------------------------------------------------------- mục 3.4

def check_calendar(df, env, ref, rep):
    """Bẫy múi giờ — QĐ-010.

    `bucket * 300` là epoch với E1/E2, là giây-từ-đầu-trace với E3. Dù nghĩa khác
    nhau, công thức là một, nên kiểm được: sin/cos phải tái lập đúng từ bucket.
    """
    g = "5. Bẫy — mốc thời gian và đặc trưng lịch"
    t = df["bucket"].to_numpy(dtype="int64") * GRID
    hour = (t // 3600) % 24
    dow = ((t // 86400) + 4) % 7
    want = {
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "dow_sin": np.sin(2 * np.pi * dow / 7),
        "dow_cos": np.cos(2 * np.pi * dow / 7),
    }
    sai = [c for c, v in want.items()
           if not np.allclose(df[c].to_numpy(), v, atol=1e-9)]
    if sai:
        rep.add(g, f"{env}: đặc trưng lịch suy đúng từ bucket", FAIL,
                f"lệch ở {sai} — nghi bucket bị đánh số lại từ 0 theo từng chuỗi, "
                "hoặc sai gốc dow (QĐ-010: epoch 1970-01-01 là thứ Năm)")
        return False

    rep.add(g, f"{env}: đặc trưng lịch suy đúng từ bucket", OK)
    if not ref.get("moc_lich_that", True):
        rep.add(g, f"{env}: mốc thời gian là tương đối, không phải epoch", WARN,
                "đúng theo QĐ-010 — hour là giờ kể từ đầu trace, pha chưa biết, "
                "dow không diễn giải được theo lịch tuần")
    return True


# ------------------------------------------------------------- vân tay số học

def check_fingerprint(df, env, ref, rep):
    """So mean và std từng đặc trưng với bản hiện thực độc lập của A (trên h=1)."""
    g = "6. Vân tay đặc trưng so với tham chiếu của A"
    ref_f = ref.get("dac_trung", {})
    if not ref_f:
        rep.add(g, f"{env}: có vân tay trong reference_gd2.json", FAIL,
                "chạy scripts/reference_gd2.py --env all --out results/tables/reference_gd2.json")
        return False

    lech = []
    for c in FEATURES:
        if c not in ref_f:
            lech.append(f"{c}: thiếu trong tham chiếu")
            continue
        m, s = float(df[c].mean()), float(df[c].std(ddof=1))
        if not close(m, ref_f[c]["mean"]):
            lech.append(f"{c}.mean B={m:.6f} A={ref_f[c]['mean']}")
        if not close(s, ref_f[c]["std"]):
            lech.append(f"{c}.std B={s:.6f} A={ref_f[c]['std']}")

    if lech:
        rep.add(g, f"{env} h=1: 19 đặc trưng khớp tham chiếu", FAIL,
                "; ".join(lech[:4]) + ("..." if len(lech) > 4 else "")
                + " — nếu chỉ lệch ở roll_std thì nghi ddof (QĐ-010 chốt ddof=1)")
        return False
    rep.add(g, f"{env} h=1: 19 đặc trưng khớp tham chiếu (mean và std)", OK)
    return True


# ------------------------------------------------------------------- tiến độ

def tien_do(root, feat_dir):
    items = [("src/cwp/features/", "module sinh đặc trưng"),
             ("tests/test_features.py", "test rò rỉ R1–R4")]
    items += [(f"{feat_dir}/{e}_h{h}.parquet", f"ma trận {e} h={h}")
              for e in ENVS for h in HORIZONS]
    items += [("results/figures/", "hình phân phối, ACF, burstiness")]
    def co(p):
        q = root / p
        if not q.exists():
            return False
        # Thư mục rỗng không tính là xong — `src/cwp/features/` chỉ có __init__.py
        # rỗng thì vẫn là chưa làm.
        if q.is_dir():
            return any(f.stat().st_size > 0 for f in q.rglob("*") if f.is_file())
        return True

    done = [(p, d) for p, d in items if co(p)]
    todo = [(p, d) for p, d in items if not co(p)]
    print()
    print("─" * 66)
    print(f"TIẾN ĐỘ GĐ2: {len(done)}/{len(items)} sản phẩm")
    print("─" * 66)
    for p, d in done:
        print(f"  [xong ] {p:<34} {d}")
    for p, d in todo:
        print(f"  [thiếu] {p:<34} {d}")
    print()
    print("Đặc tả: docs/protocol.md mục 8 và QĐ-010.")
    print("Số phải khớp: research-log/gate-gd2.md mục 2.")


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default="data/features")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--ref", default="results/tables")
    a = ap.parse_args()

    feat_dir = ROOT / a.features
    cat_path = ROOT / a.catalog
    ref_path = ROOT / a.ref / "reference_gd2.json"

    print()
    print("KIỂM CỔNG GĐ2 — research-log/gate-gd2.md")
    print(f"đặc trưng  : {feat_dir}")
    print(f"tham chiếu : {ref_path}")

    rep = Report()
    g0 = "0. Tiền đề"

    if not ref_path.exists():
        rep.add(g0, "Có tham chiếu GĐ2 của A", FAIL,
                f"thiếu {ref_path} — chạy scripts/reference_gd2.py")
        rep.show()
        tien_do(ROOT, a.features)
        return 1
    refs = {r["env"]: r for r in json.loads(ref_path.read_text(encoding="utf-8"))}
    rep.add(g0, f"Có tham chiếu GĐ2 của A ({len(refs)} môi trường)", OK)

    if not cat_path.exists():
        rep.add(g0, "Đọc được catalog GĐ1 (neo cứng)", FAIL, f"thiếu {cat_path}")
        rep.show()
        tien_do(ROOT, a.features)
        return 1
    cat = pd.read_parquet(cat_path)
    rep.add(g0, f"Đọc được catalog GĐ1 ({len(cat):,} dòng)", OK)

    thieu = [f"{e}_h{h}.parquet" for e in ENVS for h in HORIZONS
             if not (feat_dir / f"{e}_h{h}.parquet").exists()]
    if thieu:
        rep.add(g0, "Có đủ 9 ma trận đặc trưng", FAIL,
                f"thiếu {len(thieu)}: {thieu[:3]}{'...' if len(thieu) > 3 else ''} — "
                "trạng thái BÌNH THƯỜNG khi B chưa làm xong")
        rep.show()
        tien_do(ROOT, a.features)
        return 1
    rep.add(g0, "Có đủ 9 ma trận đặc trưng", OK)

    for env in ENVS:
        ref = refs.get(env, {})
        for h in HORIZONS:
            df = pd.read_parquet(feat_dir / f"{env}_h{h}.parquet")
            if not check_schema(df, env, h, rep):
                continue
            check_rows(df, env, h, cat, rep)
            check_no_nan(df, env, h, rep)
            check_rolling_convention(df, env, h, rep)
            check_shift_one(df, env, h, rep)
            if h == 1:
                check_boundary(df, env, ref, rep)
                check_calendar(df, env, ref, rep)
                check_fingerprint(df, env, ref, rep)

    code = rep.show()
    tien_do(ROOT, a.features)
    return code


if __name__ == "__main__":
    sys.exit(main())
