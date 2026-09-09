# Phiếu giao việc GĐ2 — cho B

**Người giao:** A · **Ngày:** 2026-09-09
**Đọc trước:** `docs/protocol.md` mục 8, 9, 17 · `research-log/gate-gd2.md`
**Cổng:** `research-log/gate-gd2.md`

Mỗi bước có ba phần: **Prompt** để đưa cho agent, **Lệnh** để chạy, **Phải thấy** để
đối chiếu. Làm xong bước nào chạy lệnh bước đó ngay, đừng viết hết rồi mới kiểm.

---

## Rào chắn quan trọng nhất: đừng code hướng về con số

Mỗi bước dưới đây có mục **Phải thấy** với số cụ thể. Số đó chỉ để **đối chiếu SAU
khi chạy**, không phải mục tiêu để code hướng tới.

> **Tuyệt đối không viết code điều chỉnh kết quả cho khớp số kỳ vọng.**
> Ra sai thì sửa cách hiện thực cho đúng đặc tả, không sửa đầu ra cho vừa đáp án.

Ngày 2026-09-09 đã xảy ra đúng chuyện này ở GĐ1: `io/alibaba.py` có đoạn thay máy
trong mẫu cho tới khi số chuỗi `gan_chet` bằng đúng 1, kèm chú thích *"Đảm bảo phân
tầng có đúng 1 chuỗi gần chết theo ngưỡng kiểm cổng"*. Đã xoá.

**Dán dòng này vào cuối mọi prompt gửi agent:**

```
Số kỳ vọng trong phiếu chỉ để đối chiếu sau khi chạy. Không viết code điều chỉnh
kết quả cho khớp con số nào. Sai thì sửa cách hiện thực cho đúng đặc tả trong
docs/protocol.md, không sửa đầu ra.
```

Ở GĐ2 rào chắn này còn quan trọng hơn GĐ1. Số dòng ma trận đặc trưng ở Bước 3 phải
khớp **tuyệt đối** với `catalog.parquet`. Một agent được giao "làm cho ra 1.642.811
dòng" sẽ tìm được cách cắt cho đủ. Việc cần làm là sinh đặc trưng đúng đặc tả rồi
**xem** nó có ra con số đó không — lệch thì đó là tín hiệu có lỗi, không phải việc
cần che.

---

## Lưu ý về tính độc lập

`scripts/reference_gd2.py` là bản hiện thực của A. Giá trị nằm ở chỗ **hai bản độc
lập ra cùng con số**. Các prompt dưới đây chỉ mô tả hành vi và kết quả cần đạt, cố ý
không nói cách làm. Đừng đưa mã của A cho agent đọc.

---

## Trước khi bắt đầu: chờ A chốt QĐ-010

`gate-gd2.md` mục 6 có hai điểm giao thức còn thiếu, **B không được tự quyết**:

1. Múi giờ và mốc lịch — E3 dùng thời gian tương đối, không có ngày thật.
2. EDA được nhìn phần dữ liệu nào (train 70% hay toàn cửa sổ).

**Bước 1 và Bước 5–7 phụ thuộc hai quyết định này.** Bước 0, 2, 3, 4 làm được ngay.
Nếu A chưa chốt mà đã đến Bước 5 thì dừng và hỏi, đừng tự chọn — quy tắc phối hợp 1
và 4 ở `docs/research-plan.md`.

---

## Bước 0 — Chuẩn bị (không cần agent)

```bash
git pull
python -m pip install -e .
python tests/test_env.py
python scripts/check_gd1.py
pytest tests/ -q
```

**Phải thấy**

```
Khớp: 12/12
ĐẠT — sản phẩm GĐ1 khớp tham chiếu trong ngưỡng cho phép.
81 passed
```

`check_gd1.py` phải còn ĐẠT trước khi động vào GĐ2. GĐ2 xây thẳng lên
`data/processed/`, hỏng nền thì mọi thứ sau đều vô nghĩa.

---

## Bước 0b — Bù hai việc còn treo của GĐ1

`gate-gd1.md` mục 5.3. Làm trước, đừng để dồn.

1. **Chạy lại toàn bộ tiền xử lý bằng một lệnh `--env all`.** Catalog hiện sinh từ
   hai lần chạy (08:28 và 08:33). Cùng máy nên số không sai, nhưng mục 3.4b của cổng
   đòi một lệnh duy nhất.
