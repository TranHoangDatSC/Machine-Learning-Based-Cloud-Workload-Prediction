# 2026-09-09 — Rà soát toàn dự án trước khi đi tiếp GĐ2

**Người thực hiện:** B (agent)
**Giai đoạn:** GĐ2, chen giữa Bước 3 và Bước 4
**Thời lượng:** ~1 giờ

## Mục tiêu phiên

Dự án sắp dùng để viết paper. Dò lại toàn bộ hành trình từ GĐ0 tới nay, tìm chỗ số
liệu mâu thuẫn, tài liệu lỗi thời, hoặc lập luận dựa trên tiền đề đã đổi — **trước
khi** sinh hình và bảng của Bước 4–7, vì hình và bảng đó sẽ đi thẳng vào paper.

Cách làm: không đọc suông. Mọi con số dưới đây đều **đo lại trên sản phẩm thật**
(`data/catalog.parquet`, `data/processed/`, `data/features/`,
`results/tables/reference_gd2.json`) rồi so với tài liệu.

---

## Phần I — Những chỗ KHÔNG có vấn đề

Ghi ra trước, vì phần sau toàn tin xấu và cần biết nền móng vẫn vững.

| Kiểm | Kết quả |
|---|---|
| `catalog.parquet` | 2.250 dòng (1250+500+500), `series_id` duy nhất toàn dự án |
| Nguồn gốc catalog | một máy `DESKTOP-J03IDG1`, một dấu thời gian `2026-09-09T11:50:43` cho cả 2.250 dòng |
| Mẫu E3 đóng băng | catalog E3 trùng **500/500** với `config/e3_machines.txt` |
| Cửa sổ 8 ngày | cả 1.535 chuỗi kept đều đúng 2.304 bucket, cùng `b0`, cùng `b_max` |
| Miền giá trị | `y` nằm trọn trong [0, 100] ở cả ba môi trường, không giá trị lạ |
| `catalog.mean/p50/std` | tính đúng **chỉ trên điểm quan sát thật** như protocol mục 6b đòi (lệch 1e-14 so với tính lại) |
| `judge` | xét đúng thứ tự bốn lý do của protocol mục 6 bước 7 |
| 5 lỗi ở `ra-soat-code-b.md` | đã sửa hết; không còn code chỉnh mẫu cho khớp số |
| Neo số dòng GĐ2 | 9/9 khớp tuyệt đối |
| Vân tay 19 đặc trưng | khớp bản độc lập của A ở cả ba môi trường, ngưỡng 1e-6 |

**Phép kiểm mới, chưa ai làm:** đối chiếu **từng ô** của ma trận đặc trưng với
`data/processed/`. Lấy ngẫu nhiên 400 dòng × 22 cột × 9 tệp = **79.200 ô**, tính lại
từ đầu bằng numpy. Sai **0 ô**, trừ sai số dấu phẩy động của `roll_std` (xem F10).
Cổng GĐ2 chỉ kiểm tổng hợp và bất biến đại số, nên đây là phép kiểm bổ sung đáng có.

Mã `hang` chưa bao giờ kích hoạt trong catalog. **Không phải lỗi:** `gan_chet` xét
trước và mọi chuỗi hằng đều có mean < 1,0. Chuỗi được giữ có ít nhất 7 giá trị phân
biệt (E1), 16 (E2), 67 (E3).

---

## Phần II — Năm vấn đề ảnh hưởng trực tiếp tới paper

### F1. `docs/data-card.md` mô tả quần thể TRƯỚC lọc, mà không nói ra

Data card ghi *"Mọi số liệu dưới đây đo trực tiếp trên dữ liệu. Đo ngày 2026-08-30."*
Đúng — nhưng đó là dữ liệu **thô, trước cửa sổ 8 ngày và trước bộ lọc chuỗi**. Không
dòng nào trong tệp nói điều đó.

| Chỉ số | data-card (trước lọc) | sản phẩm GĐ1 (sau lọc) | Chênh |
|---|---:|---:|---|
| E1 p50 | 0,84 | 1,7833 | **hơn gấp đôi** |
| E1 trung bình | 6,75 | 13,6352 | **hơn gấp đôi** |
| E2 p50 | 1,07 | 1,7667 | +65% |
| E2 trung bình | 6,99 | 9,2199 | +32% |
| E3 trung bình | 38,13 | 38,0123 | ~0 |

Nguyên nhân rõ ràng: bộ lọc `gan_chet` bỏ 36% chuỗi E1 và 39% chuỗi E2 nhưng chỉ
0,4% chuỗi E3. Lọc chủ yếu ở đuôi dưới, nên trung bình E1/E2 nhảy vọt còn E3 đứng yên.

