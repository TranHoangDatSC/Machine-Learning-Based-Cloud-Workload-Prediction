# Báo cáo: sửa lỗi P0, kiểm tra tính đúng và ngân sách chạy v5

Ngày: 20/09/2026. Máy chạy: 12 nhân CPU, không có GPU NVIDIA.

Tài liệu thiết kế: `dinh-huong-v5-va-thiet-ke-thuc-nghiem.md`. Báo cáo này ghi phần đã sửa, số đo thực tế và ngân sách đề nghị. **Chưa khởi chạy thí nghiệm dài nào.**

> **Cập nhật 23/09/2026.** Ba lựa chọn đã chốt và phần mã đã hoàn thiện, bàn giao. Ngân sách ở mục 5 dưới đây là bản ngày 20/09; bản mới hơn, tính theo phạm vi đã chốt và có thêm phần độ nhạy, K = 0 và Random Forest, nằm ở `CWP-Cloud-Notebooks/HUONG_DAN_CHAY_V5.md`. Quy ước thực nghiệm khoá ở `CWP-Cloud-Notebooks/PROTOCOL_V5.md`.

---

## 1. Phần đã sửa

Mọi thay đổi nằm trong `CWP-Cloud-Notebooks`. Kết quả v4 giữ nguyên tại `results/ket_qua_chay_goc/` và `results/tables/`; dữ liệu đã xử lý của v4 sao lưu sang `data/v4_backup/` trước khi sinh lại.

| Mã | Việc | Tệp và hàm | Thay đổi hành vi |
|---|---|---|---|
| P0-1 | Seasonal naïve lấy y(t+h−288) thay cho y(t−288) | `src/cwp/models/baselines.py`: `du_doan_seasonal` nhận thêm `h`, khoá tra cứu thành `bucket + h − 288`; `du_doan` bắt buộc có `h` | Mốc so sánh theo chu kỳ ngày nhắm đúng thời điểm cần dự báo |
| P0-2 | Trung bình trượt gồm cả điểm hiện tại | `baselines.py`: `du_doan_ma6` tính `roll_mean_6 + (lag_0 − lag_6)/6` | Mốc trung bình trượt dùng y(t−5) đến y(t) thay vì y(t−6) đến y(t−1) |
| P0-3 | Thêm đặc trưng y(t) | `src/cwp/features/spec.py`: `LAGS` thêm 0, `FEATURE_COLS` 19 → 20, `MATRIX_COLS` 22 → 23; `src/cwp/features/windows.py`: `add_lag_features` | Mô hình cây nhìn thấy y(t) trực tiếp, trước đây phải dựng lại qua tổng `lag_1 + diff_1` |
| P0-4 | Lọc chuỗi chỉ dùng phần train | `src/cwp/preprocess/filter.py`: `judge` nhận `n_train`; `src/cwp/preprocess/build.py`: thêm `doc_n_train`, hai lượt gọi `judge(..., n_train=1612)`, catalog thêm cột `mean_train` | Quyết định chọn quần thể không dùng dữ liệu validation và test |
| P0-5 | Tầng độ giật tính trên phần train | `src/cwp/evaluation/tang.py`: thêm `bang_cv` và hằng `COT_TANG = "cv_train"`, `gan_tang` đổi sang cột đó; `scripts/fig_burstiness.py` và `scripts/build_may_gia.py` gọi chung một hàm | Mẫu con của SVR không còn phân tầng theo thống kê có chứa phần test |
| P0-6 | Lưu dự đoán từng dòng | `src/cwp/evaluation/luu_du_doan.py` (mới); `scripts/run_experiments.py` gọi khi chấm test | Mỗi lần chấm ghi một tệp parquet 14 cột, xem mục 1.1 |
| P0-7 | Đo nội suy ở cả ba vị trí | `scripts/check_dac_trung_va_baseline.py`, phép kiểm K10 | Báo cả tỉ lệ dòng có điểm nội suy trong cửa sổ đặc trưng, không chỉ ở y(t) |
| P1-1 | Biến thể XGBoost dùng hàm mất mát tuyệt đối | `src/cwp/models/registry.py`: thêm `xgb_mae` (`objective="reg:absoluteerror"`), `ModelSpec` thêm trường `loss`, `ML_NAMES` thêm một tên | `xgb` và `xgb_mae` khác nhau đúng một tham số, tạo thành lưới hai hàm mất mát |

