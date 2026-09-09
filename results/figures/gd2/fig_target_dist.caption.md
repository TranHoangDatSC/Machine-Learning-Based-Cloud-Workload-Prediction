# Caption — hình phân phối CPU%

Sinh bằng `python scripts/fig_target_dist.py`. Không sửa tay.

## Caption ngắn (đặt dưới hình trong paper)

> **Hình 1. Phân phối CPU% của ba môi trường sau tiền xử lý.** Hàm phân phối tích
> luỹ thực nghiệm (ECDF) trên (a) trục tuyến tính và (b) trục symlog. Trung vị là
> 1.78% (E1), 1.77% (E2) và
> 37.83% (E3). Bước nhảy thẳng đứng tại 100 là hệ quả của bước
> clip: 5.12% điểm của E1 và 2.28% của E2 nằm đúng tại trần,
> E3 không có điểm nào. Quần thể là các chuỗi còn lại sau bộ lọc ở protocol mục 6
> bước 7, không phải toàn bộ trace.

## Vì sao chọn ECDF — trả lời yêu cầu của phiếu giao việc

Vấn đề: trung vị của E1 và E2 dưới 2%, của E3 gần 38%. Trên một trục **mật độ**
tuyến tính chung, toàn bộ khối lượng của E1/E2 rơi vào cột đầu tiên và hình không
nói được gì.

Ba phương án phiếu nêu là ECDF, log1p, và trục phụ. Chọn **ECDF**:

| Phương án | Vì sao chọn hay bỏ |
|---|---|
| **ECDF** | Trục tung là xác suất tích luỹ nên **mỗi đường bắt buộc đi từ 0 lên 1** — không môi trường nào bị nén, kể cả khi mức tải lệch 20 lần. Không có tham số bin để vô tình chỉnh. Đọc thẳng được phân vị. Khối bị kiểm duyệt tại trần hiện thành bước nhảy nhìn thấy được |
| log1p | Đọc được cả ba, nhưng bóp méo khoảng cách giữa các mức tải — mà chênh lệch mức tải chính là điều hình này phải cho thấy |
| Trục phụ | **Loại.** Hai thang y trên một hình cho phép đặt hai đường cạnh nhau ở bất kỳ vị trí tương đối nào, nên hình nói được điều dữ liệu không nói |

Hai panel vì chúng trả lời hai câu khác nhau. Panel (a) trục tuyến tính trả lời câu
của RQ3 — ba môi trường ở ba mức tải khác nhau. Panel (b) trục symlog phóng to vùng
dưới 1%, nơi trung vị của E1/E2 thực sự nằm; trên trục tuyến tính vùng đó chỉ chiếm
vài pixel sát trục tung.

## Ghi chú kỹ thuật

- Quần thể: gộp mọi điểm `y` không NaN của các chuỗi được giữ, trong cửa sổ 8 ngày.
  **Không phải** cột `target` của ma trận đặc trưng — xem QĐ-011 điểm 2.
- Bảng phân vị đọc từ `results/tables/describe_gd2.csv`, không tính lại. Script kiểm
  chéo trung vị suy từ ECDF với `p50` trong bảng đó, lệch quá bước lưới thì thoát 1.
- Màu lấy ba khe categorical đầu của bảng màu tham chiếu, đúng thứ tự. Đã chạy
  validator: qua cả sáu phép kiểm trên nền sáng, ΔE deutan 9,2 ở cặp xấu nhất. Kèm
  mã hoá thứ hai bằng kiểu nét (liền / đứt / gạch-chấm) để hình đọc được khi in đen
  trắng và khi người đọc mù màu.
