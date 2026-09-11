# 2026-09-11 — GĐ4 Bước 3, và khắc phục rủi ro quy trình của phiên trước

**Người thực hiện:** một phiên đóng cả hai vai (B làm, A duyệt), tiếp nối
`2026-09-11-gd4-buoc-0-2.md`.
**Giai đoạn:** GĐ4
**Thời lượng:** ~2 giờ

## Mục tiêu phiên

Phiên trước kết thúc với một rủi ro đã ghi nhận nhưng **chưa khắc phục**: B3 của
`check_gd4.py` được sửa bởi chính phiên vừa viết `normalize.py`, nên "sản phẩm khớp
công cụ" không còn là bằng chứng. Phiên này khắc phục bằng hai việc đo được, rồi làm
trọn Bước 3.

## Đã làm

- Đối chiếu `normalize.py` với bản mồi độc lập của A — **không đọc mã**, chỉ gọi hàm
- `scripts/pha_gd4.py` — 8 bản phá, hai lớp
- Thêm **B11** và **B12** vào `check_gd4.py`, kèm hai ca phá trong test của nó

## Số liệu thu được

### 1. Đối chiếu chéo hai bản hiện thực — khắc phục chính

`scripts/_moi_normalize_gd4.py` là một bản `normalize.py` **đúng, trọn vẹn**, do A
soạn trước khi phiên hiện thực bắt đầu, và nằm trong danh sách "không được đọc" của
`brief-gd4-b.md` Bước 0. Phiên này **vẫn không đọc nó** — chỉ `importlib` rồi gọi ba
hàm và so số.

So trên **toàn bộ 1.535 chuỗi thật**, cả ba môi trường:

| Phép so | Lệch tối đa |
|---|---:|
| `thong_ke_train` → `mu` | 2,132e−14 |
| `thong_ke_train` → `sd` | 7,105e−15 |
| `bien_doi` N0 / N2 | **0,0** |
| `bien_doi` N1 | 3,638e−12 |
| `map_nguoc` N0 / N2 | **0,0** |
| `map_nguoc` N1 | 5,684e−14 |

Vị trí `NaN` **trùng khớp tuyệt đối** ở cả ba chế độ, mọi chuỗi.

Đây là bằng chứng loại A đúng nghĩa cho `normalize.py`: hai bản viết độc lập, không
bên nào thấy bên kia, ra cùng con số. **Tính độc lập của phần sản phẩm không những còn
nguyên mà nay đã được xác nhận** — rủi ro chỉ còn ở phạm vi hẹp là B3.

### 2. Bước 3 — tám bản phá, hai lớp

`brief-gd4-b.md` Bước 3 liệt kê năm kiểu bắt buộc **Q1–Q5**; ba kiểu **R1–R3** là bổ
sung của phiên này cho các lỗi N2.

| Mã | Phá gì | Bị bắt bởi |
|---|---|---|
| Q1 | `mu`/`sd` trên **toàn chuỗi** (rò rỉ) | `test_normalize.py`, C1, C2, **B11**, loại A |
| Q2 | quên map ngược | `test_normalize.py`, C3, C4, bất biến |
| Q3 | áp `mu`/`sd` của chuỗi khác | `test_normalize.py`, C3, C4, bất biến |
| Q4 | naive ở N2 dùng `Δ̂ = Δ_t` thay vì 0 | bất biến |
| Q5 | chuẩn hoá cả 4 đặc trưng lịch | **B12** |
| R1 | N2 bắc cầu qua ranh giới chuỗi | B3 |
| R2 | N2 sai phân **tiến** (rò rỉ tương lai) | B3 |
| R3 | N2 lấp điểm đầu bằng 0 | B3 |

**8/8 bị bắt.** Mã nguồn và `data/features/` về nguyên trạng sau khi chạy.

Lớp Q phá **mã nguồn** (`normalize.py`, `run_normalize_gd4.py`), lớp R phá **ma trận
đặc trưng**. Hai lớp cần cả hai vì chúng đi qua hai đường phát hiện khác nhau: lớp Q
bị bắt bởi test đơn vị và loại C, lớp R bởi loại B.

## Phát hiện — hai lỗ hổng thật của cổng, cùng một họ

Việc chạy phá trên **dữ liệu thật** tìm ra hai chỗ mà cổng không bắt được, và cả hai
đều là cùng một dạng thiếu sót: **không gì nối hai sản phẩm của B lại với nhau.**

### Lỗ hổng 1 — Q1 lọt, phải thêm B11

`mu`/`sd` tính trên toàn chuỗi là rò rỉ mà QĐ-016 điểm 1 gọi thẳng là *"chỗ dễ sai
nhất"*. Lúc đầu nó **lọt qua toàn bộ cổng** khi chỉ ma trận bị phá:

