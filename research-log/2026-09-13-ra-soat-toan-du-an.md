# 2026-09-13 — Rà soát toàn dự án sau GĐ4, và đính chính Q3

**Người thực hiện:** một phiên đóng cả hai vai, theo yêu cầu của A sau log
`2026-09-13-gd4-buoc-4-6.md`.
**Giai đoạn:** GĐ4, trước Bước 7
**Thời lượng:** ~1,5 giờ

## Mục tiêu phiên

A hỏi ba câu: `container_usage.csv` nặng hàng trăm GB thì phương án dự phòng của
QĐ-004 còn làm được không; nghiên cứu đã thất bại chưa; và từ GĐ0 tới giờ có chỗ nào
sai giữa chừng. Phiên này **kiểm lại bằng số** thay vì kể lại theo trí nhớ, nên tìm ra
ba điều mới, trong đó một điều sửa kết luận đã ghi ở log trước.

## Đã làm

- `scripts/hau_kiem_q3_gd4.py` — **hậu kiểm**, chỉ đọc, không ghi tệp: tính lại Q3 với
  mốc là model train ngay trên đích thay vì naive
- Đo khả thi của phép thử hiệu ứng tổng hợp: gộp VM Bitbrains ngẫu nhiên thành "máy
  giả", đo ACF lag 1 và CV. Chỉ đo độ mượt, **không** chạy transfer nào
- Đọc lại QĐ-004, QĐ-005, protocol mục 14 và 17, gate-gd4 mục 3.4 và toàn bộ INDEX

## Phát hiện mới

### 1. Tiền đề "N0 phải thất bại nặng" sai ngay từ GĐ0

`research-plan.md` và gate-gd4 mục 3.4 viết: *"N0 phải thất bại nặng ở cặp Bitbrains
và Alibaba. Nếu N0 không thất bại thì gần như chắc chắn có rò rỉ."* QĐ-005 viết:
*"Transfer thô sẽ cho MAE khoảng 36."*

Cả hai suy từ **một hằng số** mức tải trung bình (28,24 ở cơ sở GĐ4). Nhưng model của
dự án không dự đoán bằng hằng số: nó thấy `lag_1 = y[t−1]`, nên **mức tải của chuỗi
đích đi thẳng vào model qua đặc trưng**. Số thật, E1→E3, N0, h=1, lịch = co:

| model | MAE transfer | MAE train ngay trên E3 | hằng số |
|---|---:|---:|---:|
| lr | 4,34 | 4,08 | 28,24 |
| rf | 4,29 | 4,13 | 28,24 |
| xgb | 4,30 | 4,04 | 28,24 |

N0 không thất bại theo chiều này, và **không phải vì rò rỉ**: log trước đã loại trừ
bằng ba bằng chứng. Cái sai nằm ở **điều kiện qua cổng**, không nằm ở sản phẩm.

Đây cũng là gốc của lỗi sơ bộ #1 ở log trước ("neo vào mốc hằng số"): phiên đó mắc lại
đúng cái bẫy đã viết sẵn trong kế hoạch. Không sửa câu chữ của gate mục 3.4; A ghi lý
do khi nghiệm thu Bước 7.

### 2. Q3 phóng đại bất đối xứng — đính chính con số "0 ngược dễ hơn"

Q3 so tỉ số `MAE / naive tại đích`. GĐ3 đã cho thấy naive vượt được ở E3 và gần như
không vượt được ở Bitbrains, nên tỉ số đó **trộn độ khó của đích với mất mát do
transfer**. Tính lại với mốc là cùng model train ngay trên chuỗi đích (GĐ3), cùng
Mann–Whitney, Holm trên cả 135 phép:

