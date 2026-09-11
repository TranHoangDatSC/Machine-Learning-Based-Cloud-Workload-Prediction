# Hồ sơ cổng GĐ3

**Người giữ cổng:** A
**Trạng thái:** **ĐÓNG — ĐẠT ngày 2026-09-11.** Đủ 8 model × 9 tổ hợp, Bước 6 xong,
`check_gd3.py` thoát 0, `pytest` 277 passed.
**Cập nhật:** 2026-09-11 (nghiệm thu lần hai, sau khi B chạy nốt `rf`/`svr`)
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

> **Đã kiểm hết, 2026-09-11.** Các ô dưới đây tick theo kết quả ở mục 5; bằng chứng
> máy chạy được là `python scripts/check_gd3.py` thoát 0 và `pytest tests/` 277 passed.

### 3.1 Sản phẩm có đủ không

- [x] `src/cwp/models/baselines.py` — ba baseline của mục 11
- [x] `src/cwp/evaluation/metrics.py` — MAE, RMSE, SMAPE, MASE, R² theo QĐ-013
- [x] `src/cwp/evaluation/splits.py` — chia theo bucket, purge dòng vắt ranh giới,
      rolling-origin 5 fold
- [x] `tests/` — test cho cả ba module trên, và test **biết đỏ**: `scripts/pha_gd3.py`
      phá 5 kiểu, cả 5 bị bắt, mã nguồn về nguyên trạng
- [x] `runs/` — 5 thư mục, mỗi thư mục kèm snapshot config và `meta.json`
- [x] `results/tables/` — 9 bảng, có cả bản gộp và bản tách theo tầng (`tang_gd3.csv`)
- [x] Log GĐ3 trong `research-log/` — `2026-09-10-gd3-thi-nghiem-a.md`

### 3.2 Bộ máy đánh giá khớp neo — khớp **tuyệt đối**

- [x] 27 con số ở mục 2.2 — lệch `(0, 0, 0)` cả chín tổ hợp
- [x] Tổng ba tập nhỏ hơn tổng dòng hợp lệ đúng `n_chuỗi × 2 × h` — E1/E2 khớp đúng
      bằng; E3 mất ít hơn 3 đơn vị ở `h = 1` vì NaN gần ranh giới, nằm trong cận của B1
- [x] 9 mẫu số MASE và 9 giá trị MASE của naive ở mục 2.4
- [x] Ngưỡng và số chuỗi mỗi tầng ở mục 2.5
- [x] Tỉ lệ dòng bỏ của seasonal naive ở mục 2.6

### 3.3 Ba baseline khớp neo — khớp **tuyệt đối**

- [x] 27 con số MAE ở mục 2.3
- [x] RMSE, SMAPE, MASE, R² khớp `reference_gd3.json` — 45/45 chỉ số p50, **sau khi
      sửa lỗi R² ở tham chiếu của A** (mục 5.1)
- [x] Gộp bằng **trung vị theo chuỗi** kèm IQR — `pha_gd3.py` P4 đổi sang trung bình
      thì hai test đỏ và B5 báo 40 dòng vi phạm `p25 ≤ p50 ≤ p75`

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

**Kết quả bốn phép kiểm, 2026-09-11:**

- [x] **L1** — 18 test `test_L1_*`/`test_L3_*` xanh ở cả ba horizon, và B chạy lại
      trực tiếp trên 9 ma trận thật: `max(t+h)` của train = 1.611, của vùng khớp cuối
      = 1.956, `min(t)` của test = 1.957
- [x] **L2** — 55 lần chạm test trên 45 tổ hợp; chênh 10 lần đều giải thích được, xem
      mục 5.6. Không lần nào test được dùng để **chọn** gì
- [x] **L3** — biên 5 fold in ra là `1612, 1681, 1750, 1819, 1888, 1957`, không fold
      nào chạm `[1957, 2304)`
- [x] **L4** — B7 của `check_gd3.py` xác nhận 9 ma trận đặc trưng đúng 22 cột

### 3.5 Điều kiện qua cổng — và một áp lực mới

`research-plan.md`: *"trả lời được 'ML có vượt naive không, ở horizon nào' kèm kiểm
định thống kê. Nếu ML không vượt ở `h=1` thì **đó là finding**, ghi lại và đi tiếp,
không được ép model."*

- [x] Có bảng so mọi model với naive, ba môi trường × ba horizon —
      `ml_vs_naive_gd3.csv`, 63 dòng
- [x] Có kiểm định Wilcoxon cho chênh lệch giữa các model (mục 15) —
      `wilcoxon_gd3.csv`, 252 cặp, Holm–Bonferroni trong từng `(env, h)`
