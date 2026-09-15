<!--
Bản thảo v3, 2026-09-15. Nguồn của paper/ban-thao-v3.docx (sinh bằng scripts/tao_docx.py).
Dựa trên bản v2 nhóm tác giả đã sửa trực tiếp trong Word, cộng các sửa sau rà soát:
số liệu (1,23; từ 1,07 đến 1,08; 6/15), trích dẫn cho công thức, bớt chi tiết kỹ thuật,
bỏ gạch ngang và chữ đậm. Chú thích hình/bảng KHÔNG gõ số: template HJS tự đánh.
Đối chiếu số: python scripts/doi_chieu_so_lieu_bai_bao.py
-->

::tieu-de:: HỌC MÁY DỰ ĐOÁN TẢI CPU TRÊN ĐÁM MÂY: KHI NÀO THẮNG ĐƯỢC DỰ BÁO NAÏVE VÀ CÓ DÙNG LẠI ĐƯỢC Ở TRUNG TÂM DỮ LIỆU KHÁC?

::tac-gia:: Trần Hoàng Đạt, Trần Hoàng Phát, Lương Trần Ngọc Khiết

::co-quan:: Khoa Công nghệ thông tin, Trường Đại học Sư Phạm TP.HCM

::email:: 4901104030@student.hcmue.edu.vn, 4901104107@student.hcmue.edu.vn, khietltn@hcmue.edu.vn

::tom-tat:: TÓM TẮT— Trung tâm dữ liệu cần biết trước máy chủ sắp bận đến mức nào để cấp thêm hoặc thu hồi tài nguyên đúng lúc: cấp thiếu thì dịch vụ chậm, cấp thừa thì tốn điện và tiền thuê máy. Học máy thường được dùng để dự đoán việc này, nhưng hai điều quan trọng ít khi được kiểm chứng. Thứ nhất, mô hình học máy có thật sự đoán tốt hơn cách đơn giản nhất, cho rằng mấy phút tới máy vẫn bận y như lúc này, gọi là dự báo naïve, hay không. Thứ hai, một mô hình đã học ở trung tâm dữ liệu này có đem sang dùng được ở trung tâm dữ liệu khác hay không. Nhóm chúng tôi kiểm chứng hai điều đó trên dữ liệu thật của 1.535 máy từ hai nhà cung cấp là Bitbrains (máy ảo) và Alibaba (máy chủ vật lý), với năm mô hình học máy phổ biến, dự đoán trước 5, 30 và 60 phút. Mọi phép so sánh được làm trên từng máy và kiểm tra bằng thống kê, để kết luận không phụ thuộc vào may rủi. Kết quả cho thấy với máy ảo, dự báo naïve gần như không bị mô hình học máy nào vượt qua. Chỉ với máy chủ vật lý, học máy mới thắng rõ ràng. Mô hình học ở nhóm máy ảo này dùng cho nhóm máy ảo khác của cùng nhà cung cấp chỉ kém đi không quá 8%. Ngược lại, mô hình học trên máy chủ Alibaba đem sang máy ảo Bitbrains kém đi từ 2,2 đến 3,4 lần. Nếu đưa dữ liệu của từng máy về cùng một thang đo trước khi dự đoán, mức kém đi giảm còn từ 10% đến 44%. Nhóm cũng chỉ ra hai lỗi dễ mắc khi xử lý dữ liệu cho bài toán này và cách tránh. Kết quả giúp người vận hành biết khi nào nên đầu tư vào học máy, khi nào dự báo naïve là đủ, và có thể dùng lại một mô hình ở nơi khác đến mức nào.

::tu-khoa:: Từ khóa— Dự đoán tải CPU, điện toán đám mây, dự báo naïve, học máy, dùng lại mô hình giữa các trung tâm dữ liệu

# Giới thiệu

Điện toán đám mây cho phép cấp phát tài nguyên theo nhu cầu, nhưng quyết định cấp phát chỉ tốt khi dự đoán được tải sắp tới. Dự đoán quá thấp gây quá tải và vi phạm cam kết chất lượng dịch vụ, dự đoán quá cao gây lãng phí máy chủ và điện năng. Vì vậy dự đoán mức sử dụng CPU đã được nghiên cứu từ các mô hình thống kê như ARIMA [1] đến mạng nơ-ron và các mô hình học máy khác [2], với nhiều khảo sát tổng hợp các hướng tiếp cận [3].

Tuy nhiên, khi đọc các kết quả dự đoán, nhóm chúng tôi nhận thấy hai khoảng trống về cách đánh giá. Khoảng trống thứ nhất là mốc so sánh. Một mô hình đạt sai số tuyệt đối trung bình (MAE) thấp chưa chắc đã tốt, vì trên dữ liệu CPU lấy mẫu dày, cách đoán đơn giản nhất là lấy giá trị hiện tại làm dự đoán cho bước sau, gọi là dự báo naïve, thường đã cho sai số rất thấp. Các nghiên cứu so sánh quy mô lớn đã cảnh báo rằng mô hình học máy không phải lúc nào cũng vượt được các phương pháp đơn giản [4], và chỉ số MASE ra đời chính để đo sai số tương đối so với dự báo naïve [5]. Nếu không so với mốc này, không thể biết mô hình học được điều gì mà cách đoán naïve không làm được.

Khoảng trống thứ hai là việc dùng lại mô hình giữa các môi trường. Trong vận hành thực tế, một mô hình thường được huấn luyện ở một trung tâm dữ liệu rồi đem dùng cho máy mới hoặc cụm máy khác. Khi đánh giá khả năng này bằng sai số thô, con số thu được trộn lẫn hai nguồn khác biệt: chênh lệch mức tải trung bình và khác biệt về động lực học, tức cách tải lên xuống theo thời gian. Trên dữ liệu của nghiên cứu này, chỉ riêng một hằng số bằng mức tải trung bình của tập máy ảo Bitbrains fastStorage đem áp cho máy vật lý Alibaba đã cho MAE 28,24, tức không cần mô hình nào cũng *“chuyển giao thất bại”*. Một kết luận như vậy đúng nhưng không cho biết gì. Thêm vào đó, bước chuẩn hoá dùng để loại mức tải lại dễ gây rò rỉ dữ liệu, tức vô tình dùng thông tin mà lúc dự đoán thật chưa có [6]. Những lỗi như vậy thường không làm chương trình báo lỗi mà chỉ làm con số đẹp lên hoặc sai lệch một cách âm thầm.

Hai khoảng trống này có hệ quả rất cụ thể cho người vận hành. Nếu dự báo naïve đã đủ tốt, việc thu thập dữ liệu, huấn luyện và bảo trì một mô hình học máy là chi phí không mang lại lợi ích. Nếu một mô hình đã học có thể dùng lại ở trung tâm dữ liệu khác, một cụm máy mới không phải chờ tích luỹ đủ lịch sử mới có dự đoán. Còn nếu không dùng lại được, cần biết nó kém đi bao nhiêu và vì sao, để quyết định có nên huấn luyện lại hay không.

