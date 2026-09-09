# 2026-09-09 — GĐ2: module đặc trưng và bốn phép kiểm rò rỉ

**Người thực hiện:** B (agent)
**Giai đoạn:** GĐ2
**Thời lượng:** ~4 giờ (Bước 1–5 của `research-log/brief-gd2-b.md`)

> **Trạng thái: đang làm dở.** Log này ghi Bước 1–5. Bước 6 và 7 chưa chạy lệnh
> nào, nên không mục nào dưới đây nói "đã hoàn thành" cho chúng.
>
> `check_gd2.py` nay báo **12/12 sản phẩm** — nhưng dòng `results/figures/` của nó chỉ
> kiểm thư mục có tệp không rỗng, và thư mục đó mới có hình phân phối. **ACF/PACF và
> burstiness vẫn chưa làm.** Đừng đọc 12/12 thành xong GĐ2.
>
> `scripts/check_gd2.py` báo **ĐẠT** — nhưng đó là phần cổng **tự động hoá được**
> (mục 3.2, R2–R4, bẫy mốc thời gian, vân tay đặc trưng). Điều kiện qua cổng thật ở
> `gate-gd2.md` mục 3.5 là **hình phân phối**, và A duyệt bằng mắt. Hình đã có
> (Bước 5) nhưng **chưa ai duyệt**, nên GĐ2 chưa qua cổng.
>
> Giữa Bước 3 và Bước 4 có một đợt rà soát toàn dự án trước khi viết paper, sinh ra
> **QĐ-011**. Kết quả ở `research-log/2026-09-09-ra-soat-truoc-paper.md`; Bước 4 làm
> theo định nghĩa quần thể mà QĐ-011 điểm 2 chốt.

## Mục tiêu phiên

Viết `src/cwp/features/` theo protocol mục 8 và QĐ-010, viết `tests/test_features.py`
với bốn phép kiểm rò rỉ R1–R4 — và chứng minh bộ test đó biết đỏ, không chỉ biết
xanh — rồi sinh chín ma trận đặc trưng và đối chiếu với neo GĐ1.

## Đã làm

- **Bước 0.** `test_env.py` 12/12, `check_gd1.py` **ĐẠT**, `pytest tests/ -q` 90
  passed. Nền GĐ1 còn nguyên trước khi động vào GĐ2.
- **Bước 1.** `src/cwp/features/` — 4 module, 448 dòng.
- **Bước 2.** `tests/test_features.py` — 38 test, tất cả xanh.
- **Bước 2 (phần sau).** Phá code 7 kiểu, xác nhận test bắt được từng kiểu. Đóng gói
  thành `scripts/pha_features.py` để A chạy lại được.
- **Bước 3.** `scripts/build_features.py --env all` — 9 tệp, khớp tuyệt đối chín neo.
- **Rà soát trước paper.** 8 phát hiện, chốt thành QĐ-011 — log riêng.
- **Bước 4.** `scripts/describe_gd2.py --env all` — 9 chỉ số neo lệch 0,0000%.
- **Bước 5.** `scripts/fig_target_dist.py` — hình phân phối, hai bản: duyệt cổng và
  đưa vào paper. Đây là **điều kiện qua cổng GĐ2**, chờ A duyệt bằng mắt.
- **Ngoài phiếu.** Sửa nhãn `dow` sai trong QĐ-010 và protocol mục 8 (mục Phát hiện 4),
  và thêm `data/features/**` vào `.gitignore` — 351 MB parquet suýt lọt vào Git.

## Bước 1 — `src/cwp/features/`

| Tệp | Việc |
|---|---|
| `spec.py` | 19 tên cột chốt theo QĐ-010, `ROLL_DDOF = 1`, `DOW_EPOCH_OFFSET = 4`, `MATRIX_COLS` 22 cột |
| `windows.py` | lag, rolling, `diff_1`, `target` — mọi phép dịch qua `groupby("series_id")` |
| `calendar.py` | 4 đặc trưng lịch từ `bucket * 300`, **một công thức cho cả ba môi trường** |
| `matrix.py` | `valid_row_mask` (luật cửa sổ `[t-24, t]`), `build_feature_frame`, `make_feature_matrix` |

Lệnh Bước 1 (`python -c "import cwp.features as f; print(f.__all__)"`) trả về 24 tên
công khai, **không có** tên nào kiểu `fill`, `impute`, `smooth`.

Ba lựa chọn hiện thực đáng ghi:

1. **Luật dòng hợp lệ tách hẳn khỏi việc sinh đặc trưng.** `valid_row_mask` tính
   trên `y` của bảng gốc bằng `rolling(25).max()` của `y.isna()`, không đụng tới ma
   trận đặc trưng. `make_feature_matrix` lọc bằng mặt nạ đó, không bằng `dropna()`.