- [x] **Nếu ML thua naive ở đâu đó, điều đó được BÁO CÁO, không bị giấu** — E1 báo
      thẳng *"KHÔNG CÓ"* ở cả ba horizon, và bảng phân tầng báo thẳng rằng ở tầng
      bursty nhất **mọi** model đều thua naive

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

Nghiệm thu **2026-09-11**, máy `DESKTOP-J03IDG1`, `pytest tests/` = **277 passed,
1 skipped**.

Nghiệm thu hai vòng. Vòng một (2026-09-10) trượt vì thiếu sản phẩm, lúc đó `pytest`
là 275; vòng hai (2026-09-11) sau khi B chạy nốt `rf`, `svr`, Bước 6, và thêm hai test
T5 cho mẫu con SVR — thành 277.

| Mục | Kết quả | Ghi chú |
|---|---|---|
| 3.1 Sản phẩm | **ĐẠT** | Đủ 8 model × 9 tổ hợp; `tang_gd3.csv`, `wilcoxon_gd3.csv`, `ml_vs_naive_gd3.csv`, 10 hình + PDF; log đầy đủ |
| 3.2 Bộ máy đánh giá | **ĐẠT** | 27 số dòng, 9 mẫu số MASE, ngưỡng tầng, tỉ lệ bỏ của seasonal — khớp tuyệt đối |
| 3.3 Ba baseline | **ĐẠT** | 45 chỉ số p50 khớp, **sau khi sửa lỗi ở tham chiếu của A** — xem 5.1 |
| 3.4 Rò rỉ L1–L4 | **ĐẠT** | 18 test L1/L3/L4 xanh; L2: **55 lần chạm test trên 45 tổ hợp** `(env, h, model ML)`, cộng dồn 5 run — xem 5.6 |
| 3.5 ML so với naive | **ĐẠT** | Bảng đủ, Wilcoxon + Holm trên 252 cặp, và **chỗ ML thua được báo cáo thẳng** |

**Kết luận: ĐẠT.** `python scripts/check_gd3.py` thoát 0; `pytest tests/` **277 passed,
1 skipped**. Điều kiện qua cổng ở `docs/research-plan.md` — *"trả lời được 'ML có vượt
naive không, ở horizon nào' kèm kiểm định thống kê"* — đã thoả, và câu trả lời là
**phần lớn là không** (mục 5.3).

**Ngày duyệt:** 2026-09-11

### 5.1 Lỗi R² của tham chiếu — B đúng, A sai, đã sửa

B báo 27 ô R² của E1 lệch tham chiếu và **từ chối sửa code cho khớp**, kèm đề nghị A
quyết. Truy nguyên xác nhận B đúng hoàn toàn.

Chuỗi **`E1_830`** có **346** dòng test mang **đúng một giá trị** `1,1333333333333333`
(346 là số bị ép bởi số học: mục 2.2 ghi E1 `h = 1` có 254.310 dòng test, chia 735
chuỗi ra đúng 346,0). Về toán học `SS_tot = 0` nên QĐ-013 điểm 4 bảo loại chuỗi. Nhưng
`ȳ = sum/n` của 346 bản sao một số không biểu diễn được chính xác ra
`1,133333333333333`, nên `sum((y−ȳ)²) = 1,71 × 10⁻²⁹ > 0`. Bản của A kiểm
`sstot > 0` nên **chấm R² = 1,0** — điểm tuyệt đối cho một chuỗi hằng mà naive đoán
trúng tầm thường, và giá trị đó đẩy trung vị cả cột lên.

> **Đính chính 2026-09-11.** Bản đầu của mục này ghi *347 dòng* và
> `ss_tot = 6,84 × 10⁻²⁹`. Hai con số đó đi với nhau và đều **đúng cho n = 347** — tức
> phép chẩn đoán sinh ra chúng đã cắt cửa sổ test `[1957, 2304)` **chưa áp luật purge**
> (với `h = 1`, purge bỏ đúng một bucket). Bản thân `reference_gd3.py` thì cắt đúng, nên
> `reference_gd3.json` không bị ảnh hưởng — 45/45 chỉ số khớp bản của B.
>
> Chính chỗ này lại là lập luận mạnh nhất cho `min == max`: **cùng một số 0 toán học
> hiện ra thành `1,7e−29` hay `6,8e−29` tuỳ cách cắt và cách cộng dồn.** Không có
> ngưỡng epsilon nào đúng cho mọi cách hiện thực; chỉ có phép so chính xác là đúng.

