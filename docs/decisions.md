# Nhật ký quyết định

Mỗi quyết định ảnh hưởng đến giao thức hoặc phạm vi đều ghi ở đây. Không xoá mục cũ;
quyết định bị đảo thì thêm mục mới và đánh dấu mục cũ là đã thay thế.

Định dạng: bối cảnh, quyết định, lý do, hệ quả.

---

## QĐ-001 — Loại Google 2019 Borg trace khỏi đề tài
**Ngày:** 2026-08-30 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Kế hoạch ban đầu dùng ba trace, trong đó có Google 2019. File đã tải là
`borg_traces_data.csv`, 405.894 dòng, 34 cột.

**Quyết định.** Loại Google khỏi đề tài. Còn ba môi trường: Bitbrains fastStorage,
Bitbrains Rnd, Alibaba v2018.

**Lý do.** File này là dataset phân loại job failure, không phải chuỗi thời gian:
- Có cột nhãn nhị phân `failed`, phân bố 313.216 / 92.678
- Mỗi dòng là một sự kiện lập lịch, không phải một mốc thời gian
- `time` không sắp xếp tăng dần, và chứa sentinel `9223372036854775807`
- `average_usage` và `maximum_usage` là tổng kết cả vòng đời instance

Muốn có chuỗi thời gian Google 2019 thật thì phải lấy bảng `instance_usage` trên
BigQuery, khoảng 2,4 TiB — vượt xa khả năng đồ án.

**Hệ quả.** Mất một môi trường "khác tổ chức". Bù lại bằng cách tách Bitbrains thành
hai môi trường độc lập, cho hai mức độ khác biệt thay vì một.

---

## QĐ-002 — Thay Alibaba GPU v2020 bằng cluster-trace-v2018
**Ngày:** 2026-08-30 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** File Alibaba ban đầu là `pai_group_tag_table.csv` từ
`cluster-trace-gpu-v2020`.

**Quyết định.** Chuyển sang `cluster-trace-v2018`, bảng `machine_usage.csv`.

**Lý do.** `pai_group_tag_table` chỉ có 5 cột: `inst_id`, `user`, `gpu_type_spec`,
`group`, `workload`. Không timestamp, không resource usage, hai cột gần như rỗng
hoàn toàn. Là bảng metadata gắn tag, không dựng được chuỗi thời gian.

`machine_usage` có `cpu_util_percent` thang 0–100, khớp trực tiếp với
`CPU usage [%]` của Bitbrains, cho một target chung cùng đơn vị và cùng thang đo
giữa cả ba môi trường. Đây là điều kiện tiên quyết của RQ3.

**Hệ quả.** Đơn vị quan sát của E3 là máy vật lý gộp nhiều container, khác với VM
đơn lẻ ở E1 và E2. Xem QĐ-004.

---

## QĐ-003 — Cắt phạm vi để vừa 12 tuần
**Ngày:** 2026-08-30 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Phạm vi trong README ban đầu không kịp trong một học kỳ với hai người.

**Quyết định.** Năm điều chỉnh:

| # | Cắt | Lý do |
|---|---|---|
| 1 | Bitbrains Rnd chỉ dùng `2013-8` | Ba tháng gấp ba chi phí xử lý, lợi ích biên nhỏ. `2013-8` trùng cửa sổ thời gian với fastStorage nên so sánh sạch hơn |
| 2 | Alibaba lấy mẫu phân tầng 500 trên 4.023 máy | 500 chuỗi đã quá đủ cho global model. Giảm khoảng 8 lần thời gian chạy |
| 3 | LSTM/GRU ra khỏi scope chính | Ngốn thời gian nhất, và trên dữ liệu dạng này thường thua XGBoost |
| 4 | Gộp ba thí nghiệm còn hai | "Model comparison" là *trục* bên trong A và B, không phải thí nghiệm riêng. Giữ ba sẽ khiến phần Kết quả lặp lại chính nó |
| 5 | Horizon cố định 1, 6, 12 | Giới hạn số tổ hợp phải chạy |

