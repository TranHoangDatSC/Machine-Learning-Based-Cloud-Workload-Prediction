# Dữ liệu thô (chỉ đọc)

Ba public cloud trace dùng cho đồ án. Mỗi thư mục có:
- `about.md` — mô tả gốc từ nguồn phát hành (paste nguyên văn, để trích dẫn)
- `explain.md` — ghi chú dùng trong đồ án: vai trò, target, cảnh báo tiền xử lý

## Tổng quan

| | E1 — Bitbrains fastStorage | E2 — Bitbrains Rnd | E3 — Alibaba v2018 |
|---|---|---|---|
| Nguồn | GWA-T-12 (TU Delft) | GWA-T-12 (TU Delft) | alibaba/clusterdata |
| Năm | 2013 | 2013 | 2018 |
| Đơn vị quan sát | VM | VM | Máy vật lý |
| Số đơn vị | 1.250 | 500 × 3 tháng | 4.023 |
| Khoảng thời gian | ~30 ngày | ~90 ngày | 8 ngày |
| Interval gốc | 300 s | 300 s | ~10 s (không đều) |
| Tổng số dòng | 11.221.800 | 12.496.728 | **246.934.820** |
| Dung lượng | ~1,2 GB | ~1,1 GB | 8,99 GB |
| Header | Có | Có | **Không** |
| Delimiter | `;\t` | `;\t` | `,` |

## Target chung

| Environment | Cột target | Thang |
|---|---|---|
| E1, E2 | `CPU usage [%]` | 0–100 |
| E3 | `cpu_util_percent` | 0–100 |

Cả ba cùng đơn vị, cùng thang đo → so sánh và transfer giữa các environment là
hợp lệ. Đây là điều kiện tiên quyết của RQ3.

**Không** dùng `CPU usage [MHZ]` làm target: nó phụ thuộc số core và tốc độ core
của từng VM nên không so sánh được giữa các môi trường.

## Chuẩn hoá bắt buộc trước khi train

1. **Resample toàn bộ về lưới 5 phút.** E1/E2 đã sẵn 300 s; E3 phải hạ tần từ ~10 s.
   Không được train ở granularity khác nhau rồi so kết quả.
2. **Lọc chuỗi quá ngắn.** Đề xuất ngưỡng ≥ 2.000 mẫu sau resample. Ghi rõ ngưỡng
   và số đơn vị bị loại trong paper.
3. **Chia train/test theo thời gian**, không shuffle. Dùng rolling-origin /
   `TimeSeriesSplit`.
4. **Metric:** MAE, RMSE, R², và **SMAPE hoặc MASE** thay cho MAPE — nhiều chuỗi
   (nhất là Rnd) có giá trị gần 0 làm MAPE nổ vô cực.

## Ba mức độ "khác môi trường" cho RQ3

| Cặp transfer | Khác gì |
|---|---|
| E1 → E2 | Cùng tổ chức, cùng thời điểm, **khác hạ tầng lưu trữ** |
| E2 → E1 | (chiều ngược lại) |
| E1/E2 → E3 | **Khác tổ chức, khác quy mô, khác thời đại** |

Có hai mức độ khác biệt này thì RQ3 mới kết luận được *nguyên nhân* suy giảm,
thay vì chỉ báo cáo một con số.

## Ghi chú lịch sử

Bản đầu của repo dùng `data/raw/Google-2019-Cluster/borg_traces_data.csv` và
`Alibaba .../pai_group_tag_table.csv`. Cả hai đã bị loại:

- **borg_traces_data.csv** là dataset *job failure prediction* (405.894 dòng
  event-level, có nhãn nhị phân `failed`, `time` không sắp xếp và chứa sentinel
  `9223372036854775807`). Không dựng được chuỗi thời gian. Muốn có time series
  Google 2019 thật thì phải lấy bảng `instance_usage` trên BigQuery (~2,4 TiB).
- **pai_group_tag_table.csv** chỉ có 5 cột (`inst_id, user, gpu_type_spec, group,
  workload`), không timestamp, không resource usage. Là bảng metadata của GPU
  trace v2020, không phải utilisation.
