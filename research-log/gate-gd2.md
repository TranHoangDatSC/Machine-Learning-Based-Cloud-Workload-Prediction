# Hồ sơ cổng GĐ2

**Người giữ cổng:** A
**Trạng thái:** **MỞ — B vào làm được ngay.** Thước đo, lệnh nghiệm thu và QĐ-010 đều
đã xong. Phiếu giao việc: `research-log/brief-gd2-b.md`.
**Cập nhật:** 2026-09-09
**Giai đoạn:** Khám phá dữ liệu và bộ đặc trưng (`docs/research-plan.md` GĐ2)

Tài liệu này định nghĩa A kiểm gì khi B báo xong GĐ2. Cùng khuôn với `gate-gd1.md`:
thước đo độc lập, ngưỡng ghi trước, lệnh nghiệm thu tự động.

---

## 0. Bài học GĐ1 mang sang

Ba thứ đã chứng minh giá trị ở GĐ1, giữ nguyên:

1. **Thước đo là bản hiện thực độc lập của A**, không phải số liệu cũ. GĐ1 đạt
   0,000% trên 37/38 chỉ số vì hai bên viết riêng rồi so. Đừng đưa mã của A cho B.
2. **Công cụ kiểm phải có test của chính nó.** `test_env.py` từng hai lần báo đạt
   trên môi trường hỏng; `check_gd1.py` vì thế có `test_check_gd1.py` sinh catalog
   giả lập và xác nhận nó phân biệt được đạt với trượt. `check_gd2.py` phải có tương
   đương.
3. **Rào chắn "đừng code hướng về con số"** phải nằm trong mọi prompt gửi agent. Lý
   do ở `2026-09-09-ra-soat-code-b.md`.

Một thứ GĐ1 **chưa** kiểm được và nay thành trọng tâm: `.shift(1)` ở rolling. Mục
3.5 của `gate-gd1.md` ghi *"nếu B đã sinh đặc trưng rolling"* — điều kiện đó chưa
xảy ra, `src/cwp/features/` còn rỗng. Toàn bộ rủi ro rò rỉ dồn vào GĐ2.

---

## 1. Thước đo là gì

Hai nguồn, dùng cho hai loại chỉ số khác nhau.

**Neo cứng từ GĐ1.** `data/catalog.parquet` đã được kiểm chéo và khớp tham chiếu của
A đến từng đơn vị. Mọi con số GĐ2 dẫn xuất từ đó phải khớp **tuyệt đối**, không có
ngưỡng sai số — vì hai bên tính trên cùng một tệp `data/processed/`, lệch nghĩa là
sai chứ không phải nhiễu.

**Bản hiện thực độc lập của A:** `scripts/reference_gd2.py` — **đã viết 2026-09-09**,
chạy ra `results/tables/reference_gd2.json`. Sinh 19 đặc trưng theo protocol mục 8,
đếm dòng hợp lệ, đo ACF và CV.

Cố ý dùng lối nghĩ khác B: nạp mỗi môi trường thành **một ma trận numpy
`(số chuỗi, 2304)`** rồi dịch theo trục thời gian, thay vì `groupby(series_id)` trên
bảng dài. Ranh giới chuỗi khi đó là ranh giới hàng, nên lỗi bắc cầu giữa hai chuỗi
không xảy ra được về mặt cấu trúc. Độc lập cả về cách tiếp cận, không chỉ về dòng mã.

> **Đừng đưa `reference_gd2.py` cho agent đang viết `src/cwp/features/` đọc.** Nếu
> cùng một agent viết cả hai bản thì việc chúng khớp nhau không chứng minh gì.

---

## 2. Số liệu tham chiếu

> Mọi số dưới đây đều **đo được**, không phỏng đoán. Một con số sai ở bảng này sẽ
> thành "đáp án" mà cả hai bên vô thức hướng tới, đúng cái bẫy QĐ-009 đã mắc — nên
> chỗ nào chưa chạy thì để trống, không điền ước lượng.

### 2.1 Neo cứng — đã kiểm chứng, khớp tuyệt đối

Lấy từ `catalog.parquet`, đã đối chiếu với `reference_E*.json` ngày 2026-09-09.
**Số dòng ma trận đặc trưng sau khi bỏ dòng không hợp lệ phải bằng đúng các số này.**

