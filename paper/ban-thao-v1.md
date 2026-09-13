<!--
Bản thảo v1 — 2026-09-14. Nguồn gốc của paper/ban-thao-v1.docx (sinh bằng scripts/tao_docx.py).
Cú pháp: ::the:: nội dung — xem đầu scripts/tao_docx.py. Chú thích hình/bảng KHÔNG gõ số:
template HJS tự đánh "Hình N." và "Bảng N." theo thứ tự xuất hiện.
⟦CHỜ QĐ-019⟧ = số N2 ở h = 6, 12 đang chạy lại (research-log/2026-09-14-loi-target-n2.md).
⟦CẦN BỔ SUNG⟧ = thông tin nhóm tác giả tự điền.
-->

::tieu-de:: HỌC MÁY DỰ ĐOÁN TẢI CPU TRÊN ĐÁM MÂY: ĐỐI CHỨNG VỚI DỰ BÁO NGÂY THƠ VÀ PHÂN RÃ KHẢ NĂNG CHUYỂN GIAO GIỮA CÁC MÔI TRƯỜNG

::tac-gia:: Trần Hoàng Đạt, Trần Hoàng Phát, Lương Trần Ngọc Khiết

::co-quan:: Khoa Công nghệ thông tin, Trường Đại học Sư Phạm TP.HCM

::email:: 4901104030@student.hcmue.edu.vn, 4901104107@student.hcmue.edu.vn, khietltn@hcmue.edu.vn

::tom-tat:: TÓM TẮT— Dự đoán mức sử dụng CPU là nền tảng của việc cấp phát tài nguyên tự động trên đám mây, và các mô hình học máy thường được báo cáo là cho sai số thấp. Tuy nhiên, hai câu hỏi hay bị bỏ ngỏ: mô hình có thực sự tốt hơn cách đoán "năm phút tới giống năm phút trước" hay không, và một mô hình học ở trung tâm dữ liệu này có dùng được ở trung tâm dữ liệu khác hay không. Nghiên cứu này trả lời hai câu hỏi đó trên 1.535 chuỗi CPU thật từ ba môi trường công khai: hai tập máy ảo của Bitbrains và một tập máy vật lý của Alibaba. Tám mô hình, gồm ba mô hình cơ sở và năm mô hình học máy (hồi quy tuyến tính, Ridge, Random Forest, XGBoost, SVR), được đánh giá ở ba tầm dự báo 5, 30 và 60 phút, bằng kiểm định Wilcoxon ghép cặp theo từng chuỗi có hiệu chỉnh Holm. Để tách mức tải khỏi động lực học khi chuyển giao, nhóm đề xuất chạy song song ba chế độ chuẩn hoá (thô, z-score theo chuỗi, sai phân) và đo mất mát chuyển giao L so với chính mô hình đó huấn luyện ngay trên môi trường đích ở cùng chế độ. Kết quả cho thấy: trên máy ảo, dự báo ngây thơ gần như không thể vượt qua (0/15 và 2/15 phép so có ý nghĩa), trong khi trên máy vật lý học máy vượt ở 11/15 phép so. Chuyển giao giữa hai tập máy ảo gần như không mất mát (L từ 0,97 đến 1,08). Chuyển giao từ máy vật lý sang máy ảo tốn 2,2 đến 3,4 lần ở dữ liệu thô, giảm còn 1,10 đến 1,44 lần khi chuẩn hoá z-score, còn chiều ngược lại chỉ tốn 1,03 đến 1,10 lần. Nghiên cứu cũng chỉ ra hai lỗi âm thầm trong quy trình chuẩn hoá mà các phép kiểm thông thường không phát hiện, cùng cách khắc phục.

::tu-khoa:: Từ khóa— Dự đoán tải đám mây, dự báo ngây thơ, chuyển giao giữa môi trường, chuẩn hoá chuỗi thời gian, rò rỉ dữ liệu

# Giới thiệu

Điện toán đám mây cho phép cấp phát tài nguyên theo nhu cầu, nhưng quyết định cấp phát chỉ tốt khi dự đoán được tải sắp tới. Dự đoán quá thấp gây quá tải và vi phạm cam kết chất lượng dịch vụ; dự đoán quá cao gây lãng phí máy chủ và điện năng. Vì vậy dự đoán mức sử dụng CPU đã được nghiên cứu từ các mô hình thống kê như ARIMA [1] đến mạng nơ-ron và các mô hình học máy khác [2], với nhiều khảo sát tổng hợp các hướng tiếp cận [3].

Tuy nhiên, khi đọc các kết quả dự đoán, nhóm chúng tôi nhận thấy hai khoảng trống về cách đánh giá. Khoảng trống thứ nhất là **mốc so sánh**. Một mô hình đạt sai số tuyệt đối trung bình (MAE) thấp chưa chắc đã tốt, vì trên dữ liệu CPU lấy mẫu dày, cách đoán đơn giản nhất — lấy giá trị hiện tại làm dự đoán cho bước sau, gọi là dự báo ngây thơ (naive persistence) — thường đã cho sai số rất thấp. Các nghiên cứu so sánh quy mô lớn đã cảnh báo rằng mô hình học máy không phải lúc nào cũng vượt được các phương pháp đơn giản [4], và chỉ số MASE ra đời chính để đo sai số tương đối so với dự báo ngây thơ [5]. Nếu không so với mốc này, không thể biết mô hình học được điều gì mà cách đoán ngây thơ không làm được.

Khoảng trống thứ hai là **chuyển giao giữa các môi trường**. Trong vận hành thực tế, một mô hình thường được huấn luyện ở một trung tâm dữ liệu rồi đem dùng cho máy mới hoặc cụm máy khác. Khi đánh giá khả năng này bằng sai số thô, con số thu được trộn lẫn hai nguồn khác biệt: chênh lệch **mức tải** trung bình và khác biệt về **động lực học** — cách tải lên xuống theo thời gian. Trên dữ liệu của nghiên cứu này, chỉ riêng một hằng số bằng mức tải trung bình của tập máy ảo Bitbrains fastStorage đem áp cho máy vật lý Alibaba đã cho MAE 28,24, tức không cần mô hình nào cũng "chuyển giao thất bại". Một kết luận như vậy đúng nhưng không cho biết gì. Thêm vào đó, bước chuẩn hoá dùng để loại mức tải lại là nơi rò rỉ dữ liệu dễ xảy ra nhất [6], và các lỗi ở đây thường không làm chương trình báo lỗi mà chỉ làm con số đẹp lên hoặc sai lệch một cách âm thầm.

Xuất phát từ hai khoảng trống trên, nghiên cứu này đặt ba câu hỏi. **RQ1:** mô hình học máy nào dự đoán tải CPU tốt nhất, và có vượt được dự báo ngây thơ không? **RQ2:** hiệu năng thay đổi thế nào giữa các môi trường? **RQ3:** mô hình huấn luyện ở môi trường này có dùng được ở môi trường khác không, và thành phần nào của tín hiệu chuyển giao được?

