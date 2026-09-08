# Giao thức nghiên cứu

**Trạng thái:** ĐÃ CHỐT — 2026-08-30
**Sửa đổi:** chỉ qua `decisions.md`, kèm lý do và ngày. Không sửa im lặng.

> Tài liệu này chốt luật chơi **trước khi nhìn thấy bất kỳ kết quả model nào**.
> Mục đích là chặn việc điều chỉnh tiêu chí cho khớp với kết quả đẹp — lỗi phổ biến
> nhất khiến một nghiên cứu thực nghiệm mất giá trị.
>
> Nếu trong quá trình chạy phát hiện giao thức có chỗ sai, **dừng lại, ghi vào
> `decisions.md`, sửa ở đây, rồi chạy lại từ đầu**. Không chạy tiếp với luật đã đổi.

---

## 1. Bài toán

Dự đoán một bước và nhiều bước mức sử dụng CPU của một đơn vị tính toán (VM hoặc
máy vật lý) trong hạ tầng đám mây, dựa trên lịch sử sử dụng tài nguyên của chính
đơn vị đó.

**Không** phải bài toán phân loại, **không** phải phát hiện bất thường, **không**
phải dự đoán job failure.

## 2. Câu hỏi nghiên cứu

| Mã | Câu hỏi | Thí nghiệm |
|---|---|---|
| RQ1 | Mô hình ML nào dự đoán workload tốt nhất, và có vượt được baseline naive không? | TN-A |
| RQ2 | Hiệu năng thay đổi thế nào giữa các môi trường đám mây khác nhau? | TN-A |
| RQ3 | Model train trên môi trường A có generalize sang môi trường B không, và thành phần nào của tín hiệu thì transfer được? | TN-B |

RQ1 và RQ2 dùng chung kết quả TN-A, khác nhau ở cách đọc: RQ1 đọc theo cột model,
RQ2 đọc theo cột môi trường.

## 3. Dữ liệu

| Mã | Nguồn | Phạm vi dùng |
|---|---|---|
| E1 | Bitbrains fastStorage | Toàn bộ 1.250 VM |
| E2 | Bitbrains Rnd | **Chỉ `2013-8`**, 500 VM |
| E3 | Alibaba v2018 `machine_usage` | **Mẫu phân tầng 500 máy** trên 4.023 |

Lý do giới hạn E2 và E3: xem `decisions.md` mục QĐ-003. Dữ liệu còn lại giữ nguyên
trên đĩa, dùng cho kiểm tra tính vững nếu còn thời gian.

### Mẫu phân tầng E3
Chia 4.023 máy thành 5 tầng theo ngũ phân vị của CPU% trung bình, lấy ngẫu nhiên
100 máy mỗi tầng. `random_state = 42`.

## 4. Biến mục tiêu

**CPU%, thang 0–100.**

| Môi trường | Cột |
|---|---|
| E1, E2 | `CPU usage [%]` |
| E3 | `cpu_util_percent` |

**Không dùng** `CPU usage [MHZ]`: phụ thuộc số core và tốc độ core của từng VM nên
không so sánh được giữa các môi trường, làm RQ3 vô nghĩa.

## 5. Lưới thời gian

**300 giây (5 phút) cho cả ba môi trường.**

- Căn về lưới tuyệt đối `floor(t / 300)`. E1, E2 vốn đã 300 s; E3 hạ tần từ khoảng
  10 s.
- Giá trị mỗi bucket bằng **trung bình** các mẫu rơi vào bucket đó.
- Bucket không có mẫu nào thì để `NaN`. Cách xử lý `NaN` nằm ở mục 6, không làm ở
  bước này.

## 6. Làm sạch và xử lý lỗ hổng

> Sửa theo QĐ-008 ngày 2026-09-08. Quy tắc cũ *"ffill 3 bước rồi cắt chuỗi"* đã bị
> bãi bỏ vì phá huỷ 74% dữ liệu E2 và 99% dữ liệu E3. Lý do đầy đủ và bằng chứng
> định lượng ở `decisions.md` QĐ-008.

