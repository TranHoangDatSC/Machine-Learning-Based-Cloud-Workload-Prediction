# Hồ sơ cổng GĐ1

**Người giữ cổng:** A
**Trạng thái:** đang mở, chờ B nộp
**Lập ngày:** 2026-09-07

Tài liệu này định nghĩa A sẽ kiểm gì khi B báo xong GĐ1, và cung cấp **thước đo tham
chiếu** để đối chiếu.

---

## 1. Vì sao cần tài liệu này

`research-plan.md` ghi điều kiện qua cổng GĐ1 là *"A đối chiếu bảng thống kê của B
với số liệu trong `research-log/2026-08-30-tham-dinh-du-lieu.md`"*.

**Điều kiện đó không dùng được.** Số liệu ngày 30-08 đo trên mẫu ngẫu nhiên 150–250
VM, **chưa lọc, chưa cắt cửa sổ 8 ngày**. Còn B sẽ nộp số liệu trên **toàn bộ dữ
liệu, đã áp đủ quy tắc protocol mục 5–7**. Hai bên đo hai thứ khác nhau nên không so
trực tiếp được — đúng loại lỗi mà `tu-bai-cu-den-bai-nay.md` mục 3 mô tả.

Thước đo thay thế: `scripts/reference_gd1.py`, một **bản hiện thực độc lập** của
protocol mục 5–7 do A viết. Hai bản hiện thực độc lập ra cùng con số là bằng chứng
mạnh; lệch nhau là dấu hiệu có lỗi ở một trong hai bên.

---

## 2. Phát hiện chặn: protocol mục 6 bước 6 phá huỷ dữ liệu

Khi chạy bản tham chiếu, A phát hiện quy tắc *"còn thiếu thì cắt chuỗi tại đó"*
huỷ phần lớn dữ liệu của E2 và gần như toàn bộ E3.

### Cơ chế

Protocol mục 6 xếp **lọc chuỗi ở bước 5**, **điền khuyết ở bước 6**. Nên bộ lọc độ
dài chạy *trước* khi cắt chuỗi, và không thể bắt được chuỗi bị cắt cụt sau đó.

```text
buoc 5: loc do dai  -> chuoi dai 2304, DAT
buoc 6: ffill(3) roi cat tai lo hong dau tien > 3 -> con 484 diem
                                                     ^ khong ai kiem lai
```

### Mức thiệt hại đo được

| Môi trường | Tỉ lệ NaN | Luật hiện tại giữ được | Phương án sửa giữ được |
|---|---|---|---|
| E1 fastStorage | 0,00% | 100% | 98,4% |
| E2 Rnd 2013-8 | 0,43% | **20,9%** | **94,5%** |
| E3 Alibaba | 12,11% | **1,1%** | **34,9%** |

E2 chỉ có 0,43% NaN nhưng mất 79% dữ liệu, vì các lỗ hổng đi thành cụm 8–12 điểm
liên tiếp (37/40 chuỗi mẫu có ít nhất một cụm), xuất hiện lần đầu quanh vị trí 480.

### Vì sao nguy hiểm hơn là chỉ mất dữ liệu

Bảng tổng kết **không lộ ra vấn đề**. Với luật hiện tại, E3 báo:

```text
chuoi_vao      : 500
chuoi_con_lai  : 498
ti_le_giu      : 99,6%      <- trong rat dep
do_dai_trung_vi: 26         <- tren toi da 2304
```

Nếu A chỉ nhìn cột "tỉ lệ giữ", cổng sẽ được cho qua và toàn bộ GĐ3, GĐ4 chạy trên
dữ liệu đã hỏng. Đây là lý do bảng nộp của B **bắt buộc phải có cột độ dài trung vị**.

### Đề xuất xử lý

Xem `decisions.md` QĐ-008 (đang chờ A duyệt). Tóm tắt: bỏ quy tắc cắt chuỗi, giữ
nguyên chuỗi có lỗ hổng, và loại **từng dòng huấn luyện** nào có cửa sổ đặc trưng
hoặc target chạm NaN.

---

## 3. Số liệu tham chiếu

Sinh bởi `scripts/reference_gd1.py`, lưu ở `results/tables/reference_E*.json`.

> **Cảnh báo:** bảng dưới đây tính theo **luật hiện tại của protocol**, tức là đã bao
> gồm khuyết tật ở mục 2. Dùng nó để *chứng minh khuyết tật*, **không** dùng làm
> thước đo nghiệm thu. Sau khi QĐ-008 được duyệt phải sinh lại.

| Chỉ số | E1 | E2 | E3 |
|---|---|---|---|
| Chuỗi vào | 1.250 | 500 | 500 |
| Loại vì độ dài | 32 | 0 | 1 |
| Loại vì NaN > 20% | 0 | 0 | 0 |
| Loại vì gần chết | 473 | 198 | 1 |
| Loại vì hằng | 0 | 0 | 0 |
| **Chuỗi còn lại** | **745** | **302** | **498** |
| Tỉ lệ giữ | 59,6% | 60,4% | 99,6% |
| **Độ dài trung vị** | **2.304** | **484** | **26** |
| Tổng điểm dữ liệu | 1.714.454 | 202.420 | 17.106 |
| Mẫu bị clip trên 100 | 319.082 (2,84%) | 95.137 (2,19%) | 0 |
| Target mean | 13,88 | 8,59 | 30,15 |
| Target p50 | 1,78 | 1,73 | 29,78 |
| Target std | 28,28 | 20,91 | 12,48 |

