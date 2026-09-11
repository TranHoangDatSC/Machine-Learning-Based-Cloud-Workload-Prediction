# 2026-09-10 — GĐ3: bộ máy đánh giá, ba baseline, và Thí nghiệm A

**Người thực hiện:** B
**Giai đoạn:** GĐ3
**Thời lượng:** ~7 giờ (chạy sang rạng sáng 2026-09-11)

## Mục tiêu phiên

Làm trọn `research-log/brief-gd3-b.md`: chia tập theo bucket có purge, năm chỉ số theo
QĐ-013, ba baseline khớp 27 con số neo, phá code kiểm ngược, rồi chạy tám model × ba
môi trường × ba horizon và trả lời RQ1 — *ML có vượt naive không*.

## Đã làm

| Bước | Việc | Trạng thái |
|---|---|---|
| 0 | Hai cổng cũ còn ĐẠT, `pytest` xanh | xong |
| 1 | `src/cwp/evaluation/splits.py` + 54 test | xong |
| 2 | `src/cwp/evaluation/metrics.py` + 31 test | xong |
| 3 | `baselines.py`, `run_baselines.py`, 27 số MAE khớp tuyệt đối | xong |
| 4 | `scripts/pha_gd3.py` — năm kiểu phá, cả năm bị bắt | xong |
| 5 | `run_experiments.py` — 8 model × 9 tổ hợp = 72/72 | xong |
| 6 | `fig_gd3_results.py` — phân tầng + Wilcoxon + 10 hình | xong |
| 7 | Log này; `check_gd3.py` **ĐẠT**, `277 passed, 1 skipped` | xong |

## Nghiệm thu

```
ĐẠT — bộ máy đánh giá và ba baseline GĐ3 khớp tham chiếu.
TIẾN ĐỘ GĐ3: 8/8 sản phẩm
277 passed, 1 skipped
```

## Bước 1 — chia tập

Ranh giới theo **bucket**, offset so với `b0` của từng môi trường. `b0` đọc từ
`data/processed/`, **không** lấy `min(bucket)` của ma trận đặc trưng — 24 dòng đầu mỗi
chuỗi không hợp lệ nên bucket nhỏ nhất ở đó là `b0 + 24`, lấy nhầm sẽ đẩy cả ba ranh
giới đi 24 bucket mà không có gì báo lỗi.

```
tập  : train [0, 1612)   val [1612, 1957)   test [1957, 2304)
fold 0: train (0, 1612)  val (1612, 1681)
fold 1: train (0, 1681)  val (1681, 1750)
fold 2: train (0, 1750)  val (1750, 1819)
fold 3: train (0, 1819)  val (1819, 1888)
fold 4: train (0, 1888)  val (1888, 1957)
```

Biên fold `1612, 1681, 1750, 1819, 1888, 1957` — khớp QĐ-014 điểm 1.

Ba phép kiểm phiếu gọi đích danh, xanh ở cả `h = 1, 6, 12`:

| Phép kiểm | Test |
|---|---|
| mọi dòng train có `t + h < 1612` | `test_L1_moi_dong_train_co_target_van_trong_train` |
| `max(t+h)` train fold `i` < `min(t)` val fold `i` | `test_L3_train_fold_ket_thuc_truoc_val_fold` |
| không dòng nào của fold nào có `t ≥ 1957` | `test_L3_khong_fold_nao_cham_test` |

Thêm `fit_mask()` cho vùng huấn luyện của model **cuối cùng** — train + val
`[0, 1957)`, vẫn purge.

**L1 chạy lại trên dữ liệu thật** (không phải offset giả lập), cả 9 ma trận:

| | max(t+h) train | max(t+h) fit | min(t) test |
|---|---:|---:|---:|
| cả 9 tổ hợp | 1.611 | 1.956 | 1.957 |

## Bước 3 — số dòng và ba baseline

**27 số dòng khớp tuyệt đối** với gate mục 2.2 (lệch `(0, 0, 0)` cả chín tổ hợp).

