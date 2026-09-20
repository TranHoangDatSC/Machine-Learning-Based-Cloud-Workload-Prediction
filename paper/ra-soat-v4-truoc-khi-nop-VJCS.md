# Rà soát bản thảo v4 trước khi nộp VJCS

Ngày rà soát: 19/09/2026. Đầu vào gồm:

- `paper/ban-thao-v4.docx`: 19 tài liệu tham khảo, 5 bảng, 5 hình.
- Góp ý của thầy Khiết (Zalo, 19/09/2026).
- Nhận xét của GPT về bản v4.
- Mã nguồn và kết quả gốc trong `CWP-Cloud-Notebooks`: `src/cwp`, `scripts/`, `config/`, `results/ket_qua_chay_goc/`, `results/tables/`.
- Dữ liệu thô trong `ML-CWP-Cloud/data/raw`.

Mọi con số dưới đây được tính lại từ kết quả đã lưu hoặc từ dữ liệu thô bằng các phép tính chỉ đọc. Không huấn luyện lại mô hình nào và không sửa tệp nào trong hai repo. Cách tính từng con số ghi ở Phụ lục B.

---

## 0. Tóm tắt

**Kết luận chung: bản v4 chưa nộp được.** Thầy đúng ở phần lớn góp ý, chỉ nhầm ở chỗ Random Forest. GPT đúng ở gần hết các điểm, nhưng vì không có mã nguồn nên đã bỏ sót những vấn đề lớn nhất. Khi đối chiếu với dữ liệu thật, có 5 vấn đề nặng hơn mọi góp ý của cả hai:

| # | Vấn đề | Bằng chứng từ dữ liệu | Mức độ |
|---|---|---|---|
| A | **Kết luận chính đảo chiều khi đổi chỉ số.** Theo MAE, học máy thắng naïve 0/15 phép so ở E1 và 2/15 ở E2. Theo RMSE, con số là 9/15 ở E1 và 9/15 ở E2. | Wilcoxon và Holm tính lại trên `per_series_tn1.csv` (cột `rmse` đã có sẵn) | Chí mạng |
| B | **Chính dữ liệu của bài mâu thuẫn với câu "máy ảo không đáng dùng học máy".** Khi chuẩn hoá z-score theo từng máy (N1, đã chạy ở Thí nghiệm 2), học máy thắng naïve 7/15 ở E1 theo MAE và 15/15 theo RMSE. Bài không báo cáo điều này ở mục IV.A. | Bảng tại chỗ N1 ghép từ `tai_cho` và `n1_loai_dung_yen` | Chí mạng |
| C | **Validation của E1 rơi đúng Chủ nhật 18/08/2013, còn test là thứ Hai và thứ Ba.** MAE của naïve ở validation là 0,219, ở test là 0,408, gần gấp đôi. Siêu tham số được chọn trên một ngày cuối tuần. | Mốc `b0` trong `data/processed/E1.parquet` đổi ra lịch | Nặng |
| D | **Tính mới trùng với hai bài đã có.** Christofidi và cộng sự (ACM SoCC 2023) đặt đúng câu hỏi *"Is Machine Learning Necessary for Cloud Resource Usage Forecasting?"*. Rossi và cộng sự (Cluster Computing) đã kết luận rằng chuyển giao trong cùng nhà cung cấp chấp nhận được còn khác nhà cung cấp thì không. Bản v4 không trích dẫn bài nào trong hai bài này. | Tra cứu, xem mục 4 | Nặng |
| E | **Tiêu đề sai về dữ liệu.** E1 và E2 cùng thuộc *một* trung tâm dữ liệu phân tán của Bitbrains, nên kết quả chính E1↔E2 không phải "dùng lại ở trung tâm dữ liệu khác". | `data/raw/Bitbrains-*/about.md`: *"1,750 VMs from **a distributed datacenter** from Bitbrains"* | Nặng |

**Thứ tự nên làm:**

1. Sửa pipeline (mục 3, nhóm P0).
2. Chạy lại trên nhiều cửa sổ thời gian và thêm các mô hình đối chứng (nhóm P1).
3. Viết lại bài bằng tiếng Anh theo mẫu của World Scientific (nhóm P2).

Riêng việc bổ sung RMSE, MASE và bảng số mẫu **không cần chạy lại**, vì số liệu đã có sẵn trong các tệp kết quả.

---

## 1. Đối chiếu góp ý của thầy với dữ liệu thật

