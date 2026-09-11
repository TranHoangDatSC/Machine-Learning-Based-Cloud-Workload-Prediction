# Hồ sơ cổng GĐ4

**Người giữ cổng:** A
**Trạng thái:** **MỞ — B vào làm được ngay.** Thước đo `scripts/reference_gd4.py` đã
chạy, năm quy ước đã chốt ở QĐ-016. Phiếu giao việc: `research-log/brief-gd4-b.md`.
**Cập nhật:** 2026-09-11
**Giai đoạn:** Thí nghiệm B — xuyên môi trường (`docs/research-plan.md` GĐ4)

Cùng khuôn với `gate-gd1.md`, `gate-gd2.md`, `gate-gd3.md`: thước đo độc lập, ngưỡng
ghi trước, lệnh nghiệm thu tự động.

---

## 0. Bốn bài học mang sang

1. **Thước đo là bản hiện thực độc lập.** Cơ chế này đã bắt được **mọi** lỗi của dự án
   — và ở ba giai đoạn liền, lỗi hoá ra nằm ở **thước đo của A**, không phải sản phẩm
   của B (GĐ1 đếm điểm nội suy, GĐ2 `dropna`, GĐ3 chuỗi `E1_830`). Phép so này không
   phải để B chứng minh mình khớp A; nó để **chỗ lệch nào cũng bị truy tới cùng**.
2. **Công cụ kiểm phải có test của chính nó.** `tests/test_check_gd4.py` dựng thế
   giới giả lập rồi phá **16 kiểu**, bắt được cả 16 — như ba lần trước.
3. **Rào chắn "đừng code hướng về con số"** vào mọi prompt.
4. **Mới ở GĐ4:** rào chắn *"đừng để chuẩn hoá làm số đẹp lên"*. Xem mục 0b.

### 0b. Cái bẫy của GĐ4 khác cả ba giai đoạn trước

GĐ2 sợ rò rỉ đặc trưng. GĐ3 sợ áp lực để ML thắng naive. **GĐ4 sợ một thứ tinh vi
hơn: rò rỉ qua bước chuẩn hoá, thứ không báo lỗi mà chỉ làm số liệu tốt lên.**

`docs/giai-thich-chuan-hoa.md` mục 5 nói thẳng: nếu `mu`, `sd` tính trên toàn chuỗi
thay vì cửa sổ train thì *"kết quả sẽ đẹp bất thường và toàn bộ thí nghiệm B mất giá
trị"*, và *"đây là lỗi khó phát hiện vì nó không làm chương trình báo lỗi"*.

**Dấu hiệu nhận biết, ghi sẵn ở đây để không ai quên:** nếu **N0 thô KHÔNG thất bại
nặng** ở cặp Bitbrains ↔ Alibaba thì gần như chắc chắn có rò rỉ. Mục 2.5 dưới đây cho
biết "thất bại nặng" là bao nhiêu — một **hằng số** cũng đạt được MAE 28,24 ở E1→E3,
nên bất kỳ con số N0 nào quanh đó **không nói lên điều gì** về model.

---

## 1. Thước đo là gì

`scripts/reference_gd4.py` — đã chạy 2026-09-11, ra `results/tables/reference_gd4.json`.

**Độc lập ở chỗ nào.** Bản này **chỉ đọc `data/processed/`** và **không import gì từ
`src/cwp/`**. Nó tự dựng lại ranh giới chia tập, luật dòng hợp lệ mục 8, ba phép biến
đổi, phép map ngược và ba baseline — trên ma trận `(số chuỗi, 2304)`, dùng `cumsum` để
kiểm cửa sổ 25 điểm thay vì `rolling`.

**Bằng chứng nó thật sự độc lập mà vẫn đúng:** chín số dòng hợp lệ của chế độ N0 mà nó
tính ra **khớp tuyệt đối** chín neo đã kiểm chéo ở GĐ2 và GĐ3 — dù đường đi khác hẳn.