- z-score không đổi số dòng nào → B1, B2 không thấy gì
- C1, C2 kiểm thẳng hàm `thong_ke_train`, không kiểm ma trận
- `normalize_gd4.csv` do một đường code khác sinh ra nên nó **vẫn đúng**

**B11** nối hai thứ đó lại: `lag_1` ở N0 là `y[t−1]`, ở N1 là `(y[t−1] − mu)/sd`. Quan
hệ `y = sd·z + mu` là affine và thừa xác định, nên giải ngược ra `mu`, `sd` của từng
chuỗi rồi so với bảng đã khai.

Ngưỡng **1e−10** chọn theo số đo chứ không cho tròn: sai số giải ngược trên sản phẩm
đúng là 6,0e−13 (E1), 3,9e−13 (E2), 3,9e−14 (E3). Ngưỡng nằm trên nhiễu ~100 lần nên
không báo oan, và dưới 1e−8 ~100 lần nên bắt được cả trò cộng epsilon vào `sd`.

### Lỗ hổng 2 — Q5 lọt, phải thêm B12

Chuẩn hoá luôn 4 đặc trưng lịch cũng lọt: số dòng không đổi, `lag_1` không đổi nên
B11 cũng không thấy. **B12** dùng đúng điều QĐ-016 điểm 2 nói: bốn đặc trưng lịch chỉ
suy từ `bucket`, nên với cùng `(series_id, bucket)` chúng phải bằng nhau **tuyệt đối**
ở N0, N1, N2.

### Một chỗ chính phiên này suýt tự lừa mình

Bản đầu của Q5 để `bien_doi=None`, nên ma trận N1 được sinh từ `y` **chưa biến đổi** —
tức bản phá vô tình thành *"quên áp N1"*, và B11 bắt được. Nhìn bảng thì thấy "Q5 bị
bắt", nhưng nó bắt **nhầm thứ**: Q5 thật sự vẫn lọt.

Chỉ lộ ra khi đọc lại vì sao B11 — vốn chỉ đọc `lag_1` — lại phản ứng với một bản phá
chỉ đụng cột lịch. Bài học: khi một phép kiểm bắt được bản phá mà **cơ chế không giải
thích nổi**, đó là dấu hiệu bản phá sai chứ không phải phép kiểm giỏi.

## Quyết định

Không phát sinh quyết định giao thức. QĐ-016 giữ nguyên; B11 và B12 chỉ là hiện thực
hoá điểm 1 và điểm 2 của nó thành phép kiểm máy chạy được.

## Hạn chế còn lại — thu hẹp, chưa mất hẳn

Rủi ro quy trình của phiên trước đã **thu hẹp**, không còn ở mức "không có bằng chứng
nào":

| | Trước | Sau |
|---|---|---|
| `normalize.py` | độc lập nhưng chưa được xác nhận | **đã đối chiếu bản mồi của A, khớp tới 1e−12** |
| 27 ma trận | khớp 27/27 neo công bố | không đổi |
| B3, B11, B12 | do cùng phiên viết sản phẩm sửa | vẫn vậy — nhưng nay có 8 bản phá độc lập chứng minh chúng biết đỏ |

Phần chưa khắc phục được: ba phép kiểm B3/B11/B12 do cùng một phiên viết. Cách bù duy
nhất trong tầm tay là **không dùng "sản phẩm khớp công cụ" làm lập luận** — nên mỗi
phép kiểm đều có một chứng minh toán học viết ra trong mã, và một bản phá tương ứng
trong `pha_gd4.py` và trong `tests/test_check_gd4.py`.

Nếu sau này có người rảnh: cho một phiên **chưa từng đọc** `check_gd4.py` viết lại ba
phép kiểm đó từ QĐ-016 rồi so. Ghi vào việc tiếp theo, không chặn GĐ4.

## Việc tiếp theo

- [ ] Bước 4 — `scripts/run_transfer.py`, 6 cặp × 3 chế độ × 2 biến thể lịch × 3 h
- [ ] Bước 5–7 — đọc kết quả, xét QĐ-004, log và nghiệm thu
- [ ] Khi rảnh: phiên độc lập viết lại B3/B11/B12 từ QĐ-016 để đối chiếu

## File sinh ra

- `scripts/pha_gd4.py` — 8 bản phá, hai lớp, khôi phục trong `finally`
- `scripts/check_gd4.py` — thêm B11, B12; B3 giữ bản đã sửa ở phiên trước
- `tests/test_check_gd4.py` — fixture có `lag_1` và 4 cột lịch thật; thêm 2 ca phá.
  **21 test**, tất cả xanh
