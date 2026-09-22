# Định hướng v5 và thiết kế thực nghiệm

Ngày lập: 20/09/2026. Tài liệu chuẩn bị cho bản thảo v5, viết sau khi đọc toàn văn hai công trình trong `paper/`, mã nguồn `CWP-Cloud-Notebooks`, kết quả gốc và báo cáo rà soát `ra-soat-v4-truoc-khi-nop-VJCS.md`.

**Cập nhật 20/09/2026:** sáu điểm ở mục 12 đã được chốt, các lỗi P0 đã sửa và đã chạy thử để đo chi phí. Phần đã sửa, kết quả kiểm tra và ngân sách nằm ở `bao-cao-sua-p0-va-ngan-sach.md`. Tài liệu này giữ vai trò thiết kế; con số đo được nằm ở báo cáo kia.

---

## 1. Kết luận ngắn

**Giữ được:**

| Thành phần | Lý do |
|---|---|
| Đề tài dự báo CPU theo từng máy trên Bitbrains và Alibaba | Hai công trình trước dự báo ở mức khác: Rossi dựng chuỗi trung bình của cả cụm, Christofidi chỉ đo tính bền của dữ liệu trên Bitbrains và Alibaba chứ không dự báo |
| Hạ tầng mã nguồn: đọc dữ liệu, lưới 5 phút, luật dòng hợp lệ, chia theo bucket, purge dòng vắt ranh giới, chỉ số theo từng máy, kiểm định ghép cặp | Đã kiểm và chạy đúng; đây là phần tốn công nhất và vẫn dùng lại được |
| Ba chế độ chuẩn hoá N0, N1, N2 và mã sinh lại đặc trưng theo từng chế độ | Chính là yếu tố cần khảo sát có kiểm soát ở v5 |
| Khung chuyển giao hai chiều và tỉ số L | Giữ ở vai trò hướng phụ, thêm mốc naïve tại đích |
| Thí nghiệm máy giả | Phép kiểm giả thuyết hiệu ứng tổng hợp, không trùng với ai |

**Phải bỏ:**

| Thành phần | Lý do |
|---|---|
| Kết luận "với máy ảo thì gần như không đáng dùng học máy" | Mâu thuẫn với chính số liệu của bài ở RMSE và ở chế độ N1; trùng thông điệp với Christofidi |
| Tuyên bố "một cách đo mới" cho tỉ số L | Không chứng minh được tính mới |
| Cụm "trung tâm dữ liệu khác" trong tiêu đề | E1 và E2 cùng một trung tâm dữ liệu phân tán theo mô tả của GWA-T-12 |
| Hai lỗi chuẩn hoá ở vai trò đóng góp | Lỗi 1 là hệ quả của bộ lọc dùng dữ liệu tương lai, lỗi 2 là lỗi viết mã |
| Bảng 3 và Bảng 4 ở dạng hiện tại | Chỉ có MAE, chỉ một cửa sổ test, seasonal naïve sai công thức |

**Phải viết lại:** toàn bộ phần Giới thiệu, Tổng quan, Kết quả và Kết luận. Phần Phương pháp giữ khung nhưng đổi thiết kế đánh giá.

---

## 2. Đối chiếu với hai công trình trước

Hai bài đã đọc toàn văn từ bản PDF trong `paper/`. Bản Rossi là arXiv:2303.13525v2 ngày 12/11/2023; bản tạp chí trên Cluster Computing cần đối chiếu số tập và số trang trước khi trích dẫn. Bản Christofidi là SoCC '23, trang 544 đến 554, doi 10.1145/3620678.3624790.

### 2.1 Bảng đối chiếu

| Tiêu chí | Christofidi 2023 | Rossi 2023 | Đề tài v5 |
|---|---|---|---|
| Câu hỏi | Học máy có cần thiết cho dự báo mức dùng tài nguyên không (§1) | Dự báo kèm bất định và khả năng chuyển giao giữa các miền dữ liệu (§1) | Lợi thế của mô hình so với dự báo naïve phụ thuộc thế nào vào chuẩn hoá, hàm mất mát và tiêu chí đánh giá, và có ổn định theo thời gian không |
| Nguồn dữ liệu | Google 2019 cho phần dự báo; Alibaba 2018, Azure, Google, Bitbrains cho phần đo tính bền (Bảng 1, §3.1) | Google 2011 và 2019, Alibaba 2018 và 2020, gộp thành 12 bộ (§4.1) | Bitbrains fastStorage, Bitbrains Rnd, Alibaba 2018 |
| Đơn vị dự báo | Một task của một job; huấn luyện một mô hình cho mỗi job, dùng chuỗi của một task ngẫu nhiên (§2.1) | **Chuỗi trung bình của toàn bộ máy trong một cụm**: "For each cluster, we create a time series dataset that includes the average CPU and average memory usage for all the machines with a 5-minute interval" (§4.1.1) | Từng máy ảo và từng máy vật lý, 1.535 chuỗi |
| Cách tổng hợp | Không gộp; nhưng phần đo tính bền dùng chỉ số ARD của từng chuỗi (§3.1) | Gộp trung bình theo cụm trước khi huấn luyện | Không gộp; chỉ số tính riêng từng máy rồi lấy trung vị trên tập máy |
| Chân trời dự báo | Một bước, tức t+1 (§2.1) | Một mức duy nhất, 10 phút (§4.3) | 5, 30 và 60 phút |
| Mô hình | LSTM một lớp 50 đơn vị (§2.1) | LSTM có lớp tích chập, LSTMD, HBNN (§3) | Naïve, seasonal naïve, trung bình trượt, Ridge, XGBoost, DLinear, GRU, SVR |
| Chuẩn hoá | Min-max [0,1] cho từng chuỗi (§2.1); ARD cũng chuẩn hoá min-max kèm cắt đuôi 1% (§3.1) | Min-max [0,1] cho từng bộ dữ liệu (§4.1.1) | Yếu tố khảo sát: thô N0 và z-score theo từng máy N1, trên cùng quần thể và cùng tập test |
| Hàm mất mát | MAE, chọn sau khi thử MSE, MAE, MSLE, Huber (§2.1) | MSE cho LSTM, log-likelihood âm cho HBNN và LSTMD (§3) | Yếu tố khảo sát: bình phương và tuyệt đối trên cùng một họ mô hình |
| Mốc so sánh | Dự báo bền y(t+1) = y(t), gọi là non-ML (§2.2) | **Không có mốc naïve**; mốc duy nhất là LSTM điểm (§3.1) | Naïve, seasonal naïve và trung bình trượt, cộng mô hình học tại đích cho phần chuyển giao |
| Chỉ số | MAE trên thang đã chuẩn hoá (Hình 1); ARD cho tính bền (§3.1) | MSE và MAE trên thang đã chuẩn hoá; SR, OP, UP, TPR cho mức dịch vụ (§5.1) | MAE chính, kèm RMSE và MASE; thêm một hàm chi phí bất đối xứng ở phần phân tích |
| Kiểm định | Không có | Diebold-Mariano theo cặp mô hình, kết quả cho thấy các mô hình không khác nhau có ý nghĩa (§5.1) | Wilcoxon ghép cặp theo từng máy, hiệu chỉnh Holm, kèm cỡ hiệu ứng và tỉ lệ máy thắng |
| Chia thời gian | Không mô tả tách bạch; Thí nghiệm A chấm trên chính dữ liệu huấn luyện (§2.1) | 80% đầu huấn luyện, 20% của phần đó làm kiểm định, 20% cuối làm test; một lần chia duy nhất (§4.3) | Nhiều cửa sổ test theo thời gian trên Bitbrains; Alibaba giữ 8 ngày và nêu rõ giới hạn |
| Chuyển giao | Thí nghiệm C: mô hình của job 113 chấm cho ba job khác, trong cùng Google (§2.1) | Sáu kịch bản zero-shot và tinh chỉnh, trong cùng nhà cung cấp và khác nhà cung cấp (§4.2, §5.2) | Sáu chiều giữa ba tập vết, mỗi chiều so với cả mô hình học tại đích lẫn naïve tại đích |
| Kết luận chính | LSTM dự đoán gần như bản dịch một bước của dữ liệu; chuỗi tài nguyên có tính bền cao, ARD trung bình 3,29% (§2.2, §3) | Mô hình bất định vượt LSTM ở chỉ số mức dịch vụ; chuyển giao được trong cùng nhà cung cấp, thất bại khi khác nhà cung cấp, tinh chỉnh làm xấu thêm trong hầu hết kịch bản (§5.2) | Chưa có |