2. **`assert_contiguous_grid` — thêm ngoài phiếu.** Lag và rolling ở đây tính theo
   *vị trí dòng*; điều đó chỉ trùng với khoảng cách *thời gian* khi lưới không thủng.
   Sản phẩm GĐ1 thoả điều kiện đó theo thiết kế, nhưng một bảng đã bị `dropna()` từ
   trước sẽ làm `lag_1` lặng lẽ thành khoảng cách 2 giờ thật — đúng cái bẫy phiếu
   cảnh báo cho ACF ở Bước 6. Giờ nó ném `ValueError` thay vì đi tiếp.
3. **Tên cột hardcode trong `spec.py`, không đọc `config/features.yaml`.** QĐ-010
   chốt tên cột nên không để config đổi được chúng. Rủi ro: hai nguồn trôi khỏi nhau
   về sau. **Cần A quyết** — xem mục Vướng mắc.

Số dòng đối chiếu với neo GĐ1: xem Bước 3.

## Bước 2 — `tests/test_features.py`

38 test, xanh hết. Phân bố:

| Nhóm | Số test | Nội dung |
|---|---:|---|
| R1 — không chạm tương lai | 7 | thay tương lai bằng NaN, và bằng **giá trị khác**; kèm một đối chứng rằng `target` **phải** đổi |
| R2 — rolling loại điểm hiện tại | 6 | `roll_mean_6` tại `t=6` ra 3,5; cửa sổ 12 cùng quy ước; `ddof = 1`; lag lấy đúng `y_{t-k}` |
| R3 — không bắc cầu qua ranh giới | 4 | `lag_24` đầu chuỗi sau là NaN; rolling chuỗi B không dính số của A; thêm chuỗi lạ vào bảng không đổi chuỗi cũ |
| R4 — cửa sổ thiếu điểm ra NaN | 4 | 6 dòng đầu NaN, dòng 7 có số; chuỗi 3 điểm toàn NaN; một NaN làm hỏng cả cửa sổ |
| Lịch | 6 | tuần hoàn 24 giờ và 7 ngày; bucket tuyệt đối; gốc `dow`; không rẽ nhánh theo môi trường |
| Luật dòng hợp lệ | 5 | khác `dropna` đúng 11 điểm; đòi cả 25 điểm; đòi target |
| Vệ sinh đầu vào | 6 | lưới thủng, thiếu cột, không sửa bảng gốc, thứ tự dòng không đổi kết quả, horizon sai |

Hai test được thêm ngoài danh sách của phiếu, và cả hai đều có lý do cụ thể:

- **R1 biến thể "thay bằng giá trị khác".** Bản NaN có điểm mù: một phép tính bỏ qua
  NaN (`skipna` mặc định của pandas) vẫn ra kết quả cũ dù nó có chạm tương lai. Thay
  bằng số thật thì không còn chỗ nấp.
- **`test_make_feature_matrix_loc_theo_luat_cua_so_chu_khong_phai_dropna`.** Phát
  hiện khi phá code: hai test về luật cửa sổ đều gọi thẳng `valid_row_mask`, nên
  chúng **vẫn xanh** nếu bộ lọc thật bị đổi thành `dropna()`. Lỗ hổng đó chỉ có neo
  số dòng của `check_gd2.py` bịt được, mà neo thì cần `data/processed/`. Xem mục
  Phát hiện.

### Kết quả phá code có chủ ý

`python scripts/pha_features.py` — sao lưu, phá, chạy pytest, khôi phục ở `finally`.

| Mã | Phá gì | Kỳ vọng | Kết quả | Test bắt được |
|---|---|---|---|---|
| P0 | không phá, đối chứng | xanh | **XANH** 38 passed | — |
| P1 | bỏ `.shift(1)` ở rolling | R2 đỏ | **ĐỎ** 5 failed | `test_r2_roll_mean_6_tai_t6...`, `test_r2_roll_min_max_6...`, `test_r2_cua_so_12...`, + 2 test R4 |
| P2 | `min_periods=1` | R4 đỏ | **ĐỎ** 6 failed | cả 4 test R4, + 2 test luật cửa sổ |
| P3 | bỏ `groupby(series_id)` | R3 đỏ | **ĐỎ** 3 failed | `test_r3_lag_24_dau_chuoi_sau_la_nan`, `test_r3_rolling_chuoi_sau_khong_mang_dau_vet...`, + 1 test R4 |
| P4 | `roll_std` dùng `ddof=0` | R2 đỏ | **ĐỎ** 2 failed | `test_r2_roll_std_6_dung_ddof_1_theo_qd010`, `test_r2_cua_so_12...` |
| P5 | `center=True` ở rolling | R1 đỏ | **ĐỎ** 12 failed | cả 6 test R1, + 6 test khác |
| P6 | gốc `dow` từ `+4` thành `+3` | lịch đỏ | **ĐỎ** 1 failed | `test_lich_goc_dow_dung_cong_thuc_chot_o_qd010` |
| P7 | `dropna()` thay luật cửa sổ | luật đỏ | **ĐỎ** 1 failed | `test_make_feature_matrix_loc_theo_luat_cua_so_chu_khong_phai_dropna` |

