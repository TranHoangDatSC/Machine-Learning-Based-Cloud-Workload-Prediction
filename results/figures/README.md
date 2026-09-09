# Hình của GĐ2

Sinh lại toàn bộ bằng ba lệnh, không sửa tay tệp ảnh nào:

```bash
python scripts/fig_target_dist.py
python scripts/fig_acf.py --env all
python scripts/fig_burstiness.py --env all
```

## Mỗi hình có hai biến thể

| Hậu tố | Dùng cho | Khác gì |
|---|---|---|
| *(không có)* | duyệt cổng, dán vào log, xuất PDF báo cáo | tiêu đề panel **diễn giải** kết luận; `fig_target_dist` có thêm panel (c) hướng dẫn đọc; được phép nhắc mã quyết định nội bộ (QĐ-0xx) |
| `_paper` | **dán vào bài báo** | tiêu đề panel **mô tả thuần**; không có panel văn xuôi; không nhắc mã quyết định nội bộ nào |

Lý do tách: trong một bài báo, kết luận thuộc về caption và phần bàn luận, không
thuộc về tiêu đề trục. Một panel đặt tên *"CV có phải mức tải trá hình?"* hay
*"ba mức tải tách hẳn nhau"* đã khẳng định trước điều đang cần chứng minh, và người
đọc bài báo cũng không biết "QĐ-011" là gì. Bản `_paper` **tự đứng được** mà không
cần bất kỳ tài liệu nào của dự án.

Số liệu trên hai biến thể **giống hệt nhau** — chỉ chữ khác.

## Danh sách

| Tệp | Bước | Nội dung |
|---|---|---|
| `fig_target_dist{,_paper}` | 5 | ECDF phân phối CPU% ba môi trường + bảng phân vị. **Điều kiện qua cổng GĐ2** |
| `fig_acf{,_paper}` | 6 | ACF lag 1–48, PACF lag 1–48, ACF lag 1–300, tỉ lệ cặp bị bỏ vì NaN |
| `fig_burstiness{,_paper}` | 7 | ECDF của CV, CV so với mức tải, trung vị và IQR, bảng số |
| `fig_target_dist.caption.md` | 5 | Caption đầy đủ, kèm câu caption ngắn dán thẳng dưới hình |

Mỗi hình có cả `.png` (200 dpi, để xem nhanh) và `.pdf` (vector, để đưa vào LaTeX).

## Chọn hình vào bài báo là việc của A

`docs/research-plan.md` GĐ2: *"A duyệt hình, chọn 2–3 hình đưa vào paper."* Thư mục
này giữ **mọi** hình đã sinh; hình được chọn thì chép sang `paper/figures/`. B không
tự chép sang đó.

## Quy ước hiển thị

- Ba khe màu categorical đầu của bảng màu tham chiếu, dùng đúng thứ tự cho E1/E2/E3,
  không xoay vòng. Đã chạy validator: qua cả sáu phép kiểm trên nền sáng, ΔE deutan
  9,2 ở cặp xấu nhất.
- Kèm **mã hoá thứ hai bằng kiểu nét** (liền / đứt / gạch-chấm) để hình đọc được khi
  in đen trắng và với người mù màu.
- Không hình nào dùng **trục phụ** (hai thang y). Hai thang trên một hình cho phép
  đặt hai đường cạnh nhau ở bất kỳ vị trí tương đối nào, nên hình nói được điều dữ
  liệu không nói.
