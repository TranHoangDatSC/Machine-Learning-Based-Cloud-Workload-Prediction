# Phiếu giao việc GĐ4 — cho B

**Người giao:** A · **Ngày:** 2026-09-11
**Đọc trước:** `docs/giai-thich-chuan-hoa.md` **toàn bộ** · `docs/protocol.md` mục 14,
9, 12 · `docs/decisions.md` QĐ-016 · `research-log/gate-gd4.md`
**Cổng:** `research-log/gate-gd4.md`

Mỗi bước có ba phần: **Prompt** để đưa cho agent, **Lệnh** để chạy, **Phải thấy** để
đối chiếu. Làm xong bước nào chạy lệnh bước đó ngay.

---

## Hai rào chắn, đọc trước khi làm gì

### 1. Đừng code hướng về con số

**Dán dòng này vào cuối mọi prompt gửi agent:**

```
Số kỳ vọng trong phiếu chỉ để đối chiếu sau khi chạy. Không viết code điều chỉnh
kết quả cho khớp con số nào. Sai thì sửa cách hiện thực cho đúng đặc tả trong
docs/protocol.md và QĐ-016, không sửa đầu ra.
```

### 2. Rào chắn của GĐ4 — chuẩn hoá sai thì số ĐẸP LÊN, không đỏ

Đây là rào chắn khác hẳn ba giai đoạn trước, và là lý do GĐ4 được gọi là *"chỗ dễ sai
nhất toàn dự án"*.

GĐ2 sợ rò rỉ đặc trưng — test bắt được. GĐ3 sợ áp lực để ML thắng naive — neo bắt được.
**GĐ4 sợ rò rỉ qua bước chuẩn hoá, thứ không làm chương trình báo lỗi, chỉ làm số liệu
tốt lên.**

`giai-thich-chuan-hoa.md` mục 5 cho sẵn dấu hiệu nhận biết:

> Nếu **N0 không thất bại nặng** ở cặp Bitbrains và Alibaba thì gần như chắc chắn có rò
> rỉ ở đâu đó — dừng lại truy nguyên, đừng đi tiếp.

`gate-gd4.md` mục 2.5 định lượng "nặng": một **hằng số** cho MAE **28,24** ở E1→E3 và
**35,98** ở E3→E1. Model N0 nào ra số quanh đó thì **không chứng minh gì**.

**Phản xạ đúng: N1 hoặc N2 bỗng tốt lên nhiều thì nghi rò rỉ trước, mừng sau.** Chạy
lại ba bất biến ở Bước 1 trước khi tin.

---

## Bước 0 — Chuẩn bị và hợp đồng tên tệp

```bash
git pull
python -m pip install -e .
python scripts/check_gd1.py && python scripts/check_gd2.py && python scripts/check_gd3.py
pytest tests/ -q
```

**Phải thấy** ba dòng ĐẠT và `295 passed, 1 skipped` (277 của GĐ3 cộng 18 test
của `check_gd4.py`). Cả ba cổng cũ phải còn ĐẠT trước
khi động vào GĐ4.

**Hợp đồng tên tệp — chốt ở đây, `check_gd4.py` đọc theo đúng tên này:**

| Tệp | Cột |
|---|---|
| `data/features/{env}_{mode}_h{h}.parquet` | 22 cột như GĐ2, giá trị đã biến đổi |
| `results/tables/normalize_gd4.csv` | `env, mode, series_id, mu, sd, n_dong_train` |
| `results/tables/transfer_gd4.csv` | `nguon, dich, mode, lich, h, model, metric, p25, p50, p75, iqr, n_chuoi, n_loai, n_dong_test` |
| `results/tables/invariants_gd4.csv` | `env, bat_bien, lech_toi_da, nguong, dat` |

`mode` nhận `N0 \| N1 \| N2`; `lich` nhận `co \| khong` (biến thể có/không 4 đặc trưng
lịch, mục 8 đòi riêng cho TN-B).

### Bốn tệp KHÔNG được đọc