Đóng góp chính của nghiên cứu gồm ba điểm:

- **Một giao thức đánh giá có kiểm soát rò rỉ** trên 1.535 chuỗi CPU thật từ ba môi trường công khai, trong đó mọi mô hình được so ghép cặp với dự báo ngây thơ trên từng chuỗi, có kiểm định thống kê và hiệu chỉnh so sánh bội.
- **Một cách phân rã khả năng chuyển giao**: chạy song song ba chế độ chuẩn hoá và đo mất mát chuyển giao L so với chính mô hình đó huấn luyện ngay trên môi trường đích, ở cùng chế độ. Nhờ tử số và mẫu số cùng chế độ, L chỉ còn phần do chuyển giao, không lẫn tác động của phép chuẩn hoá.
- **Hai lỗi âm thầm của bước chuẩn hoá và cách khắc phục**: z-score theo chuỗi hỏng khi máy đứng yên trong cửa sổ huấn luyện, và định nghĩa đích của chế độ sai phân dễ bị hiện thực lệch ở tầm dự báo dài. Cả hai đều lọt qua các phép kiểm thông thường.

Phần II tiếp theo tổng quan các nghiên cứu liên quan. Phần III trình bày dữ liệu, mô hình và giao thức đánh giá. Phần IV báo cáo kết quả và thảo luận. Phần V kết luận, nêu hạn chế và hướng phát triển.

# Tổng quan tài liệu

## Dự đoán tải tài nguyên trên đám mây

Dự đoán tải đám mây thường được đặt thành bài toán chuỗi thời gian: từ lịch sử sử dụng tài nguyên của một máy, dự đoán giá trị ở một hoặc nhiều bước tới. Calheiros và cộng sự [1] dùng ARIMA để dự đoán tải và phân tích tác động của sai số dự đoán tới chất lượng dịch vụ. Kumar và Singh [2] kết hợp mạng nơ-ron với thuật toán tiến hoá vi phân để cải thiện độ chính xác. Khảo sát của Masdari và Khoshnevis [3] phân loại các phương pháp theo nhóm thống kê, học máy và lai ghép, và cho thấy phần lớn nghiên cứu đánh giá trên một bộ dữ liệu duy nhất.

## Mốc so sánh và chỉ số đánh giá

Makridakis và cộng sự [4] so sánh nhiều phương pháp thống kê và học máy trên hàng nghìn chuỗi, và ghi nhận rằng các phương pháp học máy thường không vượt được phương pháp thống kê đơn giản khi đánh giá ngoài mẫu. Hyndman và Koehler [5] đề xuất MASE, chia sai số của mô hình cho sai số của dự báo ngây thơ một bước trên tập huấn luyện, nhờ đó so sánh được giữa các chuỗi có thang đo khác nhau. Tashman [7] nhấn mạnh rằng đánh giá dự báo phải chia theo thời gian, không xáo trộn, để mô hình không nhìn thấy tương lai.

Kinh nghiệm của chính nhóm cũng cho thấy tầm quan trọng của mốc so sánh. Trong nghiên cứu trước về phát hiện giao dịch bất thường [8], nhóm từng đặt cạnh nhau hai chỉ số AUC đo trên hai tập đánh giá khác nhau. Hai con số trông so được, nhưng thực chất đo hai bài toán khác nhau. Bài học đó được áp dụng xuyên suốt nghiên cứu này: mọi phép so sánh phải cùng chuỗi, cùng tập kiểm tra và cùng mốc.

## Dữ liệu tải công khai và chuyển giao giữa môi trường

Hai nguồn dữ liệu được dùng rộng rãi là Bitbrains, nơi Shen và cộng sự [9] phân tích đặc trưng tải của các máy ảo phục vụ ứng dụng doanh nghiệp, và bộ vết cụm máy Alibaba 2018, được Guo và cộng sự [10] phân tích hiệu quả sử dụng tài nguyên ở mức máy vật lý. Hai nguồn này khác nhau không chỉ ở tổ chức vận hành mà còn ở **đơn vị quan sát**: Bitbrains ghi từng máy ảo, Alibaba ghi từng máy vật lý chứa nhiều container. Chuỗi ở mức máy vật lý vì thế là tổng của nhiều tải nhỏ và mượt hơn một cách hệ thống. Khi so sánh hay chuyển giao giữa hai nguồn, khác biệt này phải được nêu rõ.

Khi chuyển giao, chuẩn hoá từng chuỗi là cách phổ biến để loại chênh lệch mức tải. Nhưng thống kê chuẩn hoá phải được tính chỉ trên phần dữ liệu huấn luyện; dùng thống kê của toàn chuỗi là một dạng rò rỉ dữ liệu điển hình [6].

## Khoảng trống nghiên cứu

Từ các nghiên cứu trên, nhóm xác định ba khoảng trống. Thứ nhất, hiếm có đánh giá nào so ghép cặp mô hình học máy với dự báo ngây thơ trên từng chuỗi, kèm kiểm định thống kê, ở nhiều môi trường cùng lúc. Thứ hai, khả năng chuyển giao thường được đo bằng sai số thô, không tách được đâu là do mức tải, đâu là do động lực học. Thứ ba, các lỗi ở bước chuẩn hoá hiếm khi được kiểm tra bằng các phép kiểm độc lập với cách hiện thực. Nghiên cứu này nhắm vào cả ba.

# Phương pháp nghiên cứu

## Quy trình nghiên cứu

::hinh:: paper/figures/hinh1_quy-trinh.png | Sơ đồ quy trình nghiên cứu | 15.5

Quy trình được tổ chức như Hình 1. Dữ liệu thô của ba môi trường được đưa về cùng lưới thời gian và cùng cửa sổ quan sát, rồi sinh một bộ đặc trưng quá khứ chung. Từ đó chia thành hai thí nghiệm: Thí nghiệm A (TN-A) đánh giá mô hình **trong** từng môi trường để trả lời RQ1 và RQ2; Thí nghiệm B (TN-B) đánh giá mô hình **giữa** các môi trường để trả lời RQ3.

Xuyên suốt quy trình, mỗi giai đoạn chỉ được chuyển sang giai đoạn sau khi qua một **cổng nghiệm thu**: các con số của phần hiện thực phải khớp với một bản tính độc lập, và công cụ kiểm tra phải chứng minh được nó phát hiện lỗi bằng cách cố tình làm hỏng mã nguồn. Với các phân tích bổ sung, giả thuyết, phép kiểm định và luật đọc kết quả được ghi và lưu phiên bản **trước khi chạy** [11], để kết luận không bị điều chỉnh theo kết quả.

## Dữ liệu

::bang:: Ba môi trường dữ liệu sau tiền xử lý