**Hệ quả.** Dữ liệu bị cắt vẫn nằm nguyên trên đĩa. Nếu xong sớm thì đưa vào phần
kiểm tra tính vững, không cần tải lại gì.

---

## QĐ-004 — Chấp nhận lệch đơn vị quan sát, nêu trong Limitations
**Ngày:** 2026-08-30 · **Người quyết:** A · **Trạng thái:** ĐÃ XÁC NHẬN 2026-08-30
**Xác nhận lại:** A đồng ý chấp nhận lệch và thu hẹp phạm vi đề tài. Phương án dự
phòng chỉ kích hoạt theo điều kiện ở mục "Phương án dự phòng" bên dưới.

**Bối cảnh.** E1 và E2 quan sát ở mức VM đơn lẻ. E3 quan sát ở mức máy vật lý, mỗi
máy gộp nhiều container. Chuỗi của E3 do đó mượt hơn một cách hệ thống — autocorr
bậc 1 đo được là 0,781 so với 0,675 và 0,644.

**Quyết định.** Giữ `machine_usage`, nêu rõ là giới hạn của nghiên cứu.

**Lý do.** Phương án thay thế là tải `container_usage.csv` để có so sánh ngang cấp,
nhưng đó là một tệp lớn nữa và thêm một vòng tiền xử lý. Với ràng buộc 12 tuần thì
không đáng đánh đổi.

**Hệ quả.** Một phần chênh lệch hiệu năng giữa E3 và hai môi trường kia đến từ mức
độ tổng hợp chứ không phải từ bản chất môi trường. Khi diễn giải RQ2 và RQ3 phải nói
rõ điều này, và phải nói ở cả phần Results chứ không chỉ giấu trong Limitations.

**Cách phát biểu trong bài.** Không viết "Alibaba dễ dự đoán hơn Bitbrains". Viết
"chuỗi ở mức máy vật lý của Alibaba dễ dự đoán hơn chuỗi ở mức VM của Bitbrains, một
phần do hiệu ứng tổng hợp". Câu thứ hai đúng; câu thứ nhất là kết luận vượt quá dữ
liệu.

### Phương án dự phòng — chỉ kích hoạt khi có ít nhất một điều kiện

Bổ sung `container_usage.csv` của cùng bản trace v2018 để có so sánh ngang cấp VM.
Đây là phương án tốn kém, **không làm nếu không rơi vào các trường hợp sau**:

| # | Điều kiện kích hoạt | Ai phát hiện |
|---|---|---|
| 1 | Ở GĐ4, kết luận về RQ3 **đảo chiều** tuỳ theo có hay không có E3 trong bảng | B báo, A quyết |
| 2 | Chênh lệch hiệu năng E3 so với E1/E2 lớn tới mức không tách được đâu là hiệu ứng tổng hợp, đâu là bản chất môi trường | A khi review GĐ4 |
| 3 | Giảng viên hướng dẫn hoặc phản biện yêu cầu cụ thể điểm này | A |

**Chi phí nếu kích hoạt:** thêm khoảng 1,5 đến 2 tuần cho tải, tiền xử lý và chạy
lại toàn bộ thí nghiệm có E3. Nếu kích hoạt sau tuần 9 thì **không kịp** — khi đó
chọn cách khác: hạ mức tuyên bố trong bài, chỉ so E1 với E2 ở phần RQ3 chính, và
đưa E3 xuống thành phân tích bổ sung.

**Điểm kiểm tra:** A xem lại điều kiện 1 và 2 ngay khi có bảng kết quả GĐ4 đầu tiên,
không đợi đến lúc viết bài.

---

## QĐ-005 — RQ3 phải tách mức tải khỏi động lực học
**Ngày:** 2026-08-30 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Đo phân phối target cho thấy Bitbrains và Alibaba gần như không giao
nhau: trung vị 0,84 và 1,07 so với 37,0. Tỉ lệ mẫu dưới 1% là 53,4% và 43,2% so với
2,0%.

**Quyết định.** Thí nghiệm B chạy ba chế độ chuẩn hoá N0, N1, N2 như một ablation,
thay vì chỉ chạy transfer thô.

