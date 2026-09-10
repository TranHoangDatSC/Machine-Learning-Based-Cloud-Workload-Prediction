# Phiếu giao việc GĐ3 — cho B

**Người giao:** A · **Ngày:** 2026-09-10
**Đọc trước:** `docs/protocol.md` mục 9–13, 15, 17 · `research-log/gate-gd3.md`
**Cổng:** `research-log/gate-gd3.md`

Mỗi bước có ba phần: **Prompt** để đưa cho agent, **Lệnh** để chạy, **Phải thấy** để
đối chiếu. Làm xong bước nào chạy lệnh bước đó ngay.

---

## Hai rào chắn, đọc trước khi làm gì

### 1. Đừng code hướng về con số

Số ở phiếu này chỉ để **đối chiếu SAU khi chạy**. Ngày 2026-09-09 đã có một lần
`io/alibaba.py` tự chỉnh mẫu cho tới khi số chuỗi `gan_chet` bằng đúng 1 — đã xoá.

**Dán dòng này vào cuối mọi prompt gửi agent:**

```
Số kỳ vọng trong phiếu chỉ để đối chiếu sau khi chạy. Không viết code điều chỉnh
kết quả cho khớp con số nào. Sai thì sửa cách hiện thực cho đúng đặc tả trong
docs/protocol.md và QĐ-013, không sửa đầu ra.
```

### 2. Rào chắn mới của GĐ3 — đừng ép ML thắng naive

Đây là rào chắn quan trọng hơn ở giai đoạn này, và nó khác hẳn GĐ2.

Nhìn bảng neo ở Bước 3: ở `h = 1`, naive persistence cho MAE **0,4077** trên E1 và
**4,2955** trên E3. Đó là những con số **rất khó vượt** — trên lưới 5 phút, giá trị
5 phút trước là một dự đoán mạnh.

`docs/research-plan.md` GĐ3 viết thẳng: *"Nếu ML không vượt ở `h=1` thì **đó là
finding**, ghi lại và đi tiếp, không được ép model."* Và `protocol.md` mục 17 đã cam
kết *"Không giấu việc baseline naive thắng model ML, nếu điều đó xảy ra."*

**Nếu một model ML bỗng cho MAE thấp hơn hẳn naive ở h=1, phản xạ đầu tiên là nghi rò
rỉ, không phải mừng.** Chạy lại L1 ở gate mục 3.4 trước khi tin.

---

## Bước 0 — Chuẩn bị

```bash
git pull
python -m pip install -e .
python tests/test_env.py
python scripts/check_gd1.py
python scripts/check_gd2.py
pytest tests/ -q
```

**Phải thấy**

```
Khớp: 12/12
ĐẠT — sản phẩm GĐ1 khớp tham chiếu trong ngưỡng cho phép.
ĐẠT — bộ đặc trưng GĐ2 khớp protocol mục 8, không phát hiện rò rỉ.
148 passed, 1 skipped
```

Cả hai cổng phải còn ĐẠT trước khi động vào GĐ3. GĐ3 xây thẳng lên `data/features/`.

> **Không đọc `scripts/reference_gd3.py`.** Đó là thước đo độc lập của A. Nếu agent
> viết code GĐ3 đọc nó thì việc hai bản khớp nhau không chứng minh gì — và đó là cơ
> chế đã bắt được mọi lỗi của dự án từ GĐ1 tới nay. Cũng đừng đọc
> `results/tables/reference_gd3.json` trước khi code chạy xong lần đầu.

---

## Bước 1 — `src/cwp/evaluation/splits.py`

Làm **trước** baseline, vì baseline cần biết tập test là gì.

### Prompt

