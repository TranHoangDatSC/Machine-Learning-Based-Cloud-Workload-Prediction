# Kế hoạch nghiên cứu tổng thể

**Đề tài:** Machine Learning-Based Cloud Workload Prediction — A Comparative Study Across Public Cloud Traces
**Đích nhắm:** đồ án môn học Machine Learning + một paper tạp chí trong nước (HJS, TNU, hoặc tương đương)
**Thời lượng dự kiến:** 12 tuần
**Lập kế hoạch:** 2026-08-30

---

## Phân vai

| Vai | Người | Trách nhiệm | Không làm |
|---|---|---|---|
| **A** | Bạn | Lập kế hoạch, chốt giao thức, review kết quả, quyết định khi B vướng, viết paper | Không viết code sản xuất |
| **B** | Anh trai | Triển khai code, chạy thí nghiệm, ghi nhật ký, báo cáo số liệu | Không tự đổi giao thức |

### Quy tắc phối hợp

1. **B không sửa `docs/protocol.md`.** Thấy giao thức có vấn đề thì ghi vào
   `research-log/` và báo A. A quyết định, ghi vào `docs/decisions.md`, rồi mới sửa
   protocol.
2. **Mỗi phiên làm việc của B kết thúc bằng một file trong `research-log/`.**
   Không có log thì coi như phiên đó chưa xong.
3. **A review ở cuối mỗi giai đoạn**, không review từng commit. Cổng kiểm tra ghi
   trong mục "Điều kiện qua cổng" của từng giai đoạn.
4. **Vướng quá 2 giờ thì dừng và hỏi A.** Không tự xoay sở âm thầm.

---

## Phạm vi đã cắt

Đề tài ở dạng ban đầu không kịp trong 12 tuần. Năm điều chỉnh dưới đây đã được áp
dụng vào `protocol.md`. Chi tiết lý do trong `decisions.md` mục QĐ-003.

| Ban đầu | Sau khi cắt | Tiết kiệm |
|---|---|---|
| Bitbrains Rnd cả 3 tháng | Chỉ `2013-8` | ~2/3 chi phí xử lý E2 |
| Toàn bộ 4.023 máy Alibaba | Mẫu phân tầng 500 máy | ~8 lần thời gian chạy |
| Có LSTM/GRU trong scope | Đưa ra ngoài scope chính | ~2 tuần |
| 3 thí nghiệm A, B, C | 2 thí nghiệm A, B | Bỏ phần trùng lặp |
| Horizon tuỳ ý | Cố định 1, 6, 12 | Giới hạn tổ hợp |

Dữ liệu bị cắt vẫn nằm nguyên trên đĩa. Nếu xong sớm thì đưa vào phần kiểm tra tính
vững.

---

## Rủi ro đã nhận diện

| Rủi ro | Xác suất | Ảnh hưởng | Cách chặn |
|---|---|---|---|
| Naive baseline thắng mọi model ML | Trung bình | Cao | Vẫn là kết quả hợp lệ. Chuyển trọng tâm sang phân tích *khi nào* ML thắng, theo horizon và theo độ burstiness |
| Transfer thô thất bại tầm thường | **Cao** | **Rất cao** | Đã chặn bằng ba chế độ chuẩn hoá N0/N1/N2 trong protocol mục 14 |
| Lệch đơn vị quan sát VM và máy vật lý | Chắc chắn | Trung bình | **A đã chấp nhận, thu hẹp phạm vi đề tài.** Nêu ở cả Results lẫn Limitations. Phương án `container_usage` chỉ kích hoạt theo 3 điều kiện ở QĐ-004, và không kích hoạt sau tuần 9 |
| Xử lý 9 GB quá chậm | Thấp | Trung bình | Sau resample chỉ còn khoảng 9 triệu dòng. Đọc theo chunk |
| Tính mới không đủ để đăng | Trung bình | Cao | Đóng góp nằm ở phân rã mức tải và động lực học, không nằm ở việc so model |
| B và A hiểu khác nhau về giao thức | Trung bình | Cao | Cổng kiểm tra cuối GĐ0 buộc B diễn giải lại protocol bằng lời của mình |

---

## Giai đoạn 0 — Chốt nền tảng
**Tuần 1 · Chủ trì: A**

Không có model nào ở giai đoạn này. Đây là giai đoạn quyết định paper có bảo vệ được
hay không.

