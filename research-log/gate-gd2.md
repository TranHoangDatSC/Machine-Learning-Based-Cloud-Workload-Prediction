# Hồ sơ cổng GĐ2

**Người giữ cổng:** A
**Trạng thái:** đang dựng — **A phải làm xong mục 2 và mục 4 trước khi B bắt đầu**
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

**Bản hiện thực độc lập của A:** `scripts/reference_gd2.py` — *chưa viết*. Sinh ma
trận đặc trưng theo protocol mục 8 và bộ thống kê mô tả, để đối chiếu với sản phẩm
của B. Đây là việc A phải làm **trước khi** B bắt đầu, đúng như GĐ1.

---

## 2. Số liệu tham chiếu

> **CHƯA SINH.** Bảng dưới đây trống có chủ đích — A chưa chạy `reference_gd2.py`.
> Không điền số phỏng đoán vào đây; một con số sai ở bảng này sẽ thành "đáp án" mà
> cả hai bên vô thức hướng tới, đúng cái bẫy QĐ-009 đã mắc.

### 2.1 Neo cứng — đã kiểm chứng, khớp tuyệt đối

Lấy từ `catalog.parquet`, đã đối chiếu với `reference_E*.json` ngày 2026-09-09.
**Số dòng ma trận đặc trưng sau khi bỏ dòng không hợp lệ phải bằng đúng các số này.**

| Môi trường | Chuỗi giữ | Dòng h=1 | Dòng h=6 | Dòng h=12 |
|---|---:|---:|---:|---:|
| E1 | 735 | 1.650.896 | 1.647.221 | 1.642.811 |
| E2 | 302 | 678.486 | 675.665 | 673.322 |
| E3 | 498 | 938.933 | 926.892 | 917.463 |

Đây là phép kiểm mạnh nhất của cổng GĐ2, và nó gần như miễn phí. Định nghĩa dòng hợp
lệ ở protocol mục 8 (`[t−24, t]` và `t+h` đều không NaN) trùng đúng với điều kiện để
19 đặc trưng ở mục 8 tính được. Lệch một dòng nghĩa là có đặc trưng dùng cửa sổ sai —
`min_periods=1` là thủ phạm phổ biến nhất.

### 2.2 Phân phối target — đã có từ GĐ1

| Chỉ số | E1 | E2 | E3 |
|---|---:|---:|---:|
| Target mean | 13,6352 | 9,2199 | 38,0123 |
| Target p50 | 1,7833 | 1,7667 | 37,8333 |
| Target std | 27,9530 | 21,4265 | 14,9522 |

Ba con số p50 này là lý do hình phân phối ở mục 3.5 phải cẩn thận: E1 và E2 có trung
vị dưới 2%, E3 gần 38%. Vẽ trên trục tuyến tính chung thì E1 và E2 dồn hết vào cột
đầu tiên và hình không nói được gì.

### 2.3 Thống kê đặc trưng — A sinh sau

```bash
python scripts/reference_gd2.py --env all --out results/tables/reference_gd2.json
```

| Chỉ số | E1 | E2 | E3 |
|---|---|---|---|
| Số đặc trưng | | | |
| Tỉ lệ NaN mỗi đặc trưng | | | |
| ACF lag 1 / 6 / 12 / 24 (trung vị theo chuỗi) | | | |
| CV trung vị, IQR | | | |

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

| Nhóm | Đặc trưng | Số lượng |
|---|---|---:|
| Lag | `t-1, t-2, t-3, t-6, t-12, t-24` | 6 |
| Rolling cửa sổ 6 | mean, std, min, max | 4 |
| Rolling cửa sổ 12 | mean, std, min, max | 4 |
| Sai phân | `y_t − y_{t−1}` | 1 |
| Lịch | `hour_sin, hour_cos, dow_sin, dow_cos` | 4 |
| | **Tổng** | **19** |

- [ ] Đủ 19, đúng tên nhóm
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

Hình này A duyệt bằng mắt, không tự động hoá được. Hai hình còn lại (ACF/PACF,
burstiness) A chọn 2–3 hình đưa vào paper theo kế hoạch.

---

## 4. Lệnh nghiệm thu

```bash
python scripts/check_gd2.py     # CHƯA VIẾT — A làm trước khi B bắt đầu
pytest tests/ -v
```