| | E1 — Bitbrains fastStorage | E2 — Bitbrains Rnd | E3 — Alibaba 2018 |
|---|---|---|---|
| Nguồn | [9] | [9] | [10] |
| Đơn vị quan sát | máy ảo | máy ảo | máy vật lý |
| Số chuỗi đưa vào | 1.250 | 500 (tháng 8/2013) | 500 (mẫu phân tầng từ 4.023) |
| Số chuỗi bị loại | 515 | 198 | 2 |
| **Số chuỗi giữ lại** | **735** | **302** | **498** |
| Trung vị CPU (%) | 1,78 | 1,77 | 37,83 |
| Tự tương quan bậc 1 | 0,67 | 0,64 | 0,86 |
| Tự tương quan ở 24 giờ | 0,13 | 0,13 | 0,60 |
| Tỉ lệ điểm chạm trần 100% | 5,12% | 2,28% | 0% |

Nghiên cứu dùng ba môi trường như Bảng 1. E1 và E2 là hai tập máy ảo của Bitbrains [9], ghi CPU theo phần trăm mỗi 5 phút. E3 là bảng sử dụng máy vật lý trong bộ vết cụm Alibaba năm 2018 [10], ghi khoảng 10 giây một lần. Do tệp gốc của Alibaba lớn (9 GB, gần 247 triệu dòng), nhóm lấy mẫu phân tầng 500 máy theo mức CPU trung bình, với danh sách máy được cố định để mọi lần chạy dùng đúng một quần thể. Biến mục tiêu ở cả ba môi trường là CPU tính theo phần trăm, thang 0–100.

::hinh:: paper/figures/hinh2_phan-phoi-cpu.png | Phân phối CPU (%) của ba môi trường sau tiền xử lý | 16.5

Hình 2 cho thấy khác biệt lớn nhất giữa các môi trường là **mức tải**. Hơn một nửa số điểm của hai tập máy ảo nằm dưới 2% CPU, trong khi máy vật lý của Alibaba tập trung quanh 30–50%. Bảng 1 còn cho thấy khác biệt về **độ mượt**: chuỗi máy vật lý có tự tương quan bậc 1 là 0,86 và chu kỳ ngày rõ (tự tương quan ở độ trễ 24 giờ là 0,60), so với 0,64–0,67 và 0,13 ở máy ảo. Một phần khác biệt này đến từ hiệu ứng tổng hợp: một máy vật lý là tổng của nhiều container, nên dao động nhỏ của từng container triệt tiêu lẫn nhau.

## Tiền xử lý và đặc trưng

Tiền xử lý gồm các bước theo thứ tự:

- Cắt CPU về khoảng [0, 100].
- Đưa về lưới 5 phút bằng trung bình các mẫu trong mỗi ô thời gian.
- Lấy cửa sổ 8 ngày đầu của mỗi môi trường, tức 2.304 điểm, vì Alibaba chỉ có 8 ngày.
- Nội suy tuyến tính các lỗ hổng dài tối đa 2 điểm (10 phút). Lỗ dài hơn giữ nguyên là giá trị thiếu. Nhóm không dùng cách lấp bằng giá trị trước đó, vì cách đó tạo đoạn phẳng giả và làm tăng tự tương quan — đại lượng trung tâm của RQ3.
- Loại chuỗi nếu:
  - không có điểm nào trong cửa sổ;
  - CPU trung bình dưới 1% (máy gần như không hoạt động);
  - gần như hằng số;
  - hoặc có dưới 500 dòng huấn luyện hợp lệ.

Bộ lọc loại 41% chuỗi của E1 và 40% của E2 nhưng chỉ 0,4% của E3, và loại gần như hoàn toàn ở phía tải thấp. Mọi phát biểu của nghiên cứu vì vậy chỉ áp dụng cho quần thể đã lọc.

::bang:: Mười chín đặc trưng dùng chung cho mọi mô hình

| Nhóm | Đặc trưng | Số lượng |
|---|---|---|
| Giá trị trễ | y(t−1), y(t−2), y(t−3), y(t−6), y(t−12), y(t−24) | 6 |
| Thống kê trượt 30 phút | trung bình, độ lệch chuẩn, nhỏ nhất, lớn nhất trên 6 điểm trước t | 4 |
| Thống kê trượt 60 phút | trung bình, độ lệch chuẩn, nhỏ nhất, lớn nhất trên 12 điểm trước t | 4 |
| Sai phân | y(t) − y(t−1) | 1 |
| Lịch | sin và cos của giờ trong ngày, sin và cos của ngày trong tuần | 4 |

Mỗi dòng huấn luyện tại thời điểm t có 19 đặc trưng như Bảng 2. Mọi đặc trưng chỉ dùng quá khứ của **chính chuỗi đó**; thống kê trượt tính trên đúng các điểm trước t, không gồm t. Một dòng được coi là hợp lệ khi toàn bộ 25 điểm từ t−24 đến t đều có giá trị và giá trị đích tại t+h cũng có giá trị. Nhóm không xoá dòng theo đặc trưng bị thiếu: 19 đặc trưng chỉ chạm 15 trong 25 điểm của cửa sổ, nên cách xoá đó lỏng hơn luật trên và giữ lại những dòng có lỗ hổng bên trong cửa sổ.

## Chia dữ liệu và mô hình

Mỗi môi trường được chia theo thời gian, không xáo trộn [7]: 70% đầu cửa sổ để huấn luyện, 15% tiếp theo để chọn siêu tham số, 15% cuối để kiểm tra. Ranh giới tính theo mốc thời gian chung của cả môi trường, nên mọi chuỗi có cùng khoảng kiểm tra. Dòng nào có đầu vào và giá trị đích nằm ở hai phía của một ranh giới thì bị loại, để giá trị đích của tập huấn luyện không rơi vào tập kiểm tra. Siêu tham số được chọn bằng kiểm định trượt gốc 5 lần trên vùng validation; mô hình cuối huấn luyện trên cả tập huấn luyện lẫn validation, rồi chấm trên tập kiểm tra đúng một lần.

::bang:: Tám mô hình và lưới siêu tham số

| Mô hình | Loại | Lưới siêu tham số | Ghi chú |
|---|---|---|---|
| Ngây thơ | cơ sở | — | ŷ(t+h) = y(t) |
| Trung bình trượt | cơ sở | — | trung bình 6 điểm gần nhất |
| Ngây thơ theo mùa | cơ sở | — | giá trị cùng giờ ngày hôm trước |
| Hồi quy tuyến tính | học máy | — | chuẩn hoá đặc trưng |
| Ridge | học máy | alpha ∈ {0,01; 0,1; 1; 10; 100} | chuẩn hoá đặc trưng |
| Random Forest [12] | học máy | độ sâu tối đa ∈ {8; 16} | 50 cây |
| XGBoost [13] | học máy | (độ sâu; số cây) ∈ {(4; 300), (8; 300), (8; 600)} | tốc độ học 0,1 |
| SVR nhân RBF [14] | học máy | C ∈ {1; 10} | mẫu con 10.000 dòng phân tầng |

