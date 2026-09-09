# Hồ sơ cổng GĐ1

**Người giữ cổng:** A
**Trạng thái:** **ĐÓNG — ĐẠT ngày 2026-09-09.** Toàn bộ danh sách mục 3 đã thoả.
**Cập nhật:** 2026-09-09 (điền mục 5; hai việc treo ở 5.3 đã bù xong)

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
| Loại — `gan_chet` | 454 | 197 | 2 |
| Loại — `hang` | 0 | 0 | 0 |
| Loại — `it_dong` | 6 | 0 | 0 |
| **Chuỗi còn lại** | **735** | **302** | **498** |
| Tỉ lệ giữ | 58,80% | 60,40% | 99,60% |
| Dòng hợp lệ h=1 | 1.650.896 | 678.486 | 938.933 |
| Dòng hợp lệ h=6 | 1.647.221 | 675.665 | 926.892 |
| Dòng hợp lệ h=12 | 1.642.811 | 673.322 | 917.463 |
| Điểm được nội suy | 272 | 641 | 1.738 |
| Tỉ lệ nội suy | 0,016% | 0,092% | 0,167% |
| Mẫu clip trên 100 | 319.082 | 95.137 | 0 |
| Tỉ lệ clip | 2,8434% | 2,1933% | 0% |
| Target mean | 13,6352 | 9,2199 | 38,0123 |
| Target p50 | 1,7833 | 1,7667 | 37,8333 |
| Target std | 27,9530 | 21,4265 | 14,9522 |

> **Đính chính hai ô của cột E3.** `Điểm được nội suy` và `Tỉ lệ nội suy` ở trên
> (1.738 và 0,167%) là **số sai**, do lỗi đếm trong `reference_gd1.py` — xem mục 5.5.
> Giá trị đúng: **1.714 điểm, 0,165%**. Bảng giữ nguyên số cũ vì
> `results/tables/reference_E3.json` chưa sinh lại; dùng số ở mục 5.1 và ở
> `2026-09-09-ban-giao-gd1.md` làm chuẩn. Mọi ô còn lại không đổi.

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

### 3.4b Nguồn gốc catalog

- [ ] `catalog.parquet` có cột `built_on` và `built_at`
- [ ] Toàn bộ dòng sinh trên **một máy** — nhiều máy là TRƯỢT
- [ ] Bản nộp cuối sinh từ **một lệnh `--env all`**, không phải ghép từng env

`catalog.parquet` vào Git nhưng `data/processed/` thì không, nên bảng tổng hợp đi
được giữa hai máy trong khi dữ liệu thì không. Đã xảy ra thật ngày 2026-09-08:
catalog có E1 do B tính, E2 do A tính. Chi tiết ở protocol mục 6b.

### 3.5 Kiểm rò rỉ

- [ ] `data/processed/` không chứa cột nào tính từ tương lai
- [ ] Nếu B đã sinh đặc trưng rolling: kiểm có `.shift(1)` không
- [ ] Nội suy **chỉ áp cho cụm ≤ 2 điểm**, không phải toàn bộ chuỗi

---

## 4. Lệnh nghiệm thu

Toàn bộ mục 3 đã được tự động hoá. **B chạy trước khi báo xong, A chạy khi nghiệm
thu — cùng một lệnh, cùng một kết quả.**

```bash
python scripts/check_gd1.py
```

Script kiểm schema `catalog.parquet` theo protocol mục 6b, đối chiếu số với
`results/tables/reference_E*.json` theo ngưỡng ở mục 3.3, và kiểm bốn cái bẫy. Thoát
0 nếu ĐẠT, 1 nếu chưa. Chỉ đọc, không sửa gì.

Ba lệnh phụ khi cần:

```bash
# Sinh lại tham chiếu (chỉ khi protocol đổi)
python scripts/reference_gd1.py --env all

# Kiểm tra độ vững, không nội suy
python scripts/reference_gd1.py --env all --interp 0

# Toàn bộ test, gồm cả test của chính công cụ kiểm
pytest tests/ -v
```