Ba kiểu phiếu chỉ đích danh là P1, P2, P3 — cả ba đỏ đúng nhóm phép kiểm phiếu dự
đoán. Sau khi khôi phục: 38 passed, và **chín neo GĐ1 vẫn khớp tuyệt đối** — dùng
chính phép đối chiếu số dòng làm bằng chứng mã nguồn về đúng nguyên trạng, chặt hơn
là nhìn bằng mắt.

## Bước 3 — chín ma trận đặc trưng

`python scripts/build_features.py --env all` → 9 tệp, 351 MB, 70 giây.

Script không lọc thêm gì; toàn bộ việc lọc nằm trong `cwp.features.make_feature_matrix`
và đi qua `valid_row_mask`, tức luật cửa sổ `[t-24, t]` chứ không phải `dropna()`.

### Số dòng — khớp tuyệt đối cả chín

| Môi trường | h | Số dòng | Neo `catalog.parquet` | Lệch | Chuỗi | MB |
|---|---:|---:|---:|---:|---:|---:|
| E1 | 1 | 1.650.896 | 1.650.896 | **0** | 735 | 51,4 |
| E1 | 6 | 1.647.221 | 1.647.221 | **0** | 735 | 50,6 |
| E1 | 12 | 1.642.811 | 1.642.811 | **0** | 735 | 50,2 |
| E2 | 1 | 678.486 | 678.486 | **0** | 302 | 22,2 |
| E2 | 6 | 675.665 | 675.665 | **0** | 302 | 21,9 |
| E2 | 12 | 673.322 | 673.322 | **0** | 302 | 21,7 |
| E3 | 1 | 938.933 | 938.933 | **0** | 498 | 44,9 |
| E3 | 6 | 926.892 | 926.892 | **0** | 498 | 44,2 |
| E3 | 12 | 917.463 | 917.463 | **0** | 498 | 43,7 |

Đã kiểm **cả ba** môi trường, không chỉ E1 — đúng cảnh báo của phiếu rằng E1 khớp kể
cả khi lọc sai. E2 và E3 là hai chỗ `dropna()` sẽ lộ (thừa 1.513 và 7.461 dòng), và
cả hai đều lệch 0.

Số chuỗi trong ma trận bằng đúng số chuỗi `kept` của GĐ1 ở cả ba môi trường
(735 / 302 / 498), nên không chuỗi nào bị bộ lọc dòng xoá sạch.

### `check_gd2.py` — ĐẠT

```
ĐẠT — bộ đặc trưng GĐ2 khớp protocol mục 8, không phát hiện rò rỉ.
TIẾN ĐỘ GĐ2: 11/12 sản phẩm
```

Không mục nào trượt. Một cảnh báo, và nó **đúng theo QĐ-010**: *"E3: mốc thời gian là
tương đối, không phải epoch"*.

Ba nhóm đáng ghi lại vì chúng so B với bản độc lập của A:

| Phép kiểm | Kết quả |
|---|---|
| **Vân tay 19 đặc trưng** (mean và std, so `reference_gd2.json`, ngưỡng 1e-6) | khớp ở **cả ba** môi trường |
| **R2 — `.shift(1)` có thật không**: tỉ lệ `y_t` lọt biên `[roll_min_6, roll_max_6]` | 78,85% / 78,18% / 66,14% — tham chiếu A: 78,9 / 78,2 / 66,1 |
| **R3 — ranh giới chuỗi**: mọi chuỗi có đủ 24 bucket lịch sử riêng | 735 / 302 / 498 chuỗi, không chuỗi nào vi phạm |

Vân tay khớp là phép so có giá trị nhất ở đây: A nạp mỗi môi trường thành một ma trận
numpy `(số chuỗi, 2304)` rồi dịch theo trục thời gian, B dùng `groupby(series_id)`
trên bảng dài. Hai lối nghĩ khác nhau, cùng 19 con số mean và 19 con số std đến chữ
số thập phân thứ sáu, trên cả ba môi trường.

## Bước 4 — thống kê mô tả sau lọc

`python scripts/describe_gd2.py --env all` → `results/tables/describe_gd2.{csv,md}`.

