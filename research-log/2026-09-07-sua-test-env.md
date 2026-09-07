# 2026-09-07 — Sửa `test_env.py`: metadata đúng không có nghĩa môi trường chạy được

**Người thực hiện:** A
**Giai đoạn:** GĐ0 (sửa công cụ cổng)
**Thời lượng:** ~30 phút

## Mục tiêu phiên
A dựng venv ghim trên máy mình theo QĐ-007. `test_env.py` báo 12/12 ĐẠT, nhưng
`scripts/reference_gd1.py` chạy thì vỡ ngay ở `import numpy`.

## Phát hiện

### Môi trường hỏng mà công cụ vẫn cho qua

`.venv` được tạo lần đầu bằng Python 3.13, cài đủ gói. Sau đó chạy
`py -3.11 -m venv .venv` **đè lên thư mục đã tồn tại**.

`python -m venv` khi gặp thư mục sẵn có thì chỉ thay `python.exe` và `pyvenv.cfg`,
**giữ nguyên `site-packages`**. Kết quả:

| | |
|---|---|
| `pyvenv.cfg` | `version = 3.11.9` |
| Tệp `.pyd` trong site-packages | **296/296 mang tag `cp313`** |

Interpreter 3.11 tìm `cp311`, không thấy, báo
`No module named 'numpy._core._multiarray_umath'`.

`pip install -r requirements.txt` báo "Requirement already satisfied" cho toàn bộ 12
gói, vì pip chỉ đọc metadata trong `dist-info`, không kiểm tra ABI của gói đã cài.

### Lỗi trong công cụ của A

`test_env.py` dùng `importlib.metadata.version()` — chỉ đọc tệp văn bản trong
`site-packages`, **không hề import gói nào**. Nên nó báo 12/12 ĐẠT trên một môi
trường mà không gói biên dịch nào chạy được.

Đây là đúng loại lỗi mà cả dự án đang cố tránh: một con số trông đạt nhưng đo sai
thứ. Công cụ đo "phiên bản đã khai" trong khi câu hỏi thật là "môi trường có chạy
được không".

## Đã sửa

Bổ sung `can_import()` vào `test_env.py`: import thật từng gói, và khi module có
`__version__` thì đối chiếu với phiên bản ghim để bắt trường hợp metadata lệch mã.

Thêm `test_all_packages_import()` cho pytest, và thông điệp chẩn đoán riêng khi phát
hiện lỗi import, chỉ thẳng nguyên nhân venv bị tạo đè.

Bảng ánh xạ tên: `pyyaml` → `yaml`, `scikit-learn` → `sklearn`.

## Kiểm chứng

Chạy bản đã sửa bằng chính `python.exe` của venv hỏng:

```
Khớp: 3/12
pandas, numpy, pyarrow, scikit-learn, xgboost,
lightgbm, matplotlib, scipy, jupyterlab  -> IMPORT LỖI
pyyaml, tqdm, pytest                     -> khớp
```

Đúng như dự đoán: chỉ ba gói thuần Python chạy được, mọi gói có phần biên dịch đều
hỏng. Bản cũ báo 12/12 cho cùng môi trường này.

## Hệ quả

**Kết quả 12/12 mà B báo ngày 2026-09-07 được đo bằng bản `test_env.py` cũ.** Bản cũ
không thể phân biệt môi trường tốt với môi trường có metadata đúng nhưng nhị phân
sai. B cần chạy lại bằng bản đã sửa để xác nhận.

Khả năng cao B vẫn đạt, vì B cài mới từ đầu trên Mint chứ không tạo đè. Nhưng chưa
xác nhận thì chưa coi là đạt.

## Việc tiếp theo
- [ ] A xoá hẳn `.venv` rồi tạo lại bằng 3.11
- [ ] B chạy lại `python tests/test_env.py` bằng bản đã sửa, báo lại
- [ ] Sau đó mới chạy `scripts/reference_gd1.py`

## File sinh ra
- Cập nhật `tests/test_env.py`