> **Cảnh báo về tính độc lập, như QĐ-014 điểm 3.** Giữ nguyên giá trị chỉ khi phiên
> viết `src/cwp/preprocess/normalize.py` **không đọc tệp này**. `E1_830` ở GĐ3 là bằng
> chứng sống cho chuyện hai bản cùng sai một kiểu: chúng khớp nhau ở 378/405 ô mà cả
> hai vẫn sai ở 27 ô còn lại.

**Đã chốt 2026-09-11: GĐ4 làm hai phiên tách bạch.** Phiên A viết thước đo, hồ sơ cổng,
phiếu và công cụ kiểm; phiên hiện thực là **phiên khác**, không đọc bốn tệp liệt kê ở
`brief-gd4-b.md` Bước 0. Đây là lần đầu dự án làm được điều QĐ-014 điểm 3 khuyến nghị
mà GĐ3 không làm được.

Kèm một chỗ siết cụ thể: bản mồi `normalize.py` mà loại C cần đã được **tách khỏi
`tests/`** ra `scripts/_moi_normalize_gd4.py`, đúng cách QĐ-014 đề xuất. Ở GĐ3 bản mồi
`metrics.py` nằm ngay trong `tests/test_check_gd3.py` và đó là điểm yếu đã khai báo.

---

## 2. Số liệu tham chiếu

> Mọi số dưới đây **đo được**, không phỏng đoán. Chúng là **đáp án để đối chiếu SAU
> khi chạy**, không phải mục tiêu để code hướng tới.

### 2.1 Ranh giới chia tập — không đổi so với GĐ3

| Tập | Offset so với `b0` | Số bucket |
|---|---|---:|
| train | `[0, 1612)` | 1.612 |
| validation | `[1612, 1957)` | 345 |
| test | `[1957, 2304)` | 347 |

Mọi con số TN-B đo trên **tập test của môi trường ĐÍCH**, cùng luật purge QĐ-013 điểm 2.

### 2.2 Số dòng hợp lệ trên test, theo từng chế độ — khớp **tuyệt đối**

| Env | h | N0 | N1 | N2 |
|---|---:|---:|---:|---:|
| E1 | 1 | 254.310 | 254.310 | 254.310 |
| E1 | 6 | 250.635 | 250.635 | 250.635 |
| E1 | 12 | 246.225 | 246.225 | 246.225 |
| E2 | 1 | 104.492 | 104.492 | 104.492 |
| E2 | 6 | 102.982 | 102.982 | 102.982 |
| E2 | 12 | 101.170 | 101.170 | 101.170 |
| E3 | 1 | 171.716 | 171.716 | **171.711** |
| E3 | 6 | 169.209 | 169.209 | **169.203** |
| E3 | 12 | 166.203 | 166.203 | **166.197** |

Ba điều đọc ra được, và cả ba đều là phép kiểm:

1. **Cột N0 phải khớp tuyệt đối chín neo của GĐ2/GĐ3.** Lệch nghĩa là đường sinh đặc
   trưng đã đổi khi thêm chế độ — dừng truy nguyên, đừng đi tiếp.
2. **N1 bằng đúng N0** ở cả chín ô. z-score là affine và không sinh thêm `NaN` nào khi
   `sd > 0`; cả ba môi trường **không có chuỗi nào `sd = 0`** (mục 2.3).
3. **Chỉ E3 mất dòng ở N2**, và mất rất ít (5–6 dòng). Vì sai phân biến `y_t − y_{t−1}`
   thành `NaN` ở điểm ngay sau một lỗ hổng; E1 và E2 gần như không có lỗ hổng còn lại
   sau nội suy ≤2 của QĐ-008, còn E3 thì có. Bucket 0 của mọi chuỗi cũng thành `NaN`
   nhưng nó vốn đã không hợp lệ vì `max_lag = 24`.

### 2.3 Thống kê chuẩn hoá N1 — QĐ-016 điểm 1

Tính trên **cửa sổ train của chính chuỗi đó**, `[0, 1612)`, `ddof = 1`.

| Env | `mu` trung vị | `sd` trung vị | số chuỗi `sd = 0` |
|---|---:|---:|---:|
| E1 | 2,642263 | 1,326401 | 0 |
| E2 | 2,310990 | 1,497268 | 0 |
| E3 | 40,060336 | 10,989168 | 0 |