Bốn chuỗi hằng còn lại của E1 (`E1_172, E1_295, E1_543, E1_807`) mang hằng số biểu
diễn được chính xác nên tổng bình phương ra đúng 0 và bị loại bình thường. Chỉ
`E1_830` lọt. E2 và E3 không có chuỗi hằng nào trên test nên không bị ảnh hưởng.

**Đã sửa `scripts/reference_gd3.py`** dùng `min == max` — đặc trưng chính xác của
phương sai bằng 0, không phụ thuộc thứ tự cộng dồn. Sinh lại `reference_gd3.json`;
`check_gd3.py` chuyển sang **ĐẠT**, `n_chuoi/n_loai` của E1 nay là **730/5**.

> Đây là **lần thứ ba** thước đo của A sai còn sản phẩm của B đúng (GĐ1: lỗi đếm
> điểm nội suy; GĐ2: `dropna` thay luật cửa sổ; GĐ3: chuỗi này). Cơ chế kiểm chéo
> không phải để B chứng minh mình khớp A — nó để chỗ lệch nào cũng bị truy tới cùng,
> bất kể lỗi thuộc bên nào. Cách B xử lý lần này là mẫu mực: báo lệch, truy nguyên,
> **không** sửa đầu ra cho vừa đáp án, và nói rõ cổng chưa nên coi là ĐẠT.

### 5.2 Nhãn hướng so sánh — lỗi đã phát hiện ở vòng một, B đã sửa

Vòng một A phát hiện `fig_gd3_results.py::kiem_dinh_cap` lấy **p-value từ Wilcoxon
ghép cặp** (kiểm trung vị của **hiệu**) nhưng lấy **hướng** từ
`delta_p50 = median(a) − median(b)` (**hiệu của hai trung vị**). Hai đại lượng này
ngược dấu được, và khi đó bảng khẳng định một chiến thắng có ý nghĩa **sai chiều**.
Đo trên dữ liệu lúc đó: 4 trong 40 cặp so với naive bị gán sai, cả 4 đều nghiêng về
phía ML.

**B đã sửa trước khi chạy Bước 6.** Bản hiện tại tính cả hai và tách vai trò:

```python
"delta_p50": float(np.median(va) - np.median(vb)),   # hiệu hai trung vị — chỉ để báo cáo
"hieu_p50":  float(np.median(va - vb)),              # trung vị của hiệu — dùng gán hướng
```

Kiểm lại trên bảng đã sinh: `hieu_p50` khớp trung vị của hiệu tính lại từ
`per_series_gd3.csv`, và **252/252 cặp gán đúng hướng** (32 cặp không kết luận được
sau hiệu chỉnh Holm). `ml_vs_naive_gd3.csv` cũng suy `vuot_naive` từ đúng đại lượng
ghép cặp ở cả 63 dòng.

> **Đính chính của A.** Vòng một A viết rằng `ml_vs_naive_gd3.csv` *"sẽ khẳng định ML
> vượt naive ở h=1, ngược với dữ liệu"*. Sai — A đọc `kiem_dinh_cap` rồi suy ra cho cả
> `bang_ml_vs_naive`, mà hàm thứ hai vốn đã dùng đúng thống kê ghép cặp ngay từ đầu.
> Lỗi chỉ nằm ở cột `tot_hon` của `wilcoxon_gd3.csv`. Phạm vi hẹp hơn A nói.

### 5.3 Trả lời RQ1 — ML phần lớn KHÔNG vượt naive

Wilcoxon signed-rank trên MAE theo chuỗi, hiệu chỉnh Holm–Bonferroni trong từng
`(env, h)`, hướng lấy từ trung vị của hiệu ghép cặp.

| | Số ô ML vượt naive | Chi tiết |
|---|---|---|
| **E1** | **0 / 15** | Không model ML nào vượt naive ở bất kỳ horizon nào |
| **E2** | **2 / 15** | Chỉ `svr`, ở h=6 và h=12 |
| **E3** | **11 / 15** | `lr`, `ridge`, `rf` ở h=1; thêm `xgb` ở h=6 và h=12 |

Đây là **finding**, không phải thất bại — `docs/research-plan.md` đã lường trước:
*"Nếu ML không vượt ở h=1 thì đó là finding, ghi lại và đi tiếp, không được ép model."*
Và `protocol.md` mục 17 cam kết *"không giấu việc baseline naive thắng model ML"*.

