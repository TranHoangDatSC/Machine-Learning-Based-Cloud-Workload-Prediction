# 2026-09-05 — Đối chiếu hai nghiên cứu cũ, viết tài liệu bắc cầu

**Người thực hiện:** A
**Giai đoạn:** GĐ0
**Thời lượng:** ~2 giờ

## Mục tiêu phiên
Đọc hai nghiên cứu trước của A (bài HJS về ví điện tử, báo cáo đồ án về gian lận
thẻ), viết tài liệu nối kiến thức ML sẵn có sang bài toán hiện tại — kèm chỉ rõ chỗ
phép loại suy gãy.

## Đã làm
- Trích xuất và đọc toàn văn `8.Xaydungmohinh.pdf` (18 trang) và
  `FinalReport-CCFraudD.docx`
- Viết `docs/tu-bai-cu-den-bai-nay.md`
- Bổ sung mục 6b vào `giai-thich-chuan-hoa.md`, nối sang Bảng 6 bài HJS
- Thêm danh mục tài liệu vào README mục 7, thêm lộ trình đọc cho B

## Phát hiện

**Bảng 6 của bài HJS chứa đúng cái bẫy mà protocol mục 14 đang chặn.** Bảng so AUC
0,9160 của nhóm với 0,830 / 0,845 / 0,784 của Gillespie rồi kết luận "vượt trội đáng
kể". Nhưng:

- Con số của nhóm đo **trên toàn bộ giao dịch**; ba con số kia đo **trên 1000 giao
  dịch bất thường nhất** — hai tập đánh giá khác nhau, tức hai bài toán khác nhau
- Tập thử nghiệm 30% so với 20%
- Cột S. Ounacer còn khác cả bộ dữ liệu: CCFD 284.807 dòng thật, so với Paysim
  6.362.621 dòng mô phỏng
- Câu "AUC cao hơn với ít dữ liệu huấn luyện hơn chứng minh siêu tham số tối ưu" là
  suy luận nhân quả rút từ một so sánh không kiểm soát

Cấu trúc lỗi giống hệt cái bẫy ở RQ3: con số trông như đang đo chất lượng model,
thực chất đang đo sự khác nhau của điều kiện đo. Đây là chất liệu giảng tốt hơn bất
kỳ ví dụ giả định nào, vì A đã tự trải qua.

**Báo cáo đồ án có hai quan sát rời nhau chưa được nối.** Bài ghi F1 = 0,9912 ở phần
kết quả, và ghi "hơn 95% trường hợp gian lận đều dẫn đến cạn kiệt tài khoản gửi tiền"
ở phần hạn chế. Nối lại thì thấy: Paysim sinh gian lận bằng quy tắc rút cạn tài khoản,
nên `isOrigEmptyAfterTx` gần như là nhãn viết lại. Con số 0,9912 phần lớn đo năng lực
học thuộc quy tắc của trình mô phỏng. Báo cáo nhận ra ở tầng hiện tượng nhưng chưa
chỉ ra cơ chế.

**Naïve Bayes trong Bảng 3 là ví dụ dạy chỉ số tốt nhất.** AUC 0,9567 nghe rất khá,
nhưng F1 = 0,0066 và báo nhầm 493.089 ca. Cùng một model, hai chỉ số, hai kết luận
trái ngược — vì AUC đo xếp hạng ở mọi ngưỡng còn F1 đo một điểm vận hành. Dùng để
giải thích vì sao bài này lấy MASE làm chỉ số chính.

**Cả hai bài cũ đều thiếu baseline tầm thường.** Với Paysim, quy tắc một dòng "cảnh
báo mọi TRANSFER/CASH_OUT làm cạn tài khoản" nhiều khả năng đạt recall rất cao. Không
có mốc đó thì 0,9912 không có nghĩa.

## Quyết định
Không mở mục mới trong `decisions.md` — phiên này không đổi giao thức, chỉ bổ sung
tài liệu giải thích.

Có thêm một ràng buộc mềm cho lúc viết paper: phần so sánh với nghiên cứu khác phải
ghi rõ điều kiện đo, và không phát biểu "vượt trội" khi giao thức khác nhau. Đã viết
vào `tu-bai-cu-den-bai-nay.md` mục 7.

## Vướng mắc
Không.

## Việc tiếp theo
- [ ] B đọc `tu-bai-cu-den-bai-nay.md` trước khi đọc protocol
- [ ] A giảng mục 14, dùng Bảng 6 làm ví dụ dẫn nhập

## File sinh ra
- `docs/tu-bai-cu-den-bai-nay.md`
- Cập nhật `docs/giai-thich-chuan-hoa.md` (mục 6b), `docs/research-plan.md`, `README.md`