| # | Thầy nói | Dữ liệu thực tế | Kết luận |
|---|---|---|---|
| T1 | "Random Forest mẫu quá ít, trong khi SVR lại 10k mẫu, chênh lệch quá lớn" | RF học trên **toàn bộ** dòng huấn luyện: 1.395.851 dòng ở E1 (h=1), 573.692 ở E2, 766.720 ở E3. Con số 50 là **số cây** (`registry.py`, `_rf`: `n_estimators=50`, không đặt `max_samples`). **SVR mới là mô hình ít mẫu**: 10.000 dòng, tức 0,72% (E1), 1,74% (E2), 1,30% (E3) so với các mô hình khác. | **Sai ở RF, nhưng đúng về bản chất.** Chênh lệch cỡ mẫu có thật, chỉ là ở phía SVR. Câu trả lời của bạn với thầy, "vốn nó đã bị giới hạn vậy rồi", cũng chưa đúng: 50 cây là cấu hình nhóm tự chọn để giảm thời gian chạy (84,5 giây mỗi lần khớp), không phải giới hạn của thuật toán. |
| T2 | "Cần có thống kê số lượng mẫu" | Bài chỉ có số chuỗi (Bảng 1), không có số dòng huấn luyện, validation và test. | **Đúng.** Bảng dùng được ngay nằm ở Phụ lục A. |
| T3 | "Sao không so với LSTM, GRU, TCN, PatchTST, DLinear?" | Dữ liệu sau tiền xử lý **chỉ 7,9 MB** (`data/processed`). Tệp 9 GB chỉ đọc một lần ở bước tiền xử lý, nên lý do "nhẹ máy" không đứng vững. Máy hiện có 12 nhân CPU, không có GPU NVIDIA, môi trường chưa cài `torch`. | **Đúng về nhu cầu.** Không cần chạy đủ năm mô hình, xem P1-2. Lưu ý: tiêu đề v4 đã không còn cụm "Negative Results". |
| T4 | "8 ngày hơi ngắn, cần dẫn chứng vì sao chọn 8 ngày" | Mục III.C có nêu lý do: Alibaba chỉ có 8 ngày. Nhưng đó là lý do để **đồng bộ** ba môi trường, không chứng minh 8 ngày là **đủ đại diện**. Dữ liệu cho thấy không đủ: (i) E1 có 30 ngày, E2 có 3 tháng liền nhau, nhưng bài chỉ dùng 8 ngày; (ii) tự tương quan của E1 tính trên 8 ngày là 0,667 (bậc 1) và 0,133 (24 giờ), tính trên đủ 30 ngày là **0,806 và 0,269**; (iii) test chỉ dài 28,9 giờ, validation của E1 là Chủ nhật. | **Đúng, và nặng hơn thầy nói.** Các con số dùng để *giải thích* vì sao máy ảo khó đoán thay đổi mạnh theo độ dài cửa sổ. |
| T5 | "Tính chu kỳ tuần hoàn toàn bị bỏ qua" | Mã nguồn **có** hai đặc trưng `dow_sin` và `dow_cos`. Nhưng 8 ngày chỉ chứa một chu kỳ tuần, nên mỗi thứ trong tuần xuất hiện 1 đến 2 lần. Đặc trưng này thực chất thành nhãn "hôm nay là ngày nào", mô hình không học được chu kỳ tuần. Trên 30 ngày của E1: tự tương quan trễ 7 ngày có trung vị 0,146, thấp hơn trễ 1 ngày (0,269); 27% số máy có tương quan theo tuần cao hơn theo ngày. CPU trung bình theo ngày dao động từ 6,8 đến 17,8, có chỗ giảm vào cuối tuần nhưng không đều. | **Đúng một phần.** Chu kỳ tuần không bị bỏ qua trong mã nguồn, nhưng không học và không đánh giá được. Chu kỳ tuần ở Bitbrains yếu nhưng có thật, cần đo và báo cáo. |
| T6 | "Naïve 60 phút trên 8 ngày có thể không đại diện cho biến động dài hạn" | Tầm dự báo 60 phút và độ dài lịch sử 8 ngày là hai chuyện khác nhau (GPT nói đúng điểm này). Vấn đề thật là **chỉ có một cửa sổ test dài 29 giờ**. | **Đúng về hệ quả, lập luận chưa chuẩn.** Cách sửa là đánh giá trên nhiều cửa sổ test (P1-1). |
| T7 | "Tăng trích dẫn về workload forecasting và transfer learning" | 19 tài liệu: 3 bài về dự đoán tải ([1] đến [3]), **0 bài về transfer learning**, bài nghiên cứu mới nhất năm 2019 (không tính sách [10] năm 2021). Có hai bài trùng trực tiếp với câu hỏi của đề tài (mục 4). | **Đúng, và cấp thiết hơn thầy nói.** Nếu không định vị so với hai bài trùng, người phản biện sẽ hỏi tính mới ở đâu. |
| T8 | "Lỗi lập trình (implementation/debugging) chưa phải đóng góp lý thuyết" | Cả 10 máy "đứng yên" ở E3 gây ra lỗi 1 đều có CPU trung bình **trên phần train** dưới 1%. Nếu bộ lọc chỉ nhìn phần train, tức lọc theo nguyên tắc nhân quả, chúng đã bị loại và lỗi 1 không xảy ra. Lỗi 2 là lỗi viết mã đơn thuần. | **Đúng.** Lỗi 1 thực chất là hệ quả của việc lọc chuỗi bằng dữ liệu tương lai (GPT-3 bên dưới). Chuyển phần này thành mục kiểm tra tính đúng hoặc phụ lục. |
| T9 | "Thêm RMSE, MASE; nếu đồng nhất với MAE thì càng chứng minh làm đúng" | RMSE, SMAPE, MASE và R² **đã được tính sẵn** cho từng máy trong mọi tệp `*_chuoi.csv` và `per_series_*.csv`. MASE đã dùng đúng mẫu số Hyndman: sai số naïve một bước trên phần train (`metrics.py`, `mase_denominators_train`). Nhưng **RMSE không đồng nhất với MAE** trên máy ảo (vấn đề A). | **Đúng về việc thêm, sai về kỳ vọng.** Các chỉ số ra kết quả giống nhau không chứng minh cách làm đúng. Ở đây chúng khác nhau, và chỗ khác nhau đó là phát hiện quan trọng nhất của bài. |

---

## 2. Đối chiếu nhận xét của GPT với mã nguồn