Quần thể mô tả theo **QĐ-011 điểm 2**: phân phối gộp của `y` trên các chuỗi được
giữ, trong cửa sổ 8 ngày — gọi là *"CPU% sau tiền xử lý"*, **không phải** cột
`target`. Đây là chỗ mà đợt rà soát trước Bước 4 đã gỡ được một cái bẫy đặt tên:
`gate-gd2.md` mục 2.2 gọi ba con số neo là "Target mean/p50/std" trong khi chúng mô
tả `y`, còn `reference_gd2.json` của A lại dùng đúng cột `target` — hai tài liệu nói
hai thứ dưới cùng một chữ, chênh 0,3–0,9%, dưới ngưỡng 2% nên cổng không bắt.

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| Số chuỗi | 735 | 302 | 498 |
| Điểm trong cửa sổ | 1.693.440 | 695.808 | 1.147.392 |
| Trung bình | **13,6352** | **9,2199** | **38,0123** |
| Độ lệch chuẩn | **27,9530** | **21,4265** | **14,9522** |
| Nhỏ nhất | 0,0000 | 0,0000 | 0,0000 |
| p10 / p25 | 0,7000 / 1,2000 | 0,4583 / 1,0417 | 20,9000 / 29,2500 |
| **Trung vị** | **1,7833** | **1,7667** | **37,8333** |
| p75 / p90 | 5,3667 / 57,7000 | 4,0667 / 23,5667 | 47,3333 / 56,3000 |
| p95 | **100,0000** | 60,0667 | 61,2667 |
| Lớn nhất | 100,0000 | 100,0000 | 99,8000 |
| Tỉ lệ NaN % | 1,4272 | 0,3086 | **9,2936** |
| Điểm bằng đúng 100 % | **5,1238** | **2,2788** | 0,0000 |
| Tỉ lệ nội suy % | 0,0163 | 0,0924 | 0,1647 |

**Chín chỉ số neo lệch 0,0000%** so với `gate-gd2.md` mục 2.2 — script tự đối chiếu
và thoát 1 nếu quá 2%, giống `build_features.py`.

Hai cột thêm ngoài danh sách của phiếu, mỗi cột một lý do cụ thể:

- `Điểm bằng đúng 100 %` — QĐ-011 điểm 3 đòi khai báo trần clip. Con số nói lên vấn
  đề rõ hơn mọi câu văn: **p95 của E1 chính là trần**, còn E3 thì 0%.
- `Tỉ lệ nội suy %` — protocol mục 6 liệt nó vào danh sách **bắt buộc báo cáo**.

Thêm `p10` và `p90` (phiếu chỉ đòi p25/p50/p75/p95) vì bảng *"quần thể thô"* trong
data card dùng bộ phân vị p10–p90; thiếu hai phân vị này thì hai quần thể không so
được từng dòng một. So xong thấy chênh lớn nhất ở E1: trung vị 0,84 → 1,7833, trung
bình 6,75 → 13,6352, đúng như QĐ-011 điểm 1 mô tả.

Script kiểm một bất biến trước khi tính: `set(series_id)` trong `data/processed/`
phải **bằng đúng** tập `kept` của catalog. Đây là hợp đồng giữa GĐ1 và GĐ2; lệch thì
mọi con số trong bảng mô tả một quần thể không ai định nghĩa. Hiện khớp cả ba.

Bảng trong `docs/data-card.md` mục *Sau tiền xử lý* nay là **bản chép từ tệp máy
sinh**, kèm ghi chú "sửa tay ở đây là tạo ra bản thứ hai không ai kiểm được".

## Bước 5 — hình phân phối (điều kiện qua cổng)

`python scripts/fig_target_dist.py` → `results/figures/fig_target_dist{,_paper}.{png,pdf}`
và `fig_target_dist.caption.md`.

### Chọn ECDF, và vì sao không chọn hai phương án kia

Phiếu nêu ba lối: ECDF, log1p, trục phụ.

| Phương án | Quyết định |
|---|---|
| **ECDF** | **Chọn.** Trục tung là xác suất tích luỹ nên **mỗi đường bắt buộc đi từ 0 lên 1** — không môi trường nào bị nén, kể cả khi mức tải lệch 20 lần. Không có tham số bin để vô tình chỉnh cho hình đẹp lên. Đọc thẳng được phân vị. Và khối bị kiểm duyệt tại trần hiện thành **bước nhảy nhìn thấy được** |
| log1p | Bỏ. Đọc được cả ba nhưng bóp méo khoảng cách giữa các mức tải — mà chênh lệch mức tải chính là điều hình này phải cho thấy |
| Trục phụ | **Bỏ dứt khoát.** Hai thang y trên một hình cho phép đặt hai đường cạnh nhau ở bất kỳ vị trí tương đối nào, nên hình nói được điều dữ liệu không nói |

Hai panel vì chúng trả lời hai câu khác nhau. Panel (a) trục tuyến tính trả lời câu
của RQ3: ba mức tải tách hẳn nhau. Panel (b) trục symlog phóng to vùng dưới 1%, nơi
trung vị của E1/E2 thực sự nằm — trên trục tuyến tính vùng đó chỉ chiếm vài pixel
sát trục tung.

### Hai bản, hai người đọc

