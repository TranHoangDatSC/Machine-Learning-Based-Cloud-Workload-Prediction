# Giao thức nghiên cứu

**Trạng thái:** ĐÃ CHỐT — 2026-08-30
**Sửa đổi:** chỉ qua `decisions.md`, kèm lý do và ngày. Không sửa im lặng.

> Tài liệu này chốt luật chơi **trước khi nhìn thấy bất kỳ kết quả model nào**.
> Mục đích là chặn việc điều chỉnh tiêu chí cho khớp với kết quả đẹp — lỗi phổ biến
> nhất khiến một nghiên cứu thực nghiệm mất giá trị.
>
> Nếu trong quá trình chạy phát hiện giao thức có chỗ sai, **dừng lại, ghi vào
> `decisions.md`, sửa ở đây, rồi chạy lại từ đầu**. Không chạy tiếp với luật đã đổi.

---

## 1. Bài toán

Dự đoán một bước và nhiều bước mức sử dụng CPU của một đơn vị tính toán (VM hoặc
máy vật lý) trong hạ tầng đám mây, dựa trên lịch sử sử dụng tài nguyên của chính
đơn vị đó.

**Không** phải bài toán phân loại, **không** phải phát hiện bất thường, **không**
phải dự đoán job failure.

## 2. Câu hỏi nghiên cứu

| Mã | Câu hỏi | Thí nghiệm |
|---|---|---|
| RQ1 | Mô hình ML nào dự đoán workload tốt nhất, và có vượt được baseline naive không? | TN-A |
| RQ2 | Hiệu năng thay đổi thế nào giữa các môi trường đám mây khác nhau? | TN-A |
| RQ3 | Model train trên môi trường A có generalize sang môi trường B không, và thành phần nào của tín hiệu thì transfer được? | TN-B |

RQ1 và RQ2 dùng chung kết quả TN-A, khác nhau ở cách đọc: RQ1 đọc theo cột model,
RQ2 đọc theo cột môi trường.

## 3. Dữ liệu

| Mã | Nguồn | Phạm vi dùng |
|---|---|---|
| E1 | Bitbrains fastStorage | Toàn bộ 1.250 VM |
| E2 | Bitbrains Rnd | **Chỉ `2013-8`**, 500 VM |
| E3 | Alibaba v2018 `machine_usage` | **Mẫu phân tầng 500 máy** trên 4.023 |

Lý do giới hạn E2 và E3: xem `decisions.md` mục QĐ-003. Dữ liệu còn lại giữ nguyên
trên đĩa, dùng cho kiểm tra tính vững nếu còn thời gian.

### Mẫu phân tầng E3 — ĐÃ ĐÓNG BĂNG

Danh sách 500 máy cố định ở **`config/e3_machines.txt`**, đã commit vào repo. Mọi
lần chạy E3 **phải đọc đúng tệp này**, không được tự chọn lại mẫu.

Cách sinh danh sách (đã chạy một lần, `scripts/freeze_e3_sample.py`):
sắp xếp 4.023 máy theo `machine_id` → xếp 5 tầng theo rank của CPU% trung bình →
lấy 100 máy mỗi tầng với `random_state = 42`.

> **Vì sao phải đóng băng.** Bản đặc tả cũ chỉ ghi `random_state = 42`. Chưa đủ:
> `.sample()` chọn theo **vị trí**, mà vị trí phụ thuộc **thứ tự** danh sách máy —
> thứ tự đó lại phụ thuộc cách hiện thực xây bảng trung bình.
>
> Ngày 2026-09-09, A và B chạy hai bản hiện thực **đều đúng đặc tả** nhưng chỉ trùng
> nhau **56/500 máy**. Thống kê gộp vẫn lệch dưới 0,05% — phép phân tầng làm đúng
> việc của nó — nhưng hai bên đang đo hai quần thể khác nhau, nên con số E3 của B
> không kiểm chứng được code của B.
>
> Đây cùng loại lỗi với Bảng 6 bài HJS phân tích ở `tu-bai-cu-den-bai-nay.md` mục 3:
> hai con số trông so được nhưng đo hai thứ khác nhau. Chi tiết: `decisions.md`
> QĐ-009.

Đọc danh sách bằng `scripts/freeze_e3_sample.load_frozen()`. Dùng danh sách cố định
cũng bỏ được lượt quét thứ nhất trên tệp 9 GB.

## 4. Biến mục tiêu

**CPU%, thang 0–100.**

| Môi trường | Cột |
|---|---|
| E1, E2 | `CPU usage [%]` |
| E3 | `cpu_util_percent` |

**Không dùng** `CPU usage [MHZ]`: phụ thuộc số core và tốc độ core của từng VM nên
không so sánh được giữa các môi trường, làm RQ3 vô nghĩa.

### Trần 100 là kiểm duyệt, và nó bất đối xứng — QĐ-011

> Bổ sung 2026-09-09.

Bitbrains ghi CPU% vượt 100 (máy nhiều core), Alibaba thì không. Mục 6 bước 1 clip về
`[0, 100]`, nên sau khi căn lưới:

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Điểm bằng đúng 100 | **5,1238%** | **2,2788%** | **0,0000%** |
| Phân vị 95 của CPU% | **100,0000** | 60,0667 | 61,2667 |