| # | GPT nói | Kiểm trên mã nguồn và dữ liệu | Kết luận |
|---|---|---|---|
| GPT-1 | Seasonal naïve phải là ŷ(t+h) = y(t+h−288), không phải y(t−288) | Mã nguồn dùng y(t−288) (`baselines.py`, `du_doan_seasonal`: khoá `bucket − 288`, không có h). Tính lại trên test (trung vị MAE theo máy): E1 h=1: 0,583 → **0,512**; E2 h=6: 0,721 → **0,475**; E2 h=12: 0,664 → 0,476; E3 h=12: 7,878 → 7,258. Ở E2 h=6, bản đúng (0,475) **tốt hơn naïve** (0,481). | **Đúng, và ảnh hưởng không nhỏ.** Bắt buộc sửa. |
| GPT-2 | Kiểm xem học máy có thấy y(t) như naïve không | Trong 19 đặc trưng **không có cột y(t)**. `lag_1` là y(t−1); y(t) chỉ dựng lại được bằng `lag_1 + diff_1`. Hồi quy tuyến tính biểu diễn được đúng tổng này. **RF và XGBoost thì không**: cây chia theo từng đặc trưng riêng, nên chỉ xấp xỉ được một tổng qua rất nhiều lần chia. | **Đúng.** Đây là bất lợi thật cho hai mô hình cây. Thêm cột y(t) (P0-2). |
| GPT-3 | Lọc máy theo CPU trung bình của cả 8 ngày là dùng thông tin của giai đoạn test | Đúng như vậy: `filter.judge` nhận cả cửa sổ 8 ngày. Nếu chỉ nhìn phần train, số máy đang giữ sẽ bị loại thêm là 9 (E1), 2 (E2), 11 (E3), và 10/10 máy đứng yên của E3 nằm trong số đó. | **Đúng.** Đây còn là gốc của lỗi 1. |
| GPT-3b | Nội suy tuyến tính có thể dùng điểm neo nằm sau thời điểm dự báo | Đúng về nguyên tắc, nhưng chỉ 0,039% (E1), 0,022% (E2), 0,002% (E3) dòng test có y(t) là giá trị nội suy. | **Đúng nhưng không đáng kể.** Chỉ cần ghi một câu kèm tỉ lệ này. |
| GPT-4 | Bất đẳng thức Samuelson chỉ ràng buộc các điểm trong mẫu, không ràng buộc quan sát tương lai | Đúng. Với n = 1.612, giới hạn là 40,1, rất lỏng. Luật này hữu ích như một phép kiểm dựa trên kinh nghiệm, không phải một bảo đảm toán học. | **Đúng.** Viết lại thành "quy tắc kinh nghiệm". Nếu áp dụng lọc nhân quả (P0-3), luật này chỉ còn là lớp bảo vệ phụ. |
| GPT-5 | L = 1 chưa có nghĩa là mô hình đáng dùng; cần so thêm với naïve tại đích | Ở N0, mô hình học ở E1 đem sang E2 có L ≈ 1,00 nhưng **tệ hơn naïve tại E2 22%** (tỉ số trung vị 1,224) và chỉ thắng naïve 1/15 phép so. Chiều E3 sang E1 ở N1 có L ≈ 1,10 đến 1,44 nhưng vẫn tệ hơn naïve 21% (1,210). | **Đúng.** Câu "cụm mới có thể dùng ngay mô hình có sẵn" ở mục IV.E là sai. |
| GPT-6 | "Không quá 8%" là con số tổng hợp, không phải giới hạn trên cho mọi mô hình | Trung vị qua 5 mô hình cao nhất là 1,081. Nhưng xét **từng mô hình**, chiều E2 sang E1 lên tới **1,216** ở N0 (LR, h=12) và **1,616** ở N2. | **Đúng.** Sửa Tóm tắt, IV.E và Kết luận. |
| GPT-7 | Cần chứng minh E1 và E2 là hai trung tâm dữ liệu khác nhau | Tài liệu gốc ghi rõ cả hai thuộc *một* trung tâm dữ liệu phân tán. E1 và E2 khác nhau ở loại hệ thống lưu trữ và thành phần ứng dụng. | **Đúng.** Đổi tiêu đề và cách gọi. |
| GPT-8 | Siêu tham số nằm ở biên và dùng lại cấu hình N0 cho N1, N2 | Lưới quá nhỏ nên nằm ở biên là tất yếu: RF chỉ có 2 ứng viên (`max_depth` 8 hoặc 16), SVR 2 ứng viên (C bằng 1 hoặc 10), XGBoost 3 ứng viên. Ridge chọn α = 0,01 ở 6/9 ô và α = 100 ở 3/9 ô, đều là hai đầu mút. | **Đúng.** Xem P1-3. |
| GPT-9 | MASE ≠ MAE mô hình / MAE naïve trên test; MASE không hoàn toàn là bằng chứng độc lập | Mã nguồn đã tính MASE đúng định nghĩa. Trên cùng một máy, thứ hạng các mô hình theo MASE giống theo MAE, nhưng kiểm định gộp qua các máy thì khác: số phép thắng ở E2 giảm từ 2 xuống 1. | **Đúng.** |
| GPT-10 | "Tám ngày: bản thảo đã có lý do" | Đúng, mục III.C có nêu. | Đúng. |
| GPT-11 | Nên thêm DLinear, một mạng hồi tiếp (GRU hoặc LSTM), cân nhắc PatchTST; không cần chạy đủ danh sách | Đồng ý. Bổ sung một lý do GPT chưa thấy: các mô hình học sâu này thường chuẩn hoá từng chuỗi (RevIN) và học với hàm mất mát MAE, đúng hai yếu tố mà vấn đề A và B cho thấy là quan trọng. | **Đúng**, xem P1-2. |
| GPT-12 | Phép so N0, N1, N2 không phải một phân rã nhân quả "sạch" | Đúng. N2 còn đổi cả giá trị cần dự đoán. | **Đúng.** Bỏ cụm "tách được" ở mục I và mục V. |

**Những điểm GPT bỏ sót** (vì không có mã nguồn): vấn đề A đến E ở mục 0, cùng các điểm N1 đến N6 dưới đây.