- `fig_target_dist` — có panel (c) hướng dẫn đọc. Để A duyệt cổng và dán vào log.
- `fig_target_dist_paper` — **bản sạch, không có chữ văn xuôi trong hình.** Chữ nằm
  trong ảnh là chỗ của caption LaTeX; một khối văn xuôi in cứng vào PNG thì không
  sửa được khi câu chữ của bài đổi, và trông nghiệp dư trong paper.

Caption đầy đủ nằm ở `results/figures/fig_target_dist.caption.md`, gồm cả câu caption
ngắn để dán thẳng xuống dưới hình.

### Ba việc hình phải làm, và cách kiểm

| Đòi hỏi (`gate-gd2.md` mục 3.5) | Làm thế nào |
|---|---|
| Ba môi trường trên cùng một hình, cùng trục | Cả ba đường trên cùng một cặp trục ở cả hai panel |
| Trục đọc được, không đường nào bị ép sát mép | ECDF ép mọi đường dùng hết chiều cao. Đã mở ảnh nhìn bằng mắt |
| Cho thấy điều RQ3 dựa vào | Panel (a): ba đường gần như không giao nhau |
| **Chú thích trần 100** (QĐ-011 điểm 3) | Hộp chú thích chỉ vào bước nhảy tại 100, ghi 5,12% / 2,28% / 0% |
| Vẽ phân phối gộp của `y`, không phải cột `target` (QĐ-011 điểm 2) | Ghi trong phụ đề hình, trong docstring, và trong caption |
| Sinh lại bằng một lệnh | `python scripts/fig_target_dist.py` |

**Khoá vòng giữa hình và bảng.** Bảng phân vị trong hình **đọc từ**
`results/tables/describe_gd2.csv` chứ không tính lại — một nguồn sự thật, nên hình và
bảng của paper không thể lệch nhau. Script còn kiểm chéo trung vị suy từ ECDF với
`p50` trong bảng đó và thoát 1 nếu lệch quá bước lưới:

```
E1: ECDF  1,7937   bảng  1,7833
E2: ECDF  1,7741   bảng  1,7667
E3: ECDF 37,8500   bảng 37,8333
```

Chênh nhỏ là bước lưới hoành độ, không phải bất đồng về dữ liệu.

### Màu và khả năng đọc

Ba khe categorical đầu của bảng màu tham chiếu, dùng đúng thứ tự, không xoay vòng.
Chạy validator trước khi vẽ: qua cả sáu phép kiểm trên nền sáng — dải độ sáng, sàn
chroma, tách màu cho người mù màu (ΔE 9,2 deutan ở cặp xấu nhất), sàn thị lực thường
(ΔE 27,6). Một cảnh báo tương phản ở màu aqua của E3, đã bù bằng nhãn trực tiếp và
bảng phân vị. Thêm **mã hoá thứ hai bằng kiểu nét** (liền / đứt / gạch-chấm) để hình
đọc được khi in đen trắng.

### Ba lỗi bố cục tự bắt khi mở ảnh ra nhìn

Validator kiểm màu, không kiểm bố cục. Mở ảnh xem mới thấy:

1. Panel (c) **tràn chữ sang dưới bảng** — chữ bị cắt ở mép phải. Sửa bằng ngắt dòng
   theo bề rộng thật (`textwrap`) thay vì xuống dòng bằng tay.
2. Nhãn "trung vị" đặt bên phải, **bị hộp chú thích trần đè lên**. Dời sang trái.
3. Mũi tên chú thích **cắt ngang đường E3**. Dời hộp xuống vùng trống thật ở góc
   dưới phải — với `x > 60` cả ba đường đều trên `y = 0,9`, còn chú giải chiếm
   `y < 0,25`, nên dải giữa hoàn toàn rỗng.

Bản paper còn một lỗi thứ tư: tiêu đề panel (c) dài quá cột hẹp và bị cắt ở mép hình.
Rút gọn còn "Bảng phân vị".

## Phát hiện

**1. Bộ test tự nó có một lỗ hổng, và chỉ lộ ra khi phá code.** Vòng phá đầu tiên,
P7 (`dropna` thay luật cửa sổ) chạy ra **XANH**. Đây đúng là kiểu sai nguy hiểm nhất
của GĐ2 — kiểu A đã mắc khi viết bản tham chiếu, và kiểu im lặng trên E1. Nguyên
nhân: mọi test về luật cửa sổ đều gọi thẳng `valid_row_mask`, nên chúng kiểm rằng
*luật tồn tại và đúng*, không kiểm rằng *bộ lọc thật có dùng nó không*. Đã thêm test
bịt lại; P7 giờ đỏ. Nếu chỉ chạy `pytest` mà không phá code thì lỗ hổng này đi thẳng
tới Bước 3 và chỉ bị neo số dòng chặn lại — tức là muộn hơn một bước.