### 2.2 Ba nhóm phát biểu

**Nhóm A. Nghiên cứu trước đã làm, đề tài v5 không được nhận là mới.**

- Dự báo naïve đủ mạnh cho dự báo tài nguyên đám mây, và LSTM thường chỉ học lại phép dịch một bước (Christofidi §2.2, Hình 2).
- Chuỗi CPU của Alibaba và Bitbrains có tính bền cao giữa hai bước liên tiếp; ARD của CPU Alibaba là 6,97% và của CPU Bitbrains là 3,05% (Christofidi §3.2, Bảng 2).
- Tính bền giữ được khi mở rộng cửa sổ từ 5 phút lên 2 giờ, đo trên Google (Christofidi Hình 4).
- Chuyển giao mô hình trong cùng nhà cung cấp chấp nhận được, khác nhà cung cấp thì hỏng (Rossi §5.2, Bảng 5 và Bảng 7).
- Huấn luyện một mô hình trên nhiều bộ dữ liệu tốt hơn nhiều mô hình trên từng bộ (Rossi §5.1).
- Dùng Bitbrains hoặc Alibaba, thêm mô hình vào danh sách so sánh, hoặc quan sát rằng MAE và RMSE xếp hạng khác nhau: không phải đóng góp.

**Nhóm B. Đề tài v5 bổ sung được, với điều kiện thực hiện đúng thiết kế ở mục 5.**

| Bổ sung | Vì sao chưa có trong hai bài |
|---|---|
| Đối chứng dự báo theo từng máy trên Bitbrains và Alibaba, có mốc naïve và kiểm định ghép cặp | Christofidi chỉ đo ARD trên hai bộ dữ liệu, phần dự báo chỉ chạy trên bốn job của Google (§2.1, §3.1). Rossi dự báo chuỗi trung bình của cụm và không có mốc naïve |
| Đo mức phụ thuộc của kết luận vào chuẩn hoá, hàm mất mát và tiêu chí đánh giá, thay từng yếu tố một | Christofidi cố định MAE cho cả hàm mất mát lẫn chỉ số. Rossi cố định MSE và log-likelihood âm. Không bài nào thay đổi một yếu tố và giữ các yếu tố còn lại |
| Độ ổn định của kết luận qua nhiều giai đoạn thời gian | Rossi dùng một lần chia 80/20. Christofidi không đánh giá dự báo theo thời gian |
| Ba chân trời dự báo 5, 30 và 60 phút với cùng bộ dữ liệu và cùng quần thể | Christofidi dừng ở t+1, Rossi dừng ở 10 phút |
| Chuyển giao đo bằng hai mốc: mô hình học tại đích và naïve tại đích | Rossi không có mốc nào trong hai mốc đó |

**Nhóm C. Chưa đủ bằng chứng để tuyên bố, phải chạy xong mới biết.**

- Chuẩn hoá theo từng máy có làm đảo kết luận naïve so với học máy hay không. Số liệu hiện có cho thấy hướng đó ở E1 (7/15 phép so ở N1 so với 0/15 ở N0) nhưng thiết kế cũ không sạch: siêu tham số của N1 lấy lại từ N0 và quần thể huấn luyện lệch 2 máy.
- Hàm mất mát tuyệt đối có đưa mô hình cây vượt naïve theo MAE trên máy ảo hay không. Hiện chỉ có SVR làm được, mà SVR khác cả hàm mất mát lẫn cỡ mẫu nên không tách được nguyên nhân.
- Có quy tắc sàng lọc theo từng máy, tính trên lịch sử huấn luyện, dự đoán được máy nào đáng dùng mô hình hay không. Đây là câu hỏi mà Christofidi để ngỏ (§3.3: "identify the data subset for which a simple forecast does not deliver the desired end-to-end performance").

---

## 3. Tên đề tài và câu hỏi nghiên cứu

### 3.1 Tên

- Tiếng Việt: **Dự báo tải CPU theo từng máy trên đám mây: ảnh hưởng của chuẩn hoá, hàm mất mát và tiêu chí đánh giá đến so sánh với dự báo naïve**
- Tiếng Anh: **Per-machine CPU load forecasting in the cloud: how scaling, training loss and evaluation criterion affect the comparison with naïve forecasting**

