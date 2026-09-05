# 2026-08-30 — Chốt QĐ-004 và xác nhận trích dẫn

**Người thực hiện:** A
**Giai đoạn:** GĐ0
**Thời lượng:** ngắn

## Mục tiêu phiên
Đóng hai việc còn treo sau phiên thẩm định dữ liệu.

## Đã làm
- A xác nhận chấp nhận lệch đơn vị quan sát giữa E1/E2 (VM) và E3 (máy vật lý), và
  thu hẹp phạm vi đề tài tương ứng
- A đối chiếu toàn bộ nguồn dữ liệu và hai mục trích dẫn trên trang gốc — đúng
- Chuyển QĐ-004 từ "cần xem lại" sang "đã xác nhận", bổ sung điều kiện kích hoạt
  phương án dự phòng

## Quyết định
- QĐ-004 chuyển sang trạng thái ĐÃ XÁC NHẬN → `docs/decisions.md`
- Phương án bổ sung `container_usage.csv` **không** nằm trong kế hoạch. Chỉ kích hoạt
  khi có ít nhất một trong ba điều kiện, và không kích hoạt sau tuần 9
- Trích dẫn không cần kiểm tra lại → `docs/data-card.md`

## Phát hiện
Lúc viết điều kiện kích hoạt mới thấy "bí quá thì tải thêm" là chỉ dẫn không dùng
được: không ai biết lúc nào là bí. Đã thay bằng ba điều kiện quan sát được, kèm mốc
thời gian chặn.

Phát sinh thêm một ràng buộc về cách viết bài: không được phát biểu "Alibaba dễ dự
đoán hơn Bitbrains", vì câu đó gán chênh lệch cho môi trường trong khi một phần đến
từ hiệu ứng tổng hợp ở mức máy vật lý. Đã ghi vào QĐ-004 và `data-card.md`.

## Vướng mắc
Không.

## Việc tiếp theo
- [ ] A giao protocol cho B, giảng trực tiếp mục 14
- [ ] B hoàn thành checklist GĐ0

## File sinh ra
- Không có file mới. Cập nhật `docs/decisions.md`, `docs/data-card.md`,
  `docs/research-plan.md`