```
Viết src/cwp/evaluation/splits.py, theo docs/protocol.md mục 9 và QĐ-013 điểm 1-2.

Đầu vào là ma trận đặc trưng data/features/{env}_h{h}.parquet (22 cột, có
series_id và bucket) và horizon h.

QUY ƯỚC BẮT BUỘC, chốt ở QĐ-013:

1. Ranh giới chia tính theo BUCKET, không theo số dòng. Cửa sổ 8 ngày có 2304
   bucket, tính offset so với b0 = bucket nhỏ nhất của môi trường đó:
     train      offset trong [0, 1612)
     validation offset trong [1612, 1957)
     test       offset trong [1957, 2304)
   n_train = floor(0.70*2304) = 1612, n_val = floor(0.15*2304) = 345.

2. Một dòng có gốc t và horizon h thuộc tập S khi CẢ t VÀ t+h đều nằm trong S.
   Dòng vắt qua ranh giới bị LOẠI. Đây là chống rò rỉ: nếu gán theo t thôi thì
   dòng cuối tập train có target rơi vào test, và huấn luyện trên nó là cho model
   nhìn thấy nhãn của tập đánh giá.

3. Tuyệt đối không shuffle.

Thêm một hàm rolling-origin 5 fold trên phần train + validation, cũng purge h dòng
ở mỗi mối nối. Chốt một cách chia và ghi rõ trong docstring; đề xuất: expanding
window, 5 điểm gốc chia đều trên phần validation.

Trả về mặt nạ bool hoặc chỉ số, không trả về bản sao dữ liệu.
```

### Lệnh
```bash
pytest tests/test_splits.py -v
```

### Phải thấy
Test xanh, và **quan trọng hơn**: một phép kiểm khẳng định với mọi dòng train thì
`t + h < 1612`. Không có phép kiểm đó thì chưa đủ.

---

## Bước 2 — `src/cwp/evaluation/metrics.py`

### Prompt

```
Viết src/cwp/evaluation/metrics.py theo docs/protocol.md mục 12 và QĐ-013 điểm 3-5.

Năm chỉ số: MAE, RMSE, SMAPE, MASE, R2. KHÔNG có MAPE (QĐ-006).

Định nghĩa chốt:

- SMAPE = 100 * mean(|y - yhat| / ((|y| + |yhat|) / 2)). Khi |y| + |yhat| = 0 thì
  số hạng đó bằng 0. Chỗ này quan trọng: E1 và E2 có rất nhiều điểm gần 0.

- MASE = MAE / d, với d = trung bình |y_t - y_{t-1}| trên phần TRAIN của chính
  chuỗi đó, chỉ lấy cặp mà cả hai đầu không NaN. d KHÔNG phụ thuộc horizon — cùng
  một d dùng cho cả h = 1, 6, 12. Chuỗi có d = 0 thì MASE không xác định: LOẠI
  chuỗi đó khỏi phần gộp và đếm số chuỗi bị loại. Không thay bằng 0, không thêm
  epsilon.

- R2 = 1 - SS_res/SS_tot, SS_tot tính trên target của chính chuỗi đó trong tập
  đang đánh giá. SS_tot = 0 thì loại chuỗi, cũng đếm.

CÁCH GỘP (QĐ-013 điểm 5): tính chỉ số RIÊNG cho từng chuỗi trước, rồi lấy TRUNG VỊ
và IQR trên tập chuỗi. KHÔNG gộp mọi dòng của mọi chuỗi vào một dãy rồi tính một
chỉ số — cách đó cho chuỗi tải cao chi phối con số gộp.
```

### Lệnh
```bash
pytest tests/test_metrics.py -v
```

### Phải thấy
Test xanh. Bắt buộc có ba ca biên: `|y| + |ŷ| = 0` cho SMAPE ra 0; chuỗi train phẳng
cho MASE là NaN chứ không phải vô cực; chuỗi test hằng cho R² là NaN.

---

## Bước 3 — `src/cwp/models/baselines.py` và bảng baseline

**Đây là bước quan trọng nhất của GĐ3.** Mọi con số về sau đều so với nó.

### Prompt

```
Viết src/cwp/models/baselines.py — ba baseline của docs/protocol.md mục 11:

  naive           yhat = y_t
  moving average  yhat = trung binh y[t-6 .. t-1], cua so 6, KHONG gom diem hien tai
  seasonal naive  yhat = y_{t-288}   (cung gio hom truoc)

Hai cai dau lay thang tu ma tran dac trung: y_t = lag_1 + diff_1, va roll_mean_6.

Cai thu ba KHONG co trong ma tran dac trung — bo 19 dac trung sau nhat chi toi
lag_24. Phai noi nguoc ve data/processed/{env}.parquet theo khoa
(series_id, bucket - 288). Doc protocol muc 11, muc con "Seasonal naive lay gia tri
tu dau", truoc khi lam.

BA DIEU CAM:
- KHONG them lag_288 vao bo dac trung. Them mot dac trung ngoai muc 8 la doi giao
  thuc.
- KHONG siet luat dong hop le thanh t >= b0 + 288. Lam the se doi ca chin neo da
  kiem cheo o GD1 va GD2.
- Dong nao khong co y_{t-288} thi PHAI xu ly hien: bao ti le dong bi bo, va bao
  rieng cho tung baseline. Khong lang le lap gia tri.

Roi viet mot script sinh bang baseline cho ba moi truong x ba horizon, tinh nam
chi so tren tap TEST, ghi ra results/tables/.
```

