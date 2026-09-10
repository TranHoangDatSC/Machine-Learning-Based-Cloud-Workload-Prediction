# Data card

Mọi số liệu dưới đây **đo trực tiếp trên dữ liệu**, không lấy từ tài liệu mô tả.

> ## Đọc kỹ trước khi trích số — hai quần thể khác nhau
>
> Theo **QĐ-011** (2026-09-09). Tệp này chứa số của **hai** quần thể, và chúng lệch
> nhau nhiều. Trích nhầm là viết sai phần Dữ liệu của paper.
>
> | | **Thô** | **Nghiên cứu** |
> |---|---|---|
> | Là gì | toàn bộ trace, trước cửa sổ 8 ngày và trước bộ lọc chuỗi | chuỗi được giữ, trong cửa sổ 8 ngày |
> | Đo khi nào, thế nào | 2026-08-30, trên **mẫu ngẫu nhiên**, trước QĐ-003/008/009 | 2026-09-09, trên **toàn bộ** `catalog.parquet` + `data/processed/` |
> | Nằm ở mục nào | *Tổng quan*, *Đặc tính thống kê*, *Vấn đề chất lượng* | ***Sau tiền xử lý*** |
> | Dùng để | mô tả nguồn dữ liệu, giải thích vì sao cắt scope | **mọi bảng và hình của paper** |
>
> Chênh lệch không nhỏ và không đều: trung bình CPU% của E1 là **6,75 → 13,6352**,
> của E3 gần như không đổi. Nguyên nhân đã truy được — bộ lọc `gan_chet` bỏ 36,3%
> chuỗi E1 và 39,4% chuỗi E2 nhưng chỉ 0,4% chuỗi E3, và lọc gần như chỉ cắt ở đuôi
> dưới. **Đó là hiệu ứng chọn lọc, không phải đặc tính tự nhiên của Bitbrains.**

Cách đo quần thể thô: `research-log/2026-08-30-tham-dinh-du-lieu.md`.
Cách đo quần thể nghiên cứu: `research-log/2026-09-09-ra-soat-truoc-paper.md`.

---

## Tổng quan

| | E1 — Bitbrains fastStorage | E2 — Bitbrains Rnd | E3 — Alibaba v2018 |
|---|---|---|---|
| Nguồn | GWA-T-12, TU Delft | GWA-T-12, TU Delft | alibaba/clusterdata |
| Năm thu thập | 2013 | 2013 | 2018 |
| Đơn vị quan sát | VM | VM | Máy vật lý |
| Số đơn vị | 1.250 | 500 x 3 tháng | 4.023 |
| Khoảng thời gian | 2013-08-12 → 09-11 | 2013-06-30 → 09-29 | 8 ngày |
| Interval gốc | 300 s | 300 s | khoảng 10 s, không đều |
| Tổng số dòng | 11.221.800 | 12.496.728 | 246.934.820 |
| Dung lượng | khoảng 1,2 GB | khoảng 1,1 GB | 8,99 GB |
| Header | Có | Có | **Không** |
| Delimiter | `;\t` | `;\t` | `,` |
| Số cột | 11 | 11 | 9 |
| Giấy phép | Yêu cầu ghi nhận nguồn | Yêu cầu ghi nhận nguồn | Yêu cầu ghi nhận nguồn |

## Biến mục tiêu

| Môi trường | Cột | Thang |
|---|---|---|
| E1, E2 | `CPU usage [%]` | 0–100 |
| E3 | `cpu_util_percent` | 0–100 |

## Đặc tính thống kê của target — **quần thể THÔ**

> Mẫu ngẫu nhiên, trước cửa sổ và trước lọc. **Không dùng cho bảng của paper** — số
> tương ứng của quần thể nghiên cứu ở mục *Sau tiền xử lý*.