Phân vị 95 của E1 chính là trần. **Thang 0–100 giữ nguyên** — nó là định nghĩa của
biến mục tiêu, đổi nó là đổi bài toán. Nhưng ba điều phải làm:

- Hình phân phối ở GĐ2 chú thích rõ cột dựng đứng tại 100 của E1/E2.
- Diễn giải chỉ số ở vùng tải cao của E1/E2 phải nhắc rằng dữ liệu đã bị chặn trần;
  model dự đoán vượt 100 bị phạt dù có thể đúng.
- Limitations nêu rằng một phần của kết luận "E3 dễ dự đoán hơn" đến từ việc E3
  không chạm trần, chứ không chỉ từ hiệu ứng tổng hợp ở QĐ-004.

## 5. Lưới thời gian

**300 giây (5 phút) cho cả ba môi trường.**

- Căn về lưới tuyệt đối `floor(t / 300)`. E1, E2 vốn đã 300 s; E3 hạ tần từ khoảng
  10 s.
- Giá trị mỗi bucket bằng **trung bình** các mẫu rơi vào bucket đó.
- Bucket không có mẫu nào thì để `NaN`. Cách xử lý `NaN` nằm ở mục 6, không làm ở
  bước này.

## 6. Làm sạch và xử lý lỗ hổng

> Sửa theo QĐ-008 ngày 2026-09-08. Quy tắc cũ *"ffill 3 bước rồi cắt chuỗi"* đã bị
> bãi bỏ vì phá huỷ 74% dữ liệu E2 và 99% dữ liệu E3. Lý do đầy đủ và bằng chứng
> định lượng ở `decisions.md` QĐ-008.

Áp dụng theo đúng thứ tự này:

1. **Clip** CPU% về `[0, 100]`. Ghi lại tỉ lệ bị clip mỗi môi trường.
2. **Mask** giá trị bất thường của E3: `disk_io_percent` bằng `-1` hoặc `101` thì
   cho về `NaN`.
3. **Bỏ cột** `mem_gps` và `mkpi` của E3 (rỗng 79%).
4. **Căn lưới** 5 phút như mục 5.
5. **Cắt cửa sổ 8 ngày** như mục 7.
6. **Nội suy lỗ hổng ngắn.** Nội suy tuyến tính những cụm `NaN` dài **≤ K = 2 điểm**
   (tối đa 10 phút). Cụm dài hơn giữ nguyên `NaN`.
   - **Không dùng forward-fill.** ffill tạo ra đoạn phẳng, làm autocorrelation tăng
     giả tạo — mà autocorrelation là đại lượng trung tâm của RQ3.
   - `K` là tham số cấu hình trong `config/preprocess.yaml`, không chôn trong code.
7. **Lọc chuỗi** — loại nếu vi phạm bất kỳ điều kiện nào:
   - Không có mẫu nào nằm trong cửa sổ 8 ngày (`ngoai_cua_so`)
   - CPU% trung bình dưới 1,0 — chuỗi gần chết (`gan_chet`)
   - Số giá trị phân biệt từ 2 trở xuống — chuỗi hằng (`hang`)
   - Dưới **500 dòng huấn luyện hợp lệ ở h = 12** (`it_dong`), theo định nghĩa ở
     mục 8
8. **Không cắt chuỗi tại lỗ hổng.** Chuỗi giữ nguyên độ dài, kể cả khi còn `NaN`.
   Việc loại bỏ diễn ra ở mức **dòng huấn luyện**, xem mục 8.

**Bắt buộc báo cáo cho từng môi trường:**

| Cột | Vì sao bắt buộc |
|---|---|
| Số chuỗi vào | Mốc gốc |
| Số bị loại theo **từng** lý do, bốn cột tách riêng | Gộp lại thì không truy được nguyên nhân |
| Số chuỗi còn lại | |
| Số dòng huấn luyện hợp lệ ở mỗi horizon | Con số thực sự dùng để train |
| **Tỉ lệ điểm được nội suy** | Đây là can thiệp vào dữ liệu, phải khai báo |
| Tỉ lệ mẫu bị clip | Kiểm chứng bước làm sạch có chạy |

Bảng này vào phần Dữ liệu của paper.

## 6b. Sản phẩm của bước tiền xử lý

> Bổ sung 2026-09-08. Trước đó chỉ ghi "sinh `catalog.parquet`, một dòng mỗi chuỗi"
> mà không nói cột nào — không đủ để A và B ra cùng con số.

### `data/processed/` — chuỗi đã xử lý

Định dạng **parquet**, một tệp mỗi môi trường: `E1.parquet`, `E2.parquet`,
`E3.parquet`. Dạng bảng dài, mỗi dòng là một điểm thời gian của một chuỗi.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `env` | string | `E1`, `E2` hoặc `E3` |
| `series_id` | string | Định danh chuỗi, **duy nhất trong toàn dự án** |
| `bucket` | int64 | Số hiệu bucket 5 phút tuyệt đối, `floor(t / 300)` |
| `y` | float64 | CPU%, thang 0–100, đã clip và đã nội suy lỗ hổng ngắn |
| `is_interp` | bool | `True` nếu điểm này do nội suy sinh ra, không phải quan sát thật |

`y` được phép là `NaN` — đó là lỗ hổng dài không nội suy. Không xoá dòng đó.

**`is_interp` là cột bắt buộc.** Không có nó thì không tính được tỉ lệ nội suy để
báo cáo, và không chạy được kiểm tra độ vững K=0.