| Môi trường | Chuỗi giữ | Dòng h=1 | Dòng h=6 | Dòng h=12 |
|---|---:|---:|---:|---:|
| E1 | 735 | 1.650.896 | 1.647.221 | 1.642.811 |
| E2 | 302 | 678.486 | 675.665 | 673.322 |
| E3 | 498 | 938.933 | 926.892 | 917.463 |

Đây là phép kiểm mạnh nhất của cổng GĐ2, và nó gần như miễn phí. `reference_gd2.py`
đã tái lập đúng cả 9 con số này từ `data/processed/` bằng một hiện thực độc lập.

> **Bẫy: `dropna()` trên ma trận đặc trưng KHÔNG bằng luật dòng hợp lệ.** Nó lỏng
> hơn, và lỏng theo hướng im lặng.
>
> 19 đặc trưng chỉ chạm **15 điểm** trong cửa sổ: `t−24`, `t−12..t−1`, và `t`. Các
> điểm **`t−23` đến `t−13` không đặc trưng nào dùng** — `lag` nhảy từ 12 sang 24,
> rolling sâu nhất chỉ 12 bước. Nhưng protocol mục 8 đòi *toàn bộ* `[t−24, t]` không
> NaN, và đó là chủ ý (xem câu "một điểm NaN đơn lẻ làm hỏng 25 dòng").
>
> Đo trên sản phẩm GĐ1, `dropna` thừa ra: **E2 h=1 thừa 1.513 dòng, E3 h=1 thừa
> 7.461 dòng**. **E1 thì khớp** — NaN của E1 thưa và có cấu trúc nên lỗi không lộ.
> Ai chỉ thử E1 sẽ tưởng mình đúng.
>
> A đã mắc đúng lỗi này khi viết bản tham chiếu, và chỉ phát hiện nhờ neo cứng. Nếu
> cổng GĐ2 không có phép so này thì cả hai bên đã cùng đi tiếp với ma trận sai.

Lệch theo hướng **nhiều hơn** thì nghi `dropna` thay cho luật cửa sổ, hoặc
`min_periods=1`. Lệch theo hướng **ít hơn** thì nghi quên `groupby(series_id)` hoặc
nhầm `t+h`.

### 2.2 Phân phối target — đã có từ GĐ1

> **Đổi nhãn 2026-09-09 theo QĐ-011 điểm 2. Con số không đổi.** Ba dòng dưới đây là
> **phân phối gộp của `y`** trên các chuỗi được giữ, không phải cột `target` của ma
> trận đặc trưng. Cột `target` thật cho 13,6741 / 9,2667 / 38,3678 ở h=1 (xem
> `reference_gd2.json: target_mean_h*`) — chênh 0,3–0,9%, dưới ngưỡng 2% nên cổng
> không bắt được, và đó chính là lý do phải chốt tên gọi thay vì để hai tài liệu nói
> hai thứ dưới cùng một chữ.
>
> Bảng mô tả ở Bước 4 và hình ở Bước 5 mô tả **"CPU% sau tiền xử lý"** — quần thể
> dưới đây, không phụ thuộc horizon.

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| CPU% sau tiền xử lý — mean | 13,6352 | 9,2199 | 38,0123 |
| CPU% sau tiền xử lý — p50 | 1,7833 | 1,7667 | 37,8333 |
| CPU% sau tiền xử lý — std | 27,9530 | 21,4265 | 14,9522 |
| *(tham khảo)* p95 | **100,0000** | 60,0667 | 61,2667 |
| *(tham khảo)* điểm bằng đúng 100 | **5,1238%** | **2,2788%** | 0,0000% |

Ba con số p50 này là lý do hình phân phối ở mục 3.5 phải cẩn thận: E1 và E2 có trung
vị dưới 2%, E3 gần 38%. Vẽ trên trục tuyến tính chung thì E1 và E2 dồn hết vào cột
đầu tiên và hình không nói được gì.

### 2.3 Thống kê đặc trưng — đã sinh 2026-09-09

```bash
python scripts/reference_gd2.py --env all --out results/tables/reference_gd2.json
```