Xuất phát từ đó, nghiên cứu này đặt ba câu hỏi. Đầu tiên là có mô hình học máy nào dự đoán tải CPU tốt nhất, và có vượt được dự báo naïve không? Thứ hai là kết quả thay đổi thế nào giữa các môi trường? Cuối cùng là mô hình huấn luyện ở môi trường này có dùng được ở môi trường khác không, và phần nào của tín hiệu tải dùng lại được?

Nghiên cứu đóng góp ba điều. (1) Một câu trả lời có kiểm chứng cho câu hỏi *“học máy có đáng dùng không”*. Trên dữ liệu thật của 1.535 máy, mỗi mô hình được so với dự báo naïve trên từng máy và kiểm tra bằng thống kê. Kết quả rõ ràng là với máy ảo thì gần như không đáng: tải máy ảo biến động khó đoán và hầu như không lặp lại theo ngày, nên giá trị hiện tại đã chứa gần hết thông tin có ích và dự báo naïve rất khó bị vượt. Với máy chủ vật lý thì ngược lại, học máy thật sự đáng dùng. (2) Một cách đo mới cho câu hỏi *“mô hình có dùng lại được ở nơi khác không”*. Thay vì chỉ nhìn sai số, nhóm so mô hình đem từ nơi khác sang với chính mô hình đó học ngay tại chỗ, sau khi đã loại khác biệt về thang đo. Nhờ vậy tách được phần kém đi do hai nơi có mức tải khác nhau và phần kém đi do tải ở hai nơi biến động khác nhau. (3) Hai lỗi dễ mắc khi chuẩn bị dữ liệu, cùng cách phát hiện. Lỗi thứ nhất xảy ra khi có máy gần như tắt trong giai đoạn học rồi mới bật lên. Lỗi thứ hai xảy ra khi dự đoán mức thay đổi của tải ở tầm xa. Cả hai không làm chương trình báo lỗi mà chỉ làm kết quả sai lệch, và đều lọt qua các cách kiểm tra thông thường. Các nhóm dùng lại quy trình tương tự có thể tránh được.

Phần II tiếp theo tổng quan các nghiên cứu liên quan. Phần III trình bày dữ liệu, mô hình và cách đánh giá. Phần IV báo cáo kết quả và thảo luận. Phần V kết luận, nêu hạn chế và hướng phát triển.

# Tổng quan tài liệu

## Dự đoán tải tài nguyên trên đám mây

Dự đoán tải đám mây thường được đặt thành bài toán chuỗi thời gian: từ lịch sử sử dụng tài nguyên của một máy, dự đoán giá trị ở một hoặc nhiều bước tới. Calheiros và cộng sự [1] dùng ARIMA để dự đoán tải và phân tích tác động của sai số dự đoán tới chất lượng dịch vụ. Kumar và Singh [2] kết hợp mạng nơ-ron với thuật toán tiến hoá vi phân thích nghi để cải thiện độ chính xác. Masdari và Khoshnevis [3] khảo sát và phân loại các phương pháp dự đoán tải đã được đề xuất cho điện toán đám mây.

## Mốc so sánh và chỉ số đánh giá

Makridakis và cộng sự [4] so sánh các phương pháp thống kê và học máy trên 1.045 chuỗi thời gian theo tháng, và ghi nhận rằng các phương pháp học máy thường không vượt được phương pháp thống kê đơn giản khi đánh giá ngoài mẫu. Hyndman và Koehler [5] đề xuất MASE, chia sai số của mô hình cho sai số của dự báo naïve một bước trên tập huấn luyện, nhờ đó so sánh được giữa các chuỗi có thang đo khác nhau. Tashman [7] nhấn mạnh rằng đánh giá dự báo phải dùng dữ liệu nằm sau giai đoạn huấn luyện, để mô hình không nhìn thấy tương lai.

## Dữ liệu tải công khai và dùng lại mô hình giữa môi trường

Hai nguồn dữ liệu được dùng rộng rãi là Bitbrains, nơi Shen và cộng sự [8] phân tích đặc trưng tải của các máy ảo phục vụ ứng dụng doanh nghiệp, và bộ vết cụm máy Alibaba 2018, được Guo và cộng sự [9] phân tích hiệu quả sử dụng tài nguyên ở mức máy vật lý. Hai nguồn này khác nhau không chỉ ở tổ chức vận hành mà còn ở đơn vị quan sát: Bitbrains ghi từng máy ảo, Alibaba ghi từng máy vật lý chứa nhiều container. Chuỗi ở mức máy vật lý vì thế là tổng của nhiều tải nhỏ và mượt hơn một cách hệ thống. Khi so sánh hay dùng lại mô hình giữa hai nguồn, khác biệt này phải được nêu rõ.

Khi dùng lại mô hình, chuẩn hoá từng chuỗi là cách phổ biến để loại chênh lệch mức tải. Nhưng thống kê chuẩn hoá phải được tính chỉ trên phần dữ liệu huấn luyện, vì dùng thống kê của toàn chuỗi là đưa thông tin tương lai vào mô hình, một dạng rò rỉ dữ liệu theo nghĩa của Kaufman và cộng sự [6].

## Khoảng trống nghiên cứu

Từ các nghiên cứu trên, nhóm xác định ba khoảng trống. Thứ nhất, hiếm có đánh giá nào so ghép cặp mô hình học máy với dự báo naïve trên từng chuỗi, kèm kiểm định thống kê, ở nhiều môi trường cùng lúc. Khoảng trống này ứng với hai câu hỏi đầu. Thứ hai, khả năng dùng lại mô hình thường được đo bằng sai số thô, không tách được đâu là do mức tải, đâu là do động lực học. Khoảng trống này ứng với câu hỏi thứ ba. Thứ ba, các lỗi ở bước chuẩn hoá hiếm khi được báo cáo cùng cách phát hiện, ứng với đóng góp thứ ba của bài.

# Phương pháp nghiên cứu

## Quy trình nghiên cứu

::hinh:: paper/figures/hinh1_quy-trinh.png | Sơ đồ quy trình nghiên cứu | 15.5

Quy trình được tổ chức như Hình 1. Dữ liệu thô của ba môi trường được đưa về cùng lưới thời gian và cùng cửa sổ quan sát, rồi sinh một bộ đặc trưng quá khứ chung. Từ đó chia thành hai thí nghiệm. Thí nghiệm 1 đánh giá mô hình trong từng môi trường để trả lời hai câu hỏi đầu. Thí nghiệm 2 đánh giá mô hình khi đem từ môi trường này sang môi trường khác để trả lời câu hỏi thứ ba.