Ngoài danh sách trên, hai sửa chữa phát sinh trong lúc làm, ghi ở mục 4.

### 1.1 Lược đồ tệp dự đoán

`runs/<timestamp>/du_doan/<nguồn>-<đích>_<mode>_<lịch>_<model>_<loss>_h<h>_<fold>.parquet`, mỗi tệp 14 cột:

```
nguon, dich, mode, lich, model, loss, h, fold, seed,
series_id, bucket_phat, bucket_muc_tieu, y, yhat
```

`bucket × 300` là số giây: với E1 và E2 là epoch UTC thật, với E3 là giây kể từ đầu trace. Quy ước đó ghi trong `meta.json` của từng lần chạy, cùng cấu hình, phiên bản thư viện và mã commit.

Đã chạy thử đường ghi bằng một lượt ba mô hình cơ sở trên E2 h = 1: ba tệp, 104.492 dòng mỗi tệp, tổng 1,4 MB. Suy ra cho TN-A đầy đủ, khoảng 160 tệp và **dưới 200 MB**.

### 1.2 Hai bảng đầu vào phải sinh lại

- `results/tables/cv.csv` đã sinh lại, nay có thêm `mean_train`, `std_train`, `n_diem_train` và `cv_train`. Bản v4 của toàn bộ `results/tables/` đã sao lưu sang `results/v4_tables/` trước khi ghi đè, vì các bảng đó dẫn xuất từ dữ liệu đã xử lý của v4 và không còn khớp quần thể mới.
- Trung vị `cv_train` so với `cv`: E1 0,490 so với 0,476; E2 0,496 so với 0,533; E3 0,275 so với 0,285. Tầng độ giật vì vậy có xê dịch, và mẫu con của SVR sẽ khác bản v4.

### 1.3 Hai điều cố ý chưa làm

- **Hàm mất mát tuyệt đối cho Ridge và SVR:** không thêm. Hai mô hình giữ đúng hàm mất mát của chúng, nên chúng không phải hai ô tương đương trong lưới hai hàm mất mát. Lưới chỉ gồm `xgb` và `xgb_mae`.
- **Cửa sổ và ranh giới theo tham số (P1-2):** chưa làm, vì chỉ cần cho TN-B. `src/cwp/evaluation/splits.py` vẫn ghi cứng 2.304 bucket và hai câu lệnh assert cho mốc 1.612 và 1.957.

---

## 2. Kết quả kiểm tra

### 2.1 Bộ kiểm tra tính đúng

`scripts/check_dac_trung_va_baseline.py` chạy trên E2 với ba tầm dự báo: **32/32 phép kiểm đạt**.

| Mã | Phép kiểm | Kết quả |
|---|---|---|
| K01 | Schema 23 cột đúng thứ tự | đạt, 678.492 dòng ở h = 1 |
| K02 | lag_0 = lag_1 + diff_1 | lệch tối đa 1,4·10⁻¹⁴ |
| K03 | lag_0 = y(t) đọc từ `data/processed/` | lệch 0 |
| K04 | naïve = y(t) | lệch 0 |
| K05 | ma6 = trung bình y[t−5 .. t] | lệch tối đa 4,3·10⁻¹⁴ |
| K06 | seasonal = y(t+h−288) | lệch 0; 0,00% dòng test thiếu giá trị đó |
| K07 | target = y(t+h) | lệch 0 |
| K08 | 20 đặc trưng dựng lại được từ riêng y[.. t] | 200 dòng mẫu mỗi tầm, lệch tối đa 2,7·10⁻⁹ |
| K09 | Ba tập rời nhau, luật purge đúng | đạt; h = 1 loại 604 dòng, h = 12 loại 7.248 dòng |
| K10 | Tỉ lệ dòng test chạm giá trị nội suy | xem mục 2.2 |
| K11 | Mẫu số MASE tính trên riêng phần train | lệch 0 trên 302 chuỗi |
| K12 | Mọi chuỗi đang giữ qua được bộ lọc train | đạt |

