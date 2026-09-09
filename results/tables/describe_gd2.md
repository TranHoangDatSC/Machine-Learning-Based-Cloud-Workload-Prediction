# CPU% sau tiền xử lý — thống kê mô tả

Sinh bằng `python scripts/describe_gd2.py --env all`. Không sửa tay.

Quần thể: mọi điểm `y` không NaN của các chuỗi được giữ, trong cửa sổ 8 ngày
(QĐ-011 điểm 2). **Không phải** cột `target` của ma trận đặc trưng — thống kê
của cột đó ở `results/tables/reference_gd2.json`, khoá `target_mean_h*`.

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| Số chuỗi | 735 | 302 | 498 |
| Số điểm | 1,693,440 | 695,808 | 1,147,392 |
| Trung bình | 13.6352 | 9.2199 | 38.0123 |
| Độ lệch chuẩn | 27.9530 | 21.4265 | 14.9522 |
| Nhỏ nhất | 0.0000 | 0.0000 | 0.0000 |
| p10 | 0.7000 | 0.4583 | 20.9000 |
| p25 | 1.2000 | 1.0417 | 29.2500 |
| Trung vị | 1.7833 | 1.7667 | 37.8333 |
| p75 | 5.3667 | 4.0667 | 47.3333 |
| p90 | 57.7000 | 23.5667 | 56.3000 |
| p95 | 100.0000 | 60.0667 | 61.2667 |
| Lớn nhất | 100.0000 | 100.0000 | 99.8000 |
| Tỉ lệ NaN % | 1.4272 | 0.3086 | 9.2936 |
| Điểm bằng 100 % | 5.1238 | 2.2788 | 0.0000 |
| Tỉ lệ nội suy % | 0.0163 | 0.0924 | 0.1647 |

Ba điều phải đọc kèm bảng này:

1. **Hiệu ứng chọn lọc.** Bộ lọc `gan_chet` bỏ 36,3% chuỗi E1 và 39,4% chuỗi
   E2 nhưng chỉ 0,4% chuỗi E3, và cắt gần như hoàn toàn ở đuôi dưới. Trung
   bình CPU% của E1 vì thế tăng từ 6,75 (quần thể thô) lên giá trị ở bảng
   này. Phát biểu phải nói trên quần thể đã lọc, không nói trên "Bitbrains".
2. **Trần 100 là kiểm duyệt, và bất đối xứng.** Xem dòng *Điểm bằng 100 %*:
   E1 và E2 có, E3 không. Phân vị 95 của E1 chính là trần.
3. **E3 thiếu nhiều hơn hẳn.** Xem dòng *Tỉ lệ NaN %*.

Chi tiết: `docs/data-card.md` mục *Sau tiền xử lý*, và QĐ-011.