Hai tên không khẳng định trước bên nào thắng. Cụm "trung tâm dữ liệu khác" bị loại; phần chuyển giao gọi là *model reuse across traces*, vì E1 và E2 cùng một trung tâm dữ liệu phân tán của Bitbrains.

### 3.2 Câu hỏi nghiên cứu

| Mã | Câu hỏi | Thí nghiệm | Giá trị khi mô hình thắng | Giá trị khi mô hình thua |
|---|---|---|---|---|
| RQ1 | Với dự báo CPU theo từng máy, kết luận "mô hình có vượt naïve không" thay đổi bao nhiêu khi đổi chuẩn hoá, hàm mất mát và tiêu chí đánh giá, ở ba chân trời dự báo | TN-A, mục 5.1 | Chỉ ra cấu hình tối thiểu để mô hình có ích, và mức cải thiện đo được | Chỉ ra rằng kết luận âm của các bài trước bền vững kể cả khi đã chỉnh ba yếu tố có lợi cho mô hình |
| RQ2 | Kết luận của RQ1 có giữ nguyên qua các giai đoạn thời gian khác nhau không | TN-B, mục 5.2 | Cho biết mức cải thiện ổn định hay chỉ xuất hiện ở vài ngày | Cho biết một lần chia dữ liệu duy nhất đủ để đảo kết luận, tức cảnh báo về cách đánh giá của các bài trước |
| RQ3 | Mô hình học ở một tập vết dùng lại được ở tập vết khác đến mức nào, khi đo bằng cả mô hình học tại đích lẫn naïve tại đích | TN-C, mục 5.3 | Xác định chiều chuyển giao và chế độ chuẩn hoá dùng lại được | Xác định ngưỡng mà dùng lại mô hình kém hơn cả naïve, là thông tin trực tiếp cho người vận hành |

Phần sàng lọc theo từng máy nằm ở mục 5.4, đặt ở mức phân tích thăm dò, chưa tuyên bố là đóng góp.

---

## 4. Nguyên tắc phương pháp và hiện trạng mã nguồn

| # | Nguyên tắc | Hiện trạng đã kiểm | Việc phải làm |
|---|---|---|---|
| 1 | Tiền xử lý chỉ dùng lịch sử có sẵn tại thời điểm dự báo | `build.py` gọi `filter.judge` trên cả cửa sổ 8 ngày; CPU trung bình và số giá trị phân biệt tính trên cả phần test | Chuyển tiêu chí lọc sang phần huấn luyện của từng fold |
| 2 | Lọc máy, phân tầng mẫu, tính thống kê chuẩn hoá và chọn tham số đều theo ranh giới thời gian của fold | `normalize` đã tính mu và sd trên train; tầng CV cho mẫu con SVR lấy từ `cv.csv` tính trên cả 8 ngày | Tính lại tầng CV trên phần train; ghi rõ mọi thống kê lấy từ đâu |
| 3 | Giữ ngưỡng loại máy CPU trung bình dưới 1% thì phải nêu phạm vi quần thể và kiểm độ nhạy | Ngưỡng đang loại 454/1250 chuỗi E1 và 197/500 chuỗi E2 | Báo cáo kết quả ở hai quần thể: đã lọc và toàn bộ. Không loại thêm máy vì khó dự báo |
| 4 | Sửa seasonal naïve, đưa y(t) vào đầu vào, thống nhất thời điểm thông tin giữa các mô hình | `du_doan_seasonal` dùng y(t−288) thay vì y(t+h−288); 19 đặc trưng không có y(t); `du_doan_ma6` bỏ điểm hiện tại | Sửa cả ba, xem mục 6 |
| 5 | Kiểm nội suy trên đầu vào, lag, rolling và nhãn | Mới đo tỉ lệ y(t) nội suy trên test: 0,039% ở E1, 0,022% ở E2, 0,002% ở E3 | Đo thêm tỉ lệ dòng có bất kỳ điểm nội suy nào trong cửa sổ [t−24, t] và tỉ lệ nhãn y(t+h) nội suy; chạy lại bản K = 0 để đối chứng |
| 6 | MAE là chỉ số chính, kèm RMSE và MASE, không đổi chỉ số chính theo kết quả | `metrics.py` đã tính đủ năm chỉ số theo từng máy | Khai báo chỉ số chính trong phần Phương pháp trước khi báo kết quả |
| 7 | Thử hàm mất mát bình phương và tuyệt đối trên ít nhất một họ mô hình | Chỉ SVR dùng hàm ε-insensitive, và SVR đồng thời khác cỡ mẫu | Thêm XGBoost với `reg:absoluteerror` và HistGradientBoosting với `absolute_error`, giữ nguyên mọi thứ khác |
| 8 | So N0 và N1 trên cùng quần thể và cùng tập test, tách tác động chuẩn hoá khỏi thay đổi trọng số sai số giữa các máy | Bản N1 hiện loại 2, 1 và 10 máy khỏi phần huấn luyện, nên quần thể huấn luyện khác N0 | Sau khi áp nguyên tắc 1, kiểm tra lại có còn máy nào phải loại riêng cho N1 không; nếu còn thì loại cùng danh sách đó ở cả N0 |
| 9 | Thay từng yếu tố một | v4 đổi đồng thời chuẩn hoá, đặc trưng và giá trị cần dự đoán giữa N0, N1, N2 | Thiết kế TN-A theo lưới hai yếu tố, mục 5.1 |
| 10 | Đánh giá nhiều cửa sổ trên Bitbrains; chỉ nối các tháng E2 nếu xác minh được danh tính máy | **Đã kiểm: không nối được.** Trên mẫu 60 máy, chỉ 31 máy giữ nguyên cả ba thuộc tính số nhân, xung nhịp và dung lượng RAM qua ba tháng. Giữa hai tháng liên tiếp còn một khoảng hở đúng một ngày | Đánh giá ba tháng của E2 như ba giai đoạn riêng. E1 có 30 ngày liên tục nên dùng cửa sổ trượt |
| 11 | Giữ giới hạn 8 ngày của Alibaba | Đúng như v4 | Nêu rõ: mọi phát biểu về độ ổn định thời gian không áp dụng cho Alibaba |
| 12 | Ghi nhận phần test cũ đã dùng để phân tích thiết kế | Tập test 8 ngày của cả ba môi trường đã được xem nhiều lần, kể cả trong đợt rà soát 19/09 | Không gọi phần đó là holdout. Giai đoạn chưa đụng tới: E1 từ 20/08 đến 11/09, E2 tháng 7 và tháng 9. Chốt thiết kế trên cửa sổ 8 ngày rồi chạy xác nhận đúng một lần trên hai giai đoạn đó |
| 13 | Chốt cách hiệu chỉnh nhiều phép kiểm trước lượt chạy chính | Mã hiện hiệu chỉnh Holm trên 28 cặp trong mỗi tổ hợp môi trường và chân trời; bản thảo lại mô tả 15 phép so | Chốt họ kiểm định là các phép so mô hình với naïve trong một tổ hợp, ghi vào Phương pháp trước khi chạy |
| 14 | Báo cáo độ lớn cải thiện, tỉ lệ máy thắng và độ bất định; xét phụ thuộc giữa máy và giữa ngày | Chỉ có p-value và trung vị | Thêm khoảng tin cậy bootstrap theo máy, và bootstrap theo khối ngày cho TN-B |
| 15 | Không suy ra giảm vi phạm SLA từ RMSE | v4 chưa mắc, nhưng phần diễn giải RMSE mới dễ mắc | Nếu muốn nói về chi phí vận hành thì tính thẳng hàm chi phí bất đối xứng, kèm câu ghi rõ đây là mô hình chi phí giản lược |
| 16 | Lưu dự đoán từng dòng | Chỉ lưu chỉ số theo máy | Thêm tệp parquet: `series_id, bucket, h, model, loss, scaling, fold, seed, y, yhat`, kèm `meta.json` ghi cấu hình và mã commit |

