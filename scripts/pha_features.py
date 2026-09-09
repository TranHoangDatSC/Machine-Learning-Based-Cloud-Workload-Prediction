"""Phá `src/cwp/features/` có chủ ý, xác nhận `tests/test_features.py` bắt được.

    python scripts/pha_features.py

Lý do tồn tại: test xanh chưa chứng minh được gì nếu nó không biết đỏ. `test_env.py`
của chính dự án này đã hai lần báo đạt trên môi trường hỏng (`gate-gd2.md` mục 0).
`research-log/brief-gd2-b.md` Bước 2 vì thế yêu cầu phá code rồi ghi kết quả vào log
— script này để A chạy lại được lời khai đó thay vì phải tin.

Cách làm: sao lưu `src/cwp/features/*.py`, thay chuỗi để dựng lại đúng bảy kiểu sai
đã biết, chạy pytest sau mỗi lần, rồi **luôn** khôi phục ở khối `finally`. Không sửa
gì vĩnh viễn; nếu tiến trình bị giết giữa chừng thì bản sao lưu còn nằm ở
`scripts/.pha_backup/`, chép ngược lại là xong.

Bảy kiểu phá, và phép kiểm phải bắt được từng kiểu:

    P1  bỏ .shift(1) ở rolling        -> R2
    P2  min_periods=1                 -> R4
    P3  bỏ groupby(series_id)         -> R3
    P4  roll_std ddof=0               -> R2, QĐ-010
    P5  center=True ở rolling         -> R1
    P6  sai gốc dow (+4 thành +3)     -> đặc trưng lịch, QĐ-010
    P7  dropna thay cho luật cửa sổ   -> luật dòng hợp lệ, mục 8

P1, P2, P3 là ba kiểu phiếu giao việc chỉ đích danh. P5 là kiểu duy nhất chỉ R1 bắt
được — nó không vi phạm quy ước cửa sổ nào mà vẫn đọc thẳng vào tương lai. P7 là kiểu
nguy hiểm nhất vì nó im lặng trên E1 (xem QĐ-010).
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEAT = ROOT / "src" / "cwp" / "features"
BACKUP = Path(__file__).resolve().parent / ".pha_backup"
TEST = "tests/test_features.py"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# (mã, mô tả, [(tệp, tìm, thay), ...], nhóm phép kiểm phải đỏ)
PHA = [
    ("P1 bỏ .shift(1)",
     "rolling lăn thẳng trên y, cửa sổ thành [t-5, t]",
     [("windows.py", '    past = _past(df)\n', '    past = df["y"]\n')],
     "R2"),

    ("P2 min_periods=1",
     "cửa sổ chưa đủ điểm vẫn trả về số",
     [("windows.py", "r = past.groupby(sid, sort=False).rolling(w)",
       "r = past.groupby(sid, sort=False).rolling(w, min_periods=1)")],
     "R4"),

    ("P3 bỏ groupby(series_id)",
     "đuôi chuỗi trước chảy vào đầu chuỗi sau",
     [("windows.py", '    g = df.groupby("series_id", sort=False)["y"]\n',
       '    g = df["y"]\n'),
      ("windows.py", '    return df.groupby("series_id", sort=False)["y"].shift(1)',
       '    return df["y"].shift(1)'),
      ("windows.py", "        r = past.groupby(sid, sort=False).rolling(w)",
       "        r = past.rolling(w)"),
      ("windows.py", 'out[f"roll_{stat}_{w}"] = _flatten(ket_qua[stat], df.index)',
       'out[f"roll_{stat}_{w}"] = ket_qua[stat]')],
     "R3"),

    ("P4 roll_std ddof=0",
     "theo mặc định của numpy thay vì QĐ-010",
     [("windows.py", "r.std(ddof=ROLL_DDOF)", "r.std(ddof=0)")],
     "R2 (ddof)"),

    ("P5 center=True",
     "cửa sổ rolling đối xứng, nuốt cả tương lai",
     [("windows.py", "r = past.groupby(sid, sort=False).rolling(w)",
       "r = past.groupby(sid, sort=False).rolling(w, center=True)")],
     "R1"),

    ("P6 sai gốc dow",
     "đổi gốc QĐ-010 từ +4 sang +3",
     [("calendar.py", "+ DOW_EPOCH_OFFSET) % 7", "+ 3) % 7")],
     "lịch"),

    ("P7 dropna thay luật cửa sổ",
     "lọc bằng dropna() trên ma trận đặc trưng",
     [("matrix.py",
       "    hop_le = valid_row_mask(chuan, h, max_lag=max_lag)\n"
       "    return khung.loc[hop_le].reset_index(drop=True)",
       "    return khung.dropna().reset_index(drop=True)")],
     "luật cửa sổ"),
]


def sao_luu() -> None:
    if BACKUP.exists():
        shutil.rmtree(BACKUP)
    BACKUP.mkdir(parents=True)
    for f in FEAT.glob("*.py"):
        shutil.copy2(f, BACKUP / f.name)


def khoi_phuc() -> None:
    for f in BACKUP.glob("*.py"):
        shutil.copy2(f, FEAT / f.name)


def ap_dung(vet: list[tuple[str, str, str]]) -> None:
    """Thay chuỗi trong mã nguồn. Không tìm thấy thì dừng — mã đã đổi, vết đã cũ."""
    for ten_file, tim, thay in vet:
        p = FEAT / ten_file
        s = p.read_text(encoding="utf-8")
        if tim not in s:
            raise SystemExit(
                f"Không tìm thấy trong {ten_file}: {tim!r}\n"
                "Mã nguồn đã đổi từ lần viết vết phá này. Cập nhật lại PHA."
            )
        p.write_text(s.replace(tim, thay), encoding="utf-8")


def chay_pytest() -> tuple[int, list[str], str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", TEST, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    do = []
    for dong in r.stdout.splitlines():
        if dong.startswith(("FAILED ", "ERROR ")):
            nid = dong.split(" ", 1)[1].split(" - ")[0].strip()
            do.append(nid.split("::")[-1].split("[")[0])
    tom = [d for d in r.stdout.splitlines()
           if " passed" in d or " failed" in d or " error" in d]
    return r.returncode, sorted(set(do)), (tom[-1] if tom else "?")


def main() -> int:
    sao_luu()
    ket_qua = []
    try:
        ket_qua.append(("P0 không phá", "bản gốc, đối chứng", "—", *chay_pytest()))
        for ma, mo_ta, vet, nhom in PHA:
            khoi_phuc()
            ap_dung(vet)
            ket_qua.append((ma, mo_ta, nhom, *chay_pytest()))
    finally:
        khoi_phuc()
        shutil.rmtree(BACKUP, ignore_errors=True)

    print()
    print("=" * 74)
    print("PHÁ CODE CÓ CHỦ Ý — brief-gd2-b.md Bước 2")
    print("=" * 74)
    hong = []
    for ma, mo_ta, nhom, code, do, tom in ket_qua:
        xanh = code == 0
        print(f"\n{ma}  [{nhom}]  →  {'XANH' if xanh else 'ĐỎ'}   ({tom})")
        print(f"   {mo_ta}")
        for d in do:
            print(f"   ✗ {d}")
        # P0 phải xanh, mọi bản phá phải đỏ. Ngược lại là test không biết đỏ.
        if (ma.startswith("P0") and not xanh) or (not ma.startswith("P0") and xanh):
            hong.append(ma)

    print()
    print("=" * 74)
    code_cuoi, _, tom_cuoi = chay_pytest()
    print(f"Sau khi khôi phục: {tom_cuoi}  (exit {code_cuoi})")
    if hong:
        print(f"CHƯA ĐẠT — {hong} không cho kết quả mong đợi.")
        return 1
    if code_cuoi != 0:
        print("CHƯA ĐẠT — khôi phục xong mà test vẫn đỏ. Kiểm tra src/cwp/features/.")
        return 1
    print("ĐẠT — mọi bản phá đều bị bắt, và mã nguồn đã về nguyên trạng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