Ba dòng in đậm là chỗ lộ khuyết tật: E1 giữ đủ 2.304 điểm, E2 còn 484, E3 còn 26.

---

## 4. Điểm mơ hồ trong protocol cần chốt

Ngoài QĐ-008, khi hiện thực A gặp hai chỗ protocol chưa nói rõ. B sẽ gặp y hệt và có
thể chọn khác A, dẫn đến lệch số mà không ai biết vì sao.

**Một — cửa sổ 8 ngày tính từ đâu?** Mục 7 ghi *"8 ngày đầu"* nhưng không nói tính
từ thời điểm sớm nhất của toàn môi trường, hay từ điểm đầu tiên của từng chuỗi. A
tạm dùng **từ điểm đầu của từng chuỗi**. Cần chốt.

**Hai — ngưỡng 2.000 điểm giờ mang nghĩa khác.** Đặt ra khi chuỗi dài ~8.635 điểm
(30 ngày). Sau khi cắt còn 8 ngày, tối đa chỉ còn 2.304 điểm, nên ngưỡng 2.000 thực
chất là **yêu cầu độ phủ 86,8%**, không còn là yêu cầu độ dài. Nếu QĐ-008 được duyệt
thì ngưỡng này phải diễn giải lại theo số dòng huấn luyện hợp lệ.

---

## 5. Danh sách A kiểm khi B nộp

Chạy theo thứ tự. Trượt bất kỳ mục nào thì dừng, không kiểm tiếp.

### 5.1 Sản phẩm có đủ không

- [ ] `src/cwp/io/bitbrains.py`, `src/cwp/io/alibaba.py`
- [ ] `src/cwp/preprocess/clean.py`, `resample.py`, `filter.py`
- [ ] `data/processed/` có dữ liệu, định dạng parquet
- [ ] `data/catalog.parquet` — một dòng mỗi chuỗi
- [ ] `tests/test_io.py`, `tests/test_resample.py`, chạy xanh
- [ ] Log trong `research-log/` có bảng lọc đầy đủ

Thiếu `catalog.parquet` hoặc thiếu bảng lọc thì trả lại ngay, chưa kiểm tiếp.

### 5.2 Bảng lọc phải có đủ cột

Bảng của B bắt buộc có, cho từng môi trường:

| Cột | Vì sao bắt buộc |
|---|---|
| Chuỗi vào | Mốc gốc |
| Loại theo từng điều kiện, tách riêng bốn cột | Gộp lại thì không truy được nguyên nhân |
| Chuỗi còn lại | |
| **Độ dài trung vị sau xử lý** | **Cột duy nhất lộ được khuyết tật ở mục 2** |
| Tổng số dòng huấn luyện hợp lệ | Con số thực sự dùng để train |
| Tỉ lệ mẫu bị clip | Kiểm chứng bước làm sạch có chạy |

### 5.3 Đối chiếu số

- [ ] Chuỗi vào khớp **tuyệt đối**: E1 = 1.250, E2 = 500, E3 = 500
- [ ] Số chuỗi còn lại lệch không quá **5%** so với bản tham chiếu
- [ ] Độ dài trung vị lệch không quá **5%**
- [ ] Tỉ lệ clip lệch không quá **5%**
- [ ] Target mean và p50 lệch không quá **5%**

Chuỗi vào mà lệch thì không phải sai số — là đọc sót tệp hoặc lấy nhầm mẫu.

### 5.4 Ba cái bẫy đã báo trước

- [ ] **Rnd trùng tên tệp.** Mở `catalog.parquet`, kiểm định danh chuỗi E2 có phân
      biệt được tháng không. Nếu định danh chỉ là `1`, `2`, `3` thì sai.
- [ ] **Parser Bitbrains.** Kiểm tên cột không lẫn ký tự tab. Dấu hiệu sai:
      `'CPU usage [%]\t'` hoặc `'\tCPU cores'`.
- [ ] **Alibaba không header.** Kiểm tổng số dòng đọc được phải là **246.934.820**.
      Thiếu đúng 1 dòng nghĩa là dòng đầu bị nuốt làm tên cột.

### 5.5 Kiểm rò rỉ

- [ ] `data/processed/` không chứa cột nào tính từ tương lai
- [ ] Nếu B đã sinh đặc trưng rolling: kiểm có `.shift(1)` không

---

## 6. Lệnh A chạy khi nghiệm thu

```bash
# 1. Sinh lại tham chiếu (sau khi QĐ-008 được duyệt)
python scripts/reference_gd1.py --env all --out results/tables/reference_gd1.json

# 2. Chạy test của B
pytest tests/ -v

# 3. Xem bảng của B
python -c "import pandas as pd; d=pd.read_parquet('data/catalog.parquet'); \
print(d.groupby('env').agg(n=('series_id','count'), \
len_med=('length','median'), mean=('mean','median')))"

# 4. Kiểm bẫy Rnd trùng tên
python -c "import pandas as pd; d=pd.read_parquet('data/catalog.parquet'); \
e2=d[d.env=='E2']; print('E2 dinh danh duy nhat:', e2.series_id.nunique(), '/', len(e2))"
```

---

## 7. Kết quả cổng

Điền khi nghiệm thu.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 5.1 Sản phẩm | | |
| 5.2 Bảng lọc | | |
| 5.3 Đối chiếu số | | |
| 5.4 Ba cái bẫy | | |
| 5.5 Rò rỉ | | |

**Kết luận:**
**Ngày duyệt:**