---

## 5. Thiết kế thực nghiệm

Ba thí nghiệm chính và một phân tích thăm dò. Mọi thí nghiệm dùng chung: lưới 5 phút, 19 đặc trưng cộng y(t), luật dòng hợp lệ [t−24, t] sạch và y(t+h) không thiếu, chia theo bucket có purge, chỉ số tính theo từng máy rồi lấy trung vị, `random_state = 42`.

### 5.1 TN-A: yếu tố quyết định kết luận

| Mục | Nội dung |
|---|---|
| Mục đích | RQ1 |
| Dữ liệu | E1, E2, E3, cửa sổ 8 ngày chung, quần thể đã lọc theo nguyên tắc nhân quả |
| Chia thời gian | Train [0, 1612), Validation [1612, 1957), Test [1957, 2304); rolling-origin 5 fold trong vùng validation để chọn siêu tham số |
| Yếu tố thay đổi | Chuẩn hoá: N0 thô, N1 z-score theo từng máy. Hàm mất mát: bình phương, tuyệt đối. Chân trời: 1, 6, 12 bước |
| Yếu tố giữ cố định | Bộ đặc trưng, quần thể máy, tập test, cách chia, cách gộp chỉ số, seed |
| Mô hình | Naïve, seasonal naïve theo ngày, trung bình trượt, Ridge, XGBoost, DLinear, GRU, SVR |
| Chỉ số | MAE chính; RMSE và MASE báo kèm; thêm bảng chi phí bất đối xứng ở mục phân tích |
| Tiêu chí diễn giải | Một mô hình được coi là vượt naïve khi Wilcoxon ghép cặp có p sau hiệu chỉnh Holm dưới 0,05 và trung vị hiệu ghép cặp âm. Kèm tỉ lệ máy thắng và khoảng tin cậy bootstrap của tỉ số trung vị |

Lưới yếu tố áp cho Ridge và XGBoost, là hai họ mô hình đổi được hàm mất mát mà không đổi kiến trúc. DLinear và GRU chạy ở hàm mất mát tuyệt đối với chuẩn hoá theo từng chuỗi, đúng cách dùng phổ biến của hai mô hình đó, và được đánh dấu là cấu hình mặc định chứ không phải một ô của lưới. SVR giữ nguyên hàm ε-insensitive, thêm một phép kiểm độ nhạy cỡ mẫu con 10.000 so với 30.000 dòng.

### 5.2 TN-B: độ ổn định theo thời gian

| Mục | Nội dung |
|---|---|
| Mục đích | RQ2 |
| Dữ liệu | E1 đủ 30 ngày, từ 12/08 đến 11/09/2013. E2 ba tháng, mỗi tháng một giai đoạn riêng, không nối |
| Chia thời gian | Cửa sổ mở rộng dần, huấn luyện lại mỗi 7 ngày, chấm trên từng ngày kế tiếp. E1 cho khoảng 16 ngày test sau khi trừ 14 ngày lịch sử tối thiểu |
| Yếu tố thay đổi | Giai đoạn test |
| Yếu tố giữ cố định | Cấu hình thắng ở TN-A, bộ đặc trưng, quần thể, siêu tham số chọn trong từng fold theo đúng ranh giới thời gian |
| Mô hình | Naïve, seasonal naïve theo ngày, seasonal naïve theo tuần khi lịch sử đủ 14 ngày, Ridge, XGBoost, DLinear |
| Chân trời | 1 và 12 bước, để giữ chi phí |
| Chỉ số | Như TN-A, cộng thêm phân bố kết quả theo ngày và theo thứ trong tuần |
| Tiêu chí diễn giải | Báo cáo số ngày test mà mô hình vượt naïve trên tổng số ngày, kèm bootstrap theo khối ngày. Không lấy trung bình gộp mọi ngày rồi kết luận một con số |

E3 không tham gia TN-B vì chỉ có 8 ngày. Phần kết luận ghi rõ giới hạn đó.

### 5.3 TN-C: dùng lại mô hình giữa các tập vết

| Mục | Nội dung |
|---|---|
| Mục đích | RQ3 |
| Dữ liệu | Cửa sổ 8 ngày chung của E1, E2, E3; sáu chiều nguồn và đích |
| Chia thời gian | Huấn luyện trên [0, 1957) của nguồn, chấm trên [1957, 2304) của đích |
| Yếu tố thay đổi | Chiều chuyển giao, chuẩn hoá N0 và N1 |
| Yếu tố giữ cố định | Mô hình, siêu tham số theo môi trường nguồn, tập test của đích, cách gộp |
| Mô hình | Ridge, XGBoost, DLinear |
| Chỉ số | Hai tỉ số bắt buộc báo cùng nhau: L bằng MAE mô hình chuyển sang chia MAE mô hình học tại đích, và MAE mô hình chuyển sang chia MAE naïve tại đích |
| Tiêu chí diễn giải | Chỉ kết luận "dùng lại được" khi cả hai tỉ số đều dưới 1. Dẫn kết quả của Rossi §5.2 để nêu điểm giống và khác |