Vân tay từng đặc trưng (mean, std, %NaN của cả 19) nằm trong
`results/tables/reference_gd2.json`. Bảng dưới là phần A duyệt bằng mắt.

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| Số đặc trưng | 19 | 19 | 19 |
| ACF lag 1 | 0,6674 | 0,6431 | **0,8634** |
| ACF lag 6 | 0,4074 | 0,3414 | 0,6944 |
| ACF lag 12 | 0,4459 | 0,2978 | 0,6287 |
| ACF lag 24 | 0,3551 | 0,1982 | 0,4952 |
| **ACF lag 288 (chu kỳ ngày)** | 0,1334 | 0,1271 | **0,5956** |
| Cặp bị bỏ khi tính ACF lag 1 | 1,43% | 0,35% | 9,76% |
| CV p25 / **p50** / p75 | 0,173 / **0,497** / 1,018 | 0,188 / **0,537** / 1,342 | 0,248 / **0,286** / 0,343 |
| CV IQR | 0,845 | 1,154 | **0,096** |

Ba điều đọc ra được ngay, và cả ba đều liên quan trực tiếp tới RQ2 và RQ3:

1. **E3 mượt hơn hẳn.** ACF lag 1 là 0,86 so với 0,67 và 0,64. Máy vật lý gộp tải
   của nhiều VM nên nhiễu triệt tiêu bớt — khớp với chênh lệch đơn vị quan sát đã
   chấp nhận ở QĐ-004.
2. **Chỉ E3 có chu kỳ ngày rõ.** ACF tại lag 288 là 0,60 với E3, còn E1 và E2 chỉ
   0,13. Đáng chú ý: chu kỳ này đọc được **dù mốc thời gian E3 là tương đối** — pha
   chưa biết không xoá được tính tuần hoàn. Đây là lập luận ủng hộ việc vẫn giữ đặc
   trưng lịch cho E3 (mục 6).
3. **E1 và E2 bursty hơn nhiều.** IQR của CV là 0,845 và 1,154, so với 0,096 của E3.
   Đủ chênh để dùng burstiness làm biến phân tầng ở GĐ3.

E1 có một chi tiết lạ: ACF lag 12 (0,4459) **cao hơn** lag 6 (0,4074). Không đơn
điệu — có thể là nhịp một giờ. Chưa giải thích; nếu B thấy lại thì đó là xác nhận,
không phải trùng hợp.

---

## 3. Danh sách A kiểm khi B nộp

Chạy theo thứ tự. Trượt mục nào thì dừng, không kiểm tiếp.

### 3.1 Sản phẩm có đủ không

- [ ] `src/cwp/features/` — sinh lag, rolling, sai phân, lịch theo protocol mục 8
- [ ] `tests/test_features.py` chạy xanh, có đủ bốn phép kiểm rò rỉ ở mục 3.3
- [ ] `results/tables/` — bảng thống kê mô tả sau lọc, ba môi trường
- [ ] `results/figures/` — hình phân phối target, ACF/PACF, burstiness
- [ ] Hình sinh **bằng script**, không phải ô notebook đã mất
- [ ] Log GĐ2 của B trong `research-log/`

Thiếu log hoặc thiếu `tests/test_features.py` thì trả lại ngay. GĐ1 đã cho qua một
lần thiếu log (`gate-gd1.md` mục 5.2); lần này thì không.

### 3.2 Bộ đặc trưng phải khớp protocol mục 8

Đúng 19 đặc trưng, không thừa không thiếu. Thừa một đặc trưng ngoài danh sách là đổi
giao thức, mà B không được đổi giao thức (`docs/research-plan.md`, quy tắc phối hợp 1).

| Nhóm | Tên cột | Số lượng |
|---|---|---:|
| Lag | `lag_1, lag_2, lag_3, lag_6, lag_12, lag_24` | 6 |
| Rolling cửa sổ 6 | `roll_mean_6, roll_std_6, roll_min_6, roll_max_6` | 4 |
| Rolling cửa sổ 12 | `roll_mean_12, roll_std_12, roll_min_12, roll_max_12` | 4 |
| Sai phân | `diff_1` | 1 |
| Lịch | `hour_sin, hour_cos, dow_sin, dow_cos` | 4 |
| | **Tổng** | **19** |

Tên cột chốt theo QĐ-010, không phải gợi ý. `check_gd2.py` so đúng từng tên.

**Schema tệp `data/features/{env}_h{h}.parquet`:** 19 cột trên, cộng `series_id`,
`bucket`, và `target` (giá trị `y` tại `t+h`). Đúng 22 cột, không thừa cột nào.