2. **Viết log GĐ1** trong `research-log/YYYY-MM-DD-slug.md`, có bảng lọc đủ sáu nhóm
   cột theo `gate-gd1.md` mục 3.2, ba môi trường. Số lấy từ `catalog.parquet` của
   chính B, không chép bảng của A.

**Phải thấy** — sau khi chạy lại, `check_gd1.py` không còn dòng cảnh báo:

```
[  ok  ] Sinh từ một lần chạy duy nhất
```

---

## Bước 1 — `src/cwp/features/`

### Prompt

```
Viết module sinh đặc trưng trong src/cwp/features/, theo docs/protocol.md mục 8.
Đầu vào là data/processed/{env}.parquet với các cột env, series_id, bucket, y,
is_interp. Đầu ra là ma trận đặc trưng cho một horizon h cho trước.

Đúng 19 đặc trưng, không thừa không thiếu:
- Lag: t-1, t-2, t-3, t-6, t-12, t-24            (6)
- Rolling cửa sổ 6:  mean, std, min, max          (4)
- Rolling cửa sổ 12: mean, std, min, max          (4)
- Sai phân: y_t - y_{t-1}                         (1)
- Lịch: hour_sin, hour_cos, dow_sin, dow_cos      (4)

Bốn ràng buộc bắt buộc, sai một cái là hỏng cả giai đoạn:

1. Mọi thống kê rolling tính CHỈ trên quá khứ, KHÔNG gồm điểm hiện tại. Tức
   rolling_mean_6 tại t bằng mean của y[t-6 .. t-1].
2. Không dùng min_periods=1. Cửa sổ chưa đủ điểm thì để NaN.
3. Lag và rolling tính theo từng series_id. Tuyệt đối không để đuôi chuỗi này
   chảy sang đầu chuỗi kia — một file có tới 735 chuỗi nối nhau.
4. Không đặc trưng nào được chạm tới y tại thời điểm t+1 trở đi.

Đặc trưng lịch suy từ cột bucket: bucket * 300 là số giây. Với E1 và E2 đó là
epoch thật; với E3 đó là giây kể từ lúc bắt đầu trace, KHÔNG phải epoch —
xử lý theo QĐ-010, hỏi A nếu chưa có quyết định đó.

Giữ lại cột series_id và bucket trong đầu ra để truy vết. Target là y tại t+h.
```

### Lệnh
```bash
python -c "import cwp.features as f; print(f.__all__)"
```

### Phải thấy
Danh sách hàm công khai, và **không có** hàm nào tên kiểu `fill`, `impute`,
`smooth` — GĐ2 không lấp thêm gì, việc đó đã xong và đã khai báo ở GĐ1.

---

## Bước 2 — `tests/test_features.py`

Làm **trước** khi sinh ma trận thật. Đây là bước quan trọng nhất của cả GĐ2.

### Prompt

```
Viết tests/test_features.py bằng pytest, kiểm module sinh đặc trưng.
Không dùng dữ liệu thật, tự tạo chuỗi nhỏ tính tay được.

Bắt buộc có bốn phép kiểm rò rỉ sau:

R1 - Không chạm tương lai. Sinh đặc trưng trên một chuỗi. Rồi thay toàn bộ y từ
     t+1 trở đi bằng NaN và sinh lại. Mọi đặc trưng tại t phải KHÔNG ĐỔI.
     Viết phép kiểm này cho vài mốc t khác nhau.

R2 - Rolling loại điểm hiện tại. Trên chuỗi y = [1,2,3,4,5,6,7,8],
     rolling_mean_6 tại t=6 phải bằng mean(y[0..5]) = 3.5, không phải
     mean(y[1..6]) = 4.5.

R3 - Không bắc cầu qua ranh giới chuỗi. Ghép hai series_id, chuỗi A toàn giá trị
     nhỏ, chuỗi B toàn giá trị lớn. 24 dòng đầu của chuỗi B phải có lag_24 là
     NaN, và rolling của chuỗi B không được mang dấu vết chuỗi A.

R4 - Cửa sổ thiếu điểm ra NaN, không được min_periods=1: 6 dòng đầu của mỗi
     chuỗi phải có rolling_mean_6 là NaN, và dòng thứ 7 thì có giá trị.

Thêm: đặc trưng lịch mã hoá sin/cos phải tuần hoàn đúng — hour_sin tại hai thời
điểm cách nhau đúng 24 giờ phải bằng nhau.
```

### Lệnh
```bash
pytest tests/test_features.py -v
```

### Phải thấy
Tất cả PASSED.