**Lý do.** Transfer thô sẽ cho MAE khoảng 36 và kết luận "generalization thất bại".
Kết luận đó đúng nhưng vô giá trị: nó chỉ đo chênh lệch mức tải trung bình, biết
trước được mà không cần train model nào. Phản biện sẽ đánh vào đúng chỗ này.

Autocorr bậc 1 trên lưới 5 phút của ba môi trường nằm cùng vùng, 0,644 đến 0,781.
Nghĩa là động lực học *có* khả năng so sánh được, chỉ mức tải là lệch. Tách hai
thành phần biến RQ3 từ câu hỏi hiển nhiên thành câu hỏi thật.

**Hệ quả.** Đây trở thành đóng góp chính của paper. Cũng là phần dễ rò rỉ dữ liệu
nhất — thống kê chuẩn hoá N1 bắt buộc chỉ tính trên cửa sổ train.

---

## QĐ-006 — Không dùng MAPE
**Ngày:** 2026-08-30 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** MAPE là chỉ số quen thuộc trong các paper dự đoán workload.

**Quyết định.** Dùng SMAPE và MASE. Không báo cáo MAPE.

**Lý do.** Trên 40% mẫu Bitbrains có CPU% gần 0. Mẫu số của MAPE nổ, giá trị mất ý
nghĩa và không so được giữa các môi trường.

**Hệ quả.** MASE là chỉ số chính khi so sánh giữa các môi trường, vì đã chuẩn hoá
theo độ khó nội tại của từng chuỗi.

---

## QĐ-007 — Ghim đúng phiên bản thư viện, ràng buộc Python 3.10–3.12
**Ngày:** 2026-09-07 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Review cổng GĐ0 phát hiện môi trường của B lệch hoàn toàn so với
`requirements.txt`: 0/12 gói khớp, thiếu hẳn `pyarrow`, `xgboost`, `lightgbm`,
`tqdm`. Thiếu `pyarrow` là chặn cứng, vì sản phẩm chính của GĐ1 là parquet.

Có hai hướng: ghim đúng phiên bản đã khai, hoặc cập nhật `requirements.txt` theo
phiên bản mới hơn đang có sẵn trên máy.

**Quyết định.** Ghim đúng phiên bản đã khai. Không sửa `requirements.txt` theo máy.
Bổ sung ràng buộc **Python 3.10 đến 3.12**.

**Lý do.**

`protocol.md` mục 16 lấy "phiên bản thư viện ghim trong requirements.txt" làm một
trong bốn điều kiện tái lập. Chạy trên phiên bản khác thì cam kết đó rỗng: ba tháng
sau không ai dựng lại được đúng môi trường đã cho ra các con số trong paper.

Ràng buộc Python có trần và sàn cụ thể:
- **Trần 3.12** — scikit-learn 1.5.2 và matplotlib 3.9.2 chưa có wheel cho 3.13.
- **Sàn 3.10** — scipy 1.14.1 đã bỏ Python 3.9.

Linux Mint 21.x có sẵn Python 3.10, Mint 22.x có sẵn 3.12. B không cần cài thêm
Python.

**Hệ quả.**

1. B phải tạo venv riêng, không dùng Python toàn cục. Hướng dẫn đầy đủ cho Mint ở
   README mục 9 Cách 1.
2. Thêm `tests/test_env.py` làm cổng kiểm tra. Phải ra **12/12 khớp** thì cổng GĐ0
   phần môi trường mới đóng.
3. **Máy của A cũng không đạt** — Windows, Python 3.13.13, 0/12 gói khớp. A không
   chạy thí nghiệm nên không chặn, nhưng nếu A cần chạy lại để đối chiếu số của B
   thì phải dựng venv với Python 3.10–3.12 y như vậy.
4. Muốn nâng cấp bất kỳ gói nào về sau: mở một mục QĐ mới, nêu lý do, rồi chạy lại
   toàn bộ thí nghiệm đã có. Không nâng cấp giữa chừng.
