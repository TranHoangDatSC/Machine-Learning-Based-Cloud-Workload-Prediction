# Hồ sơ cổng GĐ3

**Người giữ cổng:** A
**Trạng thái:** **MỞ — B vào làm được ngay.** Thước đo `scripts/reference_gd3.py` đã
chạy, năm quy ước đã chốt ở QĐ-013. Phiếu giao việc: `research-log/brief-gd3-b.md`.
**Cập nhật:** 2026-09-10
**Giai đoạn:** Thí nghiệm A — trong cùng môi trường (`docs/research-plan.md` GĐ3)

Cùng khuôn với `gate-gd1.md` và `gate-gd2.md`: thước đo độc lập, ngưỡng ghi trước,
lệnh nghiệm thu tự động.

---

## 0. Ba bài học mang sang

1. **Thước đo là bản hiện thực độc lập của A.** GĐ1 khớp 0,000% trên 47/48 chỉ số;
   GĐ2 khớp trên 114 vân tay đặc trưng, 30 chỉ số ACF, 12 chỉ số CV. Cơ chế này đã
   bắt được **mọi** lỗi của dự án. **Đừng đưa `reference_gd3.py` cho agent đang viết
   `src/cwp/models/` hay `src/cwp/evaluation/` đọc.**
2. **Công cụ kiểm phải có test của chính nó.** `check_gd1.py` và `check_gd2.py` đều
   có test dựng thế giới giả lập rồi phá. `check_gd3.py` phải có tương đương.
3. **Rào chắn "đừng code hướng về con số"** vào mọi prompt. Ở GĐ3 nó còn quan trọng
   hơn GĐ2, vì lần này có một áp lực mới: **áp lực để ML thắng naive**.

### Cái khác biệt của cổng GĐ3

Hai giai đoạn trước kiểm **sản phẩm tất định**: cùng dữ liệu, cùng quy ước thì phải ra
cùng con số. GĐ3 không có tính chất đó cho phần model — kết quả phụ thuộc siêu tham
số, seed, phiên bản thư viện.

Nên cổng này neo vào hai thứ **vẫn tất định**:

- **Ba baseline** ở protocol mục 11. Không seed, không siêu tham số, không huấn
  luyện. Lệch một chữ số là có lỗi, không phải nhiễu.
- **Bộ máy đánh giá**: ranh giới chia tập, số dòng mỗi tập, mẫu số MASE, cách gộp.

Neo được cái **đo**, không neo được cái **học**. Nhưng nếu cái đo đúng thì con số của
model đọc được; còn nếu baseline sai thì mọi so sánh về sau đều vô nghĩa, vì
`research-plan.md` viết *"Chạy baseline trước tiên. Mọi con số về sau so với nó."*

---

## 1. Thước đo là gì

`scripts/reference_gd3.py` — đã chạy 2026-09-10, ra
`results/tables/reference_gd3.json`.

**Độc lập ở chỗ nào.** Bản này **chỉ đọc `data/processed/`**, không đụng tới
`data/features/`. Nó tự dựng lại luật dòng hợp lệ của mục 8, tự tính `y_t`,
`roll_mean_6`, `y_{t-288}` từ `y` thô, và nạp mỗi môi trường thành một ma trận
`(số chuỗi, 2304)` thay vì `groupby` trên bảng dài.

Hệ quả: nếu B tính baseline **từ `data/features/`** mà ra cùng số, phép so đó kiểm
chéo được **cả ma trận đặc trưng lẫn code baseline** cùng lúc.

> **Cảnh báo về tính độc lập của lần này.** `reference_gd3.py` do cùng một agent đã
> viết code B của GĐ2 soạn ra, ngày 2026-09-10, **trước khi có bất kỳ dòng code GĐ3
> nào**. Tính độc lập chỉ còn nguyên nếu phiên hiện thực GĐ3 **không đọc tệp này**.
> Tốt nhất là một phiên khác làm. Nếu buộc phải cùng phiên thì ghi rõ trong log rằng
> tính độc lập đã yếu, và tăng trọng số cho các phép kiểm không dựa vào so sánh hai
> bản — mục 3.4 dưới đây.

---

## 2. Số liệu tham chiếu

> Mọi số dưới đây **đo được**, không phỏng đoán. Chúng là **đáp án để đối chiếu SAU
> khi chạy**, không phải mục tiêu để code hướng tới.

### 2.1 Ranh giới chia tập — QĐ-013 điểm 1