Tám mô hình ở Bảng 3 được hiện thực bằng scikit-learn [15] và XGBoost [13], với random_state = 42 ở mọi chỗ có yếu tố ngẫu nhiên. Mô hình học máy là **mô hình toàn cục**: một mô hình học trên mọi chuỗi của môi trường, không phải mỗi chuỗi một mô hình. Ba tầm dự báo là h = 1, 6 và 12 bước, tương ứng 5, 30 và 60 phút. Random Forest chỉ dùng 50 cây và SVR chỉ học trên mẫu con 10.000 dòng vì giới hạn tính toán; đây là bất lợi của hai mô hình này và được khai báo trong phần hạn chế.

## Chỉ số và kiểm định thống kê

Mỗi mô hình được chấm bằng MAE, RMSE, SMAPE, MASE [5] và R² trên **từng chuỗi**, sau đó tóm tắt bằng trung vị qua các chuỗi. MAE của một chuỗi được tính như sau:

::cong-thuc:: MAE = (1/n) · Σ |y(t+h) − ŷ(t+h)|

trong đó n là số dòng kiểm tra hợp lệ của chuỗi, y(t+h) là giá trị thật và ŷ(t+h) là giá trị dự đoán. Nhóm không dùng MAPE vì nhiều máy ảo có CPU gần 0, làm MAPE tăng vô hạn.

Để kết luận một mô hình tốt hơn mô hình khác, nhóm dùng kiểm định Wilcoxon hạng có dấu [16] trên MAE ghép cặp theo chuỗi, với mức ý nghĩa 0,05 và hiệu chỉnh Holm [17] trong mỗi họ phép so. **Hướng** của kết luận lấy từ trung vị của hiệu ghép cặp, không lấy từ hiệu của hai trung vị; hai cách này có thể cho kết luận ngược nhau, và điều đó đã xảy ra trong quá trình thực hiện. Khi so hai tập chuỗi khác nhau, nhóm dùng kiểm định Mann–Whitney [18], hướng xác định bằng hệ số rank-biserial.

## Thí nghiệm B: ba chế độ chuẩn hoá và mất mát chuyển giao

::bang:: Ba chế độ chuẩn hoá của Thí nghiệm B

| Chế độ | Biến đổi chuỗi | Giá trị đích | Đưa về CPU (%) | Loại bỏ thành phần nào |
|---|---|---|---|---|
| N0 — thô | không | y(t+h) | giữ nguyên | không |
| N1 — z-score theo chuỗi | z(t) = (y(t) − μ) / σ | z(t+h) | ŷ = ẑ·σ + μ | mức tải và biên độ |
| N2 — sai phân | d(t) = y(t) − y(t−1) | y(t+h) − y(t) | ŷ = y(t) + Δ̂ | mức tải, biên độ tuyệt đối |

Thí nghiệm B huấn luyện mô hình trên môi trường nguồn và dự đoán tập kiểm tra của môi trường đích, không huấn luyện lại. Sáu cặp nguồn–đích được tạo từ ba môi trường. Mỗi cặp chạy ở ba chế độ như Bảng 4:

- Ở N1, μ và σ lấy trên cửa sổ huấn luyện của **chính chuỗi đích**, không phải của môi trường nguồn. Nghiên cứu vì vậy không phải bài toán "không cần dữ liệu đích" (zero-shot), mà trả lời câu hỏi: quy luật biến động có chuyển giao được không, khi mỗi máy đích được chuẩn hoá bằng lịch sử của chính nó.
- Ở cả N1 và N2, 19 đặc trưng được sinh lại từ chuỗi đã biến đổi.
- Mọi dự đoán được đưa về thang CPU (%) gốc trước khi tính chỉ số, để ba chế độ so được với nhau.

Nếu so sai số chuyển giao với sai số của mô hình ở chế độ thô, con số thu được sẽ trộn hai tác động: tác động của chính phép chuẩn hoá và mất mát do chuyển giao. Vì vậy nhóm định nghĩa **mất mát chuyển giao** trên từng chuỗi đích s như sau:

::cong-thuc:: L(A→B, k, s) = MAE(mô hình học ở A, chế độ k, trên chuỗi s) / MAE(mô hình học ở B, chế độ k, trên chuỗi s)

Tử số và mẫu số dùng cùng loại mô hình, cùng siêu tham số, cùng chế độ, cùng chuỗi, cùng dòng kiểm tra; chỉ khác nơi mô hình được huấn luyện. L = 1 nghĩa là chuyển giao không mất gì; L = 1,3 nghĩa là tệ hơn 30% so với huấn luyện ngay tại đích. Khác biệt giữa chuyển giao và huấn luyện tại chỗ được kiểm định bằng Wilcoxon ghép cặp; tính bất đối xứng giữa hai chiều A→B và B→A được kiểm định bằng Mann–Whitney trên L.

Kết quả chính của RQ3 là cặp **E1 ↔ E2**, vì hai môi trường cùng đơn vị quan sát là máy ảo. Bốn cặp giữa Bitbrains và Alibaba được báo cáo như **phân tích bổ sung**: vì khác đơn vị quan sát, không thể gán khác biệt cho riêng bản chất môi trường.

## Kiểm soát tính đúng đắn

Ngoài việc so với bản tính độc lập, nhóm dùng hai loại phép kiểm không phụ thuộc cách hiện thực.

Loại thứ nhất là **bất biến toán học** của phép chuẩn hoá:

- dự báo ngây thơ qua N1 rồi đưa về thang gốc phải trùng dự báo ngây thơ ở N0, vì z-score là phép biến đổi affine;
- tương tự với trung bình trượt;
- dự báo ngây thơ ở N2 với Δ̂ = 0 phải trùng dự báo ngây thơ ở N0.

Trên dữ liệu thật, cả ba bất biến đạt với sai lệch tối đa 4,3·10⁻¹⁴. Loại thứ hai là **cố tình làm hỏng**: tám kiểu lỗi chuẩn hoá được cài vào mã nguồn, trong đó có dùng thống kê toàn chuỗi và sai phân bắc cầu giữa hai chuỗi; công cụ kiểm tra phải phát hiện được cả tám.

Trong quá trình thực hiện, hai lỗi vẫn lọt qua các phép kiểm này. Chúng được trình bày ở mục IV.D vì bản thân chúng là một phát hiện về phương pháp.

# Kết quả thực nghiệm và thảo luận

## Học máy so với dự báo ngây thơ (RQ1)

::bang:: Sai số của dự báo ngây thơ và số phép so học máy vượt ngây thơ có ý nghĩa thống kê