| Chỉ số | E1 | E2 | E3 |
|---|---|---|---|
| p10 | 0,00 | 0,00 | 20,0 |
| p25 | 0,00 | 0,30 | 28,0 |
| **p50** | **0,84** | **1,07** | **37,0** |
| p75 | 2,00 | 2,17 | 48,0 |
| p90 | 11,00 | 14,75 | 58,0 |
| Trung bình | 6,75 | 6,99 | 38,13 |
| Độ lệch chuẩn | 20,33 | 19,89 | 16,01 |
| Tỉ lệ mẫu dưới 1% | 53,4% | 43,2% | 2,0% |
| Tỉ lệ mẫu trên 20% | 7,6% | 8,0% | 89,0% |
| Autocorr t-1 trên lưới 5 phút | 0,675 | 0,644 | 0,781 |
| Autocorr t-12 trên lưới 5 phút | 0,350 | 0,304 | 0,549 |

**Đây là bảng quan trọng nhất của data card.** Phân phối E1/E2 và E3 gần như không
giao nhau. Toàn bộ thiết kế thí nghiệm B xuất phát từ quan sát này. Xem
`decisions.md` mục QĐ-005.

> **Đính chính 2026-09-09 (QĐ-011).** Câu gốc còn viết *"trong khi autocorr nằm cùng
> vùng"* — đã bỏ. Trên quần thể nghiên cứu, ACF lag 1 của E3 là **0,8634**, tách hẳn
> khỏi 0,6674 (E1) và 0,6431 (E2). Ba môi trường lệch nhau ở **cả** mức tải **lẫn**
> mức tự tương quan. QĐ-005 giữ nguyên hiệu lực; chỉ lý do được viết lại.

## Vấn đề chất lượng đã biết

| Vấn đề | E1 | E2 | E3 | Xử lý |
|---|---|---|---|---|
| CPU% vượt 100 | 1,91%, đỉnh 111,07 | 2,41%, đỉnh 107,47 | không | Clip về [0, 100] |
| Chuỗi gần chết, mean dưới 1% | 42,5% VM | 34,5% VM | 0,6% máy | Lọc bỏ |
| Chuỗi hằng | 1,0% | 0,0% | 0,5% | Lọc bỏ |
| Cột rỗng | không | không | `mem_gps`, `mkpi` rỗng 79% | Bỏ cột |
| Sentinel bất thường | không | không | `disk_io_percent` bằng -1 hoặc 101 | Mask thành NaN |
| Lấy mẫu không đều | không | không | 10 s đến 640 s | Resample 5 phút |
| Độ dài chuỗi lệch | 5 đến 20.255 dòng | 437 đến 14.095 dòng | tương đối đều | **Ngưỡng `min_valid_rows_h12 = 500`** (QĐ-008 thay cho "2.000 điểm") |
| Trùng định danh | không | **Tên file lặp giữa 3 tháng** | không | Khoá `(month, vm_id)` |
| Giá trị thiếu | 0,00% | 0,00% | có, do gap | **Nội suy tuyến tính cụm ≤ 2 điểm; KHÔNG ffill** (QĐ-008) |

> **Đính chính hai ô cột "Xử lý" — 2026-09-09 (QĐ-011 điểm 4).** Bản gốc ghi
> *"Forward-fill tối đa 3 bước"* và *"Ngưỡng 2.000 điểm"*. Cả hai đã bị **QĐ-008 bãi
> bỏ** ngày 2026-09-08 vì phá huỷ 74% dữ liệu E2 và 99% dữ liệu E3.
>
> Đây không phải số lệch mà là **mô tả sai phương pháp**, và sai đúng chỗ nguy hiểm:
> ffill tạo đoạn phẳng làm autocorrelation tăng giả tạo, mà autocorrelation là đại
> lượng trung tâm của RQ3. `tests/test_resample.py` có hẳn một test chống ffill.

Ba dòng tỉ lệ trong bảng trên (`gan_chet`, chuỗi hằng, và tỉ lệ dùng được) là **ước
lượng trên mẫu ngẫu nhiên dưới bộ lọc CŨ**. Số thật sau khi chạy bộ lọc hiện hành ở
mục kế tiếp — chênh tới 5 điểm phần trăm ở E2, và mã `hang` thực tế **chưa bao giờ
kích hoạt** vì `gan_chet` xét trước và bắt hết chuỗi hằng.

---

## Sau tiền xử lý — **quần thể NGHIÊN CỨU**

> Đây là bảng dùng cho **mọi bảng và hình của paper**. Đo 2026-09-09 trên toàn bộ
> `data/catalog.parquet` và `data/processed/`, không phải trên mẫu. Sinh lại được
> bằng `python -m cwp.preprocess.build --env all` rồi `python scripts/check_gd1.py`.
> Bảng máy sinh sẽ nằm ở `results/tables/` sau GĐ2 Bước 4.