K08 là phép kiểm rò rỉ: chuỗi bị cắt cụt ngay tại `t` rồi sinh lại đặc trưng, nên nếu một đặc trưng chạm `y` sau `t` thì hai bản lệch nhau. Mức lệch còn lại là sai số làm tròn của phép lăn cửa sổ.

### 2.2 Nội suy: con số đầy đủ thay cho con số cũ

Báo cáo rà soát trước chỉ đo tỉ lệ y(t) là giá trị nội suy. Đo lại ở cả ba vị trí trên E2:

| Vị trí | E1 | E2 | E3 |
|---|---|---|---|
| y(t) là giá trị nội suy | 0,040 – 0,041% | 0,022 – 0,023% | 0,000% |
| y(t+h), tức nhãn, là giá trị nội suy | 0,040 – 0,041% | 0,022 – 0,023% | 0,000% |
| **có ít nhất một điểm nội suy trong cửa sổ [t−24, t]** | **0,853 – 0,891%** | **0,550 – 0,568%** | **0,000%** |

Khoảng giá trị là qua ba tầm dự báo. Con số thứ ba lớn gấp 22 lần con số cũ ở E1 và 25 lần ở E2; E3 không có dòng test nào chạm giá trị nội suy. Vẫn nhỏ, nhưng cách nói "không đáng kể" phải dựa trên con số thứ ba. Bản đối chứng không nội suy, tức K = 0, chưa chạy.

Tỉ lệ dòng test mà seasonal naïve không có giá trị tương ứng: 0,00% ở E1 và E2, 0,13 – 0,14% ở E3.

### 2.3 Bộ lọc nhân quả đổi quần thể thế nào

| Môi trường | Quần thể v4 | Quần thể v5 | Thay đổi |
|---|---|---|---|
| E1 | 735 chuỗi | **708 chuỗi** | loại thêm 27; lý do loại: ngoài cửa sổ 61, gần như tắt 459, ít dòng 22 |
| E2 | 302 chuỗi | **302 chuỗi** | cùng số lượng nhưng **khác 2 chuỗi**: 2 chuỗi bị loại, 2 chuỗi khác được nhận |
| E3 | 498 chuỗi | **487 chuỗi** | loại thêm 11, tất cả vì gần như tắt trong phần train |

Cả ba môi trường chạy lại xong, và bộ kiểm tra đạt toàn bộ trên cả ba: 32/32 ở E1, 32/32 ở E2, 32/32 ở E3.

Số dòng huấn luyện ở h = 1 theo quần thể mới: E1 1.122.106, E2 469.508, E3 583.671.

Sau khi lọc theo phần train, E2 không còn chuỗi nào có CPU trung bình phần train dưới 1%. Một chuỗi có trung bình cả cửa sổ 0,981% nhưng trung bình phần train 1,003% nên được giữ, đúng như quy tắc mới mô tả.

---

## 3. Chạy thử để đo chi phí

Tất cả chạy trên **E2, h = 1**, huấn luyện trên train `[0, 1612)`, chấm trên validation `[1612, 1957)`. **Không chạm tập test.** Mỗi mô hình một cấu hình cố định, không dò siêu tham số, không kiểm định. Các con số sai số dưới đây là **số đo thăm dò trên dữ liệu phát triển**, không phải kết quả của đề tài.

### 3.1 XGBoost: hai hàm mất mát

469.508 dòng huấn luyện, 20 đặc trưng, cấu hình `max_depth = 8`, `n_estimators = 300`.

| Mô hình | Hàm mất mát | Thời gian khớp | Thời gian dự đoán | MAE trung vị trên validation | RMSE trung vị |
|---|---|---|---|---|---|
| naïve | không có | 0 | 0 | 0,3589 | 0,8665 |
| `xgb` | bình phương | 14,0 s | 0,13 s | 0,3866 | 0,7544 |
| `xgb_mae` | tuyệt đối | 40,5 s | 0,15 s | **0,3202** | 0,8075 |

