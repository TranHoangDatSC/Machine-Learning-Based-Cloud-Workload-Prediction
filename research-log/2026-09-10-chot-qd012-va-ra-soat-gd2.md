# 2026-09-10 — Chốt QĐ-012, rà soát GĐ2, kiểm sẵn sàng GĐ3

**Người thực hiện:** B (agent), theo quyết định của A
**Giai đoạn:** GĐ2 đóng lại, chuẩn bị GĐ3
**Thời lượng:** ~1,5 giờ

## Mục tiêu phiên

A duyệt V1 và giao xử lý V2–V4. Rà lại toàn bộ GĐ2 tìm chỗ hỏng, sửa nếu nhỏ, báo
nếu lớn. Kiểm xem còn thiếu gì trước khi vào GĐ3.

## Đã làm

- Chốt **QĐ-012** gom cả bốn việc treo, cộng hai thứ tìm được khi rà.
- Rà máy toàn bộ GĐ2: **mọi con số nhất quán**, không chỗ nào lệch.
- Tìm và sửa **hai lỗi thật**, một trong đó nằm ở mục biện minh cho đóng góp chính.
- Kiểm sẵn sàng GĐ3: tìm được một khoảng trống trong sản phẩm GĐ2 — đo ra thì nhỏ.

## QĐ-012 — bốn việc treo

| | Quyết định | Ghi vào |
|---|---|---|
| **V1** | Phân tầng theo **phân vị CV trong từng môi trường**, không dùng ngưỡng tuyệt đối chung | protocol mục 13, `config/split.yaml` |
| **V2** | Chặn `CV ≤ √((100−m)/m)` thành **Giới hạn số 9** của data card | `data-card.md` |
| **V3** | E1/E2 không có chu kỳ ngày — dự báo cho GĐ4 ghi cạnh chỗ QĐ-010 chốt hai biến thể | protocol mục 8 |
| **V4** | Nhịp một giờ thuộc phần **Dữ liệu** của paper | `data-card.md` |

### Một chỗ rò rỉ chưa xảy ra, chốt luôn cho khỏi quên

`cv_gd2.csv` tính CV trên **toàn bộ cửa sổ 8 ngày**, tức nó biết cả validation và
test. Dùng để **nhóm chuỗi khi đọc bảng** thì vô hại — đó là một cách sắp xếp kết quả,
không phải đầu vào của model.

Nhưng nếu GĐ3 hay GĐ4 dùng CV làm **đặc trưng**, làm **trọng số huấn luyện**, hay làm
**tiêu chí chọn model theo tầng**, thì con số hiện tại là rò rỉ. Khi ấy bắt buộc tính
lại CV **chỉ trên cửa sổ train** của từng chuỗi — đúng nguyên tắc đã áp cho thống kê
chuẩn hoá N1 ở mục 14. Đã ghi thành một đoạn riêng trong protocol mục 13 và một khoá
`chi_dung_de_bao_cao: true` trong `config/split.yaml`.

## Hai lỗi tìm được khi rà

### Lỗi 1 — protocol mục 14 trích số đo trên quần thể đã biến mất

Mục 14 là chỗ biện minh cho **đóng góp chính của paper**. Nó viết *"Đã đo trên dữ liệu
thật (833 chuỗi E3 sau lọc)"* — nhưng quần thể nghiên cứu chỉ có **498 chuỗi**. Con số
833 có từ trước khi QĐ-009 đóng băng mẫu 500 máy.

Cùng loại lỗi mà QĐ-011 đã dọn một lượt, sót lại một chỗ. Đo lại trên
`data/features/E3_h1.parquet`, MAE trung vị theo chuỗi:

| Phép đo | 833 chuỗi (cũ) | **498 chuỗi (nay)** |
|---|---:|---:|
| (a) hằng số bằng mức tải trung bình E1 | 28,64 | **26,90** |
| (b) hằng số bằng mức tải trung bình E3 | 10,48 | **10,06** |
| (c) naive persistence trong E3 | 5,76 | **4,35** |
| Phần sai số chỉ là chênh mức tải | 63,4% | **62,6%** |
| Naive tốt hơn "kết quả transfer" | 5× | **6,2×** |

