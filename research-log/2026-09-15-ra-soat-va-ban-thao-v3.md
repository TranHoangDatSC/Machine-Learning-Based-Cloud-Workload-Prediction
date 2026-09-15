# 2026-09-15 — Rà soát toàn dự án, kiểm độc lập QĐ-016, bản thảo v3

**Người thực hiện:** một phiên đóng cả hai vai; một phiên con độc lập viết phép kiểm QĐ-016.
**Giai đoạn:** GĐ5
**Thời lượng:** ~4 giờ (phiên con chạy ~21 phút)

## Mục tiêu phiên

Theo yêu cầu của A:

1. Rà lại toàn bộ dự án trước khi sửa bài.
2. Đối chiếu trích dẫn và tính đúng đắn của chúng; công thức nào dùng của người khác thì ghi nguồn.
3. Viết bài bớt kỹ thuật, tập trung vào đóng góp; bỏ gạch ngang và chữ đậm; trích dẫn câu nói dạng ngoặc kép in nghiêng; không nhắc lưu phiên bản, khai trước hay mã nguồn.
4. Việc tồn: kiểm độc lập B3/B11/B12; hình GĐ3 gốc dùng bảng màu chưa qua kiểm.

## Rà soát

| Phép kiểm | Kết quả |
|---|---|
| `check_data`, `check_gd1` đến `check_gd4`, `check_qd017`, `check_qd018`, `check_qd019` | đều ĐẠT |
| `pytest` | 367 đạt, 1 bỏ qua (chạy lại sau khi sửa hình: vẫn 367 đạt) |
| `scripts/doi_chieu_so_lieu_bai_bao.py` (mới): tính lại 175 con số của bài từ bảng gốc | bản v2: 1 lệch và 2 chỗ chữ sai; bản v3: **0 lệch** |

Ba lỗi số liệu trong bản v2 đã sửa ở v3:

| Chỗ | v2 ghi | Đúng |
|---|---|---|
| Bảng máy đứng yên, L của E3 sang E2 sau khi xử lý | 1,24 | 1,23 (1,2349) |
| E2 sang E1, N0 và N1, tầm 30 và 60 phút | 1,03–1,08 | từ 1,07 đến 1,08 |
| Máy giả N1, chiều đơn lẻ sang gộp tốn hơn | 4/15 | 6/15 (số cũ là trước QĐ-019; Holm cùng họ nên đổi) |

Thêm một chỗ **lời văn không khớp code**: bài v2 ngầm hiểu naïve theo mùa là "cùng giờ hôm trước" của thời điểm cần dự đoán. `src/cwp/models/baselines.py` dùng ŷ(t+h) = y(t−288) cho mọi h, tức cùng giờ hôm trước của thời điểm *t*. v3 ghi đúng công thức này. Không đổi kết quả.

## Kiểm độc lập QĐ-016 (B3, B11, B12 và target)

Phiên con không được đọc `check_gd4.py`, `pha_gd4.py`, `reference_gd4.*`, `check_qd019.py`, `build_qd019.py`, `normalize.py`, `build_features.py`, `src/cwp/features` và `research-log/`; chỉ đọc protocol và các QĐ. Sản phẩm: `scripts/kiem_doc_lap_qd016.py`, chạy trên toàn bộ dữ liệu (36 ma trận).

| Tính chất | Kết quả |
|---|---|
| P1 thống kê N1 lấy trên train [0, 1612), ddof=1; ma trận N1 sinh lại khớp | 12/12 đạt; giải ngược mu, sd từ `lag_1` khớp bảng 735/735, 302/302, 498/498 |
| P2 N2 không bắc cầu qua đầu chuỗi | 18/18 đạt; 0 dòng chạm z[0] |
| P3 cột lịch trùng bit giữa các chế độ | 27/27 đạt |
| P4 target so với chuỗi gốc | N0, N1 18/18 đạt; N2 `features_qd019` 9/9 đạt; **N2 `data/features` h = 6, 12: 6/6 trượt** |
| Tự kiểm đột biến | 33/33 bị bắt |

Chỗ trượt P4 là **đúng lỗi QĐ-019 đã khai** (target cũ y(t+h)−y(t+h−1) trên 100% dòng), bằng chứng độc lập rằng lỗi có thật và bản sửa đúng. Mọi con số N2 h > 1 trong bài đọc từ bảng QĐ-019; `data/features` N2 h > 1 chỉ còn dùng cho cột *"trước khi sửa"*. Vì 6 ô này, script trả mã thoát 1; đó là trạng thái mong đợi, không phải lỗi mới.

Ghi nhận thêm, không ảnh hưởng kết quả: bảng mu và ma trận N1 lệch nhau cỡ vài ULP (lệch tương đối ≤ 3e−14); E3_m_2848 không có dữ liệu sau train nên với chuỗi này thống kê train trùng toàn chuỗi.