Đổi hàm mất mát làm MAE giảm 17% so với bản bình phương và thấp hơn naïve 11%, trong khi RMSE đi ngược lại. Đây là một điểm đo trên một môi trường, một tầm dự báo, một cấu hình, chưa có kiểm định; nó cho thấy lưới hai hàm mất mát của TN-A đáng chạy, chứ chưa kết luận gì.

Ba ứng viên của lưới đều được đo, để ngân sách không phải dựa vào giả định:

| Ứng viên | `xgb`, bình phương | `xgb_mae`, tuyệt đối | Tỉ lệ |
|---|---|---|---|
| `max_depth` 4, 300 cây | 8,2 s | 66,7 s | 8,1 |
| `max_depth` 8, 300 cây | 9,2 s | 69,6 s | 7,6 |
| `max_depth` 8, 600 cây | 19,1 s | 139,4 s | 7,3 |
| **Tổng ba ứng viên** | **36,5 s** | **275,7 s** | **7,6** |

Hàm mất mát tuyệt đối đắt hơn khoảng 7,6 lần, không phải 2,9 lần như lần đo đầu. Lần đo đầu cho `max_depth` 8, 300 cây là 40,5 s, lần sau là 69,6 s trên cùng dữ liệu và cùng máy, tức có dao động khoảng 1,7 lần giữa hai lần chạy. Ngân sách dưới đây lấy con số lớn hơn.

### 3.2 DLinear và GRU

Cửa sổ đầu vào 288 bước, chuẩn hoá theo từng cửa sổ, hàm mất mát tuyệt đối, batch 1.024, Adam lr 10⁻³, 10 luồng CPU.

| | DLinear | GRU (32 đơn vị ẩn) |
|---|---|---|
| Số tham số | 578 | 3.393 |
| Thời gian mỗi epoch | **3,5 s** | **1.220 s** (đo 30/303 batch trong 120,8 s rồi suy ra) |
| Thời gian dự đoán validation | 0,9 s | 13,8 s |
| MAE trung vị sau 2 epoch | 0,3621 | 0,4343 (mới 30 batch, chưa học xong) |

Mốc naïve trên **đúng tập mẫu đó** là 0,3589.

Hai điều rút ra:

- **DLinear rẻ**, khoảng 350 lần rẻ hơn GRU ở cùng cửa sổ đầu vào, nên đưa vào lưới chính được.
- **GRU không vào lưới chính được.** 1.220 giây mỗi epoch là trên môi trường **nhỏ nhất**; nhân 30 epoch, 3 môi trường, 3 tầm dự báo và 2 chế độ chuẩn hoá thì ra khoảng 287 giờ. Ba lối xử lý ở mục 5.

### 3.3 Cửa sổ 288 bước làm mất bao nhiêu mẫu

| | Mô hình bảng (cửa sổ 25 điểm) | Mô hình chuỗi (cửa sổ 288 điểm) |
|---|---|---|
| Mẫu huấn luyện E2 h = 1 | 469.508 | 310.170, còn 66% |
| Mẫu validation E2 h = 1 | 103.888 | 103.588, còn 99,7% |

Chênh lệch nằm ở phần huấn luyện, vì đầu cửa sổ 8 ngày không đủ 288 điểm lịch sử. Hệ quả cho thiết kế: **tập dòng được chấm phải lấy giao của hai bên** để mọi mô hình chấm trên đúng cùng một tập, và tỉ lệ dòng bị bỏ phải báo trong bài.

### 3.4 Thời gian các bước một lần

| Bước | Thời gian đo được |
|---|---|
| Tiền xử lý E2, 500 tệp | 39 s |
| Tiền xử lý E1, 1.250 tệp | 110 s |
| Tiền xử lý E3, quét tệp 9 GB | 148 s |
| Sinh đặc trưng E2, ba tầm dự báo, một chế độ | 10 s |
| Sinh đặc trưng E1, ba tầm dự báo, một chế độ | 21 s cho N0, 25 s cho N1 |
| Sinh đặc trưng E3, ba tầm dự báo, một chế độ | 15 s cho N0, 17 s cho N1 |
| Bộ kiểm tra tính đúng, một môi trường, ba tầm dự báo | dưới 2 phút |