| # | Vấn đề mới | Bằng chứng |
|---|---|---|
| N1 | **Hàm mất mát khi huấn luyện không khớp với chỉ số khi chấm.** LR, Ridge, RF và XGBoost học bằng sai số bình phương, tức dự đoán trung bình có điều kiện, rồi được chấm bằng MAE, vốn ứng với trung vị có điều kiện. Chỉ có SVR (hàm mất mát ε-insensitive, gần với MAE) cho trung vị MAE thấp hơn naïve ở cả 6 ô máy ảo, dù chỉ học 10.000 dòng. | `experiments_tn1.csv`: SVR ở E2 có MAE 0,364, 0,373, 0,395 so với naïve 0,414, 0,481, 0,465 |
| N2 | **Lập luận về hồi quy tuyến tính ở IV.A không đứng vững.** Bài viết "LR không có siêu tham số để nới mà vẫn tệ hơn ít nhất 1,30 lần". Nhưng LR biểu diễn được đúng dự báo naïve (hệ số 1 cho `lag_1` và 1 cho `diff_1`). LR thua vì một mô hình chung được khớp bằng sai số bình phương trên các máy có thang đo rất khác nhau, nên bị kéo về mức trung bình chung, chứ không phải vì tải máy ảo không dự đoán được. Ở N1, tỉ số của LR giảm còn khoảng 0,96 đến 1,10. | Bảng N1 tại chỗ, Phụ lục B |
| N3 | Bài viết "mỗi môi trường có 15 phép so, hiệu chỉnh Holm", nhưng mã nguồn hiệu chỉnh Holm trên **28 cặp** (mọi cặp trong 8 mô hình) của từng tổ hợp môi trường và tầm dự báo. | `fig_tn1.py`, `kiem_dinh_cap` |
| N4 | Baseline trung bình trượt dùng y(t−6) đến y(t−1), **bỏ mất điểm mới nhất y(t)**. Bài lại viết "6 điểm gần nhất". | `baselines.py`, `du_doan_ma6` dùng `roll_mean_6` |
| N5 | Mẫu con của SVR được lấy phân tầng theo độ giật (CV) tính trên **cả 8 ngày**, kể cả phần test. Rò rỉ nhỏ ở khâu chọn mẫu. | `tang.py` (có ghi chú), `config/split.yaml` |
| N6 | Dự đoán của từng dòng **không được lưu**, chỉ lưu chỉ số theo máy. Muốn tính chỉ số mới (ví dụ chi phí khi cấp thiếu tài nguyên) thì phải chạy lại. | `run_experiments.py` chỉ ghi `per_series_*` |

---

## 3. Danh sách việc cần làm

Ký hiệu: **P0** là bắt buộc trước khi chạy thêm bất kỳ thứ gì; **P1** là cần có để đủ sức nặng cho một tạp chí Q3; **P2** là hoàn thiện hồ sơ nộp. Thời gian chạy ước lượng theo tệp `meta_*.json` của các lần chạy gốc.

### Nhóm A: làm ngay, không cần chạy lại mô hình (1–2 ngày)

**A1. Bảng số mẫu (T2).** Dán bảng ở Phụ lục A vào mục III.D. Thêm một câu giải thích: "RF học trên toàn bộ dòng với 50 cây; SVR học trên mẫu con 10.000 dòng, chiếm 0,7–1,7%, vì chi phí dự đoán của SVR tăng theo số vector hỗ trợ."

**A2. Thêm RMSE và MASE cho Bảng 3 (T9, vấn đề A).** Chạy lại Wilcoxon và Holm trên các cột `rmse` và `mase` của `per_series_tn1.csv`. Bảng 3 mới có ba cột "số phép thắng naïve": MAE, RMSE, MASE. Số liệu đã tính được:

| Môi trường | MAE | RMSE | MASE |
|---|---|---|---|
| E1 | 0/15 | **9/15** (RF, XGB, SVR ở cả 3 tầm) | 0/15 |
| E2 | 2/15 | **9/15** (RF, XGB, SVR ở cả 3 tầm) | 1/15 |
| E3 | 11/15 | 12/15 | 11/15 |

Cách diễn giải cần viết lại: trên máy ảo, **học máy giảm được các sai số lớn** (RMSE thấp hơn naïve 5–20%, thắng trên 57–87% số máy) **nhưng kém hơn ở sai số thông thường** (MAE). Với bài toán cấp phát tài nguyên, các sai số lớn ở đỉnh tải chính là thứ gây vi phạm cam kết chất lượng dịch vụ. Vì vậy kết luận "máy ảo không đáng dùng học máy" phải bỏ, thay bằng "câu trả lời phụ thuộc vào chi phí của sai số lớn". Trích dẫn Gneiting (2011) cho mối liên hệ giữa hàm mất mát và chỉ số chấm.

**A3. Đưa kết quả N1 tại chỗ vào mục IV.A (vấn đề B).** Số liệu đã có:

| Môi trường | Số phép thắng naïve theo MAE: N0 / N1 / N2 | Theo RMSE: N0 / N1 / N2 | Tỉ số MAE mô hình / naïve (trung vị qua 5 mô hình × 3 tầm): N0 / N1 / N2 |
|---|---|---|---|
| E1 | 0 / **7** / 1 | 9 / **15** / 5 | 1,220 / **0,988** / 1,209 |
| E2 | 2 / 1 / 3 | 9 / 12 / 7 | 1,245 / **0,962** / 1,167 |
| E3 | 11 / 7 / 15 | 12 / 9 / 15 | 0,880 / 0,872 / 0,931 |

Ở N1, Random Forest tốt hơn naïve trên 53–64% số máy ảo, với tỉ số 0,87–0,99.

**A4. So mô hình chuyển giao với naïve tại đích (GPT-5).** Thêm một cột cho Bảng 4 hoặc một bảng riêng:

| Nguồn → đích | Tỉ số MAE (mô hình chuyển sang / naïve tại đích): N0 / N1 / N2 | Số phép thắng naïve / 15 (MAE): N0 / N1 / N2 |
|---|---|---|
| E1 → E2 | 1,224 / 0,950 / 1,257 | 1 / 3 / 3 |
| E2 → E1 | 1,352 / 1,015 / 1,228 | 1 / 4 / 0 |
| E3 → E1 | 3,147 / 1,210 / 2,023 | 0 / 1 / 0 |
| E3 → E2 | 2,930 / 1,176 / 1,963 | 0 / 2 / 0 |
| E1 → E3 | 0,938 / 0,941 / 0,950 | 8 / 7 / 11 |
| E2 → E3 | 0,951 / 0,950 / 0,965 | 6 / 8 / 11 |

**A5. Sửa các phát biểu định lượng.**

- "Không quá 8%": ghi rõ đó là trung vị qua 5 mô hình, ở N0 và N1. Nêu thêm khoảng theo từng mô hình, cao nhất 1,216 ở N0.
- "Từ 10% đến 44%": nói thêm rằng dù vậy, mô hình chuyển sang vẫn tệ hơn naïve tại đích khoảng 18–21%.
- "0/15": ghi rõ tiêu chí (chỉ số MAE, chế độ N0).
- Mô tả họ kiểm định Holm: 28 cặp cho mỗi tổ hợp môi trường và tầm dự báo (N3).
- Trung bình trượt: sửa mô tả thành y(t−6) đến y(t−1), hoặc sửa mã nguồn theo P0-1.