**Rủi ro cụ thể:** phần Dữ liệu của paper viết theo data card, phần Kết quả viết theo
bảng cổng — hai phần mâu thuẫn nhau về chính bộ dữ liệu đang mô tả, và người phản
biện sẽ thấy trước tác giả.

### F2. Data card ghi phương pháp ĐÃ BỊ BÃI BỎ

Bảng *"Vấn đề chất lượng đã biết"* ghi hai thứ nay đã sai:

| Data card ghi | Thực tế hiện hành |
|---|---|
| Giá trị thiếu → *"Forward-fill tối đa 3 bước"* | **QĐ-008 bãi bỏ ffill.** Protocol mục 6 bước 6 dùng nội suy tuyến tính cụm ≤ 2, và `tests/test_resample.py` có hẳn một test chống ffill vì nó làm autocorrelation tăng giả tạo |
| Độ dài chuỗi lệch → *"Ngưỡng 2.000 điểm"* | QĐ-008 thay bằng `min_valid_rows_h12: 500` (`config/preprocess.yaml` ghi rõ "thay cho min_length: 2000 truoc day") |

Đây là chỗ nguy hiểm nhất trong năm chỗ: nó không phải số lệch, nó là **mô tả sai
phương pháp**. Autocorrelation là đại lượng trung tâm của RQ3, và ffill là thứ làm
hỏng đúng đại lượng đó — nói nhầm rằng mình đã ffill là tự bắn vào chân.

### F3. Ba tỉ lệ lọc trong data card lệch so với catalog

| Chỉ số | data-card | Đo trên catalog |
|---|---:|---:|
| E1 `gan_chet` | 42,5% | **36,3%** |
| E2 `gan_chet` | 34,5% | **39,4%** |
| E1 chuỗi hằng | 1,0% | **0%** — mã `hang` không bao giờ kích hoạt |
| E1 / E2 / E3 dùng được sau lọc | 56,5 / 65,5 / 99,4% | **58,8 / 60,4 / 99,6%** |

E2 lệch 5 điểm phần trăm ở hai dòng, và lệch **ngược chiều nhau** giữa E1 và E2 nên
không phải một sai số hệ thống giải thích được bằng một câu.

### F4. Hiệu ứng trần do clip — chưa tài liệu nào khai báo

Hai phần. Phần nhỏ: tỉ lệ clip trong data card cũng lệch, và lệch ngược chiều.

| | data-card | Đo trên catalog |
|---|---:|---:|
| E1 CPU% vượt 100 | 1,91% | **2,8434%** |
| E2 CPU% vượt 100 | 2,41% | **2,1933%** |

Phần lớn hơn, và chưa ai ghi ở đâu: **sau khi clip và căn lưới, tỉ lệ điểm nằm đúng
tại 100** là

| E1 | E2 | E3 |
|---:|---:|---:|
| **5,12%** | **2,28%** | **0,00%** |

Đây là **kiểm duyệt bất đối xứng** giữa chính ba môi trường đang được đem so sánh.
Hệ quả:

- Đuôi phải của phân phối E1/E2 bị nén vào một điểm, còn E3 thì không. Hình phân
  phối ở Bước 5 — hình quan trọng nhất của paper — sẽ có một cột dựng đứng tại 100
  cho E1/E2 mà không giải thích thì người đọc không hiểu.
- Mọi metric ở vùng tải cao của E1/E2 đo trên dữ liệu đã bị chặn trần. Model dự đoán
  vượt 100 sẽ bị phạt dù đúng.
- Lập luận "E3 mượt hơn, dễ dự đoán hơn" có một phần đến từ việc E3 không bị chặn.

### F5. Tiền đề số của QĐ-005 nay đã sai

QĐ-005 là **đóng góp chính của paper** — nó lập luận rằng RQ3 phải tách mức tải khỏi
động lực học. Câu biện minh nguyên văn:

> *"Autocorr bậc 1 trên lưới 5 phút của ba môi trường nằm cùng vùng, 0,644 đến 0,781.
> Nghĩa là động lực học có khả năng so sánh được, chỉ mức tải là lệch."*

Đo lại trên sản phẩm GĐ1 (`reference_gd2.json`, bản độc lập của A):

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| ACF lag 1 — data-card, trước lọc | 0,675 | 0,644 | 0,781 |
| ACF lag 1 — sau lọc và cắt cửa sổ | 0,6674 | 0,6431 | **0,8634** |
| ACF lag 12 — trước lọc | 0,350 | 0,304 | 0,549 |
| ACF lag 12 — sau lọc | **0,4459** | 0,2978 | **0,6287** |

