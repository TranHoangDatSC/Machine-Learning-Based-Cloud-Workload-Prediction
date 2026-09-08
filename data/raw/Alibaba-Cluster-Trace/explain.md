# Alibaba Cluster Trace v2018 — machine_usage

## Vai trò trong đồ án
Environment **E3**. Đây là môi trường "khác tổ chức, khác quy mô, khác thời đại"
(2018 vs 2013) — mức độ khác biệt lớn nhất trong ba environment.

Cặp `Bitbrains → Alibaba` là bài test khắc nghiệt nhất của RQ3. Kỳ vọng hiệu năng
suy giảm mạnh; nếu KHÔNG suy giảm thì đó mới là finding đáng viết.

## Số liệu đã kiểm chứng (scan toàn bộ file)
| Thuộc tính | Giá trị |
|---|---|
| Kích thước | 8,99 GB |
| Tổng số dòng | **246.934.820** |
| Số máy | **4.023** |
| Dòng / máy (trung bình) | 61.381 |
| time_stamp | 0 → 691.190 s = **8 ngày** |
| Sampling interval | mode 10 s, median 60 s, **gap tới 640 s** |
| Định dạng | CSV, phân tách bằng `,`, **KHÔNG có header** |
| Số cột | 9 |

Kiểm chứng schema bằng chính dữ liệu:
- `cpu_util_percent` ∈ [0, 100] ✓
- `mem_util_percent` ∈ [0, 98] ✓
- `disk_io_percent` ∈ [**-1**, **101**] ✓ — khớp đúng ghi chú "abnormal values are of -1 or 101" trong schema gốc
- `mem_gps`, `mkpi` chỉ có dữ liệu ở **~21%** số dòng, còn lại rỗng

## Target
`cpu_util_percent` — thang 0–100.

Khớp trực tiếp với `CPU usage [%]` của Bitbrains. Đây chính là lý do chọn
machine_usage thay vì các bảng khác: nó cho một **target chung có cùng đơn vị và
cùng thang đo** giữa cả ba environment, không phải ép ba metric khác nhau vào
một bài toán.

## Cảnh báo tiền xử lý
1. **KHÔNG `pd.read_csv()` thẳng file 9 GB.** Sẽ hết RAM. Bắt buộc đọc theo
   `chunksize` hoặc dùng `usecols=[0,1,2]` (chỉ machine_id, time_stamp, cpu_util_percent).
2. **Không có header** → phải truyền `names=[...]` thủ công, nếu không dòng dữ liệu
   đầu tiên sẽ bị nuốt làm tên cột.
3. **Phải resample về lưới 5 phút** để khớp granularity với Bitbrains. Sau khi resample:
   691.200 / 300 = 2.304 điểm/máy × 4.023 máy ≈ **9,3 triệu dòng** — vừa RAM, và
   quan trọng hơn là làm cho RQ3 hợp lệ (không thể so model train ở 5 phút với
   dữ liệu 10 giây).
4. **Sampling không đều.** Interval dao động 10–640 s. Resample phải kèm chiến lược
   xử lý gap (đề xuất: mean trong mỗi bucket 5 phút, bucket rỗng → đánh dấu NaN,
   không nội suy mù quáng).
5. **Làm sạch `disk_io_percent`** nếu dùng làm feature: loại bỏ hoặc mask giá trị
   -1 và 101.
6. **Bỏ `mem_gps` và `mkpi`** khỏi feature set — 79% rỗng, không cứu được.

## Ghi chú
Đây là cluster co-location (online service + batch chạy chung máy). Đặc tính tải
khác hẳn Bitbrains (VM doanh nghiệp, tải theo giờ hành chính). Chỉ có 8 ngày nên
không phân tích được mùa vụ theo tuần — khi so sánh với Bitbrains (~30 ngày) phải
nói rõ giới hạn này trong paper, hoặc cắt Bitbrains xuống cùng 8 ngày cho công bằng.
