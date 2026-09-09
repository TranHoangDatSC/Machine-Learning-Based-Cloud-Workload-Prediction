# Mục lục nhật ký

Cập nhật thủ công mỗi khi thêm log mới. Mới nhất ở trên.

| Ngày | Phiên | Người | GĐ | Kết quả chính |
|---|---|---|---|---|
| 2026-09-09 | [B chưa áp dụng QĐ-009](2026-09-09-b-chua-ap-dung-qd009.md) | A | GĐ1 | Số E3 không đổi vì code chưa sửa; trùng 146/500 máy — đúng biến thể đã chẩn đoán |
| 2026-09-09 | [QĐ-009 đóng băng mẫu E3](2026-09-09-qd009-dong-bang-e3.md) | A | GĐ1 | A và B chọn hai tập máy khác nhau 89% — đóng băng `config/e3_machines.txt` |
| 2026-09-08 | [Nguồn gốc catalog](2026-09-08-provenance-catalog.md) | A | GĐ1 | **B khớp A tuyệt đối** ở E1/E2; catalog là khảm 2 máy → thêm `built_on`/`built_at` |
| 2026-09-08 | [Schema và kiểm cổng tự động](2026-09-08-schema-va-checker.md) | A | GĐ1 | Đặc tả 13 cột catalog; `check_gd1.py` + test cho chính nó, 4 tình huống xanh |
| 2026-09-08 | [Chốt QĐ-008, mở khoá GĐ1](2026-09-08-chot-qd008.md) | A | GĐ1 | Khảo sát 4 phương án; chọn nội suy ≤2 + lọc theo dòng. K=0 cho cùng số chuỗi |
| 2026-09-08 | [Conda env và chốt GĐ0](2026-09-08-conda-va-chot-gd0.md) | A | GĐ0 | Công cụ không nhận conda env — đã sửa. **GĐ0 ĐÓNG.** QĐ-008 vẫn chặn GĐ1 |
| 2026-09-07 | [Sửa `test_env.py`](2026-09-07-sua-test-env.md) | A | GĐ0 | Công cụ cũ báo 12/12 trên venv hỏng hoàn toàn — chỉ đọc metadata, không import |
| 2026-09-07 | [Dựng thước đo cổng GĐ1](2026-09-07-thuoc-do-cong-gd1.md) | A | GĐ1 | Protocol mục 6 bước 6 phá huỷ 79% E2 và 99% E3 — QĐ-008 chờ duyệt |
| 2026-09-07 | [Chốt ghim môi trường](2026-09-07-ghim-moi-truong.md) | A | GĐ0 | QĐ-007 ghim phiên bản + Python 3.10–3.12; thêm `tests/test_env.py` làm cổng |
| 2026-09-07 | [A review cổng GĐ0](2026-09-07-review-cong-gd0.md) | A | GĐ0 | B xong GĐ0 không phải GĐ1; hiểu bài đạt, môi trường chưa cài (0/12 gói) |
| 2026-09-06 | [B hoàn thành Giai đoạn 0](2026-09-06-hoan-thanh-gd0.md) | B | GĐ0 | Nắm vững mục 14, trả lời 4 câu hỏi sát hạch, chốt checklist sẵn sàng cho GĐ1 |
| 2026-09-05 | [Đối chiếu hai nghiên cứu cũ](2026-09-05-doi-chieu-bai-cu.md) | A | GĐ0 | Bảng 6 bài HJS chứa đúng cái bẫy protocol mục 14 đang chặn |
| 2026-09-05 | [Soạn tài liệu giảng mục 14](2026-09-05-giang-muc-14.md) | A | GĐ0 | Đo được: hằng số cho MAE 28,64 trên E3 — "thảm hoạ transfer" không cần model |
| 2026-08-30 | [Chốt QĐ-004 và xác nhận trích dẫn](2026-08-30-chot-qd004-va-trich-dan.md) | A | GĐ0 | Chấp nhận lệch đơn vị quan sát; đặt 3 điều kiện kích hoạt phương án dự phòng |
| 2026-08-30 | [Thẩm định dữ liệu và tái cấu trúc](2026-08-30-tham-dinh-du-lieu.md) | A | GĐ0 | Xác nhận 3 nguồn; phát hiện lệch mức tải E1/E2 vs E3 |