Theo **bucket**, không theo số dòng. Giống hệt nhau ở cả ba môi trường:

| Tập | Offset so với `b0` | Số bucket |
|---|---|---:|
| train | `[0, 1612)` | 1.612 |
| validation | `[1612, 1957)` | 345 |
| test | `[1957, 2304)` | 347 |

### 2.2 Số dòng mỗi tập — khớp **tuyệt đối**

| Env | h | train | validation | test |
|---|---:|---:|---:|---:|
| E1 | 1 | 1.142.276 | 252.840 | 254.310 |
| E1 | 6 | 1.138.601 | 249.165 | 250.635 |
| E1 | 12 | 1.134.191 | 244.755 | 246.225 |
| E2 | 1 | 469.502 | 103.888 | 104.492 |
| E2 | 6 | 466.681 | 102.378 | 102.982 |
| E2 | 12 | 464.338 | 100.566 | 101.170 |
| E3 | 1 | 596.549 | 169.675 | 171.716 |
| E3 | 6 | 584.598 | 167.127 | 169.209 |
| E3 | 12 | 575.245 | 164.102 | 166.203 |

**Phép kiểm tự thân, làm được ngay bằng đầu:** tổng ba tập phải **nhỏ hơn** tổng dòng
hợp lệ của GĐ2 đúng `số_chuỗi × 2 × h` — số dòng bị purge vì vắt qua hai ranh giới.
E1 h=12: `1.642.811 − (1.134.191 + 244.755 + 246.225) = 17.640 = 735 × 2 × 12`. ✔

Lệch nhiều hơn thì nghi **quên purge** — và quên purge là **rò rỉ**, không phải sai
sót đếm.

### 2.3 Ba baseline — MAE trung vị trên test

Đây là neo quan trọng nhất của cổng.

| Env | h | naive | moving avg 6 | seasonal naive |
|---|---:|---:|---:|---:|
| E1 | 1 | **0,4077** | 0,4007 | 0,5834 |
| E1 | 6 | **0,4661** | 0,4263 | 0,6005 |
| E1 | 12 | **0,4494** | 0,4558 | 0,5818 |
| E2 | 1 | **0,4140** | 0,4100 | 0,5997 |
| E2 | 6 | **0,4808** | 0,4466 | 0,7207 |
| E2 | 12 | **0,4649** | 0,4633 | 0,6644 |
| E3 | 1 | **4,2955** | 5,0658 | 7,3528 |
| E3 | 6 | **6,5087** | 5,9087 | 7,7643 |
| E3 | 12 | **7,0270** | 6,8214 | 7,8778 |

`reference_gd3.json` còn chứa RMSE, SMAPE, MASE, R² cho cả ba baseline × ba horizon,
mỗi cái kèm p25/p50/p75/IQR và số chuỗi bị loại.

### 2.4 MASE — mẫu số và giá trị của naive

| Env | mẫu số MASE (trung vị) | MASE naive h=1 | h=6 | h=12 | chuỗi bị loại |
|---|---:|---:|---:|---:|---:|
| E1 | 0,3487 | 0,9683 | 1,3658 | 1,3997 | 0 |
| E2 | 0,3352 | 1,0366 | 1,3739 | 1,4400 | 0 |
| E3 | 4,4235 | 0,9643 | 1,4844 | 1,6167 | 0 |

**MASE của naive ở h=1 xấp xỉ 1 là dấu hiệu đúng** — mẫu số chính là MAE của naive
một bước trên train, nên tỉ số gần 1 nghĩa là test khó ngang train. Lệch xa khỏi 1
thì nghi mẫu số tính sai tập hoặc sai horizon.

### 2.5 Tầng burstiness — QĐ-012

| Env | ngưỡng thấp/vừa | ngưỡng vừa/cao | số chuỗi mỗi tầng |
|---|---:|---:|---|
| E1 | 0,256049 | 0,848935 | 245 / 245 / 245 |
| E2 | 0,285320 | 0,943359 | 101 / 100 / 101 |
| E3 | 0,258254 | 0,320560 | 166 / 166 / 166 |

### 2.6 Dòng bị bỏ của seasonal naive

protocol mục 11 đòi xử lý **hiện** chứ không lặng lẽ:

| Env | h=1 | h=6 | h=12 |
|---|---:|---:|---:|
| E1, E2 | 0,0000% | 0,0000% | 0,0000% |
| **E3** | **0,4251%** | **0,4285%** | **0,4326%** |