**2. `center=True` là kiểu sai mà chỉ R1 bắt được.** P5 không vi phạm quy ước cửa sổ
nào nhìn thấy được: `roll_min_6 ≤ lag_1 ≤ roll_max_6` vẫn đúng, cửa sổ 12 vẫn bao cửa
sổ 6. Nó chỉ đơn giản là đọc thẳng vào tương lai. `gate-gd2.md` mục 3.3 gọi R1 là
"phép kiểm quyết định" và điều đó đo được: P5 làm đỏ 12 test, nhưng nếu bỏ 6 test R1
đi thì các test còn lại đỏ vì lý do phái sinh chứ không vì rò rỉ.

**3. Chênh lệch `dropna` vs luật cửa sổ đúng bằng 11 dòng, và con số đó suy ra được.**
Trên một chuỗi giả lập 60 điểm có đúng **một** NaN, chênh lệch là 11 dòng ở cả h=1, 6,
12. 11 chính là số điểm `t-23 … t-13` mà không đặc trưng nào chạm. Không phải trùng
hợp — đó là hệ quả số học của đặc tả, nên đã viết thẳng thành test thay vì chỉ ghi
chú.

**4. QĐ-010 chú thích sai nhãn của gốc `dow`.** Công thức chốt là
`((t // 86400) + 4) % 7`, kèm chú thích *"→ 0 là thứ Hai"*. Số đo nói khác:

| Mốc | Thứ thật | Công thức ra |
|---|---|---:|
| 1970-01-01 (epoch) | thứ Năm | 4 |
| `b0` của E1 = 4.587.716 → 2013-08-12 | thứ Hai | 1 |
| `b0` của E2 = 4.584.360 → 2013-07-31 | thứ Tư | 3 |

Tức **0 là Chủ Nhật**, không phải thứ Hai. Đây chỉ là nhãn diễn giải — **không con số
nào đổi**, `check_gd2.py` cũng hiện thực đúng công thức chứ không dựa vào nhãn. Nhưng
E1 và E2 có mốc thời gian thật, nên nếu phần bàn về chu kỳ tuần trong paper đọc theo
nhãn thì nó lệch đi một ngày. Đã giữ nguyên công thức (nó là cái chốt), ghi sự thật
vào docstring test. **Cần A sửa một chữ trong QĐ-010.**

## Số liệu thu được

| Chỉ số | Giá trị | Ghi chú |
|---|---|---|
| Module đặc trưng | 4 tệp, 448 dòng | `src/cwp/features/` |
| Test đặc trưng | 38, xanh hết | `tests/test_features.py` |
| Test ghim config | 13, xanh hết | `tests/test_config.py` |
| Toàn bộ test dự án | 141 passed | 90 cũ + 38 + 13 |
| Kiểu phá code bị bắt | 7/7 | `scripts/pha_features.py` ĐẠT |
| Kiểu phá config bị bắt | 6/6 | chạy tay, bảng ở mục "Ghim config" |
| `assert_contiguous_grid` | 0,07s / 1,69 triệu dòng | 0,4% thời gian sinh đặc trưng |
| Neo số dòng GĐ1 | 9/9 khớp tuyệt đối | `build_features.py --env all` |
| Vân tay 19 đặc trưng vs A | khớp 3/3 môi trường | ngưỡng 1e-6, `check_gd2.py` mục 6 |
| `y_t` lọt biên quá khứ | 78,85 / 78,18 / 66,14% | tham chiếu A: 78,9 / 78,2 / 66,1% |
| Ma trận đặc trưng | 9 tệp, 351 MB, 61s | `data/features/` |
| `check_gd2.py` | **ĐẠT**, 11/12 sản phẩm | còn thiếu `results/figures/` |
| Thống kê mô tả | 9/9 chỉ số neo lệch **0,0000%** | `describe_gd2.py`, ngưỡng 2% |
| Bảng màu hình | qua 6/6 phép kiểm | ΔE 9,2 deutan ở cặp xấu nhất |
| Lỗi bố cục tự bắt | 4 | chỉ thấy khi mở ảnh ra nhìn |

## Quyết định

- **Sửa nhãn `dow` trong QĐ-010 và protocol mục 8**, giữ nguyên công thức. Đã ghi
  đính chính có ngày và lý do vào `docs/decisions.md` (QĐ-010) theo quy tắc "không
  sửa im lặng" ở đầu `protocol.md`. Không con số nào phải sinh lại.
- Thêm `assert_contiguous_grid` chặn bảng đầu vào đã bị lọc NaN. Không có trong phiếu;
  bỏ được mà không ảnh hưởng con số nào nếu A thấy thừa.
- Giữ `scripts/pha_features.py` trong repo thay vì chạy tay rồi vứt — bảng "phá code"
  ở trên là một lời khai, và lời khai thì phải kiểm chứng lại được.
- Thêm `data/features/**` vào `.gitignore`, cùng chỗ với `data/processed/**`. Chín
  tệp nặng 351 MB; `.gitignore` trước đó chưa có dòng nào chặn thư mục này.