| Môi trường | MAE ngây thơ, h = 1 | h = 6 | h = 12 | Số phép so học máy vượt ngây thơ |
|---|---|---|---|---|
| E1 — máy ảo | 0,408 | 0,466 | 0,449 | **0 / 15** |
| E2 — máy ảo | 0,414 | 0,481 | 0,465 | **2 / 15** (chỉ SVR, h = 6 và 12) |
| E3 — máy vật lý | 4,296 | 6,509 | 7,027 | **11 / 15** |

Bảng 5 trả lời RQ1. Mỗi môi trường có 15 phép so (5 mô hình học máy × 3 tầm dự báo), mỗi phép là một kiểm định Wilcoxon ghép cặp trên toàn bộ chuỗi, có hiệu chỉnh Holm. Trên hai tập máy ảo, dự báo ngây thơ gần như không thể vượt qua: không mô hình nào vượt ở E1, và ở E2 chỉ SVR vượt ở tầm 30 và 60 phút. Trên máy vật lý, học máy vượt ở 11/15 phép so.

::hinh:: paper/figures/hinh3_ti-so-naive.png | Trung vị theo chuỗi của tỉ số MAE mô hình / MAE dự báo ngây thơ; xanh là tốt hơn ngây thơ, đỏ là tệ hơn | 16

Hình 3 cho thấy độ lớn của chênh lệch. Trên máy ảo, hồi quy tuyến tính và Ridge tệ hơn ngây thơ từ 1,30 đến 2,66 lần, và càng tệ khi tầm dự báo dài ra. Random Forest và XGBoost cũng tệ hơn ngây thơ ở hầu hết các ô. Trên máy vật lý, mọi mô hình học máy tốt hơn ngây thơ khoảng 6–16%.

Có hai điểm cần đọc đúng. Thứ nhất, siêu tham số được chọn đều nằm ở mép lưới, và Random Forest chỉ có 50 cây; phát biểu chính xác là *với lưới và ngân sách tính toán này*, học máy không vượt dự báo ngây thơ trên máy ảo. Tuy nhiên hồi quy tuyến tính không có siêu tham số nào để nới, mà vẫn tệ hơn ít nhất 1,30 lần ngay ở tầm 5 phút. Thứ hai, trên máy ảo, CPU ở lưới 5 phút biến động khó đoán và ít có chu kỳ ngày, nên giá trị hiện tại đã mang gần hết thông tin hữu ích về giá trị kế tiếp. Với bài toán cấp phát tài nguyên ngắn hạn cho máy ảo, dự báo ngây thơ vì thế là một mốc khó, và mọi đề xuất mô hình phức tạp nên được đặt cạnh mốc này.

## Khác biệt giữa các môi trường (RQ2)

Kết quả của RQ1 đọc theo cột môi trường trả lời RQ2: chuỗi ở mức máy vật lý của Alibaba dễ dự đoán hơn chuỗi ở mức máy ảo của Bitbrains, **một phần do hiệu ứng tổng hợp**. Hai đặc điểm ở Bảng 1 giải thích vì sao học máy có chỗ để thắng trên E3: tự tương quan bậc 1 cao hơn (0,86 so với 0,64–0,67), nghĩa là tín hiệu ít nhiễu hơn, và chu kỳ ngày rõ rệt (0,60 so với 0,13), là thứ dự báo ngây thơ không khai thác được mà đặc trưng lịch và giá trị trễ thì có.

Nhóm không phát biểu rằng "Alibaba dễ dự đoán hơn Bitbrains". Hai nguồn khác nhau đồng thời về đơn vị quan sát, mức tải và tỉ lệ chạm trần 100%. Riêng trần 100% làm dữ liệu máy ảo bị cắt ở vùng tải cao: 5,12% điểm của E1 nằm đúng tại trần, còn E3 thì không có điểm nào. Dữ liệu hiện có không tách được các yếu tố này.

## Khả năng chuyển giao giữa các môi trường (RQ3)

::hinh:: paper/figures/hinh4_mat-mat-transfer.png | Mất mát chuyển giao L theo cặp môi trường và chế độ chuẩn hoá; mỗi ô là trung vị qua 5 mô hình và các tầm dự báo (cột N2 hiện chỉ gồm h = 1, ⟦CHỜ QĐ-019⟧) | 12.5

::bang:: Mất mát chuyển giao L theo tầm dự báo (trung vị qua 5 mô hình)

| Cặp nguồn → đích | N0, h = 1 | N0, h = 6 | N0, h = 12 | N1, h = 1 | N1, h = 6 | N1, h = 12 | N2, h = 1 | N2, h = 6 và 12 |
|---|---|---|---|---|---|---|---|---|
| **E1 → E2** | 1,004 | 0,996 | 1,001 | 1,002 | 1,000 | 0,995 | 1,033 | ⟦CHỜ QĐ-019⟧ |
| **E2 → E1** | 0,974 | 1,072 | 1,081 | 1,026 | 1,075 | 1,067 | 0,970 | ⟦CHỜ QĐ-019⟧ |
| E1 → E3 | 1,063 | 1,059 | 1,043 | 1,032 | 1,025 | 1,096 | 1,064 | ⟦CHỜ QĐ-019⟧ |
| E2 → E3 | 1,070 | 1,088 | 1,070 | 1,044 | 1,042 | 1,085 | 1,054 | ⟦CHỜ QĐ-019⟧ |
| E3 → E1 | 2,279 | 3,320 | 2,516 | 1,096 | 1,332 | 1,435 | 1,427 | ⟦CHỜ QĐ-019⟧ |
| E3 → E2 | 2,216 | 3,421 | 3,422 | 1,100 | 1,175 | 1,319 | 1,586 | ⟦CHỜ QĐ-019⟧ |

Hình 4 và Bảng 6 trả lời RQ3. Nhóm đọc kết quả theo ba ý.

**Kết quả chính — chuyển giao giữa hai tập máy ảo gần như không mất mát.** Từ E1 sang E2, L nằm trong khoảng 0,995–1,004 ở cả N0 lẫn N1, tức mô hình học ở E1 dùng cho E2 tốt ngang mô hình học ngay tại E2. Chiều ngược lại tốn hơn một chút, 1,03–1,08 ở tầm 30 và 60 phút, và chiều E2→E1 tốn hơn chiều E1→E2 ở 11/15 phép so (N0) và 12/15 phép so (N1). Một giải thích khả dĩ, chưa được kiểm định, là E1 có lượng dữ liệu huấn luyện gấp khoảng 2,4 lần E2. Kết quả này cũng cho thấy chuẩn hoá z-score giúp dự đoán **ngay trong** môi trường máy ảo — tốt hơn N0 ở 9/15 phép so tại E1 và 8/15 tại E2 — nhưng không làm chuyển giao tốt thêm.