| Env | h | train | val | test | hợp lệ GĐ1 | mất | trần `n×2×h` |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 | 1 | 1.142.276 | 252.840 | 254.310 | 1.650.896 | 1.470 | 1.470 |
| E1 | 6 | 1.138.601 | 249.165 | 250.635 | 1.647.221 | 8.820 | 8.820 |
| E1 | 12 | 1.134.191 | 244.755 | 246.225 | 1.642.811 | 17.640 | 17.640 |
| E2 | 1 | 469.502 | 103.888 | 104.492 | 678.486 | 604 | 604 |
| E2 | 6 | 466.681 | 102.378 | 102.982 | 675.665 | 3.624 | 3.624 |
| E2 | 12 | 464.338 | 100.566 | 101.170 | 673.322 | 7.248 | 7.248 |
| E3 | 1 | 596.549 | 169.675 | 171.716 | 938.933 | 993 | 996 |
| E3 | 6 | 584.598 | 167.127 | 169.209 | 926.892 | 5.958 | 5.976 |
| E3 | 12 | 575.245 | 164.102 | 166.203 | 917.463 | 11.913 | 11.952 |

E1 và E2 mất **đúng** `n_chuỗi × 2 × h`; E3 mất ít hơn ba đơn vị ở `h = 1` vì vài dòng
sát ranh giới vốn đã bị luật cửa sổ mục 8 loại từ trước — đúng như đính chính QĐ-014
dự đoán, và là lý do B1 là bất đẳng thức chứ không phải đẳng thức.

**MAE trung vị theo chuỗi, trên test — khớp tuyệt đối cả 27 ô:**

| Env | h | naive | ma6 | seasonal |
|---|---:|---:|---:|---:|
| E1 | 1 | 0,4077 | 0,4007 | 0,5834 |
| E1 | 6 | 0,4661 | 0,4263 | 0,6005 |
| E1 | 12 | 0,4494 | 0,4558 | 0,5818 |
| E2 | 1 | 0,4140 | 0,4100 | 0,5997 |
| E2 | 6 | 0,4808 | 0,4466 | 0,7207 |
| E2 | 12 | 0,4649 | 0,4633 | 0,6644 |
| E3 | 1 | 4,2955 | 5,0658 | 7,3528 |
| E3 | 6 | 6,5087 | 5,9087 | 7,7643 |
| E3 | 12 | 7,0270 | 6,8214 | 7,8778 |

Mẫu số MASE trung vị E1 **0,3487**, E2 **0,3352**, E3 **4,4235**; 0 chuỗi có `d = 0`.
MASE của naive ở `h = 1`: 0,968 / 1,037 / 0,964 — xấp xỉ 1 đúng dấu hiệu mục 2.4.

Tỉ lệ dòng bỏ trên test: `naive` và `ma6` bỏ **0,0000%** ở cả ba môi trường; `seasonal`
bỏ 0% ở E1/E2 và **0,4251% / 0,4285% / 0,4326%** ở E3 — khớp mục 2.6.

## Phát hiện 1 — chuỗi `E1_830` và phép so `SS_tot == 0`

**Hiện tượng.** 378/405 ô của bảng baseline khớp tham chiếu tuyệt đối ngay lần đầu. 27
ô còn lại đều là **R² của E1** (3 baseline × 3 horizon × p25/p50/p75).

**Nguyên nhân.** `E1_830` có target **hằng** trên test: 346 dòng đều đúng
`1,1333333333333333`. `SS_tot` bằng 0 về mặt toán học nên QĐ-013 điểm 4 nói R² không
xác định. Nhưng `sum((y − ȳ)²)` tính bằng dấu phẩy động ra **`1,7 × 10⁻²⁹`**, vì
`ȳ = sum/n` của 346 bản sao một số không biểu diễn được chính xác thì không rơi đúng
vào chính số đó. Bản kiểm `ss_tot == 0` không bắt được, chuỗi lọt vào phần gộp với
`R² = 1,0` và kéo trung vị cả cột lên.

E1 có **5** chuỗi target hằng trên test (`E1_172, E1_295, E1_543, E1_807, E1_830`); bốn
chuỗi kia có hằng số biểu diễn được chính xác nên tổng bình phương ra đúng 0 và bị loại
bình thường. Chỉ `E1_830` lọt.

**Cách truy.** Dựng lại mảng R² của A từ ba phân vị nó công bố: mảng đúng (730 chuỗi,
đã loại cả 5) **cộng thêm `E1_830` với R² = 1,0** cho ra đúng `p25 = −0,115417`,
`p50 = 0,090004`, `p75 = 0,503074` — khớp cả ba tới 6 chữ số ở `naive` và `seasonal`.