### Lệnh
```bash
python scripts/run_baselines.py --env all
```

### Phải thấy — MAE trung vị trên test, khớp **tuyệt đối**

| Env | h | naive | moving avg 6 | seasonal naive |
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

Ba baseline **không có yếu tố ngẫu nhiên nào** — không seed, không siêu tham số,
không huấn luyện. Lệch một chữ số là **có lỗi**, không phải nhiễu.

**Số dòng mỗi tập cũng phải khớp tuyệt đối:**

| Env | h | train | validation | test |
|---|---:|---:|---:|---:|
| E1 | 1 | 1.142.276 | 252.840 | 254.310 |
| E1 | 12 | 1.134.191 | 244.755 | 246.225 |
| E2 | 1 | 469.502 | 103.888 | 104.492 |
| E2 | 12 | 464.338 | 100.566 | 101.170 |
| E3 | 1 | 596.549 | 169.675 | 171.716 |
| E3 | 12 | 575.245 | 164.102 | 166.203 |

Đủ chín tổ hợp ở `gate-gd3.md` mục 2.2.

**Kiểm tự thân, làm được bằng đầu:** tổng ba tập phải nhỏ hơn tổng dòng hợp lệ của
GĐ2 đúng `số_chuỗi × 2 × h`. E1 h=12: `1.642.811 − 1.625.171 = 17.640 = 735 × 2 × 12`.
Lệch khác đi thì **nghi quên purge** — và quên purge là rò rỉ.

**Tỉ lệ dòng bị bỏ:** `naive` và `ma6` phải bỏ **0%** ở cả ba môi trường. `seasonal`
bỏ 0% ở E1 và E2, và **0,4251% / 0,4285% / 0,4326%** ở E3 cho h = 1 / 6 / 12.

---

## Bước 4 — Phá code kiểm ngược

Như Bước 2 của GĐ2. Test xanh mà không chứng minh được nó biết đỏ thì chưa phải test.

### Prompt

```
Pha code co chu y roi xac nhan test bat duoc, dong goi thanh
scripts/pha_gd3.py theo khuon scripts/pha_features.py da co.

Nam kieu pha, moi kieu phai lam do dung nhom phep kiem:

  P1 gan tap theo t thoi, khong doi t+h cung tap   -> phep kiem L1 phai do
  P2 bo purge o ranh gioi                          -> so dong khong khop neo
  P3 mau so MASE tinh tren test thay vi train      -> MASE naive lech xa 1
  P4 gop bang trung binh thay vi trung vi          -> chi so lech neo
  P5 seasonal naive lap gia tri thieu bang ffill   -> ti le dong bo thanh 0%

Sao luu truoc, khoi phuc o khoi finally, va in ra test nao bat duoc tung kieu.
```

### Lệnh
```bash
python scripts/pha_gd3.py
```

### Phải thấy
Bản gốc **XANH**, cả năm bản phá **ĐỎ**, và sau khi khôi phục thì `check_gd3.py` vẫn
ĐẠT. Ghi kết quả từng lần phá vào log.

---

## Bước 5 — Bảy model, ba horizon

### Prompt

```
Chay bay model cua protocol muc 11 tren ba moi truong x ba horizon:
Linear Regression, Ridge, Random Forest, XGBoost, SVR RBF, cong hai baseline da co.

Chien luoc: GLOBAL model — mot model hoc tren nhieu chuoi cua cung mot moi truong,
khong phai moi chuoi mot model (muc 11).

Chon sieu tham so CHI TREN VALIDATION, dung rolling-origin 5 fold o Buoc 1.
TEST CHI CHAM MOT LAN, khi da chot toan bo model (muc 9).

Moi lan chay sinh mot thu muc runs/<timestamp>/ chua: snapshot config, seed, phien
ban thu vien, sieu tham so da chon, va ket qua tho.

SVR co the qua cham. Neu phai lay mau con thi mau con PHAI PHAN TANG THEO CV theo
QD-012, khong lay ngau nhien — neu khong thi SVR duoc danh gia tren mot quan the
khac voi sau model kia va bang so sanh mat nghia. Ghi ro cach lay mau.
```

