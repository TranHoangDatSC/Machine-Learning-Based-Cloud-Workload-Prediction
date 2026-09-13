# 2026-09-14 — Lỗi định nghĩa target N2 ở h > 1, phát hiện khi viết bản thảo

**Người thực hiện:** một phiên đóng cả hai vai.
**Giai đoạn:** GĐ5, đang viết bản thảo — quay lại GĐ4
**Thời lượng:** ghi ngay khi phát hiện, **trước** mọi thay đổi code hay lần chạy lại
(QĐ-017 điểm 6.3)

## Mục tiêu phiên

Ghi nhận lỗi, đo phạm vi ảnh hưởng, và khai cách xử lý trước khi chạm vào code.

## Phát hiện

Khi soạn công thức N2 cho mục Phương pháp của bài báo, cần viết target là gì. Đối chiếu
ba nguồn thì chúng không nói cùng một điều:

| Nguồn | Target N2 |
|---|---|
| protocol mục 14, bảng ba chế độ | `y_{t+h} − y_t` |
| QĐ-016 hệ quả, dòng 1133 | `y_{t+h} − y_t` |
| `normalize.bien_doi` + `features.add_target` | **`z_{t+h} = y_{t+h} − y_{t+h−1}`** |

Code biến đổi `y` thành sai phân một bước **trước**, rồi `add_target` dịch **chuỗi đã biến
đổi** đi `h` bước. Kết quả là target của N2 = sai phân một bước **tại** `t+h`, không phải
tổng thay đổi từ `t` tới `t+h`.

Đo trên dữ liệu thật, `E3_N2_h6.parquet`, 2.000 dòng ngẫu nhiên:

- `target == y(t+6) − y(t+5)`: **đúng**
- `target == y(t+6) − y(t)`: **sai**

## Vì sao nguy hiểm

Map ngược vẫn là `ŷ_{t+h} = y_t + Δ̂` (QĐ-016). Nên ở h > 1 dự đoán N2 bằng `y_t` **cộng
một bước thay đổi**, trong khi phải cộng `h` bước. Kỳ vọng của một bước thay đổi gần 0,
nên **mọi model N2 ở h > 1 bị kéo về gần dự báo ngây thơ** `ŷ = y_t`.

Thấy ngay trong bảng D1 (đường chéo), MAE p50 chia naive p50, trung vị qua 5 model:

| | h=1 | h=6 | h=12 |
|---|---:|---:|---:|
| E1 N2 | 1,063 | 1,081 | 1,085 |
| E2 N2 | 1,078 | 1,070 | 1,089 |
| E3 N2 | 0,940 | **0,997** | **1,011** |

E3 là môi trường ML thắng naive ở TN-A, vậy mà N2 ở h=6, 12 dính sát 1. Ở h=1 thì không —
đúng như lỗi dự báo, vì hai định nghĩa trùng nhau khi h = 1.

## Vì sao không phép kiểm nào bắt được

- Bất biến N2 của QĐ-016 điểm 5 (`Δ̂ = 0` ⇒ naive) **đúng với cả hai định nghĩa**.
- B3 kiểm bắc cầu ranh giới chuỗi, không kiểm target.
- Tham chiếu `reference_gd4.py` của A hiện thực **cùng đường** biến đổi-rồi-dịch, nên hai
  bên khớp nhau và **cùng sai** — đúng kiểu `E1_830` ở GĐ3.
- Không phép kiểm nào so `target` của N2 với `y` gốc.

Mâu thuẫn nằm ngay trong QĐ-016: điểm 2 nói *"biến đổi `y` trước, rồi sinh lại đặc
trưng"*, và đường code đó tự nhiên sinh lại luôn target. Còn bảng mục 14 thì định nghĩa
target khác hẳn.

## Phạm vi ảnh hưởng

**Không ảnh hưởng:** mọi kết quả N0; mọi kết quả N1 (gồm bản QĐ-018); **N2 ở h = 1**.

**Không đọc được — N2 ở h = 6, 12:**

- `transfer_gd4.csv`, `per_series_gd4.csv`: 60 tổ hợp N2 h ∈ {6, 12} × 2 biến thể lịch
- QĐ-017 D1 và D2: mọi dòng N2 ở h = 6, 12
- Kiểm định dính N2 ở h > 1: T-D1a (N2 vs N0), T-D1b và T-D1c ở N2, T-D2 ở N2, và các
  dự đoán P2, P4, P6
- Mọi câu đã ghi trong log và `gate-gd4.md` mục 5.4 dựa trên các số đó, cụ thể:
  - *"N2 chỉ mất ≤ 10%"*
  - *"bất đối xứng ở N2 co còn 1,10"* (26/30)
  - *"N2 tốt hơn N0 trong Bitbrains"* — rất có thể chỉ là *"gần-naive thắng ML N0"*, vì
    naive vốn khó thắng trên VM
  - *"N2 hại E3"*

## Quyết định — khai trước, chi tiết ở QĐ-019

Sửa được, không phải hạn chế phải chấp nhận: target đúng tính được thẳng từ `y` gốc,
và chỉ cần chạy lại N2 ở h = 6, 12. Theo QĐ-017 điểm 6.3: sửa, chạy lại **toàn bộ** phần
N2 h > 1 đã khai, báo cáo cả bản cũ lẫn bản sửa, kèm lý do.

## Việc tiếp theo

- [ ] QĐ-019: định nghĩa đúng, phép kiểm mới so target với `y` gốc, phạm vi chạy lại
- [ ] Sinh lại ma trận N2 h = 6, 12 vào thư mục riêng, không ghi đè sản phẩm GĐ4
- [ ] Chạy lại, phân tích lại, cập nhật `gate-gd4.md` mục 5.4 bằng một đính chính
- [ ] Bản thảo bài báo: phần N2 h > 1 để trống chờ số mới
