# Mục lục nhật ký

Cập nhật thủ công mỗi khi thêm log mới. Mới nhất ở trên.

| Ngày | Phiên | Người | GĐ | Kết quả chính |
|---|---|---|---|---|
| 2026-09-11 | [A nghiệm thu GĐ3, chốt QĐ-015](2026-09-11-nghiem-thu-gd3.md) | A | GĐ3 | **GĐ3 ĐẠT, ĐÓNG.** Lỗi R² `E1_830` nằm ở tham chiếu của A — lần thứ ba B đúng A sai. QĐ-015: đếm 8 model, khai báo lưới, **không nới lưới sau khi đã thấy ML thua** (mục 17). Siêu tham số chốt ở biên trên lưới 7/9 với `rf` và `svr` — hạn chế phải nêu trong paper |
| 2026-09-10 | [GĐ3: bộ máy đánh giá, ba baseline, Thí nghiệm A](2026-09-10-gd3-thi-nghiem-a.md) | B | GĐ3 | Trọn 7 bước, cổng **ĐẠT**, 277 test xanh. 27 số dòng + 27 số MAE khớp tuyệt đối; phá code 5 kiểu đều bị bắt. **RQ1: E1 không model ML nào vượt naive ở bất kỳ horizon nào; E2 chỉ SVR vượt ở h=6/12; E3 ML vượt ở cả ba.** Ở tầng bursty nhất **mọi** model đều thua naive. Ba lỗi tìm được: `E1_830` lọt phép so `ss_tot == 0` (A đã sinh lại tham chiếu), mẫu con SVR chỉ trùng 2,9% giữa các horizon thay vì dùng chung, và hướng Wilcoxon lấy nhầm từ hiệu hai trung vị thay vì trung vị của hiệu — chỗ này **đảo kết luận** ở 8 cặp |
| 2026-09-10 | [Đóng cổng GĐ2, mở cổng GĐ3](gate-gd3.md) | A | GĐ2→3 | **GĐ2 ĐẠT, ĐÓNG.** QĐ-013 chốt 5 quy ước GĐ3, QĐ-014 chốt 5 fold expanding + mẫu con SVR; `reference_gd3.py` neo 27 con số baseline + 27 số dòng. Cổng GĐ3 neo vào baseline vì model không tất định. Công cụ kiểm chạy **ba loại phép kiểm** — chỉ loại A cần tính độc lập, mà GĐ3 độc lập yếu hơn; test của chính công cụ phá 9 kiểu, bắt được cả 9, và tìm ra 3 lỗi trong bản đầu |
| 2026-09-10 | [Chốt QĐ-012, rà soát GĐ2, kiểm sẵn sàng GĐ3](2026-09-10-chot-qd012-va-ra-soat-gd2.md) | B | GĐ2→3 | Phân tầng CV theo phân vị trong từng môi trường; chặn rò rỉ CV trước khi nó xảy ra. **Mục 14 trích số đo trên 833 chuỗi trong khi quần thể chỉ có 498** — đo lại, lập luận mạnh hơn. Seasonal naive thiếu `lag_288` nhưng test vẫn ~100% |
| 2026-09-09 | [Rà soát toàn dự án trước paper](2026-09-09-ra-soat-truoc-paper.md) | B | GĐ2 | Nền móng vững (79.200 ô đặc trưng sai 0), nhưng **data card mô tả quần thể trước lọc** và ghi phương pháp đã bãi bỏ; tiền đề ACF của QĐ-005 đã đổi; clip tạo trần 5,12% ở E1 chưa ai khai báo |
| 2026-09-09 | [GĐ2: module đặc trưng và kiểm rò rỉ](2026-09-09-gd2-dac-trung.md) | B | GĐ2 | Trọn 8 bước. 19 đặc trưng + 51 test; phá code 7 kiểu đều bị bắt. mọi chỉ số đối chiếu được đều khớp bản độc lập của A (42 qua `reference_gd2.json`, 114 vân tay đặc trưng, 9 neo số dòng). Nhịp một giờ có thật; chỉ E3 có chu kỳ ngày; CV bị chặn cứng bởi thang đo. **Chờ A duyệt hình để qua cổng** |
| 2026-09-09 | [Mở cổng GĐ2](2026-09-09-mo-cong-gd2.md) | A | GĐ2 | QĐ-010 + thước đo + checker. `dropna` ≠ luật dòng hợp lệ — E1 khớp kể cả khi làm sai |
| 2026-09-09 | [Bàn giao GĐ1](2026-09-09-ban-giao-gd1.md) | A thay B | GĐ1 | Bảng lọc đầy đủ; **GĐ1 ĐÓNG**. Lệch cuối cùng hoá ra là lỗi đếm của A, không phải của B |
| 2026-09-09 | [A rà soát và sửa code GĐ1](2026-09-09-ra-soat-code-b.md) | A | GĐ1 | Code tự chỉnh mẫu cho khớp `gan_chet==1` — đã xoá. 5 lỗi, **cổng ĐẠT** |
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