### Bộ lọc chuỗi (protocol mục 6 bước 7)

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Chuỗi vào | 1.250 | 500 | 500 |
| Loại — `ngoai_cua_so` | 55 | 1 | 0 |
| Loại — `gan_chet` (mean < 1,0) | **454** | **197** | **2** |
| Loại — `hang` | 0 | 0 | 0 |
| Loại — `it_dong` | 6 | 0 | 0 |
| **Chuỗi giữ lại** | **735** | **302** | **498** |
| Tỉ lệ giữ | 58,8% | 60,4% | 99,6% |

Bộ lọc cắt 41% E1 và 40% E2 nhưng chỉ 0,4% E3, và cắt gần như hoàn toàn ở đuôi dưới.
Mọi so sánh giữa các môi trường phải đọc kèm dữ kiện này.

### Phân phối CPU% sau tiền xử lý

Gộp mọi điểm không NaN của các chuỗi được giữ, trong cửa sổ 8 ngày. Theo QĐ-011
điểm 2, **đây** là "phân phối target" mà bảng mô tả và hình phân phối của paper mô
tả — không phải cột `target` của ma trận đặc trưng.

> **Bảng máy sinh.** Chép từ `results/tables/describe_gd2.md`, sinh bằng
> `python scripts/describe_gd2.py --env all`. Sửa tay ở đây là tạo ra bản thứ hai
> không ai kiểm được — chạy lại lệnh rồi chép đè.

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| Số chuỗi | 735 | 302 | 498 |
| Điểm trong cửa sổ | 1.693.440 | 695.808 | 1.147.392 |
| Trung bình | 13,6352 | 9,2199 | 38,0123 |
| Độ lệch chuẩn | 27,9530 | 21,4265 | 14,9522 |
| Nhỏ nhất | 0,0000 | 0,0000 | 0,0000 |
| p10 | 0,7000 | 0,4583 | 20,9000 |
| p25 | 1,2000 | 1,0417 | 29,2500 |
| **p50** | **1,7833** | **1,7667** | **37,8333** |
| p75 | 5,3667 | 4,0667 | 47,3333 |
| p90 | 57,7000 | 23,5667 | 56,3000 |
| p95 | **100,0000** | 60,0667 | 61,2667 |
| Lớn nhất | 100,0000 | 100,0000 | 99,8000 |
| Tỉ lệ `NaN` % | 1,4272 | 0,3086 | **9,2936** |
| Điểm bằng đúng 100 % | **5,1238** | **2,2788** | 0,0000 |
| Tỉ lệ điểm được nội suy % | 0,0163 | 0,0924 | 0,1647 |

Bảng *Đặc tính thống kê của target* ở trên dùng cùng bộ phân vị p10–p90, nên so được
từng dòng một giữa hai quần thể. Chênh lớn nhất ở E1: trung vị 0,84 → **1,7833**,
trung bình 6,75 → **13,6352**.

Thống kê của cột `target` là chuyện khác và thuộc phần Thiết lập thí nghiệm:
trung bình ở h=1 là 13,6741 / 9,2667 / 38,3678 (`results/tables/reference_gd2.json`).

### Hiệu ứng trần do clip — bất đối xứng giữa các môi trường

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Mẫu thô bị clip về 100 | 319.082 | 95.137 | 0 |
| Tỉ lệ clip trên mẫu thô | 2,8434% | 2,1933% | 0,0000% |
| **Điểm bằng đúng 100 sau căn lưới** | **5,1238%** | **2,2788%** | **0,0000%** |

Phân vị 95 của E1 **chính là trần 100**. Đây là kiểm duyệt, và nó bất đối xứng giữa
đúng ba môi trường đang được đem so sánh. Xem QĐ-011 điểm 3; phải vào Limitations.

*(Bảng "Vấn đề chất lượng" phía trên ghi CPU% vượt 100 là 1,91% và 2,41% — ước lượng
trên mẫu ngẫu nhiên của dữ liệu thô. Số đo trên toàn bộ là 2,8434% và 2,1933%.)*