E3 chạy từ 0,781 lên 0,863 và **tách hẳn** khỏi E1/E2. Vùng không còn là 0,644–0,781
mà là 0,643–0,863.

**Quyết định QĐ-005 vẫn đúng** — thậm chí còn cần hơn, vì nay hai bên khác nhau cả về
mức tải lẫn về mức tự tương quan. Nhưng **câu biện minh thì không còn đúng**, và nếu
nó vào paper nguyên văn thì đó là một phát biểu sai về chính dữ liệu của mình.

---

## Phần III — Ba vấn đề mức trung bình

### F6. `gate-gd2.md` mục 2.2 gọi nhầm nhãn "Target mean / p50 / std"

Bảng đó ghi 13,6352 / 9,2199 / 38,0123. Truy ra được ba con số này là **phân phối gộp
của `y`** trên các chuỗi kept (kể cả điểm nội suy) — tức "biến mục tiêu" theo nghĩa
protocol mục 4, chứ không phải cột `target` của ma trận đặc trưng.

Cột `target` thật cho số khác:

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Gộp mọi điểm `y` (bảng mục 2.2) | 13,6352 | 9,2199 | 38,0123 |
| Cột `target` h=1 | **13,6741** | **9,2667** | **38,3678** |

Chênh 0,3–0,9%, dưới ngưỡng 2% mà phiếu cho phép ở Bước 4 nên cổng **sẽ không bắt**.
Nhưng Bước 4 và Bước 5 phải biết mình đang mô tả và vẽ quần thể nào, và paper phải
dùng một định nghĩa nhất quán. `reference_gd2.json` của A dùng đúng cột `target`
(`target_mean_h1`), nên hai tài liệu của A đang nói hai thứ khác nhau dưới cùng một
cái tên.

### F7. Đặc trưng lịch của E1/E2 là UTC, mà trace là giờ Hà Lan

Đo được: `b0` của E2 = 4.584.360 → **2013-07-31T22:00:00Z**, đúng bằng **00:00 giờ
Amsterdam mùa hè (UTC+2)**. Nghĩa là trace E2 bắt đầu đúng nửa đêm giờ địa phương, và
"một ngày" trong dữ liệu bắt đầu tại giờ UTC 22.

QĐ-010 chốt dùng UTC và **không quy về giờ địa phương** — quyết định hợp lệ, giữ
nguyên. Nhưng hệ quả phải khai báo: nếu paper nói *"tải đạt đỉnh vào giờ X"* thì X là
UTC và lệch 2 giờ so với giờ vận hành thật của trung tâm dữ liệu. Với `dow` thì lệch
này có thể đẩy hoạt động nửa đêm sang ngày hôm trước.

### F8. E3 thiếu 9,29% điểm, và ACF lag 288 bỏ 14,65% số cặp

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Tỉ lệ `y` là NaN | 1,427% | 0,309% | **9,294%** |
| Cặp bị bỏ khi tính ACF lag 1 | 1,43% | 0,35% | **9,76%** |
| Cặp bị bỏ khi tính ACF lag 288 | 1,63% | 0,71% | **14,65%** |

E3 thiếu gấp 6,5 lần E1 và 30 lần E2. Đáng chú ý: E3 có 9,29% NaN nhưng chỉ 0,15%
điểm được nội suy — nghĩa là **gần như toàn bộ lỗ hổng của E3 dài hơn 2 bucket**.

Kết luận trụ cột *"chỉ E3 có chu kỳ ngày rõ, ACF lag 288 = 0,5956"* đo trên tập đã bỏ
14,65% số cặp. Con số vẫn dùng được — cách tính theo cặp là đúng, không co trục thời
gian — nhưng tỉ lệ bỏ phải nằm cạnh con số mỗi khi nó xuất hiện.

---

## Phần IV — Hai chỗ nhỏ

**F9.** README mục 8 "Cấu trúc repository" thiếu hẳn `scripts/` (8 tệp, gồm cả hai
công cụ cổng `check_gd1.py` và `check_gd2.py`) và thiếu `data/features/`.

**F10.** `roll_std` lệch **tối đa 5,05e-7 tương đối** so với tính lại bằng
`numpy.std(ddof=1)` trên cùng cửa sổ. Chỉ xảy ra ở cửa sổ gần hằng, do pandas dùng
thuật toán lăn cửa sổ kiểu Welford còn numpy tính lại từ đầu. **Không phải lỗi** —
ghi lại để lần sau ai đối chiếu không tưởng là rò rỉ.