Thí nghiệm máy giả giữ nguyên thiết kế cũ, chạy lại sau khi sửa pipeline, đặt ở phần phân tích bổ sung của TN-C.

### 5.4 Phân tích thăm dò: sàng lọc theo từng máy

Câu hỏi: từ thống kê tính trên phần huấn luyện của mỗi máy, gồm tự tương quan bậc 1, hệ số biến thiên, ARD theo định nghĩa của Christofidi §3.1 và mức tải trung bình, có dự đoán được máy nào mô hình sẽ vượt naïve hay không.

Cách làm: hồi quy logistic hoặc cây quyết định nông, khớp trên E1 giai đoạn đầu, chấm trên E2 và trên các giai đoạn sau của E1. Báo cáo AUC và độ lợi khi chỉ áp mô hình cho nhóm máy được sàng chọn.

Ghi rõ trong bài: đây là phân tích thăm dò, không phải một phương pháp được đề xuất. Nếu AUC không vượt mức ngẫu nhiên thì báo cáo đúng như vậy.

---

## 6. Bộ mô hình và vai trò

| Mô hình | Vai trò | Lý do giữ hoặc thêm |
|---|---|---|
| Naïve y(t+h) = y(t) | Mốc chính | Là đối tượng của cả ba câu hỏi |
| Seasonal naïve y(t+h−288) | Mốc khai thác chu kỳ ngày | Công thức hiện tại sai thời điểm; bản sửa giảm MAE từ 12% đến 34% và ở E2 h = 6 còn thấp hơn naïve |
| Trung bình trượt gồm y(t) | Mốc làm trơn | Bản hiện tại bỏ điểm hiện tại nên yếu hơn mức đáng có |
| Ridge | Mốc dưới của nhóm học máy, đổi được hàm mất mát qua hồi quy phân vị 0,5 | Rẻ, dùng để kiểm lưới hai yếu tố |
| XGBoost | Mô hình cây chính, đổi hàm mất mát bằng `reg:absoluteerror` | Đã có trong pipeline, chi phí đo được 0,15 giờ cho mỗi tổ hợp môi trường và chân trời |
| DLinear | Mô hình chuỗi thời gian tuyến tính trên cửa sổ, chuẩn hoá theo từng chuỗi | Trả lời trực tiếp yêu cầu của thầy về mô hình hiện đại, và là mốc mạnh trong dòng nghiên cứu phản biện Transformer |
| GRU | Đại diện mạng hồi tiếp, phạm vi hẹp | Christofidi chỉ thử LSTM trên Google, nên cần một mạng hồi tiếp chạy trên dữ liệu theo từng máy. Đo được 1.220 giây mỗi epoch với cửa sổ 288 bước trên chính môi trường nhỏ nhất, tức không đưa vào lưới chính được; giữ ở phạm vi hẹp, xem báo cáo ngân sách |
| SVR | Chứng cứ về ảnh hưởng của hàm mất mát | Là mô hình duy nhất trong v4 có MAE trung vị thấp hơn naïve ở cả sáu ô máy ảo, và cũng là mô hình duy nhất dùng hàm ε-insensitive |
| Random Forest | Chỉ giữ ở phụ lục để nối với v4 | Chiếm 7,35 giờ trong tổng 9,99 giờ của Thí nghiệm 1, tức 74% chi phí, mà không trả lời câu hỏi nào của v5 |

Không thêm PatchTST, ARIMA hay ETS ở lượt này. PatchTST chỉ thêm nếu phản biện đòi một mô hình Transformer. ARIMA và ETS chỉ thêm nếu chuyển sang so sánh mô hình riêng cho từng máy, là một câu hỏi khác.

---

## 7. Danh sách sửa mã nguồn theo ưu tiên

Mọi đường dẫn đã mở và kiểm trong lượt này.

### P0: sửa tính đúng, phải xong trước mọi lượt chạy

| Mã | Việc | Tệp và hàm |
|---|---|---|
| P0-1 | Seasonal naïve lấy khoá `bucket + h − 288`; thêm tham số `h` | `src/cwp/models/baselines.py`, `du_doan_seasonal`, `du_doan` |
| P0-2 | Trung bình trượt tính trên y(t−5) đến y(t) | `src/cwp/models/baselines.py`, `du_doan_ma6` |
| P0-3 | Thêm đặc trưng y(t) | `src/cwp/features/spec.py` (`LAGS`, `FEATURE_COLS`, hai câu lệnh assert 19 và 22), `src/cwp/features/windows.py`, `add_lag_features` |
| P0-4 | Lọc chuỗi chỉ trên phần huấn luyện | `src/cwp/preprocess/filter.py`, `judge`; `src/cwp/preprocess/build.py`, hai vòng lặp gọi `judge(w_interp)` |
| P0-5 | Tầng độ giật tính trên phần train | `src/cwp/evaluation/tang.py`, `scripts/describe_data.py` |
| P0-6 | Lưu dự đoán từng dòng kèm siêu dữ liệu | `scripts/run_experiments.py` (`cham_test`), `scripts/run_transfer.py`, `scripts/run_tai_cho_may_gia.py` |
| P0-7 | Đo nội suy đầy đủ: dòng có điểm nội suy trong cửa sổ đặc trưng, nhãn nội suy, và bản đối chứng K = 0 | `src/cwp/preprocess/resample.py` đã có tham số `k`; thêm script báo cáo |

### P1: mở rộng thiết kế