Đây là điều kiện để loại A của cổng GĐ4 còn giá trị. Cơ chế thước đo độc lập đã bắt
được **mọi** lỗi của dự án — và ba lần liền lỗi nằm ở phía A, nên nó bảo vệ cả hai bên.

| Tệp | Vì sao |
|---|---|
| `scripts/reference_gd4.py` | thước đo độc lập của A |
| `results/tables/reference_gd4.json` | đáp án — mở được **sau** khi code chạy xong lần đầu |
| `scripts/_moi_normalize_gd4.py` | **một bản `normalize.py` đúng, trọn vẹn** |
| `scripts/check_gd4.py` | **chạy thoải mái, đừng ĐỌC** — loại C của nó chỉ ra cách kiểm |

Chỗ cuối cần phân biệt rõ: **chạy `check_gd4.py` là việc bạn được khuyến khích làm liên
tục**, ngay từ Bước 1. Chỉ đừng mở mã nguồn của nó ra đọc, vì loại C bày sẵn cách dựng
ba bất biến — mà dựng được ba bất biến đúng là một phần bài tập.

`scripts/_moi_normalize_gd4.py` là chỗ dễ vấp nhất: nó nằm trong `scripts/` và `pytest`
có chạm tới nó. Nó có banner cảnh báo ở dòng đầu. Thấy banner thì đóng lại.

---

## Bước 1 — `src/cwp/preprocess/normalize.py` và ba bất biến

Làm **trước tất cả**. Đây là bước mà cả GĐ4 dựa vào.

### Prompt

```
Viet src/cwp/preprocess/normalize.py theo docs/protocol.md muc 14 va QD-016.

Ba che do, moi che do can CA phep bien doi VA phep map nguoc:

  N0  giu nguyen CPU%
  N1  z-score tung chuoi: (y - mu) / sd
  N2  sai phan: y_t - y_{t-1}

QUY UOC BAT BUOC, chot o QD-016:

1. mu va sd tinh tren CUA SO TRAIN cua CHINH CHUOI DO — bucket [0, 1612) tinh theo
   offset so voi b0 cua moi truong. KHONG phai thong ke cua moi truong nguon, KHONG
   phai toan bo chuoi. ddof = 1.

   Day la cho de sai nhat. Dung thong ke toan chuoi la RO RI: no dung thong tin cua
   tap test de chuan hoa tap train, va ket qua se dep bat thuong.

2. Chuoi co sd = 0 thi N1 khong xac dinh: danh dau va bao so chuoi, KHONG thay bang 0,
   KHONG them epsilon.

3. Map nguoc phai dua du doan ve THANG CPU% GOC truoc khi tinh bat ky chi so nao:
     N1:  yhat_goc = z * sd + mu
     N2:  yhat_goc = y_t + delta_hat

4. Ghi mu, sd cua tung chuoi ra results/tables/normalize_gd4.csv.

Roi viet tests/test_normalize.py voi BA BAT BIEN. Ca ba deu dung vi TOAN HOC, khong
vi hai ban khop nhau:

  naive o N0  ==  naive o N1 sau khi map nguoc      (z-score la affine)
  ma6   o N0  ==  ma6   o N1 sau khi map nguoc      (trung binh cua z la z cua trung binh)
  naive o N0  ==  naive o N2 voi delta_hat = 0      (yhat = y_t + 0)

Hai cai dau nguong < 1e-9; cai thu ba phai bang 0 TUYET DOI.

Them mot test nua, quan trong khong kem: doi gia tri y o bucket >= 1612 roi tinh lai
mu va sd — HAI CON SO PHAI KHONG DOI. Do la phep kiem truc tiep cho quy uoc 1.
```

### Hợp đồng API — `check_gd4.py` loại C gọi thẳng ba hàm này

```python
from cwp.preprocess.normalize import thong_ke_train, bien_doi, map_nguoc

thong_ke_train(y)            # y: mảng 1 chiều 2304 điểm của MỘT chuỗi
                             # -> (mu, sd), tính trên [0, 1612), ddof = 1
bien_doi(y, mode)            # mode ∈ {"N0", "N1", "N2"} -> mảng cùng độ dài
map_nguoc(yhat, y, mode)     # đưa dự đoán về thang CPU% gốc
```

