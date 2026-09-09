# 2026-09-09 — B chạy lại E3 nhưng chưa áp dụng QĐ-009

**Người thực hiện:** A
**Giai đoạn:** GĐ1
**Thời lượng:** ~30 phút

## Sự việc

B chạy lại `--env E3` sau khi QĐ-009 được chốt, kết quả **y hệt lần trước**:
499 chuỗi giữ, 919.526 dòng h=12, 0,178% nội suy.

A kiểm tra và xác nhận: **không phải lệch mới, mà là B chưa áp dụng sửa.**

## Bằng chứng

| Nguồn | Dấu hiệu |
|---|---|
| Log của B | còn dòng `Lượt 1: Quét tính CPU trung bình` và `Đã chọn 500 máy phân tầng` — hai dòng này phải biến mất khi đọc danh sách cố định |
| `src/cwp/io/alibaba.py` | vẫn định nghĩa `machine_means`, `sample_machines`; không có `load_frozen`, không nhắc `e3_machines` |
| `src/cwp/preprocess/build.py:276` | vẫn gọi `machine_means()` rồi `sample_machines()` |

`check_gd1.py` báo: **trùng 146/500** máy với danh sách đóng băng.

Con số 146 khớp chính xác với biến thể "sort theo `machine_id` rồi phân tầng" mà A đã
đo khi truy nguyên QĐ-009. Xác nhận đúng cơ chế đã chẩn đoán: B sắp xếp theo
`machine_id` trước khi chia tầng, A dùng thứ tự quét tệp.

## Điểm đáng lưu ý

Ngay cả khi dùng **sai tập máy**, phần lớn chỉ số vẫn qua ngưỡng:

| Chỉ số E3 | B | Tham chiếu | Kết quả |
|---|---:|---:|---|
| Số chuỗi vào | 500 | 500 | ok |
| Chuỗi còn lại | 499 | 498 | ok (lệch 0,2%) |
| Dòng hợp lệ h=12 | 919.526 | 917.463 | ok (lệch 0,22%) |
| Loại `gan_chet` | 1 | 2 | **TRƯỢT** |
| Tỉ lệ nội suy | 0,178% | 0,167% | **TRƯỢT** (6,59%) |

Nếu không có kiểm tra danh sách đóng băng thì chỉ hai chỉ số nhỏ trượt, rất dễ bị
coi là sai số chấp nhận được. Đây đúng là lý do QĐ-009 tồn tại: **thống kê gộp khớp
không có nghĩa hai bên đo cùng một thứ.**

## Đã sửa thêm

`check_gd1.py` trước đây **dừng sớm** khi thiếu cột: gặp thiếu `built_on`/`built_at`
là trả về ngay, không chạy tới kiểm tra danh sách máy. B sẽ phải sửa từng lỗi rồi
chạy lại nhiều vòng.

Đã đổi thành: thiếu cột vẫn báo, nhưng **tiếp tục kiểm mọi thứ kiểm được**. Giờ một
lần chạy hiện hết vấn đề. Với B đang lặp dưới áp lực thời gian thì khác biệt này
đáng kể.

Toàn bộ: **12 test xanh**.

## Việc tiếp theo
- [ ] B `git pull`, sửa `io/alibaba.py` và `build.py` đọc `config/e3_machines.txt`
- [ ] B chạy `--env all` một lệnh
- [ ] Rồi mới làm Bước 7, 8

## File sinh ra
- Cập nhật `scripts/check_gd1.py`