## Dữ liệu

::bang:: Ba môi trường dữ liệu sau tiền xử lý

| | E1: Bitbrains fastStorage | E2: Bitbrains Rnd | E3: Alibaba 2018 |
|---|---|---|---|
| Nguồn | [8] | [8] | [9] |
| Đơn vị quan sát | máy ảo | máy ảo | máy vật lý |
| Số chuỗi đưa vào | 1.250 | 500 (tháng 8/2013) | 500 (mẫu phân tầng từ 4.023) |
| Số chuỗi bị loại | 515 | 198 | 2 |
| Số chuỗi giữ lại | 735 | 302 | 498 |
| Trung vị CPU (%) | 1,78 | 1,77 | 37,83 |
| Tự tương quan bậc 1 | 0,67 | 0,64 | 0,86 |
| Tự tương quan ở 24 giờ | 0,13 | 0,13 | 0,60 |
| Tỉ lệ điểm chạm trần 100% | 5,12% | 2,28% | 0% |

Nghiên cứu dùng ba môi trường như Bảng 1. E1 và E2 là hai tập máy ảo của Bitbrains [8], ghi CPU theo phần trăm mỗi 5 phút. E3 là bảng sử dụng máy vật lý trong bộ vết cụm Alibaba năm 2018 [9], ghi khoảng 10 giây một lần. Do tệp gốc của Alibaba lớn (9 GB, gần 247 triệu dòng), nhóm lấy mẫu phân tầng 500 máy theo mức CPU trung bình, với danh sách máy được cố định để mọi lần chạy dùng đúng một quần thể. Biến mục tiêu ở cả ba môi trường là CPU tính theo phần trăm, thang từ 0 đến 100.

::hinh:: paper/figures/hinh2_phan-phoi-cpu.png | Phân phối CPU (%) của ba môi trường sau tiền xử lý | 16.5

Hình 2 cho thấy khác biệt lớn nhất giữa các môi trường là mức tải. Hơn một nửa số điểm của hai tập máy ảo nằm dưới 2% CPU với đồ thị lệch phải nặng, trong khi máy vật lý của Alibaba tập trung quanh khoảng 30% đến 50%. Bảng 1 còn cho thấy khác biệt về độ mượt: chuỗi máy vật lý có tự tương quan bậc 1 là 0,86 và chu kỳ ngày rõ (tự tương quan ở độ trễ 24 giờ là 0,60), so với 0,64 đến 0,67 và 0,13 ở máy ảo. Một phần khác biệt này đến từ hiệu ứng tổng hợp: một máy vật lý là tổng của nhiều container, nên dao động nhỏ của từng container triệt tiêu lẫn nhau.

## Tiền xử lý và đặc trưng

Tiền xử lý gồm các bước theo thứ tự:

- Cắt CPU về khoảng [0, 100].
- Đưa về lưới 5 phút bằng trung bình các mẫu trong mỗi ô thời gian.
- Lấy cửa sổ 8 ngày đầu của mỗi môi trường, tức 2.304 điểm, vì Alibaba chỉ có 8 ngày.
- Nội suy tuyến tính các lỗ hổng dài tối đa 10 phút. Lỗ dài hơn giữ nguyên là giá trị thiếu. Nhóm không lấp bằng giá trị trước đó, vì cách đó tạo đoạn phẳng giả và làm tăng tự tương quan, là đại lượng quan trọng khi so sánh các môi trường.
- Loại những chuỗi không có điểm nào trong cửa sổ, có CPU trung bình dưới 1% (máy gần như không hoạt động), gần như hằng số, hoặc có quá ít dữ liệu huấn luyện.

Bộ lọc loại 41% chuỗi của E1 và 40% của E2 nhưng chỉ 0,4% của E3, và loại gần như hoàn toàn ở phía tải thấp. Mọi phát biểu của nghiên cứu vì vậy chỉ áp dụng cho quần thể đã lọc.

Mỗi thời điểm t được mô tả bằng 19 đặc trưng, chỉ lấy từ quá khứ của chính máy đó: sáu giá trị trễ từ 5 phút đến 2 giờ trước, trung bình, độ lệch chuẩn, giá trị nhỏ nhất và lớn nhất trong 30 phút và 60 phút gần nhất, mức thay đổi so với bước trước, cùng bốn đặc trưng mô tả giờ trong ngày và ngày trong tuần. Mọi mô hình học máy dùng chung bộ đặc trưng này.

## Chia dữ liệu và mô hình

Mỗi môi trường được chia theo thời gian, không xáo trộn [7]: 70% đầu cửa sổ để huấn luyện (Train), 15% tiếp theo để chọn siêu tham số (Validation), 15% cuối để kiểm tra (Test). Ranh giới tính theo cùng một mốc thời gian cho mọi máy của môi trường, và dòng nào có giá trị cần dự đoán rơi sang phía bên kia ranh giới thì bị loại. Mô hình cuối được huấn luyện trên Train và Validation, rồi chấm trên Test đúng một lần.

Nhóm dùng ba mô hình cơ sở không cần huấn luyện [10]. Dự báo naïve lấy giá trị hiện tại làm dự đoán, ŷ(t+h) = y(t). Trung bình trượt lấy trung bình 6 điểm gần nhất. Dự báo naïve theo mùa, ở dạng đơn giản, lấy giá trị tại thời điểm t của ngày hôm trước, ŷ(t+h) = y(t−288), với 288 là số điểm 5 phút trong một ngày. Năm mô hình học máy là hồi quy tuyến tính, hồi quy Ridge, Random Forest [11], XGBoost [12] và hồi quy vector hỗ trợ SVR [13], được hiện thực bằng scikit-learn [14] và thư viện XGBoost. Mỗi mô hình học máy là một mô hình chung, học trên mọi máy của môi trường, không phải mỗi máy một mô hình. Siêu tham số được chọn trên tập Validation. Ba tầm dự báo là h = 1, 6 và 12 bước, tương ứng 5, 30 và 60 phút. Random Forest chỉ dùng 50 cây và SVR chỉ học trên mẫu con 10.000 dòng vì giới hạn tính toán, điều này được nêu lại trong phần hạn chế.

## Chỉ số và kiểm định thống kê

Chỉ số chính là MAE [5], tính riêng trên từng máy rồi tóm tắt bằng trung vị qua các máy:

::cong-thuc:: MAE = (1/n) · Σ |y(t+h) − ŷ(t+h)|

trong đó n là số dòng kiểm tra của máy, y(t+h) là giá trị thật và ŷ(t+h) là giá trị dự đoán. Nhóm không dùng MAPE vì nhiều máy ảo có CPU gần 0, làm MAPE tăng vô hạn [5].