Áp dụng theo đúng thứ tự này:

1. **Clip** CPU% về `[0, 100]`. Ghi lại tỉ lệ bị clip mỗi môi trường.
2. **Mask** giá trị bất thường của E3: `disk_io_percent` bằng `-1` hoặc `101` thì
   cho về `NaN`.
3. **Bỏ cột** `mem_gps` và `mkpi` của E3 (rỗng 79%).
4. **Căn lưới** 5 phút như mục 5.
5. **Cắt cửa sổ 8 ngày** như mục 7.
6. **Nội suy lỗ hổng ngắn.** Nội suy tuyến tính những cụm `NaN` dài **≤ K = 2 điểm**
   (tối đa 10 phút). Cụm dài hơn giữ nguyên `NaN`.
   - **Không dùng forward-fill.** ffill tạo ra đoạn phẳng, làm autocorrelation tăng
     giả tạo — mà autocorrelation là đại lượng trung tâm của RQ3.
   - `K` là tham số cấu hình trong `config/preprocess.yaml`, không chôn trong code.
7. **Lọc chuỗi** — loại nếu vi phạm bất kỳ điều kiện nào:
   - Không có mẫu nào nằm trong cửa sổ 8 ngày (`ngoai_cua_so`)
   - CPU% trung bình dưới 1,0 — chuỗi gần chết (`gan_chet`)
   - Số giá trị phân biệt từ 2 trở xuống — chuỗi hằng (`hang`)
   - Dưới **500 dòng huấn luyện hợp lệ ở h = 12** (`it_dong`), theo định nghĩa ở
     mục 8
8. **Không cắt chuỗi tại lỗ hổng.** Chuỗi giữ nguyên độ dài, kể cả khi còn `NaN`.
   Việc loại bỏ diễn ra ở mức **dòng huấn luyện**, xem mục 8.

**Bắt buộc báo cáo cho từng môi trường:**

| Cột | Vì sao bắt buộc |
|---|---|
| Số chuỗi vào | Mốc gốc |
| Số bị loại theo **từng** lý do, bốn cột tách riêng | Gộp lại thì không truy được nguyên nhân |
| Số chuỗi còn lại | |
| Số dòng huấn luyện hợp lệ ở mỗi horizon | Con số thực sự dùng để train |
| **Tỉ lệ điểm được nội suy** | Đây là can thiệp vào dữ liệu, phải khai báo |
| Tỉ lệ mẫu bị clip | Kiểm chứng bước làm sạch có chạy |

Bảng này vào phần Dữ liệu của paper.

## 7. Cửa sổ thời gian chung

E3 chỉ có 8 ngày. Thí nghiệm chính dùng **8 ngày đầu** của cả ba môi trường.

**Cửa sổ là toàn cục theo từng môi trường**, tính từ mốc thời gian sớm nhất của môi
trường đó — không phải từ điểm đầu của mỗi chuỗi. Cụ thể: `b0 = min` bucket trên
toàn bộ chuỗi của môi trường, cửa sổ là `[b0, b0 + 2304)`.

Lý do: giữ mọi chuỗi cùng phủ một khoảng lịch, nên đặc trưng giờ-trong-ngày và
thứ-trong-tuần so sánh được giữa các chuỗi, và phát biểu "8 ngày đầu của trace" đúng
theo nghĩa đen. 92% chuỗi E1 và 99% chuỗi E2 vốn đã bắt đầu cùng một mốc; số bắt đầu
muộn bị loại với lý do `ngoai_cua_so` và phải được báo cáo.

Chuỗi dài hơn của E1 và E2 chỉ dùng cho phân tích bổ sung về chu kỳ tuần, và phải
ghi rõ là phân tích bổ sung.

## 8. Đặc trưng

Chỉ dùng lịch sử của **chính chuỗi đó**. Không dùng thông tin từ chuỗi khác, không
dùng thông tin tương lai.