| Mã | Việc | Tệp và hàm |
|---|---|---|
| P1-1 | Hàm mất mát tuyệt đối | `src/cwp/models/registry.py`: thêm `XGBRegressor(objective="reg:absoluteerror")` và `HistGradientBoostingRegressor(loss="absolute_error")`; xgboost 2.1.3 và scikit-learn 1.5.2 trong `requirements.txt` đều hỗ trợ |
| P1-2 | Cửa sổ và ranh giới theo tham số | `src/cwp/evaluation/splits.py`: `WINDOW_BUCKETS`, `N_TRAIN`, `N_VAL` và ba câu lệnh assert đang ghi cứng cho 8 ngày; `config/preprocess.yaml`, khoá `window.days` |
| P1-3 | Cửa sổ trượt nhiều mốc test | Thêm `scripts/run_rolling.py` dùng lại `fold_masks` và `mask_khoang` |
| P1-4 | E2 ba tháng như ba giai đoạn riêng | `config/datasets.yaml`, mục E2; `src/cwp/io/bitbrains.py`, `make_series_id` đã khoá theo tháng |
| P1-5 | DLinear và GRU | Môi trường ảo riêng, không đụng `requirements.txt` đang ghim; bộ nạp dữ liệu đọc thẳng `data/processed/{env}.parquet` và dùng đúng mặt nạ test của `splits.py` |
| P1-6 | Bootstrap theo máy và theo khối ngày; chốt họ kiểm định | `scripts/fig_tn1.py`, `kiem_dinh_cap` và `bang_ml_vs_naive` |
| P1-7 | Hàm chi phí bất đối xứng, tính từ dự đoán đã lưu | Thêm hàm vào `src/cwp/evaluation/metrics.py` |

### P2: sau khi có kết quả

| Mã | Việc |
|---|---|
| P2-1 | Cập nhật `scripts/doi_chieu_so_lieu_bai_bao.py`, hiện đối chiếu 175 con số của v4 |
| P2-2 | Chạy lại notebook 01 đến 09 và sửa phần mô tả cho khớp thiết kế mới |
| P2-3 | Viết v5 theo mục 10 |

---

## 8. Kết quả cũ: giữ ở mức thăm dò hay chạy lại

| Kết quả v4 | Trạng thái | Lý do |
|---|---|---|
| Bảng 1, thống kê mô tả ba môi trường | Chạy lại | Bộ lọc đổi theo P0-4; ACF trên 8 ngày cần đặt cạnh ACF trên 30 ngày |
| Bảng 3, học máy so với naïve | Chạy lại toàn bộ | Thiếu y(t), seasonal naïve sai, chỉ một chỉ số, một cửa sổ test |
| Bảng 4 và Hình 4, mất mát chuyển giao L | Chạy lại | Phụ thuộc đặc trưng và quần thể đã đổi; thiếu mốc naïve tại đích |
| Bảng 2 và ba tính chất kiểm chuẩn hoá | Giữ | Là phép kiểm hiện thực, không phụ thuộc thiết kế đánh giá |
| Bảng 5, máy đứng yên ở N1 | Giữ ở mức minh hoạ trong phụ lục | Sau P0-4 thì tình huống không còn phát sinh; cả 10 máy E3 gây lỗi đều có CPU trung bình phần train dưới 1% |
| Lỗi giá trị cần dự đoán của N2 | Giữ một đoạn ngắn trong phần kiểm tra quy trình | Là lỗi viết mã, đã sửa |
| Thí nghiệm máy giả | Chạy lại, giữ vai trò phân tích bổ sung | Rẻ, đo được 0,98 giờ |
| Con số SVR có MAE trung vị thấp hơn naïve ở sáu ô máy ảo | Thăm dò, là giả thuyết đầu vào của RQ1 | SVR khác cả hàm mất mát lẫn cỡ mẫu nên chưa tách được nguyên nhân |
| Con số N1 tại chỗ thắng naïve 7/15 ở E1 | Thăm dò, là giả thuyết đầu vào của RQ1 | Siêu tham số lấy lại từ N0 và quần thể huấn luyện lệch 2 máy |
| RMSE cho kết quả ngược MAE ở máy ảo | Thăm dò, là giả thuyết đầu vào của RQ1 | Tính từ tệp kết quả cũ, chưa qua pipeline đã sửa |

---

## 9. Chi phí và thứ tự triển khai

### 9.1 Chi phí đã đo của v4

Tính từ `cv_search_tn1.csv`, `chosen_tn1.csv` và các tệp `meta_*.json`. Máy 12 nhân CPU, không có GPU NVIDIA.

| Lượt chạy | Giờ | Ghi chú |
|---|---|---|
| Thí nghiệm 1 | 9,99 | Random Forest 7,35; XGBoost 1,34; SVR 1,23; Ridge 0,05; hồi quy tuyến tính 0,02 |
| Thí nghiệm 2, chuyển giao | 14,02 | 108 tổ hợp, 816 lần chấm test |
| Mô hình học tại chỗ | 4,58 | |
| Máy giả | 0,98 | |
| N1 chạy lại | 1,86 | |
| N2 chạy lại | 1,83 | |
| Tổng | 33,26 | |

### 9.2 Ước lượng cho v5

Ước lượng suy từ chi phí đo được, theo số tổ hợp và theo số dòng. Phần chưa đo thì ghi là chưa đo.

| Lượt chạy | Cơ sở tính | Ước lượng |
|---|---|---|
| Sinh lại đặc trưng cho cả ba môi trường, thêm y(t) | Bước cũ mất vài chục phút | dưới 1 giờ |
| TN-A, Ridge và XGBoost, 2 chuẩn hoá × 2 hàm mất mát × 3 môi trường × 3 chân trời | XGBoost đo được 0,15 giờ cho mỗi tổ hợp môi trường và chân trời, đã gồm dò 3 ứng viên trên 5 fold | 5 đến 6 giờ |
| TN-A, SVR, 2 chuẩn hoá, thêm phép kiểm cỡ mẫu | 1,23 giờ cho một cấu hình | 3 đến 4 giờ |
| TN-A, DLinear và GRU | Chưa đo | chạy thử trước, mục 9.3 |
| TN-B trên E1 30 ngày và E2 ba tháng | Dữ liệu E1 gấp 3,75 lần cửa sổ 8 ngày; huấn luyện lại mỗi 7 ngày nên số lần khớp ít | chưa đo, ước lượng sau bước chạy thử |
| TN-C, 6 chiều × 2 chuẩn hoá × 3 mô hình × 3 chân trời | Bản cũ 14,02 giờ cho 108 tổ hợp gồm cả Random Forest và SVR | 2 đến 3 giờ |
| Máy giả | Đo được 0,98 giờ | khoảng 1 giờ |

Bỏ Random Forest khỏi phần chính cắt được phần lớn chi phí của Thí nghiệm 1 cũ.