### Quy tắc đặt `series_id`

| Môi trường | Dạng | Ví dụ |
|---|---|---|
| E1 | `E1_<tên tệp>` | `E1_137` |
| E2 | `E2_<tháng>_<tên tệp>` | `E2_2013-8_137` |
| E3 | `E3_<machine_id>` | `E3_m_1932` |

E2 **bắt buộc** có phần tháng. Tên tệp Rnd trùng nhau giữa ba tháng; thiếu phần này
là rò rỉ định danh.

### `data/catalog.parquet` — một dòng mỗi chuỗi

Gồm **mọi** chuỗi đã xét, kể cả chuỗi bị loại. Đây là bảng A dùng để nghiệm thu.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `env` | string | `E1`, `E2`, `E3` |
| `series_id` | string | Như trên |
| `kept` | bool | `True` nếu chuỗi được giữ |
| `reject_reason` | string | `ngoai_cua_so`, `gan_chet`, `hang`, `it_dong`, hoặc `""` nếu giữ |
| `n_points` | int64 | Số điểm không NaN trong cửa sổ, sau nội suy |
| `n_interp` | int64 | Số điểm do nội suy sinh ra |
| `valid_rows_h1` | int64 | Số dòng huấn luyện hợp lệ ở h=1 |
| `valid_rows_h6` | int64 | Số dòng huấn luyện hợp lệ ở h=6 |
| `valid_rows_h12` | int64 | Số dòng huấn luyện hợp lệ ở h=12 |
| `mean` | float64 | CPU% trung bình của chuỗi, tính trên điểm quan sát thật |
| `p50` | float64 | Trung vị |
| `std` | float64 | Độ lệch chuẩn |
| `n_clipped` | int64 | Số mẫu thô bị clip về 100 trước khi căn lưới |
| `built_on` | string | Tên máy sinh ra dòng này, lấy bằng `platform.node()` |
| `built_at` | string | Thời điểm sinh, ISO 8601 tới giây: `datetime.now().isoformat(timespec="seconds")` |

Chuỗi bị loại vẫn phải có đủ các cột thống kê, điền giá trị tính được đến thời điểm
bị loại. Chỉ `reject_reason` phân biệt giữ hay loại — **không xoá dòng**.

### Vì sao cần `built_on` và `built_at`

> Bổ sung 2026-09-08.

`catalog.parquet` **được commit** vào Git, còn `data/processed/*.parquet` thì
**không** (quá lớn). Hệ quả: bảng tổng hợp đi được giữa hai máy nhưng dữ liệu thì
không. Nếu A chạy `--env E2` trên máy mình trong khi dòng E1 trong catalog đến từ
máy B, thì catalog trở thành **khảm từ nhiều lần chạy** mà không ai nhận ra.

Chuyện này đã xảy ra thật ngày 2026-09-08: catalog có E1 do B tính, E2 do A tính.
Cả hai đều khớp tham chiếu nên không lộ ra, nhưng về nguyên tắc tái lập thì đó là
một bảng không có nguồn gốc rõ ràng.

Hai cột này khiến tình trạng đó **hiện ra thay vì im lặng**:

| Tình huống | `check_gd1.py` xử lý |
|---|---|
| Một lần chạy `--env all`, một máy | ĐẠT |
| Cùng một máy, chạy từng env vào các thời điểm khác nhau | CẢNH BÁO — bình thường khi đang làm, nhưng bản nộp cuối phải là một lần chạy |
| **Nhiều máy khác nhau** | **TRƯỢT** — không xác định được kết quả sinh ra trong môi trường nào |

Bản nộp cuối của GĐ1 phải sinh bằng **một lệnh `--env all` trên một máy**.

### Kiểm tra trước khi báo xong

B chạy lệnh sau và phải ra ĐẠT trước khi báo hoàn thành GĐ1:

```bash
python scripts/check_gd1.py
```

Script đối chiếu `catalog.parquet` với số liệu tham chiếu ở
`results/tables/reference_E*.json` theo ngưỡng ghi trong `research-log/gate-gd1.md` mục 3.3.

## 7. Cửa sổ thời gian chung

E3 chỉ có 8 ngày. Thí nghiệm chính dùng **8 ngày đầu** của cả ba môi trường.

**Cửa sổ là toàn cục theo từng môi trường**, tính từ mốc thời gian sớm nhất của môi
trường đó — không phải từ điểm đầu của mỗi chuỗi. Cụ thể: `b0 = min` bucket trên
toàn bộ chuỗi của môi trường, cửa sổ là `[b0, b0 + 2304)`.

Lý do: giữ mọi chuỗi cùng phủ một khoảng lịch, nên đặc trưng giờ-trong-ngày và
thứ-trong-tuần so sánh được giữa các chuỗi, và phát biểu "8 ngày đầu của trace" đúng
theo nghĩa đen. 92% chuỗi E1 và 99% chuỗi E2 vốn đã bắt đầu cùng một mốc; số bắt đầu
muộn bị loại với lý do `ngoai_cua_so` và phải được báo cáo.

Chuỗi dài hơn của E1 và E2 chỉ dùng cho phân tích bổ sung về chu kỳ tuần, và phải
ghi rõ là phân tích bổ sung.

## 8. Đặc trưng