| Nhóm | Cụ thể |
|---|---|
| Lag | `t-1, t-2, t-3, t-6, t-12, t-24` (5 phút đến 2 giờ) |
| Rolling | mean, std, min, max trên cửa sổ 6 và 12 điểm |
| Sai phân | `y_t` trừ `y_{t-1}` |
| Lịch | giờ trong ngày, thứ trong tuần, mã hoá sin/cos |

Mọi thống kê rolling tính **chỉ trên quá khứ**, không bao gồm điểm hiện tại.

### Dòng huấn luyện hợp lệ

> Bổ sung theo QĐ-008.

Cửa sổ đặc trưng sâu nhất là **24 bước** (lag `t-24`). Một dòng huấn luyện tại thời
điểm `t` với horizon `h` là **hợp lệ** khi và chỉ khi:

- mọi điểm trong `[t − 24, t]` đều không `NaN`, **và**
- target tại `t + h` không `NaN`

Dòng không hợp lệ thì **bỏ dòng đó**, không cắt chuỗi và không lấp thêm.

Hệ quả cần nhớ: **một điểm `NaN` đơn lẻ làm hỏng 25 dòng.** Đó là lý do bước nội suy
lỗ hổng ngắn ở mục 6 tồn tại — nó thu hồi phần lớn số dòng mà không bịa ra động lực
học.

## 9. Chia dữ liệu

**Chia theo thời gian. Tuyệt đối không shuffle.**

Với mỗi chuỗi, theo trục thời gian: 70% train, 15% validation, 15% test.

Chọn siêu tham số **chỉ trên validation**. Test chỉ chạm vào một lần duy nhất, khi
đã chốt toàn bộ mô hình.

Kiểm định chéo dùng **rolling-origin** 5 fold trên phần train cộng validation.

## 10. Horizon

`h` nhận giá trị 1, 6, 12 — tương ứng 5 phút, 30 phút, 60 phút.

Dự đoán nhiều bước theo kiểu **direct**: mỗi horizon một model riêng. Không dùng
recursive vì sai số tích luỹ và khó quy trách nhiệm.

## 11. Mô hình

| Nhóm | Mô hình | Vai trò |
|---|---|---|
| Baseline | Naive / persistence, `ŷ = y_t` | **Mốc bắt buộc.** Mọi con số đều so với nó |
| Baseline | Moving average, cửa sổ 6 | Mốc thứ hai |
| Baseline | Seasonal naive, `ŷ = y_{t-288}` (cùng giờ hôm trước) | Mốc mùa vụ |
| Tuyến tính | Linear Regression, Ridge | Cận dưới của họ ML |
| Cây | Random Forest | |
| Cây | XGBoost | |
| Kernel | SVR nhân RBF | Chỉ chạy trên mẫu con nếu quá chậm |

**Ngoài scope chính:** LSTM/GRU. Chỉ làm nếu hoàn thành toàn bộ phần trên và còn
thời gian. Nếu làm mà thua XGBoost thì **báo cáo đúng như vậy** — đó là kết quả hợp
lệ và phổ biến trên dữ liệu dạng này.

**Chiến lược huấn luyện:** global model — một model học trên nhiều chuỗi của cùng
một môi trường, không phải mỗi chuỗi một model.

## 12. Chỉ số đánh giá

| Chỉ số | Dùng vì |
|---|---|
| MAE | Chỉ số chính, cùng đơn vị với target |
| RMSE | Phạt lỗi lớn, nhạy với burst |
| SMAPE | Thay cho MAPE |
| **MASE** | **So được giữa các môi trường có mức tải khác nhau** |
| R² | Tỉ lệ phương sai giải thích được |

**Không dùng MAPE.** Trên 40% mẫu Bitbrains có giá trị gần 0, mẫu số nổ.

MASE lấy naive một bước trên tập train làm mẫu số. Đây là chỉ số chính khi so sánh
**giữa các môi trường**, vì nó đã chuẩn hoá theo độ khó nội tại của từng chuỗi.

Gộp kết quả nhiều chuỗi bằng **trung vị** kèm IQR, không dùng trung bình, vì phân
phối lệch nặng.

## 13. Thí nghiệm A — trong cùng môi trường

