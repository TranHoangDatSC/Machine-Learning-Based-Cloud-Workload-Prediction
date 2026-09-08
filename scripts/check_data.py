"""Kiểm dữ liệu thô trên máy này có khớp bản của A không.

`data/raw/` không vào Git (11 GB). Mỗi máy phải tự có dữ liệu, nên cần cách xác
minh hai bên đang chạy trên **cùng một bộ dữ liệu** — nếu không thì mọi con số đối
chiếu ở cổng GĐ1 đều vô nghĩa.

Đối chiếu với results/tables/data_fingerprint.json: số tệp, tổng dung lượng, và md5
của vài tệp mẫu.

    python scripts/check_data.py

Thoát 0 nếu khớp, 1 nếu chưa. Chỉ đọc, không sửa gì.
"""

import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FP = ROOT / "results" / "tables" / "data_fingerprint.json"


def md5_file(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


def md5_edges(p, n=1 << 20):
    with open(p, "rb") as f:
        head = f.read(n)
        f.seek(-n, 2)
        tail = f.read()
    return hashlib.md5(head).hexdigest(), hashlib.md5(tail).hexdigest()


def main():
    print()
    print("KIỂM DỮ LIỆU THÔ")
    print(f"thư mục: {RAW}")
    print()

    if not FP.exists():
        print(f"Không thấy {FP}")
        print("Chạy trên máy A trước để sinh vân tay, rồi commit tệp đó.")
        return 1

    fp = json.loads(FP.read_text(encoding="utf-8"))
    problems = []

    print(f"{'thư mục':<36}{'tệp':>7}{'cần':>7}   dung lượng")
    print("-" * 74)
    for rel, want in fp["dirs"].items():
        d = RAW / rel
        if not d.is_dir():
            print(f"{rel:<36}{'—':>7}{want['n_files']:>7}   THIẾU CẢ THƯ MỤC")
            problems.append(f"{rel}: chưa có thư mục")
            continue
        fs = sorted(d.glob("*.csv"))
        tot = sum(f.stat().st_size for f in fs)
        ok_n = len(fs) == want["n_files"]
        ok_b = tot == want["total_bytes"]
        mark = "ok" if (ok_n and ok_b) else "LỆCH"
        print(f"{rel:<36}{len(fs):>7}{want['n_files']:>7}   {tot:>15,}  {mark}")
        if not ok_n:
            problems.append(f"{rel}: có {len(fs)} tệp, cần {want['n_files']}")
        elif not ok_b:
            problems.append(
                f"{rel}: tổng {tot:,} bytes, cần {want['total_bytes']:,}")

    a = RAW / "Alibaba-Cluster-Trace" / "machine_usage.csv"
    want_a = fp["alibaba"]
    print()
    if not a.exists():
        print("machine_usage.csv                    THIẾU")
        problems.append("Alibaba machine_usage.csv: chưa có")
    else:
        size = a.stat().st_size
        ok = size == want_a["bytes"]
        print(f"machine_usage.csv  {size:,} bytes  "
              f"{'ok' if ok else 'LỆCH, cần ' + format(want_a['bytes'], ',')}")
        if not ok:
            problems.append(
                f"Alibaba: {size:,} bytes, cần {want_a['bytes']:,} — "
                "nhiều khả năng tải chưa xong")
        else:
            h, t = md5_edges(a)
            if h != want_a["md5_head_1mb"]:
                problems.append("Alibaba: md5 1 MB đầu không khớp")
            if t != want_a["md5_tail_1mb"]:
                problems.append("Alibaba: md5 1 MB cuối không khớp")
            print(f"  md5 đầu/cuối 1 MB: "
                  f"{'ok' if h == want_a['md5_head_1mb'] and t == want_a['md5_tail_1mb'] else 'LỆCH'}")

    print()
    print("md5 tệp mẫu:")
    for rel, want_h in fp["samples"].items():
        p = RAW / rel
        if not p.exists():
            print(f"  {rel:<42} THIẾU")
            problems.append(f"{rel}: chưa có")
            continue
        got = md5_file(p)
        ok = got == want_h
        print(f"  {rel:<42} {'ok' if ok else 'LỆCH'}")
        if not ok:
            problems.append(f"{rel}: md5 {got[:12]}… khác bản của A")

    print()
    print("=" * 74)
    if problems:
        print(f"CHƯA KHỚP — {len(problems)} vấn đề:")
        for p in problems:
            print(f"  - {p}")
        print()
        print("Xem README mục 10 để biết cách lấy dữ liệu.")
        print("=" * 74)
        return 1

    print("KHỚP — dữ liệu thô giống hệt bản của A. Chạy được GĐ1.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