**Đã sửa ở bản của B**, không sửa để khớp số: điều kiện `SS_tot = 0` kiểm bằng
`min == max`, đặc trưng **chính xác** của phương sai bằng 0, không phụ thuộc thứ tự
cộng dồn.

> **A đã xác nhận và sinh lại `reference_gd3.json` lúc 22:36 ngày 2026-09-10**, giờ báo
> `n_chuoi 730, n_loai 5`. Cả 45 chỉ số p50 khớp, cổng **ĐẠT**.

**Lỗi thứ hai cùng họ, tự phát hiện.** `n_loai` ban đầu đếm trên số chuỗi **có mặt
trong tập đang chấm** thay vì tổng số chuỗi của môi trường. `E3_m_2848` không có dòng
hợp lệ nào trên test nên nó biến mất khỏi cả `n_chuoi` lẫn `n_loai`, và bảng nói dối
rằng E3 có 497 chuỗi. Sau khi sửa, `n_chuoi + n_loai = 498` khớp tham chiếu ở cả năm
chỉ số.

Hai lỗi cùng một họ: **so số thực với 0, và đếm trên mẫu số sai.** Cả hai lọt qua
test đơn vị và chỉ bị bắt khi đối chiếu với bản độc lập.

## Bước 4 — phá code kiểm ngược

`python scripts/pha_gd3.py` — năm kiểu phá, hai bộ phát hiện chạy sau mỗi lần
(`pytest`, và `run_baselines.py --out <tạm>` rồi `check_gd3.py --tables <tạm>`). Bảng
thật ở `results/tables/` không bị đụng tới.

| Kiểu phá | Kết quả | Phép kiểm bắt được |
|---|---|---|
| P1 gán tập theo `t` thôi | **BỊ BẮT** | `test_L1_*`, `test_L3_*` (28 test đỏ) + 18 ô số dòng lệch neo + B1 |
| P2 purge hụt một dòng (`<=` thay `<`) | **BỊ BẮT** | như trên, số dòng lệch đúng `+n_chuỗi` mỗi tập |
| P3 mẫu số MASE tính trên test | **BỊ BẮT** | `test_mau_so_mase_train_lay_dung_vung_train_cua_cua_so` + cột `mase` lệch neo |
| P4 gộp bằng trung bình thay trung vị | **BỊ BẮT** | hai test `test_gop_*` + B5 (40 dòng vi phạm `p25 ≤ p50 ≤ p75`) |
| P5 seasonal lấp thiếu bằng `ffill` | **BỊ BẮT** | `test_N3_*`, `test_N4_*` + `n_dong_dung` lệch (E3 bỏ 0% thay vì 0,43%) |

Kết luận script: `ĐẠT — cả năm bản phá đều bị bắt, và mã nguồn đã về nguyên trạng.`

Hai điều suýt làm bài kiểm này **vô nghĩa**, ghi lại:

1. Bản đầu chạy `check_gd3.py` trên thư mục tạm **không có `reference_gd3.json`**, nên
   công cụ dừng ở tiền đề và mọi bản phá đều trông như "lọt" vì lý do chẳng liên quan.
2. Bản đầu so **nhãn** phép kiểm trượt. P3 làm trượt đúng cái nhãn `45 chỉ số p50` vốn
   đã trượt sẵn vì `E1_830`, nên nó bị tính là "lọt" dù công cụ đã in ra sai lệch ở cột
   `mase`. Đã đổi sang so **nhãn kèm dòng chi tiết**.

Vì bản gốc lúc đó đã trượt sẵn một mục, script ghi lại **vết nền** rồi đòi mỗi bản phá
làm trượt thêm ít nhất một phép kiểm **mới** — chặt hơn "đỏ là đạt".

## Bước 5 — tám model × ba môi trường × ba horizon

**Tám model, không phải bảy.** Mục 13 ghi *"3 môi trường x 7 model x 3 horizon"* nhưng
mục 11 liệt kê tám dòng (ba baseline + năm ML). B chạy và báo cả tám — xem mục Vướng
mắc.

### MAE trung vị theo chuỗi, trên test