**Lập luận không đổi, và mạnh hơn.** Một hằng số vẫn đạt MAE ≈ 27; gần hai phần ba sai
số vẫn chỉ là chênh mức tải; và naive nay tốt hơn 6,2 lần chứ không phải 5. Vì kết
luận không đảo chiều nên sửa số tại chỗ theo khuôn QĐ-011: giữ cột cũ để đối chiếu,
thêm cột mới, ghi ngày và lý do. Sửa ở `protocol.md` mục 14 và
`giai-thich-chuan-hoa.md`.

### Lỗi 2 — ba docstring script chỉ tới tệp không còn tồn tại

Sau đợt đổi cấu trúc hình hôm qua, cả ba `scripts/fig_*.py` vẫn ghi ở dòng đầu rằng
chúng sinh `results/figures/fig_*.{png,pdf}`. Đó là thứ đầu tiên người đọc thấy, và nó
dẫn tới đường dẫn đã bị xoá. Đã sửa cả ba, cộng bốn chỗ tương tự trong log GĐ2.

## Rà máy toàn bộ GĐ2 — nhất quán

Viết script tính lại và so, không đọc suông:

| Nhóm | Kết quả |
|---|---|
| 9 neo số dòng ma trận đặc trưng vs `catalog.parquet` | khớp |
| 30 chỉ số ACF + tỉ lệ cặp bỏ vs `reference_gd2.json` | khớp |
| 12 chỉ số CV vs `reference_gd2.json` | khớp |
| 9 ngưỡng tam phân vị / Spearman / CV-chạm-chặn trong QĐ-012 | khớp |
| 5 con số mới của mục 14 | khớp |
| Sản phẩm: 9 parquet, 11 `.png`, 3 PDF, 3 CSV | đủ |
| Câu chết trong `docs/` ngoài khối đính chính | không còn |

`check_gd1.py` **ĐẠT**, `check_gd2.py` **ĐẠT** 12/12, `pytest tests/` **148 passed,
1 skipped**.

## Sẵn sàng GĐ3

### Khoảng trống tìm được: seasonal naive không tính được từ `data/features/`

protocol mục 11 đòi ba baseline. Hai cái đầu lấy thẳng từ ma trận đặc trưng
(`y_t = lag_1 + diff_1`, và `roll_mean_6`). Cái thứ ba, `ŷ = y_{t-288}`, **không có**:
bộ 19 đặc trưng sâu nhất chỉ tới `lag_24`.

Ban đầu tưởng là chuyện lớn — nếu phải siết luật dòng hợp lệ thành `t ≥ b0 + 288` thì
cả chín neo đã kiểm chéo sẽ đổi. Đo ra thì **không cần**:

| Tỉ lệ dòng có sẵn `y_{t-288}` | train | val | **test** |
|---|---:|---:|---:|
| E1 | 83,03% | 100,00% | **100,00%** |
| E2 | 82,59% | 99,99% | **100,00%** |
| E3 | 81,37% | 99,98% | **99,57%** |

Phần thiếu nằm gần như trọn trong **train**, vì 288 bucket đầu của mỗi chuỗi rơi vào
12,5% đầu cửa sổ. Trên **test** — nơi mọi con số của paper được tính — seasonal naive
xác định được ở gần như toàn bộ dòng. Và không model nào cần `lag_288`, chỉ baseline
này cần, mà baseline thì không huấn luyện.

Đã ghi thành mục con ở protocol mục 11: nối ngược về `data/processed/` theo
`(series_id, bucket − 288)`; **không** thêm `lag_288` vào bộ đặc trưng; **không** siết
luật dòng hợp lệ; và **728 dòng test của E3** (0,43%) không có giá trị thì phải xử lý
hiện chứ không lặng lẽ.

### Còn thiếu, và đó là việc của A

Theo đúng khuôn đã dùng ở GĐ1 và GĐ2, B không nên bắt đầu khi chưa có thước đo độc
lập:

- `research-log/gate-gd3.md` — chưa có
- `research-log/brief-gd3-b.md` — chưa có
- `scripts/reference_gd3.py` — chưa có
- `config/models/` — rỗng, chưa có siêu tham số cho 5 model

Đầu vào thì đã đủ: 9 ma trận đặc trưng, `cv_gd2.csv` cho phân tầng, `config/split.yaml`
đã khai đủ tỉ lệ chia, rolling-origin 5 fold, ba horizon, ba chế độ chuẩn hoá và khối
`stratify` mới.

