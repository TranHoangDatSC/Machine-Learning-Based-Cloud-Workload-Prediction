# Data card

Mọi số liệu dưới đây **đo trực tiếp trên dữ liệu**, không lấy từ tài liệu mô tả.
Đo ngày 2026-08-30. Chi tiết cách đo trong `research-log/2026-08-30-tham-dinh-du-lieu.md`.

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

## Đặc tính thống kê của target

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
giao nhau, trong khi autocorr nằm cùng vùng. Toàn bộ thiết kế thí nghiệm B xuất phát
từ quan sát này. Xem `decisions.md` mục QĐ-005.

## Vấn đề chất lượng đã biết

| Vấn đề | E1 | E2 | E3 | Xử lý |
|---|---|---|---|---|
| CPU% vượt 100 | 1,91%, đỉnh 111,07 | 2,41%, đỉnh 107,47 | không | Clip về [0, 100] |
| Chuỗi gần chết, mean dưới 1% | 42,5% VM | 34,5% VM | 0,6% máy | Lọc bỏ |
| Chuỗi hằng | 1,0% | 0,0% | 0,5% | Lọc bỏ |
| Cột rỗng | không | không | `mem_gps`, `mkpi` rỗng 79% | Bỏ cột |
| Sentinel bất thường | không | không | `disk_io_percent` bằng -1 hoặc 101 | Mask thành NaN |
| Lấy mẫu không đều | không | không | 10 s đến 640 s | Resample 5 phút |
| Độ dài chuỗi lệch | 5 đến 20.255 dòng | 437 đến 14.095 dòng | tương đối đều | Ngưỡng 2.000 điểm |
| Trùng định danh | không | **Tên file lặp giữa 3 tháng** | không | Khoá `(month, vm_id)` |
| Giá trị thiếu | 0,00% | 0,00% | có, do gap | Forward-fill tối đa 3 bước |

Tỉ lệ đơn vị dùng được sau lọc: E1 khoảng 56,5%, E2 khoảng 65,5%, E3 khoảng 99,4%.

## Giới hạn

1. **Lệch đơn vị quan sát.** E1 và E2 là VM đơn lẻ; E3 là máy vật lý gộp nhiều
   container. Chuỗi E3 mượt hơn một cách hệ thống — autocorr bậc 1 là 0,781 so với
   0,675 và 0,644. **A đã chấp nhận giới hạn này** và thu hẹp phạm vi đề tài tương
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