**A6. Tiêu đề và cách gọi (vấn đề E).** Không gọi E1 và E2 là hai trung tâm dữ liệu. Tiêu đề tiếng Anh gợi ý:

- *"Revisiting the Naïve Baseline for Cloud CPU Load Forecasting: Effects of Error Metric, Per-Series Scaling and Cross-Trace Model Reuse"*
- *"When Does Machine Learning Beat Naïve Forecasting of Cloud CPU Load? Evidence from Bitbrains and Alibaba Traces"*

### Nhóm P0: sửa pipeline (khoảng 2–3 ngày viết mã, sau đó gom một lần chạy lại)

| Mã | Việc | Sửa ở đâu | Ghi chú |
|---|---|---|---|
| P0-1 | Sửa seasonal naïve thành y(t+h−288); trung bình trượt gồm cả y(t), tức y(t−5) đến y(t) | `src/cwp/models/baselines.py`: truyền `h` vào `du_doan_seasonal`, khoá thành `bucket + h − 288`; `du_doan_ma6` tính lại từ `data/processed` | Rẻ, chạy trong vài giây. Nếu có dữ liệu dài hơn (P1-1), thêm seasonal naïve theo tuần: y(t+h−2016). |
| P0-2 | Thêm y(t) làm đặc trưng trực tiếp (`lag_0`) | `src/cwp/features/spec.py` (đổi assert 19 → 20 và 22 → 23), `windows.py` (`add_lag_features`) | Phải sinh lại ma trận đặc trưng và chạy lại toàn bộ. Số liệu sẽ không còn khớp với v4, nên phải cập nhật `doi_chieu_so_lieu_bai_bao.py` (175 con số). |
| P0-3 | Lọc chuỗi theo nguyên tắc nhân quả: các tiêu chí `gan_chet`, `hang`, `it_dong` chỉ xét phần train | `src/cwp/preprocess/build.py`: gọi `judge(w_interp.iloc[:1612])`, còn `count_valid_rows` giữ nguyên | Số máy giữ lại giảm 9, 2 và 11 máy. Lỗi 1 ở E3 tự biến mất. Phương án khác: giữ bộ lọc hiện tại nhưng ghi rõ đây là cách chọn quần thể hồi cứu. **Cần bạn quyết định.** |
| P0-4 | Thêm biến thể mô hình học với hàm mất mát MAE (N1) | `src/cwp/models/registry.py`: `XGBRegressor(objective="reg:absoluteerror")` (có sẵn trong xgboost 2.1.3), `HistGradientBoostingRegressor(loss="absolute_error")` (có sẵn trong sklearn 1.5.2) | Rẻ hơn RF nhiều. Đây là phép kiểm quyết định: nếu bản dùng MAE thắng naïve ở máy ảo, kết luận câu hỏi 1 thay đổi. |
| P0-5 | Tính lại tầng độ giật chỉ trên phần train khi lấy mẫu con cho SVR | `src/cwp/evaluation/tang.py`, `scripts/describe_data.py` (tệp `cv.csv`) | Rò rỉ nhỏ, sửa cho sạch. |
| P0-6 | Lưu dự đoán từng dòng | `scripts/run_experiments.py`, `run_transfer.py`: ghi parquet gồm `series_id, bucket, h, model, mode, yhat` | Để về sau thêm chỉ số mà không cần chạy lại. |
| P0-7 | Sửa lời văn: Samuelson là quy tắc kinh nghiệm; bỏ cụm "tách được thang đo và động lực học"; bỏ "một cách đo mới" nếu không chứng minh được tính mới | Bản thảo, mục I, III.F, IV.D, V | |

Sau khi sửa P0-1 đến P0-6, chạy lại một lần duy nhất:

- Tiền xử lý và đặc trưng: vài chục phút.
- Thí nghiệm 1: khoảng 5,5 giờ, cộng thêm phần mô hình mới.
- Thí nghiệm 2: khoảng 19 giờ.
- Thí nghiệm máy giả: khoảng 1 giờ.

Có thể giảm Thí nghiệm 2 bằng cách bỏ RF khỏi phần chuyển giao, hoặc thay RF bằng HistGradientBoosting.

### Nhóm P1: đủ sức nặng cho tạp chí (khoảng 1–2 tuần)

**P1-1. Đánh giá trên nhiều cửa sổ thời gian (T4, T5, T6, vấn đề C).**

- **Giữ nguyên** thí nghiệm chung 8 ngày cho Thí nghiệm 2 (chuyển giao), vì E3 chỉ có 8 ngày.
- **Thêm** Thí nghiệm 1 mở rộng trên Bitbrains:
  - **E1 đủ 30 ngày** (12/08 đến 11/09/2013).
  - **E2 nối ba tháng** 7, 8 và 9/2013 (30/06 đến 29/09). Cần kiểm trước xem `vm_id` có đúng là cùng một máy qua ba tháng không, vì tên tệp trùng nhau nhưng tài liệu gốc không cam kết điều đó.
- Cách chia: rolling-origin. Huấn luyện trên phần lịch sử mở rộng dần (ít nhất 14 ngày để thấy 2 chu kỳ tuần), test từng ngày một, trượt mỗi lần một ngày. E1 có khoảng 16 ngày test, E2 khoảng 75.
- Báo cáo: phân phối số phép thắng naïve qua các ngày test; tách ngày thường và cuối tuần; tự tương quan ở trễ 1 ngày và 7 ngày trên chuỗi dài.
- Chỉ bật đặc trưng thứ trong tuần khi có ít nhất 2 chu kỳ tuần. Thêm phép thử bỏ đặc trưng lịch (`lich = khong`) cho Thí nghiệm 1; Thí nghiệm 2 đã có cờ này.
- Sửa ở đâu:
  - `config/preprocess.yaml`: `window.days`.
  - `src/cwp/evaluation/splits.py`: đang ghi cứng `WINDOW_BUCKETS = 2304` và `assert N_TRAIN == 1612`, cần tổng quát hoá thành ranh giới theo tham số.
  - `config/datasets.yaml`: E2 lấy cả ba thư mục.
