# Hồ sơ cổng GĐ1

**Người giữ cổng:** A
**Trạng thái:** mở, chờ B nộp
**Cập nhật:** 2026-09-08 (sau khi QĐ-008 có hiệu lực)

Tài liệu này định nghĩa A kiểm gì khi B báo xong GĐ1, và cung cấp **thước đo tham
chiếu** để đối chiếu.

---

## 1. Thước đo là gì

`research-plan.md` bản đầu ghi điều kiện qua cổng là *"A đối chiếu bảng của B với
`research-log/2026-08-30-tham-dinh-du-lieu.md`"*. **Điều kiện đó đã bị thay.**

Số liệu ngày 30-08 đo trên mẫu ngẫu nhiên 150–250 VM, chưa lọc, chưa cắt cửa sổ 8
ngày. B nộp số trên toàn bộ dữ liệu đã áp đủ quy tắc. Hai bên đo hai thứ khác nhau
nên không so trực tiếp được — đúng loại lỗi mà `tu-bai-cu-den-bai-nay.md` mục 3
phân tích.

Thước đo hiện tại: **`scripts/reference_gd1.py`**, bản hiện thực độc lập của
protocol mục 5–8 do A viết. Hai bản hiện thực độc lập ra cùng con số là bằng chứng
mạnh; lệch nhau là dấu hiệu có lỗi ở một trong hai bên.

---

## 2. Số liệu tham chiếu

Chạy trên **toàn bộ** dữ liệu, K = 2, môi trường ghim theo QĐ-007.
Nguồn: `results/tables/reference_E1.json`, `reference_E2.json`, `reference_E3.json`.

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| Chuỗi vào | 1.250 | 500 | 500 |
| Loại — `ngoai_cua_so` | 55 | 1 | 0 |
| Loại — `gan_chet` | 454 | 197 | 1 |
| Loại — `hang` | 0 | 0 | 0 |
| Loại — `it_dong` | 6 | 0 | 0 |
| **Chuỗi còn lại** | **735** | **302** | **499** |
| Tỉ lệ giữ | 58,80% | 60,40% | 99,80% |
| Dòng hợp lệ h=1 | 1.650.896 | 678.486 | 941.439 |
| Dòng hợp lệ h=6 | 1.647.221 | 675.665 | 929.331 |
| Dòng hợp lệ h=12 | 1.642.811 | 673.322 | 919.907 |
| Điểm được nội suy | 272 | 641 | 1.910 |
| Tỉ lệ nội suy | 0,016% | 0,092% | 0,183% |
| Mẫu clip trên 100 | 319.082 | 95.137 | 0 |
| Tỉ lệ clip | 2,8434% | 2,1933% | 0% |
| Target mean | 13,6352 | 9,2199 | 38,0464 |
| Target p50 | 1,7833 | 1,7667 | 37,8276 |
| Target std | 27,9530 | 21,4265 | 15,0669 |

Sinh lại bất cứ lúc nào:

```bash
python scripts/reference_gd1.py --env all --out results/tables/reference_gd1.json
```

---

## 3. Danh sách A kiểm khi B nộp

Chạy theo thứ tự. Trượt mục nào thì dừng, không kiểm tiếp.

### 3.1 Sản phẩm có đủ không

- [ ] `src/cwp/io/bitbrains.py`, `src/cwp/io/alibaba.py`
- [ ] `src/cwp/preprocess/clean.py`, `resample.py`, `filter.py`
- [ ] `data/processed/` có dữ liệu, định dạng parquet
- [ ] `data/catalog.parquet` — một dòng mỗi chuỗi
- [ ] `tests/test_io.py`, `tests/test_resample.py` chạy xanh
- [ ] Log trong `research-log/` có bảng lọc đầy đủ

Thiếu `catalog.parquet` hoặc thiếu bảng lọc thì trả lại ngay.

### 3.2 Bảng lọc phải có đủ cột

| Cột | Vì sao bắt buộc |
|---|---|
| Chuỗi vào | Mốc gốc |
| Bị loại theo **từng** lý do, bốn cột tách riêng | Gộp lại thì không truy được nguyên nhân |
| Chuỗi còn lại | |
| Dòng hợp lệ ở mỗi horizon | Con số thực sự dùng để train |
| **Tỉ lệ điểm được nội suy** | Can thiệp vào dữ liệu, phải khai báo |
| Tỉ lệ mẫu bị clip | Kiểm chứng bước làm sạch có chạy |