Để kết luận một mô hình tốt hơn mô hình khác, nhóm dùng kiểm định Wilcoxon hạng có dấu [15] trên MAE ghép cặp theo từng máy, với mức ý nghĩa 0,05 và hiệu chỉnh Holm [16] khi thực hiện nhiều phép so cùng lúc. Hướng của kết luận lấy từ trung vị của hiệu ghép cặp, không lấy từ hiệu của hai trung vị, vì hai cách này có thể cho kết luận ngược nhau.

## Thí nghiệm 2: ba cách chuẩn hoá và mất mát khi dùng lại mô hình

Thí nghiệm 2 huấn luyện mô hình trên môi trường nguồn rồi dự đoán tập kiểm tra của môi trường đích, không huấn luyện lại. Ba môi trường tạo ra sáu cặp nguồn và đích. Mỗi cặp được chạy với ba cách chuẩn hoá như Bảng 2.

::bang:: Ba cách chuẩn hoá dùng trong Thí nghiệm 2

| Chế độ | Biến đổi chuỗi | Giá trị cần dự đoán | Đưa về CPU (%) | Loại bỏ thành phần nào |
|---|---|---|---|---|
| N0: thô | không | y(t+h) | giữ nguyên | không |
| N1: z-score theo chuỗi [17] | z(t) = (y(t) − μ) / σ | z(t+h) | ŷ = ẑ·σ + μ | mức tải và biên độ |
| N2: sai phân [10] | d(t) = y(t) − y(t−1) | Δ = y(t+h) − y(t) | ŷ = y(t) + Δ̂ | mức tải |

Ở N1, trung bình μ và độ lệch chuẩn σ lấy trên phần huấn luyện của chính máy đích, không phải của môi trường nguồn. Nghiên cứu vì vậy không xét trường hợp *“hoàn toàn không có dữ liệu đích”*, mà trả lời câu hỏi: quy luật biến động có dùng lại được không, khi mỗi máy đích được chuẩn hoá bằng lịch sử của chính nó. Ở N1 và N2, 19 đặc trưng được sinh lại từ chuỗi đã biến đổi. Mọi dự đoán được đưa về thang CPU (%) gốc trước khi tính MAE, để ba chế độ so được với nhau.

Nếu so sai số khi dùng lại mô hình với sai số của mô hình ở dữ liệu thô, con số thu được sẽ trộn hai tác động: tác động của chính phép chuẩn hoá và phần mất mát do đem mô hình sang nơi khác. Để tách hai tác động này, nhóm đề xuất đo mất mát chuyển giao trên từng máy đích s như sau:

::cong-thuc:: L(A→B, k, s) = MAE(mô hình học ở A, chế độ k, trên máy s) / MAE(mô hình học ở B, chế độ k, trên máy s)

Tử số và mẫu số dùng cùng loại mô hình, cùng siêu tham số, cùng chế độ, cùng máy và cùng dữ liệu kiểm tra, chỉ khác nơi mô hình được huấn luyện. L = 1 nghĩa là đem mô hình sang không mất gì, L = 1,3 nghĩa là tệ hơn 30% so với huấn luyện ngay tại đích. Để so hai chiều từ A sang B và từ B sang A, vốn chấm trên hai tập máy khác nhau, nhóm dùng kiểm định Mann-Whitney [18] trên L.

Kết quả chính của câu hỏi thứ ba là cặp E1 và E2, vì hai môi trường cùng đơn vị quan sát là máy ảo. Bốn cặp giữa Bitbrains và Alibaba được báo cáo như phân tích bổ sung: vì khác đơn vị quan sát, không thể gán khác biệt cho riêng bản chất môi trường.

Để chắc chắn phép chuẩn hoá được hiện thực đúng, nhóm kiểm tra ba tính chất mà nó phải thoả mãn về mặt toán học. Dự báo naïve đi qua N1 rồi đưa về thang gốc phải trùng với dự báo naïve ở N0, vì z-score chỉ là phép co giãn và tịnh tiến. Điều tương tự phải đúng với trung bình trượt. Dự báo naïve ở N2 với Δ̂ = 0 cũng phải trùng với dự báo naïve ở N0. Trên dữ liệu thật, sai lệch lớn nhất là 4,3·10⁻¹⁴, tức chỉ là sai số làm tròn của máy tính. Dù vậy, trong quá trình thực hiện vẫn có hai lỗi lọt qua các phép kiểm này. Chúng được trình bày ở mục IV.D vì bản thân chúng là một phát hiện về phương pháp.

# Kết quả thực nghiệm và thảo luận

## Học máy so với dự báo naïve

::bang:: Sai số của dự báo naïve và số phép so học máy vượt naïve có ý nghĩa thống kê

| Môi trường | MAE naïve, h = 1 | h = 6 | h = 12 | Số phép so học máy vượt naïve |
|---|---|---|---|---|
| E1 (máy ảo) | 0,408 | 0,466 | 0,449 | 0 / 15 |
| E2 (máy ảo) | 0,414 | 0,481 | 0,465 | 2 / 15 (chỉ SVR, h = 6 và 12) |
| E3 (máy vật lý) | 4,296 | 6,509 | 7,027 | 11 / 15 |

Bảng 3 trả lời câu hỏi thứ nhất. Mỗi môi trường có 15 phép so (5 mô hình học máy nhân 3 tầm dự báo), mỗi phép là một kiểm định Wilcoxon ghép cặp trên toàn bộ máy, có hiệu chỉnh Holm. Trên hai tập máy ảo, dự báo naïve gần như không thể vượt qua: không mô hình nào vượt ở E1, và ở E2 chỉ SVR vượt ở tầm 30 và 60 phút. Trên máy vật lý, học máy vượt ở 11/15 phép so.

::hinh:: paper/figures/hinh3_ti-so-naive.png | Trung vị theo máy của tỉ số MAE mô hình chia MAE dự báo naïve; xanh là tốt hơn naïve, đỏ là tệ hơn | 16

Hình 3 cho thấy độ lớn của chênh lệch. Trên máy ảo, hồi quy tuyến tính và Ridge tệ hơn naïve từ 1,30 đến 2,66 lần, và càng tệ khi tầm dự báo dài ra. Random Forest và XGBoost cũng tệ hơn naïve ở hầu hết các ô. Trên máy vật lý, mọi mô hình học máy tốt hơn naïve khoảng từ 6% đến 16%.