**A:**
- [x] Thẩm định ba nguồn dữ liệu
- [x] Đo phân phối target, phát hiện lệch mức tải
- [x] Cắt scope, ghi vào `decisions.md`
- [x] Viết `protocol.md`
- [x] Dựng cấu trúc thư mục và quy ước `research-log/`
- [x] Viết `data-card.md`
- [x] Đối chiếu nguồn và trích dẫn, xác nhận đúng
- [x] Chốt QĐ-004: chấp nhận lệch đơn vị quan sát, thu hẹp phạm vi
- [x] Soạn tài liệu giảng mục 14: `docs/giai-thich-chuan-hoa.md`
- [ ] Giao protocol cho B, giảng mục 14 bằng tài liệu trên

**B:**
- [ ] Đọc toàn bộ `protocol.md`
- [ ] Cài môi trường theo `requirements.txt`, xác nhận chạy được
- [ ] Đọc `data/raw/*/explain.md` của cả ba môi trường
- [ ] Viết một log tóm tắt lại giao thức **bằng lời của mình**, đặc biệt là mục 14
- [ ] Trả lời 4 câu hỏi kiểm tra ở `docs/giai-thich-chuan-hoa.md` mục 6

**Điều kiện qua cổng:** B giải thích được vì sao cần ba chế độ chuẩn hoá mà không
cần mở lại tài liệu. Nếu chưa thì A giảng lại — đây là phần dễ hiểu sai nhất và
cũng là phần quyết định giá trị bài.

---

## Giai đoạn 1 — Nạp và chuẩn hoá dữ liệu
**Tuần 2–3 · Chủ trì: B**

Tốn thời gian nhất, ít được ghi nhận nhất. Làm chắc ở đây thì mọi thứ sau đều trôi.

**B:**
- [ ] `src/cwp/io/bitbrains.py` — parser `;\t`, timestamp là **giây** không phải mili-giây
- [ ] `src/cwp/io/alibaba.py` — đọc chunk, không header, chỉ lấy 3 cột cần
- [ ] `src/cwp/preprocess/clean.py` — clip `[0, 100]`, mask sentinel
- [ ] `src/cwp/preprocess/resample.py` — căn lưới 5 phút, bucket rỗng để NaN
- [ ] `src/cwp/preprocess/filter.py` — bốn điều kiện lọc ở protocol mục 6
- [ ] Sinh `data/processed/` dạng parquet
- [ ] Sinh `data/catalog.parquet` — một dòng mỗi chuỗi
- [ ] `tests/test_io.py`, `tests/test_resample.py`
- [ ] Log: bảng số chuỗi vào, bị loại theo từng điều kiện, còn lại

**Bẫy đã biết** — kiểm tra kỹ ba chỗ này:
- Tên file Rnd trùng nhau giữa ba tháng. Phải khoá `(month, vm_id)`.
- `sep=';'` thay vì `sep=';\t'` sẽ để tab lẫn vào tên cột, im lặng và khó phát hiện.
- Alibaba không có header. Quên `names=[...]` sẽ nuốt mất dòng dữ liệu đầu tiên.

**Điều kiện qua cổng:** A đối chiếu bảng thống kê của B với số liệu trong
`research-log/2026-08-30-tham-dinh-du-lieu.md`. Lệch quá 5% thì tìm nguyên nhân
trước khi đi tiếp.

---

## Giai đoạn 2 — Khám phá dữ liệu và bộ đặc trưng
**Tuần 4 · Chủ trì: B, A review**

**B:**
- [ ] Thống kê mô tả từng môi trường, sau khi đã lọc
- [ ] Biểu đồ phân phối target ba môi trường trên cùng một hình
- [ ] ACF/PACF đại diện mỗi môi trường
- [ ] Phân tích burstiness: hệ số biến thiên theo từng chuỗi
- [ ] `src/cwp/features/` — lag, rolling, calendar theo protocol mục 8
- [ ] Kiểm tra rò rỉ: xác nhận không đặc trưng nào chạm vào tương lai

**A:**
- [ ] Duyệt hình, chọn 2–3 hình đưa vào paper
- [ ] Xác nhận bộ đặc trưng khớp protocol

**Điều kiện qua cổng:** có hình phân phối target ba môi trường — đây là hình quan
trọng nhất của paper, nó dựng nền cho toàn bộ lập luận ở RQ3.

---

## Giai đoạn 3 — Thí nghiệm A, trong cùng môi trường
**Tuần 5–6 · Chủ trì: B**

**B:**
- [ ] `src/cwp/models/baselines.py` — naive, moving average, seasonal naive
- [ ] `src/cwp/evaluation/metrics.py` — MAE, RMSE, SMAPE, MASE, R²
- [ ] `src/cwp/evaluation/splits.py` — rolling-origin, khẳng định không shuffle
- [ ] **Chạy baseline trước tiên.** Mọi con số về sau so với nó
- [ ] Linear, Ridge, Random Forest, XGBoost, SVR
- [ ] Ba horizon: 1, 6, 12
- [ ] Mỗi lần chạy sinh một thư mục `runs/`
- [ ] Bảng kết quả vào `results/tables/`