Toàn bộ các bước trên **đã chạy xong** cho cả ba môi trường, tổng cộng dưới 12 phút. Dữ liệu đã xử lý và ma trận đặc trưng của v5 hiện có đủ cho N0 và N1.

---

## 4. Hai lỗi môi trường phát hiện trong lúc làm

**Gói `cwp` trỏ nhầm repo.** `.venv` cài `cwp` ở chế độ editable trỏ về `ML-CWP-Cloud/src`. Bảy script của repo public không tự chèn `src` của chính nó vào đường dẫn tìm kiếm, nên khi chạy bằng môi trường đó, chúng dùng mã của repo nháp chứ không phải mã đang sửa: `build_features.py`, `fig_acf.py`, `fig_burstiness.py`, `fig_target_dist.py`, `fig_tn1.py`, `run_baselines.py`, `run_experiments.py`. Đã thêm `sys.path.insert(0, ROOT/"src")` trước các lệnh import `cwp`, giống 19 script còn lại. Phạm vi ảnh hưởng: **chỉ các lượt chạy khởi động từ repo public**. Notebook không dính, vì `notebooks/tien_ich.py` tự chèn đường dẫn. Kết quả gốc của v4 sinh ra từ repo nháp nên không sai lệch; rủi ro nằm ở các lượt chạy v5 nếu không sửa.

**Thứ tự import của torch.** Trên máy này, import `numpy` hoặc `pandas` trước `torch` làm hỏng nạp `c10.dll` với lỗi WinError 1114. Mọi script học sâu phải import `torch` trước. Môi trường học sâu để riêng tại `D:\Research 2026\.venv-dl` (torch 2.14.0+cpu, numpy 2.1.3, pandas 2.2.3), không đụng `requirements.txt` đang ghim.

---

## 5. Ngân sách đề nghị

### 5.1 Cách tính

Chi phí mô hình cây suy từ số đo ở mục 3.1 theo công thức:

```
chi phí một (môi trường, tầm dự báo, chế độ)
    = tổng ba ứng viên × 5 fold × 1,09   (dò siêu tham số bằng rolling-origin)
    + 1,21 × chi phí ứng viên được chọn  (khớp mô hình cuối trên train + validation)
```

Hai hệ số 1,09 và 1,21 là tỉ lệ độ dài vùng huấn luyện của một fold và của lần khớp cuối so với vùng train. Chi phí khớp coi như tỉ lệ thuận với số dòng; hệ số theo môi trường lấy từ **số dòng train của quần thể mới**: E1 gấp 2,39 lần E2, E3 gấp 1,24 lần E2, tổng ba môi trường là 4,63 lần E2.

Giả định duy nhất còn lại là tính tỉ lệ thuận theo số dòng. Chi phí từng ứng viên đã đo thật, không còn ước theo độ sâu và số cây.

Hai con số thời gian được phân biệt ở mọi bảng:

- **Giờ máy cộng dồn**: tổng thời gian tính toán của mọi lượt chạy.
- **Giờ chờ**: thời gian thực tế từ lúc bắt đầu tới lúc xong.

Trên máy này hai con số xấp xỉ nhau, vì XGBoost đặt `n_jobs = -1` và DLinear dùng 10 luồng, tức mỗi lượt đã chiếm gần hết 12 nhân. Chạy song song nhiều lượt không rút ngắn được đáng kể.

Ghi chú về seed và fold: mọi con số dưới đây **đã gồm** 5 fold của bước dò siêu tham số và lần khớp cuối. Mô hình cây và Ridge cố định `random_state = 42` nên chạy **một seed**; DLinear phụ thuộc khởi tạo ngẫu nhiên nên chạy **ba seed** và báo kèm độ phân tán.

### 5.2 TN-A, lưới chính

Phạm vi: 3 môi trường × 3 tầm dự báo × 2 chế độ chuẩn hoá N0 và N1.