| Env | h | naive | ma6 | seasonal | lr | ridge | rf | xgb | svr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E1 | 1 | 0,4077 | 0,4007 | 0,5834 | 0,5508 | 0,5511 | 0,3850 | 0,3969 | **0,3781** |
| E1 | 6 | 0,4661 | 0,4263 | 0,6005 | 0,8781 | 0,8783 | 0,5561 | 0,5876 | **0,3960** |
| E1 | 12 | 0,4494 | 0,4558 | 0,5818 | 1,0489 | 1,0490 | 0,5939 | 0,6390 | **0,4103** |
| E2 | 1 | 0,4140 | 0,4100 | 0,5997 | 0,5107 | 0,5108 | 0,3911 | 0,4106 | **0,3643** |
| E2 | 6 | 0,4808 | 0,4466 | 0,7207 | 0,9005 | 0,9006 | 0,5209 | 0,5464 | **0,3733** |
| E2 | 12 | 0,4649 | 0,4633 | 0,6644 | 1,1959 | 1,1958 | 0,5904 | 0,7063 | **0,3950** |
| E3 | 1 | 4,2955 | 5,0658 | 7,3528 | 4,0845 | 4,0847 | 4,1331 | **4,0423** | 4,1659 |
| E3 | 6 | 6,5087 | 5,9087 | 7,7643 | 5,6326 | 5,6321 | **5,3920** | 5,4231 | 5,4494 |
| E3 | 12 | 7,0270 | 6,8214 | 7,8778 | 6,4334 | 6,4329 | **5,8400** | 5,9183 | 6,1613 |

Tỉ số so với naive (dưới 1 là MAE gộp thấp hơn):

| Env | h | ma6 | lr | ridge | rf | xgb | svr |
|---|---:|---:|---:|---:|---:|---:|---:|
| E1 | 1 | 0,983 | 1,351 | 1,352 | 0,944 | 0,973 | 0,927 |
| E1 | 6 | 0,915 | 1,884 | 1,885 | 1,193 | 1,261 | 0,850 |
| E1 | 12 | 1,014 | 2,334 | 2,334 | 1,322 | 1,422 | 0,913 |
| E2 | 1 | 0,990 | 1,234 | 1,234 | 0,945 | 0,992 | 0,880 |
| E2 | 6 | 0,929 | 1,873 | 1,873 | 1,083 | 1,137 | 0,777 |
| E2 | 12 | 0,997 | 2,572 | 2,572 | 1,270 | 1,519 | 0,850 |
| E3 | 1 | 1,179 | 0,951 | 0,951 | 0,962 | 0,941 | 0,970 |
| E3 | 6 | 0,908 | 0,865 | 0,865 | 0,828 | 0,833 | 0,837 |
| E3 | 12 | 0,971 | 0,916 | 0,915 | 0,831 | 0,842 | 0,877 |

### Siêu tham số đã chốt — chỉ trên validation

Lưới do B chọn theo **chi phí đo được**, khai báo ở `src/cwp/models/registry.py`; giao
thức không chốt lưới nào.

| Env | h | ridge | rf | xgb | svr |
|---|---:|---|---|---|---|
| E1 | 1 | `alpha 100` | `max_depth 16` | `depth 8, 600 cây` | `C 10` |
| E1 | 6 | `alpha 0,01` | `max_depth 16` | `depth 8, 300 cây` | `C 10` |
| E1 | 12 | `alpha 0,01` | `max_depth 16` | `depth 8, 300 cây` | `C 10` |
| E2 | 1, 6, 12 | `alpha 0,01` | `max_depth 16` | `depth 8, 300 cây` | `C 10` |
| E3 | 1 | `alpha 100` | `max_depth 16` | `depth 4, 300 cây` | `C 10` |
| E3 | 6, 12 | `alpha 100` | `max_depth 8` | `depth 4, 300 cây` | `C 1` |

`lr` không có siêu tham số. `rf` chạy **50 cây**, `min_samples_leaf = 5` — với 100 cây
và hai ứng viên `max_depth`, riêng phần dò siêu tham số của RF đã mất hơn 3 giờ. **50
cây là một bất lợi của RF trong bảng này và nó được khai báo**; đừng đọc "RF thua
XGBoost" ở GĐ3 như kết luận về hai họ thuật toán.

Thời gian khớp model cộng dồn: `rf` 14.466 s, `svr` 4.631 s, `xgb` 2.487 s,
`ridge` 98 s, `lr` 39 s.

### Mẫu con của SVR — QĐ-014 điểm 2

**Có lấy mẫu con**, 10.000 dòng huấn luyện, phân tầng theo ba tầng CV, `random_state = 42`,
**tập test giữ 100%**. Số dòng thực dùng:

| Env | h = 1 | h = 6 | h = 12 |
|---|---:|---:|---:|
| E1 | 10.000 | 9.971 | 9.944 |
| E2 | 10.000 | 9.946 | 9.899 |
| E3 | 10.000 | 9.815 | 9.689 |

Tỉ lệ ba tầng trong mẫu: E1 3.392 / 3.388 / 3.220, E2 3.344 / 3.310 / 3.346,
E3 3.335 / 3.325 / 3.340.

## Phát hiện 2 — mẫu con SVR ban đầu **không** dùng chung cho ba horizon

Bản đầu rút mẫu riêng trong vùng train + val của **từng** horizon với cùng seed 42.
Nghe thì có vẻ tương đương, nhưng không: vùng train + val của `h = 12` ngắn hơn của
`h = 1` đúng 11 bucket, nên vị trí trong mảng lệch đi và `rng.choice` cho hai tập khác
hẳn nhau. Đo được:

| | trùng nhau |
|---|---:|
| h = 1 vs h = 6 | **2,9%** |
| h = 1 vs h = 12 | **1,6%** |
| h = 6 vs h = 12 | **2,2%** |

QĐ-014 điểm 2 đòi *"cùng một mẫu con dùng cho cả ba horizon"*, nên đây là **sai lệch
thật so với quyết định đã chốt**, không phải chuyện thẩm mỹ: ba horizon lẽ ra so được
với nhau vì SVR học trên đúng cùng bộ dòng.

**Đã sửa:** rút một lần theo khoá `(series_id, offset)` trên ma trận `h = 1`, mỗi
horizon lấy **giao** với dòng hợp lệ của chính nó. Giờ mẫu của `h = 6` và `h = 12` là
**tập con** của `h = 1` (99,4%–99,7% ở E1/E2, 96,9%–98,2% ở E3). **Đã chạy lại SVR cho
cả 9 tổ hợp** với mẫu mới; số trong mọi bảng của log này là số sau khi sửa.

Ghim bằng `tests/test_tang.py::test_T5_mau_con_svr_dung_chung_cho_ba_horizon`.

## Bước 6 — phân tầng và kiểm định

Ngưỡng tam phân vị CV **trong từng môi trường**, tính lại từ `cv_gd2.csv` mỗi lần chạy
(cách chia đọc từ `config/split.yaml`, ngưỡng **không** nằm trong config):

| Env | ngưỡng thấp/vừa | ngưỡng vừa/cao | số chuỗi mỗi tầng |
|---|---:|---:|---|
| E1 | 0,256049 | 0,848935 | 245 / 245 / 245 |
| E2 | 0,285320 | 0,943359 | 101 / 100 / 101 |
| E3 | 0,258254 | 0,320560 | 166 / 166 / 166 |

Khớp tuyệt đối gate mục 2.5.

## Phát hiện 3 — hướng của Wilcoxon phải lấy từ **trung vị của hiệu**

Bản đầu quyết định "model X vượt naive" bằng dấu của `trung vị(X) − trung vị(naive)`.
Sai. Wilcoxon signed-rank là kiểm định **ghép cặp**: nó nói về phân phối của
`MAE_X − MAE_naive` **trên từng chuỗi**, nên chỉ `trung vị(MAE_X − MAE_naive)` mới cùng
một thứ với cái nó kiểm. Hai đại lượng này **ngược dấu nhau ở 8 cặp** của GĐ3:

| Env | h | model | hiệu hai trung vị | trung vị của hiệu |
|---|---:|---|---:|---:|
| E1 | 1 | ma6 | −0,0070 | **+0,0130** |
| E1 | 1 | rf | −0,0227 | **+0,0109** |
| E1 | 1 | xgb | −0,0108 | **+0,0165** |
| E1 | 1 | svr | −0,0296 | **+0,0125** |
| E1 | 12 | svr | −0,0390 | **+0,0094** |
| E2 | 1 | ma6 | −0,0040 | **+0,0136** |
| E2 | 1 | xgb | −0,0034 | **+0,0041** |
| E2 | 12 | ma6 | −0,0016 | **+0,0230** |

Nghĩa là: MAE **gộp** của bốn model ở E1 `h = 1` thấp hơn naive, nhưng **chuỗi điển
hình lại tệ hơn** dưới các model đó — ví dụ `ma6` chỉ tốt hơn naive ở 309/735 chuỗi
(42%). Con số gộp thấp đến từ **hình dạng phân phối**, không phải từ việc thắng trên
từng máy.