Có hai điểm cần đọc đúng. Thứ nhất, siêu tham số được chọn đều nằm ở biên của khoảng tìm kiếm, và Random Forest chỉ có 50 cây, nên phát biểu chính xác là *“với khoảng tìm kiếm và ngân sách tính toán này”*, học máy không vượt dự báo naïve trên máy ảo. Tuy nhiên hồi quy tuyến tính không có siêu tham số nào để nới, mà vẫn tệ hơn ít nhất 1,30 lần ngay ở tầm 5 phút. Thứ hai, trên máy ảo, CPU ở lưới 5 phút biến động khó đoán và ít có chu kỳ ngày, nên giá trị hiện tại đã mang gần hết thông tin hữu ích về giá trị kế tiếp. Với bài toán cấp phát tài nguyên ngắn hạn cho máy ảo, dự báo naïve vì thế là một mốc khó, và mọi đề xuất mô hình phức tạp nên được đặt cạnh mốc này.

## Khác biệt giữa các môi trường

Đọc kết quả trên theo từng môi trường sẽ trả lời câu hỏi thứ hai: chuỗi ở mức máy vật lý của Alibaba dễ dự đoán hơn chuỗi ở mức máy ảo của Bitbrains, một phần do hiệu ứng tổng hợp. Hai đặc điểm ở Bảng 1 giải thích vì sao học máy có chỗ để thắng trên E3: tự tương quan bậc 1 cao hơn (0,86 so với 0,64 và 0,67), nghĩa là tín hiệu ít nhiễu hơn, và chu kỳ ngày rõ rệt (0,60 so với 0,13), là thứ dự báo naïve không khai thác được mà đặc trưng lịch và giá trị trễ thì có.

Nhóm không phát biểu rằng *“Alibaba dễ dự đoán hơn Bitbrains”*. Hai nguồn khác nhau đồng thời về đơn vị quan sát, mức tải và tỉ lệ chạm trần 100%. Riêng trần 100% làm dữ liệu máy ảo bị cắt ở vùng tải cao: 5,12% điểm của E1 nằm đúng tại trần, còn E3 thì không có điểm nào. Dữ liệu hiện có không tách được các yếu tố này.

## Khả năng dùng lại mô hình giữa các môi trường

::hinh:: paper/figures/hinh4_mat-mat-transfer.png | Mất mát chuyển giao L theo cặp môi trường và cách chuẩn hoá; mỗi ô là trung vị qua 5 mô hình và 3 tầm dự báo | 12.5

::bang:: Mất mát chuyển giao L theo tầm dự báo (trung vị qua 5 mô hình)

| Nguồn → đích | N0, h = 1 | N0, h = 6 | N0, h = 12 | N1, h = 1 | N1, h = 6 | N1, h = 12 | N2, h = 1 | N2, h = 6 | N2, h = 12 |
|---|---|---|---|---|---|---|---|---|---|
| E1 → E2 | 1,004 | 0,996 | 1,001 | 1,002 | 1,000 | 0,995 | 1,033 | 0,950 | 0,894 |
| E2 → E1 | 0,974 | 1,072 | 1,081 | 1,026 | 1,075 | 1,067 | 0,970 | 1,109 | 1,214 |
| E1 → E3 | 1,063 | 1,059 | 1,043 | 1,032 | 1,025 | 1,096 | 1,064 | 1,016 | 0,996 |
| E2 → E3 | 1,070 | 1,088 | 1,070 | 1,044 | 1,042 | 1,085 | 1,054 | 1,048 | 1,009 |
| E3 → E1 | 2,279 | 3,320 | 2,516 | 1,096 | 1,332 | 1,435 | 1,427 | 1,820 | 1,736 |
| E3 → E2 | 2,216 | 3,421 | 3,422 | 1,100 | 1,175 | 1,319 | 1,586 | 1,834 | 1,618 |

Hình 4 và Bảng 4 trả lời câu hỏi thứ ba. Nhóm đọc kết quả theo bốn ý.

Ý thứ nhất, cũng là kết quả chính, là mô hình dùng lại giữa hai tập máy ảo gần như không mất gì. Từ E1 sang E2, L nằm trong khoảng từ 0,995 đến 1,004 ở cả N0 lẫn N1, tức mô hình học ở E1 dùng cho E2 tốt ngang mô hình học ngay tại E2. Chiều ngược lại tốn hơn một chút, từ 1,07 đến 1,08 ở tầm 30 và 60 phút, và chiều từ E2 sang E1 tốn hơn chiều từ E1 sang E2 ở 11/15 phép so với N0 và 12/15 phép so với N1. Một giải thích khả dĩ, chưa được kiểm định, là E1 có lượng dữ liệu huấn luyện gấp khoảng 2,4 lần E2. Với N2, chiều từ E2 sang E1 tốn hơn rõ ở tầm dài (từ 1,11 đến 1,21), còn chiều từ E1 sang E2 lại tốt hơn cả mô hình học tại chỗ (từ 0,89 đến 0,95). Kết quả cũng cho thấy chuẩn hoá z-score giúp dự đoán ngay trong môi trường máy ảo (tốt hơn N0 ở 9/15 phép so tại E1 và 8/15 tại E2) nhưng không làm việc dùng lại mô hình tốt thêm.

Ý thứ hai, thuộc phân tích bổ sung, là mức tải không dùng lại được theo chiều từ máy vật lý sang máy ảo. Ở dữ liệu thô, mô hình học trên Alibaba dùng cho Bitbrains tệ hơn mô hình học ngay tại Bitbrains từ 2,2 đến 3,4 lần, trong khi chiều ngược lại chỉ tốn từ 4% đến 9%. Cần lưu ý rằng ở N0, chiều từ Bitbrains sang Alibaba không thất bại dù hai môi trường lệch mức tải hơn 20 lần, vì mô hình nhìn thấy giá trị trễ y(t−1) nên mức tải của máy đích đi thẳng vào mô hình qua đặc trưng. Khi chuẩn hoá z-score theo chuỗi, mất mát chiều từ Alibaba sang Bitbrains giảm còn 1,10 lần ở tầm 5 phút và từ 1,32 đến 1,44 lần ở tầm 60 phút. Như vậy, phần lớn thất bại ở dữ liệu thô đến từ thang đo, phần còn lại tăng theo tầm dự báo.

Ý thứ ba là chuẩn hoá z-score theo chuỗi là cách dùng lại mô hình tốt nhất. Ở chiều từ Alibaba sang Bitbrains, N1 cho mất mát thấp nhất ở cả ba tầm dự báo (từ 1,10 đến 1,44). Cách sai phân N2 cũng loại được mức tải nên tốt hơn hẳn dữ liệu thô, nhưng kém N1 ở mọi tầm (từ 1,43 đến 1,59 ở tầm 5 phút, từ 1,62 đến 1,83 ở tầm 30 và 60 phút). Nói cách khác, khi chuyển từ máy vật lý sang máy ảo, việc đưa cả mức tải lẫn biên độ dao động của từng máy về cùng thang đo giữ lại nhiều thông tin hữu ích hơn so với chỉ dự đoán mức thay đổi. Ở chiều ngược lại, cả ba cách đều cho mất mát nhỏ (từ 0,996 đến 1,096).