Bảng này một mình đã nói được điều RQ3 dựa vào: **`mu` của E3 gấp 15 lần E1/E2, `sd`
gấp 7–8 lần.** Đó chính là thứ N1 sinh ra để bỏ đi.

**`sd = 0` ở 0 chuỗi cả ba môi trường** — nên N1 xác định được ở mọi chuỗi, và bảng kết
quả N1 phải có **đủ** số chuỗi như N0. Nếu bản của B loại chuỗi nào ở N1 thì đã tính
`sd` trên cửa sổ khác.

### 2.4 Ba bất biến — QĐ-016 điểm 5, phép kiểm KHÔNG cần tham chiếu

Đo trên tập test `h = 1`, lệch tuyệt đối lớn nhất trên từng ô:

| Bất biến | E1 | E2 | E3 | Ngưỡng |
|---|---:|---:|---:|---:|
| `naive` N0 ≡ N1 | 2,8e−14 | 2,8e−14 | 1,4e−14 | **< 1e−9** |
| `ma6` N0 ≡ N1 | 4,3e−14 | 4,3e−14 | 4,3e−14 | **< 1e−9** |
| `naive` N0 ≡ N2 (`Δ̂ = 0`) | 0 | 0 | 0 | **= 0** |

Hai cái đầu không bằng 0 tuyệt đối vì `((y−mu)/sd)·sd + mu` không khôi phục `y` từng
bit; `4e−14` là nhiễu dấu phẩy động đúng như mong đợi. Cái thứ ba **bằng 0 tuyệt đối**
vì `y_t + 0` không mất bit nào.

**Đây là phép kiểm giá trị nhất của cổng này**: nó đúng vì *toán học*, không vì hai bản
khớp nhau, nên nó giữ nguyên sức mạnh kể cả khi tính độc lập bằng không. Lệch thì sai ở
đúng một trong ba chỗ mà `giai-thich-chuan-hoa.md` mục 5 liệt kê.

### 2.5 Mốc "hằng số mức tải" — mục 14, và ngưỡng của điều kiện qua cổng

`h = 1`, hằng số = mức tải trung bình trên **cửa sổ train của nguồn**, chấm trên **tập
test của đích**. Không model, không đặc trưng, không huấn luyện.

| Cặp | hằng số | MAE hằng số | naive tại đích | tệ hơn naive |
|---|---:|---:|---:|---:|
| E1→E2 | 13,48 | 11,9459 | 0,4140 | 28,85× |
| E2→E1 | 8,33 | 6,9583 | 0,4077 | 17,07× |
| **E1→E3** | 13,48 | **28,2356** | 4,2955 | 6,57× |
| **E3→E1** | 37,64 | **35,9767** | 0,4077 | **88,24×** |
| E2→E3 | 8,33 | 33,3844 | 4,2955 | 7,77× |
| **E3→E2** | 37,64 | **35,8373** | 0,4140 | **86,56×** |

**Cách dùng bảng này.** `research-plan.md` đặt điều kiện qua cổng GĐ4 là *"N0 phải thất
bại nặng ở cặp Bitbrains và Alibaba"*. Bảng trên định lượng "nặng": nếu N0 thô cho MAE
quanh những con số ở cột thứ ba thì nó **không chứng minh gì cả** — một hằng số cũng
đạt được. Kết luận *"cross-environment generalization thất bại"* khi ấy đúng nhưng rỗng.

> **Hai con số của mục 14 đo trên cơ sở khác.** Mục 14 ghi `26,90` và `4,35`; chúng lấy
> hằng số trên **toàn** cửa sổ và chấm trên **mọi dòng hợp lệ**. Thước đo in ra cả hai
> cơ sở. Trích con số nào cũng được, miễn **nói rõ cơ sở** — xem ghi chú ở mục 14.

---

## 3. Danh sách A kiểm khi B nộp

Chạy theo thứ tự. Trượt mục nào thì dừng.

### 3.1 Sản phẩm có đủ không