**Phân tích bổ sung — mức tải không chuyển giao được theo chiều từ máy vật lý sang máy ảo.** Ở dữ liệu thô, mô hình học trên Alibaba dùng cho Bitbrains tệ hơn mô hình học ngay tại Bitbrains từ 2,2 đến 3,4 lần, trong khi chiều ngược lại chỉ tốn 4–9%. Cần lưu ý rằng ở N0 chiều Bitbrains→Alibaba **không** thất bại, dù hai môi trường lệch mức tải hơn 20 lần: mô hình nhìn thấy giá trị trễ y(t−1) nên mức tải của chuỗi đích đi thẳng vào mô hình qua đặc trưng. Khi chuẩn hoá z-score theo chuỗi, mất mát chiều Alibaba→Bitbrains giảm còn 1,10 lần ở tầm 5 phút và 1,32–1,44 lần ở tầm 60 phút. Như vậy, phần lớn thất bại ở dữ liệu thô đến từ thang đo; phần còn lại tăng theo tầm dự báo.

**Hướng bất đối xứng giữ nguyên dù độ lớn giảm mạnh.** Kiểm định Mann–Whitney trên L cho thấy chiều Alibaba→Bitbrains tốn hơn chiều ngược lại ở 30/30 phép so ở N0 và 28/30 phép so ở N1. Ở N2 tầm 5 phút, chiều Alibaba→Bitbrains tốn 1,43–1,59 lần, cao hơn N1 ở cùng tầm (1,10). Kết quả N2 ở tầm 30 và 60 phút đang được tính lại ⟦CHỜ QĐ-019⟧, nên nhóm chưa kết luận chế độ nào chuyển giao tốt nhất ở tầm dài.

::hinh:: paper/figures/hinh5_phan-bo-L.png | Phân phối mất mát chuyển giao L theo từng chuỗi đích; hộp là khoảng tứ phân vị, râu là phân vị 5 và 95 | 16

Hình 5 bổ sung độ phân tán mà các trung vị ở Hình 4 che đi. Ở chiều Alibaba→Bitbrains dữ liệu thô, một phần tư số chuỗi có L trên 4, tức chuyển giao không chỉ tệ trung bình mà tệ trên diện rộng. Ở hai cặp máy ảo, gần như toàn bộ hộp nằm sát đường L = 1.

Để kiểm tra liệu riêng hiệu ứng tổng hợp có tạo ra bất đối xứng hay không, nhóm khai trước và chạy thêm một thí nghiệm "máy giả". Mỗi máy giả là trung bình của 5 máy ảo E1 ngẫu nhiên; 73 máy giả được đặt cạnh 368 máy ảo E1 **không** chung máy nào. Theo luật đọc đã khai, kết quả ở chế độ N1 là **không kết luận**: chiều từ máy giả sang máy ảo tốn hơn ở 8/15 phép so, chiều ngược lại ở 4/15 phép so, và hướng khác nhau theo họ mô hình. Tính trên cửa sổ huấn luyện, máy giả mượt hơn cả E3 (tự tương quan bậc 1 là 0,91 so với 0,85) nhưng không có chu kỳ ngày (tự tương quan ở 24 giờ là 0,03 so với 0,46). Điều đó cho thấy máy vật lý Alibaba khác "máy ảo gộp lại" không chỉ ở độ mượt. Nghiên cứu này vì vậy không gán được bất đối xứng cho riêng hiệu ứng tổng hợp, và cũng không gán được cho riêng khác biệt môi trường.

## Hai lỗi âm thầm của bước chuẩn hoá

::bang:: Tác động của máy đứng yên lên chế độ N1 (tầm 60 phút)

| Phép đo | Trước khi xử lý | Sau khi loại máy đứng yên khỏi tập huấn luyện |
|---|---|---|
| Hồi quy tuyến tính, E3 → E3, MAE trung vị | 42,83 | 6,19 (N0: 6,43) |
| XGBoost, E3 → E1, MAE / ngây thơ | 60,6 lần | 1,59 lần |
| Trung vị L của E3 → E1 và E3 → E2, gộp các tầm | 2,77 và 3,79 | 1,33 và 1,24 |

**Lỗi thứ nhất: z-score hỏng khi máy đứng yên trong cửa sổ huấn luyện.**
- *Nguyên nhân.* Mười máy E3, chiếm 2% quần thể, có CPU trung bình 0,00% trong toàn bộ cửa sổ huấn luyện rồi mới bắt đầu chạy ở vùng validation. Độ lệch chuẩn huấn luyện của chúng nhỏ tới 0,003, nên z-score ở vùng validation — vẫn thuộc dữ liệu khớp mô hình cuối — lên tới 30.196. Vài trăm điểm cực trị này kéo lệch hệ số của mô hình toàn cục và làm hỏng dự đoán cho **mọi** chuỗi, như Bảng 7 cho thấy.
- *Vì sao các phép kiểm không phát hiện.* Cả ba bất biến toán học vẫn đúng: thống kê chuẩn hoá được tính đúng như định nghĩa, cái sai nằm ở chính định nghĩa.
- *Cách khắc phục.* Nhóm loại chuỗi khỏi **tập huấn luyện** ở N1 (vẫn chấm như mọi chuỗi) khi giá trị z lớn nhất trong vùng khớp vượt giới hạn (n−1)/√n. Theo bất đẳng thức Samuelson [19], không điểm nào trong một mẫu n điểm vượt được giới hạn này, nên một điểm vượt nó mang giá trị mà chính cửa sổ huấn luyện không thể sinh ra. Luật không có tham số tự do. Nó loại 2, 1 và 10 chuỗi ở E1, E2 và E3, và được áp đồng đều cho mọi môi trường. Mọi con số N1 trong bài dùng bản đã xử lý; bản gốc được nêu ở Bảng 7.

**Lỗi thứ hai: định nghĩa đích của N2 bị hiện thực lệch ở tầm dự báo dài.**
- *Nguyên nhân.* Định nghĩa đúng của N2 là dự đoán Δ = y(t+h) − y(t), rồi đưa về thang gốc bằng ŷ = y(t) + Δ̂. Bản hiện thực ban đầu biến đổi chuỗi thành sai phân một bước trước, rồi lấy giá trị đích tại t+h **của chuỗi đã biến đổi**. Đích vì thế thành y(t+h) − y(t+h−1): chỉ một bước thay đổi thay vì h bước. Ở h = 1 hai định nghĩa trùng nhau; ở h = 6 và 12, mọi mô hình N2 bị kéo về gần dự báo ngây thơ.
- *Vì sao các phép kiểm không phát hiện.* Bất biến "Δ̂ = 0 cho lại dự báo ngây thơ" đúng với **cả hai** định nghĩa. Bản tính độc lập cũng hiện thực theo cùng một cách nên khớp tuyệt đối với bản sai.
- *Cách phát hiện và khắc phục.* Lỗi chỉ lộ ra khi nhóm soạn công thức cho bài báo và đối chiếu từng nguồn tài liệu. Nhóm đã bổ sung phép kiểm so trực tiếp giá trị đích với chuỗi CPU gốc bằng một đường tính độc lập (sai lệch phải bằng 0), xác nhận phép kiểm này phát hiện được bản sai, và đang chạy lại toàn bộ phần N2 ở h = 6, 12 ⟦CHỜ QĐ-019⟧.