| Cặp | Chế độ | Q3 cũ (mốc naive) | **Mốc train trên đích** | trung vị xuôi / ngược |
|---|---|---|---|---|
| Bitbrains ↔ Alibaba | N0 | 30 xuôi | **30 xuôi** | 1,06–1,07 / 2,52–2,74 |
| Bitbrains ↔ Alibaba | N1 | 30 xuôi | **30 xuôi** | 1,06 / 1,51–2,82 |
| Bitbrains ↔ Alibaba | N2 | 30 xuôi | **14 xuôi · 11 ngược · 5 không khác** | 1,14 / 1,06–1,14 |
| E1 ↔ E2 | N0 | 15 xuôi | 10 xuôi · 1 ngược · 4 không khác | 1,00 / 1,06 |
| E1 ↔ E2 | N1 | 7 xuôi · 8 không khác | **15 không khác** | 0,81 / 0,82 |
| E1 ↔ E2 | N2 | 5 xuôi · 10 không khác | **4 ngược** · 11 không khác | 0,97 / 0,88 |

"Xuôi" là chiều đầu của cặp: E1→E3, E2→E3, E1→E2.

**Đính chính:** câu *"117 xuôi dễ hơn · 0 ngược dễ hơn"* ở log `2026-09-13-gd4-buoc-4-6.md`
và dòng INDEX tương ứng là **phóng đại**. Với mốc đúng: 84 xuôi rẻ hơn, 16 ngược rẻ
hơn, 35 không khác (tổng 135).

**Kết luận đúng, và nó rõ hơn kết luận cũ:** bất đối xứng **có thật khi còn giữ mức tải
hoặc biên độ** (N0, N1 — 60/60 phép Bitbrains ↔ Alibaba). **Khi chỉ còn quy luật thay
đổi (N2) thì bất đối xứng biến mất**: hai chiều tốn ngang nhau, khoảng 5–15%.

Bảng Q3 gốc giữ nguyên vì đó là phép kiểm đã khai trước. Bảng trên là hậu kiểm, ghi
nhãn như vậy nếu đưa vào paper.

### 3. "Cái giá transfer" ở N1, N2 trộn hai hiệu ứng

Mẫu số của cái giá là MAE train ngay trên đích **ở N0** (GĐ3). GĐ4 không chạy đường chéo
(E1→E1, E2→E2, E3→E3) ở N1, N2. Hệ quả: E1↔E2 ở N1 có cái giá 0,80 — **không** có nghĩa
transfer làm tốt lên, mà là chuẩn hoá tự nó giúp, cộng mất mát transfer, không tách
được. Tương tự, 1,14 của Bitbrains→Alibaba ở N2 có thể phần lớn là "N2 hại E3" chứ
không phải "transfer hại".

### 4. 150 dòng lệch số dòng test giữa GĐ3 và GĐ4 — đúng thiết kế

5 chuỗi E3 ở N2 mất 1–2 dòng test so với N0: sai phân cần thêm một điểm, nên dòng ngay
sau lỗ hổng bị loại. Khớp 27/27 neo số dòng của `check_gd4.py`. Không đáng kể (≤2 trên
~300 dòng, 5 trên 498 chuỗi), nhưng các phép ghép cặp N2–N0 ở 5 chuỗi này không cùng
đúng tập dòng.

### 5. Phương án `container_usage.csv` — ước tính cũ không dựa trên kích thước tệp

QĐ-004 ghi chi phí 1,5–2 tuần mà không nêu kích thước tệp; log trước đề xuất phương án
A dựa trên con số đó mà không kiểm. `machine_usage.csv` đang có là 9,0 GB; A báo
`container_usage.csv` ở mức hàng trăm GB. Thêm nữa, container Alibaba **không phải VM**,
nên kể cả tải về cũng không có so sánh ngang cấp thật — nhiễu chỉ giảm, không hết.

### 6. Khả thi của phép thử hiệu ứng tổng hợp trên dữ liệu đang có

Gộp VM Bitbrains ngẫu nhiên (trung bình theo bucket), `random_state = 42`:

| | ACF lag 1 (trung vị) | CV | số chuỗi | mức tải trung vị |
|---|---:|---:|---:|---:|
| E1 gốc | 0,667 | 0,50 | 735 | 2,71 |
| E1 gộp 5 | 0,924 | 0,63 | 147 | 12,99 |
| E1 gộp 10 | 0,940 | 0,55 | 73 | 13,22 |
| E2 gốc | 0,643 | 0,54 | 302 | 2,57 |
| E2 gộp 5 | 0,913 | 0,70 | 60 | 7,95 |
| **E3 gốc** | **0,861** | 0,29 | 498 | 40,15 |