Bản đầu vì thế tuyên bố "ma6, rf, xgb, svr vượt naive ở E1 h = 1" — **sai hướng**. Đã
sửa: `wilcoxon_gd3.csv` giờ có cả hai cột (`delta_p50` và `hieu_p50`), và hướng kết
luận lấy từ `hieu_p50`.

## Trả lời RQ1 — ML có vượt naive không

Wilcoxon signed-rank trên MAE theo từng chuỗi, Holm–Bonferroni trong từng `(env, h)`,
`alpha = 0,05`.

| Env | h | model vượt naive có ý nghĩa | MAE gộp thấp nhất |
|---|---:|---|---|
| E1 | 1 | **KHÔNG CÓ** | svr 0,927× |
| E1 | 6 | **KHÔNG CÓ** | svr 0,850× |
| E1 | 12 | **KHÔNG CÓ** | svr 0,913× |
| E2 | 1 | **KHÔNG CÓ** | svr 0,880× |
| E2 | 6 | svr | svr 0,777× |
| E2 | 12 | svr | svr 0,850× |
| E3 | 1 | lr, ridge, rf | xgb 0,941× |
| E3 | 6 | ma6, lr, ridge, rf, xgb | rf 0,828× |
| E3 | 12 | ma6, lr, ridge, rf, xgb | rf 0,831× |

**Trả lời thẳng:**

- **E1 (Bitbrains fastStorage): không model ML nào vượt naive, ở bất kỳ horizon nào.**
- **E2 (Bitbrains Rnd): chỉ SVR vượt, và chỉ ở `h = 6` và `h = 12`. Ở `h = 1` không ai
  vượt.**
- **E3 (Alibaba): ML vượt naive ở cả ba horizon**, rõ nhất ở `h = 6` và `h = 12` với
  Random Forest (0,828× và 0,831×).

Đây đúng là tình huống `research-plan.md` GĐ3 dự phòng: *"Nếu ML không vượt ở `h=1` thì
đó là finding, ghi lại và đi tiếp, không được ép model."* Không có model nào được thêm,
không có lưới nào được nới ra sau khi nhìn kết quả.

Linear Regression và Ridge **thua naive rất nặng** trên Bitbrains và tệ dần theo
horizon — tới **2,57×** ở E2 `h = 12`. Cơ chế đọc được: cả hai tối thiểu hoá sai số
bình phương gộp trên toàn môi trường, nên chúng bị các chuỗi tải cao kéo đi, trong khi
chỉ số báo cáo là trung vị **theo chuỗi** và phần lớn chuỗi Bitbrains có trung vị dưới
2%.

## Phát hiện 4 — không model nào vượt naive ở tầng bursty nhất

Tách theo ba tầng, `h = 1`, tỉ số MAE so với naive:

| Env | tầng | ma6 | lr | rf | xgb | svr |
|---|---|---:|---:|---:|---:|---:|
| E1 | thấp | 0,969 | 1,707 | 1,046 | 1,028 | 1,066 |
| E1 | vừa | 1,058 | 1,388 | 0,938 | 0,978 | **0,902** |
| E1 | **cao** | 2,233 | 1,801 | **1,351** | **1,418** | **1,520** |
| E2 | thấp | 0,909 | 1,613 | 0,955 | 0,941 | **0,806** |
| E2 | vừa | 0,973 | 1,165 | 0,904 | 0,928 | **0,845** |
| E2 | **cao** | 1,739 | 1,565 | **1,262** | **1,258** | **1,352** |
| E3 | thấp | 1,157 | 0,929 | 0,931 | **0,908** | 0,944 |
| E3 | vừa | 1,171 | 0,935 | 0,954 | **0,934** | 0,960 |
| E3 | **cao** | 1,201 | 0,977 | 0,995 | 0,989 | 1,021 |

**Ở tầng bursty nhất, mọi model đều thua naive** — 1,26× đến 2,23× trên Bitbrains, và
xấp xỉ hoà (0,98–1,02×) trên Alibaba. Toàn bộ lợi thế của ML nằm ở tầng thấp và vừa.
Điều này nhất quán với cơ chế: burst là thứ không dự đoán được từ 19 đặc trưng lịch sử,
còn persistence thì ít nhất không đoán bừa.