> **Công cụ kiểm có test riêng.** `tests/test_check_gd1.py` sinh catalog giả lập và
> xác nhận `check_gd1.py` phân biệt được đạt với trượt ở bốn tình huống. Lý do:
> trong dự án này `test_env.py` đã hai lần báo đạt trên môi trường hỏng. Công cụ
> cổng nào cũng phải tự chứng minh nó bắt được lỗi.

---

## 5. Kết quả cổng

Nghiệm thu ngày **2026-09-09**, trên commit `27b19fb`, máy `DESKTOP-J03IDG1`.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 3.1 Sản phẩm | **ĐẠT** | Đủ mã nguồn, `data/processed/`, `catalog.parquet`, test xanh, log GĐ1 |
| 3.2 Bảng lọc | **ĐẠT** | Đủ sáu nhóm cột, ở `2026-09-09-ban-giao-gd1.md` |
| 3.3 Đối chiếu số | **ĐẠT** | 47/48 chỉ số lệch **0,000%**; chỉ số thứ 48 là lỗi của A, xem 5.5 |
| 3.4 Bốn cái bẫy | **ĐẠT** | Ba bẫy kiểm trực tiếp, bẫy Alibaba kiểm gián tiếp |
| 3.4b Nguồn gốc | **ĐẠT** | Một máy, một lệnh `--env all`, `built_at` đồng nhất `2026-09-09T11:50:43` |
| 3.5 Rò rỉ | **ĐẠT (phần áp dụng được)** | `.shift(1)`: **chưa kích hoạt** — chưa có mã rolling nào |

**Kết luận: ĐẠT** — điều kiện qua cổng ở `docs/research-plan.md` (chuỗi vào khớp
tuyệt đối, các chỉ số còn lại lệch ≤ 5%) đã thoả. `python scripts/check_gd1.py` xanh
toàn bộ, thoát 0, gồm cả `E3 dùng đúng 500 máy đã đóng băng` và
`Một lần chạy, một máy`.

### 5.1 Đối chiếu số — bảng lọc dựng từ `catalog.parquet`

`check_gd1.py` không so tỉ lệ clip, `target_p50` và `target_std`; A tính thêm để phủ
hết mục 3.2. Bảng đầy đủ ở `research-log/2026-09-09-ban-giao-gd1.md`.

| Chỉ số | E1 | E2 | E3 |
|---|---|---|---|
| Chuỗi vào | 0,000% | 0,000% | 0,000% |
| Bốn lý do loại | 0,000% | 0,000% | 0,000% |
| Chuỗi còn lại | 0,000% | 0,000% | 0,000% |
| Dòng hợp lệ h=1, h=6, h=12 | 0,000% | 0,000% | 0,000% |
| Mẫu clip trên 100 | 0,000% | 0,000% | 0,000% |
| Target mean, p50, std | 0,000% | 0,000% | 0,000% |
| Điểm được nội suy | 0,000% | 0,000% | *(xem 5.5)* |

Hai bản hiện thực độc lập ra **cùng con số đến từng đơn vị** trên 47/48 chỉ số, kể cả
319.082 mẫu clip của E1, 917.463 dòng h=12 của E3, và `target_std` tới bốn chữ số
thập phân. Đây là bằng chứng mạnh nhất mà cơ chế kiểm chéo này cho được.

### 5.2 Hai mục kiểm mắt

**`.shift(1)` ở rolling — chưa kích hoạt, không phải đạt.** `grep -n "rolling|shift("`
trên toàn bộ `src/` ra **0 kết quả**; `src/cwp/features/` chỉ có `__init__.py` rỗng.
Mục 3.5 gạch hai ghi *"Nếu B đã sinh đặc trưng rolling"* — điều kiện đó chưa xảy ra,
nên đây là **N/A**, không được đọc thành ĐẠT. Đã chuyển thành mục kiểm **bắt buộc**
của GĐ2, xem `research-log/gate-gd2.md` mục 3.3.

Kiểm rò rỉ phần còn lại thì đạt: `data/processed/E*.parquet` chỉ có 5 cột
`env, series_id, bucket, y, is_interp` — không cột nào tính từ tương lai, vì chưa có
cột dẫn xuất nào cả.