Chỉ dùng lịch sử của **chính chuỗi đó**. Không dùng thông tin từ chuỗi khác, không
dùng thông tin tương lai.

**Đúng 19 đặc trưng, không thừa không thiếu.** Tên cột chốt theo QĐ-010 để hai bản
hiện thực so được với nhau:

| Nhóm | Tên cột | Số lượng |
|---|---|---:|
| Lag | `lag_1, lag_2, lag_3, lag_6, lag_12, lag_24` (5 phút đến 2 giờ) | 6 |
| Rolling cửa sổ 6 | `roll_mean_6, roll_std_6, roll_min_6, roll_max_6` | 4 |
| Rolling cửa sổ 12 | `roll_mean_12, roll_std_12, roll_min_12, roll_max_12` | 4 |
| Sai phân | `diff_1` = `y_t` trừ `y_{t-1}` | 1 |
| Lịch | `hour_sin, hour_cos, dow_sin, dow_cos` | 4 |

Mọi thống kê rolling tính **chỉ trên quá khứ**, không bao gồm điểm hiện tại: giá trị
tại `t` lấy trên đúng `w` điểm `y[t−w] … y[t−1]`. Cửa sổ thiếu điểm hoặc dính `NaN`
đều ra `NaN` — **không dùng `min_periods=1`**.

Lag và rolling tính **theo từng chuỗi**. Một tệp `data/processed/` chứa hàng trăm
chuỗi nối nhau; thiếu `groupby(series_id)` thì đuôi chuỗi này chảy vào đầu chuỗi kia.

### Ba quy ước — QĐ-010

Chốt vì hai bản hiện thực đều đúng đặc tả mà vẫn ra số khác nhau:

- **`ddof = 1`** cho `roll_std_*` và cho hệ số biến thiên. pandas mặc định 1, numpy
  mặc định 0.
- **Gốc `dow`:** epoch 1970-01-01 là thứ Năm, `((t // 86400) + 4) % 7` → **0 là Chủ
  Nhật**. (Nhãn sửa 2026-09-09, công thức giữ nguyên — xem đính chính ở QĐ-010.)
- **Cụm `NaN` chạm mép cửa sổ không nội suy**, và không ngoại suy để hai bên khớp.

### Đặc trưng lịch — mốc thời gian E3 là tương đối

`bucket × 300` là epoch giây với E1 và E2. Với **E3 thì không**: Alibaba ghi giây kể
từ lúc bắt đầu trace (`b0 = 0`), không mang thông tin ngày thật.

> **E1 và E2 vận hành ở UTC+2 — QĐ-011 điểm 6, bổ sung 2026-09-09.** `b0` của E2 là
> 4.584.360 → `2013-07-31T22:00:00Z`, đúng bằng **00:00 giờ Amsterdam mùa hè**. Trace
> bắt đầu đúng nửa đêm giờ địa phương, nên "một ngày" trong dữ liệu E1/E2 bắt đầu ở
> giờ UTC 22. Giữ UTC, nhưng mọi phát biểu về giờ trong bài phải ghi rõ **"giờ UTC"**;
> với `dow` thì lệch 2 giờ đủ để đẩy hoạt động nửa đêm sang ngày hôm trước.

Theo QĐ-010: E1 và E2 dùng **UTC**; E3 vẫn sinh 4 đặc trưng lịch nhưng `hour` của nó
mang nghĩa *"giờ kể từ lúc bắt đầu trace"*, **pha chưa biết**, và `dow` **không diễn
giải được theo lịch tuần**. Không bịa ngày bắt đầu cho Alibaba.

Lệch pha hằng số vô hại với TN-A vì model tự học được pha, nhưng chí mạng với TN-B.
Vì vậy **TN-B chạy hai biến thể, có và không có 4 đặc trưng lịch**.

> **E1 và E2 không có chu kỳ ngày — QĐ-012 điểm 4, đo ở GĐ2 Bước 6.** ACF của chúng
> không bao giờ xuống âm đáng kể, và mức nhô tại lag 288 (+0,068 và +0,069 so với hai
> lag láng giềng) xấp xỉ đúng mức nhô của **nhịp một giờ** — mà 288 = 24 × 12 cũng là
> bội số của 12. Nghĩa là giá trị tại lag 288 của E1/E2 giải thích hết bằng nhịp giờ,
> không cần giả định thêm chu kỳ ngày nào. Chỉ E3 có sóng ngày thật.
>
> Dự báo cho GĐ4: biến thể "bỏ lịch" gần như **không đổi gì với E1 và E2**, chỉ ảnh
> hưởng E3. Quan sát đúng như vậy là **xác nhận**, không phải phát hiện mới; nếu bỏ
> lịch mà E1/E2 đổi nhiều thì phải đi tìm nguyên nhân khác. Giữ chúng lại là
có cơ sở: ACF tại lag 288 (24 giờ) của E3 là 0,60 so với 0,13 của E1 và E2 — chu kỳ
ngày của E3 rất rõ và đọc được kể cả khi pha chưa biết.

### Dòng huấn luyện hợp lệ

> Bổ sung theo QĐ-008.

Cửa sổ đặc trưng sâu nhất là **24 bước** (lag `t-24`). Một dòng huấn luyện tại thời
điểm `t` với horizon `h` là **hợp lệ** khi và chỉ khi:

- mọi điểm trong `[t − 24, t]` đều không `NaN`, **và**
- target tại `t + h` không `NaN`

Dòng không hợp lệ thì **bỏ dòng đó**, không cắt chuỗi và không lấp thêm.

Hệ quả cần nhớ: **một điểm `NaN` đơn lẻ làm hỏng 25 dòng.** Đó là lý do bước nội suy
lỗ hổng ngắn ở mục 6 tồn tại — nó thu hồi phần lớn số dòng mà không bịa ra động lực
học.

> **Lọc dòng theo luật trên, KHÔNG bằng `dropna()` trên ma trận đặc trưng.** Hai thứ
> đó không tương đương: 19 đặc trưng chỉ chạm 15 điểm trong cửa sổ (`t−24`,
> `t−12..t−1`, `t`), còn `t−23` đến `t−13` thì không đặc trưng nào dùng. `dropna`
> lỏng hơn — đo được thừa 1.513 dòng ở E2 h=1 và 7.461 dòng ở E3 h=1. **E1 khớp kể cả
> khi làm sai**, nên phải kiểm cả ba môi trường. Xem QĐ-010.

## 9. Chia dữ liệu

**Chia theo thời gian. Tuyệt đối không shuffle.**

Với mỗi chuỗi, theo trục thời gian: 70% train, 15% validation, 15% test.

> **Hai quy ước chốt ở QĐ-013, bổ sung 2026-09-10.** Câu trên chưa đủ chặt để hai bản
> hiện thực độc lập ra cùng con số.
>
> 1. **Ranh giới tính theo bucket**, không theo số dòng hợp lệ: train `[0, 1612)`,
>    validation `[1612, 1957)`, test `[1957, 2304)` — offset so với `b0`. Cửa sổ 8
>    ngày là toàn cục theo môi trường (mục 7) nên đây là một lát cắt thời gian giống
>    hệt nhau ở mọi chuỗi.
> 2. **Một dòng thuộc tập `S` khi cả `t` và `t+h` nằm trong `S`.** Dòng vắt qua ranh
>    giới bị **loại**. Gán theo `t` thôi là rò rỉ: dòng cuối tập train sẽ có target
>    rơi vào validation hoặc test. Giá phải trả là `số_chuỗi × 2 × h` dòng, dưới 1,1%
>    ở `h = 12`.

Chọn siêu tham số **chỉ trên validation**. Test chỉ chạm vào một lần duy nhất, khi
đã chốt toàn bộ mô hình.

Kiểm định chéo dùng **rolling-origin** 5 fold trên phần train cộng validation.

## 10. Horizon

`h` nhận giá trị 1, 6, 12 — tương ứng 5 phút, 30 phút, 60 phút.

Dự đoán nhiều bước theo kiểu **direct**: mỗi horizon một model riêng. Không dùng
recursive vì sai số tích luỹ và khó quy trách nhiệm.

## 11. Mô hình

| Nhóm | Mô hình | Vai trò |
|---|---|---|
| Baseline | Naive / persistence, `ŷ = y_t` | **Mốc bắt buộc.** Mọi con số đều so với nó |
| Baseline | Moving average, cửa sổ 6 | Mốc thứ hai |
| Baseline | Seasonal naive, `ŷ = y_{t-288}` (cùng giờ hôm trước) | Mốc mùa vụ |
| Tuyến tính | Linear Regression, Ridge | Cận dưới của họ ML |
| Cây | Random Forest | |
| Cây | XGBoost | |
| Kernel | SVR nhân RBF | Chỉ chạy trên mẫu con nếu quá chậm |

**Ngoài scope chính:** LSTM/GRU. Chỉ làm nếu hoàn thành toàn bộ phần trên và còn
thời gian. Nếu làm mà thua XGBoost thì **báo cáo đúng như vậy** — đó là kết quả hợp
lệ và phổ biến trên dữ liệu dạng này.

**Chiến lược huấn luyện:** global model — một model học trên nhiều chuỗi của cùng
một môi trường, không phải mỗi chuỗi một model.

**Đếm cho đúng: bảng trên có 7 dòng nhưng 8 model** — dòng *"Linear Regression,
Ridge"* chứa hai. Xem mục 13 và QĐ-015.

### Lưới siêu tham số — QĐ-015

> Bổ sung 2026-09-11, khai báo sau khi GĐ3 chạy xong.

Giao thức bản đầu không chốt lưới nào. Lưới thực dùng ở GĐ3 do B chọn theo chi phí đo
được; **nguồn thật là `src/cwp/models/registry.py`**, bảng dưới chỉ để đọc:

| Model | Lưới | Ghi chú |
|---|---|---|
| `lr` | — | không có siêu tham số |
| `ridge` | `alpha ∈ {0,01 · 0,1 · 1 · 10 · 100}` | |
| `rf` | `max_depth ∈ {8, 16}` | **50 cây**, `min_samples_leaf = 5` |
| `xgb` | `(depth 4, 300) · (depth 8, 300) · (depth 8, 600)` | |
| `svr` | `C ∈ {1, 10}` | RBF, mẫu con 10.000 dòng (QĐ-014 điểm 2) |

Chọn trên **validation**, rolling-origin 5 fold expanding theo QĐ-014 điểm 1.