Bài học chung của hai lỗi là: một bất biến chỉ có giá trị nếu nó **sai** khi hiện thực sai. Với mọi phép biến đổi giá trị đích, cần so trực tiếp đích với dữ liệu gốc bằng một đường tính khác, không chỉ kiểm các tính chất mà cả bản đúng lẫn bản sai cùng thoả mãn.

## Hàm ý thực tiễn

Với người vận hành hệ thống cấp phát tài nguyên, kết quả gợi ý bốn điều:

- **Trên máy ảo ở tầm 5–60 phút**, luôn đặt mô hình cạnh dự báo ngây thơ trước khi triển khai; mô hình phức tạp có thể tệ hơn cách đoán không cần học.
- **Trong cùng một nhà cung cấp và cùng đơn vị quan sát**, mô hình học ở cụm này có thể dùng cho cụm khác với mất mát không đáng kể.
- **Khi chuyển giao giữa các đơn vị quan sát khác nhau** (máy vật lý sang máy ảo), phải chuẩn hoá theo chuỗi bằng lịch sử của máy đích. Ngay cả khi đó vẫn còn mất mát 10–44% tuỳ tầm dự báo.
- **Bước chuẩn hoá cần được kiểm tra với các ca biên**, như máy vừa được bật lên. Đây là tình huống rất phổ biến trong trung tâm dữ liệu nhưng hiếm có trong dữ liệu kiểm thử.

# Kết luận và hướng phát triển

## Kết luận

Nghiên cứu này đánh giá tám mô hình dự đoán tải CPU trên 1.535 chuỗi thật từ ba môi trường đám mây công khai, với trọng tâm là hai câu hỏi về cách đánh giá: mô hình có vượt dự báo ngây thơ không, và mô hình có chuyển giao được giữa các môi trường không. Để trả lời, nhóm xây dựng một giao thức so ghép cặp theo chuỗi có kiểm định thống kê, và một cách đo mất mát chuyển giao L cùng chế độ chuẩn hoá, tách được tác động của phép chuẩn hoá khỏi mất mát do chuyển giao.

Ba kết luận chính đã được kiểm định:

1. Trên máy ảo, dự báo ngây thơ ở lưới 5 phút gần như không thể vượt qua với lưới siêu tham số đã dùng; học máy chỉ thắng rõ trên chuỗi ở mức máy vật lý, một phần nhờ hiệu ứng tổng hợp.
2. Chuyển giao giữa hai tập máy ảo cùng nhà cung cấp gần như không mất mát.
3. Chuyển giao từ máy vật lý sang máy ảo thất bại ở dữ liệu thô chủ yếu do thang đo; chuẩn hoá z-score theo chuỗi thu hẹp mất mát từ 2,2–3,4 lần xuống 1,10–1,44 lần, nhưng tính bất đối xứng giữa hai chiều vẫn còn.

Ngoài ra, nghiên cứu ghi nhận hai lỗi âm thầm của bước chuẩn hoá cùng cách phát hiện và khắc phục. Nhóm cho rằng đây là đóng góp có giá trị cho các nghiên cứu dùng lại quy trình tương tự.

## Hạn chế

- **Đơn vị quan sát lệch giữa Bitbrains (máy ảo) và Alibaba (máy vật lý).** Đây là nhiễu lớn nhất và không gỡ được bằng dữ liệu hiện có. Bảng sử dụng container của Alibaba có dung lượng hàng trăm GB và cũng không tương đương máy ảo.
- **Cửa sổ 8 ngày và mẫu 500 máy của Alibaba** giới hạn tính tổng quát. Bộ lọc loại khoảng 40% chuỗi máy ảo có tải thấp, nên kết luận chỉ áp dụng cho quần thể đã lọc.
- **Siêu tham số chọn ở mép lưới**, Random Forest chỉ 50 cây, SVR chỉ học trên mẫu con. Siêu tham số chọn ở N0 được dùng lại cho N1 và N2.
- **Chế độ N1 dùng lịch sử huấn luyện của chuỗi đích**, nên không phải chuyển giao không cần dữ liệu đích.
- **Kết quả N1 phụ thuộc cách xử lý máy đứng yên**; bản gốc và bản đã xử lý đều được báo cáo.
- **Với vài trăm chuỗi mỗi phép so**, những khác biệt rất nhỏ vẫn có ý nghĩa thống kê. Vì vậy mọi kết luận được đọc kèm độ lớn L.
- **Mốc thời gian của Alibaba là tương đối**, nên đặc trưng ngày trong tuần không mang nghĩa lịch thật.

## Hướng phát triển

Hướng thứ nhất là thay đơn vị quan sát cho đồng nhất: tìm bộ dữ liệu có cả máy ảo lẫn máy vật lý trong cùng một trung tâm dữ liệu, để tách hiệu ứng tổng hợp khỏi khác biệt môi trường. Hướng thứ hai là mở rộng lưới siêu tham số và thêm các mô hình chuỗi thời gian học sâu, nhưng luôn đặt cạnh dự báo ngây thơ. Hướng thứ ba là chuyển từ đánh giá sai số sang đánh giá theo quyết định cấp phát — ví dụ số lần thiếu tài nguyên — với ngưỡng được khai trước khi chạy. Cuối cùng, nhóm dự định công bố kèm mã nguồn các phép kiểm bất biến và phép kiểm đích, để các nghiên cứu khác kiểm tra được bước chuẩn hoá của mình.

# Lời cảm ơn

⟦CẦN BỔ SUNG⟧ Lời cảm ơn và thông tin tài trợ, nếu có. Bitbrains IT Services Inc. và Grid Workloads Archive yêu cầu ghi nhận nguồn khi sử dụng dữ liệu; nhóm trân trọng cảm ơn Bitbrains và Alibaba đã công bố bộ dữ liệu phục vụ nghiên cứu.

# Tài liệu tham khảo