`naive` và `ma6` bỏ **0%** ở cả ba môi trường. Nếu bản của B bỏ khác con số này thì
hoặc nó dùng luật dòng hợp lệ khác, hoặc nó lặng lẽ lấp giá trị thiếu.

---

## 3. Danh sách A kiểm khi B nộp

Chạy theo thứ tự. Trượt mục nào thì dừng.

### 3.1 Sản phẩm có đủ không

- [ ] `src/cwp/models/baselines.py` — ba baseline của mục 11
- [ ] `src/cwp/evaluation/metrics.py` — MAE, RMSE, SMAPE, MASE, R² theo QĐ-013
- [ ] `src/cwp/evaluation/splits.py` — chia theo bucket, purge dòng vắt ranh giới,
      rolling-origin 5 fold
- [ ] `tests/` — test cho cả ba module trên, và test **biết đỏ** (phá code kiểm ngược)
- [ ] `runs/` — mỗi lần chạy một thư mục, kèm snapshot config
- [ ] `results/tables/` — bảng kết quả, có cả bản gộp và bản tách theo tầng burstiness
- [ ] Log GĐ3 trong `research-log/`

### 3.2 Bộ máy đánh giá khớp neo — khớp **tuyệt đối**

- [ ] 27 con số ở mục 2.2 (3 env × 3 h × 3 tập)
- [ ] Tổng ba tập nhỏ hơn tổng dòng hợp lệ đúng `n_chuỗi × 2 × h`
- [ ] 9 mẫu số MASE và 9 giá trị MASE của naive ở mục 2.4
- [ ] Ngưỡng và số chuỗi mỗi tầng ở mục 2.5
- [ ] Tỉ lệ dòng bỏ của seasonal naive ở mục 2.6

### 3.3 Ba baseline khớp neo — khớp **tuyệt đối**

- [ ] 27 con số MAE ở mục 2.3
- [ ] RMSE, SMAPE, MASE, R² khớp `reference_gd3.json`
- [ ] Gộp bằng **trung vị theo chuỗi** kèm IQR, không phải trung bình, không phải
      gộp mọi dòng vào một dãy (QĐ-013 điểm 5)

### 3.4 Rò rỉ — phần nặng nhất của cổng này

Ba phép kiểm dưới đây **không dựa vào so sánh hai bản**, nên chúng vẫn có giá trị kể
cả khi tính độc lập bị yếu.

**L1 — Không dòng train nào có target rơi vào val hoặc test.** Kiểm trực tiếp trên
tập chỉ số: với mọi dòng train, `t + h < 1612`. Đây là điều purge ở QĐ-013 điểm 2
bảo đảm; nếu B gán tập theo `t` mà quên `t+h` thì phép kiểm này đỏ.

**L2 — Test chỉ chạm một lần.** protocol mục 9: *"Test chỉ chạm vào một lần duy nhất,
khi đã chốt toàn bộ mô hình."* Kiểm bằng log và bằng `runs/`: mọi lần chọn siêu tham
số phải đọc **validation**. Hỏi B thẳng: đã chạy test bao nhiêu lần, và nếu hơn một
lần thì vì sao.

**L3 — Rolling-origin không nhìn tương lai.** 5 fold trên train + validation, mỗi
fold train phải **kết thúc trước** khi fold val bắt đầu, và cũng phải purge `h` dòng
ở mối nối. Kiểm bằng cách in ra biên của 5 fold rồi đọc.

**L4 — Đặc trưng vẫn là 19 cột của mục 8.** Không thêm `lag_288`, không thêm CV,
không thêm gì. `check_gd2.py` đã ghim schema; GĐ3 không được nới ra.

### 3.5 Điều kiện qua cổng — và một áp lực mới

`research-plan.md`: *"trả lời được 'ML có vượt naive không, ở horizon nào' kèm kiểm
định thống kê. Nếu ML không vượt ở `h=1` thì **đó là finding**, ghi lại và đi tiếp,
không được ép model."*

- [ ] Có bảng so mọi model với naive, ba môi trường × ba horizon
- [ ] Có kiểm định Wilcoxon cho chênh lệch giữa các model (mục 15)
- [ ] **Nếu ML thua naive ở đâu đó, điều đó được BÁO CÁO, không bị giấu**

