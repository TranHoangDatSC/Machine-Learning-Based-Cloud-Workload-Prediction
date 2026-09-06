# 2026-09-06 — B hoàn thành Giai đoạn 0 và sát hạch Mục 14

**Người thực hiện:** B (Implementation & Experiment)
**Giai đoạn:** GĐ0
**Thời lượng:** ~2 giờ

## Mục tiêu phiên
Hoàn thành toàn bộ checklist của Người B trong Giai đoạn 0:
1. Đọc và thông suốt các tài liệu nền tảng: `tu-bai-cu-den-bai-nay.md`, `protocol.md`, `giai-thich-chuan-hoa.md`, `data-card.md`.
2. Diễn giải lại giao thức nghiên cứu bằng lời của B, đặc biệt là bản chất của Mục 14 (3 chế độ chuẩn hoá).
3. Trả lời chính xác 4 câu hỏi kiểm tra ở mục 6 của `giai-thich-chuan-hoa.md` để vượt qua cổng kiểm tra GĐ0.
4. Chuẩn bị môi trường thực thi theo `requirements.txt`.

---

## Tóm tắt giao thức bằng lời của B

1. **Bài toán và Target:**
   - Dự đoán mức sử dụng CPU (`CPU%`, thang 0–100) của từng đơn vị tính toán (VM hoặc máy vật lý) trên lưới thời gian chuẩn hoá 5 phút (300 giây).
   - Target chung trên cả 3 môi trường: E1/E2 (`CPU usage [%]`), E3 (`cpu_util_percent`). Tuyệt đối không dùng MHz vì phụ thuộc xung nhịp phần cứng.

2. **Quy tắc chia dữ liệu và Tránh rò rỉ (Lookahead Bias):**
   - Phân chia theo trục thời gian: 70% train / 15% val / 15% test. **Tuyệt đối không shuffle.**
   - Mọi đặc trưng rolling (mean, std, min, max) phải áp dụng `.shift(1)` — chỉ nhìn vào quá khứ, không được bao gồm điểm hiện tại $t$.
   - Các tham số chuẩn hoá ($\mu, \sigma$) trong N1 chỉ được tính trên cửa sổ train của chính chuỗi đó.

3. **Luật chơi về Baseline và Đánh giá:**
   - Luôn chạy các Baseline trước tiên (Naive persistence $\hat{y}_{t+h} = y_t$, Moving Average window 6, Seasonal Naive $y_{t-288}$).
   - Mọi kết quả ML đều phải đối chiếu với Naive persistence thông qua chỉ số **MASE** làm thước đo chính giữa các môi trường. Tuyệt đối không dùng MAPE do mẫu số tiệm cận 0 trên Bitbrains.

4. **Trọng tâm nghiên cứu — Mục 14 (Ba chế độ chuẩn hoá):**
   - Lệch mức tải cơ bản giữa Bitbrains (~11%) và Alibaba (~38%) là sự thật hiển nhiên. Transfer thô (N0) chắc chắn thất bại vì lệch load level (~63,4% sai số), không phản ánh năng lực model.
   - N1 (z-score per-series) và N2 (sai phân) bóc tách mức tải cơ bản để trả lời câu hỏi cốt lõi: **Liệu động lực học (dynamics - xu hướng biến thiên, tính chu kỳ) của workload có transfer được giữa các đám mây khác nhau hay không?**
   - Mọi dự đoán sau khi infer bắt buộc phải map ngược về thang đo CPU% gốc trước khi tính chỉ số đánh giá.

---

## Trả lời 4 câu hỏi kiểm tra hiểu bài (Mục 6 `docs/giai-thich-chuan-hoa.md`)

### Câu 1: Vì sao con số MAE 28,64 khi transfer E1 sang E3 lại không chứng minh được rằng model kém?
* **Trả lời:** Vì con số MAE = 28,64 đạt được bởi **một hằng số** (bằng mức tải trung bình của E1 = 11,26%) áp thẳng lên E3 mà không cần bất kỳ mô hình, đặc trưng hay quá trình huấn luyện nào. Do một hằng số cũng đạt được sai số quanh 28, nên nếu model ML transfer thô cho MAE ≈ 28 thì điều đó chỉ chứng minh hai môi trường lệch mức tải cơ bản (load level), chứ hoàn toàn không phản ánh việc model có học được quy luật biến động (dynamics) hay không.