## Việc tiếp theo

- [ ] A duyệt hình phân phối bằng mắt — **vẫn là điều kiện qua cổng GĐ2**
- [ ] A dựng `gate-gd3.md`, `reference_gd3.py`, `brief-gd3-b.md`
- [ ] GĐ3 đọc `stratify` từ `config/split.yaml` chứ không hardcode ngưỡng

## File sửa

- `docs/decisions.md` — thêm **QĐ-012**
- `docs/protocol.md` — mục 8 (V3), mục 11 (seasonal naive), mục 13 (phân tầng CV),
  mục 14 (sửa bốn con số)
- `docs/data-card.md` — Giới hạn số 9 (chặn CV), nhịp một giờ vào mục cấu trúc thời gian
- `docs/giai-thich-chuan-hoa.md` — bảng hai cột 833 / 498 chuỗi
- `config/split.yaml` — khối `stratify`
- `scripts/fig_{target_dist,acf,burstiness}.py` — sửa docstring chỉ sai đường dẫn
- `research-log/2026-09-09-gd2-dac-trung.md` — đóng V1–V4, sửa 4 đường dẫn

---

## Kiểm định tính đúng của 11 hình — 2026-09-10, A yêu cầu

A duyệt hình bằng mắt thấy ổn nhưng không tự kiểm được phần toán (ECDF, ACF, PACF,
chặn CV vượt quá môn ML cơ bản). Vấn đề thật: **khớp với bản của A chỉ chứng minh hai
bên đồng ý, chưa chứng minh cả hai đúng** — nếu cùng hiểu sai một định nghĩa thì vẫn
khớp nhau. Nên kiểm bằng **dữ liệu có đáp án giải tích biết trước**.

### 1. ACF và PACF trên chuỗi AR có nghiệm đóng

Sinh AR(1) `y_t = φ·y_{t-1} + e`, n = 200.000. ACF lý thuyết là `φ^k`; PACF bằng `φ`
tại bậc 1 và **bằng 0** từ bậc 2.

| φ | lệch ACF lớn nhất (lag 1–6) | PACF bậc 1 lệch | max \|PACF\| bậc ≥ 2 |
|---:|---:|---:|---:|
| +0,8 | 0,0045 | 0,0014 | 0,0024 |
| +0,5 | 0,0049 | 0,0039 | 0,0039 |
| −0,6 | 0,0031 | 0,0006 | 0,0026 |

AR(2) với `φ₁ = 0,6`, `φ₂ = −0,3`: PACF đo được `[+0,4606, −0,3039, ≈0, …]` so với lý
thuyết `[+0,4615, −0,3000, 0, …]` — **cắt đúng sau bậc 2**. Đệ quy Durbin–Levinson tự
viết cho kết quả đúng.

### 2. Định nghĩa ACF có phải định nghĩa chuẩn không

Bản hiện thực dùng **tương quan Pearson của từng cặp** (hai trung bình, hai độ lệch
chuẩn riêng). Sách giáo khoa và `statsmodels.acf` dùng dạng **một trung bình chung,
mẫu số là tổng phương sai toàn chuỗi**. Hai dạng khác nhau về nguyên tắc, nên phải đo:

| | lag 1 | lag 6 | lag 12 | lag 24 |
|---|---:|---:|---:|---:|
| Lệch giữa hai định nghĩa, trên 710 chuỗi E1 không NaN | 0,0011 | 0,0022 | 0,0013 | 0,0034 |

Lệch ≤ 0,0034. **Không phải vấn đề** — người đọc tính lại bằng `statsmodels` sẽ ra
gần như cùng số.

### 3. Cách xử lý NaN có thật sự cứu được ACF không

Đây là lý do tồn tại của cả cách làm, nên phải đo chứ không tin. AR(1) `φ = 0,8`, đục
lỗ theo cụm 5–20 điểm cho tới 13,2% thiếu — giống dạng thiếu của E3:

| | lệch lớn nhất so với `φ^k` |
|---|---:|
| Theo cặp `(t, t+k)` — cách đang dùng | **0,0038** |
| `dropna()` rồi mới tính — cách sai | 0,0132 |

Cách theo cặp giữ được đáp án đúng; `dropna` lệch gấp 3,5 lần. **Thiết kế đúng.**

