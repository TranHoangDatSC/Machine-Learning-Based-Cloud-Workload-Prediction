"""Phá code GĐ3 có chủ ý, xác nhận cổng và test bắt được (brief-gd3-b.md Bước 4).

    python scripts/pha_gd3.py

Cùng lý do như `scripts/pha_features.py` ở GĐ2: **test xanh chưa chứng minh được gì
nếu nó không biết đỏ**. `test_env.py` của chính dự án này đã hai lần báo đạt trên môi
trường hỏng (`gate-gd2.md` mục 0). Script này để A chạy lại được lời khai đó thay vì
phải tin.

Cách làm: sao lưu `src/cwp/evaluation/`, `src/cwp/models/` và `scripts/run_baselines.py`,
thay chuỗi để dựng lại năm kiểu sai đã biết, chạy **hai** bộ phát hiện sau mỗi lần
phá, rồi **luôn** khôi phục ở khối `finally`.

    pytest      tests/test_splits.py, test_metrics.py, test_baselines.py
    cổng        run_baselines.py --out <tạm>  rồi  check_gd3.py --tables <tạm>

Bảng thật ở `results/tables/` **không bị đụng tới** — mọi bản phá ghi vào thư mục tạm.

Năm kiểu phá, và nhóm phép kiểm phải đỏ:

    P1  gán tập theo `t` thôi, không đòi `t+h` cùng tập  -> L1, và số dòng lệch neo
    P2  purge hụt một dòng ở ranh giới (`<=` thay `<`)   -> số dòng lệch neo
    P3  mẫu số MASE tính trên test thay vì train         -> cột `mase` lệch neo
    P4  gộp bằng trung bình thay vì trung vị             -> 45 chỉ số p50 lệch neo
    P5  seasonal naive lấp giá trị thiếu bằng ffill      -> tỉ lệ dòng bỏ thành 0%

Một điều phải nói trước về "bản gốc XANH"
-----------------------------------------

`check_gd3.py` **trượt sẵn một mục trên bản gốc**: loại A, 27 ô R² của E1. Nguyên nhân
đã truy được và không nằm ở code B — `results/tables/reference_gd3.json` giữ chuỗi
`E1_830` trong phần gộp R² dù target của nó hằng trên test, tức `SS_tot = 0`. Chi tiết
ở `research-log/2026-09-10-gd3-thi-nghiem-a.md`.

Nên script này **không** đòi bản gốc xanh tuyệt đối. Nó ghi lại tập phép kiểm trượt
của bản gốc làm **vết nền**, rồi đòi mỗi bản phá làm trượt thêm ít nhất một phép kiểm
**mới**. Cách này chặt hơn "đỏ là đạt": một bản phá chỉ tái hiện đúng vết nền cũ thì
bị tính là **không bị bắt**.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = Path(__file__).resolve().parent / ".pha_gd3_backup"
TAM = Path(__file__).resolve().parent / ".pha_gd3_tables"

TEST = ["tests/test_splits.py", "tests/test_metrics.py", "tests/test_baselines.py"]

# Tệp được sao lưu và khôi phục. Đường dẫn tương đối so với ROOT.
NGUON = [
    "src/cwp/evaluation/splits.py",
    "src/cwp/evaluation/metrics.py",
    "src/cwp/models/baselines.py",
    "scripts/run_baselines.py",
]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# (mã, mô tả, [(tệp, tìm, thay), ...], nhóm phép kiểm phải đỏ)
PHA = [
    ("P1 gán tập theo t thôi",
     "bỏ điều kiện t+h cùng tập — đúng kiểu rò rỉ QĐ-013 điểm 2 chặn",
     [("src/cwp/evaluation/splits.py",
       "    return (off >= lo) & (off + h < hi)",
       "    return (off >= lo) & (off < hi)")],
     "L1 + số dòng"),

    ("P2 purge hụt một dòng",
     "dùng <= thay < ở ranh giới, dòng cuối train có target rơi sang val",
     [("src/cwp/evaluation/splits.py",
       "    return (off >= lo) & (off + h < hi)",
       "    return (off >= lo) & (off + h <= hi)")],
     "số dòng"),

    ("P3 mẫu số MASE trên test",
     "d tính trên test thay vì train — MASE của naive sẽ lệch xa 1",
     [("src/cwp/evaluation/metrics.py",
       '    lo, hi = bucket_bounds()["train"]',
       '    lo, hi = bucket_bounds()["test"]')],
     "cột mase"),

    ("P4 gộp bằng trung bình",
     "p50 lấy trung bình thay vì trung vị — chuỗi tải cao chi phối con số gộp",
     [("src/cwp/evaluation/metrics.py",
       "            p25, p50, p75 = (float(x) for x in np.percentile(v, [25, 50, 75]))",
       "            p25, p75 = (float(x) for x in np.percentile(v, [25, 75]))\n"
       "            p50 = float(np.mean(v))")],
     "45 chỉ số p50"),

    ("P5 seasonal lấp bằng ffill",
     "lặng lẽ lấp y_{t-288} thiếu — tỉ lệ dòng bỏ của E3 tụt từ 0,43% xuống 0%",
     [("src/cwp/models/baselines.py",
       '    return tra_cuu.reindex(khoa).to_numpy("float64")',
       '    return tra_cuu.reindex(khoa).ffill().to_numpy("float64")')],
     "dòng bị bỏ"),
]


def sao_luu() -> None:
    if BACKUP.exists():
        shutil.rmtree(BACKUP)
    BACKUP.mkdir(parents=True)
    for rel in NGUON:
        dich = BACKUP / rel.replace("/", "__")
        shutil.copy2(ROOT / rel, dich)


def khoi_phuc() -> None:
    for rel in NGUON:
        shutil.copy2(BACKUP / rel.replace("/", "__"), ROOT / rel)


def ap_dung(vet: list[tuple[str, str, str]]) -> None:
    """Thay chuỗi trong mã nguồn. Không tìm thấy thì dừng — mã đã đổi, vết đã cũ."""
    for rel, tim, thay in vet:
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        if tim not in s:
            raise SystemExit(
                f"Không tìm thấy trong {rel}: {tim!r}\n"
                "Mã nguồn đã đổi từ lần viết vết phá này. Cập nhật lại PHA."
            )
        p.write_text(s.replace(tim, thay, 1), encoding="utf-8")


def _chay(lenh: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(lenh, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def chay_pytest() -> tuple[int, list[str], str]:
    r = _chay([sys.executable, "-m", "pytest", *TEST, "-q", "--no-header",
               "-p", "no:cacheprovider"])
    do = []
    for dong in r.stdout.splitlines():
        if dong.startswith(("FAILED ", "ERROR ")):
            nid = dong.split(" ", 1)[1].split(" - ")[0].strip()
            do.append(nid.split("::")[-1].split("[")[0])
    tom = [d for d in r.stdout.splitlines()
           if " passed" in d or " failed" in d or " error" in d]
    return r.returncode, sorted(set(do)), (tom[-1] if tom else "?")


def chay_cong() -> tuple[int, set[str], str]:
    """Sinh bảng vào thư mục tạm rồi chấm bằng `check_gd3.py`.

    Trả về tập **nhãn phép kiểm bị trượt**, đọc từ các dòng `[ TRƯỢT]` của công cụ.
    """
    if TAM.exists():
        shutil.rmtree(TAM)
    TAM.mkdir(parents=True)
    # `check_gd3.py` tìm tham chiếu trong chính thư mục `--tables`; thiếu nó thì công
    # cụ dừng ở tiền đề và mọi bản phá đều "lọt" vì lý do chẳng liên quan gì.
    for ten in ("reference_gd3.json", "cv_gd2.csv"):
        nguon = ROOT / "results" / "tables" / ten
        if nguon.exists():
            shutil.copy2(nguon, TAM / ten)

    r1 = _chay([sys.executable, "scripts/run_baselines.py", "--env", "all",
                "--splits", "test", "--no-snapshot", "--out", str(TAM)])
    if r1.returncode != 0:
        return r1.returncode, {"run_baselines.py đổ vỡ"}, "sinh bảng thất bại"

    r2 = _chay([sys.executable, "scripts/check_gd3.py", "--tables", str(TAM)])
    ket = [d for d in r2.stdout.splitlines() if "ĐẠT" in d or "CHƯA ĐẠT" in d]
    return r2.returncode, _doc_truot(r2.stdout), (ket[-1].strip() if ket else "?")


def _doc_truot(stdout: str) -> set[str]:
    """Tập phép kiểm trượt, **kèm dòng chi tiết** của từng cái.

    Lấy nhãn thôi thì chưa đủ: P3 làm trượt đúng cái nhãn `45 chỉ số p50` vốn đã có
    trong vết nền, nên nó sẽ trông như "không bị bắt" dù công cụ đã in ra sai lệch ở
    cột `mase`. Ghép nhãn với dòng chi tiết ngay dưới nó thì hai lý do khác nhau
    thành hai vết khác nhau.
    """
    truot, dang_mo = set(), None
    for dong in stdout.splitlines():
        if "[ TRƯỢT]" in dong:
            if dang_mo:
                truot.add(dang_mo)
            dang_mo = dong.split("]", 1)[1].strip()
        elif dang_mo is not None:
            # Dòng chi tiết là dòng thụt sâu, không mang nhãn trạng thái mới.
            if dong.startswith(" " * 9) and "[" not in dong[:12]:
                dang_mo += " | " + dong.strip()
            else:
                truot.add(dang_mo)
                dang_mo = None
    if dang_mo:
        truot.add(dang_mo)
    return truot


def main() -> int:
    sao_luu()
    ket_qua = []
    try:
        print("Bản gốc — lấy vết nền…")
        goc = ("P0 không phá", "bản gốc, đối chứng", "—", *chay_pytest(), *chay_cong())
        nen = goc[7]   # (ma, mo_ta, nhom, mã_pytest, đỏ, tóm, mã_cổng, trượt, tóm)
        ket_qua.append(goc)
        for ma, mo_ta, vet, nhom in PHA:
            khoi_phuc()
            ap_dung(vet)
            print(f"{ma}…")
            ket_qua.append((ma, mo_ta, nhom, *chay_pytest(), *chay_cong()))
    finally:
        khoi_phuc()
        shutil.rmtree(BACKUP, ignore_errors=True)
        shutil.rmtree(TAM, ignore_errors=True)

    print()
    print("=" * 78)
    print("PHÁ CODE CÓ CHỦ Ý — brief-gd3-b.md Bước 4")
    print("=" * 78)
    if nen:
        print("\nVết nền của bản gốc (đã truy nguyên, không phải lỗi code B):")
        for t in sorted(nen):
            print(f"   • {t}")

    hong = []
    for ma, mo_ta, nhom, _pc, pdo, ptom, _cc, ctruot, ctom in ket_qua:
        moi = ctruot - nen
        goc_p0 = ma.startswith("P0")
        bat_duoc = bool(pdo) or bool(moi)
        print(f"\n{ma}  [{nhom}]  →  {'BỊ BẮT' if bat_duoc else 'LỌT'}")
        print(f"   {mo_ta}")
        print(f"   pytest: {ptom}")
        for d in pdo:
            print(f"      ✗ {d}")
        print(f"   cổng  : {ctom}")
        for t in sorted(moi):
            print(f"      ✗ {t}")
        # P0 phải không có gì mới ngoài vết nền; mọi bản phá phải bị bắt.
        if goc_p0 and bat_duoc:
            hong.append(ma)
        if not goc_p0 and not bat_duoc:
            hong.append(ma)

    print()
    print("=" * 78)
    ma_p, do_p, tom_p = chay_pytest()
    ma_c, truot_c, tom_c = chay_cong()
    shutil.rmtree(TAM, ignore_errors=True)   # lần chấm cuối cũng phải dọn sau mình
    print(f"Sau khi khôi phục: {tom_p}   |   {tom_c}")
    if hong:
        print(f"CHƯA ĐẠT — {hong} không cho kết quả mong đợi.")
        return 1
    if do_p:
        print("CHƯA ĐẠT — khôi phục xong mà pytest vẫn đỏ.")
        return 1
    if truot_c != nen:
        print("CHƯA ĐẠT — khôi phục xong mà vết cổng khác vết nền ban đầu.")
        return 1
    print("ĐẠT — cả năm bản phá đều bị bắt, và mã nguồn đã về nguyên trạng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