Ý thứ tư là sự bất đối xứng giữa hai chiều không mất đi khi chuẩn hoá. Kiểm định Mann-Whitney trên L cho thấy chiều từ Alibaba sang Bitbrains tốn hơn chiều ngược lại ở 30/30 phép so với N0, 28/30 với N1 và 26/30 với N2. Độ lớn chênh lệch giảm mạnh khi chuẩn hoá, nhưng không biến mất.

::hinh:: paper/figures/hinh5_phan-bo-L.png | Phân phối mất mát chuyển giao L theo từng máy đích; hộp là khoảng tứ phân vị, râu là phân vị 5 và 95 | 16

Hình 5 bổ sung độ phân tán mà các trung vị ở Hình 4 che đi. Ở chiều từ Alibaba sang Bitbrains với dữ liệu thô, một phần tư số máy có L trên 4, tức việc dùng lại không chỉ tệ trung bình mà tệ trên diện rộng. Ở hai cặp máy ảo, gần như toàn bộ hộp nằm sát đường L = 1.

Để kiểm tra liệu riêng hiệu ứng tổng hợp có tạo ra bất đối xứng hay không, nhóm chạy thêm một thí nghiệm *“máy giả”*. Mỗi máy giả là trung bình của 5 máy ảo E1 chọn ngẫu nhiên. 73 máy giả được đặt cạnh 368 máy ảo E1 khác, không chung máy nào. Kết quả với N1 chưa cho phép kết luận: chiều từ máy giả sang máy ảo tốn hơn ở 8/15 phép so, chiều ngược lại ở 6/15 phép so, và hướng phụ thuộc loại mô hình (hai mô hình tuyến tính cho một hướng, các mô hình còn lại cho hướng kia). Tính trên phần huấn luyện, máy giả mượt hơn cả E3 (tự tương quan bậc 1 là 0,91 so với 0,85) nhưng không có chu kỳ ngày (tự tương quan ở 24 giờ là 0,03 so với 0,46). Điều đó cho thấy máy vật lý Alibaba khác *“máy ảo gộp lại”* không chỉ ở độ mượt. Nghiên cứu này vì vậy không gán được bất đối xứng cho riêng hiệu ứng tổng hợp, và cũng không gán được cho riêng khác biệt môi trường.

## Hai lỗi âm thầm của bước chuẩn hoá

### Z-score hỏng khi có máy đứng yên trong giai đoạn huấn luyện

::bang:: Tác động của máy đứng yên lên chế độ N1

| Phép đo | Trước khi xử lý | Sau khi loại máy đứng yên khỏi dữ liệu huấn luyện |
|---|---|---|
| Hồi quy tuyến tính, E3 sang E3, h = 12, MAE trung vị | 42,83 | 6,19 (N0: 6,43) |
| XGBoost, E3 sang E1, h = 12, MAE so với naïve | 60,6 lần | 1,59 lần |
| Trung vị L của E3 sang E1 và E3 sang E2, gộp các tầm | 2,77 và 3,79 | 1,33 và 1,23 |

*Nguyên nhân.* Mười máy E3, chiếm 2% quần thể, có CPU trung bình 0,00% trong toàn bộ phần huấn luyện rồi mới bắt đầu chạy ở phần Validation. Độ lệch chuẩn huấn luyện của chúng nhỏ tới 0,003, nên z-score ở phần Validation, vốn vẫn dùng để huấn luyện mô hình cuối, lên tới 30.196. Vài trăm điểm cực trị này kéo lệch mô hình chung và làm hỏng dự đoán cho mọi máy, như Bảng 5 cho thấy.

*Vì sao khó phát hiện.* Cả ba tính chất toán học ở mục III.F vẫn đúng: thống kê chuẩn hoá được tính đúng như định nghĩa, cái sai nằm ở chính việc áp định nghĩa đó cho một máy đứng yên.

*Cách khắc phục.* Theo bất đẳng thức Samuelson [19], trong một mẫu n điểm, không điểm nào có |z| vượt quá (n−1)/√n. Một điểm vượt giới hạn này mang giá trị mà chính phần huấn luyện không thể sinh ra. Nhóm dùng giới hạn đó làm luật: máy nào có điểm vượt giới hạn thì không được dùng để huấn luyện ở N1, nhưng vẫn được chấm như mọi máy khác. Luật không có tham số tự chọn, được áp đồng đều cho mọi môi trường, và loại 2, 1 và 10 máy ở E1, E2 và E3. Mọi con số N1 trong bài dùng bản đã xử lý.

### Giá trị cần dự đoán của N2 bị lệch ở tầm dự báo dài

*Nguyên nhân.* Theo định nghĩa ở Bảng 2, N2 dự đoán Δ = y(t+h) − y(t), rồi đưa về thang gốc bằng ŷ = y(t) + Δ̂. Bản hiện thực ban đầu biến đổi chuỗi thành sai phân một bước trước, rồi lấy giá trị tại t+h của chuỗi đã biến đổi. Giá trị cần dự đoán vì thế thành y(t+h) − y(t+h−1), chỉ là một bước thay đổi thay vì h bước. Ở h = 1 hai cách trùng nhau, nhưng ở h = 6 và 12, mọi mô hình N2 bị kéo về gần dự báo naïve.

*Vì sao khó phát hiện.* Tính chất *“Δ̂ = 0 cho lại dự báo naïve”* đúng với cả cách đúng lẫn cách sai, nên phép kiểm dựa trên tính chất này không phân biệt được hai cách.

*Cách phát hiện và khắc phục.* Lỗi lộ ra khi nhóm viết lại công thức cho bài báo và đối chiếu với tài liệu gốc. Nhóm bổ sung phép kiểm so trực tiếp giá trị cần dự đoán với chuỗi CPU gốc, xác nhận phép kiểm này bắt được cách sai, rồi chạy lại toàn bộ phần N2 ở h = 6 và 12. Mọi con số N2 trong bài là bản đã sửa.

*Hậu quả nếu không phát hiện.* Trên máy vật lý, mô hình N2 bản sai dính sát dự báo naïve (tỉ số 1,00 và 1,01), còn bản đúng tốt hơn naïve từ 7% đến 13%. Bản sai còn cho mất mát chuyển giao từ Alibaba sang Bitbrains ở N2 chỉ khoảng 1,10, khiến N2 trông như cách tốt nhất, trong khi bản đúng là từ 1,62 đến 1,83, kém hơn N1. Tức một lỗi hiện thực đã đảo kết luận về cách chuẩn hoá nên dùng.

