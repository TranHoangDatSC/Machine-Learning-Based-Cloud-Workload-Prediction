"""Kiểm tra môi trường khớp đúng requirements.txt.

Chạy hai cách:
    python tests/test_env.py          # bảng đối chiếu, dùng ngay sau khi cài
    pytest tests/test_env.py -v       # dạng test, dùng khi kiểm tra định kỳ

Cổng GĐ0 chỉ đóng khi lệnh thứ nhất báo 12/12 khớp.
"""

import sys
from pathlib import Path

import importlib
import importlib.metadata as md

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PY_MIN = (3, 10)
PY_MAX = (3, 12)

ROOT = Path(__file__).resolve().parents[1]
REQ = ROOT / "requirements.txt"

# Tên trên PyPI khác tên khi import
IMPORT_NAME = {
    "pyyaml": "yaml",
    "scikit-learn": "sklearn",
}


def parse_requirements():
    """Đọc requirements.txt, trả về {tên gói: phiên bản ghim}."""
    pinned = {}
    for line in REQ.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, version = line.partition("==")
        if sep:
            pinned[name.strip()] = version.strip()
    return pinned


def installed_version(name):
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def can_import(name):
    """Import thật gói đó. Trả về None nếu ổn, chuỗi lỗi nếu hỏng.

    Bắt buộc phải có bước này: đọc metadata thôi là chưa đủ. Nếu venv bị tạo đè lên
    một venv cũ của Python khác, metadata vẫn đúng nhưng tệp .pyd lại biên dịch cho
    phiên bản khác, và mọi thứ chỉ vỡ khi chạy thật.
    """
    mod = IMPORT_NAME.get(name, name.replace("-", "_"))
    try:
        m = importlib.import_module(mod)
    except Exception as e:
        return f"{type(e).__name__}: {str(e).splitlines()[0][:90]}"
    want = parse_requirements().get(name)
    got = getattr(m, "__version__", None)
    if want and got and got != want:
        return f"metadata ghi {want} nhưng module báo {got}"
    return None


def in_venv():
    return sys.prefix != sys.base_prefix


def audit():
    """Trả về (rows, problems). rows dùng để in bảng."""
    rows, problems = [], []

    py = sys.version_info[:3]
    if not (PY_MIN <= py[:2] <= PY_MAX):
        problems.append(
            "Python {}.{}.{} nằm ngoài khoảng cho phép {}.{}–{}.{}".format(
                *py, *PY_MIN, *PY_MAX
            )
        )

    if not in_venv():
        problems.append(
            "Đang chạy Python toàn cục, chưa kích hoạt venv. "
            "Chạy: source .venv/bin/activate"
        )

    for name, want in parse_requirements().items():
        have = installed_version(name)
        if have is None:
            status = "CHƯA CÀI"
            problems.append(f"{name}: chưa cài (cần {want})")
        elif have != want:
            status = "LỆCH"
            problems.append(f"{name}: đang là {have}, cần {want}")
        else:
            err = can_import(name)
            if err:
                status = "IMPORT LỖI"
                problems.append(f"{name}: metadata đúng nhưng import hỏng — {err}")
            else:
                status = "khớp"
        rows.append((name, want, have or "—", status))

    return rows, problems


def main():
    rows, problems = audit()
    py = ".".join(str(x) for x in sys.version_info[:3])

    print()
    print(f"Python      : {py}   (cần {PY_MIN[0]}.{PY_MIN[1]}–{PY_MAX[0]}.{PY_MAX[1]})")
    print(f"venv        : {'có' if in_venv() else 'KHÔNG — đang dùng Python toàn cục'}")
    print(f"Thư mục     : {sys.prefix}")
    print()
    print(f"{'gói':<16}{'cần':<12}{'đang có':<12}trạng thái")
    print("-" * 56)
    for name, want, have, status in rows:
        print(f"{name:<16}{want:<12}{have:<12}{status}")
    print("-" * 56)

    ok = sum(1 for r in rows if r[3] == "khớp")
    print(f"Khớp: {ok}/{len(rows)}")
    print()

    if problems:
        print("CHƯA ĐẠT. Cần xử lý:")
        for p in problems:
            print(f"  - {p}")
        print()
        if any(r[3] == "IMPORT LỖI" for r in rows):
            print("Có gói lỗi import — gần như chắc chắn .venv bị tạo đè lên một")
            print("venv cũ của Python khác. pip báo 'already satisfied' nhưng tệp")
            print("nhị phân lại biên dịch cho phiên bản khác. Phải xoá hẳn rồi tạo lại:")
            print()
            print("  Linux/macOS:  deactivate; rm -rf .venv")
            print("  Windows:      deactivate; Remove-Item -Recurse -Force .venv")
            print()
            print("rồi tạo lại venv và cài lại từ đầu.")
        else:
            print("Cài lại đúng phiên bản:")
            print("  pip install -r requirements.txt")
        print()
        return 1

    print("ĐẠT. Môi trường khớp requirements.txt, cổng GĐ0 phần môi trường đã xong.")
    print()
    return 0


# ---- dạng pytest ----

def test_python_version():
    py = sys.version_info[:2]
    assert PY_MIN <= py <= PY_MAX, (
        f"Python {py[0]}.{py[1]} ngoài khoảng "
        f"{PY_MIN[0]}.{PY_MIN[1]}-{PY_MAX[0]}.{PY_MAX[1]}"
    )


def test_running_in_venv():
    assert in_venv(), "Chưa kích hoạt venv — chạy: source .venv/bin/activate"


def test_all_packages_import():
    problems = [f"{n}: {e}" for n in parse_requirements()
                if (e := can_import(n)) is not None]
    assert not problems, "Gói không import được:\n" + "\n".join(problems)


def test_all_packages_pinned():
    _, problems = audit()
    pkg_problems = [p for p in problems if "Python" not in p and "venv" not in p]
    assert not pkg_problems, "Gói lệch phiên bản:\n" + "\n".join(pkg_problems)


if __name__ == "__main__":
    raise SystemExit(main())