Gộp chỉ 5 VM đã mượt **hơn** E3. Vậy có thể dựng một cặp transfer chỉ khác nhau ở mức
gộp, cùng một datacenter: E1-gộp → E1 và E1 → E1-gộp. Nếu bất đối xứng N0 ở đó giống
Bitbrains ↔ Alibaba, hiệu ứng tổng hợp đủ giải thích; nếu không, còn phần do môi trường.

Hạn chế đã thấy trước: gộp cũng đổi mức tải (2,7 → 13), nên phép thử không tách sạch
độ mượt khỏi mức tải ở N0; N1, N2 xử lý phần mức tải. 147 chuỗi ít hơn E2 (302) nhưng
đủ cho global model (~237 nghìn dòng train).

## Tổng hợp chỗ sai từ GĐ0 tới nay

### Sai trong kế hoạch và tài liệu của A

| GĐ | Chỗ sai | Phát hiện lúc | Trạng thái |
|---|---|---|---|
| GĐ0 | `test_env.py` báo 12/12 trên venv hỏng — chỉ đọc metadata | 09-07 | đã sửa |
| GĐ0 | Tiền đề "N0 phải thất bại nặng", "transfer thô MAE ~36" | **hôm nay** | **hạn chế của thiết kế**, ghi ở Bước 7 |
| GĐ0 | QĐ-004 ước chi phí `container_usage` không nêu kích thước tệp | hôm nay | phương án A không khả thi |
| GĐ1 | Protocol mục 6 bước 6 phá huỷ 79% E2, 99% E3 | 09-07 | QĐ-008 |
| GĐ1 | A và B chọn hai tập máy E3 khác nhau 89% | 09-09 | QĐ-009 đóng băng |
| GĐ2 | Data card mô tả quần thể trước lọc; mục 14 đo trên 833 thay vì 498 chuỗi | 09-09, 09-10 | đã đính chính |
| GĐ2 | Tiền đề ACF của QĐ-005 đổi trên quần thể thật (0,78 → 0,86) | 09-09 | đính chính, quyết định giữ |
| GĐ2 | Trần clip 100 tạo 5,12% điểm ở E1, chưa khai | 09-09 | QĐ-011 |

### Công cụ kiểm của A sai — bốn lần, cả bốn đều bị bắt trước khi vào kết quả

| GĐ | Chỗ sai |
|---|---|
| GĐ1 | `reference_gd1.py` đếm thừa 24 điểm nội suy ở mép E3 |
| GĐ2 | Thước đo dùng `dropna` thay luật dòng hợp lệ |
| GĐ3 | Tham chiếu R² lọt chuỗi hằng `E1_830` |
| GĐ4 | B3 thưởng cho đúng lỗi bắc cầu nó định bắt; B11, B12 thiếu |

### Sai trong sản phẩm, đã sửa trước khi chốt số

| GĐ | Chỗ sai | Hệ quả nếu không bắt |
|---|---|---|
| GĐ1 | Code tự chỉnh mẫu E3 cho khớp `gan_chet == 1` | mẫu không tái lập |
| GĐ3 | Mẫu con SVR chỉ trùng 2,9% giữa các horizon | so horizon không cùng dữ liệu |
| GĐ3 | Hướng Wilcoxon lấy từ hiệu hai trung vị | **đảo kết luận ở 8 cặp** |
| GĐ4 | `--resume` bỏ qua im lặng theo tên model | ba lần chạy "thành công" không chạy gì |
| GĐ4 | Bước 4 không ghi per-series | chạy lại 446,7 phút |

### Sai trong phân tích, chưa đi vào bảng chính thức