Train và test trên cùng một môi trường.

Tổ hợp: 3 môi trường x 7 model x 3 horizon.

Trả lời RQ1 và RQ2.

## 14. Thí nghiệm B — xuyên môi trường

Train trên môi trường nguồn, test trên môi trường đích, **không huấn luyện lại**.

Sáu cặp: E1→E2, E2→E1, E1→E3, E3→E1, E2→E3, E3→E2.

### Ba chế độ chuẩn hoá — trục chính của paper

> Giải thích chi tiết kèm số liệu chứng minh: `giai-thich-chuan-hoa.md`.
> Đọc file đó trước khi triển khai phần này.

Đây là phần quan trọng nhất. Chạy cả ba, báo cáo cả ba như một ablation.

| Chế độ | Target | Câu hỏi nó trả lời |
|---|---|---|
| **N0 — Thô** | CPU% nguyên bản | Đối chứng. Dự kiến thất bại nặng ở cặp Bitbrains và Alibaba |
| **N1 — Chuẩn hoá per-series** | z-score từng chuỗi | Bỏ mức tải, giữ biên độ tương đối |
| **N2 — Sai phân** | `y_{t+h}` trừ `y_t` | Chỉ còn động lực học thuần |

**Thống kê chuẩn hoá của N1 chỉ được tính trên cửa sổ train của chuỗi đó.** Dùng
thống kê toàn chuỗi là rò rỉ dữ liệu.

Khi báo cáo, mọi dự đoán phải **đưa ngược về thang CPU% gốc** rồi mới tính chỉ số,
để ba chế độ so sánh được với nhau.

### Vì sao phần này quyết định giá trị của paper

Phân phối target lệch rất mạnh: trung vị E1 và E2 khoảng 1%, E3 khoảng 37%.

**Đã đo trên dữ liệu thật** (833 chuỗi E3 sau lọc, horizon 1, trung vị): một **hằng
số** bằng mức tải trung bình của E1 áp lên E3 cho MAE = **28,64**. Không model, không
đặc trưng, không huấn luyện. Trong đó 63,4% sai số chỉ là chênh lệch mức tải. Để so
sánh, naive persistence trong chính E3 cho MAE = 5,76.

Nghĩa là nếu chạy N0 thô và thu được MAE khoảng 28, con số đó **không nói lên điều gì**
về chất lượng model — một hằng số cũng đạt được. Kết luận "cross-environment
generalization thất bại" khi đó đúng nhưng rỗng.

Có N1 và N2 thì câu hỏi đổi thành: *hình dạng biến thiên của workload có transfer
giữa các datacenter không?* Câu này chưa có lời giải hiển nhiên, và là đóng góp thật
sự của bài.

## 15. Kiểm định thống kê

So sánh hai model trên cùng tập chuỗi: **Wilcoxon signed-rank** trên MAE theo từng
chuỗi. Mức ý nghĩa `alpha = 0,05`.

Khi so nhiều model cùng lúc: hiệu chỉnh Holm–Bonferroni.

**Không tuyên bố "model X tốt hơn model Y" nếu chưa có kiểm định.** Chênh lệch 2%
MAE trên trung vị hoàn toàn có thể là nhiễu.

## 16. Tái lập

- `random_state = 42` ở mọi chỗ có yếu tố ngẫu nhiên
- Mỗi lần chạy sinh một thư mục `runs/<ngày>_<thí nghiệm>_<model>_<env>/` kèm bản
  sao config đúng lúc chạy
- Phiên bản thư viện ghim trong `requirements.txt`
- Mọi số trong paper phải truy ngược được về một thư mục `runs/` cụ thể

## 17. Điều cam kết không làm

Ghi ra đây để tự ràng buộc:

- Không đổi metric sau khi thấy kết quả
- Không đổi ngưỡng lọc để có bảng đẹp hơn
- Không bỏ môi trường nào khỏi bảng vì kết quả xấu
- Không giấu việc baseline naive thắng model ML, nếu điều đó xảy ra
- Không chạy test nhiều lần rồi chọn lần tốt nhất
