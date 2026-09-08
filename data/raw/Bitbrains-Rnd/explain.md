# Bitbrains — Rnd

## Vai trò trong đồ án
Environment **E2**. Cùng nhà cung cấp với fastStorage nhưng khác hạ tầng lưu trữ
(SAN nhanh **và** NAS chậm) và khác thành phần workload (nhiều management machine hơn).

Đây là cặp so sánh giá trị nhất của đồ án: `fastStorage → Rnd` là transfer
**cùng tổ chức, khác hạ tầng**, trong khi `Bitbrains → Alibaba` là transfer
**khác tổ chức hoàn toàn**. Hai mức độ "khác môi trường" này tách bạch được
nguyên nhân suy giảm hiệu năng trong RQ3 — không có nó thì RQ3 chỉ có một
điểm dữ liệu và không kết luận được gì.

## Số liệu đã kiểm chứng
| Thư mục | Số VM | Rows/VM (median) | Rows/VM (min–max) | Khoảng thời gian |
|---|---|---|---|---|
| `2013-7` | 500 | 8.254 | 437 – 8.630 | 2013-06-30 → 2013-07-30 |
| `2013-8` | 500 | 8.623 | 8.615 – 8.631 | 2013-07-31 → 2013-08-30 |
| `2013-9` | 500 | 8.318 | 3.306 – 14.095 | 2013-08-31 → 2013-09-29 |

Sampling interval: 300 s. Định dạng và 11 cột giống hệt fastStorage.

## Target
`CPU usage [%]` — giống fastStorage.

## Cảnh báo tiền xử lý
1. **500 VM lặp lại qua 3 tháng, KHÔNG phải 1.500 VM khác nhau.** Tên file (`1.csv`,
   `2.csv`, …) trùng nhau giữa ba thư mục. Nếu gộp cả ba tháng mà không xử lý thì
   sẽ hoặc bị ghi đè, hoặc coi nhầm cùng một VM thành ba VM độc lập → **data leakage**
   khi chia train/test. Phải tạo khoá `(month, vm_id)` hoặc nối chuỗi theo thời gian.
2. Ba tháng **liền kề nhau** (30/6 → 29/9). Có thể nối thành chuỗi ~3 tháng cho mỗi VM —
   đây là chuỗi dài nhất trong toàn đồ án, rất hợp để phân tích horizon dài.
3. `2013-8` của Rnd trùng thời gian với fastStorage (08/2013). Khi so sánh E1 vs E2
   nên dùng đúng cửa sổ này để loại bỏ yếu tố thời điểm.
4. `2013-7` có VM chỉ 437 dòng, `2013-9` có VM 14.095 dòng → áp cùng ngưỡng lọc và
   resample như fastStorage.

## Ghi chú
Rnd nhiều management machine → tải thấp, nhiều đoạn gần như phẳng, nhưng xen kẽ
burst. Kỳ vọng: naive baseline mạnh bất thường ở đây, và MAPE không dùng được
(mẫu số gần 0). Dùng **SMAPE hoặc MASE** thay thế.