### Lệnh
```bash
python scripts/run_experiments.py --env all
```

### Phải thấy
Bảng kết quả trong `results/tables/`. **Không có số kỳ vọng cho phần này** — đó là
kết quả nghiên cứu, không phải thứ để đối chiếu.

Nhưng có hai dấu hiệu cảnh báo:

- **Model ML thấp hơn hẳn naive ở h=1** → nghi rò rỉ trước, mừng sau. Chạy lại L1.
- **MASE của model xa 1 một cách bất thường** → nghi mẫu số tính sai tập.

---

## Bước 6 — Phân tầng và kiểm định thống kê

### Prompt

```
Tach bang ket qua theo BA TANG BURSTINESS, chia bang tam phan vi CV TRONG TUNG MOI
TRUONG (QD-012, protocol muc 13). Nguong doc tu config/split.yaml, KHONG hardcode.

Moi bang phan tang bao kem cot ti_le_cham_chan tu results/tables/cv_gd2.csv, de
phan biet mot chuoi it bursty do ban chat voi mot chuoi it bursty vi da cung tran
thang do.

CV chi dung de BAO CAO. Khong dung lam dac trung, khong dung lam trong so huan
luyen, khong dung lam tieu chi chon model — cv_gd2.csv tinh tren toan bo cua so 8
ngay nen no biet tuong lai (QD-012 diem 2).

Roi chay kiem dinh Wilcoxon cho chenh lech giua cac model, theo protocol muc 15.
```

### Lệnh
```bash
python scripts/fig_gd3_results.py --env all
```

### Phải thấy
Ngưỡng và số chuỗi mỗi tầng khớp:

| Env | ngưỡng | số chuỗi mỗi tầng |
|---|---|---|
| E1 | 0,256049 / 0,848935 | 245 / 245 / 245 |
| E2 | 0,285320 / 0,943359 | 101 / 100 / 101 |
| E3 | 0,258254 / 0,320560 | 166 / 166 / 166 |

---

## Bước 7 — Log và nghiệm thu

### Prompt

```
Viet research-log/YYYY-MM-DD-gd3-thi-nghiem-a.md theo mau research-log/_template.md.

Phai co:
- Bang 27 con so baseline, kem cot doi chieu voi gate-gd3.md muc 2.3
- Bang so dong moi tap, kem phep kiem tu than n_chuoi x 2 x h
- Ket qua nam lan pha code o Buoc 4
- Tra loi thang: ML co vuot naive khong, o horizon nao, tren moi truong nao
- Cach chia rolling-origin da chot, va cach lay mau con cua SVR neu co
- Cho nao chua chac, cho nao phai hoi A

Khong viet "da hoan thanh" cho muc nao chua chay duoc lenh kiem.
```

### Lệnh
```bash
python scripts/check_gd3.py
pytest tests/ -v
```

### Phải thấy
```
ĐẠT — bộ máy đánh giá và ba baseline GĐ3 khớp tham chiếu.
```

Chưa ĐẠT thì **đừng báo xong**.

> `check_gd3.py` do A viết, chưa có lúc phiếu này phát hành. Hỏi A nếu tới Bước 7 mà
> vẫn chưa có.

---

## Tóm tắt thứ tự

| Bước | Việc | Phụ thuộc |
|---|---|---|
| 0 | Hai cổng cũ còn ĐẠT | — |
| 1 | `splits.py` — chia theo bucket, purge dòng vắt ranh giới | — |
| 2 | `metrics.py` — năm chỉ số theo QĐ-013 | — |
| 3 | **`baselines.py` + bảng baseline, khớp 27 con số** | 1, 2 |
| 4 | Phá code kiểm ngược, 5 kiểu | 1, 2, 3 |
| 5 | Bảy model × ba horizon | 1, 2, 3 |
| 6 | Phân tầng + Wilcoxon | 5 |
| 7 | Log + `check_gd3.py` | tất cả |

Bước 3 là chỗ nặng nhất và cũng là chỗ cổng kiểm gắt nhất. Vướng quá 2 giờ thì dừng
và hỏi A.