| Ngày | Chỗ sai | Trạng thái |
|---|---|---|
| 09-11 | `E1_830` 347 thay vì 346; đếm biên lưới; dải 2,3–2,6× | đính chính ở nghiệm thu GĐ3 |
| 09-13 | Neo vào hằng số; `min` qua model trên test; chia cho naive h=1 | ghi ở log trước |
| 09-13 | Q3 dùng mốc naive, phóng đại bất đối xứng | **đính chính ở đây** |
| 09-13 | Đề xuất phương án A mà không kiểm kích thước tệp | **ghi ở đây** |

### Rủi ro quy trình

GĐ4 do một phiên đóng cả hai vai. Đã bù bằng đối chiếu bản mồi độc lập của A (khớp
1e−12) và 8 bản phá. B3, B11, B12 vẫn do cùng phiên viết — việc tồn từ log 09-11.

### Hạn chế phương pháp còn mở — phải nêu trong paper

1. Siêu tham số GĐ3 chốt ở mép lưới 9/9; RF chỉ 50 cây (QĐ-015)
2. Siêu tham số N0 dùng lại cho N1, N2 (QĐ-016 điểm 3)
3. N1 không phải zero-shot — dùng lịch sử train của chuỗi đích (QĐ-016 điểm 1)
4. Thiếu đường chéo N1, N2 → cái giá ở N1, N2 trộn hai hiệu ứng (phát hiện 3)
5. Per-series chỉ có cho lịch = co; ablation lịch chỉ có số gộp
6. n = 300–700 chuỗi mỗi phép → hiệu ứng rất nhỏ vẫn có ý nghĩa; phải đọc kèm độ lớn
7. Trần clip 100 bất đối xứng (QĐ-011); mốc thời gian E3 tương đối (QĐ-010)
8. Hậu kiểm N2 vs N1 và hậu kiểm Q3 ở đây đều đặt ra sau khi thấy kết quả
9. **Đơn vị quan sát lệch** — VM vs máy vật lý (QĐ-004), nhiễu lớn nhất cho RQ3

## Quyết định — đề xuất cho A, chưa chốt

Phương án A của log trước **rút lại**. Thay bằng:

**Phương án D = phương án B của QĐ-004 + hai thí nghiệm bổ sung khai trước**, dùng dữ liệu
đang có:

| # | Việc | Trả lời được gì |
|---|---|---|
| D1 | Đường chéo ở N1, N2: E1→E1, E2→E2, E3→E3, cùng siêu tham số, cùng test | tách "chuẩn hoá giúp" khỏi "transfer mất" — phát hiện 3 |
| D2 | Gộp VM giả k = 5: E1-gộp ↔ E1, ba chế độ, lịch = co | bất đối xứng có do riêng hiệu ứng tổng hợp không — điều kiện 2 của QĐ-004 |

Bắt buộc theo mục 17: **viết QĐ-017 trước khi chạy**, gồm k, cách chọn nhóm, seed, các
phép kiểm, và **dự đoán cho từng kết quả có thể xảy ra**, rồi mới chạy. Dán nhãn "phân
tích bổ sung đặt ra sau GĐ4" trong paper.

Nếu A không muốn thêm việc: phương án B nguyên bản vẫn đứng được — RQ3 chính là E1↔E2,
Bitbrains ↔ Alibaba thành phân tích bổ sung, và phát biểu theo khuôn câu QĐ-004. Mục 17
cấm bỏ môi trường **vì kết quả xấu**; hạ E3 xuống phần bổ sung là phương án đã khai từ
08-30 vì lý do đơn vị quan sát, và E3 vẫn nằm trong mọi bảng.

## Việc tiếp theo

- [ ] **A chọn: D, hay B nguyên bản**
- [ ] Nếu D: viết QĐ-017 trước, rồi mới viết code
- [ ] Bước 7: nghiệm thu GĐ4, ghi lý do gate mục 3.4 gạch đầu sai tiền đề (phát hiện 1)
- [ ] Việc tồn: phiên độc lập viết lại B3, B11, B12; sinh lại hình GĐ3 bằng bảng màu đã qua kiểm

## File sinh ra

- `scripts/hau_kiem_q3_gd4.py` — hậu kiểm Q3, chỉ đọc
