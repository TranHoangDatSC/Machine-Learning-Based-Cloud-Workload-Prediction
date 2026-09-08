# 2026-09-08 — Công cụ cổng không nhận conda env; chốt đóng GĐ0

**Người thực hiện:** A
**Giai đoạn:** GĐ0 (đóng)
**Thời lượng:** ~20 phút

## Mục tiêu phiên
B chạy lại `test_env.py` bản có kiểm import. Kết quả 12/12 gói khớp nhưng công cụ
vẫn báo CHƯA ĐẠT. Truy nguyên và chốt cổng.

## Phát hiện

Môi trường của B:

```
Python      : 3.11.16   (trong khoảng 3.10–3.12)
Thư mục     : /home/phat/miniconda3/envs/ml-cwp
Khớp        : 12/12
CHƯA ĐẠT    : "Đang chạy Python toàn cục, chưa kích hoạt venv"
```

B dùng **conda env**, không dùng venv. Hàm kiểm của A viết
`sys.prefix != sys.base_prefix` — đúng với venv nhưng **luôn sai với conda env**, vì
conda env là một bản cài Python đầy đủ chứ không phải lớp phủ lên bản gốc, nên hai
giá trị đó bằng nhau.

Đây là lỗi thứ hai trong cùng một công cụ, và cùng một dạng với lỗi thứ nhất: công
cụ đo một dấu hiệu thay cho thứ cần đo. Lần trước đo "phiên bản đã khai" thay vì
"môi trường chạy được". Lần này đo "có phải venv không" thay vì "môi trường có tách
riêng không".

Nghiêm trọng hơn ở chỗ README mục 9 **cho phép cả conda lẫn venv**. Công cụ của A
mâu thuẫn với chính tài liệu của dự án.

## Đã sửa

`env_kind()` thay cho `in_venv()`, nhận cả hai dạng:

| Môi trường | Kết quả |
|---|---|
| venv | hợp lệ |
| conda env có tên khác `base` | hợp lệ |
| conda `base` | **không hợp lệ** — base là môi trường dùng chung |
| Python toàn cục | không hợp lệ |

Kiểm chứng bằng cách mô phỏng biến `CONDA_PREFIX` và `CONDA_DEFAULT_ENV`: env
`ml-cwp` cho `(True, "conda env 'ml-cwp'")`, env `base` cho `(False, ...)`.

Dòng hiển thị đổi từ `venv: có/không` sang `Môi trường: <mô tả>` để không ngụ ý chỉ
venv mới hợp lệ.

## Quyết định

**Cổng GĐ0 ĐÓNG.** B đạt cả hai phần:
- Hiểu bài: 4/4 câu sát hạch đúng bản chất
- Môi trường: Python 3.11.16, conda env riêng, 12/12 gói khớp và import thật được

Hai môi trường khác nhau giữa A (venv Windows) và B (conda Mint) được chấp nhận, vì
điều ghim trong QĐ-007 là **phiên bản thư viện và khoảng Python**, không phải công
cụ quản lý môi trường.

## Vướng mắc

**QĐ-008 vẫn đang chờ duyệt và đang chặn GĐ1.** B dự kiến xong GĐ1 ngày mai. Nếu B
hiện thực `filter.py` theo quy tắc hiện hành của protocol mục 6 thì E2 mất 79% và E3
mất 99% dữ liệu, và phần việc đó phải làm lại.

## Việc tiếp theo
- [ ] **A duyệt hoặc bác QĐ-008 trong hôm nay** — chặn tiến độ ngày mai của B
- [ ] Báo B: khoan viết `filter.py` và `resample.py` cho tới khi có kết luận
- [ ] Sau khi chốt: A sinh lại tham chiếu, B mới chạy phần lọc

## File sinh ra
- Cập nhật `tests/test_env.py`, `docs/research-plan.md`