Diễn giải thẳng: trên trace **VM** (E1, E2), persistence ở lưới 5 phút gần như không
thể vượt — chuỗi gần bước ngẫu nhiên. Trên trace **máy vật lý** (E3), nơi tải của
nhiều VM cộng lại làm ACF lag 1 lên 0,86 (so với 0,67) và chu kỳ ngày rõ
(ACF lag 288 = 0,60 so với 0,13), ML **có** chỗ để thắng. Đây là vật liệu trực tiếp
cho RQ2 và là nền cho RQ3.

Một chi tiết dễ đọc nhầm: `svr` có **tỉ số MAE gộp** thấp hơn naive ở cả sáu ô của
E1 và E2 (0,78–0,93), trông như thắng đậm. Nhưng thống kê **ghép cặp** chỉ xác nhận
hai ô. Hai cách đo trả lời hai câu hỏi khác nhau — *"tổng thể tốt hơn bao nhiêu"* so
với *"tốt hơn trên bao nhiêu chuỗi"* — và khi chúng lệch nhau thì bảng phải nói cả hai,
đừng chọn cái đẹp hơn.

### 5.4 Sản phẩm Bước 5 và Bước 6 — đã đủ

Bảng công bố là **hợp của 5 lần chạy**; snapshot đầy đủ và **khớp bảng công bố từng ô**
là `runs/20260910-202500_experiments_gd3` (lần chạy lại `svr` sau khi B sửa mẫu con).

> **Đính chính 2026-09-11.** Bản đầu trỏ vào `runs/20260910-154617_experiments_gd3`.
> Snapshot đó cũng đủ 72 tổ hợp nhưng **lệch bảng công bố 30 ô** — toàn bộ `svr` ở
> `h = 6` và `h = 12`, vì nó chụp **trước** khi mẫu con SVR được sửa (QĐ-014 điểm 2).
> Ví dụ E2 `h = 12`: snapshot cũ `0,3732`, bảng công bố `0,3950`. Protocol mục 16 đòi
> mọi số trong paper truy ngược được về một thư mục `runs/` cụ thể, nên con trỏ phải là
> `20260910-202500`.

RF chiếm phần lớn chi phí máy (14.466 s trên tổng ~21.700 s của lần chạy 154617).

**Hạn chế phải ghi vào paper: siêu tham số chốt nằm ở BIÊN TRÊN của lưới.**

| Model | Lưới | Chốt ở biên **trên** | Chốt ở biên **dưới** | Chạm biên bất kỳ |
|---|---|---:|---:|---:|
| `rf` | `max_depth ∈ {8, 16}` | **7 / 9** | 2 / 9 | 9 / 9 |
| `svr` | `C ∈ {1, 10}` | **7 / 9** | 2 / 9 | 9 / 9 |
| `xgb` — trục `depth` | `{4, 8}` | **6 / 9** | 3 / 9 | 9 / 9 |
| `xgb` — trục `n_estimators` | `{300, 600}` | 1 / 9 | **8 / 9** | 9 / 9 |
| `ridge` | `alpha ∈ {0,01 … 100}` | 4 / 9 | **5 / 9** | **9 / 9** |

> **Đính chính 2026-09-11.** Bản đầu chỉ đếm biên **trên** và ghi `ridge` 4/9, `xgb`
> 6/9. Hai chỗ đó nói **nhẹ đi** so với sự thật:
>
> - `ridge` chốt `alpha = 0,01` ở 5/9 tổ hợp còn lại, tức **biên dưới**. Cộng lại,
>   `ridge` chạm mép lưới ở **9/9** — lưới alpha hẹp ở *cả hai* đầu, không phải chỉ
>   đầu trên.
> - `xgb` 6/9 là của trục `depth`. Trên trục số cây thì ngược hẳn: 8/9 chọn **300**,
>   giá trị *thấp*, chỉ 1/9 chọn 600. Nghĩa là số cây **không** phải chỗ bị lưới chặn,
>   và nới nó gần như chắc chắn không đổi được gì.
>
> Với hai model quan trọng nhất, `rf` và `svr`, lưới chỉ có **hai** ứng viên nên mọi
> lựa chọn đều nằm ở mép — đó là hạn chế thật, và nó nặng hơn con số 7/9 gợi ra.

Khi lựa chọn rơi vào mép lưới thì tối ưu thật có thể nằm ngoài, nghĩa là ML đang bị
**giới hạn bởi lưới**, không phải bởi dữ liệu. Cộng thêm việc B khai rõ `rf` chỉ chạy
**50 cây** vì chi phí. Nên phát biểu đúng phải là: *"với lưới siêu tham số này và ngân
sách tính toán này, ML không vượt naive trên E1 và E2"* — chứ không phải một kết luận
về năng lực của họ thuật toán.

