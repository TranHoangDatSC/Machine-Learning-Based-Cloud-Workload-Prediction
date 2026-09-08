"""Cho phép chạy pytest ngay cả khi chưa `pip install -e .`.

Đây là lưới an toàn, không thay thế bước cài. `python -c "import cwp"` ngoài pytest
vẫn cần cài editable, hoặc đặt PYTHONPATH — xem README mục 9.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