- [ ] `src/cwp/preprocess/normalize.py` — ba chế độ, và phép **map ngược** cho từng chế độ
- [ ] `tests/test_normalize.py` — **ba bất biến của mục 2.4 phải có mặt**
- [ ] `data/features/` sinh cho cả ba chế độ theo QĐ-016 điểm 2
- [ ] Ma trận transfer trong `results/tables/` — 6 cặp × 3 chế độ × 3 horizon
- [ ] Bảng biến thể **có / không có 4 đặc trưng lịch** (mục 8 đòi, cho riêng TN-B)
- [ ] `runs/` — mỗi lần chạy một thư mục, kèm snapshot config
- [ ] Log GĐ4 trong `research-log/`

### 3.2 Bước chuẩn hoá — phần nặng nhất của cổng này

- [ ] Ba bất biến ở mục 2.4 đạt ngưỡng
- [ ] Thống kê N1 khớp mục 2.3, và **không chuỗi nào bị loại vì `sd = 0`**
- [ ] Số dòng hợp lệ khớp mục 2.2 — đặc biệt **cột N0 khớp tuyệt đối neo GĐ2/GĐ3**
- [ ] Mọi chỉ số tính **sau khi map ngược về thang CPU% gốc** (mục 14)
- [ ] `mu`, `sd` lấy trên cửa sổ train của **chuỗi đích**, không phải của nguồn, không
      phải toàn chuỗi (QĐ-016 điểm 1)

### 3.3 Rò rỉ — bốn phép kiểm

**T1 — Thống kê chuẩn hoá không nhìn tương lai.** Đổi giá trị `y` của chuỗi đích ở
bucket `≥ 1612` rồi tính lại `mu`, `sd`: **hai con số phải không đổi**. Đây là phép
kiểm mạnh nhất cho QĐ-016 điểm 1, và nó không cần tham chiếu.

**T2 — Không huấn luyện lại trên môi trường đích.** Model chỉ được `fit` trên dữ liệu
môi trường **nguồn**. Kiểm bằng `runs/` và bằng cách đọc code: hàm huấn luyện không
được nhận dữ liệu đích.

**T3 — Test của đích chỉ chạm một lần mỗi tổ hợp.** Như L2 của GĐ3, đếm tự động và ghi
vào `meta.json`. Hơn một lần thì **phải giải thích được**, như B đã làm ở `gate-gd3.md`
mục 5.6.

**T4 — Đặc trưng vẫn là 19 cột.** Ba chế độ đổi **giá trị** của đặc trưng, không đổi
**số lượng** hay tên. Không thêm cột nào để "giúp" transfer.

### 3.4 Điều kiện qua cổng

`research-plan.md`: *"N0 phải thất bại nặng ở cặp Bitbrains và Alibaba. Nếu N0 không
thất bại thì gần như chắc chắn có rò rỉ dữ liệu — dừng lại truy nguyên."*

- [ ] N0 thất bại nặng ở bốn cặp Bitbrains ↔ Alibaba, và mức thất bại **đọc được cạnh
      mốc hằng số** ở mục 2.5
- [ ] N1 và N2 được báo cáo **cả ba** như một ablation, không chọn cái đẹp
- [ ] Trả lời được: **thành phần nào của tín hiệu transfer được** — mức tải, biên độ,
      hay động lực học
- [ ] **Xét điều kiện kích hoạt QĐ-004** ngay khi có bảng đầu tiên: kết luận RQ3 có đảo
      chiều khi bỏ E3 khỏi bảng không? `research-plan.md` GĐ4 dặn làm ngay, không đợi
      lúc viết bài

---

## 4. Lệnh nghiệm thu

```bash
python scripts/check_gd4.py
pytest tests/ -v
```

**Đã có, 2026-09-11.** `scripts/check_gd4.py` chạy ba loại phép kiểm:

| Loại | Gồm |
|---|---|
| **C** — đáp án giải tích | C1 cửa sổ `mu`/`sd`, **C2 đổi `y` sau 1612 thì `mu`/`sd` không đổi**, C3–C5 ba bất biến, C6 chuỗi `sd = 0`, C7 sai phân |
| **A** — so tham chiếu | thống kê N1, ba bất biến trên dữ liệu thật, 27 ma trận đặc trưng |
| **B** — đẳng thức tự thân | B1 N0 khớp neo GĐ2, B2 N1 ≡ N0, B3 N2 làm biến mất dòng đầu của mọi chuỗi, **B11** ma trận N1 khớp `mu`/`sd` đã khai, **B12** 4 đặc trưng lịch giống nhau ở ba chế độ, B4 đủ 108 tổ hợp, B5–B8 bất đẳng thức chỉ số, B9 `n_chuoi + n_loai`, **B10 baseline giống nhau ở ba chế độ** |

`tests/test_check_gd4.py` dựng thế giới giả lập rồi **phá 16 kiểu**, bắt được cả 16,
cộng hai trạng thái phải xanh (thế giới đúng; thế giới đúng có thêm model ngoài bộ bắt
buộc). Chạy được ở trạng thái **B chưa bắt đầu**: báo thiếu, in tiến độ 0/7, không đổ vỡ.

Loại C chạy **kể cả khi B chưa sinh bảng nào** — nó chỉ cần `cwp/preprocess/normalize.py`.
Nên B dùng được ngay từ Bước 1 làm phản hồi tức thì, không phải đợi tới Bước 7.

Hợp đồng tên tệp đầu ra chốt ở `brief-gd4-b.md` Bước 0; hợp đồng **API** của
`normalize.py` ở Bước 1.

---

### B3 đã bị sửa — công cụ kiểm thưởng cho đúng cái lỗi nó định bắt

> Phát hiện 2026-09-11 khi hiện thực Bước 2. **Lần thứ tư công cụ của A sai.**

Bản đầu của B3 đòi *"N2 không mất dòng ở E1/E2"*, giải thích *"mất nghĩa là sai phân
bắc cầu qua ranh giới chuỗi"*. Cả hai vế sai, và sai **ngược chiều**.

**Mọi bản hiện thực đúng đều phải mất dòng.** Gọi `t*` là dòng hợp lệ đầu tiên của một
chuỗi ở N0. N2 đòi thêm `y[t*−25]` và `y[t*+h−1]`. Nếu `y[t*+h−1]` là `NaN` thì `t*`
trượt ngay; nếu nó hữu hạn **và** `y[t*−25]` cũng hữu hạn thì `t*−1` đã có cửa sổ sạch
lẫn target hữu hạn, tức `t*` không phải dòng đầu — mâu thuẫn. Vậy `t*` **luôn** trượt
N2, ở mọi môi trường và mọi horizon.

Bản bắc cầu thì mất **ít hơn**, vì `z` ở đầu chuỗi thứ hai trở đi lấy được giá trị
cuối của chuỗi trước nên không `NaN`. Đo trên dữ liệu thật:

| | bản ĐÚNG mất | bản BẮC CẦU mất | B3 cũ | B3 mới |
|---|---:|---:|---|---|
| E1 | 735 (= số chuỗi) | 26 | đánh trượt bản đúng | phân biệt được |
| E2 | 607 | 306 | đánh trượt bản đúng | phân biệt được |

**Vì sao không dùng ngưỡng đếm.** Cách sửa đầu tiên là đòi `mất ≥ số chuỗi`. Nó bắt
được E1 (26 < 735) nhưng **lọt ở E2**: bản bắc cầu mất 306, vẫn vượt ngưỡng 302. Phép
kiểm chỉ đúng ở một môi trường là phép kiểm chưa đúng.

**Bản chốt kiểm `min(bucket)` của từng chuỗi.** Bản đúng làm dòng đầu của *mọi* chuỗi
biến mất nên `min(bucket)` ở N2 luôn lớn hơn ở N0; bản bắc cầu giữ nguyên dòng đầu từ
chuỗi thứ hai trở đi nên hai giá trị bằng nhau — lộ ra bất kể môi trường có bao nhiêu
lỗ hổng. Đo trên sản phẩm thật: **0/735, 0/302, 0/498 chuỗi vi phạm.**