- Chi phí: dữ liệu E1 gấp khoảng 3,75 lần hiện tại. Nên dùng HistGradientBoosting hoặc XGBoost thay cho RF 50 cây trong phần này.

**P1-2. Thêm mô hình đối chứng (T3).** Bộ tối thiểu, đặt tên theo đúng công trình gốc:

| Nhóm | Mô hình | Vì sao cần | Thư viện gợi ý |
|---|---|---|---|
| Thống kê theo từng chuỗi | AutoETS hoặc AutoARIMA, SeasonalNaive | Phần mở đầu trích ARIMA [1], nên người phản biện sẽ hỏi | `statsforecast` (chạy nhanh trên CPU) |
| Tuyến tính trên cửa sổ | **DLinear** (Zeng và cộng sự, AAAI 2023) | Mốc tuyến tính mạnh, có chuẩn hoá theo chuỗi | `neuralforecast` |
| Mạng hồi tiếp | **GRU** *hoặc* LSTM (chọn một) | Đại diện cho các bài dự đoán tải bằng mạng nơ-ron | `neuralforecast` |
| Transformer | PatchTST (Nie và cộng sự, ICLR 2023), không bắt buộc | Người đọc tạp chí quen thuộc | `neuralforecast`, chạy trên GPU của Colab |

Quy ước bắt buộc để so công bằng:

- Cùng các dòng test, cùng ba tầm dự báo, cùng hàm `per_series_metrics`.
- Cửa sổ đầu vào 288 hoặc 576 điểm.
- Hàm mất mát MAE, chuẩn hoá theo chuỗi (`scaler_type="robust"` hoặc `"standard"`).
- Chọn siêu tham số trên validation.
- Cài `torch` và `neuralforecast` trong **một môi trường ảo riêng**, để không phá các phiên bản đã ghim trong `requirements.txt`.

Tuỳ chọn, rất hợp với câu hỏi chuyển giao: thêm một mô hình nền tảng cho chuỗi thời gian dùng ở chế độ zero-shot (Chronos-Bolt hoặc TimesFM), xem như trường hợp "dùng lại mô hình mà không huấn luyện".

**P1-3. Nới lưới siêu tham số và kiểm độ nhạy (GPT-8, T1).**

- Ridge: α từ 10⁻⁴ đến 10⁴ theo thang log.
- XGBoost: độ sâu {4, 6, 8, 10}, dừng sớm trên validation.
- SVR: C ∈ {1, 10, 100}, cỡ mẫu con {10.000, 30.000, 100.000}. Nếu quá chậm, dùng xấp xỉ Nystroem kết hợp LinearSVR trên toàn bộ dữ liệu.
- RF: 100 đến 200 cây với `max_samples = 0,2` để giữ chi phí.
- Thí nghiệm "cùng cỡ mẫu" để trả lời thầy trực tiếp: cả 5 mô hình học trên đúng 10.000 dòng mà SVR dùng, rồi so với bản học trên toàn bộ dữ liệu.
- Chọn lại ít nhất α (Ridge) và C (SVR) riêng cho N1 và N2, vì hai tham số này nhạy với thang đo.

**P1-4. Bổ sung tổng quan tài liệu (T7).** Xem mục 4. Mục tiêu là khoảng 35–45 tài liệu, trong đó ít nhất 10 bài từ năm 2020 trở đi.

**P1-5. Viết lại đóng góp (T8).**

1. Bằng chứng ghép cặp theo từng máy trên ba môi trường, cho thấy câu trả lời cho câu hỏi "học máy có thắng naïve không" **phụ thuộc vào chỉ số, hàm mất mát và cách chuẩn hoá**. Đây là điểm khác so với Christofidi và cộng sự (2023); cần đọc kỹ bài đó để nêu khác biệt cụ thể.
2. Phép đo chuyển giao L, luôn kèm tỉ số so với naïve tại đích, trên sáu chiều chuyển giao, cùng thí nghiệm máy giả để kiểm giả thuyết hiệu ứng tổng hợp.
3. Hai lỗi: chuyển xuống mục "Kiểm tra tính đúng của quy trình" hoặc phụ lục, dẫn Hewamalage và cộng sự (2023) và Kapoor và Narayanan (2023). Không trình bày là đóng góp.

**P1-6. Thống kê.** Báo cáo cỡ hiệu ứng (tỉ lệ máy thắng; tỉ số trung vị kèm khoảng tin cậy bootstrap qua các máy) bên cạnh p-value. Với 300 đến 700 máy mỗi phép so, p-value gần như luôn nhỏ. Đã kiểm: dùng ước lượng Hodges–Lehmann thay cho trung vị của hiệu cho ra cùng số phép thắng, nên không cần đổi tiêu chí xác định hướng.

### Nhóm P2: hoàn thiện hồ sơ nộp VJCS

- **Dịch toàn văn sang tiếng Anh.** VJCS chỉ nhận bài tiếng Anh; v4 hiện là tiếng Việt, chỉ có tóm tắt tiếng Anh.
- **Đổi sang mẫu trình bày của World Scientific.** v4 đang theo mẫu của một tạp chí trong nước (`paper/sample/HJS@Template-OTH.docx`). Bỏ khung giới thiệu tác giả là sinh viên.
- Thêm các mục: Data and Code Availability (link repo public), khai báo có dùng công cụ AI (câu mẫu trong `HUONG_DAN_DUA_LEN_GITHUB.md`), Conflict of Interest.
- Thư gửi ban biên tập: nêu rõ đóng góp theo P1-5 và điểm khác với hai bài trùng.
- Đọc trực tiếp hướng dẫn tác giả trên trang của VJCS (phí xuất bản, giới hạn độ dài, kiểu trích dẫn). Lần này không truy cập được: World Scientific và Scimago trả lỗi 403.

---

## 4. Tài liệu cần bổ sung

Hai bài đã kiểm tra là có thật và **bắt buộc phải trích dẫn**:

1. G. Christofidi, K. Papaioannou, T. D. Doudali, "Is Machine Learning Necessary for Cloud Resource Usage Forecasting?", *Proc. ACM Symposium on Cloud Computing (SoCC '23)*, 2023. doi:10.1145/3620678.3624790. Bài này kết luận rằng dịch chuỗi một bước (tức dự báo naïve) đã rất chính xác, trùng với câu hỏi 1.
2. A. Rossi, A. Visentin, D. Carraro, S. Prestwich, K. N. Brown, "Forecasting workload in cloud computing: towards uncertainty-aware predictions and transfer learning", *Cluster Computing*, doi:10.1007/s10586-024-04933-2 (arXiv:2303.13525). Dùng Google và Alibaba; chuyển giao trong cùng nhà cung cấp chấp nhận được, khác nhà cung cấp thì không. Trùng với câu hỏi 3. Cần kiểm lại số tập và năm xuất bản.

Các tài liệu dưới đây được liệt kê theo trí nhớ, nên **phải kiểm DOI trước khi đưa vào bài**:

- **Dự đoán tải đám mây:**
  - Kim, Wang, Qi, Humphrey, "Empirical evaluation of workload forecasting techniques for predictive cloud resource scaling", IEEE CLOUD 2016. Bài này so nhiều bộ dự báo, có cả naïve.
  - Cortez và cộng sự, "Resource Central", SOSP 2017.
  - Kumar, Goomer, Singh, LSTM-RNN cho tải trung tâm dữ liệu, *Procedia Computer Science* 125, 2018.
  - Janardhanan và Barrett, "CPU workload forecasting … LSTM … ARIMA", ICITST 2017.
  - Bi, Li, Yuan, Zhou, *Neurocomputing* 424, 2021.
  - Xu và cộng sự, "esDNN", ACM TOIT 2022 (arXiv:2203.02684).
  - Amiri và Mohammad-Khanli, bài khảo sát trên *JNCA* 82, 2017.
- **Chuyển giao và mô hình chung cho nhiều chuỗi:**
  - "Tr-Predictor: An Ensemble Transfer Learning Model for Small-Sample Cloud Workload Prediction", *Entropy* 2022.
  - Pan và Yang, "A survey on transfer learning", IEEE TKDE 2010.
  - Montero-Manso và Hyndman, "Locality and globality", *IJF* 2021. Rất sát với lựa chọn "một mô hình chung cho mọi máy" của bài.
  - Oreshkin và cộng sự, dự báo zero-shot, AAAI 2021.
  - Kim và cộng sự, RevIN, ICLR 2022. Liên quan trực tiếp đến N1.
  - Salinas và cộng sự, DeepAR, *IJF* 2020.
- **Mô hình học sâu:**
  - Zeng và cộng sự (DLinear), AAAI 2023.
  - Nie và cộng sự (PatchTST), ICLR 2023.
  - Bai, Kolter, Koltun (TCN), 2018.
  - Hochreiter và Schmidhuber (LSTM), 1997.
  - Cho và cộng sự (GRU), 2014.
- **Đánh giá và rò rỉ dữ liệu:**
  - Gneiting, "Making and evaluating point forecasts", *JASA* 2011. Cơ sở lý thuyết cho vấn đề A và N1.
  - Hewamalage, Ackermann, Bergmeir, "Forecast evaluation for data scientists", *DMKD* 2023.
  - Kapoor và Narayanan, "Leakage and the reproducibility crisis…", *Patterns* 2023.
  - Makridakis và cộng sự, M5 accuracy, *IJF* 2022.
- **Bộ dữ liệu:**
  - Reiss và cộng sự, phân tích vết cụm máy Google, SoCC 2012.
  - Lu và cộng sự, "Imbalance in the cloud" (Alibaba), IEEE BigData 2017.

---

## 5. Khả năng đăng ở VJCS

- **Phạm vi:** phù hợp. VJCS là tạp chí truy cập mở của World Scientific, nhận bài tiếng Anh về trí tuệ nhân tạo, trí tuệ tính toán, khai phá dữ liệu và ứng dụng máy tính.
- **Bản v4 hiện tại: chưa nộp được.** Kết luận chính không đứng vững khi đổi chỉ số (vấn đề A và B), tính mới trùng với các bài đã có (D), và bài chưa ở dạng tiếng Anh theo mẫu của tạp chí.
- **Nếu làm xong nhóm A, P0 và P1, rồi viết lại:** có cơ sở để nộp. Rủi ro lớn nhất vẫn là tính mới so với Christofidi và cộng sự (2023). Bài chỉ đứng được nếu đóng góp được đặt ở chỗ **câu trả lời phụ thuộc vào chỉ số, hàm mất mát và cách chuẩn hoá**, cộng với đánh giá chuyển giao hai chiều và thí nghiệm máy giả, chứ không phải ở câu "học máy không thắng naïve".
- Không thể dự đoán chắc chắn bài có được chấp nhận hay không.

**Gợi ý trả lời thầy:**

> "Dạ thầy, em đã kiểm lại. Random Forest học trên toàn bộ khoảng 1,4 triệu dòng, 50 là số cây. Mô hình ít mẫu là SVR, chỉ 10.000 dòng, bằng 0,7–1,7% các mô hình khác; em sẽ bổ sung bảng số mẫu và thí nghiệm cho các mô hình học cùng cỡ mẫu. Khi thêm RMSE thì kết quả trên máy ảo đổi chiều: học máy thắng naïve 9/15 phép so theo RMSE, trong khi theo MAE là 0/15. Em sẽ đánh giá lại trên đủ 30 ngày của Bitbrains để xét chu kỳ tuần, thêm DLinear, GRU, ARIMA, và chuyển phần lỗi xuống mục kiểm tra quy trình."

---

## Phụ lục A. Bảng số mẫu (dán vào mục III.D)

Nguồn: `data/catalog.parquet`, `results/tables/splits_tn1.csv`, `results/ket_qua_chay_goc/tn1/chosen_tn1.csv`, `results/ket_qua_chay_goc/n1_loai_dung_yen/n1_loai_dung_yen_khop.csv`.

| | E1: Bitbrains fastStorage | E2: Bitbrains Rnd (08/2013) | E3: Alibaba 2018 |
|---|---|---|---|
| Chuỗi đưa vào | 1.250 | 500 | 500 (mẫu phân tầng từ 4.023) |
| Chuỗi bị loại (gần như tắt / ngoài cửa sổ / ít dòng) | 515 (454 / 55 / 6) | 198 (197 / 1 / 0) | 2 (2 / 0 / 0) |
| Chuỗi giữ lại | 735 | 302 | 498 |
| Điểm 5 phút sau xử lý (chuỗi × 2.304) | 1.693.440 | 695.808 | 1.147.392 |
| Mốc Train / Validation / Test | 12/08 13:40 → 18/08 04:00 / → 19/08 08:45 / → 20/08 13:40 | 31/07 22:00 → 06/08 12:20 / → 07/08 17:05 / → 08/08 22:00 | ngày 0 → 5,6 / → 6,8 / → 8,0 (mốc tương đối) |
| Dòng Train (h = 1 / 6 / 12) | 1.142.276 / 1.138.601 / 1.134.191 | 469.502 / 466.681 / 464.338 | 596.549 / 584.598 / 575.245 |
| Dòng Validation | 252.840 / 249.165 / 244.755 | 103.888 / 102.378 / 100.566 | 169.675 / 167.127 / 164.102 |
| Dòng Test | 254.310 / 250.635 / 246.225 | 104.492 / 102.982 / 101.170 | 171.716 / 169.209 / 166.203 |
| Điểm test mỗi máy (h = 1 / 6 / 12) | 346 / 341 / 335 | như E1 | như E1 |
| Dòng khớp mô hình cuối (Train + Validation), cho LR, Ridge, RF, XGBoost | 1.395.851 / 1.392.176 / 1.387.766 | 573.692 / 570.871 / 568.528 | 766.720 / 754.701 / 745.299 |
| Dòng khớp của SVR (mẫu con) | 10.000 / 9.971 / 9.944 (0,72%) | 10.000 / 9.946 / 9.899 (1,74%) | 10.000 / 9.815 / 9.689 (1,30%) |
| Dòng khớp ở N1 sau khi loại máy đứng yên | 1.391.987 / 1.388.322 / 1.383.924 (loại 2 máy) | 571.789 / 568.976 / 566.639 (loại 1) | 752.400 / 740.677 / 731.488 (loại 10) |
| Chọn siêu tham số | rolling-origin 5 fold mở rộng dần, mỗi fold validation 69 điểm (5,75 giờ) | như E1 | như E1 |

Thí nghiệm máy giả: E1a gồm 368 máy ảo, dòng khớp h=1 là 696.259; E1g gồm 73 máy giả, dòng khớp h=1 là 132.721.

## Phụ lục B. Cách tính các con số kiểm chứng

| Con số | Đầu vào | Cách tính |
|---|---|---|
| Số phép thắng theo MAE, RMSE, MASE (A2) | `results/ket_qua_chay_goc/tn1/per_series_tn1.csv` | Với mỗi (môi trường, h): Wilcoxon hai phía trên mọi cặp của 8 mô hình, hiệu chỉnh Holm trong 28 cặp (giống `fig_tn1.kiem_dinh_cap`). "Thắng" nghĩa là p_holm < 0,05 và trung vị của hiệu ghép cặp (mô hình trừ naïve) nhỏ hơn 0. Lặp lại cho cột `rmse` và `mase`. |
| Tỉ lệ máy thắng, tỉ số trung vị theo máy | như trên | Trung vị qua các máy của MAE mô hình chia MAE naïve (hoặc RMSE); tỉ lệ máy có mô hình < naïve. |
| N1 tại chỗ, chuyển giao so với naïve (A3, A4) | `scripts/phan_tich_cuoi.bang_cuoi()` (đã thay N1 bằng bản loại máy đứng yên, N2 ở h = 6, 12 bằng bản sửa) ghép với naïve từ `per_series_tn1.csv` theo (đích, h, máy) | Wilcoxon mô hình so với naïve, Holm trong 15 phép so của mỗi (nguồn, đích, chế độ, chỉ số). |
| Khoảng L theo từng mô hình (GPT-6) | `results/tables/cuoi_L.csv` | min, trung vị, max của `L_p50` theo (nguồn, đích, chế độ). |
| Seasonal naïve đúng và sai (GPT-1) | `data/processed/*.parquet`, `data/features/*_h{h}.parquet`, dòng test theo `split_masks` | Tra y tại khoá `bucket − 288` và tại `bucket + h − 288`; tính trung vị MAE theo máy bằng `per_series_metrics`. |
| Tỉ lệ y(t) được nội suy (GPT-3b) | `data/processed` (cột `is_interp`) | Tỉ lệ dòng test có `is_interp` = True tại `bucket`. |
| Bộ lọc chỉ nhìn phần train (GPT-3, T8) | `data/processed`, `config/may_dung_yen.csv` | CPU trung bình trên offset [0, 1612) nhỏ hơn 1%; lấy giao với danh sách máy đứng yên. |
| Mốc lịch của các tập (vấn đề C) | `data/processed` | `b0 × 300` là giây epoch; cộng các ranh giới 1612 và 1957. |
| Tự tương quan 8 ngày và 30 ngày, CPU theo ngày (T4, T5) | `data/raw/Bitbrains-fastStorage/08-2013` (735 máy đang giữ), `data/processed/E1.parquet` | Đưa về lưới 5 phút, cắt về [0, 100]; hệ số Pearson trên các cặp trễ không NaN ở trễ 1, 288 và 2016; lấy trung vị theo máy. Chuỗi 30 ngày không qua bước nội suy. |
| MAE ở Train, Validation, Test (vấn đề C) | `results/tables/baselines_tn1.csv`, `chosen_tn1.csv` | Đọc trực tiếp. Điểm validation của mô hình học máy là trung bình của 5 fold, nên chỉ so gần đúng được với MAE naïve trên cả giai đoạn validation. |