### Câu 2: Trong 28,64 đó, bao nhiêu phần trăm chỉ là chênh lệch mức tải? Con số này lấy ở đâu ra?
* **Trả lời:** Chiếm **63,4%** (tương đương **18,16 điểm MAE**). Con số này lấy từ so sánh thực nghiệm giữa dòng (a) và (b) ở mục 2 `docs/giai-thich-chuan-hoa.md`:
  - Hằng số mức tải TB của E1 áp lên E3: $\text{MAE} = 28,64$.
  - Hằng số mức tải TB của chính E3 áp lên E3: $\text{MAE} = 10,48$.
  - Khi đổi mức tải từ E1 sang đúng E3 (triệt tiêu chênh lệch mức tải), sai số giảm $28,64 - 10,48 = 18,16$ điểm. Tỷ lệ đóng góp của chênh lệch mức tải là: $18,16 / 28,64 \approx 63,4\%$. Còn lại $36,6\%$ (10,48 điểm) là biến thiên nội tại của chuỗi E3.

### Câu 3: Vì sao naive persistence cho kết quả giống hệt nhau ở N0 và N1? Điều đó dùng để kiểm tra cái gì?
* **Trả lời:** 
  - z-score ($z_t = \frac{y_t - \mu}{\sigma}$) là một phép biến đổi affine tuyến tính. Naive persistence dự đoán $\hat{z}_{t+1} = z_t$. Khi map ngược về thang gốc: $\hat{y}_{t+1} = z_t \cdot \sigma + \mu = y_t$, trùng khớp hoàn toàn với dự đoán ban đầu. Do đó, naive persistence bất biến dưới phép biến đổi z-score.
  - **Mục đích kiểm tra:** Dùng làm **bài kiểm tra đơn vị (unit test)** bắt buộc cho code chuẩn hoá của B (`tests/test_normalize.py`). Nếu chạy Naive persistence ở N0 và N1 (sau khi map ngược) mà kết quả MAE không khớp nhau đến 6 chữ số thập phân, code của B chắc chắn bị sai (quên map ngược, tính $\mu, \sigma$ trên toàn chuỗi gây rò rỉ dữ liệu, hoặc nhầm chuỗi).

### Câu 4: Nếu tính $\mu$ và $\sigma$ trên toàn chuỗi thay vì chỉ phần train thì chuyện gì xảy ra, và làm sao phát hiện?
* **Trả lời:**
  - **Hệ quả:** Gây ra **rò rỉ dữ liệu nghiêm trọng (data leakage / lookahead bias)**. Thông tin của tập validation và test (tương lai) đã bị tuồn vào quá trình chuẩn hoá tập train. Kết quả đo được sẽ đẹp một cách giả tạo, phá huỷ tính hợp lệ của toàn bộ nghiên cứu.
  - **Cách phát hiện:**
    1. Bằng unit test ở Câu 3: kiểm tra xem giá trị chuẩn hoá có thay đổi khi bổ sung dữ liệu ngoài train hay không.
    2. Dấu hiệu thực nghiệm: Ở chế độ N0 (thô), cặp transfer Bitbrains $\rightarrow$ Alibaba bắt buộc phải thất bại nặng nề (MAE quanh 28–36). Nếu thấy N0 không thất bại nặng, chắc chắn đã xảy ra rò rỉ dữ liệu.

---

## Số liệu đối chiếu thẩm định
| Chỉ số | E1 fastStorage | E2 Rnd (2013-8) | E3 Alibaba | Ghi chú |
|---|---|---|---|---|
| Đơn vị | 1.250 VM | 500 VM | 500 máy (mẫu phân tầng) | QĐ-003, QĐ-004 |
| Target p50 | 0,84% | 1,07% | 37,0% | Lệch mức tải rõ rệt |
| Mức tải TB sau lọc | 11,26% | — | 38,54% | Chênh lệch 27,27 điểm |
| Autocorr t-1 (5p) | 0,675 | 0,644 | 0,781 | Dynamics cùng vùng giá trị |

---

## Việc tiếp theo (Bắt đầu Giai đoạn 1)
- [ ] B kích hoạt môi trường và cài đặt `requirements.txt`.
- [ ] Triển khai module đọc dữ liệu: `src/cwp/io/bitbrains.py` và `src/cwp/io/alibaba.py`.
- [ ] Triển khai tiền xử lý: `clean.py`, `resample.py`, `filter.py`.

## File sinh ra
- `research-log/2026-09-06-hoan-thanh-gd0.md` (file này)
- Cập nhật `research-log/INDEX.md`
