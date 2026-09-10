"""Kiểm cổng GĐ3 tự động.

    python scripts/check_gd3.py

Thoát 0 nếu ĐẠT, 1 nếu chưa. Không sửa gì, chỉ đọc.

## Ba loại phép kiểm — và vì sao phải có ba

Ở GĐ1 và GĐ2, thước đo của A và bản hiện thực của B do **hai bên khác nhau** viết,
nên việc hai bên ra cùng con số là bằng chứng mạnh. Ở GĐ3, `reference_gd3.py` do cùng
một agent đã viết code B của GĐ2 soạn ra (QĐ-014 điểm 3), nên bằng chứng đó **yếu
hơn**: hai bản có thể cùng sai một kiểu.

Cách bù: đừng dựa vào một loại bằng chứng duy nhất.

| Loại | Phụ thuộc tính độc lập? | Bắt được gì |
|---|---|---|
| **A** — so với `reference_gd3.json` | **có** | lỗi gõ, lệch một dòng, dùng sai cột |
| **B** — đẳng thức tự thân | **không** | vi phạm quan hệ mà mọi bản đúng đều phải thoả |
| **C** — đáp án giải tích trên dữ liệu tính tay được | **không** | **hiểu sai định nghĩa** — kiểu lỗi hai bản cùng tác giả dễ cùng mắc |

Loại B và C không quan tâm hai bản có khớp nhau không. Chúng giữ nguyên giá trị kể cả
khi tính độc lập bằng không, nên **đừng bỏ chúng đi cho gọn**.

## Đọc gì

Theo hợp đồng ở QĐ-014 điểm 4:

- `results/tables/splits_gd3.csv` — `env, h, split, n_dong`
- `results/tables/baselines_gd3.csv` — `env, h, model, split, metric, p25, p50, p75,
  iqr, n_chuoi, n_loai, n_dong_dung, n_dong_test`

Loại C gọi thẳng `cwp.evaluation.metrics`, nên module đó phải bày ra năm hàm
`mae, rmse, smape, mase, r2` nhận mảng một chuỗi.
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
MODELS = ["naive", "ma6", "seasonal"]
METRICS = ["mae", "rmse", "smape", "mase", "r2"]
SPLITS = ["train", "val", "test"]

# 22 cột của ma trận đặc trưng (protocol mục 8 + QĐ-010). Chép cứng ở đây, KHÔNG
# import từ `cwp.features.spec`: thước đo mà đi hỏi bản bị đo thì đo cái gì.
MATRIX_COLS = [
    "series_id", "bucket",
    "lag_1", "lag_2", "lag_3", "lag_6", "lag_12", "lag_24",
    "roll_mean_6", "roll_std_6", "roll_min_6", "roll_max_6",
    "roll_mean_12", "roll_std_12", "roll_min_12", "roll_max_12",
    "diff_1", "hour_sin", "hour_cos", "dow_sin", "dow_cos", "target",
]


def tren_test(bl: pd.DataFrame) -> pd.DataFrame:
    """Chỉ giữ dòng của tập `test`.

    Hợp đồng QĐ-014 điểm 4 có cột `split`, và B được phép báo cả `train`/`val` để tự
    theo dõi. Nhưng tham chiếu của A **chỉ neo `test`** (mục 12: báo cáo trên test),
    nên mọi phép so loại A phải lọc trước — không lọc thì một tổ hợp có ba dòng và
    checker báo nhầm là "thiếu dòng".
    """
    return bl[bl["split"] == "test"] if "split" in bl.columns else bl

# Baseline không có yếu tố ngẫu nhiên nào, nên so ở mức chặt: chỉ được lệch do làm
# tròn của tệp tham chiếu (6 chữ số thập phân).
ATOL = 5e-6


class Report:
    def __init__(self):
        self.rows, self.failed = [], 0

    def add(self, group, item, status, detail=""):
        self.rows.append((group, item, status, detail))
        if status == FAIL:
            self.failed += 1

    def show(self):
        cur = None
        for g, item, st, detail in self.rows:
            if g != cur:
                print(f"\n── {g}")
                cur = g
            mark = {OK: "  ok  ", FAIL: " TRƯỢT", WARN: " cảnh báo"}[st]
            print(f"  [{mark}] {item}")
            if detail:
                print(f"           {detail}")
        print()
        print("=" * 70)
        if self.failed:
            print(f"CHƯA ĐẠT — {self.failed} mục trượt. Xem chi tiết bên trên.")
        else:
            print("ĐẠT — bộ máy đánh giá và ba baseline GĐ3 khớp tham chiếu.")
        print("=" * 70)
        return 1 if self.failed else 0


def gan(a, b):
    return abs(float(a) - float(b)) <= ATOL


# ============================================================ LOẠI A — so tham chiếu

def loai_a_so_dong(sp: pd.DataFrame, ref: dict, rep: Report):
    g = "A. So với tham chiếu — số dòng mỗi tập"
    lech = 0
    for env in ENVS:
        for h in HORIZONS:
            want = ref[env]["so_dong"][f"h{h}"]
            for s in SPLITS:
                r = sp[(sp.env == env) & (sp.h == h) & (sp.split == s)]
                if len(r) != 1:
                    rep.add(g, f"{env} h={h} {s}: có đúng một dòng", FAIL,
                            f"tìm thấy {len(r)} dòng trong splits_gd3.csv")
                    lech += 1
                    continue
                got, exp = int(r.iloc[0]["n_dong"]), int(want[s])
                if got != exp:
                    rep.add(g, f"{env} h={h} {s}: số dòng", FAIL,
                            f"B={got:,}  A={exp:,}  lệch {got - exp:+,} — nghi quên "
                            "purge dòng vắt ranh giới (QĐ-013 điểm 2), đó là RÒ RỈ")
                    lech += 1
    if not lech:
        rep.add(g, f"{len(ENVS) * len(HORIZONS) * len(SPLITS)} con số khớp tuyệt đối", OK)


def loai_a_baseline(bl: pd.DataFrame, ref: dict, rep: Report):
    g = "A. So với tham chiếu — ba baseline trên test"
    lech = []
    bl = tren_test(bl)
    for env in ENVS:
        for h in HORIZONS:
            for m in MODELS:
                a = ref[env]["baseline"][m][f"h{h}"]
                for k in METRICS:
                    r = bl[(bl.env == env) & (bl.h == h) & (bl.model == m)
                           & (bl.metric == k)]
                    if len(r) != 1:
                        lech.append(f"{env} h{h} {m}.{k}: thiếu dòng")
                        continue
                    want = a[k]["p50"]
                    got = r.iloc[0]["p50"]
                    if want is None:
                        continue
                    if not gan(got, want):
                        lech.append(f"{env} h{h} {m}.{k} B={got:.6f} A={want:.6f}")
    if lech:
        rep.add(g, "45 chỉ số p50 khớp tham chiếu", FAIL,
                "; ".join(lech[:4]) + ("…" if len(lech) > 4 else ""))
    else:
        rep.add(g, "45 chỉ số p50 (3 env × 3 h × 3 model × 5 chỉ số) khớp", OK)


def loai_a_dong_bo(bl: pd.DataFrame, ref: dict, rep: Report):
    """Tỉ lệ dòng bị bỏ — protocol mục 11 đòi xử lý hiện chứ không lặng lẽ."""
    g = "A. So với tham chiếu — dòng bị bỏ của từng baseline"
    lech = []
    bl = tren_test(bl)
    for env in ENVS:
        for h in HORIZONS:
            for m in MODELS:
                a = ref[env]["baseline"][m][f"h{h}"]
                r = bl[(bl.env == env) & (bl.h == h) & (bl.model == m)
                       & (bl.metric == "mae")]
                if len(r) != 1:
                    continue
                got = int(r.iloc[0]["n_dong_dung"])
                if got != int(a["n_dong_dung"]):
                    lech.append(f"{env} h{h} {m}: B={got:,} A={a['n_dong_dung']:,}")
    if lech:
        rep.add(g, "số dòng thực dùng khớp", FAIL,
                "; ".join(lech[:3]) + " — nghi lặng lẽ lấp giá trị thiếu")
    else:
        rep.add(g, "số dòng thực dùng khớp ở cả 27 tổ hợp", OK)


# ====================================================== LOẠI B — đẳng thức tự thân

def loai_b(sp: pd.DataFrame, bl: pd.DataFrame, cat: pd.DataFrame, rep: Report):
    """Quan hệ mà MỌI bản hiện thực đúng đều phải thoả, không cần tham chiếu."""
    g = "B. Đẳng thức tự thân (không cần tham chiếu)"
    bt = tren_test(bl)

    # B1 — purge: số dòng mất đi phải nằm trong khoảng bắt buộc
    #
    # Mỗi chuỗi có hai ranh giới (1612 và 1957). Với horizon h, dòng tại
    # t ∈ [b−h, b−1] có t+h rơi sang tập sau, nên bị loại: **nhiều nhất** 2h dòng mỗi
    # chuỗi. Ít hơn 2h là chuyện bình thường — dòng sát ranh giới có thể đã bị luật
    # NaN loại từ trước. Nên đây là BẤT ĐẲNG THỨC, không phải đẳng thức: bản trước
    # viết `==` sẽ báo trượt oan trên dữ liệu có NaN gần ranh giới.
    #
    # Hướng bắt lỗi vẫn nguyên vẹn: quên purge thì mất **0** dòng, và cận dưới ≥ 1
    # tóm được ngay. Con số chính xác do loại A ghim (27 số dòng), B1 chỉ là lưới
    # thứ hai không cần tham chiếu.
    xau = []
    for env in ENVS:
        n_chuoi = int(cat[(cat.env == env) & cat.kept].shape[0])
        for h in HORIZONS:
            tong = int(sp[(sp.env == env) & (sp.h == h)]["n_dong"].sum())
            hop_le = int(cat[(cat.env == env) & cat.kept][f"valid_rows_h{h}"].sum())
            mat, tran = hop_le - tong, n_chuoi * 2 * h
            if mat < 1:
                xau.append(f"{env} h{h}: mất {mat:,} dòng — không dòng nào bị purge, "
                           "nghi gán tập chỉ theo t mà quên t+h, đó là RÒ RỈ")
            elif mat > tran:
                xau.append(f"{env} h{h}: mất {mat:,} > trần {tran:,} "
                           f"(={n_chuoi} chuỗi × 2 ranh giới × {h})")
    if xau:
        rep.add(g, "B1 — số dòng bị purge trong khoảng [1, n_chuỗi × 2 × h]", FAIL,
                "; ".join(xau[:3]))
    else:
        rep.add(g, "B1 — số dòng bị purge nằm trong [1, n_chuỗi × 2 × h] ở cả 9 tổ hợp",
                OK)

    # B2 — RMSE >= MAE, luôn đúng theo bất đẳng thức Jensen
    xau = []
    for env in ENVS:
        for h in HORIZONS:
            for m in MODELS:
                q = lambda k: bt[(bt.env == env) & (bt.h == h) & (bt.model == m)
                                 & (bt.metric == k)]["p50"]
                a, b = q("mae"), q("rmse")
                if len(a) == 1 and len(b) == 1 and float(b.iloc[0]) < float(a.iloc[0]) - 1e-9:
                    xau.append(f"{env} h{h} {m}: rmse {b.iloc[0]:.4f} < mae {a.iloc[0]:.4f}")
    if xau:
        rep.add(g, "B2 — RMSE ≥ MAE", FAIL, "; ".join(xau[:3]))
    else:
        rep.add(g, "B2 — RMSE ≥ MAE ở cả 27 tổ hợp (bất đẳng thức Jensen)", OK)

    # B3 — SMAPE nằm trong [0, 200]
    s = bl[bl.metric == "smape"]["p50"].astype(float)
    if len(s) and (s.min() < -1e-9 or s.max() > 200 + 1e-9):
        rep.add(g, "B3 — SMAPE ∈ [0, 200]", FAIL,
                f"nhỏ nhất {s.min():.4f}, lớn nhất {s.max():.4f}")
    else:
        rep.add(g, "B3 — SMAPE ∈ [0, 200]", OK)

    # B4 — R² <= 1
    r = bl[bl.metric == "r2"]["p50"].astype(float)
    if len(r) and r.max() > 1 + 1e-9:
        rep.add(g, "B4 — R² ≤ 1", FAIL, f"lớn nhất {r.max():.6f}")
    else:
        rep.add(g, "B4 — R² ≤ 1", OK)

    # B5 — p25 <= p50 <= p75
    xau = int(((bl["p25"] > bl["p50"] + 1e-9) | (bl["p50"] > bl["p75"] + 1e-9)).sum())
    if xau:
        rep.add(g, "B5 — p25 ≤ p50 ≤ p75", FAIL, f"{xau} dòng vi phạm")
    else:
        rep.add(g, "B5 — p25 ≤ p50 ≤ p75 ở mọi dòng", OK)

    # B6 — n_dong_dung <= n_dong_test, và n_dong_test khớp splits
    xau = []
    for env in ENVS:
        for h in HORIZONS:
            t = sp[(sp.env == env) & (sp.h == h) & (sp.split == "test")]
            if len(t) != 1:
                continue
            n_test = int(t.iloc[0]["n_dong"])
            for m in MODELS:
                r = bt[(bt.env == env) & (bt.h == h) & (bt.model == m)
                       & (bt.metric == "mae")]
                if len(r) != 1:
                    continue
                dung, co = int(r.iloc[0]["n_dong_dung"]), int(r.iloc[0]["n_dong_test"])
                if co != n_test:
                    xau.append(f"{env} h{h} {m}: n_dong_test {co:,} ≠ splits {n_test:,}")
                elif dung > co:
                    xau.append(f"{env} h{h} {m}: dùng {dung:,} > có {co:,}")
    if xau:
        rep.add(g, "B6 — n_dong_dung ≤ n_dong_test = số dòng test", FAIL,
                "; ".join(xau[:3]))
    else:
        rep.add(g, "B6 — n_dong_dung ≤ n_dong_test, và khớp bảng splits", OK)


def loai_b_dac_trung(feat_dir: Path, rep: Report):
    """B7 — ma trận đặc trưng mà GĐ3 ăn vào vẫn đúng 22 cột của mục 8.

    `check_gd2.py` đã kiểm điều này khi đóng GĐ2, nhưng GĐ3 có thể sinh lại
    `data/features/`. Thêm một đặc trưng ngoài mục 8 là **đổi giao thức**, và nếu chỉ
    kiểm ở GĐ2 thì lần sinh lại nào sau đó cũng lọt. Đọc schema thôi, không đọc dữ
    liệu, nên rẻ.
    """
    g = "B. Đẳng thức tự thân (không cần tham chiếu)"
    if not feat_dir.exists():
        rep.add(g, "B7 — ma trận đặc trưng đúng 22 cột", WARN,
                f"chưa có {feat_dir} — chạy scripts/build_features.py --env all")
        return

    import pyarrow.parquet as pq

    can = set(MATRIX_COLS)
    xau, dem = [], 0
    for env in ENVS:
        for h in HORIZONS:
            f = feat_dir / f"{env}_h{h}.parquet"
            if not f.exists():
                xau.append(f"thiếu {f.name}")
                continue
            co = set(pq.ParquetFile(f).schema_arrow.names)
            dem += 1
            if co != can:
                thua, thieu = sorted(co - can), sorted(can - co)
                xau.append(f"{f.name}: thừa {thua} thiếu {thieu}")
    if xau:
        rep.add(g, "B7 — ma trận đặc trưng đúng 22 cột (mục 8 + QĐ-010)", FAIL,
                "; ".join(xau[:3]) + " — cột thừa là ĐỔI GIAO THỨC")
    else:
        rep.add(g, f"B7 — {dem} ma trận đặc trưng đúng 22 cột, không thừa không thiếu", OK)


# ============================================ LOẠI C — đáp án giải tích, tính tay được

def loai_c(rep: Report, bat_buoc: bool, src: Path):
    """Gọi thẳng `cwp.evaluation.metrics` trên ca tính tay được.

    Đây là loại phép kiểm bắt được **hiểu sai định nghĩa** — kiểu lỗi mà hai bản do
    cùng một người viết dễ cùng mắc, nên loại A không thấy.

    `bat_buoc=False` khi B chưa sinh bảng nào: lúc đó thiếu module là trạng thái đang
    làm dở, báo **cảnh báo** chứ không đánh trượt — cùng cách đối xử với việc thiếu
    bảng. `bat_buoc=True` khi B đã nộp bảng: khi ấy thiếu module là trượt thật, vì
    bảng phải sinh ra từ chính module đó.
    """
    g = "C. Đáp án giải tích (không cần tham chiếu)"
    muc = FAIL if bat_buoc else WARN
    sys.path.insert(0, str(src))
    try:
        from cwp.evaluation import metrics as M
    except Exception as e:
        rep.add(g, "import được cwp.evaluation.metrics", muc,
                f"{type(e).__name__}: {e} — chưa viết, hoặc chưa bày ra 5 hàm "
                "mae/rmse/smape/mase/r2 (QĐ-014 điểm 4)")
        return

    thieu = [t for t in ("mae", "rmse", "smape", "mase", "r2") if not hasattr(M, t)]
    if thieu:
        rep.add(g, "module bày ra đủ 5 hàm", muc, f"thiếu {thieu}")
        return
    rep.add(g, "import được và có đủ 5 hàm", OK)

    a = np.array
    ca = [
        ("C1 dự đoán đúng tuyệt đối → MAE 0",
         lambda: M.mae(a([1., 2, 3, 4]), a([1., 2, 3, 4])), 0.0),
        ("C2 lệch đều 1 đơn vị → MAE 1",
         lambda: M.mae(a([1., 2, 3]), a([2., 3, 4])), 1.0),
        ("C3 RMSE phạt lỗi lớn: y=[0,0] ŷ=[0,2] → √2",
         lambda: M.rmse(a([0., 0]), a([0., 2])), np.sqrt(2)),
        ("C4 SMAPE của |y−ŷ| = trung bình: y=[1] ŷ=[3] → 100",
         lambda: M.smape(a([1.]), a([3.])), 100.0),
        ("C5 **SMAPE khi y = ŷ = 0 phải là 0, không phải NaN**",
         lambda: M.smape(a([0., 0]), a([0., 0])), 0.0),
        ("C6 MASE = MAE / d: MAE 1, d 0,5 → 2",
         lambda: M.mase(a([1., 2, 3]), a([2., 3, 4]), 0.5), 2.0),
        ("C7 R² của dự đoán hằng bằng trung bình → 0",
         lambda: M.r2(a([1., 2, 3, 4]), a([2.5, 2.5, 2.5, 2.5])), 0.0),
        ("C8 R² của dự đoán đúng tuyệt đối → 1",
         lambda: M.r2(a([1., 2, 3, 4]), a([1., 2, 3, 4])), 1.0),
    ]
    for ten, f, mong in ca:
        try:
            got = float(f())
        except Exception as e:
            rep.add(g, ten, FAIL, f"{type(e).__name__}: {e}")
            continue
        if not (np.isfinite(got) and abs(got - mong) < 1e-9):
            rep.add(g, ten, FAIL, f"ra {got}, phải là {mong}")
        else:
            rep.add(g, ten, OK)

    # Hai ca phải trả **NaN**, không phải một con số bịa ra, và cũng không phải `inf`.
    # `inf` là bẫy: `np.isfinite(inf)` cũng là False, nên nếu kiểm bằng "không hữu hạn"
    # thì bản chia cho 0 rồi trả `inf` sẽ lọt — mà `inf` lọt vào trung vị thì hỏng cả
    # cột. Phải hỏi đúng `isnan`.
    nan_ca = [
        ("C9 **MASE khi d = 0 phải là NaN**, không phải vô cực hay 0",
         lambda: M.mase(a([1., 2, 3]), a([2., 3, 4]), 0.0)),
        ("C10 **R² khi chuỗi test hằng (SS_tot = 0) phải là NaN**",
         lambda: M.r2(a([1., 1, 1]), a([2., 2, 2]))),
    ]
    for ten, f in nan_ca:
        try:
            got = float(f())
        except Exception as e:
            rep.add(g, ten, FAIL, f"ném {type(e).__name__} thay vì trả NaN: {e}")
            continue
        if not np.isnan(got):
            rep.add(g, ten, FAIL, f"ra {got}, phải là NaN "
                    + ("(`inf` KHÔNG được coi là NaN — nó vẫn trôi vào trung vị)"
                       if np.isinf(got) else ""))
        else:
            rep.add(g, ten, OK)


# ------------------------------------------------------------------- tiến độ

def tien_do(root: Path):
    items = [("src/cwp/evaluation/splits.py", "chia tập theo bucket + purge"),
             ("src/cwp/evaluation/metrics.py", "5 chỉ số theo QĐ-013"),
             ("src/cwp/models/baselines.py", "3 baseline mục 11"),
             ("results/tables/splits_gd3.csv", "bảng số dòng mỗi tập"),
             ("results/tables/baselines_gd3.csv", "bảng chỉ số 3 baseline"),
             ("tests/test_splits.py", "test chia tập"),
             ("tests/test_metrics.py", "test 5 chỉ số"),
             ("tests/test_baselines.py", "test 3 baseline")]

    def co(p):
        q = root / p
        return q.exists() and (q.stat().st_size > 0 if q.is_file() else True)

    xong = [(p, d) for p, d in items if co(p)]
    thieu = [(p, d) for p, d in items if not co(p)]
    print()
    print("─" * 70)
    print(f"TIẾN ĐỘ GĐ3: {len(xong)}/{len(items)} sản phẩm")
    print("─" * 70)
    for p, d in xong:
        print(f"  [xong ] {p:<36} {d}")
    for p, d in thieu:
        print(f"  [thiếu] {p:<36} {d}")
    print()
    print("Đặc tả: docs/protocol.md mục 9–13, QĐ-013 và QĐ-014.")
    print("Số phải khớp: research-log/gate-gd3.md mục 2.")


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default="results/tables")
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--features", default="data/features")
    ap.add_argument("--src", default="src",
                    help="cây nguồn cho loại C; đổi được để test chính công cụ này")
    a = ap.parse_args()

    tab = ROOT / a.tables
    ref_path = tab / "reference_gd3.json"

    print()
    print("KIỂM CỔNG GĐ3 — research-log/gate-gd3.md")
    print(f"bảng      : {tab}")
    print(f"tham chiếu: {ref_path}")

    rep = Report()
    g0 = "0. Tiền đề"

    sp_path, bl_path = tab / "splits_gd3.csv", tab / "baselines_gd3.csv"
    da_nop = sp_path.exists() and bl_path.exists()

    # Loại C chạy được kể cả khi B chưa sinh bảng nào — chạy trước để luôn có thông
    # tin, vì nó không phụ thuộc tham chiếu. Mức nghiêm khắc tuỳ B đã nộp hay chưa.
    loai_c(rep, bat_buoc=da_nop, src=(Path(a.src) if Path(a.src).is_absolute() else ROOT / a.src))

    if not ref_path.exists():
        rep.add(g0, "Có tham chiếu GĐ3 của A", FAIL,
                f"thiếu {ref_path} — chạy scripts/reference_gd3.py --env all")
        rep.show()
        tien_do(ROOT)
        return 1
    ref = {r["env"]: r for r in json.loads(ref_path.read_text(encoding="utf-8"))}
    rep.add(g0, f"Có tham chiếu GĐ3 của A ({len(ref)} môi trường)", OK)

    cat_path = ROOT / a.catalog
    if not cat_path.exists():
        rep.add(g0, "Đọc được catalog GĐ1", FAIL, f"thiếu {cat_path}")
        rep.show()
        tien_do(ROOT)
        return 1
    cat = pd.read_parquet(cat_path)
    rep.add(g0, f"Đọc được catalog GĐ1 ({len(cat):,} dòng)", OK)

    thieu = [p.name for p in (sp_path, bl_path) if not p.exists()]
    if thieu:
        rep.add(g0, "Có đủ hai bảng của B", FAIL,
                f"thiếu {thieu} — trạng thái BÌNH THƯỜNG khi B chưa làm xong. "
                "Hợp đồng tên tệp và cột ở QĐ-014 điểm 4")
        rep.show()
        tien_do(ROOT)
        return 1

    sp = pd.read_csv(sp_path)
    bl = pd.read_csv(bl_path)
    rep.add(g0, f"Đọc được splits_gd3.csv ({len(sp)} dòng) và "
                f"baselines_gd3.csv ({len(bl)} dòng)", OK)

    loai_a_so_dong(sp, ref, rep)
    loai_a_baseline(bl, ref, rep)
    loai_a_dong_bo(bl, ref, rep)
    loai_b(sp, bl, cat, rep)
    loai_b_dac_trung(ROOT / a.features, rep)

    code = rep.show()
    tien_do(ROOT)
    return code


if __name__ == "__main__":
    sys.exit(main())