| Thành phần | Dò siêu tham số | Seed | Giờ máy cộng dồn |
|---|---|---|---|
| Ba mô hình cơ sở | không có siêu tham số | không ngẫu nhiên | dưới 0,1 |
| Ridge, 5 ứng viên | có, 5 fold | 1 | 0,1 |
| `xgb`, 3 ứng viên | có, 5 fold | 1 | **1,6** |
| `xgb_mae`, 3 ứng viên | có, 5 fold | 1 | **12,2** |
| SVR, 2 ứng viên, mẫu con 10.000 dòng | có, 5 fold | 1 | 2,5 |
| SVR, kiểm độ nhạy cỡ mẫu 30.000 dòng, chỉ N0 và h = 1 | không | 1 | 0,5 |
| DLinear, 30 epoch, dừng sớm theo validation | một cấu hình | 3 | 2,4 |
| **Tổng** | | | **19,3** |

`xgb_mae` chiếm 63% ngân sách TN-A, vì hàm mất mát tuyệt đối đắt hơn 7,6 lần. Ba cách thu gọn:

| Phương án | Nội dung | `xgb` + `xgb_mae` | Tổng TN-A |
|---|---|---|---|
| A. Như thiết kế | 3 ứng viên cho cả hai hàm mất mát | 13,8 | 19,3 |
| **B. Lưới hai ứng viên** | Bỏ ứng viên 600 cây ở **cả hai** hàm mất mát, giữ độ sâu 4 và 8 với 300 cây | 7,2 | **12,7** |
| C. Dừng sớm | Một lần khớp mỗi độ sâu, số cây do validation quyết định; cần khoảng 1 giờ viết mã và sửa `do_lua_chon` | chưa đo, dự kiến thấp hơn B | chưa đo |

Phương án B giữ lưới **giống hệt nhau giữa hai hàm mất mát**, nên phép so vẫn sạch; cái mất là khả năng chọn 600 cây, vốn được chọn ở một ô của lần chạy v4. Đề nghị chọn B, và ghi trong bài rằng lưới đã bị thu gọn vì chi phí.

### 5.3 GRU, bốn lối

| Lối | Phạm vi | Giờ máy cộng dồn |
|---|---|---|
| A. Vào lưới chính, cửa sổ 288 | 3 môi trường × 3 tầm × 2 chế độ | khoảng 283, **không khả thi** |
| B. Cửa sổ 48 bước, vào lưới chính | như trên | khoảng 47 |
| C. Phạm vi hẹp tại chỗ: E2, h = 1 và 12, chỉ N1, cửa sổ 288 | 2 tổ hợp | khoảng 20 |
| D. **Phạm vi hẹp trên Colab dùng GPU** | 4 tổ hợp | 1 đến 2 giờ chờ, không tốn máy ở đây |

Đề nghị lối D. Lý do giữ GRU ở phạm vi hẹp: mạng hồi tiếp không phải trọng tâm của đề tài, Christofidi đã khảo sát LSTM, và vai trò của GRU ở đây chỉ là một điểm đối chứng cho nhóm mô hình chuỗi.

### 5.4 Các bước một lần và TN-C

| Hạng mục | Trạng thái | Giờ máy cộng dồn |
|---|---|---|
| Tiền xử lý ba môi trường | **đã chạy** | 0,08 |
| Sinh đặc trưng ba môi trường, N0 và N1 | **đã chạy** | 0,03 |
| Bộ kiểm tra tính đúng ba môi trường | **đã chạy** | 0,1 |
| Bản đối chứng không nội suy, K = 0 | chưa | 0,3 |
| TN-C chuyển giao: 6 chiều × 2 chế độ × 3 mô hình × 3 tầm | chưa | 3,0 |
| Thí nghiệm máy giả trên pipeline đã sửa | chưa | 1,0 |
| Kiểm tra Random Forest phạm vi hẹp, cấu hình định trước | chưa | 1,5 |
| **Còn phải chạy** | | **5,8** |

### 5.5 TN-B