**Rồi làm thêm việc này, nó mới là phần có giá trị:** sửa hỏng code sinh đặc trưng
một cách có chủ ý và xác nhận test bắt được. Bỏ `.shift(1)` đi thì R2 phải đỏ; đổi
`min_periods` thành 1 thì R4 phải đỏ; bỏ `groupby(series_id)` thì R3 phải đỏ. Sửa
xong khôi phục lại. Test xanh mà không chứng minh được nó biết đỏ thì chưa phải test
— `test_env.py` của dự án này đã hai lần báo đạt trên môi trường hỏng.

Ghi vào log kết quả từng lần phá.

---

## Bước 3 — Sinh ma trận đặc trưng, đối chiếu neo GĐ1

### Prompt

```
Viết script sinh ma trận đặc trưng cho ba môi trường x ba horizon (1, 6, 12),
dùng module ở Bước 1, ghi ra data/features/{env}_h{h}.parquet.

Bỏ mọi dòng không hợp lệ theo định nghĩa ở protocol mục 8: mọi điểm trong
[t-24, t] không NaN, và target tại t+h không NaN.

In ra bảng số dòng của từng tệp.
```

### Lệnh
```bash
python scripts/build_features.py --env all
```

### Phải thấy — số dòng phải khớp **TUYỆT ĐỐI**, không có ngưỡng sai số

| Môi trường | h=1 | h=6 | h=12 |
|---|---:|---:|---:|
| E1 | 1.650.896 | 1.647.221 | 1.642.811 |
| E2 | 678.486 | 675.665 | 673.322 |
| E3 | 938.933 | 926.892 | 917.463 |

Chín con số này lấy từ `catalog.parquet`, đã được kiểm chéo với bản hiện thực độc
lập của A và khớp đến từng đơn vị. Cả hai bên tính trên cùng một tệp
`data/processed/`, nên **lệch một dòng là có lỗi**, không phải nhiễu.

Lệch thì nghi theo thứ tự này: `min_periods=1` (ra nhiều dòng hơn), quên
`groupby(series_id)` (nhiều hơn), nhầm `t+h` thành `t+h-1` (lệch đúng vài nghìn).

**Không sửa số cho khớp. Sửa cách hiện thực.**

---

## Bước 4 — Thống kê mô tả sau lọc

### Prompt

```
Viết script sinh bảng thống kê mô tả cho ba môi trường, tính trên
data/processed/ SAU khi đã lọc, ghi ra results/tables/.

Mỗi môi trường một dòng: số chuỗi, số điểm, mean, std, min, p25, p50, p75, p95,
max của target, và tỉ lệ điểm là NaN.
```

### Lệnh
```bash
python scripts/describe_gd2.py --env all
```

### Phải thấy — ba cột này đã biết trước, dùng để tự kiểm

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| mean | 13,6352 | 9,2199 | 38,0123 |
| p50 | 1,7833 | 1,7667 | 37,8333 |
| std | 27,9530 | 21,4265 | 14,9522 |

Lệch quá 2% thì dừng lại, đừng đi tiếp — nghĩa là đọc sai tệp hoặc lọc nhầm.

---

## Bước 5 — Hình phân phối target *(chờ QĐ-010 nếu dùng phần train)*

**Đây là điều kiện qua cổng GĐ2.** `docs/research-plan.md`: *"hình quan trọng nhất của
paper, nó dựng nền cho toàn bộ lập luận ở RQ3."*

### Prompt

```
Vẽ phân phối target của ba môi trường E1, E2, E3 trên CÙNG MỘT HÌNH, sinh bằng
script vào results/figures/, không vẽ trong ô notebook.

Ràng buộc: E1 và E2 có trung vị dưới 2%, E3 gần 38%. Trên trục tuyến tính chung
thì E1 và E2 dồn hết vào cột đầu tiên và hình không nói được gì. Chọn cách biểu
diễn đọc được cả ba - ECDF, log1p, hay trục phụ - và ghi rõ trong caption đã
chọn gì và vì sao.

Hình phải cho thấy được điều RQ3 dựa vào: ba môi trường khác nhau về mức tải.
Kèm một bảng phân vị nhỏ bên cạnh, đừng bắt người đọc đoán con số từ hình.
```

### Lệnh
```bash
python scripts/fig_target_dist.py
```

### Phải thấy
Một tệp hình trong `results/figures/`, mở ra thấy rõ **cả ba** đường/vùng, không
đường nào bị ép sát mép. A duyệt bằng mắt, đây là chỗ không tự động hoá được.

---

## Bước 6 — ACF/PACF *(chờ QĐ-010)*

### Prompt

