# 2026-09-14 — Nghiệm thu GĐ4, và hình bổ sung dạng quen thuộc

**Người thực hiện:** một phiên đóng cả hai vai, theo yêu cầu của A.
**Giai đoạn:** GĐ4 → GĐ5
**Thời lượng:** ~2 giờ

## Mục tiêu phiên

1. Bước 7: điền `gate-gd4.md` mục 5 bằng số đo, không theo trí nhớ.
2. A thấy các hình ECDF và heatmap tỉ số log2 khó viết thành bài, đề nghị thêm dạng quen
   thuộc: histogram, heatmap, boxplot, phân cụm.

## Đã làm

- Chạy `check_gd4.py` (**ĐẠT**, tiến độ 7/7), `pytest tests/` (**359 passed, 1 skipped**),
  đếm `so_lan_cham_test` của 17 thư mục `runs/`
- Điền `gate-gd4.md` mục 5 và năm mục con 5.1–5.5
- `scripts/fig_bo_sung.py` — 13 hình, một PDF có trang hướng dẫn đọc; bảng phụ
  `results/tables/bo_sung_cum.csv`
- Thêm mục `bo_sung/` vào `results/figures/README.md`

## Số liệu thu được

### Kết quả cổng GĐ4

| Mục | Kết quả |
|---|---|
| 3.1 Sản phẩm | ĐẠT |
| 3.2 Bước chuẩn hoá | ĐẠT, kèm hạn chế máy đứng yên ở N1 |
| 3.3 Rò rỉ T1–T4 | ĐẠT — test chạm **816 lần trên 540 tổ hợp**, giải thích từng phần |
| 3.4 Điều kiện qua cổng | **3/4**. Gạch đầu "N0 thất bại nặng ở bốn cặp" **không đạt** (2/4) và **không sửa câu chữ**; ghi sai tiền đề, kèm bằng chứng thay thế |

**Kết luận: ĐẠT, có ghi chú. Không chặn GĐ5.**

Số N0 cạnh mốc hằng số (5.1): Bitbrains→Alibaba **bằng naive** (4,30 và 4,39 so với
4,30); Alibaba→Bitbrains **2,8–3,0 lần naive**. Không cặp nào gần mốc hằng số 28–36.

### Hình bổ sung

Mọi hình đều mở ra xem sau khi vẽ. Ba lỗi bố cục tìm được và đã sửa:

| Lỗi | Sửa |
|---|---|
| Boxplot GĐ3 cố định trục 0,5–3 → hộp `lr`, `ridge` của E1 bị cắt | trục tự nới theo râu p95 lớn nhất |
| Nhãn "E1" và "E2" đè nhau trên PCA | một nhãn chung "E1 + E2" — trung vị gần trùng |
| Bảng k-means gắn "đa số E1" cho **hai** cụm khác nhau | tên trơn "cụm 1/2/3" |

Màu đã chạy validator: 3 slot phân loại qua kiểm **mọi cặp** (CVD ΔE 9,2), dải xanh 3 bậc
qua `--ordinal`.

### Phân cụm — MÔ TẢ, không khai trước, không phải kiểm định

k-means k = 3 trên 4 đặc trưng tính ở cửa sổ train: log mức tải, log CV, ACF lag 1,
ACF lag 288.

| | cụm 1 | cụm 2 | cụm 3 |
|---|---:|---:|---:|
| E1 | 381 | 91 | 263 |
| E2 | 162 | 38 | 102 |
| E3 | 9 | **481** | 8 |
| E1g (chiếu, không học lại) | 4 | 12 | **57** |

E3 gần như nằm trọn một cụm; E1 và E2 chia nhau hai cụm còn lại với tỉ lệ gần giống
nhau. **57/73 máy giả nằm ở cụm của Bitbrains**, chỉ 12 ở cụm E3.

Trung vị bốn đặc trưng trên cửa sổ train:

| | mức tải % | CV | ACF lag 1 | ACF lag 288 |
|---|---:|---:|---:|---:|
| E1 | 2,6 | 0,50 | 0,61 | 0,11 |
| E2 | 2,3 | 0,50 | 0,62 | 0,08 |
| **E1g** | **11,7** | **0,67** | **0,91** | **0,03** |
| E3 | 40,1 | 0,28 | 0,85 | 0,46 |

Gộp 5 VM làm chuỗi **mượt hơn cả E3** ở lag 1, nhưng không giống máy Alibaba ở ba đặc
trưng kia: mức tải vẫn thấp, CV còn cao hơn VM đơn lẻ, và **chu kỳ ngày không xuất hiện**
(ACF lag 288 = 0,03 so với 0,46). Tức "máy vật lý Alibaba" khác "VM gộp" không chỉ ở độ
mượt. Khớp với D2 "không kết luận", nhưng chỉ là mô tả, không dùng làm bằng chứng.

## Phát hiện

Không có phát hiện mới về phương pháp. Ghi chú quy trình duy nhất: hai lần chạy thử
đường ống (27 + 30 lần chạm test) đã xoá thư mục `runs/`. Số lần chạm của chúng phải
cộng tay từ log; `gate-gd4.md` mục 5.3 đã ghi.

## Quyết định

Không phát sinh.

## Việc tiếp theo — GĐ5

- [ ] A chọn hình vào paper, từ `gd2/`, `gd3/`, `gd4/` và `bo_sung/`
- [ ] Sinh lại hình GĐ3 gốc bằng bảng màu đã qua validator — hoặc thay hẳn bằng B05–B08
- [ ] Phiên độc lập viết lại B3, B11, B12
- [ ] Viết bản thảo theo khuôn phát biểu của QĐ-004, QĐ-016 điểm 1, QĐ-017 điểm 1, QĐ-018
  điểm 4

## File sinh ra

- `research-log/gate-gd4.md` — mục 5 đầy đủ
- `scripts/fig_bo_sung.py`
- `results/figures/bo_sung/` — 13 `.png` + `bo-sung_hinh-quen-thuoc.pdf`
- `results/tables/bo_sung_cum.csv`
- `results/figures/README.md` — mục `bo_sung/`