Ba hàm này là **mức chuỗi đơn**, cố ý: chúng dễ kiểm tay và dễ test. Phần làm việc
trên bảng dài `data/processed/` bạn xây **lên trên** chúng, đừng viết song song.

### Lệnh
```bash
pytest tests/test_normalize.py -v
python scripts/check_gd4.py          # loại C chạy được ngay, không cần bảng nào
```

### Phải thấy

Test xanh, và bốn phép kiểm này **phải có mặt** — thiếu cái nào thì chưa đủ:

1. `naive` N0 ≡ N1, lệch < 1e−9
2. `ma6` N0 ≡ N1, lệch < 1e−9
3. `naive` N0 ≡ N2 với `Δ̂ = 0`, lệch **bằng 0**
4. Đổi `y` ở `bucket ≥ 1612` thì `mu`, `sd` **không đổi**

Con số để tự đối chiếu sau khi chạy, ở `gate-gd4.md` mục 2.3: `sd` trung vị là
**1,3264 / 1,4973 / 10,9892** cho E1/E2/E3, và **không môi trường nào có chuỗi `sd = 0`**.
Nếu bản của bạn loại chuỗi nào ở N1 thì `sd` đã tính trên cửa sổ khác.

---

## Bước 2 — Sinh đặc trưng cho ba chế độ

### Prompt

```
Mo rong scripts/build_features.py de sinh dac trung cho ca ba che do, theo QD-016
diem 2.

LUAT: bien doi chuoi y TRUOC, roi sinh lai 19 dac trung tu chuoi DA BIEN DOI. KHONG
nhan mu/sd vao cac cot lag/rolling da co san.

  - Bon dac trung lich (hour_sin, hour_cos, dow_sin, dow_cos) GIU NGUYEN — chung da
    nam trong [-1, 1] va khong mang thang tai.
  - Luat dong hop le cua muc 8 giu nguyen, ap tren chuoi da bien doi.
  - Ghi ra data/features/{env}_{mode}_h{h}.parquet, van dung 22 cot, dung ten cot cu.

Vi sao sinh lai chu khong nhan he so: voi N1 hai cach tuong duong vi z-score la affine,
nhung voi N2 thi KHONG — roll_std cua chuoi sai phan khac han roll_std cua chuoi goc.
Mot duong di duy nhat cho ca ba che do thi khong phai nho ngoai le.
```

### Lệnh
```bash
python scripts/build_features.py --env all --modes N0,N1,N2
```

### Phải thấy — số dòng hợp lệ trên test, khớp **tuyệt đối**

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

**Ba phép kiểm tự thân, làm được bằng đầu:**

1. **Cột N0 phải khớp tuyệt đối chín neo cũ** của GĐ2/GĐ3. Lệch nghĩa là đường sinh
   đặc trưng đã đổi khi bạn thêm chế độ — dừng, truy nguyên, đừng đi tiếp.
2. **N1 bằng đúng N0** ở cả chín ô, vì z-score không sinh thêm `NaN` nào khi `sd > 0`.
3. **Chỉ E3 mất dòng ở N2**, và chỉ 5–6 dòng. Sai phân biến điểm ngay sau một lỗ hổng
   thành `NaN`; E1/E2 gần như không còn lỗ hổng sau nội suy ≤2 của QĐ-008, E3 thì còn.
   Nếu E1 hoặc E2 **cũng** mất dòng ở N2 thì nghi bạn đã sai phân qua ranh giới chuỗi —
   thiếu `groupby(series_id)`, đúng lỗi P3 của `pha_features.py`.

---

## Bước 3 — Phá code kiểm ngược

Như Bước 4 của GĐ3. Test xanh mà không chứng minh được nó biết đỏ thì chưa phải test.

### Prompt