**Hạn chế bắt buộc nêu trong paper.** Siêu tham số chốt nằm ở **mép lưới** ở gần như
mọi tổ hợp. Đếm đủ cả hai đầu (đính chính 2026-09-11, bản đầu chỉ đếm biên trên):

| Model | Biên trên | Biên dưới | Chạm mép |
|---|---:|---:|---:|
| `rf` (`max_depth`) | 7/9 | 2/9 | 9/9 |
| `svr` (`C`) | 7/9 | 2/9 | 9/9 |
| `xgb` (`depth`) | 6/9 | 3/9 | 9/9 |
| `xgb` (`n_estimators`) | 1/9 | 8/9 | 9/9 |
| `ridge` (`alpha`) | 4/9 | 5/9 | 9/9 |

`rf` và `svr` chỉ có hai ứng viên nên mọi lựa chọn tất yếu ở mép. Khi lựa chọn nằm ở
mép thì tối ưu thật có thể nằm ngoài — nghĩa là ML đang bị giới hạn bởi **lưới và ngân
sách tính toán**, không phải bởi dữ liệu. Ngoại lệ đáng chú ý: trục `n_estimators` của
`xgb` nghiêng hẳn về giá trị **thấp** (8/9 chọn 300), nên nới số cây gần như chắc chắn
không đổi được gì.

Vì vậy phát biểu đúng của RQ1 là: *"với lưới này và ngân sách này, ML không vượt naive
trên E1 và E2"* — không phải một kết luận về năng lực của họ thuật toán.

**Không nới lưới rồi chạy lại ở GĐ3.** Nới lưới *sau khi đã thấy ML thua* rơi đúng vào
điều mục 17 cam kết không làm. Nếu muốn kiểm tra độ vững thì làm ở GĐ5, **khai báo
lưới mới trước khi chạy**, và **báo cáo cả hai kết quả** chứ không thay thế.

### Seasonal naive lấy giá trị từ đâu — ghi chú hiện thực

> Bổ sung 2026-09-10, sau khi rà sẵn sàng GĐ3.

`ŷ = y_{t-288}` **không tính được từ `data/features/`**: bộ 19 đặc trưng ở mục 8 sâu
nhất chỉ tới `lag_24`, không có `lag_288`. Phải nối ngược về `data/processed/{env}.parquet`
theo khoá `(series_id, bucket - 288)`.

Điều đó **không** kéo theo việc phải sửa luật dòng hợp lệ. Đo được tỉ lệ dòng có sẵn
`y_{t-288}`, chia theo tập của mục 9:

| | train | validation | **test** |
|---|---:|---:|---:|
| E1 | 83,03% | 100,00% | **100,00%** |
| E2 | 82,59% | 99,99% | **100,00%** |
| E3 | 81,37% | 99,98% | **99,57%** |

Phần thiếu nằm gần như trọn trong **train**, vì 288 bucket đầu của mỗi chuỗi rơi vào
12,5% đầu của cửa sổ 8 ngày. Trên **test** — nơi mọi con số của paper được tính —
seasonal naive xác định được ở gần như toàn bộ dòng.

Ba điều bắt buộc khi hiện thực:

- **Không** thêm `lag_288` vào bộ đặc trưng. Thêm một đặc trưng ngoài mục 8 là đổi
  giao thức; và không model nào cần nó, chỉ baseline này cần.
- **Không** siết luật dòng hợp lệ thành `t ≥ b0 + 288`. Làm thế sẽ đổi cả chín neo số
  dòng đã kiểm chéo ở GĐ1 và GĐ2 — cái giá quá lớn cho một baseline.
- **728 dòng test của E3** (0,43%) không có `y_{t-288}`. Phải xử lý **hiện** chứ không
  lặng lẽ: hoặc loại chúng khỏi chỉ số của riêng seasonal naive và ghi rõ tỉ lệ, hoặc
  tính mọi model trên đúng tập con chung. Chọn cách nào cũng được, miễn **ghi ra** và
  dùng nhất quán cho cả ba môi trường.

## 12. Chỉ số đánh giá

| Chỉ số | Dùng vì |
|---|---|
| MAE | Chỉ số chính, cùng đơn vị với target |
| RMSE | Phạt lỗi lớn, nhạy với burst |
| SMAPE | Thay cho MAPE |
| **MASE** | **So được giữa các môi trường có mức tải khác nhau** |
| R² | Tỉ lệ phương sai giải thích được |

**Không dùng MAPE.** Trên 40% mẫu Bitbrains có giá trị gần 0, mẫu số nổ.

MASE lấy naive một bước trên tập train làm mẫu số. Đây là chỉ số chính khi so sánh
**giữa các môi trường**, vì nó đã chuẩn hoá theo độ khó nội tại của từng chuỗi.

Gộp kết quả nhiều chuỗi bằng **trung vị** kèm IQR, không dùng trung bình, vì phân
phối lệch nặng.