**A:**
- [ ] Kiểm tra: có model nào thua naive không, và ở đâu
- [ ] Kiểm tra: chênh lệch giữa các model có qua Wilcoxon không

**Điều kiện qua cổng:** trả lời được "ML có vượt naive không, ở horizon nào" kèm
kiểm định thống kê. Nếu ML không vượt ở `h=1` thì **đó là finding**, ghi lại và đi
tiếp, không được ép model.

---

## Giai đoạn 4 — Thí nghiệm B, xuyên môi trường
**Tuần 7–9 · Chủ trì: B, A theo sát**

Phần đóng góp mới. Nặng nhất sau GĐ1.

**B:**
- [ ] `src/cwp/preprocess/normalize.py` — ba chế độ N0, N1, N2
- [ ] Xác nhận thống kê N1 **chỉ tính trên cửa sổ train**
- [ ] Chạy 6 cặp transfer x 3 chế độ chuẩn hoá
- [ ] Đưa mọi dự đoán về thang CPU% gốc trước khi tính chỉ số
- [ ] Ma trận transfer vào `results/tables/`

**A:**
- [ ] Kiểm tra rò rỉ trong bước chuẩn hoá — đây là chỗ dễ sai nhất toàn dự án
- [ ] Diễn giải: thành phần nào transfer được, thành phần nào không
- [ ] **Xét điều kiện kích hoạt QĐ-004** ngay khi có bảng kết quả đầu tiên, không
      đợi lúc viết bài. Cụ thể: kết luận RQ3 có đảo chiều khi bỏ E3 ra khỏi bảng
      không? Nếu có thì quyết ngay — còn kịp tải `container_usage` hay phải hạ mức
      tuyên bố. Sau tuần 9 thì chỉ còn lựa chọn hạ mức tuyên bố

**Điều kiện qua cổng:** N0 phải thất bại nặng ở cặp Bitbrains và Alibaba. Nếu N0
không thất bại thì gần như chắc chắn có rò rỉ dữ liệu — dừng lại truy nguyên.

---

## Giai đoạn 5 — Phân tích và viết
**Tuần 10–12 · Chủ trì: A**

**A:**
- [ ] Kiểm định thống kê toàn bộ so sánh
- [ ] Phân tích lỗi: model sai ở đâu, chuỗi nào khó nhất
- [ ] Viết bản thảo
- [ ] Chuẩn bị slide bảo vệ

**B:**
- [ ] Chạy lại toàn bộ từ đầu trên máy sạch, xác nhận tái lập được
- [ ] Kiểm tra mọi số trong paper truy được về một thư mục `runs/`
- [ ] Hình cuối cùng vào `paper/figures/`

**Tuỳ chọn nếu còn thời gian, theo thứ tự ưu tiên:**
- [ ] Kiểm tra tính vững trên Rnd 2013-7 và 2013-9
- [ ] Mở rộng mẫu Alibaba lên 1.000 máy
- [ ] LSTM/GRU

---

## Cấu trúc paper dự kiến

| Mục | Nguồn nội dung |
|---|---|
| 1. Introduction | Bối cảnh dự đoán workload, khoảng trống về cross-environment |
| 2. Related Work | Các nghiên cứu so sánh model, các nghiên cứu transfer |
| 3. Datasets | GĐ1 + `data-card.md` + bảng lọc chuỗi |
| 4. Methodology | `protocol.md` mục 8 đến 15 |
| 5. Results — Within-environment | GĐ3 |
| 6. Results — Cross-environment | GĐ4, phần trọng tâm |
| 7. Discussion | Thành phần nào transfer được và vì sao |
| 8. Limitations | Lệch đơn vị quan sát, chỉ 8 ngày, chỉ CPU |
| 9. Conclusion | |

Đóng góp tuyên bố trong bài:

> This study provides an empirical comparison of CPU-friendly machine-learning models
> for cloud workload prediction across heterogeneous public cloud traces, and shows
> that cross-environment generalization must be assessed after separating workload
> level from workload dynamics — a distinction that reverses the naive conclusion.

Câu thứ hai là phần khiến bài khác với các so sánh model đã có.

---

## Nhịp làm việc

| Việc | Tần suất |
|---|---|
| B ghi `research-log/` | Mỗi phiên |
| B cập nhật `research-log/INDEX.md` | Mỗi phiên |
| A review | Cuối mỗi giai đoạn |
| A và B đồng bộ | Mỗi tuần một lần |
| Cập nhật `decisions.md` | Mỗi khi lệch khỏi protocol |