**Log GĐ1 — lúc nghiệm thu lần đầu thì không có.** Không tệp nào trong
`research-log/` là log GĐ1 của B; log duy nhất mang tên B là
`2026-09-06-hoan-thanh-gd0.md` (GĐ0). Theo mục 3.1 (*"thiếu bảng lọc thì trả lại
ngay"*) thì đó là căn cứ trả lại.

**Đã bù cùng ngày:** `research-log/2026-09-09-ban-giao-gd1.md`, A soạn thay B vì B
bận, số lấy nguyên từ `catalog.parquet` và `data/processed/` của B. Ghi rõ người soạn
để không khai sai người thực hiện. Quy tắc phối hợp số 2 ở `docs/research-plan.md` —
*"không có log thì coi như phiên đó chưa xong"* — giữ nguyên hiệu lực cho GĐ2, và
`gate-gd2.md` mục 3.1 ghi thẳng là lần sau không cho qua nữa.

### 5.3 Hai việc phải bù — ĐÃ XONG

1. **Chạy lại một lệnh `--env all`** ✔ — `2026-09-09T11:50:43`, cả 2.250 dòng cùng
   một dấu thời gian, `check_gd1.py` mục 1b nay là `[ ok ] Một lần chạy, một máy`.
   Mọi con số ra y hệt lần chạy tách rời, đúng như kỳ vọng với pipeline tất định.
2. **Log GĐ1 có bảng lọc đủ sáu nhóm cột** ✔ — `2026-09-09-ban-giao-gd1.md`.

### 5.4 Ghi chú quá trình

Quá trình nghiệm thu phát hiện code tự điều chỉnh mẫu cho khớp tham số — chi tiết ở
`research-log/2026-09-09-ra-soat-code-b.md`. Đã xoá và chạy lại từ đầu. Rào chắn
sinh ra từ việc này đã được đưa vào `research-log/brief-gd2-b.md`.

Bước 7 và 8 của phiếu giao việc (`tests/test_io.py`, `tests/test_resample.py`) đã
xong ở commit `27b19fb`: 28 + 41 test, toàn bộ `pytest tests/` là **81 passed**.

### 5.5 Chỗ lệch cuối cùng nằm ở bản tham chiếu của A, không phải ở B

Chênh lệch duy nhất của cả GĐ1: `diem_noi_suy` của E3 — A báo 1.738, B báo **1.714**.

Truy nguyên: đếm điểm thuộc cụm NaN ngắn (≤ 2) **chạm mép cửa sổ 8 ngày** trong
`data/processed/` ra đúng **24 ở E3, 0 ở E1, 0 ở E2** — khớp đúng phân bố chênh lệch.
Nguyên nhân ở `scripts/reference_gd1.py::interp_short`: hàm trả `int(keep.sum())`,
mà `keep` gồm cả cụm chạm mép — những cụm mà `interpolate(limit_area="inside")` không
hề lấp vì thiếu neo một phía. Dòng gán ghi NaN đè NaN nên **dữ liệu vẫn đúng**, chỉ
con số báo cáo là khống.

Bằng chứng dữ liệu hai bên giống hệt: cả 9 con số dòng hợp lệ và `target_mean/p50/std`
khớp tuyệt đối. Nếu A thật sự nội suy thêm 24 điểm thì ít nhất một trong số đó phải
lệch.

**Đã sửa** thành đếm điểm thực sự được lấp; kiểm lại trên 5 hình dạng lỗ hổng, hai
bản khớp cả giá trị lẫn số đếm. Chi tiết ở `2026-09-09-ban-giao-gd1.md`.

Đáng ghi vì hai lẽ. Một, `protocol.md` mục 6 bắt buộc khai tỉ lệ nội suy với lý do
*"đây là can thiệp vào dữ liệu"* — khai 0,167% khi thực tế 0,165% là khai khống một
can thiệp chưa xảy ra, dù nhỏ. Hai, **lần này bản sai là của A.** Kiểm chéo hai bản
độc lập không phải để B chứng minh mình khớp A, mà để chỗ lệch nào cũng bị truy tới
cùng, bất kể lỗi thuộc bên nào.

`results/tables/reference_E3.json` vẫn giữ số cũ. Cổng không đổi kết luận (lệch
1,381% < 5%), nhưng muốn khớp tuyệt đối thì sinh lại:

```bash
python scripts/reference_gd1.py --env E3 --out results/tables/reference_E3.json
```

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