> **Ba định nghĩa chốt ở QĐ-013, bổ sung 2026-09-10.**
>
> - **Cách gộp:** tính chỉ số **riêng cho từng chuỗi trước**, rồi lấy trung vị và IQR
>   trên tập chuỗi. Không gộp mọi dòng của mọi chuỗi vào một dãy rồi tính một chỉ số —
>   cách đó cho chuỗi tải cao chi phối con số gộp, cùng cơ chế đã làm ACF lag 1 của E1
>   nở từ 0,6674 lên 0,9586 ở GĐ2.
> - **MASE:** mẫu số là trung bình `|y_t − y_{t−1}|` trên phần **train** của chính
>   chuỗi đó, chỉ lấy cặp mà cả hai đầu không NaN, và **không phụ thuộc horizon**.
>   Chuỗi có mẫu số bằng 0 thì loại khỏi phần gộp và báo số bị loại.
> - **SMAPE:** `100 × mean(|y−ŷ| / ((|y|+|ŷ|)/2))`, số hạng `0/0` tính là **0**.
>   **R²:** chuỗi có `SS_tot = 0` thì loại khỏi phần gộp và báo số bị loại.

## 13. Thí nghiệm A — trong cùng môi trường

Train và test trên cùng một môi trường.

Tổ hợp: **3 môi trường × 8 model × 3 horizon = 72**.

> **Đính chính 2026-09-11 (QĐ-015).** Bản cũ ghi *"7 model"*. Đó là đếm **số dòng**
> của bảng ở mục 11, mà dòng *"Linear Regression, Ridge"* chứa **hai** model. Đếm
> đúng là 8: ba baseline + `lr`, `ridge`, `rf`, `xgb`, `svr`. GĐ3 đã chạy và báo cáo
> đủ tám.

Trả lời RQ1 và RQ2.

### Phân tầng burstiness khi báo cáo — QĐ-012

> Bổ sung 2026-09-10.

Ngoài bảng gộp, mọi bảng kết quả còn phải tách theo **ba tầng burstiness**, chia bằng
**tam phân vị của CV tính riêng trong từng môi trường**:

| Môi trường | thấp / vừa | vừa / cao |
|---|---:|---:|
| E1 | 0,256 | 0,849 |
| E2 | 0,285 | 0,943 |
| E3 | 0,258 | 0,321 |

**Không dùng một ngưỡng CV tuyệt đối chung cho ba môi trường.** Hai lý do đo được:
tương quan giữa CV và mức tải **đổi dấu** giữa Bitbrains (ρ = +0,375 và +0,249) và
Alibaba (ρ = −0,692), nên ngưỡng chung chọn ra hai nhóm máy khác loại; và tam phân vị
của E3 chỉ rộng 0,06, nằm gọn trong tầng thấp nhất của E1.

Mỗi bảng phân tầng báo kèm cột **`ti_le_cham_chan`** = `CV / √((100−m)/m)`, để phân
biệt một chuỗi ít bursty do bản chất với một chuỗi ít bursty do đã cụng trần thang đo.

**CV là biến báo cáo, không phải đặc trưng.** `results/tables/cv_gd2.csv` tính CV trên
toàn bộ cửa sổ 8 ngày, tức có cả phần rơi vào validation và test. Dùng để nhóm chuỗi
khi đọc bảng thì không sao. Nhưng dùng làm **đặc trưng**, làm **trọng số huấn luyện**,
hay làm **tiêu chí chọn model theo tầng** thì đó là rò rỉ — khi ấy bắt buộc tính lại
CV **chỉ trên cửa sổ train** của từng chuỗi, đúng nguyên tắc đã áp cho thống kê chuẩn
hoá N1 ở mục 14.

## 14. Thí nghiệm B — xuyên môi trường

Train trên môi trường nguồn, test trên môi trường đích, **không huấn luyện lại**.

Sáu cặp: E1→E2, E2→E1, E1→E3, E3→E1, E2→E3, E3→E2.

### Ba chế độ chuẩn hoá — trục chính của paper

> Giải thích chi tiết kèm số liệu chứng minh: `giai-thich-chuan-hoa.md`.
> Đọc file đó trước khi triển khai phần này.

Đây là phần quan trọng nhất. Chạy cả ba, báo cáo cả ba như một ablation.

| Chế độ | Target | Câu hỏi nó trả lời |
|---|---|---|
| **N0 — Thô** | CPU% nguyên bản | Đối chứng. Dự kiến thất bại nặng ở cặp Bitbrains và Alibaba |
| **N1 — Chuẩn hoá per-series** | z-score từng chuỗi | Bỏ mức tải, giữ biên độ tương đối |
| **N2 — Sai phân** | `y_{t+h}` trừ `y_t` | Chỉ còn động lực học thuần |

**Thống kê chuẩn hoá của N1 chỉ được tính trên cửa sổ train của chuỗi đó.** Dùng
thống kê toàn chuỗi là rò rỉ dữ liệu.

> **Năm quy ước chốt ở QĐ-016, bổ sung 2026-09-11.** Câu trên chưa đủ chặt để hai bản
> hiện thực độc lập ra cùng con số.
>
> 1. **`mu`, `sd` lấy trên cửa sổ train của chính chuỗi ĐÍCH**, bucket `[0, 1612)` của
>    chuỗi đó — không phải thống kê của môi trường nguồn. Hệ quả: RQ3 **không** được
>    phát biểu là *"zero-shot"*, mà là *"động lực học có transfer không, khi mỗi chuỗi
>    đích được chuẩn hoá bằng lịch sử của chính nó"*.
> 2. **Biến đổi `y` trước, rồi sinh lại 19 đặc trưng** từ chuỗi đã biến đổi; bốn đặc
>    trưng lịch giữ nguyên. Chỉ chuẩn hoá target mà giữ `lag_*` thô thì mức tải vẫn
>    vào model qua đặc trưng, và N1 hỏng **âm thầm**.
> 3. **Siêu tham số dùng lại của GĐ3** theo từng môi trường nguồn, không dò lại.
> 4. **Ba baseline là mốc cố định của môi trường đích**, giống nhau ở cả ba chế độ;
>    `naive` dưới N2 là `Δ̂ = 0`.
> 5. **Ba bất biến** (naive N0 ≡ naive N1, ma6 N0 ≡ ma6 N1, naive N2 với `Δ̂ = 0` ≡
>    naive N0) là phép kiểm bắt buộc, trùng tới ít nhất 9 chữ số thập phân.
>
> Mọi con số TN-B đo trên **đúng tập test của môi trường đích**, `[1957, 2304)`, cùng
> luật purge của QĐ-013 điểm 2.