### 3.3 Đối chiếu số

- [ ] Chuỗi vào khớp **tuyệt đối**: E1 = 1.250, E2 = 500, E3 = 500
- [ ] Chuỗi còn lại lệch ≤ **2%** so với tham chiếu
- [ ] Số bị loại theo từng lý do lệch ≤ **5%**
- [ ] Dòng hợp lệ h=12 lệch ≤ **5%**
- [ ] Tỉ lệ nội suy lệch ≤ **5%**
- [ ] Tỉ lệ clip lệch ≤ **1%**
- [ ] Target mean và p50 lệch ≤ **2%**

Chuỗi vào mà lệch thì không phải sai số — là đọc sót tệp hoặc lấy nhầm mẫu.

### 3.4 Bốn cái bẫy đã báo trước

- [ ] **Rnd trùng tên tệp.** Mở `catalog.parquet`, kiểm định danh chuỗi E2 có phân
      biệt được tháng không. Nếu định danh chỉ là `1`, `2`, `3` thì sai.
- [ ] **Parser Bitbrains.** Kiểm tên cột không lẫn ký tự tab. Dấu hiệu sai:
      `'CPU usage [%]\t'` hoặc `'\tCPU cores'`.
- [ ] **Alibaba không header.** Tổng số dòng đọc được phải là **246.934.820**.
      Thiếu đúng 1 dòng nghĩa là dòng đầu bị nuốt làm tên cột.
- [ ] **Cửa sổ toàn cục, không phải per-series.** E1 phải có đúng 55 chuỗi bị loại
      vì `ngoai_cua_so`. Nếu con số đó bằng 0 thì B đã dùng cửa sổ per-series.

### 3.5 Kiểm rò rỉ

- [ ] `data/processed/` không chứa cột nào tính từ tương lai
- [ ] Nếu B đã sinh đặc trưng rolling: kiểm có `.shift(1)` không
- [ ] Nội suy **chỉ áp cho cụm ≤ 2 điểm**, không phải toàn bộ chuỗi

---

## 4. Lệnh A chạy khi nghiệm thu

```bash
# 1. Sinh lại tham chiếu
python scripts/reference_gd1.py --env all --out results/tables/reference_gd1.json

# 2. Chạy test của B
pytest tests/ -v

# 3. Bảng tổng hợp của B
python -c "import pandas as pd; d=pd.read_parquet('data/catalog.parquet'); print(d.groupby('env').agg(n=('series_id','count'), rows=('valid_rows_h12','sum'), mean=('mean','median')))"

# 4. Bẫy Rnd trùng tên
python -c "import pandas as pd; d=pd.read_parquet('data/catalog.parquet'); e2=d[d.env=='E2']; print('E2 dinh danh duy nhat:', e2.series_id.nunique(), '/', len(e2))"
```

---

## 5. Kết quả cổng

Điền khi nghiệm thu.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 3.1 Sản phẩm | | |
| 3.2 Bảng lọc | | |
| 3.3 Đối chiếu số | | |
| 3.4 Bốn cái bẫy | | |
| 3.5 Rò rỉ | | |

**Kết luận:**
**Ngày duyệt:**

---

## Phụ lục — khuyết tật đã sửa trước khi B triển khai

Giữ lại để truy vết. Khi dựng bản tham chiếu, A phát hiện quy tắc cũ ở protocol mục
6 bước 6 (*"ffill 3 bước rồi cắt chuỗi tại lỗ hổng"*) phá huỷ dữ liệu:

| Môi trường | Dòng h=12 giữ được theo quy tắc cũ |
|---|---|
| E1 | 100% |
| E2 | 26% |
| E3 | 1% |

Nguy hiểm nhất là bảng tổng kết không lộ ra: E3 báo giữ 99,6% số chuỗi trong khi độ
dài trung vị chỉ còn 26 trên tối đa 2.304. Nếu chỉ nhìn cột "tỉ lệ giữ" thì cổng
được cho qua và GĐ3, GĐ4 chạy trên dữ liệu hỏng.

Đã thay bằng chính sách ở QĐ-008. Đó cũng là lý do mục 3.2 bắt buộc bảng của B phải
có cột "dòng hợp lệ", không chỉ "số chuỗi còn lại".