Cột `ti_le_cham_chan` (QĐ-012 điểm 3) cho thấy tầng "cao" của E1 và E2 có trung vị
**0,694** và **0,575** — tức các chuỗi bursty nhất của Bitbrains đã tiến sát trần thang
đo, nên CV của chúng bị chặn cứng và con số ở tầng này phải đọc kèm cảnh báo đó. E3
ngược lại, cả ba tầng đều quanh 0,21–0,27, xa trần.

## Ba điều phải khai báo về tính chặt của phiên này

**1. Số lần chạm tập test.** Đếm tự động trong `runs/*/meta.json`:

| Thư mục run | số lần | phạm vi |
|---|---:|---|
| `20260910-144955` | 9 | E1, ba horizon × lr/ridge/xgb |
| `20260910-151730` | 18 | E2 + E3, ba horizon × lr/ridge/xgb |
| `20260910-153929` | 4 | svr, bốn tổ hợp đầu |
| `20260910-154617` | 15 | rf + svr, phần còn lại |
| chạy lại svr (2026-09-11) | 9 | svr, cả chín tổ hợp |

Cộng dồn **55 lần** trên **45 tổ hợp `(env, h, model ML)`**. Chênh lệch 10 lần:

- **9 lần** là do **chạy lại toàn bộ SVR** sau khi sửa mẫu con (Phát hiện 2). Đây là
  chạy lại vì hiện thực sai so với QĐ-014, không phải chọn lần tốt nhất — số cũ đã bị
  **thay hẳn**, không bên nào được giữ lại để so.
- **1 lần** là `E1_h1_svr` bị tính hai lần trong sự cố chạy song song (điểm 2 dưới
  đây); hai lần cùng seed, cùng siêu tham số, cùng mẫu con nên ra cùng kết quả.

Ngoài ra có **2 lần chạm test bị loại bỏ**: một lần chạy thử đường ống trên `E2 h=12`
với `lr` và `ridge`, ghi vào thư mục tạm ngoài repo. Tôi **có** nhìn ba con số đó, và
khẳng định không dùng chúng để đổi bất kỳ lựa chọn nào — lưới siêu tham số đã chốt
trước đó và không sửa sau.

Không lần nào chọn siêu tham số bằng test: `do_lua_chon()` không nhận mặt nạ test.

**2. Sự cố chạy song song, 2026-09-10 lúc 22:46.** Có một tiến trình thứ hai
(`--models naive,ma6,seasonal,lr,ridge,xgb,rf,svr --resume`) chạy đồng thời với chuỗi
của B. Cả hai cùng đọc–sửa–ghi bốn tệp CSV nên có nguy cơ **mất dòng lặng lẽ**. Đã dừng
chuỗi của B để nhường, rồi kiểm lại ngay: `experiments_gd3.csv` 360 dòng = 72 tổ hợp ×
5 chỉ số, `chosen_gd3.csv` 72 dòng, **0 khoá trùng** ở cả bốn tệp. Không mất dữ liệu.

**3. Tính độc lập của thước đo yếu hơn GĐ1 và GĐ2.** `reference_gd3.py` do cùng agent
đã viết code B của GĐ2 soạn ra (QĐ-014 điểm 3). Phiên này **không đọc** `reference_gd3.py`,
và chỉ mở `reference_gd3.json` **sau khi** bảng baseline đã chạy xong lần đầu. Nhưng
loại A vẫn là bằng chứng yếu hơn hai giai đoạn trước, và `E1_830` là ví dụ sống: hai bản
cùng mắc **cùng một lỗi** `ss_tot == 0`, nên chúng khớp nhau ở 378/405 ô mà cả hai đều
sai ở 27 ô còn lại. Chỉ có phép kiểm loại C (đáp án giải tích) mới độc lập với chuyện đó.

## Vướng mắc — cần A

1. **"7 model" ở mục 13 so với 8 dòng ở mục 11.** `protocol.md` mục 13 ghi *"3 môi
   trường x 7 model x 3 horizon"* nhưng mục 11 liệt kê tám model. B chạy và báo cả tám.
   Cần sửa một trong hai mục cho khớp.
2. **Lưới siêu tham số không có trong giao thức.** Mục 11 liệt kê model nhưng không chốt
   lưới. B chọn theo chi phí đo được và khai báo ở `registry.py`; nếu A muốn lưới khác
   thì phải chạy lại Bước 5. Riêng **RF chạy 50 cây** là chỗ đáng cân nhắc nhất.