```
Pha code co chu y roi xac nhan test bat duoc, dong goi thanh scripts/pha_gd4.py
theo khuon scripts/pha_gd3.py da co.

Nam kieu pha, moi kieu phai lam do dung nhom phep kiem:

  Q1 mu/sd tinh tren TOAN CHUOI thay vi cua so train  -> test "doi y sau 1612" phai do
  Q2 quen map nguoc truoc khi tinh chi so             -> bat bien naive N0/N1 phai do
  Q3 ap mu/sd cua chuoi nay len chuoi khac            -> bat bien ma6 N0/N1 phai do
  Q4 naive o N2 dung delta_hat = delta_t thay vi 0    -> bat bien naive N0/N2 phai do
  Q5 chuan hoa ca 4 dac trung lich                    -> so dong hoac vang tay dac trung lech

Sao luu truoc, khoi phuc o khoi finally, va in ra test nao bat duoc tung kieu.
```

### Lệnh
```bash
python scripts/pha_gd4.py
```

### Phải thấy
Bản gốc **XANH**, cả năm bản phá **ĐỎ**. Ghi kết quả từng lần phá vào log.

Q1 là kiểu nguy hiểm nhất: nó **làm số đẹp lên**, nên không có phép kiểm này thì nó
trôi thẳng vào paper.

---

## Bước 4 — Sáu cặp transfer × ba chế độ × hai biến thể lịch

### Prompt

```
Viet scripts/run_transfer.py — thi nghiem B cua protocol muc 14.

Sau cap: E1->E2, E2->E1, E1->E3, E3->E1, E2->E3, E3->E2.
Ba che do N0, N1, N2. Ba horizon 1, 6, 12. Hai bien the: CO va KHONG co 4 dac trung
lich (muc 8 doi rieng cho TN-B, vi pha lich cua E3 chua biet).

LUAT:

1. Train tren moi truong NGUON (train + validation, vung [0, 1957) da purge), test
   tren moi truong DICH. KHONG huan luyen lai tren dich.

2. Sieu tham so DUNG LAI cua GD3 theo tung moi truong nguon — QD-016 diem 3. KHONG
   chay lai rolling-origin. Doc tu results/tables/chosen_gd3.csv.

3. Moi chi so tinh SAU KHI map nguoc ve thang CPU% goc (muc 14).

4. Cham tren dung tap test cua moi truong dich, [1957, 2304), cung luat purge.

5. Ba baseline la MOC CO DINH cua moi truong dich, giong nhau o ca ba che do — lay
   thang tu results/tables/baselines_gd3.csv, khong tinh lai (QD-016 diem 4).

6. Dem so lan cham test va ghi vao runs/<timestamp>/meta.json, nhu run_experiments.py
   da lam o GD3.

Ghi ra results/tables/transfer_gd4.csv theo hop dong ten cot o Buoc 0.
```

### Lệnh
```bash
python scripts/run_transfer.py --all
```

### Phải thấy

**Không có số kỳ vọng cho phần này** — đó là kết quả nghiên cứu.

Nhưng có **ba dấu hiệu cảnh báo**, và cả ba đều nghĩa là dừng lại truy nguyên:

- **N0 không thất bại nặng** ở cặp Bitbrains ↔ Alibaba → gần như chắc chắn rò rỉ.
  So với mốc hằng số ở `gate-gd4.md` mục 2.5: E1→E3 là **28,24**, E3→E1 là **35,98**.
- **N1 hoặc N2 tốt lên rất nhiều** so với N0 → nghi `mu`/`sd` nhìn thấy test. Chạy lại
  bốn phép kiểm ở Bước 1.
- **Bỏ 4 đặc trưng lịch mà E1/E2 đổi nhiều** → protocol mục 8 đã dự báo là *"gần như
  không đổi gì với E1 và E2, chỉ ảnh hưởng E3"*, vì chỉ E3 có chu kỳ ngày thật. Quan sát
  đúng như dự báo là **xác nhận**; khác dự báo thì phải đi tìm nguyên nhân khác.

Ước tính thời gian máy: **≈ 5,9 giờ** cho cả 5 model ML, tính từ thời gian thật của
GĐ3. Nếu bạn thấy nó chạy tới 30 giờ thì bạn đang dò lại siêu tham số — xem lại luật 2.

---

## Bước 5 — Đọc kết quả và trả lời RQ3

### Prompt