`check_gd2.py` phải tự động hoá được mục 3.2, 3.3 (R2–R4) và 3.4 bẫy múi giờ. R1 và
mục 3.5 nằm ở `tests/test_features.py` và ở mắt A.

Kèm theo, đúng bài học GĐ1: **`tests/test_check_gd2.py`** sinh ma trận đặc trưng giả
lập và xác nhận `check_gd2.py` bắt được ít nhất bốn tình huống hỏng — thiếu
`.shift(1)`, `min_periods=1`, lag bắc cầu qua chuỗi, và số dòng lệch neo.

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

## 6. Hai điểm A phải chốt trước khi B bắt đầu

Cả hai đều là chỗ protocol chưa nói rõ. Chốt xong ghi vào `docs/decisions.md` rồi mới
sửa `docs/protocol.md` — B không tự quyết.

**Đặc trưng lịch của E3 không có mốc lịch thật.** Đây là điểm chặn nặng nhất, đo được
ngày 2026-09-09 trên chính `data/processed/`:

| Môi trường | bucket đầu | `bucket × 300` | Đọc ra |
|---|---:|---:|---|
| E1 | 4.587.716 | 1.376.314.800 | 2013-08-12T13:40:00Z — **giờ thật** |
| E2 | 4.584.360 | 1.375.308.000 | 2013-07-31T22:00:00Z — **giờ thật** |
| E3 | **0** | 0 | 1970-01-01T00:00:00Z — **vô nghĩa** |

`time_stamp` của Alibaba là **giây tính từ lúc bắt đầu trace**, không phải epoch:
E3 chạy từ 0 tới 690.900 giây, đúng 8 ngày. Trace không mang thông tin nó bắt đầu vào
thứ mấy, giờ nào.

Hệ quả cụ thể: 4 trong 19 đặc trưng ở protocol mục 8 là lịch. Với E3 chúng sẽ nói
"1970-01-01, thứ Năm" — sai lệch pha một lượng **không biết được**, và `dow` thì hoàn
toàn bịa. protocol mục 8 không lường trường hợp này.

Điều quan trọng: **lệch pha hằng số vô hại với TN-A, chí mạng với TN-B.** Trong cùng
một môi trường, model tự học được pha, nên "giờ 0" là lúc nào không quan trọng. Xuyên
môi trường thì `hour_sin = 0.5` của E1 và của E3 là hai thời điểm khác nhau trong
ngày — đúng chỗ RQ3 hỏi thành phần nào transfer được.

> Đề xuất, A quyết:
> 1. **E1, E2 dùng UTC**, không quy về giờ địa phương Hà Lan. Nhất quán quan trọng
>    hơn đúng giờ bản địa.
> 2. **E3 sinh lịch từ mốc tương đối**, khai báo thẳng `hour` của E3 là "giờ kể từ
>    lúc bắt đầu trace", pha chưa biết. Không bịa ngày bắt đầu cho Alibaba, kể cả khi
>    tìm được con số đâu đó trên mạng — không kiểm chứng được thì không đưa vào.
> 3. **TN-B báo cáo cả có và không có 4 đặc trưng lịch.** Nếu bỏ lịch đi mà transfer
>    tốt lên thì bản thân điều đó là finding cho RQ3, và là finding thật.
> 4. `dow` của E3 ghi rõ trong Limitations là không diễn giải được theo lịch tuần.

Chốt xong thì đây là **QĐ-010**, và protocol mục 8 phải sửa theo — đây là chỗ giao
thức thiếu, không phải chỗ B làm sai.

**EDA được nhìn phần dữ liệu nào.** protocol mục 9 chia 70/15/15 theo thời gian, test
chỉ chạm một lần. GĐ2 là giai đoạn khám phá, và ACF/PACF với burstiness sẽ **dẫn tới
lựa chọn đặc trưng** — nhìn vào test rồi chọn đặc trưng là rò rỉ ở mức quy trình,
loại rò rỉ không test nào bắt được.

> Đề xuất: mọi phân tích **dẫn tới quyết định** (ACF/PACF, burstiness, chọn lag) tính
> trên **phần train 70%**. Hình phân phối target mô tả dữ liệu chứ không dẫn tới
> quyết định nào, dùng toàn cửa sổ 8 ngày cũng được, nhưng phải ghi rõ trong caption
> là toàn cửa sổ.

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