::tltk:: [1]  R. N. Calheiros, E. Masoumi, R. Ranjan, R. Buyya (2015), "Workload prediction using ARIMA model and its impact on cloud applications' QoS," IEEE Transactions on Cloud Computing, vol. 3, no. 4, pp. 449–458.
::tltk:: [2]  J. Kumar, A. K. Singh (2018), "Workload prediction in cloud using artificial neural network and adaptive differential evolution," Future Generation Computer Systems, vol. 81, pp. 41–52.
::tltk:: [3]  M. Masdari, A. Khoshnevis (2020), "A survey and classification of the workload forecasting methods in cloud computing," Cluster Computing, vol. 23, pp. 2399–2424.
::tltk:: [4]  S. Makridakis, E. Spiliotis, V. Assimakopoulos (2018), "Statistical and Machine Learning forecasting methods: Concerns and ways forward," PLoS ONE, vol. 13, no. 3, e0194889.
::tltk:: [5]  R. J. Hyndman, A. B. Koehler (2006), "Another look at measures of forecast accuracy," International Journal of Forecasting, vol. 22, no. 4, pp. 679–688.
::tltk:: [6]  S. Kaufman, S. Rosset, C. Perlich, O. Stitelman (2012), "Leakage in data mining: Formulation, detection, and avoidance," ACM Transactions on Knowledge Discovery from Data, vol. 6, no. 4, pp. 1–21.
::tltk:: [7]  L. J. Tashman (2000), "Out-of-sample tests of forecasting accuracy: an analysis and review," International Journal of Forecasting, vol. 16, no. 4, pp. 437–450.
::tltk:: [8]  Nguyễn Quốc Chí, Lương Trần Ngọc Khiết, Lương Trần Hy Hiến, Trần Hoàng Đạt, Hoàng Tấn Dũng, Đoàn Quang Thiệu, Lê Minh Triết (⟦CẦN BỔ SUNG năm⟧), "Xây dựng mô hình phát hiện và cảnh báo các giao dịch bất thường trên ví điện tử," HUFLIT Journal of Science, ⟦CẦN BỔ SUNG tập, số⟧, pp. 81–98.
::tltk:: [9]  S. Shen, V. van Beek, A. Iosup (2015), "Statistical Characterization of Business-Critical Workloads Hosted in Cloud Datacenters," trong 15th IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing (CCGrid), Shenzhen, China.
::tltk:: [10]  J. Guo, Z. Chang, S. Wang, H. Ding, Y. Feng, L. Mao, Y. Bao (2019), "Who Limits the Resource Efficiency of My Datacenter: An Analysis of Alibaba Datacenter Traces," trong IEEE/ACM International Symposium on Quality of Service (IWQoS), Phoenix, USA.
::tltk:: [11]  B. A. Nosek, C. R. Ebersole, A. C. DeHaven, D. T. Mellor (2018), "The preregistration revolution," Proceedings of the National Academy of Sciences, vol. 115, no. 11, pp. 2600–2606.
::tltk:: [12]  L. Breiman (2001), "Random Forests," Machine Learning, vol. 45, no. 1, pp. 5–32.
::tltk:: [13]  T. Chen, C. Guestrin (2016), "XGBoost: A Scalable Tree Boosting System," trong Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp. 785–794.
::tltk:: [14]  H. Drucker, C. J. C. Burges, L. Kaufman, A. Smola, V. Vapnik (1997), "Support Vector Regression Machines," trong Advances in Neural Information Processing Systems 9, pp. 155–161.
::tltk:: [15]  F. Pedregosa và cộng sự (2011), "Scikit-learn: Machine Learning in Python," Journal of Machine Learning Research, vol. 12, pp. 2825–2830.
::tltk:: [16]  F. Wilcoxon (1945), "Individual comparisons by ranking methods," Biometrics Bulletin, vol. 1, no. 6, pp. 80–83.
::tltk:: [17]  S. Holm (1979), "A simple sequentially rejective multiple test procedure," Scandinavian Journal of Statistics, vol. 6, no. 2, pp. 65–70.
::tltk:: [18]  H. B. Mann, D. R. Whitney (1947), "On a test of whether one of two random variables is stochastically larger than the other," Annals of Mathematical Statistics, vol. 18, no. 1, pp. 50–60.
::tltk:: [19]  P. A. Samuelson (1968), "How Deviant Can You Be?," Journal of the American Statistical Association, vol. 63, no. 324, pp. 1522–1525.

::trang-moi::

::en-tieu-de:: MACHINE LEARNING FOR CLOUD CPU WORKLOAD PREDICTION: BENCHMARKING AGAINST NAIVE PERSISTENCE AND DECOMPOSING CROSS-ENVIRONMENT TRANSFERABILITY

::en-tac-gia:: Tran Hoang Dat*, Tran Hoang Phat, Luong Tran Ngoc Khiet

::abstract:: ABSTRACT— CPU utilization prediction underpins autoscaling in cloud computing, and machine learning models are routinely reported to achieve low errors. Two questions nevertheless often remain open: whether a model actually beats the trivial forecast "the next five minutes look like the last five", and whether a model trained in one datacenter remains useful in another. This study answers both on 1,535 real CPU series from three public environments: two Bitbrains virtual-machine traces and one Alibaba physical-machine trace. Eight models, three baselines and five learners (linear regression, Ridge, Random Forest, XGBoost, SVR), are evaluated at horizons of 5, 30 and 60 minutes using per-series paired Wilcoxon tests with Holm correction. To separate load level from dynamics under transfer, we run three normalization modes (raw, per-series z-score, differencing) and measure a transfer loss L against the same model trained directly on the target environment in the same mode. On virtual machines, naive persistence is almost unbeatable (0/15 and 2/15 significant comparisons), whereas on physical machines machine learning wins 11/15 comparisons. Transfer between the two virtual-machine traces is nearly lossless (L between 0.97 and 1.08). Transfer from physical to virtual machines costs 2.2 to 3.4 times on raw data, falls to 1.10 to 1.44 times with per-series z-scoring, while the reverse direction costs only 1.03 to 1.10 times. We also report two silent normalization pitfalls that standard checks miss, together with their detection and fixes.

::keywords:: Keywords— Cloud workload prediction, naive persistence, cross-environment transfer, time series normalization, data leakage

::tieu-su:: Trần Hoàng Đạt là sinh viên năm thứ ⟦CẦN BỔ SUNG⟧ của Trường Đại học Sư phạm TP.HCM vào thời điểm đăng bài báo này. Hiện đang quan tâm về các nghiên cứu trong lĩnh vực học máy ứng dụng, dự đoán chuỗi thời gian và phân tích dữ liệu.

::tieu-su:: Trần Hoàng Phát là sinh viên năm thứ ⟦CẦN BỔ SUNG⟧ của Trường Đại học Sư phạm TP.HCM vào thời điểm đăng bài báo này. Hướng nghiên cứu hiện tại tập trung vào tự động hóa quy trình nghiệp vụ và các ứng dụng trên nền tảng đám mây.

::tieu-su:: Lương Trần Ngọc Khiết nhận bằng Cử nhân Công nghệ phần mềm năm 2016 và Thạc sĩ Khoa học máy tính năm 2019 tại Trường Đại học Sư phạm TP. Hồ Chí Minh. Hiện ông là giảng viên tại Khoa Công nghệ thông tin, Trường Đại học Sư phạm TP. Hồ Chí Minh. Hướng nghiên cứu chính: Trí tuệ nhân tạo, phân tích dữ liệu và các ứng dụng công nghệ giáo dục.
