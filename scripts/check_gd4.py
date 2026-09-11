"""Kiểm cổng GĐ4 — ba chế độ chuẩn hoá và ma trận transfer (gate-gd4.md).

    python scripts/check_gd4.py

Ba loại phép kiểm, **không loại nào thay được loại nào**:

| Loại | Phụ thuộc tính độc lập? | Bắt được gì |
|---|---|---|
| **A** — so `reference_gd4.json` | **có** | lỗi gõ, lệch một dòng, dùng sai cột |
| **B** — đẳng thức tự thân | **không** | vi phạm quan hệ mà mọi bản đúng đều thoả |
| **C** — đáp án giải tích | **không** | **hiểu sai định nghĩa** |

Ở GĐ4, loại C nặng ký hơn hẳn ba giai đoạn trước. Ba bất biến của QĐ-016 điểm 5 đúng
vì **toán học** — `naive` và `ma6` bất biến dưới z-score vì z-score là affine, và
`naive` dưới sai phân với `Δ̂ = 0` quay về đúng persistence. Chúng không quan tâm ai
viết code hay hai bản có khớp nhau không.

Và đó là chỗ cần nhất: `research-plan.md` gọi bước chuẩn hoá là *"chỗ dễ sai nhất toàn
dự án"*, còn `giai-thich-chuan-hoa.md` mục 5 cảnh báo lỗi ở đó **không báo lỗi, chỉ làm
số đẹp lên**. Loại A không bắt được kiểu đó nếu cả hai bản cùng sai — `E1_830` ở GĐ3 là
bằng chứng sống.

Công cụ này **cố ý không import gì từ `cwp.preprocess.normalize`** ngoài phần loại C —
thước đo mà đi hỏi bản bị đo thì đo cái gì.
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
MODES = ["N0", "N1", "N2"]
LICH = ["co", "khong"]
CAP = [("E1", "E2"), ("E2", "E1"), ("E1", "E3"),
       ("E3", "E1"), ("E2", "E3"), ("E3", "E2")]
BASELINE = ["naive", "ma6", "seasonal"]
METRICS = ["mae", "rmse", "smape", "mase", "r2"]

W = 2304
N_TRAIN = 1612

# Thống kê chuẩn hoá không có yếu tố ngẫu nhiên nào, nên so ở mức chặt.
ATOL = 5e-6
# Ngưỡng của ba bất biến — QĐ-016 điểm 5.
NGUONG_BAT_BIEN = 1e-9


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
            print("ĐẠT — bước chuẩn hoá và ma trận transfer GĐ4 khớp tham chiếu.")
        print("=" * 70)
        return 1 if self.failed else 0


def gan(a, b, atol=ATOL):
    return abs(float(a) - float(b)) <= atol


# ==================================================== LOẠI C — đáp án giải tích

def loai_c(rep: Report, bat_buoc: bool, src: Path):
    """Bảy đáp án tính tay được, chạy thẳng trên `cwp.preprocess.normalize`.

    Chạy **kể cả khi B chưa sinh bảng nào** — nó không cần tham chiếu và không cần
    kết quả. Mức nghiêm khắc tuỳ B đã nộp hay chưa.
    """
    g = "C. Đáp án giải tích (không cần tham chiếu)"
    muc = FAIL if bat_buoc else WARN

    sys.path.insert(0, str(src))
    try:
        from cwp.preprocess.normalize import bien_doi, map_nguoc, thong_ke_train
    except Exception as e:
        rep.add(g, "import được `cwp.preprocess.normalize`", muc,
                f"{type(e).__name__}: {e} — cần ba hàm `thong_ke_train`, "
                "`bien_doi`, `map_nguoc` (hợp đồng ở brief-gd4-b.md Bước 1)")
        return
    finally:
        if sys.path and sys.path[0] == str(src):
            sys.path.pop(0)

    rep.add(g, "import được và có đủ 3 hàm", OK)

    # Chuỗi tính tay: train là 1612 điểm, phần sau khác hẳn để bẫy lỗi cửa sổ.
    rng = np.random.default_rng(0)
    y = np.empty(W)
    y[:N_TRAIN] = 10.0 + rng.normal(0, 2.0, N_TRAIN)
    y[N_TRAIN:] = 500.0 + rng.normal(0, 50.0, W - N_TRAIN)

    def kiem(ten, dieu_kien, chi_tiet=""):
        rep.add(g, ten, OK if dieu_kien else muc, "" if dieu_kien else chi_tiet)

    # C1 — mu, sd lấy đúng cửa sổ train.
    try:
        mu, sd = thong_ke_train(y)
        mu_dung = float(np.nanmean(y[:N_TRAIN]))
        sd_dung = float(np.nanstd(y[:N_TRAIN], ddof=1))
        kiem("C1 `mu`, `sd` tính trên đúng cửa sổ train `[0, 1612)`, ddof = 1",
             gan(mu, mu_dung) and gan(sd, sd_dung),
             f"nhận mu={mu:.6f} sd={sd:.6f}, đúng phải là "
             f"mu={mu_dung:.6f} sd={sd_dung:.6f}")
    except Exception as e:
        kiem("C1 `mu`, `sd` tính trên đúng cửa sổ train", False, f"{type(e).__name__}: {e}")
        return

    # C2 — đổi y SAU 1612 thì mu, sd không đổi. Phép kiểm rò rỉ T1.
    y2 = y.copy()
    y2[N_TRAIN:] = -999.0
    mu2, sd2 = thong_ke_train(y2)
    kiem("C2 **đổi `y` ở bucket ≥ 1612 thì `mu`, `sd` KHÔNG đổi** — chống rò rỉ",
         gan(mu, mu2) and gan(sd, sd2),
         f"mu {mu:.6f} → {mu2:.6f}, sd {sd:.6f} → {sd2:.6f}; "
         "thống kê đang nhìn thấy phần sau cửa sổ train")

    # C3, C4, C5 — ba bất biến của QĐ-016 điểm 5.
    try:
        z = bien_doi(y, "N1")
        d = bien_doi(y, "N2")
    except Exception as e:
        kiem("C3 biến đổi N1/N2 chạy được", False, f"{type(e).__name__}: {e}")
        return

    lech = float(np.nanmax(np.abs(map_nguoc(z, y, "N1") - y)))
    kiem(f"C3 **bất biến `naive`: N0 ≡ N1 sau map ngược** (lệch {lech:.2e})",
         lech < NGUONG_BAT_BIEN,
         f"lệch {lech:.3e} ≥ {NGUONG_BAT_BIEN:.0e} — nghi quên map ngược, hoặc "
         "`mu`/`sd` của chuỗi khác")

    # ma6 trong không gian z, map ngược, so với ma6 trên thang gốc.
    def ma6(v):
        out = np.full_like(v, np.nan)
        for t in range(6, len(v)):
            out[t] = np.mean(v[t - 6:t])
        return out

    lech_ma6 = float(np.nanmax(np.abs(map_nguoc(ma6(z), y, "N1") - ma6(y))))
    kiem(f"C4 **bất biến `ma6`: N0 ≡ N1 sau map ngược** (lệch {lech_ma6:.2e})",
         lech_ma6 < NGUONG_BAT_BIEN,
         f"lệch {lech_ma6:.3e} — trung bình của z phải là z của trung bình")

    lech_n2 = float(np.nanmax(np.abs(map_nguoc(np.zeros_like(d), y, "N2") - y)))
    kiem(f"C5 **bất biến `naive` N2 với `Δ̂ = 0` ≡ N0** (lệch {lech_n2:.2e})",
         lech_n2 == 0.0,
         f"lệch {lech_n2:.3e}, phải bằng 0 TUYỆT ĐỐI — `y_t + 0` không mất bit nào")

    # C6 — chuỗi phẳng: sd = 0 thì N1 không xác định, KHÔNG phải 0, KHÔNG epsilon.
    phang = np.full(W, 4.25)
    _, sd_phang = thong_ke_train(phang)
    zp = bien_doi(phang, "N1")
    kiem("C6 **chuỗi `sd = 0` thì N1 là NaN**, không phải 0 và không thêm epsilon",
         sd_phang == 0.0 and bool(np.all(np.isnan(zp))),
         f"sd={sd_phang}, N1 ra {np.unique(zp[np.isfinite(zp)])[:3]}")

    # C7 — N2 mất đúng điểm đầu, và giá trị đúng bằng hiệu liền kề.
    n2_ok = (np.isnan(d[0])
             and np.allclose(d[1:], y[1:] - y[:-1], equal_nan=True))
    kiem("C7 N2 là hiệu liền kề, bucket 0 thành NaN", n2_ok,
         "sai phân không khớp `y_t − y_{t−1}`, hoặc không để NaN ở bucket đầu")


# ================================================== LOẠI A — so với tham chiếu

def loai_a_thong_ke(nz: pd.DataFrame, ref: dict, rep: Report):
    """Trung vị `mu`, `sd` và số chuỗi `sd = 0` — gate mục 2.3."""
    g = "A. So tham chiếu — thống kê chuẩn hoá N1"
    lech = []
    for env in ENVS:
        if env not in ref:
            continue
        con = nz[(nz["env"] == env) & (nz["mode"] == "N1")]
        if con.empty:
            lech.append(f"{env}: không có dòng N1 nào")
            continue
        r = ref[env]["n1"]
        for cot, khoa in (("mu", "mu_p50"), ("sd", "sd_p50")):
            b = float(np.nanmedian(con[cot].to_numpy("float64")))
            if not gan(b, r[khoa]):
                lech.append(f"{env} {cot}_p50 B={b:.6f} A={r[khoa]:.6f}")
        n0 = int((con["sd"].to_numpy("float64") == 0).sum())
        if n0 != r["n_chuoi_sd_bang_0"]:
            lech.append(f"{env} số chuỗi sd=0 B={n0} A={r['n_chuoi_sd_bang_0']}")
    rep.add(g, "trung vị `mu`, `sd` và số chuỗi `sd = 0` khớp ở ba môi trường",
            FAIL if lech else OK, "; ".join(lech[:4]))


def loai_a_so_dong(feat_dir: Path, ref: dict, rep: Report):
    """Số dòng hợp lệ trên test theo từng chế độ — gate mục 2.2, 27 con số."""
    g = "A. So tham chiếu — số dòng hợp lệ mỗi chế độ"
    lech, thieu = [], []
    for env in ENVS:
        if env not in ref:
            continue
        for mode in MODES:
            for h in HORIZONS:
                p = feat_dir / f"{env}_{mode}_h{h}.parquet"
                if not p.exists():
                    thieu.append(p.name)
                    continue
                import pyarrow.parquet as pq
                n = pq.ParquetFile(p).metadata.num_rows
                # Ma trận chứa cả ba tập; neo của A là số dòng TEST nên chỉ so được
                # khi B ghi thêm cột. Ở đây so tổng ba tập qua tham chiếu.
                a = ref[env]["so_dong"][mode][f"h{h}"]
                tong = a["train"] + a["val"] + a["test"]
                if n < tong:
                    lech.append(f"{env} {mode} h{h}: {n:,} < tổng ba tập {tong:,}")
    if thieu:
        rep.add(g, "có đủ 27 ma trận đặc trưng", FAIL,
                f"thiếu {len(thieu)} tệp, ví dụ {thieu[:3]}")
    else:
        rep.add(g, "có đủ 27 ma trận đặc trưng", OK)
        rep.add(g, "số dòng mỗi ma trận không nhỏ hơn tổng ba tập của tham chiếu",
                FAIL if lech else OK, "; ".join(lech[:4]))


def loai_a_bat_bien(iv: pd.DataFrame, ref: dict, rep: Report):
    """Ba bất biến đo trên dữ liệu thật — gate mục 2.4."""
    g = "A. So tham chiếu — ba bất biến trên dữ liệu thật"
    xau = []
    for env in ENVS:
        if env not in ref:
            continue
        con = iv[iv["env"] == env]
        for ten, khoa, nguong in (
            ("naive_N0_vs_N1", "naive_N0_vs_N1", NGUONG_BAT_BIEN),
            ("ma6_N0_vs_N1", "ma6_N0_vs_N1", NGUONG_BAT_BIEN),
            ("naive_N0_vs_N2", "naive_N0_vs_N2", 0.0),
        ):
            d = con[con["bat_bien"] == ten]
            if d.empty:
                xau.append(f"{env}: thiếu `{ten}`")
                continue
            v = float(d["lech_toi_da"].iloc[0])
            if nguong == 0.0:
                if v != 0.0:
                    xau.append(f"{env} {ten} = {v:.3e}, phải bằng 0 tuyệt đối")
            elif not (v < nguong):
                xau.append(f"{env} {ten} = {v:.3e} ≥ {nguong:.0e}")
    rep.add(g, "ba bất biến đạt ngưỡng ở cả ba môi trường",
            FAIL if xau else OK, "; ".join(xau[:4]))


# ================================================ LOẠI B — đẳng thức tự thân

def loai_b_so_dong(feat_dir: Path, cat: pd.DataFrame, rep: Report):
    """Quan hệ giữa ba chế độ, không cần tham chiếu — gate mục 2.2 ba phép kiểm."""
    g = "B. Đẳng thức tự thân"
    import pyarrow.parquet as pq

    def dem(env, mode, h):
        p = feat_dir / f"{env}_{mode}_h{h}.parquet"
        return pq.ParquetFile(p).metadata.num_rows if p.exists() else None

    # B1 — N0 khớp tuyệt đối neo GĐ1/GĐ2 trong catalog.
    xau = []
    for env in ENVS:
        giu = cat[(cat["env"] == env) & cat["kept"]]
        for h in HORIZONS:
            n = dem(env, "N0", h)
            neo = int(giu[f"valid_rows_h{h}"].sum()) if len(giu) else None
            if n is None or neo is None:
                continue
            if n != neo:
                xau.append(f"{env} h{h}: N0 {n:,} ≠ neo GĐ2 {neo:,}")
    rep.add(g, "B1 — số dòng N0 khớp **tuyệt đối** neo GĐ2 (đường sinh đặc trưng "
               "không đổi khi thêm chế độ)", FAIL if xau else OK, "; ".join(xau[:4]))

    # B2 — N1 bằng đúng N0 (z-score không sinh thêm NaN khi sd > 0).
    xau = []
    for env in ENVS:
        for h in HORIZONS:
            a, b = dem(env, "N0", h), dem(env, "N1", h)
            if a is not None and b is not None and a != b:
                xau.append(f"{env} h{h}: N0 {a:,} ≠ N1 {b:,}")
    rep.add(g, "B2 — N1 bằng đúng N0 ở cả 9 tổ hợp", FAIL if xau else OK,
            "; ".join(xau[:4]) + ("  (lệch nghĩa là có chuỗi sd = 0, hoặc `mu`/`sd` "
                                  "tính trên cửa sổ khác)" if xau else ""))

    # B3 — N2 phải mất ÍT NHẤT một dòng mỗi chuỗi.
    #
    # Sửa 2026-09-11. Bản đầu đòi N2 **không mất dòng nào** ở E1/E2 và giải thích
    # "mất nghĩa là sai phân bắc cầu qua ranh giới chuỗi". Điều đó **ngược**: nó
    # thưởng cho đúng cái lỗi nó định bắt.
    #
    # Chứng minh mọi bản hiện thực ĐÚNG đều phải mất dòng. Gọi `t*` là dòng hợp lệ
    # đầu tiên của một chuỗi ở N0. N2 đòi thêm `y[t*-25]` và `y[t*+h-1]`.
    #   - `y[t*+h-1]` là NaN  -> `t*` trượt N2.
    #   - `y[t*+h-1]` hữu hạn VÀ `y[t*-25]` hữu hạn -> cửa sổ `[t*-25, t*-1]` sạch và
    #     target `y[(t*-1)+h]` hữu hạn, nên `t*-1` đã hợp lệ ở N0 — mâu thuẫn với việc
    #     `t*` là dòng đầu.
    # Vậy `t*` luôn trượt N2: **mất >= số chuỗi**, ở mọi môi trường và mọi horizon.
    #
    # Nếu sai phân bắc cầu, `z` ở đầu chuỗi thứ 2 trở đi lấy được giá trị cuối của
    # chuỗi trước nên không NaN, và tổng mất tụt xuống 1. Đó là thứ phép kiểm này bắt.
    #
    # Kiểm bằng **bucket nhỏ nhất của từng chuỗi**, không bằng tổng số dòng mất.
    # Đếm tổng là điều kiện cần chứ chưa đủ: đo trên dữ liệu thật, bản bắc cầu của E2
    # mất 306 dòng trong khi E2 có 302 chuỗi — nó vẫn vượt ngưỡng đếm và lọt. Bản bắc
    # cầu của E1 thì mất 26 so với 735 nên ngưỡng đếm bắt được. Phép kiểm chỉ đúng ở
    # một môi trường là phép kiểm chưa đúng.
    #
    # Với bản đúng: mọi chuỗi đều mất dòng đầu, nên `min(bucket)` ở N2 luôn LỚN HƠN ở
    # N0. Với bản bắc cầu: chuỗi thứ 2 trở đi giữ nguyên dòng đầu, `min(bucket)` bằng
    # nhau — lộ ra ngay, bất kể môi trường có bao nhiêu lỗ hổng.
    #
    # Chỉ kiểm ở h=1 cho rẻ: lỗi bắc cầu không phụ thuộc horizon.
    xau = []
    for env in ENVS:
        pa = feat_dir / f"{env}_N0_h1.parquet"
        pb = feat_dir / f"{env}_N2_h1.parquet"
        if not (pa.exists() and pb.exists()):
            continue
        c = ["series_id", "bucket"]
        a = pd.read_parquet(pa, columns=c).groupby("series_id")["bucket"].min()
        b = pd.read_parquet(pb, columns=c).groupby("series_id")["bucket"].min()
        j = a.to_frame("n0").join(b.to_frame("n2"), how="left")
        giu_nguyen = int((j["n2"] <= j["n0"]).sum())
        if giu_nguyen:
            xau.append(f"{env}: {giu_nguyen}/{len(j)} chuỗi giữ nguyên dòng đầu ở N2")
    rep.add(g, "B3 — ở N2, dòng hợp lệ ĐẦU TIÊN của mỗi chuỗi phải biến mất (còn "
               "nghĩa là sai phân bắc cầu qua ranh giới chuỗi)",
            FAIL if xau else OK, "; ".join(xau[:4]))


def loai_b_transfer(tr: pd.DataFrame, cat: pd.DataFrame, rep: Report):
    """Quan hệ phải đúng ở mọi bản hiện thực, trên bảng transfer."""
    g = "B. Đẳng thức tự thân"

    # B4 — đủ tổ hợp.
    co = set(map(tuple, tr[["nguon", "dich", "mode", "lich", "h"]].drop_duplicates()
                 .to_numpy()))
    can = {(a, b, m, l, h) for a, b in CAP for m in MODES for l in LICH
           for h in HORIZONS}
    thieu = can - co
    rep.add(g, f"B4 — đủ {len(can)} tổ hợp (6 cặp × 3 chế độ × 2 biến thể lịch × 3 h)",
            FAIL if thieu else OK,
            f"thiếu {len(thieu)}, ví dụ {sorted(thieu)[:3]}" if thieu else "")

    r = tr.pivot_table(index=["nguon", "dich", "mode", "lich", "h", "model"],
                       columns="metric", values="p50")

    def vi_pham(dk, ten):
        n = int((~dk).sum())
        rep.add(g, ten, FAIL if n else OK, f"{n} dòng vi phạm" if n else "")

    if {"rmse", "mae"} <= set(r.columns):
        vi_pham(r["rmse"] >= r["mae"] - 1e-9,
                "B5 — RMSE ≥ MAE (bất đẳng thức Jensen)")
    if "smape" in r.columns:
        vi_pham((r["smape"] >= -1e-9) & (r["smape"] <= 200 + 1e-9),
                "B6 — SMAPE ∈ [0, 200]")
    if "r2" in r.columns:
        vi_pham(r["r2"] <= 1 + 1e-9, "B7 — R² ≤ 1")
    vi_pham((tr["p25"] <= tr["p50"] + 1e-9) & (tr["p50"] <= tr["p75"] + 1e-9),
            "B8 — p25 ≤ p50 ≤ p75 ở mọi dòng")

    # B9 — n_chuoi + n_loai bằng số chuỗi của môi trường ĐÍCH.
    tong = {e: int(((cat["env"] == e) & cat["kept"]).sum()) for e in ENVS}
    xau = []
    for dich, gg in tr.groupby("dich"):
        if dich not in tong:
            continue
        sai = gg[(gg["n_chuoi"] + gg["n_loai"]) != tong[dich]]
        if len(sai):
            xau.append(f"{dich}: {len(sai)} dòng ≠ {tong[dich]}")
    rep.add(g, "B9 — `n_chuoi + n_loai` bằng số chuỗi của môi trường đích",
            FAIL if xau else OK, "; ".join(xau[:3]))

    # B10 — ba baseline giống nhau ở cả ba chế độ (QĐ-016 điểm 4).
    xau = []
    bl = tr[tr["model"].isin(BASELINE)]
    for khoa, gg in bl.groupby(["nguon", "dich", "lich", "h", "model", "metric"]):
        v = gg.set_index("mode")["p50"].reindex(MODES).dropna()
        if len(v) > 1 and (v.max() - v.min()) > ATOL:
            xau.append(f"{khoa[1]} h{khoa[3]} {khoa[4]}.{khoa[5]}: "
                       f"lệch {v.max() - v.min():.2e} giữa ba chế độ")
    rep.add(g, "B10 — ba baseline **giống nhau ở cả ba chế độ** (QĐ-016 điểm 4)",
            FAIL if xau else OK, "; ".join(xau[:3]))


# ------------------------------------------------------------------ tiến độ

SAN_PHAM = [
    ("src/cwp/preprocess/normalize.py", "ba chế độ + map ngược"),
    ("tests/test_normalize.py", "ba bất biến QĐ-016 điểm 5"),
    ("scripts/pha_gd4.py", "phá code kiểm ngược, 5 kiểu"),
    ("scripts/run_transfer.py", "6 cặp × 3 chế độ × 2 lịch × 3 h"),
    ("results/tables/normalize_gd4.csv", "mu, sd từng chuỗi"),
    ("results/tables/invariants_gd4.csv", "ba bất biến trên dữ liệu thật"),
    ("results/tables/transfer_gd4.csv", "ma trận transfer"),
]


def tien_do(root: Path, feat_dir: Path):
    print()
    print("─" * 70)
    xong = 0
    dong = []
    for rel, mo_ta in SAN_PHAM:
        co = (root / rel).exists()
        xong += co
        dong.append(("xong " if co else "thiếu", rel, mo_ta))
    n_feat = sum((feat_dir / f"{e}_{m}_h{h}.parquet").exists()
                 for e in ENVS for m in MODES for h in HORIZONS)
    print(f"TIẾN ĐỘ GĐ4: {xong}/{len(SAN_PHAM)} sản phẩm, "
          f"{n_feat}/27 ma trận đặc trưng")
    print("─" * 70)
    for tt, rel, mo_ta in dong:
        print(f"  [{tt}] {rel:<42} {mo_ta}")
    print()
    print("Đặc tả: docs/protocol.md mục 14, QĐ-016.")
    print("Số phải khớp: research-log/gate-gd4.md mục 2.")


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
    feat_dir = ROOT / a.features if not Path(a.features).is_absolute() else Path(a.features)
    src = Path(a.src) if Path(a.src).is_absolute() else ROOT / a.src
    ref_path = tab / "reference_gd4.json"

    print()
    print("KIỂM CỔNG GĐ4 — research-log/gate-gd4.md")
    print(f"bảng      : {tab}")
    print(f"tham chiếu: {ref_path}")

    rep = Report()
    g0 = "0. Tiền đề"

    nz_path = tab / "normalize_gd4.csv"
    iv_path = tab / "invariants_gd4.csv"
    tr_path = tab / "transfer_gd4.csv"
    da_nop = nz_path.exists() and iv_path.exists()

    # Loại C chạy trước và chạy được kể cả khi B chưa sinh bảng nào.
    loai_c(rep, bat_buoc=da_nop, src=src)

    if not ref_path.exists():
        rep.add(g0, "Có tham chiếu GĐ4 của A", FAIL,
                f"thiếu {ref_path} — chạy scripts/reference_gd4.py")
        rep.show()
        tien_do(ROOT, feat_dir)
        return 1
    ref = {r["env"]: r for r in
           json.loads(ref_path.read_text(encoding="utf-8"))["moi_truong"]}
    rep.add(g0, f"Có tham chiếu GĐ4 của A ({len(ref)} môi trường)", OK)

    cat_path = ROOT / a.catalog
    if not cat_path.exists():
        rep.add(g0, "Đọc được catalog GĐ1", FAIL, f"thiếu {cat_path}")
        rep.show()
        tien_do(ROOT, feat_dir)
        return 1
    cat = pd.read_parquet(cat_path)
    rep.add(g0, f"Đọc được catalog GĐ1 ({len(cat):,} dòng)", OK)

    thieu = [p.name for p in (nz_path, iv_path) if not p.exists()]
    if thieu:
        rep.add(g0, "Có đủ bảng chuẩn hoá của B", FAIL,
                f"thiếu {thieu} — trạng thái BÌNH THƯỜNG khi B chưa làm xong. "
                "Hợp đồng tên tệp và cột ở brief-gd4-b.md Bước 0")
        rep.show()
        tien_do(ROOT, feat_dir)
        return 1

    nz = pd.read_csv(nz_path)
    iv = pd.read_csv(iv_path)
    rep.add(g0, f"Đọc được normalize_gd4.csv ({len(nz):,} dòng) và "
                f"invariants_gd4.csv ({len(iv)} dòng)", OK)

    loai_a_thong_ke(nz, ref, rep)
    loai_a_bat_bien(iv, ref, rep)
    loai_a_so_dong(feat_dir, ref, rep)
    loai_b_so_dong(feat_dir, cat, rep)

    if tr_path.exists():
        tr = pd.read_csv(tr_path)
        rep.add(g0, f"Đọc được transfer_gd4.csv ({len(tr):,} dòng)", OK)
        loai_b_transfer(tr, cat, rep)
    else:
        rep.add(g0, "Có transfer_gd4.csv", FAIL,
                f"thiếu {tr_path.name} — Bước 4 của brief-gd4-b.md chưa chạy")

    code = rep.show()
    tien_do(ROOT, feat_dir)
    return code


if __name__ == "__main__":
    sys.exit(main())