Khi báo cáo, mọi dự đoán phải **đưa ngược về thang CPU% gốc** rồi mới tính chỉ số,
để ba chế độ so sánh được với nhau.

### Vì sao phần này quyết định giá trị của paper

Phân phối target lệch rất mạnh: trung vị E1 và E2 khoảng 1%, E3 khoảng 37%.

**Đã đo trên dữ liệu thật** — **498 chuỗi E3 của quần thể nghiên cứu**, horizon 1,
MAE trung vị theo chuỗi: một **hằng số** bằng mức tải trung bình của E1 áp lên E3 cho
MAE = **26,90**. Không model, không đặc trưng, không huấn luyện. Trong đó **62,6%** sai
số chỉ là chênh lệch mức tải. Để so sánh, naive persistence trong chính E3 cho
MAE = **4,35** — tốt hơn 6,2 lần.

> **Số cũ đo trên 833 chuỗi, sửa 2026-09-10 theo QĐ-012 điểm 6.** Bản trước ghi
> 28,64 / 63,4% / 5,76, đo trước khi QĐ-009 đóng băng mẫu 500 máy. Lập luận không đổi,
> và mạnh hơn một chút. Bảng đối chiếu đầy đủ ở QĐ-012.

> **Hai con số 26,90 và 4,35 đo trên CƠ SỞ KHÁC với GĐ4 — ghi chú 2026-09-11.**
> Chúng lấy hằng số trên **toàn** cửa sổ 8 ngày của E1 và chấm trên **mọi dòng hợp lệ**
> của E3. Cơ sở đó hợp lý cho một minh hoạ viết trước khi có QĐ-013, nhưng GĐ4 thì
> chấm trên **tập test** của môi trường đích và lấy hằng số trên **cửa sổ train** của
> nguồn (QĐ-016). Trên cơ sở GĐ4, cùng phép đo cho:
>
> | | hằng số | MAE hằng số | naive tại E3 | tệ hơn |
> |---|---:|---:|---:|---:|
> | cơ sở mục 14 (cũ) | 13,635 | **26,9049** | 4,3466 | 6,19× |
> | cơ sở GĐ4 (QĐ-016) | 13,480 | **28,2356** | 4,2955 | 6,57× |
>
> `scripts/reference_gd4.py` in ra cả hai để không ai phải đoán vì sao hai con số
> không khớp. **Lập luận không đổi, và mạnh hơn một chút ở cơ sở GĐ4.** Khi viết paper,
> trích con số nào cũng được — miễn **nói rõ cơ sở**, vì đây đúng cái bẫy
> `tu-bai-cu-den-bai-nay.md` mục 3 phân tích: hai con số trông so được nhưng đo hai
> thứ khác nhau.

Nghĩa là nếu chạy N0 thô và thu được MAE khoảng 27, con số đó **không nói lên điều gì**
về chất lượng model — một hằng số cũng đạt được. Kết luận "cross-environment
generalization thất bại" khi đó đúng nhưng rỗng.

Có N1 và N2 thì câu hỏi đổi thành: *hình dạng biến thiên của workload có transfer
giữa các datacenter không?* Câu này chưa có lời giải hiển nhiên, và là đóng góp thật
sự của bài.

## 15. Kiểm định thống kê

So sánh hai model trên cùng tập chuỗi: **Wilcoxon signed-rank** trên MAE theo từng
chuỗi. Mức ý nghĩa `alpha = 0,05`.

Khi so nhiều model cùng lúc: hiệu chỉnh Holm–Bonferroni.

**Không tuyên bố "model X tốt hơn model Y" nếu chưa có kiểm định.** Chênh lệch 2%
MAE trên trung vị hoàn toàn có thể là nhiễu.

## 16. Tái lập

- `random_state = 42` ở mọi chỗ có yếu tố ngẫu nhiên
- Mỗi lần chạy sinh một thư mục `runs/<ngày>_<thí nghiệm>_<model>_<env>/` kèm bản
  sao config đúng lúc chạy
- Phiên bản thư viện ghim trong `requirements.txt`
- Mọi số trong paper phải truy ngược được về một thư mục `runs/` cụ thể

## 17. Điều cam kết không làm

Ghi ra đây để tự ràng buộc:

- Không đổi metric sau khi thấy kết quả
- Không đổi ngưỡng lọc để có bảng đẹp hơn
- Không bỏ môi trường nào khỏi bảng vì kết quả xấu
- Không giấu việc baseline naive thắng model ML, nếu điều đó xảy ra
- Không chạy test nhiều lần rồi chọn lần tốt nhất