- [ ] Đủ 19, đúng tên cột
- [ ] Không có đặc trưng nào dùng thông tin từ chuỗi khác (protocol mục 8 câu đầu)
- [ ] Không có đặc trưng nào lấy từ `catalog.parquet` (mean, std của cả chuỗi — đó là
      thống kê tính trên toàn bộ thời gian, gồm cả tương lai)

### 3.3 Bốn phép kiểm rò rỉ

Đây là phần quan trọng nhất của cổng. Cả bốn phải tự động hoá được trong
`tests/test_features.py`, không kiểm bằng mắt.

**R1 — Không chạm tương lai.** Lấy một chuỗi, sinh đặc trưng. Thay toàn bộ `y` tại
`t+1` trở đi bằng NaN, sinh lại. Mọi đặc trưng tại `t` **phải không đổi**.

> Đây là phép kiểm quyết định. Nó bắt mọi dạng rò rỉ tương lai mà không cần biết B
> hiện thực thế nào — kể cả `center=True` trong rolling, `interpolate` sau khi sinh
> đặc trưng, hay `fillna(method="bfill")`.

**R2 — Rolling loại điểm hiện tại.** protocol mục 8: *"Mọi thống kê rolling tính chỉ
trên quá khứ, không bao gồm điểm hiện tại."* Nên `rolling_mean_6` tại `t` phải bằng
trung bình của đúng sáu điểm `y[t−6], …, y[t−1]` — tức `.shift(1).rolling(6)`.

Lưu ý phân biệt: `y_t` **là** đầu vào hợp lệ tại thời điểm `t` (sai phân `y_t − y_{t−1}`
dùng nó). Nên R2 không phải chống rò rỉ, mà là **đúng đặc tả**. Vẫn bắt buộc: hai bản
hiện thực chỉ so được với nhau khi cùng một quy ước cửa sổ.

- [ ] Trên `y = [1,2,3,4,5,6,7,8]`: `rolling_mean_6` tại `t=6` ra **3,5**
      (trung bình `y[0..5]`), không phải 4,5 (trung bình `y[1..6]`)
- [ ] `rolling_std_12` dùng cùng quy ước
- [ ] Không có `min_periods=1` — sáu dòng đầu mỗi chuỗi phải có
      `rolling_mean_6` là NaN

**R3 — Không bắc cầu qua ranh giới chuỗi.** `data/processed/E1.parquet` là 735 chuỗi
nối nhau trong một bảng. Lag và rolling phải tính theo `groupby("series_id")`, nếu
không thì đuôi chuỗi này chảy vào đầu chuỗi kia.

- [ ] 24 dòng đầu của **mỗi** `series_id` có `lag_24` là NaN
- [ ] Ghép hai chuỗi giả lập khác hẳn nhau, kiểm đặc trưng đầu chuỗi sau không mang
      dấu vết chuỗi trước

**R4 — Số dòng khớp neo GĐ1.** Bảng ở mục 2.1, khớp **tuyệt đối** cho cả ba môi
trường và cả ba horizon. Chín con số, chín dấu bằng.

- [ ] Lọc dòng bằng **luật cửa sổ** `[t−24, t]` sạch, **không** bằng `dropna()` trên
      ma trận đặc trưng — xem bẫy ở mục 2.1, hai thứ đó khác nhau
- [ ] Kiểm cả ba môi trường, không chỉ E1. E1 khớp kể cả khi làm sai
- [ ] Kiểm ngược: mọi dòng hợp lệ theo luật đều tính được đủ 19 đặc trưng (chiều này
      phải đúng; chiều ngược lại thì không)

### 3.4 Ba cái bẫy của GĐ2

- [ ] **Mốc thời gian E3 là tương đối, không phải epoch.** Xem mục 6 — đây là vấn đề
      đã đo được, không phải rủi ro giả định. Kiểm: `hour` suy từ bucket đầu của E1
      phải ra `2013-08-12T13:40Z`, của E2 ra `2013-07-31T22:00Z`; E3 thì **không** ra
      giờ thật được và B không được lặng lẽ coi nó là epoch.