> **Cái bẫy của GĐ3 khác cái bẫy của GĐ2.** GĐ2 sợ rò rỉ đặc trưng. GĐ3 sợ **áp lực
> để có kết quả đẹp**. Nhìn bảng ở mục 2.3 thì thấy ngay: ở h=1, naive cho MAE 0,4077
> trên E1 và 4,2955 trên E3. Đó là những con số **rất khó vượt** — persistence trên
> lưới 5 phút là một baseline mạnh.
>
> Nếu một model ML bỗng cho MAE thấp hơn hẳn ở h=1, phản xạ đầu tiên phải là **nghi
> rò rỉ**, không phải mừng. `docs/protocol.md` mục 17 đã cam kết: *"Không giấu việc
> baseline naive thắng model ML, nếu điều đó xảy ra."*

---

## 4. Lệnh nghiệm thu

```bash
python scripts/check_gd3.py
pytest tests/ -v
```

`check_gd3.py` đọc hai bảng theo **hợp đồng tên tệp và tên cột ở QĐ-014 điểm 4**:

| Tệp | Cột |
|---|---|
| `results/tables/splits_gd3.csv` | `env, h, split, n_dong` |
| `results/tables/baselines_gd3.csv` | `env, h, model, split, metric, p25, p50, p75, iqr, n_chuoi, n_loai, n_dong_dung, n_dong_test` |

Sai tên tệp hay tên cột thì công cụ không chạy được — B đọc mục này trước khi ghi.
Tham chiếu của A **chỉ neo `split = test`** (mục 12 báo cáo trên test), nên B được
phép báo thêm dòng `train`/`val` để tự theo dõi; công cụ lọc trước khi so.

Nó chạy **ba loại phép kiểm**, và ba loại này không thay thế nhau được:

| Loại | Phụ thuộc tính độc lập? | Bắt được gì |
|---|---|---|
| **A** — so với `reference_gd3.json` | **có** | lỗi gõ, lệch một dòng, dùng sai cột |
| **B** — đẳng thức tự thân (B1–B7) | **không** | vi phạm quan hệ mà mọi bản đúng đều phải thoả |
| **C** — đáp án giải tích (C1–C10) | **không** | **hiểu sai định nghĩa** |

Vì sao phải có cả ba: ở GĐ3 `reference_gd3.py` do cùng agent đã viết code GĐ2 soạn ra
(QĐ-014 điểm 3), nên "hai bản khớp nhau" là bằng chứng **yếu hơn** GĐ1/GĐ2 — hai bản
có thể cùng sai một kiểu. Loại B và C giữ nguyên giá trị kể cả khi tính độc lập bằng
không, nên **đừng bỏ chúng đi cho gọn**.

Kèm theo, đúng bài học số 2: **`tests/test_check_gd3.py`** dựng thế giới giả lập
(3 môi trường × 3 chuỗi × 2304 bucket, NaN đặt có chủ đích) rồi phá chín kiểu và xác
nhận công cụ bắt được từng kiểu:

| Kiểu phá | Phép kiểm phải đỏ |
|---|---|
| gán tập theo `t`, quên `t+h` | B1 + loại A số dòng |
| mẫu số MASE tính trên test | loại A, cột `mase` |
| gộp bằng trung bình thay vì trung vị | loại A, 45 chỉ số p50 |
| seasonal naive lấp giá trị thiếu | loại A, `n_dong_dung` |
| thêm đặc trưng ngoài mục 8 | B7 |
| RMSE < MAE | B2 |
| SMAPE(0,0) trả NaN | C5 |
| MASE khi `d = 0` trả `inf` | C9 |

Cộng hai trạng thái phải **xanh**: thế giới đúng, và thế giới đúng có thêm dòng
`train`/`val` thừa trong bảng baseline.

Ba lỗi mà chính test này phát hiện trong bản đầu của công cụ, ghi lại để không tái
phạm:

1. Loại A không lọc `split` — mỗi tổ hợp có ba dòng nên công cụ báo "thiếu dòng",
   tức **trượt oan** mà nguyên nhân rất khó lần.
2. B1 viết bằng dấu `=`. Đẳng thức `tổng = hợp_lệ − n_chuỗi × 2 × h` chỉ đúng khi mọi
   dòng sát ranh giới đều hợp lệ; dữ liệu thật có NaN gần ranh giới thì mất ít hơn
   `2h`. Đã đổi thành bất đẳng thức `1 ≤ mất ≤ n_chuỗi × 2 × h` — vẫn bắt được kiểu
   quên purge (mất **0** dòng) mà không báo oan.