- **`config/features.yaml` giữ lại làm tài liệu, không cho code đọc**, và thêm
  `tests/test_config.py` ghim nó với `spec.py`. Ghim luôn `preprocess.yaml` ở
  `grid_seconds` và `row_validity.max_lag`.
- **`assert_contiguous_grid` ở lại tầng đặc trưng**, không chuyển sang `check_gd1.py`.
- **Sản phẩm dẫn xuất thì dựng lại, không chép giữa hai máy.** Ghi thành một mục con
  trong README mục 10 kèm chuỗi lệnh đầy đủ.

## Vướng mắc

**Cả ba đã xử lý trong phiên này. Không còn gì treo.**

1. ~~QĐ-010 chú thích `dow` sai một chữ~~ → **xong**. `docs/decisions.md` QĐ-010 và
   `docs/protocol.md` mục 8 nay ghi "0 là Chủ Nhật", kèm bảng ba mốc đo được và ghi
   chú rằng công thức không đổi.
2. ~~`config/features.yaml` không được code đọc~~ → **xong**, xem mục "Ghim config"
   dưới đây.
3. ~~`assert_contiguous_grid` nằm ở tầng nào~~ → **giữ ở tầng đặc trưng**, xem mục
   "Vì sao giữ ở tầng đặc trưng".

Bước 4–7 làm tiếp được ngay.

## Ghim config với code — `tests/test_config.py`

Đếm được ngày 2026-09-09: `preprocess.yaml` có 6 nơi đọc, `datasets.yaml` 4 nơi,
còn `features.yaml`, `split.yaml`, `paths.yaml` thì **0**. Hai tệp sau mô tả GĐ3/GĐ4
chưa xây nên chưa ai đọc là bình thường; `features.yaml` mô tả thứ **vừa xây xong**
mà không ai đọc — đó mới là chỗ bất thường.

Không cho code đọc config (làm thế là biến 19 tên cột thành thứ sửa được ngoài
`decisions.md`, trái QĐ-010), cũng không xoá config. Thay vào đó: **code chốt ở
`spec.py`, config là tài liệu, `tests/test_config.py` là người gác.**

13 test. Mạnh nhất là `test_ten_19_cot_suy_tu_config_khop_spec` — dựng lại cả 19 tên
cột **từ config** rồi so với `FEATURE_COLS`, nên nó bắt được cả lệch thứ tự lẫn lệch
quy tắc ghép tên, không chỉ lệch giá trị.

Nhân tiện bổ sung ba quy ước QĐ-010 vào `features.yaml` (`rolling_ddof`,
`dow_epoch_offset`, `grid_seconds`) — trước đó tệp mô tả thiếu đúng ba thứ đã làm A
và B ra số khác nhau.

Cũng ghim luôn `preprocess.yaml`, vì ở đó có một rủi ro **thật chứ không giả định**:
`row_validity.max_lag` được `filter.py` và `build.py` đọc để đếm `valid_rows_h*` ghi
vào `catalog.parquet` — tức là neo của cổng GĐ2 — trong khi tầng đặc trưng hardcode
`MAX_LAG`. Sửa config mà không sửa `spec.py` thì chín neo lệch.

Phá config 6 kiểu để xác nhận test biết đỏ:

| Phá | Kết quả | Test bắt được |
|---|---|---|
| thêm `48` vào `lags` | ĐỎ 2 failed | `test_lags_khop_spec`, `test_ten_19_cot_suy_tu_config_khop_spec` |
| `rolling_ddof` → 0 | ĐỎ 1 failed | `test_ba_quy_uoc_qd010_khop_spec` |
| `shift_before_rolling` → false | ĐỎ 1 failed | `test_shift_before_rolling_phai_bat` |
| thêm khoá `lags_extra` | ĐỎ 1 failed | `test_config_khong_co_khoa_la` |
| `row_validity.max_lag` → 25 | ĐỎ 1 failed | `test_max_lag_cua_tien_xu_ly_bang_max_lag_cua_dac_trung` |
| `grid_seconds` → 600 | ĐỎ 1 failed | `test_grid_seconds_hai_config_bang_nhau` |

## Vì sao giữ `assert_contiguous_grid` ở tầng đặc trưng

Đo được: **0,07 giây** trên 1,69 triệu dòng của E1 — rẻ hơn lệnh `sort` đứng ngay
trước nó (0,17s), và bằng 0,4% thời gian sinh đặc trưng. Chi phí không phải yếu tố
quyết định.

Hai yếu tố quyết định:

1. `check_gd1.py` **cảnh báo chứ không đánh trượt** khi thiếu `data/processed/` —
   có chú thích trong mã ghi rõ lý do là để A nghiệm thu được trên máy chưa chạy
   tiền xử lý. Đặt phép kiểm ở đó thì **trên máy A nó không bao giờ chạy**.