Bài học chung của hai lỗi là một phép kiểm chỉ có giá trị nếu nó báo sai khi hiện thực sai. Với mọi phép biến đổi giá trị cần dự đoán, nên so trực tiếp với dữ liệu gốc, thay vì chỉ kiểm những tính chất mà cả bản đúng lẫn bản sai cùng thoả mãn.

## Nghiên cứu này giúp gì cho thực tế

Kết quả trả lời bốn câu hỏi mà người vận hành trung tâm dữ liệu thường gặp:

- *“Có nên dùng học máy để dự đoán tải máy ảo trong vài phút tới không?”* Với dữ liệu kiểu Bitbrains thì gần như không: dự báo naïve, vốn không cần huấn luyện gì, đã tốt ngang hoặc tốt hơn. Mọi mô hình mới nên được đặt cạnh dự báo naïve trước khi triển khai.
- *“Với máy chủ vật lý thì sao?”* Học máy đáng dùng, tốt hơn dự báo naïve khoảng từ 6% đến 16%, vì tải của máy chủ vật lý mượt hơn và lặp lại theo ngày.
- *“Mô hình đã học ở cụm máy này có dùng cho cụm khác được không?”* Nếu hai cụm cùng nhà cung cấp và cùng loại máy thì được: với dữ liệu thô hoặc z-score, sai số chỉ tăng không quá 8%, nên cụm mới có thể dùng ngay mô hình có sẵn. Nếu khác loại máy, như máy chủ vật lý sang máy ảo, phải đưa dữ liệu của từng máy về cùng thang đo trước. Kể cả khi đó sai số vẫn tăng từ 10% đến 44%, nên cần cân nhắc huấn luyện lại.
- *“Cần cẩn thận gì khi chuẩn bị dữ liệu?”* Hãy kiểm tra riêng những máy vừa được bật lên sau một thời gian gần như tắt. Chỉ 2% số máy như vậy đã đủ làm hỏng mô hình chung của cả môi trường.

# Kết luận và hướng phát triển

## Kết luận

Nghiên cứu này kiểm chứng hai điều thường được coi là hiển nhiên khi dùng học máy dự đoán tải CPU trên đám mây: mô hình học máy luôn tốt hơn cách đoán đơn giản, và mô hình học ở đâu cũng dùng được ở chỗ khác. Trên dữ liệu thật của 1.535 máy từ Bitbrains và Alibaba, cả hai điều đều không đúng một cách chung chung, mà phụ thuộc vào loại máy.

Ba kết luận chính đã được kiểm định:

1. Với máy ảo, dự báo naïve gần như không bị vượt qua ở tầm từ 5 đến 60 phút, với các mô hình và khoảng tìm kiếm siêu tham số đã dùng. Học máy chỉ thắng rõ ràng với máy chủ vật lý, một phần vì tải của máy chủ vật lý là tổng của nhiều tải nhỏ nên mượt hơn.
2. Mô hình dùng lại được giữa hai nhóm máy ảo cùng nhà cung cấp, sai số chỉ tăng không quá 8%.
3. Mô hình học trên máy chủ vật lý đem sang máy ảo kém đi từ 2,2 đến 3,4 lần, chủ yếu vì hai loại máy có thang tải rất khác nhau. Đưa dữ liệu từng máy về cùng thang đo giảm mức kém đi còn từ 1,10 đến 1,44 lần. Đây là cách tốt nhất trong ba cách đã thử, tốt hơn cách chỉ dự đoán mức thay đổi (từ 1,43 đến 1,83 lần). Chiều ngược lại, từ máy ảo sang máy chủ vật lý, gần như luôn dễ hơn.

Giá trị của nghiên cứu nằm ở hai phía. Với người vận hành, kết quả cho biết khi nào học máy đáng đầu tư và khi nào dùng lại mô hình là an toàn. Với người nghiên cứu, bài báo đưa ra một cách đo khả năng dùng lại mô hình tách được ảnh hưởng của thang đo, cùng hai lỗi dễ mắc khi xử lý dữ liệu và cách phát hiện chúng.

## Hạn chế

- Đơn vị quan sát lệch giữa Bitbrains (máy ảo) và Alibaba (máy vật lý). Đây là yếu tố gây nhiễu lớn nhất và không gỡ được bằng dữ liệu hiện có. Bảng sử dụng container của Alibaba có dung lượng hàng trăm GB và cũng không tương đương máy ảo.
- Cửa sổ 8 ngày và mẫu 500 máy của Alibaba giới hạn tính tổng quát. Bộ lọc loại khoảng 40% chuỗi máy ảo có tải thấp, nên kết luận chỉ áp dụng cho quần thể đã lọc.
- Siêu tham số chọn được nằm ở biên của khoảng tìm kiếm, Random Forest chỉ 50 cây, SVR chỉ học trên mẫu con. Siêu tham số chọn ở N0 được dùng lại cho N1 và N2.
- Chế độ N1 dùng lịch sử huấn luyện của máy đích, nên chưa phải trường hợp hoàn toàn không có dữ liệu đích.
- Kết quả N1 phụ thuộc cách xử lý máy đứng yên. Bản trước và sau khi xử lý đều được nêu ở Bảng 5.
- Với vài trăm máy mỗi phép so, những khác biệt rất nhỏ vẫn có ý nghĩa thống kê. Vì vậy mọi kết luận được đọc kèm độ lớn L.
- Mốc thời gian của Alibaba là tương đối, nên đặc trưng ngày trong tuần không mang nghĩa lịch thật.

## Hướng phát triển

Hướng thứ nhất là thay đơn vị quan sát cho đồng nhất: tìm bộ dữ liệu có cả máy ảo lẫn máy vật lý trong cùng một trung tâm dữ liệu, để tách hiệu ứng tổng hợp khỏi khác biệt môi trường. Hướng thứ hai là mở rộng khoảng tìm kiếm siêu tham số và thêm các mô hình chuỗi thời gian học sâu, nhưng luôn đặt cạnh dự báo naïve. Hướng thứ ba là chuyển từ đánh giá sai số sang đánh giá theo quyết định cấp phát, ví dụ số lần thiếu tài nguyên.

# Lời cảm ơn

Nhóm tác giả trân trọng cảm ơn các tác giả của những công trình được trích dẫn trong bài, vì các phương pháp và kết quả của họ là nền tảng để nhóm thực hiện nghiên cứu này. Nhóm cũng cảm ơn Bitbrains IT Services Inc., Grid Workloads Archive và Alibaba đã công bố bộ dữ liệu phục vụ cộng đồng nghiên cứu. Nghiên cứu này không nhận tài trợ.

# Tài liệu tham khảo