- [ ] **Bucket không được đánh số lại từ 0 theo từng chuỗi.** E1 và E2 phải giữ
      bucket tuyệt đối `floor(t/300)`; đánh số lại làm `hour_sin` vô nghĩa mà không
      báo lỗi gì. `tests/test_resample.py::test_to_grid_dung_luoi_tuyet_doi_khong_danh_so_lai_tu_0`
      đã chặn ở tầng `to_grid`, cần chặn tiếp ở tầng đặc trưng.
- [ ] **ACF trên chuỗi có NaN.** `statsmodels.acf` mặc định không nhận NaN;
      `dropna()` trước khi tính sẽ **co trục thời gian lại** — lag 1 sau khi dropna
      có thể là cách nhau 2 giờ thật. Kiểm: hỏi B xử lý NaN thế nào, câu trả lời phải
      là loại theo cặp `(t, t+k)` chứ không phải nén chuỗi.
- [ ] **CV của chuỗi tải thấp.** `CV = std/mean` nổ khi mean gần 0. Ở đây bộ lọc
      `gan_chet` đã bỏ mọi chuỗi mean < 1,0 nên CV bị chặn, nhưng vẫn phải báo
      **trung vị và IQR**, không phải trung bình CV — một chuỗi mean 1,01 vẫn kéo
      trung bình đi rất xa.

### 3.5 Điều kiện qua cổng — hình phân phối target

`docs/research-plan.md`: *"có hình phân phối target ba môi trường — đây là hình quan trọng
nhất của paper, nó dựng nền cho toàn bộ lập luận ở RQ3."*

- [ ] Ba môi trường trên **cùng một hình**, cùng trục
- [ ] Trục đọc được: E1/E2 p50 dưới 2, E3 gần 38 (mục 2.2). Trục tuyến tính chung
      làm E1/E2 biến mất — dùng ECDF, hoặc log1p, hoặc trục phụ, nhưng **phải nêu rõ
      chọn gì và vì sao** trong log
- [ ] Hình cho thấy được điều mà RQ3 dựa vào: ba môi trường khác nhau về **mức tải**,
      và câu hỏi transfer là thành phần nào của tín hiệu sống sót qua khác biệt đó
- [ ] Sinh lại được bằng một lệnh, ghi trong log
- [ ] **Chú thích trần 100** (QĐ-011 điểm 3). 5,12% điểm của E1 và 2,28% của E2 nằm
      đúng tại 100; phân vị 95 của E1 chính là trần. Hình sẽ có một cột dựng đứng ở
      mép phải cho E1/E2 mà E3 không có — không chú thích thì người đọc tưởng đó là
      đặc tính workload chứ không phải hệ quả của bước clip
- [ ] Vẽ và mô tả **phân phối gộp của `y`**, không phải cột `target` (QĐ-011 điểm 2)

Hình này A duyệt bằng mắt, không tự động hoá được. Hai hình còn lại (ACF/PACF,
burstiness) A chọn 2–3 hình đưa vào paper theo kế hoạch.

---

## 4. Lệnh nghiệm thu

```bash
python scripts/check_gd2.py
pytest tests/ -v
```

`check_gd2.py` tự động hoá mục 3.2, 3.3 (R2–R4) và bẫy mốc thời gian ở 3.4, cộng một
phép so vân tay từng đặc trưng (mean và std của cả 19) với `reference_gd2.json`.
Còn lại **R1** nằm ở `tests/test_features.py` vì cần gọi lại hàm sinh đặc trưng, và
**mục 3.5** thì A duyệt bằng mắt.

Hai phép kiểm đáng nói vì chúng bắt lỗi mà không cần tính lại đặc trưng từ `y`:

- **Bất biến cửa sổ.** `roll_min_6 ≤ lag_1 ≤ roll_max_6`, `roll_mean_6` nằm giữa min
  và max, và cửa sổ 12 bao cửa sổ 6.
- **`.shift(1)` có thật không.** `y_t = lag_1 + diff_1` tính lại được từ chính ma
  trận. Quên `.shift(1)` thì cửa sổ thành `[t−5, t]` nên luôn chứa `y_t`, tỉ lệ
  `roll_min_6 ≤ y_t ≤ roll_max_6` bằng **đúng 100%**. Làm đúng thì tỉ lệ đó là
  **78,9% (E1), 78,2% (E2), 66,1% (E3)** — đo trên bản tham chiếu. Ngưỡng đặt ở
  99,9%, nằm giữa hai vùng rất xa nhau.