```
Doc bang transfer va tra loi RQ3: THANH PHAN NAO cua tin hieu transfer duoc.

Ba che do tra loi ba cau khac nhau, dung nham:
  N0 that bai -> chi chung to muc tai khac nhau, dieu ai cung biet truoc
  N1 tot len  -> hinh dang tuong doi co transfer
  N2 tot len  -> quy luat thay doi co transfer

Bao cao CA BA nhu mot ablation. Khong chon cai dep.

Kem kiem dinh Wilcoxon theo protocol muc 15, hieu chinh Holm-Bonferroni. Huong ket
luan lay tu TRUNG VI CUA HIEU theo tung chuoi, KHONG phai hieu hai trung vi — hai dai
luong nay nguoc dau nhau o 8 cap cua GD3, va lay nham thi bang khang dinh SAI CHIEU.
```

### Lệnh
```bash
python scripts/fig_gd4_transfer.py --all
```

### Phải thấy
Ma trận transfer 6 cặp, ba chế độ, kèm hình. Và một câu trả lời thẳng cho RQ3.

---

## Bước 6 — Xét điều kiện kích hoạt QĐ-004

**Làm ngay khi có bảng đầu tiên, không đợi lúc viết bài.** `research-plan.md` GĐ4 dặn
đích danh, và sau tuần 9 thì chỉ còn lựa chọn hạ mức tuyên bố.

Câu hỏi: **kết luận RQ3 có đảo chiều khi bỏ E3 khỏi bảng không?** Nếu có thì báo A
ngay — còn kịp tải `container_usage`, hoặc phải hạ mức tuyên bố của paper.

---

## Bước 7 — Log và nghiệm thu

### Prompt

```
Viet research-log/YYYY-MM-DD-gd4-transfer.md theo mau research-log/_template.md.

Phai co:
- Bang thong ke chuan hoa N1, kem doi chieu gate-gd4.md muc 2.3
- Ket qua bon phep kiem o Buoc 1 va nam lan pha code o Buoc 3
- Bang so dong ba che do, kem doi chieu muc 2.2
- Ma tran transfer day du, ca ba che do
- Tra loi thang: thanh phan nao transfer duoc, thanh phan nao khong
- Ket qua xet dieu kien QD-004
- So lan cham test cua moi truong dich, va neu hon mot lan thi vi sao
- Cho nao chua chac, cho nao phai hoi A

Khong viet "da hoan thanh" cho muc nao chua chay duoc lenh kiem.
```

### Lệnh
```bash
python scripts/check_gd4.py
pytest tests/ -v
```

> `check_gd4.py` **đã có**. Đừng đợi tới Bước 7 mới chạy: **loại C của nó chạy được
> ngay từ Bước 1**, chỉ cần `cwp/preprocess/normalize.py` tồn tại — bảy phép kiểm giải
> tích, trong đó C2 là phép kiểm rò rỉ mạnh nhất của cả giai đoạn. Dùng nó làm phản hồi
> tức thì thay vì chờ.

---

## Tóm tắt thứ tự

| Bước | Việc | Phụ thuộc |
|---|---|---|
| 0 | Ba cổng cũ còn ĐẠT, chốt hợp đồng tên tệp | — |
| 1 | **`normalize.py` + ba bất biến + phép kiểm cửa sổ train** | — |
| 2 | Sinh đặc trưng ba chế độ, khớp 27 số dòng | 1 |
| 3 | Phá code kiểm ngược, 5 kiểu | 1, 2 |
| 4 | 6 cặp × 3 chế độ × 2 biến thể lịch × 3 horizon | 1, 2 |
| 5 | Đọc kết quả, Wilcoxon, trả lời RQ3 | 4 |
| 6 | Xét điều kiện QĐ-004 | 4 |
| 7 | Log + `check_gd4.py` | tất cả |

**Bước 1 là chỗ quyết định cả giai đoạn.** Ba bất biến ở đó chạy trong vài giây và bắt
được đúng loại lỗi làm hỏng toàn bộ thí nghiệm B — rẻ hơn rất nhiều so với phát hiện
sau 5,9 giờ máy. Vướng quá 2 giờ ở bất kỳ bước nào thì dừng và hỏi A.