::tltk:: [1]  R. N. Calheiros, E. Masoumi, R. Ranjan, R. Buyya (2015), "Workload prediction using ARIMA model and its impact on cloud applications' QoS," IEEE Transactions on Cloud Computing, vol. 3, no. 4, pp. 449–458.
::tltk:: [2]  J. Kumar, A. K. Singh (2018), "Workload prediction in cloud using artificial neural network and adaptive differential evolution," Future Generation Computer Systems, vol. 81, pp. 41–52.
::tltk:: [3]  M. Masdari, A. Khoshnevis (2020), "A survey and classification of the workload forecasting methods in cloud computing," Cluster Computing, vol. 23, pp. 2399–2424.
::tltk:: [4]  S. Makridakis, E. Spiliotis, V. Assimakopoulos (2018), "Statistical and Machine Learning forecasting methods: Concerns and ways forward," PLoS ONE, vol. 13, no. 3, e0194889.
::tltk:: [5]  R. J. Hyndman, A. B. Koehler (2006), "Another look at measures of forecast accuracy," International Journal of Forecasting, vol. 22, no. 4, pp. 679–688.
::tltk:: [6]  S. Kaufman, S. Rosset, C. Perlich, O. Stitelman (2012), "Leakage in data mining: Formulation, detection, and avoidance," ACM Transactions on Knowledge Discovery from Data, vol. 6, no. 4, pp. 1–21.
::tltk:: [7]  L. J. Tashman (2000), "Out-of-sample tests of forecasting accuracy: an analysis and review," International Journal of Forecasting, vol. 16, no. 4, pp. 437–450.
::tltk:: [8]  S. Shen, V. van Beek, A. Iosup (2015), "Statistical Characterization of Business-Critical Workloads Hosted in Cloud Datacenters," trong 15th IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing (CCGrid), Shenzhen, China, pp. 465–474.
::tltk:: [9]  J. Guo, Z. Chang, S. Wang, H. Ding, Y. Feng, L. Mao, Y. Bao (2019), "Who Limits the Resource Efficiency of My Datacenter: An Analysis of Alibaba Datacenter Traces," trong IEEE/ACM 27th International Symposium on Quality of Service (IWQoS), Phoenix, USA, pp. 1–10.
::tltk:: [10]  R. J. Hyndman, G. Athanasopoulos (2021), Forecasting: Principles and Practice, 3rd ed., OTexts, Melbourne, Australia.
::tltk:: [11]  L. Breiman (2001), "Random Forests," Machine Learning, vol. 45, no. 1, pp. 5–32.
::tltk:: [12]  T. Chen, C. Guestrin (2016), "XGBoost: A Scalable Tree Boosting System," trong Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp. 785–794.
::tltk:: [13]  H. Drucker, C. J. C. Burges, L. Kaufman, A. Smola, V. Vapnik (1997), "Support Vector Regression Machines," trong Advances in Neural Information Processing Systems 9, pp. 155–161.
::tltk:: [14]  F. Pedregosa và cộng sự (2011), "Scikit-learn: Machine Learning in Python," Journal of Machine Learning Research, vol. 12, pp. 2825–2830.
::tltk:: [15]  F. Wilcoxon (1945), "Individual comparisons by ranking methods," Biometrics Bulletin, vol. 1, no. 6, pp. 80–83.
::tltk:: [16]  S. Holm (1979), "A simple sequentially rejective multiple test procedure," Scandinavian Journal of Statistics, vol. 6, no. 2, pp. 65–70.
::tltk:: [17]  J. Han, M. Kamber, J. Pei (2011), Data Mining: Concepts and Techniques, 3rd ed., Morgan Kaufmann, Waltham, USA.
::tltk:: [18]  H. B. Mann, D. R. Whitney (1947), "On a test of whether one of two random variables is stochastically larger than the other," Annals of Mathematical Statistics, vol. 18, no. 1, pp. 50–60.
::tltk:: [19]  P. A. Samuelson (1968), "How Deviant Can You Be?," Journal of the American Statistical Association, vol. 63, no. 324, pp. 1522–1525.

::trang-moi::

::en-tieu-de:: MACHINE LEARNING FOR CLOUD CPU LOAD PREDICTION: WHEN DOES IT BEAT NAÏVE FORECASTING, AND CAN IT BE REUSED IN ANOTHER DATACENTER?

::en-tac-gia:: Tran Hoang Dat*, Tran Hoang Phat, Luong Tran Ngoc Khiet

::abstract:: ABSTRACT— Datacenters need to know how busy their servers are about to become, so that resources can be added or released in time: too little means slow services, too much wastes power and money. Machine learning is widely used for this prediction, yet two important points are rarely verified. First, does a machine learning model really predict better than the simplest rule, which assumes the next few minutes will look exactly like now and is known as naïve forecasting? Second, can a model trained in one datacenter be reused in another? We test both on real data from 1,535 machines of two providers, Bitbrains (virtual machines) and Alibaba (physical servers), using five common machine learning models to predict 5, 30 and 60 minutes ahead. Every comparison is made machine by machine and checked statistically, so that conclusions do not depend on chance. For virtual machines, naïve forecasting is almost never beaten by any machine learning model. Only for physical servers does machine learning clearly win. A model trained on one group of virtual machines works on another group from the same provider with at most 8% more error. In contrast, a model trained on Alibaba servers performs 2.2 to 3.4 times worse on Bitbrains virtual machines. Bringing each machine's data to a common scale before prediction reduces this loss to between 10% and 44%. We also point out two easy-to-make data preparation mistakes for this task and how to avoid them. The results help operators decide when machine learning is worth the investment, when naïve forecasting is enough, and how far a model can be reused elsewhere.

::keywords:: Keywords— CPU load prediction, cloud computing, naïve forecasting, machine learning, model reuse across datacenters

::tieu-su:: Trần Hoàng Đạt là sinh viên năm thứ tư của Trường Đại học Sư phạm TP.HCM vào thời điểm đăng bài báo này. Hiện đang quan tâm về các nghiên cứu trong lĩnh vực học máy ứng dụng, dự đoán chuỗi thời gian và phân tích dữ liệu.

::tieu-su:: Trần Hoàng Phát là sinh viên năm thứ tư của Trường Đại học Sư phạm TP.HCM vào thời điểm đăng bài báo này. Hướng nghiên cứu hiện tại tập trung vào tự động hóa quy trình nghiệp vụ và các ứng dụng trên nền tảng đám mây.

::tieu-su:: Lương Trần Ngọc Khiết nhận bằng Cử nhân Công nghệ phần mềm năm 2016 và Thạc sĩ Khoa học máy tính năm 2019 tại Trường Đại học Sư phạm TP. Hồ Chí Minh. Hiện ông là giảng viên tại Khoa Công nghệ thông tin, Trường Đại học Sư phạm TP. Hồ Chí Minh. Hướng nghiên cứu chính: Trí tuệ nhân tạo, phân tích dữ liệu và các ứng dụng công nghệ giáo dục.