Kèm theo, đúng bài học GĐ1: **`tests/test_check_gd2.py`** dựng thế giới giả lập ba
môi trường rồi phá bảy kiểu, xác nhận `check_gd2.py` bắt được từng kiểu — quên
`.shift(1)`, giữ dòng thiếu lịch sử, lag bắc cầu qua chuỗi, `dropna` thay luật cửa
sổ, thừa đặc trưng, lịch sai gốc, sai `ddof`. Cộng một ca "đúng hết phải ĐẠT" và một
ca "chưa làm thì báo thiếu, không đổ vỡ". **9 test, tất cả xanh.**

---

## 5. Kết quả cổng

Điền khi nghiệm thu.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 3.1 Sản phẩm | | |
| 3.2 Bộ đặc trưng | | |
| 3.3 Rò rỉ R1–R4 | | |
| 3.4 Ba cái bẫy | | |
| 3.5 Hình phân phối | | |

**Kết luận:**
**Ngày duyệt:**

---

## 6. Hai điểm mơ hồ — ĐÃ CHỐT, xem QĐ-010

Cả hai đã thành `docs/decisions.md` QĐ-010 ngày 2026-09-09 và đã sửa vào
`docs/protocol.md` mục 8. Tóm tắt để khỏi phải mở tệp khác:

**1. Đặc trưng lịch của E3 không có mốc lịch thật.** Đo được: bucket đầu của E1 là
4.587.716 (2013-08-12T13:40Z), E2 là 4.584.360 (2013-07-31T22:00Z), còn **E3 là 0** —
Alibaba ghi giây kể từ lúc bắt đầu trace, chạy 0 tới 690.900, đúng 8 ngày, không mang
thông tin ngày thật.

Chốt: E1 và E2 dùng **UTC**; E3 **vẫn sinh đủ 4 đặc trưng lịch** nhưng khai rõ `hour`
là *"giờ kể từ đầu trace"*, pha chưa biết, `dow` không diễn giải được theo lịch tuần.
Không bịa ngày bắt đầu cho Alibaba. **TN-B ở GĐ4 chạy hai biến thể, có và không có 4
đặc trưng lịch** — nếu bỏ lịch mà transfer tốt lên thì đó là finding thật cho RQ3.

Căn cứ giữ lại đặc trưng lịch cho E3: ACF tại lag 288 của E3 là **0,5956** so với
0,13 của E1 và E2 (mục 2.3). Chu kỳ ngày rất rõ và **đọc được kể cả khi pha chưa
biết** — bỏ đi là vứt tín hiệu mạnh nhất mà E3 có.

**2. Ba quy ước kỹ thuật** mà hai bản hiện thực đều "đúng" vẫn ra số khác nhau:
`ddof = 1` cho `roll_std_*` và CV; gốc `dow` là `((t // 86400) + 4) % 7`; cụm `NaN`
chạm mép cửa sổ không nội suy và không ngoại suy.

**Còn lại một điểm chưa chốt, và nó chưa chặn ai.** EDA được nhìn phần dữ liệu nào:
ACF/PACF và burstiness sẽ **dẫn tới lựa chọn đặc trưng**, mà bộ đặc trưng thì đã cố
định ở protocol mục 8 rồi — nên rủi ro rò rỉ quy trình ở GĐ2 gần như bằng không.
Đề xuất giữ nguyên: mô tả trên toàn cửa sổ 8 ngày, ghi rõ trong caption. Chốt lại khi
nào GĐ3 thực sự chọn siêu tham số.

---

## Phụ lục — vì sao cổng này nặng về rò rỉ

GĐ1 kiểm số: hai bên ra cùng con số thì gần như chắc chắn cả hai đúng. GĐ2 không có
tính chất đó. Một ma trận đặc trưng rò rỉ tương lai vẫn cho ra **đúng số dòng, đúng
số cột, đúng mọi thống kê mô tả** — nó chỉ lộ ra ở GĐ3 dưới dạng model đẹp bất
thường, mà lúc đó thì đã đi qua ba tuần và không ai còn nghi ngờ ma trận đặc trưng
nữa.

Đó là lý do R1 được viết dưới dạng *"đổi tương lai, đặc trưng không được đổi"* thay
vì *"kiểm có `.shift(1)` không"*. Phép kiểm thứ hai kiểm một cách hiện thực; phép
kiểm thứ nhất kiểm chính điều ta cần đúng.
