"""Kiểm cổng GĐ1 tự động.

Đối chiếu sản phẩm của B với số liệu tham chiếu do A sinh độc lập, theo ngưỡng ghi
trong research-log/gate-gd1.md mục 3.3. Kiểm cả schema lẫn số liệu.

B chạy trước khi báo xong. A chạy khi nghiệm thu. Cùng một lệnh, cùng một kết quả.

    python scripts/check_gd1.py
    python scripts/check_gd1.py --catalog data/catalog.parquet --ref results/tables

Thoát 0 nếu ĐẠT, 1 nếu chưa. Không sửa gì, chỉ đọc.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]

# Schema bắt buộc — protocol.md mục 6b
CATALOG_COLS = {
    "env": "object",
    "series_id": "object",
    "kept": "bool",
    "reject_reason": "object",
    "n_points": "int",
    "n_interp": "int",
    "valid_rows_h1": "int",
    "valid_rows_h6": "int",
    "valid_rows_h12": "int",
    "mean": "float",
    "p50": "float",
    "std": "float",
    "n_clipped": "int",
    "built_on": "object",
    "built_at": "object",
}
REASONS = {"", "ngoai_cua_so", "gan_chet", "hang", "it_dong"}
ENVS = ["E1", "E2", "E3"]

# Ngưỡng sai lệch cho phép — gate-gd1.md mục 3.3
TOL = {
    "chuoi_vao": 0.0,       # phải khớp tuyệt đối
    "chuoi_con_lai": 0.02,
    "loai": 0.05,
    "dong_h12": 0.05,
    "ti_le_noi_suy": 0.05,
    "ti_le_clip": 0.01,
    "target_mean": 0.02,
    "target_p50": 0.02,
}

OK, FAIL, WARN = "ĐẠT", "TRƯỢT", "CẢNH BÁO"


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
            print("ĐẠT — sản phẩm GĐ1 khớp tham chiếu trong ngưỡng cho phép.")
        print("=" * 66)
        return 1 if self.failed else 0


def rel_diff(got, want):
    if want in (None, 0):
        return 0.0 if got in (None, 0) else float("inf")
    return abs(got - want) / abs(want)


def check_schema(cat, rep):
    g = "1. Schema catalog.parquet"
    cols = set(cat.columns)
    missing = [c for c in CATALOG_COLS if c not in cols]
    if missing:
        rep.add(g, "Đủ cột bắt buộc", FAIL, f"thiếu: {', '.join(missing)}")
    else:
        rep.add(g, f"Đủ {len(CATALOG_COLS)} cột bắt buộc", OK)

    # Thiếu cột thì vẫn kiểm tiếp những gì kiểm được, để B thấy HẾT vấn đề trong
    # một lần chạy thay vì sửa từng lỗi rồi chạy lại.
    if "reject_reason" in cols:
        bad = set(cat["reject_reason"].fillna("").unique()) - REASONS
        rep.add(g, "Giá trị reject_reason hợp lệ", FAIL if bad else OK,
                f"giá trị lạ: {bad}" if bad else "")

    if "env" in cols:
        envs = set(cat["env"].unique())
        rep.add(g, "Đủ ba môi trường", FAIL if set(ENVS) - envs else OK,
                f"thiếu: {set(ENVS) - envs}" if set(ENVS) - envs else "")

    if "series_id" in cols:
        dup = int(cat["series_id"].duplicated().sum())
        rep.add(g, "series_id không trùng", FAIL if dup else OK,
                f"{dup} định danh bị trùng" if dup else "")

    # Bẫy Rnd: E2 phải có phần tháng trong định danh.
    # Chỉ bắt buộc với chuỗi ĐƯỢC GIỮ — đó là những chuỗi sẽ đi vào huấn luyện và
    # là nơi va chạm định danh gây rò rỉ. Chuỗi bị loại chỉ cảnh báo.
    e2_keep = (cat[(cat.env == "E2") & cat.kept]
               if {"env", "series_id", "kept"} <= cols else cat.iloc[:0])
    if len(e2_keep):
        bad = e2_keep[~e2_keep["series_id"].astype(str).str.match(r"^E2_\d{4}-\d+_")]
        rep.add(g, "E2 giữ lại có tháng trong series_id (bẫy Rnd trùng tên)",
                FAIL if len(bad) else OK,
                f"{len(bad)} chuỗi sai, ví dụ: {bad['series_id'].iloc[0]}" if len(bad) else "")
    e2_rej = (cat[(cat.env == "E2") & ~cat.kept]
              if {"env", "series_id", "kept"} <= cols else cat.iloc[:0])
    if len(e2_rej):
        bad_r = e2_rej[~e2_rej["series_id"].astype(str).str.match(r"^E2_\d{4}-\d+_")]
        if len(bad_r):
            rep.add(g, "E2 bị loại cũng nên có tháng trong series_id", WARN,
                    f"{len(bad_r)} chuỗi thiếu — không chặn, nhưng nên thống nhất")

    # E3 phải dùng đúng danh sách máy đã đóng băng — QĐ-009.
    # Trước đây A và B tự chọn mẫu riêng và chỉ trùng 56/500.
    e3 = (cat[cat.env == "E3"]
          if {"env", "series_id"} <= cols else cat.iloc[:0])
    frozen_path = ROOT / "config" / "e3_machines.txt"
    if len(e3) and frozen_path.exists():
        frozen = {ln.strip() for ln in frozen_path.read_text(encoding="utf-8").splitlines()
                  if ln.strip() and not ln.startswith("#")}
        got = {sid[3:] if sid.startswith("E3_") else sid
               for sid in e3["series_id"].astype(str)}
        missing, extra = frozen - got, got - frozen
        if missing or extra:
            rep.add(g, "E3 dùng đúng danh sách máy đã đóng băng", FAIL,
                    f"trùng {len(frozen & got)}/{len(frozen)} — thiếu {len(missing)}, "
                    f"thừa {len(extra)}. Phải đọc config/e3_machines.txt (QĐ-009), "
                    "không tự chọn mẫu.")
        else:
            rep.add(g, f"E3 dùng đúng {len(frozen)} máy đã đóng băng", OK)

    if {"kept", "reject_reason"} <= cols:
        inconsistent = int(((cat["kept"]) & (cat["reject_reason"].fillna("") != "")).sum())
        inconsistent += int(((~cat["kept"]) & (cat["reject_reason"].fillna("") == "")).sum())
        rep.add(g, "kept khớp reject_reason", FAIL if inconsistent else OK,
                f"{inconsistent} dòng mâu thuẫn" if inconsistent else "")

    # Đủ cột để đối chiếu số hay không
    return {"env", "series_id", "kept", "reject_reason", "n_points", "n_interp",
            "valid_rows_h12", "mean"} <= cols


def summarize(cat, env):
    d = cat[cat.env == env]
    k = d[d.kept]
    reasons = d[~d.kept]["reject_reason"].fillna("").value_counts()
    n_pts = int(k["n_points"].sum())
    n_int = int(k["n_interp"].sum())
    # trung bình có trọng số theo số điểm, tương đương gộp toàn bộ
    w = k["n_points"].where(k["n_points"] > 0, 0)
    mean = float((k["mean"] * w).sum() / w.sum()) if w.sum() else None
    return {
        "chuoi_vao": len(d),
        "chuoi_con_lai": len(k),
        "loai_ngoai_cua_so": int(reasons.get("ngoai_cua_so", 0)),
        "loai_gan_chet": int(reasons.get("gan_chet", 0)),
        "loai_hang": int(reasons.get("hang", 0)),
        "loai_it_dong": int(reasons.get("it_dong", 0)),
        "dong_h12": int(k["valid_rows_h12"].sum()),
        "ti_le_noi_suy_pct": round(n_int / n_pts * 100, 3) if n_pts else 0.0,
        "target_mean": round(mean, 4) if mean is not None else None,
    }


def check_provenance(cat, rep):
    """Catalog có phải sinh từ một lần chạy trên một máy không.

    catalog.parquet vào Git nhưng data/processed/ thì không, nên bảng tổng hợp đi
    được giữa hai máy trong khi dữ liệu thì không. Không kiểm thì catalog thành
    khảm từ nhiều lần chạy mà không ai biết.
    """
    g = "1b. Nguồn gốc catalog"
    if "built_on" not in cat.columns or "built_at" not in cat.columns:
        rep.add(g, "Có cột built_on và built_at", FAIL,
                "thiếu — xem protocol.md mục 6b")
        return

    combos = (cat.groupby(["env", "built_on", "built_at"])
                 .size().reset_index(name="n"))
    hosts = sorted(cat["built_on"].dropna().unique())

    for _, r in combos.iterrows():
        rep.add(g, f"{r['env']}: {r['n']:,} dòng — {r['built_on']} @ {r['built_at']}", OK)

    if len(hosts) > 1:
        rep.add(g, "Sinh trên một máy duy nhất", FAIL,
                f"catalog là khảm từ {len(hosts)} máy: {', '.join(hosts)}. "
                "Chạy lại `--env all` trên một máy.")
    elif cat["built_at"].nunique() > 1:
        rep.add(g, "Sinh từ một lần chạy duy nhất", WARN,
                f"{cat['built_at'].nunique()} thời điểm khác nhau trên cùng máy "
                f"{hosts[0]}. Bình thường khi đang làm; bản nộp cuối phải là một "
                "lệnh `--env all`.")
    else:
        rep.add(g, "Một lần chạy, một máy", OK)


def check_numbers(cat, refs, rep):
    for env in ENVS:
        g = f"2. Đối chiếu số — {env}"
        ref = refs.get(env)
        if ref is None:
            rep.add(g, "Có tệp tham chiếu", FAIL,
                    f"thiếu results/tables/reference_{env}.json")
            continue
        got = summarize(cat, env)

        checks = [
            ("Số chuỗi vào", "chuoi_vao", TOL["chuoi_vao"]),
            ("Số chuỗi còn lại", "chuoi_con_lai", TOL["chuoi_con_lai"]),
            ("Loại — ngoai_cua_so", "loai_ngoai_cua_so", TOL["loai"]),
            ("Loại — gan_chet", "loai_gan_chet", TOL["loai"]),
            ("Loại — hang", "loai_hang", TOL["loai"]),
            ("Loại — it_dong", "loai_it_dong", TOL["loai"]),
            ("Dòng hợp lệ h=12", "dong_h12", TOL["dong_h12"]),
            ("Tỉ lệ nội suy", "ti_le_noi_suy_pct", TOL["ti_le_noi_suy"]),
            ("Target mean", "target_mean", TOL["target_mean"]),
        ]
        for label, key, tol in checks:
            w, gv = ref.get(key), got.get(key)
            if w is None or gv is None:
                rep.add(g, label, WARN, "thiếu dữ liệu để so")
                continue
            d = rel_diff(gv, w)
            status = OK if d <= tol else FAIL
            detail = f"B = {gv:,}  |  tham chiếu = {w:,}  |  lệch {d*100:.2f}% (cho phép {tol*100:.0f}%)"
            rep.add(g, label, status, "" if status == OK else detail)


def check_processed(proc_dir, rep):
    g = "3. data/processed/"

    # data/processed/ nằm trong .gitignore nên chỉ có trên máy đã chạy tiền xử lý.
    # A pull về sẽ không có. Thiếu cả thư mục thì cảnh báo, không đánh trượt —
    # nếu không A sẽ không bao giờ nghiệm thu được trên máy mình.
    present = [e for e in ENVS if (proc_dir / f"{e}.parquet").exists()]
    if not present:
        rep.add(g, "Bỏ qua — không có tệp nào", WARN,
                "data/processed/ nằm trong .gitignore, chỉ máy đã chạy tiền xử lý "
                "mới có. B phải chạy mục này và báo kết quả.")
        return

    for env in ENVS:
        f = proc_dir / f"{env}.parquet"
        if not f.exists():
            rep.add(g, f"{env}.parquet tồn tại", FAIL,
                    f"không thấy {f} (các môi trường khác thì có)")
            continue
        d = pd.read_parquet(f, columns=None)
        need = {"env", "series_id", "bucket", "y", "is_interp"}
        miss = need - set(d.columns)
        if miss:
            rep.add(g, f"{env}.parquet đủ cột", FAIL, f"thiếu: {', '.join(sorted(miss))}")
            continue
        rep.add(g, f"{env}.parquet đủ cột", OK)
        n_int = int(d["is_interp"].sum())
        share = n_int / max(int(d["y"].notna().sum()), 1) * 100
        status = OK if share <= 5 else WARN
        rep.add(g, f"{env} tỉ lệ nội suy {share:.3f}%", status,
                "" if status == OK else "cao bất thường, kiểm lại K trong config")


def print_progress(root, a):
    """Chưa có catalog thì in tiến độ GĐ1 thay vì chỉ báo lỗi.

    Công cụ này B chạy nhiều lần trong lúc làm, nên khi chưa xong nó phải nói được
    còn thiếu gì, chứ không chỉ nói hỏng.
    """
    items = [
        ("src/cwp/io/bitbrains.py", "parser Bitbrains"),
        ("src/cwp/io/alibaba.py", "parser Alibaba"),
        ("src/cwp/preprocess/clean.py", "clip + mask sentinel"),
        ("src/cwp/preprocess/resample.py", "căn lưới 5 phút + nội suy ≤2"),
        ("src/cwp/preprocess/filter.py", "lọc chuỗi + đếm dòng hợp lệ"),
        ("data/processed/E1.parquet", "chuỗi E1 đã xử lý"),
        ("data/processed/E2.parquet", "chuỗi E2 đã xử lý"),
        ("data/processed/E3.parquet", "chuỗi E3 đã xử lý"),
        ("data/catalog.parquet", "bảng tổng hợp một dòng mỗi chuỗi"),
        ("tests/test_io.py", "test parser"),
        ("tests/test_resample.py", "test căn lưới"),
    ]
    done = [(p, d) for p, d in items if (root / p).exists()]
    todo = [(p, d) for p, d in items if not (root / p).exists()]

    print()
    print("─" * 66)
    print(f"TIẾN ĐỘ GĐ1: {len(done)}/{len(items)} sản phẩm")
    print("─" * 66)
    for p, d in done:
        print(f"  [xong ] {p:<34} {d}")
    for p, d in todo:
        print(f"  [thiếu] {p:<34} {d}")
    print()
    print("Đặc tả: docs/protocol.md mục 6b (schema) và mục 5–8 (quy tắc xử lý).")
    print("Số phải khớp: research-log/gate-gd1.md mục 2.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="data/catalog.parquet")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--ref", default="results/tables")
    a = ap.parse_args()

    cat_path = ROOT / a.catalog
    print()
    print("KIỂM CỔNG GĐ1 — research-log/gate-gd1.md")
    print(f"catalog    : {cat_path}")
    print(f"tham chiếu : {ROOT / a.ref}")

    rep = Report()
    g0 = "0. Tiền đề"

    refs = {}
    for env in ENVS:
        f = ROOT / a.ref / f"reference_{env}.json"
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            refs[env] = d[0] if isinstance(d, list) else d
    if len(refs) == len(ENVS):
        rep.add(g0, "Có đủ 3 tệp tham chiếu của A", OK)
    else:
        rep.add(g0, "Có đủ 3 tệp tham chiếu của A", FAIL,
                f"thiếu: {sorted(set(ENVS) - set(refs))} — chạy git pull, "
                "hoặc scripts/reference_gd1.py")

    if not cat_path.exists():
        rep.add(g0, "catalog.parquet tồn tại", FAIL,
                "chưa có — đây là trạng thái BÌNH THƯỜNG khi chưa triển khai xong")
        print_progress(ROOT, a)
        return rep.show()

    cat = pd.read_parquet(cat_path)
    rep.add(g0, f"Đọc được catalog ({len(cat):,} dòng)", OK)

    can_compare = check_schema(cat, rep)
    check_provenance(cat, rep)
    if can_compare:
        check_numbers(cat, refs, rep)
    else:
        rep.add("2. Đối chiếu số", "Bỏ qua", WARN,
                "thiếu cột cần thiết, sửa mục 1 rồi chạy lại")
    check_processed(ROOT / a.processed, rep)
    return rep.show()


if __name__ == "__main__":
    raise SystemExit(main())
