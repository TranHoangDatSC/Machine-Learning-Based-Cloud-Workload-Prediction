# Hình

Mỗi giai đoạn một thư mục con: `gd2/`, rồi `gd3/`, `gd4/`… Tìm hình của giai đoạn
nào thì vào đúng thư mục đó.

## Hai dạng tệp, hai mục đích

| Dạng | Chứa gì | Dùng cho |
|---|---|---|
| `.png` | **đúng một hình**, tiêu đề mô tả thuần, không chữ diễn giải | dán thẳng vào bài báo hoặc slide |
| `.pdf` | **tập hợp các hình đó**, cộng một trang diễn giải ở đầu và chú thích dưới mỗi hình | đọc, duyệt, gửi cho người khác xem |

Vì sao tách. Ảnh ghép nhiều panel tiện xem nhưng dở khi dùng lại: muốn đưa một hình
vào bài thì phải cắt ảnh, mà cắt ảnh raster thì mất nét và không sửa được. Còn chữ
diễn giải in cứng vào ảnh thì không sửa được khi câu chữ của bài đổi, và người đọc
bài báo cũng không cần biết mã quyết định nội bộ của dự án.

Số liệu trong `.png` và trong `.pdf` **giống hệt nhau** — cùng một hàm vẽ, gọi hai lần.

## `gd2/` — Khám phá dữ liệu và bộ đặc trưng

Sinh lại toàn bộ bằng ba lệnh, không sửa tay tệp ảnh nào:

```bash
python scripts/fig_target_dist.py          # 01–03  + gd2_phan-phoi-cpu.pdf
python scripts/fig_acf.py --env all        # 04–07  + gd2_acf-pacf.pdf
python scripts/fig_burstiness.py --env all # 08–11  + gd2_burstiness.pdf
```

| Tệp | Bước | Nội dung |
|---|---|---|
| `01_ecdf-truc-tuyen-tinh.png` | 5 | ECDF phân phối CPU%, trục tuyến tính. **Điều kiện qua cổng GĐ2** |
| `02_ecdf-truc-symlog.png` | 5 | Cùng dữ liệu, trục symlog để phóng to vùng dưới 1% |
| `03_bang-phan-vi.png` | 5 | Bảng phân vị CPU% sau tiền xử lý |
| `04_acf-lag48.png` | 6 | ACF lag 1–48 (4 giờ), trung vị và dải p25–p75 |
| `05_pacf-lag48.png` | 6 | PACF lag 1–48 |
| `06_acf-lag300.png` | 6 | ACF lag 1–300, đủ phủ lag 288 = 24 giờ |
| `07_ti-le-cap-bo.png` | 6 | Tỉ lệ cặp (t, t+k) bị bỏ vì có NaN |
| `08_cv-ecdf.png` | 7 | ECDF của hệ số biến thiên CV |
| `09_cv-so-voi-muc-tai.png` | 7 | CV so với CPU% trung bình, kèm chặn của thang đo |
| `10_cv-trung-vi-iqr.png` | 7 | Trung vị và IQR của CV |
| `11_cv-bang-so.png` | 7 | Bảng số CV |
| `gd2_phan-phoi-cpu.pdf` | 5 | Hình 01–03 + diễn giải |
| `gd2_acf-pacf.pdf` | 6 | Hình 04–07 + diễn giải (ACF là gì, PACF khác chỗ nào) |
| `gd2_burstiness.pdf` | 7 | Hình 08–11 + diễn giải (CV là gì, chặn thang đo là gì) |
| `fig_target_dist.caption.md` | 5 | Caption đầy đủ, kèm câu caption ngắn dán thẳng dưới hình |

Số ở đầu tên tệp để thư mục tự sắp đúng thứ tự, và để dẫn hình trong bài không phải
nhớ tên dài.

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
- Bộ xuất dùng chung ở `src/cwp/viz/xuat.py`, có test ở `tests/test_viz.py`.