2. Ở tầng đặc trưng thì nó chạy mọi lần hàm được gọi, kể cả khi ai đó mở notebook,
   `dropna()` cho gọn rồi gọi `make_feature_matrix`. Đó đúng là kịch bản gây hại, vì
   lag và rolling tính theo **vị trí dòng**.

Nhân đây bỏ một chỗ thừa trong `build_features.py`: script từng gọi `prepare_input`
rồi truyền kết quả cho `make_feature_matrix` — hàm này lại `prepare_input` lần nữa.
Nay gọi thẳng `make_feature_matrix(df, h)`. Mất thêm ~0,2 giây mỗi môi trường, đổi
lại **sản phẩm đi đúng đường mà `tests/test_features.py` kiểm**, không phải một
đường tắt song song. Tổng thời gian 70,4s → 61,0s (giảm vì bớt một lượt sắp xếp).

## Đồng bộ dữ liệu giữa hai máy — README mục 10

Câu hỏi lộ ra khi bàn việc trên: A pull repo về thì không có `data/processed/` lẫn
`data/features/` (cả hai trong `.gitignore`), nên A **không chạy được `check_gd2.py`**.
README mục 10 trước đó dừng ở `check_data.py`, không có lệnh nào dẫn từ raw sang hai
thư mục đó.

Đã thêm mục con **"Dựng lại sản phẩm dẫn xuất — không chép giữa hai máy"**: bảng ba
sản phẩm kèm kích thước và trạng thái Git, chuỗi lệnh đầy đủ từ repo vừa clone tới
hết GĐ2, và ba chỗ dễ vấp.

Chọn **dựng lại** chứ không chép, vì `check_data.py` đã xác minh md5 của raw nên hai
máy chắc chắn cùng đầu vào; pipeline xác định sau khi QĐ-009 đóng băng mẫu E3 vào
`config/e3_machines.txt`; và `catalog.parquet` — thứ duy nhất đi qua Git — chính là
bảng để hai bên so số. **Chép sản phẩm dẫn xuất sang nhau thì mất luôn phép kiểm
chéo, hai máy thành một máy.** Đó là bài học QĐ-009 và mục 6b, chỉ khác chỗ áp dụng.

## Việc tiếp theo

- [x] Bước 3 — `scripts/build_features.py --env all`, ghi 9 tệp `data/features/`
- [x] Bước 4 — `scripts/describe_gd2.py --env all`
- [x] Bước 5 — hình phân phối (**điều kiện qua cổng** — A duyệt bằng mắt)
- [ ] Bước 6 — ACF/PACF, kèm tỉ lệ cặp bị bỏ ở mỗi lag
- [ ] Bước 7 — burstiness
- [ ] Bước 8 — hoàn thiện log này và chạy `check_gd2.py`

## File sinh ra

- `src/cwp/features/spec.py` — 19 tên cột chốt, hằng số QĐ-010
- `src/cwp/features/windows.py` — lag, rolling, `diff_1`, `target`
- `src/cwp/features/calendar.py` — 4 đặc trưng lịch
- `src/cwp/features/matrix.py` — luật dòng hợp lệ và ráp ma trận 22 cột
- `tests/test_features.py` — 38 test, R1–R4
- `tests/test_config.py` — 13 test, ghim `config/*.yaml` với `spec.py`
- `scripts/pha_features.py` — phá code 7 kiểu, xác nhận test biết đỏ
- `scripts/build_features.py` — sinh 9 ma trận, đối chiếu neo GĐ1
- `scripts/describe_gd2.py` — bảng thống kê mô tả, tự đối chiếu neo
- `results/tables/describe_gd2.{csv,md}` — bảng máy sinh cho data card và paper
- `scripts/fig_target_dist.py` — hình phân phối, hai bản, tự khoá vòng với bảng Bước 4
- `results/figures/fig_target_dist{,_paper}.{png,pdf}` — hình
- `results/figures/fig_target_dist.caption.md` — caption đầy đủ, kèm câu ngắn cho paper
- `data/features/{E1,E2,E3}_h{1,6,12}.parquet` — 9 tệp, 351 MB, **không commit**

## File sửa

- `docs/decisions.md` — QĐ-010: nhãn `dow` "0 là thứ Hai" → "0 là Chủ Nhật", kèm đính
  chính có ngày và bảng ba mốc đo được
- `docs/protocol.md` — mục 8, ba quy ước: cùng sửa nhãn, trỏ về đính chính ở QĐ-010
- `config/features.yaml` — thêm ba quy ước QĐ-010 còn thiếu, và nói rõ ngay đầu tệp
  rằng đây là tài liệu, bản chốt ở `spec.py`
- `README.md` — mục 10: thêm "Dựng lại sản phẩm dẫn xuất — không chép giữa hai máy"
- `.gitignore` — thêm `data/features/**`
- `research-log/INDEX.md` — thêm một dòng
