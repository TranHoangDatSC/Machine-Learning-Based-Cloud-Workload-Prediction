# Bitbrains — fastStorage

## Vai trò trong đồ án
Environment **E1**. Đây là dataset chính, sạch nhất và đều nhất trong ba môi trường.
Dùng cho Experiment A (same-dataset) và làm nguồn train chính trong Experiment B (cross-dataset).

## Số liệu đã kiểm chứng
| Thuộc tính | Giá trị |
|---|---|
| Số VM (file) | 1.250 |
| Sampling interval | 300 s (5 phút) |
| Số dòng / VM | median 8.618 — min **5** — max **20.255** |
| Khoảng thời gian | 2013-08-12 → 2013-09-11 (~30 ngày) |
| Định dạng | CSV, phân tách bằng `;\t`, **có** header |
| Số cột | 11 |

## Target
`CPU usage [%]` — thang 0–100.

Đây là cột được chọn làm target chung cho cả ba environment vì nó đã chuẩn hoá sẵn,
không phụ thuộc số core hay tốc độ core của từng VM. Cột `CPU usage [MHZ]` **không**
dùng làm target vì không so sánh được giữa các môi trường (RQ3 sẽ vô nghĩa).

## Cảnh báo tiền xử lý
1. **Độ dài file rất lệch.** Có VM chỉ 5 dòng, có VM tới 20.255 dòng. Phải đặt ngưỡng
   tối thiểu (đề xuất: giữ VM có ≥ 2.000 mẫu) và ghi rõ ngưỡng này trong paper.
2. **Interval không phải lúc nào cũng đúng 300 s.** File 20.255 dòng trong 30 ngày ngụ ý
   sampling dày hơn. Phải resample về lưới 5 phút thống nhất, không giả định đều.
3. Parser phải dùng `sep=';\t'` với `engine='python'` — dùng `sep=';'` sẽ để lại tab
   trong tên cột và giá trị.
4. Timestamp là **giây** kể từ epoch, không phải mili-giây dù header ghi `[ms]`.
   (Kiểm chứng: 1376314846 → 2013-08-12, hợp lý.)

## Ghi chú
Trace này gồm nhiều application server và compute node, tải cao và có chu kỳ rõ
(ứng dụng báo cáo tài chính → có mùa vụ theo ngày/tuần). Đây là lý do fastStorage
dễ dự đoán hơn Rnd — một giả thuyết đáng kiểm định trong RQ2.