### 4. Hình có vẽ đúng dữ liệu nó khai không

Đọc ngược toạ độ từ đối tượng `Line2D` và `PathCollection` rồi so với CSV nguồn:

| Hình | Kiểm | Kết quả |
|---|---|---|
| 04, 05, 06, 07 | ba đường khớp đúng cột `acf_p50` / `pacf_p50` / `bo_cap_pct`, lag 1..48 và 1..300 | khớp |
| 08 | ECDF vẽ đúng CV đã sắp xếp, trục tung `i/n` | khớp |
| 09 | mỗi chấm là `(mean, cv)` đúng của từng chuỗi; đường đứt nét đúng `√((100−m)/m)` | khớp |
| 10 | thanh đậm p25–p75, vạch mảnh p5–p95, tính lại từ `cv_gd2.csv` | khớp |
| 01, 02 | `F(x)` không giảm, `F(100) = 1`; cắt 0,5 ra đúng `p50`; bước nhảy tại 100 bằng đúng `pct_bang_100` | khớp |

ECDF còn được kiểm bằng một mảng 7 phần tử tính tay được: `F` ra đúng
`[0, 2/7, 3/7, 3/7, 6/7, 1, 1]`.

### 5. Chặn CV — chứng minh và kiểm số

`Var ≤ m(100−m)` với biến trong `[0, 100]`, cực đại đạt bởi phân phối hai điểm ở 0 và
100 với trọng số `(1−m/100, m/100)`. Dựng đúng phân phối đó cho `m = 2 / 40 / 90`:
phương sai ra đúng `m(100−m)` (lệch tương đối < 1e-3). Trên dữ liệu: **0/1.535 chuỗi
vượt chặn**.

## Lỗi tìm được: chiều thiên lệch của `dropna` bị ghi **ngược**

Tài liệu viết *"lag 1 sau khi dropna có thể là hai điểm cách nhau 2 giờ thật, và ACF
đo được sẽ **cao giả tạo**"*. Đo ra thì ngược lại — nó **thấp** đi.

Cơ chế đúng: sau khi nén, cái được dán nhãn "lag k" thực ra trộn cả những cặp cách
nhau **nhiều hơn** k bước thật. Mà ACF **giảm** theo lag, nên số đo bị kéo **xuống**.

Đo trên chính E3 (thiếu 9,29%), ACF trung vị theo chuỗi:

| lag | theo cặp | dropna | chênh |
|---:|---:|---:|---:|
| 1 | 0,8634 | 0,8298 | **−0,0336** |
| 6 | 0,6944 | 0,6154 | −0,0790 |
| 12 | 0,6287 | 0,5229 | **−0,1057** |
| 24 | 0,4952 | 0,3897 | −0,1055 |

**Không con số nào trong dự án sai** — chỉ một câu giải thích sai chiều. Đã sửa ở hai
chỗ trong `scripts/fig_acf.py` (docstring và trang diễn giải của PDF), và sinh lại
`gd2_acf-pacf.pdf`. `gate-gd2.md` và `reference_gd2.py` chỉ nói "co trục thời gian"
mà không nêu chiều nên đúng, giữ nguyên.

### Nhân tiện kiểm luôn chiều của ffill — QĐ-008 ghi ĐÚNG

Cùng họ với lỗi trên nhưng ngược cơ chế, nên phải kiểm riêng. AR(1) `φ = 0,7`, thiếu
13,4%: sau `ffill`, ACF lag 1 **tăng** +0,0316 và lag 6 tăng +0,0782 so với lý thuyết.
Đoạn phẳng do ffill tạo ra tương quan hoàn hảo với chính nó, nên nó **thổi ACF lên** —
đúng như QĐ-008 và protocol mục 6 đã viết.

## Một chỗ đỏ hoá ra không phải lỗi

Phép kiểm `ti_le_cham_chan` báo đỏ. Truy ra: `cv_gd2.csv` ghi bằng `.round(6)` nên
`cv` và `mean` đều đã làm tròn, tính lại từ chúng không thể trùng tuyệt đối. Lệch lớn
nhất **9,9e-7**, dưới đúng mức làm tròn 1e-6, và **0/1.535 dòng** lệch quá 1e-6. Không
phải lỗi logic.