### 9.3 Chạy thử để đo trước khi cam kết

Đã chạy ngày 20/09/2026 trên E2, h = 1, chấm trên validation. Số đo và ngân sách suy ra từ đó nằm ở `bao-cao-sua-p0-va-ngan-sach.md`.

### 9.4 Thứ tự triển khai

| Giai đoạn | Nội dung | Điều kiện chuyển tiếp |
|---|---|---|
| 1 | P0-1 đến P0-7, sinh lại đặc trưng | Các phép kiểm hiện thực cũ vẫn đạt, và tỉ lệ dòng chạm nội suy được báo cáo |
| 2 | Chạy thử ba bước ở mục 9.3 | Có số đo thời gian cho DLinear và GRU |
| 3 | Chốt phạm vi TN-A, ghi Phương pháp và tiêu chí kiểm định vào một tệp chốt trước khi chạy | Tệp chốt có ngày tháng và không sửa về sau |
| 4 | Chạy TN-A trên cửa sổ 8 ngày | Kết quả đủ để chọn cấu hình cho TN-B |
| 5 | P1-2, P1-3, P1-4 rồi chạy TN-B | |
| 6 | Chạy TN-C và máy giả | |
| 7 | Chạy xác nhận trên giai đoạn chưa đụng tới: E1 từ 20/08 đến 11/09, E2 tháng 7 và tháng 9 | Chạy đúng một lần, không quay lại chỉnh thiết kế sau khi xem kết quả |
| 8 | Viết v5 | |

---

## 10. Kế hoạch viết v5

Theo yêu cầu: viết tiếng Anh trên mẫu HJS trước để duyệt, bản VJCS làm sau.

Mẫu `paper/sample/HJS@Template-OTH.docx` quy định: khổ giấy 20,5 × 28,5 cm, font Cambria 10pt cho thân bài và 9pt cho phần tóm tắt, tên bài viết hoa, chú thích bảng đặt phía trên bảng, chú thích hình đặt phía dưới hình, tài liệu tham khảo đánh số theo thứ tự trích dẫn.

`paper/SKILL.md` áp cho bản tiếng Anh qua mục 18: dấu thập phân là dấu chấm, dấu phân cách hàng nghìn là dấu phẩy, đơn vị cách số một khoảng trắng, khoảng giá trị dùng gạch ngang en không có khoảng trắng, không dùng dạng rút gọn, dùng "we", không dùng số trích dẫn làm chủ ngữ, tóm tắt không chứa trích dẫn và công thức, tránh nhóm từ bị lạm dụng trong văn AI và các khuôn câu tương ứng. Cấm tuyệt đối gạch ngang em.

Bố cục dự kiến:

| Mục | Nội dung |
|---|---|
| I. Introduction | Bài toán, hai kết quả đã có của Christofidi và Rossi, khoảng trống theo Nhóm B ở mục 2.2, ba câu hỏi |
| II. Related work | Ba nhóm: dự báo tải đám mây, mốc so sánh và cách đánh giá dự báo, dùng lại mô hình giữa các miền dữ liệu. Mỗi khẳng định gắn một trích dẫn cụ thể |
| III. Data and method | Ba tập vết, tiền xử lý nhân quả, đặc trưng, chia thời gian, mô hình, chỉ số, kiểm định. Bảng số mẫu ở Phụ lục A của báo cáo rà soát dán vào đây |
| IV. Experiments | TN-A, TN-B, TN-C theo đúng thứ tự ba câu hỏi |
| V. Discussion | So sánh trực tiếp với hai bài trước, nêu chỗ giống và chỗ khác |
| VI. Limitations | Alibaba 8 ngày, quần thể đã lọc, đơn vị quan sát lệch, phần test cũ đã dùng cho phân tích thiết kế |
| VII. Conclusion | Trả lời ba câu hỏi bằng con số |
| Appendix | Kiểm tra tính đúng của quy trình, gồm hai lỗi chuẩn hoá và ba tính chất kiểm |

Tài liệu tham khảo: mở từng nguồn đối chiếu trước khi đưa vào, theo mục 17 bước 14 của SKILL.md. Hai nguồn đã đọc toàn văn là Christofidi và Rossi. Các nguồn liệt kê trong báo cáo rà soát vẫn ở trạng thái cần kiểm DOI.

---

## 11. Đánh giá trung thực về đóng góp

**Điểm mạnh của phương án.** Cả hai bài trước đều bỏ trống đúng chỗ mà đề tài đang đứng: Christofidi kết luận dự báo naïve đủ tốt nhưng chỉ chạy dự báo trên bốn job của Google, còn với Bitbrains và Alibaba thì chỉ đo tính bền của dữ liệu; Rossi làm chuyển giao nghiêm túc nhưng trên chuỗi trung bình của cụm và không có mốc naïve. Một đối chứng theo từng máy, có mốc naïve, có kiểm định ghép cặp, trên 1.535 chuỗi và ba chân trời dự báo, là phần thực nghiệm chưa ai công bố ở dạng đó.

**Điểm yếu.** Đóng góp thuộc loại đo đạc và thiết kế đánh giá, không có phương pháp mới. Phản biện có thể xếp bài vào nhóm khảo sát tham số. Ba yếu tố khảo sát là chuẩn hoá, hàm mất mát và chỉ số, đều đã được biết trong tài liệu dự báo chuỗi thời gian nói chung; phần mới nằm ở chỗ đo chúng trên bài toán tải đám mây theo từng máy, chứ không ở bản thân ý tưởng.

**Ngưỡng để bài đứng được.** Kết quả phải cho thấy một trong hai điều, và phải nêu bằng con số: hoặc có cấu hình cụ thể làm mô hình vượt naïve ổn định qua nhiều giai đoạn thời gian, hoặc kết luận âm giữ nguyên kể cả sau khi đã chỉnh cả ba yếu tố theo hướng có lợi cho mô hình. Trường hợp thứ hai vẫn là kết quả dùng được, vì nó bác bỏ giả thuyết "thua là do cấu hình" một cách có kiểm soát, điều mà Christofidi không kiểm.

**Nếu kết quả rơi vào vùng xám**, tức mỗi giai đoạn một kiểu và không cấu hình nào ổn định, thì phần khác biệt còn lại quá mỏng cho một tạp chí. Khi đó còn hai lối: chuyển trọng tâm sang phần sàng lọc theo từng máy ở mục 5.4 nếu quy tắc sàng chạy được, hoặc hạ mục tiêu xuống hội nghị trong nước. Tình huống đó cần được nói thẳng khi có kết quả TN-A và TN-B, không chờ đến lúc viết xong bài.