3. C9/C10 kiểm bằng `not isfinite`. `inf` cũng không hữu hạn, nên một bản chia cho 0
   rồi trả `inf` sẽ **lọt** — mà `inf` trôi vào trung vị thì bôi đen cả cột. Đã đổi
   thành `isnan`.

---

## 5. Kết quả cổng

Điền khi nghiệm thu.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 3.1 Sản phẩm | | |
| 3.2 Bộ máy đánh giá | | |
| 3.3 Ba baseline | | |
| 3.4 Rò rỉ L1–L4 | | |
| 3.5 ML so với naive | | |

**Kết luận:**
**Ngày duyệt:**

---

## 6. Hai điểm mơ hồ — đã chốt bằng QĐ-014

Cả hai đã có lời giải, ghi ở `docs/decisions.md` QĐ-014. Giữ lại phần mô tả để đọc
được vì sao chọn như vậy.

**1. Rolling-origin 5 fold chia thế nào.** protocol mục 9 nói *"5 fold trên phần train
cộng validation"* nhưng không nói fold trượt bước bao nhiêu, và train mỗi fold có mở
rộng dần (expanding) hay giữ độ dài cố định (sliding).

→ **QĐ-014 điểm 1: expanding, 5 fold, chia đều vùng validation.** Vùng validation
`[1612, 1957)` rộng 345 bucket, chia 5 được 69 bucket mỗi fold:

| Fold | Train | Validation |
|---|---|---|
| 0 | `[0, 1612)` | `[1612, 1681)` |
| 1 | `[0, 1681)` | `[1681, 1750)` |
| 2 | `[0, 1750)` | `[1750, 1819)` |
| 3 | `[0, 1819)` | `[1819, 1888)` |
| 4 | `[0, 1888)` | `[1888, 1957)` |

Luật purge của QĐ-013 điểm 2 áp **trong từng fold**: dòng thuộc train của fold khi cả
`t` và `t+h` nằm trong train của fold đó, tương tự cho validation. Test `[1957, 2304)`
**không fold nào chạm tới**.

Chọn expanding vì hai lẽ: cửa sổ chỉ có 8 ngày nên sliding sẽ làm train của fold cuối
ngắn tới mức vô nghĩa; và expanding khớp với cách hệ thống thật hoạt động — càng về
sau càng có nhiều lịch sử.

**2. SVR trên mẫu con.** Mục 11 ghi *"Chỉ chạy trên mẫu con nếu quá chậm"*.

→ **QĐ-014 điểm 2: lấy mẫu con trên DÒNG huấn luyện, không trên chuỗi.** Phân tầng
theo ba tầng CV của QĐ-012, `random_state = 42`, **cùng một mẫu con cho mọi horizon**.
Tập test giữ **100%** — bảy model phải được chấm trên đúng cùng bộ dòng, nếu không
bảng so sánh mất nghĩa.

Vì sao lấy theo dòng chứ không theo chuỗi: bỏ bớt chuỗi là đổi **quần thể**, và mọi
kết luận mức chuỗi (trung vị theo chuỗi, phân tầng CV) sẽ không so được với sáu model
kia. Bỏ bớt dòng chỉ làm SVR học từ ít mẫu hơn — đó là một bất lợi *của SVR*, được
khai báo minh bạch, chứ không phải một quần thể khác.

Log GĐ3 phải ghi rõ tỉ lệ mẫu con thực dùng, hoặc ghi "không cần lấy mẫu con".

---

## Phụ lục — vì sao cổng này neo vào baseline

Có thể hỏi: sao không neo vào kết quả model cho chắc?

Vì không neo được. Random Forest với `n_estimators` khác nhau, XGBoost với seed khác
nhau, thậm chí cùng seed nhưng khác phiên bản thư viện — đều ra số khác. Ép hai bản
hiện thực ra cùng con số model là ép sai chỗ, và sẽ dẫn tới việc ghim seed rồi tự lừa
mình rằng đã kiểm chứng được gì đó.

Baseline thì ngược lại: nó **phải** ra cùng con số, vì không có gì để mà khác. Và vì
mọi kết luận của GĐ3 đều có dạng "model X tốt hơn naive bao nhiêu", một baseline sai
sẽ làm sai **toàn bộ** bảng kết quả mà không có phép kiểm nào khác bắt được.

Đó là lý do 27 con số ở mục 2.3 là phần nặng nhất của cổng này.