## Trích dẫn

Đối chiếu 18 tài liệu v2 qua tìm kiếm: đúng tác giả, năm, nơi đăng, số trang. Sửa ở v3:

- Makridakis và cộng sự [4]: *"hàng nghìn chuỗi"* → 1.045 chuỗi theo tháng.
- Masdari và Khoshnevis [3]: bỏ câu *"phần lớn nghiên cứu đánh giá trên một bộ dữ liệu duy nhất"* vì không kiểm được trong bài gốc.
- Kaufman và cộng sự [6]: bỏ *"nơi rò rỉ dễ xảy ra nhất"*, chỉ giữ định nghĩa rò rỉ.
- Thêm số trang: Shen 465–474; Guo (IWQoS lần 27) 1–10.
- Bỏ Nosek (khai trước) vì bài không còn nói về khai trước.
- Thêm Hyndman và Athanasopoulos (2021), *Forecasting: Principles and Practice*, 3rd ed., cho naïve, naïve theo mùa, sai phân; Han, Kamber, Pei (2011), *Data Mining: Concepts and Techniques*, 3rd ed., cho z-score.
- Công thức và nguồn: MAE [5]; naïve, naïve theo mùa, sai phân [10]; z-score [17]; Wilcoxon [15]; Holm [16]; Mann-Whitney [18]; Samuelson [19]. L ghi rõ là đề xuất của nhóm.

Tổng 19 tài liệu, đánh số theo thứ tự xuất hiện.

## Bản thảo v3

Dựng trên bản v2 mà nhóm tác giả đã sửa trực tiếp trong Word (giữ *naïve*, (1)(2)(3), ngoặc kép cong, Train/Validation/Test). Thay đổi chính:

- Sửa hai chỗ nội dung trong bản nhóm sửa:
  - Đóng góp (1) *"vì có quy luật rõ ràng"* sai: máy ảo gần như không có chu kỳ ngày (0,13). Đúng là tải biến động khó đoán nên giá trị hiện tại đã chứa gần hết thông tin có ích.
  - Nhãn (RQ1)(RQ2)(RQ3) gắn sai ba khoảng trống: khoảng trống 1 ứng câu hỏi 1 và 2, khoảng trống 2 ứng câu hỏi 3, khoảng trống 3 ứng đóng góp 3.
- Bớt kỹ thuật:
  - bỏ bảng 19 đặc trưng và bảng lưới siêu tham số, thay bằng một đoạn văn;
  - bỏ cổng nghiệm thu, bản tính độc lập, cố tình làm hỏng, khai trước, lưu phiên bản, công bố mã nguồn;
  - mục kiểm tra đúng đắn thu còn một đoạn.
- Hình thức:
  - bỏ mọi chữ đậm và gạch ngang trong thân bài (chỉ còn dấu — bắt buộc của template sau TÓM TẮT, Từ khóa, ABSTRACT, Keywords, và gạch nối số trang trong tài liệu tham khảo);
  - khoảng số viết *"từ … đến …"*;
  - RQ đổi thành *"câu hỏi thứ nhất/hai/ba"*.
- Lời cảm ơn: cảm ơn tác giả các công trình được trích dẫn và bên công bố dữ liệu; không tài trợ. Tiểu sử: hai sinh viên năm thứ tư.
- Hình 1 viết lại chữ (Thí nghiệm 1, 2; bỏ *"cổng nghiệm thu"*, *"khai trước"*); nhãn hình 4, 5 bỏ gạch ngang.

Kết quả: `paper/ban-thao-v3.docx`, Word mở được, 12 trang, 5 hình, 5 bảng. Đánh số mục khớp tham chiếu III.F và IV.D. Không đổi con số kết quả nào ngoài ba lỗi ở trên.

## Hình GĐ3 gốc

Bảng màu cũ trượt validator (chroma của `#3a7ca5`, `#5fa8d3`; cặp `#2a9d8f` và `#5fa8d3` ΔE 11,3 < 15). Đổi `scripts/fig_gd3_results.py`:

- năm model ML lấy năm slot đầu của bảng tham chiếu, qua kiểm cặp liền kề (CVD ΔE ≥ 9,1; mắt thường ≥ 19,6);
- ba baseline dùng xám trung tính kèm nét đứt;
- ba môi trường ở hình chạm trần dùng ba slot đầu.

Vẽ lại `results/figures/gd3/`, bảng ghi ra thư mục tạm: `tang_gd3`, `wilcoxon_gd3`, `ml_vs_naive_gd3` **trùng byte** với bảng đã commit, nên bảng gốc không bị ghi đè.

## Việc tiếp theo

- [ ] A đọc `ban-thao-v3.docx`
- [ ] Commit
- [ ] Chọn tạp chí (A hoãn)