```
Vẽ ACF và PACF đại diện cho mỗi môi trường, tới lag 48 (4 giờ).

Cẩn thận chỗ này: chuỗi đã căn lưới CÒN NaN (cụm dài hơn 2 điểm không được nội
suy). Hàm acf thông thường không nhận NaN, và dropna() trước khi tính sẽ CO TRỤC
THỜI GIAN LẠI - lag 1 sau khi dropna có thể là hai điểm cách nhau 2 giờ thật.

Tính tương quan tại lag k bằng cách chỉ dùng các cặp (t, t+k) mà cả hai đều
không NaN, giữ nguyên khoảng cách thời gian thật. Ghi rõ trong log đã xử lý NaN
thế nào và bao nhiêu phần trăm cặp bị bỏ ở mỗi lag.

"Đại diện" nghĩa là gì thì phải nói rõ: chuỗi trung vị theo tiêu chí nào, hay
trung bình ACF trên toàn bộ chuỗi. Đừng chọn tay một chuỗi đẹp.
```

### Lệnh
```bash
python scripts/fig_acf.py --env all
```

### Phải thấy
ACF suy giảm dần và có đỉnh quanh lag 288 nếu chu kỳ ngày lộ ra ở lag đó — nhưng
**đừng ép hình phải có đỉnh đó**. Không có chu kỳ ngày rõ cũng là kết quả, và với E3
thì mốc thời gian tương đối làm chu kỳ ngày khó đọc hơn hai môi trường kia.

---

## Bước 7 — Burstiness *(chờ QĐ-010)*

### Prompt

```
Tính hệ số biến thiên CV = std/mean cho từng chuỗi, ba môi trường, vẽ phân phối
CV của ba môi trường trên cùng một hình.

Báo cáo TRUNG VỊ và IQR của CV, không phải trung bình. Bộ lọc gan_chet đã bỏ mọi
chuỗi có mean dưới 1.0 nên CV không nổ, nhưng một chuỗi mean 1.01 vẫn kéo trung
bình đi rất xa.

Ghi vào log: môi trường nào bursty nhất, và chênh lệch có đủ lớn để dùng làm
biến phân tầng ở GĐ3 không.
```

### Lệnh
```bash
python scripts/fig_burstiness.py --env all
```

---

## Bước 8 — Log và nghiệm thu

### Prompt

```
Viết research-log/YYYY-MM-DD-gd2-dac-trung.md theo mẫu research-log/_template.md.

Phải có:
- Bảng số dòng ma trận đặc trưng, ba môi trường x ba horizon, kèm cột đối chiếu
  với catalog.parquet
- Kết quả bốn phép kiểm rò rỉ R1-R4, và kết quả từng lần phá code có chủ ý ở
  Bước 2
- Cách xử lý NaN khi tính ACF, kèm tỉ lệ cặp bị bỏ
- Caption hình phân phối: đã chọn cách biểu diễn nào và vì sao
- Chỗ nào chưa chắc, chỗ nào phải hỏi A

Không viết "đã hoàn thành" cho mục nào chưa chạy được lệnh kiểm.
```

### Lệnh
```bash
python scripts/check_gd2.py
pytest tests/ -v
```

### Phải thấy
```
ĐẠT — bộ đặc trưng GĐ2 khớp protocol mục 8, không phát hiện rò rỉ.
```

Chưa ĐẠT thì **đừng báo xong**. Đó là quy tắc đã áp ở GĐ1 và nó đã hiệu quả.

---

## Tóm tắt thứ tự

| Bước | Việc | Phụ thuộc |
|---|---|---|
| 0 | Kiểm môi trường, `check_gd1.py` còn ĐẠT | — |
| 0b | Bù hai việc treo của GĐ1 | — |
| 1 | `src/cwp/features/` | QĐ-010 cho phần lịch |
| 2 | `tests/test_features.py` + phá code kiểm ngược | Bước 1 |
| 3 | Ma trận đặc trưng, khớp 9 con số neo | Bước 1, 2 |
| 4 | Thống kê mô tả | — |
| 5 | **Hình phân phối target — điều kiện qua cổng** | QĐ-010 |
| 6 | ACF/PACF | QĐ-010 |
| 7 | Burstiness | QĐ-010 |
| 8 | Log + `check_gd2.py` | tất cả |

Bước 0, 0b, 2, 3, 4 làm được ngay. Bước 1 làm được phần lag/rolling/sai phân, để
phần lịch lại. Vướng quá 2 giờ thì dừng và hỏi A.
