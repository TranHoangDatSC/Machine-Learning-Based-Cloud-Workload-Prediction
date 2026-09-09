# 2026-09-09 — GĐ2: module đặc trưng và bốn phép kiểm rò rỉ

**Người thực hiện:** B (agent)
**Giai đoạn:** GĐ2
**Thời lượng:** ~1 giờ (Bước 1 và Bước 2 của `research-log/brief-gd2-b.md`)

> **Trạng thái: đang làm dở.** Log này mới ghi Bước 1 và Bước 2. Bước 3–7 chưa chạy
> lệnh nào, nên không mục nào dưới đây nói "đã hoàn thành" cho chúng. `check_gd2.py`
> hiện báo **CHƯA ĐẠT** — đúng như phải thế khi chưa có `data/features/`.

## Mục tiêu phiên

Viết `src/cwp/features/` theo protocol mục 8 và QĐ-010, rồi viết
`tests/test_features.py` với bốn phép kiểm rò rỉ R1–R4 — và chứng minh bộ test đó
biết đỏ, không chỉ biết xanh.

## Đã làm

- **Bước 0.** `test_env.py` 12/12, `check_gd1.py` **ĐẠT**, `pytest tests/ -q` 90
  passed. Nền GĐ1 còn nguyên trước khi động vào GĐ2.
- **Bước 1.** `src/cwp/features/` — 4 module, 448 dòng.
- **Bước 2.** `tests/test_features.py` — 38 test, tất cả xanh.
- **Bước 2 (phần sau).** Phá code 7 kiểu, xác nhận test bắt được từng kiểu. Đóng gói
  thành `scripts/pha_features.py` để A chạy lại được.

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

### Đối chiếu neo GĐ1 — đã chạy, nhưng đây chưa phải Bước 3

Chưa viết `scripts/build_features.py` và chưa ghi tệp nào vào `data/features/`. Gọi
thẳng `valid_row_mask` trên `data/processed/` chỉ để **xem** số dòng ra bao nhiêu:

| Môi trường | h=1 | h=6 | h=12 |
|---|---:|---:|---:|
| E1 | 1.650.896 ✓ | 1.647.221 ✓ | 1.642.811 ✓ |
| E2 | 678.486 ✓ | 675.665 ✓ | 673.322 ✓ |
| E3 | 938.933 ✓ | 926.892 ✓ | 917.463 ✓ |

Chín dấu bằng, lệch 0 dòng ở cả ba môi trường. Bước 3 vẫn phải chạy lại qua script
và ghi ra parquet để `check_gd2.py` kiểm được.

Kèm một phép so gián tiếp với bản của A: tỉ lệ `y_t` lọt biên `[roll_min_6,
roll_max_6]` đo được **78,85% (E1) / 78,18% (E2) / 66,14% (E3)**, trùng với
78,9 / 78,2 / 66,1 mà `gate-gd2.md` mục 4 đo trên `reference_gd2.py`. Hai bản hiện
thực độc lập cùng quy ước `.shift(1)`.

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
| Toàn bộ test dự án | 128 passed | 90 cũ + 38 mới |
| Kiểu phá code bị bắt | 7/7 | `scripts/pha_features.py` ĐẠT |
| Neo số dòng GĐ1 | 9/9 khớp tuyệt đối | chưa qua Bước 3, mới gọi thẳng hàm |
| `y_t` lọt biên quá khứ | 78,85 / 78,18 / 66,14% | tham chiếu A: 78,9 / 78,2 / 66,1% |

## Quyết định

- Giữ công thức `dow` theo QĐ-010, **không** sửa theo nhãn — công thức là cái chốt và
  `check_gd2.py` so đúng nó. Chỗ cần sửa là chú thích trong `docs/decisions.md`.
- Thêm `assert_contiguous_grid` chặn bảng đầu vào đã bị lọc NaN. Không có trong phiếu;
  bỏ được mà không ảnh hưởng con số nào nếu A thấy thừa.
- Giữ `scripts/pha_features.py` trong repo thay vì chạy tay rồi vứt — bảng "phá code"
  ở trên là một lời khai, và lời khai thì phải kiểm chứng lại được.

## Vướng mắc

**Cần A quyết — không chặn Bước 3, nhưng nên chốt trước khi đóng GĐ2:**

1. **QĐ-010 chú thích `dow` sai một chữ** (mục Phát hiện 4). Sửa "0 là thứ Hai" thành
   "0 là Chủ Nhật", hoặc đổi công thức sang `+3` nếu thật sự muốn 0 là thứ Hai — nhưng
   đổi công thức thì `check_gd2.py` và `reference_gd2.json` phải sinh lại, và điều đó
   không đáng cho một nhãn.
2. **`config/features.yaml` không được code đọc.** Nó đang mô tả đúng bộ đặc trưng
   nhưng chỉ bằng lời. Ba lối: (a) bỏ tệp, (b) thêm test so nó với `spec.py`, (c) để
   nguyên và chấp nhận rủi ro trôi. Tôi nghiêng về (b).
3. **`assert_contiguous_grid` có phải việc của tầng đặc trưng không**, hay nên nằm ở
   `check_gd1.py`. Hiện để ở tầng đặc trưng vì đó là nơi giả định bị vi phạm sẽ gây
   hại.

Không có gì chặn. Bước 3–7 làm tiếp được ngay.

## Việc tiếp theo

- [ ] Bước 3 — `scripts/build_features.py --env all`, ghi 9 tệp `data/features/`
- [ ] Bước 4 — `scripts/describe_gd2.py --env all`
- [ ] Bước 5 — hình phân phối target (**điều kiện qua cổng**)
- [ ] Bước 6 — ACF/PACF, kèm tỉ lệ cặp bị bỏ ở mỗi lag
- [ ] Bước 7 — burstiness
- [ ] Bước 8 — hoàn thiện log này và chạy `check_gd2.py`

## File sinh ra

- `src/cwp/features/spec.py` — 19 tên cột chốt, hằng số QĐ-010
- `src/cwp/features/windows.py` — lag, rolling, `diff_1`, `target`
- `src/cwp/features/calendar.py` — 4 đặc trưng lịch
- `src/cwp/features/matrix.py` — luật dòng hợp lệ và ráp ma trận 22 cột
- `tests/test_features.py` — 38 test, R1–R4
- `scripts/pha_features.py` — phá code 7 kiểu, xác nhận test biết đỏ