### Cấu trúc phụ thuộc thời gian

Đo bằng `scripts/reference_gd2.py`, bản hiện thực độc lập của A. Tương quan tại lag
`k` chỉ dùng các cặp `(t, t+k)` mà cả hai đều không NaN, **không** nén chuỗi.

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| ACF lag 1 | 0,6674 | 0,6431 | **0,8634** |
| ACF lag 12 (1 giờ) | 0,4459 | 0,2978 | 0,6287 |
| ACF lag 288 (24 giờ) | 0,1334 | 0,1271 | **0,5956** |
| Cặp bị bỏ ở lag 288 | 1,63% | 0,71% | **14,65%** |
| CV trung vị | 0,4974 | 0,5369 | 0,2859 |
| CV IQR | 0,8448 | 1,1543 | 0,0956 |

**Nhịp một giờ, ở cả ba môi trường.** ACF nhô lên tại **24/24 bội số của 12 bucket**
trong dải lag 12–288; mức trội trung vị so với hai lag láng giềng là +0,0618 (E1),
+0,0314 (E2), +0,0075 (E3). Đây là quan sát về **dữ liệu**, thuộc phần Dữ liệu của
paper, và là căn cứ đo được cho việc giữ `lag_12` và `lag_24` trong bộ đặc trưng ở
protocol mục 8. Xem QĐ-012 điểm 5.

Hai điều phải nói kèm mỗi khi trích bảng này:

1. **ACF lag 288 của E3 = 0,5956 đo trên tập đã bỏ 14,65% số cặp**, vì E3 thiếu
   9,294% điểm. Cách tính theo cặp là đúng và không co trục thời gian, nhưng tỉ lệ
   bỏ phải đi cùng con số.
2. E3 mượt hơn **một phần do hiệu ứng tổng hợp ở mức máy vật lý** — QĐ-004 đã chốt
   khuôn câu phải dùng trong bài.

## Giới hạn

1. **Lệch đơn vị quan sát.** E1 và E2 là VM đơn lẻ; E3 là máy vật lý gộp nhiều
   container. Chuỗi E3 mượt hơn một cách hệ thống — autocorr bậc 1 là **0,8634** so
   với 0,6674 và 0,6431 trên quần thể nghiên cứu (số cũ 0,781 / 0,675 / 0,644 đo
   trên mẫu thô; khoảng cách trên quần thể nghiên cứu **rộng hơn**, không hẹp hơn).
   **A đã chấp nhận giới hạn này** và thu hẹp phạm vi đề tài tương
   ứng; phương án bổ sung `container_usage` chỉ kích hoạt theo ba điều kiện ghi
   trong `decisions.md` mục QĐ-004.

   Khi viết bài, không phát biểu "Alibaba dễ dự đoán hơn Bitbrains" mà phải là
   "chuỗi ở mức máy vật lý dễ dự đoán hơn chuỗi ở mức VM, một phần do hiệu ứng
   tổng hợp".
2. **Lệch thời đại.** Bitbrains 2013, Alibaba 2018. Phần cứng, phần mềm và đặc tính
   workload đã thay đổi.
3. **Độ dài quan sát chênh nhau.** E3 chỉ 8 ngày, không phân tích được chu kỳ tuần.
4. **Chỉ CPU.** Không mở rộng sang memory, disk, network trong phạm vi nghiên cứu này.
5. **Bitbrains chỉ một nhà cung cấp.** E1 và E2 cùng tổ chức nên không hoàn toàn độc
   lập với nhau.

Bốn giới hạn dưới đây bổ sung ngày 2026-09-09 theo QĐ-011. Cả bốn đều **đo được**,
không phải rủi ro giả định.

6. **Hiệu ứng chọn lọc của bộ lọc `gan_chet`.** Ngưỡng mean < 1,0 loại 36,3% chuỗi
   E1 và 39,4% chuỗi E2 nhưng chỉ 0,4% chuỗi E3, và loại gần như hoàn toàn ở đuôi
   dưới. Hệ quả: trung bình CPU% của E1 tăng từ 6,75 lên 13,6352 chỉ do lọc. Quần
   thể nghiên cứu của E1/E2 vì thế **không đại diện cho toàn bộ VM Bitbrains** mà
   đại diện cho phần VM còn hoạt động. Mọi so sánh giữa các môi trường phải phát
   biểu trên quần thể đã lọc, không phát biểu trên "Bitbrains" nói chung.