`tests/test_check_gd4.py` phải sửa theo: thế giới giả lập bản đầu cho E1/E2 mất 0 dòng
ở N2, tức **mã hoá sẵn đúng cái lỗi**. Nay ma trận giả lập mang `series_id` và `bucket`
thật, ca phá mô phỏng bắc cầu bằng `_ma_tran(..., bac_cau=True)`, và có thêm một ca
xanh khẳng định *"mất đúng một dòng mỗi chuỗi vẫn ĐẠT"*. Tổng **17 kiểu phá, 19 test**.

---

### B11 và B12 — hai lỗ hổng `pha_gd4.py` tìm ra trên dữ liệu thật

> Thêm 2026-09-11, cùng đợt với bản sửa B3.

Chạy tám bản phá trên dữ liệu thật (`scripts/pha_gd4.py`) làm lộ ra **hai lỗi lọt qua
toàn bộ cổng**, và cả hai cùng một dạng thiếu sót: **không phép kiểm nào nối hai sản
phẩm của B lại với nhau.**

**Q1 — `mu`/`sd` tính trên toàn chuỗi.** Đây là rò rỉ mà QĐ-016 điểm 1 gọi thẳng là
*"chỗ dễ sai nhất"*. Nó lọt vì: z-score không đổi số dòng nào nên B1/B2 không thấy;
C1/C2 kiểm thẳng hàm `thong_ke_train` chứ không kiểm ma trận; và `normalize_gd4.csv`
do một đường code khác sinh ra nên nó **vẫn đúng**.

→ **B11** nối hai thứ đó: `lag_1` ở N0 là `y[t−1]`, ở N1 là `(y[t−1] − mu)/sd`. Quan
hệ `y = sd·z + mu` là affine và thừa xác định, nên giải ngược ra `mu`, `sd` từng chuỗi
rồi so với bảng đã khai. Ngưỡng **1e−10** chọn theo số đo — sai số giải ngược trên sản
phẩm đúng là 6,0e−13 / 3,9e−13 / 3,9e−14, nên ngưỡng nằm trên nhiễu ~100 lần mà vẫn
dưới 1e−8 ~100 lần, đủ bắt cả trò cộng epsilon vào `sd`.

**Q5 — chuẩn hoá luôn 4 đặc trưng lịch.** Lọt vì số dòng không đổi và `lag_1` không
đổi, nên B11 cũng không thấy.

→ **B12** dùng đúng điều QĐ-016 điểm 2 nói: bốn đặc trưng lịch chỉ suy từ `bucket`,
nên với cùng `(series_id, bucket)` chúng phải bằng nhau **tuyệt đối** ở N0, N1, N2.

Sau khi thêm hai phép kiểm: **8/8 bản phá bị bắt**, và `tests/test_check_gd4.py` lên
**21 test** với hai ca phá mới.

---

## 5. Kết quả cổng

Điền khi nghiệm thu.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 3.1 Sản phẩm | | |
| 3.2 Bước chuẩn hoá | | |
| 3.3 Rò rỉ T1–T4 | | |
| 3.4 Điều kiện qua cổng | | |

**Kết luận:**
**Ngày duyệt:**

---

## Phụ lục — vì sao cổng này neo vào bất biến chứ không neo vào kết quả transfer

Kết quả transfer phụ thuộc model, mà model thì phụ thuộc seed, siêu tham số và phiên
bản thư viện — không neo được, cùng lý do đã ghi ở phụ lục `gate-gd3.md`.

Nhưng GĐ4 có một thứ mà GĐ3 không có: **ba đẳng thức đúng vì toán học.** `naive` bất
biến dưới z-score, `ma6` cũng vậy, và `naive` dưới sai phân với `Δ̂ = 0` quay về đúng
persistence. Ba đẳng thức ấy không quan tâm ai viết code, chạy trên máy nào, hay thư
viện bản mấy — chúng chỉ sai khi bước chuẩn hoá sai.

Và bước chuẩn hoá **chính là** chỗ `research-plan.md` gọi là *"dễ sai nhất toàn dự
án"*. Nên cổng này dồn trọng lượng vào đó: ba bất biến ở mục 2.4, cộng T1 ở mục 3.3.
Cả bốn đều chạy được **trước khi huấn luyện một model nào** — tức bắt lỗi ở chỗ rẻ
nhất, trước khi tiêu 5,9 giờ máy.