Điều này **không** làm lung lay kết luận chính: `lr` và `ridge` thua naive
**1,23–2,57 lần** trên E1/E2 tuỳ horizon (1,23–1,35× ở `h = 1`, lên tới 2,33–2,57× ở
`h = 12`), khoảng cách đó không phải do lưới, và `lr` thì **không có siêu tham số nào**
để nới. Chỉ `rf`, `xgb`, `svr` là sát naive đủ để lưới có thể đổi kết cục.

> **Đính chính 2026-09-11.** Bản đầu ghi *"2,3–2,6 lần"*, đó là con số của riêng
> `h = 12`. Dải đúng trên cả ba horizon là **1,23–2,57**. Lập luận không đổi — thậm chí
> ở mức hẹp nhất, 1,23×, vẫn quá xa để một lưới `alpha` khác khép lại, và `lr` thì
> không có gì để nới.

**Đã chốt bằng QĐ-015: khai báo lưới, KHÔNG chạy lại ở GĐ3.** Nới lưới lúc này là nới
*sau khi đã biết ML thua* — cùng họ với điều mục 17 cam kết không làm. Muốn kiểm độ
vững thì làm ở GĐ5, khai báo lưới mới **trước** khi chạy và **báo cáo cả hai** kết
quả. Hai điểm B nêu trong mục Vướng mắc của log GĐ3 vì thế đã đóng.

### 5.5 Một quan sát cần theo dõi, chưa phải lỗi

Trên **E1**, tập validation **dễ hơn hẳn** tập test: MAE của naive là **0,2185** trên
val so với **0,4077** trên test (h=1). E2 và E3 không có khoảng cách này.

Không phải rò rỉ — nó giải thích vì sao `mae_p50_val` của xgb (0,168) thấp hơn nhiều
so với MAE test (0,397). Nhưng nó có nghĩa là siêu tham số của E1 được chọn trên một
vùng thời gian không đại diện. Nên ghi vào Limitations, và cân nhắc ở GĐ4.

### 5.6 L2 — test bị chạm bao nhiêu lần, và vì sao hơn một lần

> Bổ sung 2026-09-11. Mục 3.4 L2 dặn *"Hỏi B thẳng: đã chạy test bao nhiêu lần, và nếu
> hơn một lần thì vì sao."* Đây là câu trả lời, đếm tự động từ `runs/*/meta.json` —
> `run_experiments.py` gọi `predict` trên dòng test ở đúng một hàm và hàm đó tự đếm.

| Thư mục run | Số lần | Phạm vi |
|---|---:|---|
| `20260910-144955` | 9 | E1, ba horizon × `lr`/`ridge`/`xgb` |
| `20260910-151730` | 18 | E2 + E3, ba horizon × `lr`/`ridge`/`xgb` |
| `20260910-153929` | 4 | `svr`, bốn tổ hợp đầu |
| `20260910-154617` | 15 | `rf` + `svr`, phần còn lại |
| `20260910-202500` | 9 | `svr`, chạy lại cả chín sau khi sửa mẫu con |
| **Cộng** | **55** | trên **45** tổ hợp `(env, h, model ML)` |

Chênh 10 lần, và cả 10 đều giải thích được:

- **9 lần** là **chạy lại toàn bộ `svr`** sau khi B phát hiện mẫu con không dùng chung
  cho ba horizon như QĐ-014 điểm 2 đòi (chỉ trùng 2,9% giữa `h=1` và `h=6`). Đây là
  chạy lại vì **hiện thực sai so với quyết định đã chốt**, không phải chọn lần đẹp hơn:
  số cũ bị **thay hẳn**, không bên nào được giữ lại để so, và hướng kết luận RQ1 không
  đổi.
- **1 lần** là `E1_h1_svr` bị chấm hai lần trong sự cố hai tiến trình chạy song song
  tối 2026-09-10. Cùng seed, cùng siêu tham số, cùng mẫu con nên ra cùng kết quả.

Ngoài ra B khai thêm **2 lần chạm test đã bị loại bỏ**: một lần chạy thử đường ống trên
`E2 h=12` với `lr` và `ridge`, ghi vào thư mục tạm ngoài repo. B có nhìn ba con số đó
và khẳng định không dùng chúng để đổi bất kỳ lựa chọn nào — lưới siêu tham số đã chốt
từ trước và không sửa sau. **Khai báo chủ động một việc bất lợi cho mình là đúng tinh
thần mục 17**; A ghi nhận và chấp nhận.

Không lần nào test được dùng để **chọn** gì: `do_lua_chon()` không nhận mặt nạ test.

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