**Không thể hứa trước** bài sẽ được VJCS chấp nhận, và cũng không nên đặt mục tiêu số lượng tài liệu tham khảo.

---

## 12. Sáu điểm đã chốt và bảy điều chỉnh kèm theo

Chốt ngày 20/09/2026.

| # | Điểm đã chốt | Cách thực hiện |
|---|---|---|
| 1 | Bỏ Random Forest khỏi lưới chính | Giữ nguyên mã và kết quả cũ. Kiểm tra bổ sung phạm vi nhỏ, cấu hình và cửa sổ định trước bằng dữ liệu phát triển. Số Random Forest báo trong v5 phải sinh từ pipeline đã sửa, không lấy lại số v4 |
| 2 | Ngưỡng CPU trung bình train từ 1% trở lên cho quần thể chính | Phạm vi ghi là "máy đã hoạt động trong lịch sử". Độ nhạy chạy trên các ngưỡng định trước 0%, 0,5%, 1% và 2%, trong đó 0% là không lọc theo mức tải nhưng vẫn kiểm chất lượng dữ liệu. Ngưỡng không chọn theo kết quả. Quy tắc lọc áp theo ranh giới thời gian của từng fold và dùng chung cho mọi cấu hình được so sánh |
| 3 | Không nối ba tháng E2 | Đánh giá riêng từng tháng. Cách diễn giải: chưa đủ bằng chứng để nối an toàn. Thay đổi cấu hình phần cứng không chứng minh đó là máy khác |
| 4 | N2 xuống phần bổ sung | Phần chính chỉ có N0 và N1. Số N2 nào xuất hiện trong v5 cũng phải sinh từ pipeline đã sửa |
| 5 | Phân tích sai số bất đối xứng | Tính từ dự đoán đã lưu, với vài tỉ lệ phạt thiếu so với dư được chốt trước. Gọi đúng tên là phân tích theo kịch bản giả định. Không suy ra chi phí tài chính, không suy ra mức giảm vi phạm SLA. Chưa huấn luyện mô hình bằng hàm mất mát bất đối xứng, chưa dựng bộ mô phỏng cấp phát |
| 6 | Phân tích nhóm máy ở mức thăm dò | Đặc điểm chia nhóm tính từ lịch sử. Không chọn riêng máy có kết quả test thuận lợi rồi khái quát. Chưa xây cơ chế chọn mô hình tự động |

Bảy điều chỉnh kèm theo:

1. **Ranh giới dữ liệu chưa chấm mô hình** được định nghĩa lại ở mục 12.1.
2. **Lưới hai hàm mất mát chỉ áp cho XGBoost.** Ridge giữ bình phương kèm phạt L2, SVR giữ ε-insensitive; hai mô hình đó không phải hai ô tương đương của cùng lưới. Nhãn hàm mất mát của từng mô hình ghi trong `src/cwp/models/registry.py` và đi theo mọi dòng dự đoán.
3. **Chốt trước lượt xác nhận**: cách chọn siêu tham số, chỉ số dùng để chọn cấu hình, seed, danh sách cửa sổ đánh giá và họ kiểm định. MAE là chỉ số chính; RMSE và MASE báo kèm; độ lớn cải thiện báo kèm mọi phép kiểm.
4. **Kết quả đổi theo giai đoạn không phải thất bại của đề tài.** Tiêu chí đánh giá là mức thay đổi có đo được, giải thích được và kiểm chứng được hay không. Không chọn kết luận theo mong muốn.
5. **DLinear và GRU đo thử trên dữ liệu phát triển**, không dùng giai đoạn xác nhận để chọn thiết kế.
6. **Dự đoán từng dòng được lưu** kèm giá trị thật, mã máy, thời điểm phát dự báo, thời điểm mục tiêu, tầm dự báo, fold, seed và cấu hình. Kết quả v4 và v5 để riêng.
7. **Chưa định dạng v5 theo HJS.** Đích nộp vẫn là VJCS. Ưu tiên bản nội dung dễ sửa; chuyển sang mẫu của nơi nộp sau. Chưa viết kết luận khi chưa có kết quả.

### 12.1 Dữ liệu nào đã xem, dữ liệu nào chưa chấm mô hình

Báo cáo rà soát ngày 19/09 đã tính thống kê mô tả trên **đủ 30 ngày của E1**: tự tương quan ở ba độ trễ và CPU trung bình theo từng ngày. Vì vậy phần đó **không còn là dữ liệu chưa xem**. Phân biệt hai mức:

| Mức | Nghĩa | Phần dữ liệu |
|---|---|---|
| Đã chấm mô hình | Có mô hình huấn luyện hoặc chấm điểm trên đó | E1, E2, E3: cửa sổ 8 ngày đầu, cả ba tập train, validation và test |
| Đã xem thống kê mô tả | Có tính thống kê nhưng chưa mô hình nào chạm | E1 từ 20/08 đến 11/09: tự tương quan và CPU trung bình theo ngày |
| Chưa đụng tới | Chưa tính gì trên giá trị CPU | E2 tháng 7 và tháng 9; E2 tháng 8 sau 08/08 22:00 |

Ranh giới cho lượt xác nhận cuối, chọn để không chồng lên tập test cũ:

| Môi trường | Tập test cũ kết thúc | Giai đoạn xác nhận | Mức |
|---|---|---|---|
| E1 | 20/08/2013 13:40 | từ 20/08/2013 13:40 đến 11/09/2013 | đã xem thống kê mô tả |
| E2 | 08/08/2013 22:00 | tháng 7/2013 và tháng 9/2013, mỗi tháng đánh giá riêng | chưa đụng tới |
| E3 | ngày thứ 8 của trace | không có | hết dữ liệu |

Phần lịch sử dùng để huấn luyện cho lượt xác nhận được phép chồng lên cửa sổ 8 ngày cũ, vì ràng buộc nằm ở phần được chấm. Mọi bảng của lượt xác nhận ghi rõ mức dữ liệu theo cột "Mức" ở trên; riêng E3 không có kết quả xác nhận và điều đó phải nêu trong phần hạn chế.

## 12. Những điểm cần bạn chốt