---

## Đã xử lý — QĐ-011, cùng ngày

A chốt **QĐ-011** gom cả tám phát hiện. Nguyên tắc xuyên suốt: **không xoá và không
sửa số đã đo, chỉ nói rõ số đó thuộc quần thể nào, rồi bổ sung số của quần thể còn
thiếu.** Rủi ro thấp nhất — không con số nào bị mất, không kết quả nào phải chạy lại.

| # | Xử lý | Ở đâu |
|---|---|---|
| F6 | **Chốt:** bảng mô tả và hình phân phối mô tả *"CPU% sau tiền xử lý"* = phân phối gộp của `y`. Thống kê cột `target` báo riêng ở phần Thiết lập thí nghiệm. Con số không đổi, chỉ đổi tên | QĐ-011 điểm 2; `gate-gd2.md` mục 2.2 |
| F1 | Data card có khai báo hai quần thể ngay đầu tệp; các bảng cũ đánh dấu "THÔ — mẫu ngẫu nhiên" | QĐ-011 điểm 1; `data-card.md` |
| F2 | Hai ô "Xử lý" sai đã sửa: ffill 3 bước → nội suy tuyến tính ≤ 2; ngưỡng 2.000 điểm → `min_valid_rows_h12 = 500` | QĐ-011 điểm 4; `data-card.md` |
| F3 | Thêm mục **"Sau tiền xử lý — quần thể NGHIÊN CỨU"** với bảng lọc và phân phối đo trên toàn bộ | `data-card.md` |
| F4 | Trần 100 khai báo thành một mục riêng trong protocol mục 4, thành Giới hạn số 7, và thành một mục kiểm bắt buộc của hình Bước 5 | QĐ-011 điểm 3 |
| F5 | QĐ-005 nhận khối đính chính: **giữ quyết định, viết lại lý do**. Lập luận mới mạnh hơn — ba môi trường lệch ở *cả hai* thành phần nên transfer thô càng không quy trách nhiệm được | QĐ-011 điểm 5; `decisions.md` QĐ-005 |
| F7 | Bằng chứng `b0` của E2 = 00:00 giờ Amsterdam ghi vào protocol mục 8; Giới hạn số 9 | QĐ-011 điểm 6 |
| F8 | Tỉ lệ cặp bị bỏ vào bảng ACF của data card, kèm quy tắc "luôn đi cùng con số"; Giới hạn số 8 | `data-card.md` |
| F9 | README mục 8 thêm `scripts/`, `data/features/`, `catalog.parquet`; sửa câu "data/ không lên Git" cho đúng | `README.md` |

Ba thứ **cố ý không làm**:

- **Không đổi luật clip.** Thang 0–100 là định nghĩa biến mục tiêu ở protocol mục 4;
  đổi nó là đổi bài toán và phải chạy lại toàn bộ GĐ1. Chỉ khai báo.
- **Không đảo QĐ-005.** Tiền đề sai không kéo theo kết luận sai ở đây — quyết định
  chạy ablation N0/N1/N2 đúng hơn trước.
- **Không đo lại quần thể thô.** Số cũ đúng cho quần thể của nó; đo lại 11 GB để
  thay một bảng chỉ dùng cho phần mô tả nguồn là không đáng.

## Còn lại cho Bước 4–7

- Bước 4 sinh `results/tables/` — từ đó bảng trong data card có bản máy sinh, không
  còn là số chép tay.
- Bước 5 phải chú thích trần 100 (đã thành mục kiểm ở `gate-gd2.md` mục 3.5).
- Bước 6 báo tỉ lệ cặp bị bỏ cạnh mọi con số ACF của E3.

## File sinh ra

- `research-log/2026-09-09-ra-soat-truoc-paper.md` — tệp này

## File sửa theo QĐ-011

- `docs/decisions.md` — thêm QĐ-011; QĐ-005 nhận khối đính chính
- `docs/data-card.md` — khai báo hai quần thể, sửa hai mô tả phương pháp sai, thêm
  mục "Sau tiền xử lý", thêm bốn giới hạn
- `docs/protocol.md` — mục 4 khai báo trần 100; mục 8 ghi rõ UTC và UTC+2
- `research-log/gate-gd2.md` — mục 2.2 đổi nhãn; mục 3.5 thêm hai mục kiểm
- `README.md` — mục 8 cấu trúc repo