7. **Kiểm duyệt tại trần 100 của E1 và E2.** 5,12% điểm của E1 và 2,28% điểm của E2
   nằm đúng tại 100 sau khi clip; E3 là 0%. Phân vị 95 của E1 chính là trần. Đuôi
   phải của E1/E2 bị nén vào một điểm còn E3 thì không, nên một phần của kết luận
   "E3 dễ dự đoán hơn" đến từ chỗ này. Mọi chỉ số ở vùng tải cao của E1/E2 đo trên
   dữ liệu đã bị chặn.

8. **E3 thiếu 9,29% điểm.** Gấp 6,5 lần E1 và 30 lần E2. Gần như toàn bộ lỗ hổng của
   E3 dài hơn 2 bucket nên không được nội suy. ACF của E3 vì thế bỏ 9,76% số cặp ở
   lag 1 và **14,65% ở lag 288** — con số 0,5956 phải luôn đi kèm tỉ lệ này.

9. **CV bị chặn cứng bởi thang đo, và chặn siết khác nhau ở mỗi môi trường.** CPU%
   nằm trong [0, 100] nên một chuỗi có trung bình `m` không thể có `CV` vượt
   `√((100−m)/m)`. Đo trên 1.535 chuỗi: **0 chuỗi vi phạm**. Chặn siết rất chặt ở
   vùng tải cao — E3 chạy quanh 40% nên CV của nó không thể vượt 1,22, trong khi E1
   và E2 chạy quanh 2,7% nên chặn của chúng tới 6,0. Hệ quả: so CV **thô** giữa các
   môi trường là so hai đại lượng bị chặn khác nhau. Theo tỉ lệ chạm chặn thì E3
   dùng **0,233** lần chặn còn E1 chỉ **0,094** — tức E3 dùng gấp hơn hai lần khoảng
   biến động mà mức tải của nó cho phép. Câu "E3 ít bursty hơn" chỉ đúng với CV thô.
   Đây là cơ chế **khác** với trần 100 ở mục 7: trần kiểm duyệt các *điểm*, chặn này
   giới hạn *thống kê phân tán*. Xem QĐ-012 điểm 3.

10. **Đặc trưng lịch tính theo UTC.** `b0` của E2 rơi đúng 00:00 giờ Amsterdam mùa hè
   (UTC+2), nên "một ngày" trong dữ liệu E1/E2 bắt đầu ở giờ UTC 22. Mọi phát biểu
   về giờ trong bài phải ghi rõ là **giờ UTC**, không phải giờ vận hành. Với E3 thì
   mốc thời gian là tương đối và `dow` không diễn giải được — xem QĐ-010.

## Cách trích dẫn

**Bitbrains (E1, E2).** Bắt buộc ghi nhận nguồn theo yêu cầu của Bitbrains IT
Services Inc. và Grid Workloads Archive.

> Siqi Shen, Vincent van Beek, Alexandru Iosup. *Statistical Characterization of
> Business-Critical Workloads Hosted in Cloud Datacenters.* CCGrid 2015, Shenzhen, China.

**Alibaba (E3).**

> Jing Guo, Zihao Chang, Sa Wang, Haiyang Ding, Yihui Feng, Liang Mao, Yungang Bao.
> *Who Limits the Resource Efficiency of My Datacenter: An Analysis of Alibaba
> Datacenter Traces.* IWQoS 2019, Phoenix, USA.

**Trạng thái:** A đã đối chiếu toàn bộ nguồn và hai mục trích dẫn trên trang gốc,
xác nhận đúng — 2026-08-30. Không cần kiểm tra lại.

## Đường dẫn

```
data/raw/Bitbrains-fastStorage/08-2013/*.csv      1.250 tệp
data/raw/Bitbrains-Rnd/{2013-7,2013-8,2013-9}/    500 tệp mỗi tháng
data/raw/Alibaba-Cluster-Trace/machine_usage.csv  một tệp 8,99 GB
```

Mỗi thư mục có `about.md` mô tả nguồn và `explain.md` ghi chú tiền xử lý.