Chưa ước lượng được, vì `splits.py` chưa nhận cửa sổ theo tham số và chi phí phụ thuộc số lần huấn luyện lại. Ước lượng thô theo số dòng: E1 đủ 30 ngày gấp khoảng 3,75 lần cửa sổ 8 ngày; với bộ mô hình rút gọn và huấn luyện lại mỗi 7 ngày, rơi vào khoảng **10 đến 20 giờ máy**. Con số này **chưa đo**, chỉ để cân nhắc. Sau khi làm P1-2 sẽ đo một cửa sổ rồi nhân lên.

### 5.6 Tổng hợp

| Khối | Giờ máy cộng dồn | Giờ chờ |
|---|---|---|
| TN-A theo phương án A | 19,3 | khoảng 20 |
| **TN-A theo phương án B** | **12,7** | **khoảng 13** |
| Các bước một lần còn lại và TN-C | 5,8 | khoảng 6 |
| GRU theo lối D | không tốn máy tại chỗ | 1 đến 2 |
| **Cộng theo phương án B, chưa tính TN-B** | **18,5** | **khoảng 19** |
| TN-B, ước lượng thô chưa đo | 10 đến 20 | tương đương |

So với v4 đã đo 33,26 giờ, phần chính của v5 rẻ hơn, chủ yếu vì bỏ Random Forest khỏi lưới chính.

---

## 6. Việc chưa làm và chỗ cần bạn duyệt

**Đã làm xong trong lượt này:** sửa bảy lỗi P0 cộng một hạng mục P1, viết bộ kiểm tra 12 phép kiểm, chạy lại tiền xử lý và sinh đặc trưng cho cả ba môi trường ở N0 và N1, chạy bộ kiểm tra trên cả ba, đo chi phí XGBoost hai hàm mất mát đủ ba ứng viên, đo DLinear và GRU. Tổng thời gian máy đã dùng khoảng 0,4 giờ.

**Chưa chạy, chờ bạn duyệt ngân sách:** TN-A, TN-B, TN-C, thí nghiệm máy giả, kiểm tra Random Forest, bản đối chứng K = 0.

**Ba lựa chọn cần bạn chốt:**

| # | Lựa chọn | Đề nghị |
|---|---|---|
| 1 | Lưới XGBoost: phương án A ba ứng viên 19,3 giờ, phương án B hai ứng viên 12,7 giờ, hay phương án C dừng sớm | B, kèm một câu trong bài ghi rõ lưới bị thu gọn vì chi phí |
| 2 | GRU: lối D trên Colab, lối C thu hẹp tại chỗ 20 giờ, hay bỏ và chỉ giữ DLinear | D |
| 3 | Bản đối chứng K = 0 để khép phần nội suy, 0,3 giờ | có chạy |

**Duyệt ngân sách:** theo phương án B và lối D, tổng còn phải chạy là **18,5 giờ máy**, chưa tính TN-B. TN-B ước lượng thô 10 đến 20 giờ và sẽ đo lại sau khi làm P1-2.

**Việc phải làm trước lượt xác nhận, chưa làm:** chốt bằng văn bản có ghi ngày, không sửa về sau, gồm cách chọn siêu tham số, chỉ số dùng để chọn cấu hình, seed, danh sách cửa sổ đánh giá, họ kiểm định và cách hiệu chỉnh nhiều phép kiểm.

**Hai việc kỹ thuật còn nợ:**

- `src/cwp/evaluation/splits.py` vẫn ghi cứng cửa sổ 2.304 bucket. Phải sửa trước TN-B.
- `scripts/run_transfer.py`, `scripts/run_tai_cho_may_gia.py`, `scripts/run_n1_loai_dung_yen.py` và `scripts/run_n2_sua.py` chưa gọi `ghi_du_doan`. Phải nối trước khi chạy TN-C, nếu không thì phần chuyển giao không có dự đoán từng dòng.
- Các tệp `data/features/{env}_N0_h*.parquet` và `{env}_N2_h*.parquet` còn là bản cũ 22 cột. Phải sinh lại hoặc xoá trước khi dùng, để không trộn hai lược đồ.