3. **SVR thắng trên Bitbrains — có nên tin?** SVR học từ 10.000 dòng mà cho MAE gộp thấp
   nhất ở cả sáu tổ hợp E1/E2, trong khi XGBoost học từ 1,4 triệu dòng lại thua. Cơ chế
   đọc được là hàm mất mát: SVR dùng `epsilon`-insensitive (`epsilon = 0,1` mặc định)
   nên bỏ qua sai số nhỏ hơn 0,1 — mà trung vị tải của E1/E2 chỉ quanh 1–2%. Đây là lợi
   thế **của hàm mất mát**, không phải của họ kernel, và nó biến mất ở E3 nơi tải cao
   hơn nhiều. Nhưng sau khi sửa hướng Wilcoxon thì lợi thế ấy **chỉ còn có ý nghĩa
   thống kê ở E2 `h = 6` và `h = 12`**. A nên quyết có đưa `epsilon` vào lưới không.
4. **Chưa làm:** LSTM/GRU (mục 11 ghi ngoài scope chính).

## Việc tiếp theo

- [x] A chốt con số model ở mục 13 — **QĐ-015**: 7 là đếm *số dòng bảng* ở mục 11,
      dòng "Linear Regression, Ridge" chứa hai model. Sửa mục 13 thành `3 × 8 × 3 = 72`
- [x] A duyệt lưới siêu tham số và mức 50 cây của RF — **QĐ-015**: khai báo lưới đã
      dùng, **không chạy lại**; nới lưới sau khi đã thấy ML thua là cùng họ với điều
      mục 17 cam kết không làm. Hạn chế vào Limitations
- [ ] GĐ4 — Thí nghiệm B, ba chế độ chuẩn hoá (mục 14). **Cổng đã MỞ 2026-09-11**:
      QĐ-016 chốt năm quy ước, `gate-gd4.md` + `brief-gd4-b.md` + `reference_gd4.py`
      đã có. Còn thiếu `check_gd4.py`, A làm trước khi B nộp

## File sinh ra

| Đường dẫn | Mô tả |
|---|---|
| `src/cwp/evaluation/splits.py` | chia tập theo bucket, purge, rolling-origin 5 fold |
| `src/cwp/evaluation/metrics.py` | năm chỉ số QĐ-013, gộp bằng trung vị theo chuỗi |
| `src/cwp/evaluation/tang.py` | ba tầng burstiness, ngưỡng tính lại từ `cv_gd2.csv` |
| `src/cwp/models/baselines.py` | ba baseline mục 11 |
| `src/cwp/models/registry.py` | năm model ML và lưới siêu tham số đã khai báo |
| `scripts/run_baselines.py` | sinh `splits_gd3.csv` và `baselines_gd3.csv` |
| `scripts/run_experiments.py` | Thí nghiệm A, tám model |
| `scripts/fig_gd3_results.py` | phân tầng + Wilcoxon + 10 panel hình |
| `scripts/pha_gd3.py` | phá code kiểm ngược, năm kiểu |
| `tests/test_splits.py` · `test_metrics.py` · `test_baselines.py` · `test_tang.py` | 54 + 31 + 17 + 15 test |
| `results/tables/splits_gd3.csv` | 27 dòng, số dòng mỗi tập |
| `results/tables/baselines_gd3.csv` | 405 dòng, ba baseline × ba tập × năm chỉ số |
| `results/tables/experiments_gd3.csv` | 360 dòng, tám model trên test |
| `results/tables/per_series_gd3.csv` | 36.816 dòng, chỉ số theo từng chuỗi |
| `results/tables/cv_search_gd3.csv` | điểm validation từng ứng viên, từng fold |
| `results/tables/chosen_gd3.csv` | siêu tham số đã chốt, kèm thời gian chạy |
| `results/tables/tang_gd3.csv` | chỉ số tách theo ba tầng, kèm `ti_le_cham_chan` |
| `results/tables/wilcoxon_gd3.csv` | mọi cặp model, Wilcoxon + Holm–Bonferroni |
| `results/tables/ml_vs_naive_gd3.csv` | trả lời RQ1, một dòng mỗi (env, h, model) |
| `results/figures/gd3/` | 10 panel `.png` và `gd3_ket-qua.pdf` |
