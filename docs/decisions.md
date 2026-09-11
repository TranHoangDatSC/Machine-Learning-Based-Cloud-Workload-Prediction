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

> **Đính chính lý do — 2026-09-09, theo QĐ-011 điểm 5. Quyết định giữ nguyên.**
>
> Đoạn trên đo trên **mẫu ngẫu nhiên của dữ liệu thô** (2026-08-30), trước cửa sổ 8
> ngày và trước bộ lọc chuỗi. Đo lại trên quần thể nghiên cứu:
>
> | ACF lag 1 | E1 | E2 | E3 |
> |---|---:|---:|---:|
> | Thô, mẫu ngẫu nhiên | 0,675 | 0,644 | 0,781 |
> | **Quần thể nghiên cứu** | **0,6674** | **0,6431** | **0,8634** |
>
> E3 tách hẳn khỏi E1 và E2; vùng nay là 0,643–0,863 chứ không phải 0,644–0,781. Nên
> câu *"động lực học có khả năng so sánh được"* **không còn đúng như đã viết**.
>
> **Quyết định N0/N1/N2 vẫn giữ, và cơ sở của nó mạnh hơn trước.** Lập luận đúng bây
> giờ là: ba môi trường lệch nhau ở **cả hai** thành phần — mức tải *và* mức tự tương
> quan. Transfer thô vì thế trộn hai nguồn khác biệt vào một con số duy nhất và không
> quy trách nhiệm được cho nguồn nào. Đó chính là lý do phải tách, chứ không phải vì
> động lực học vốn giống nhau.
>
> Một phần chênh lệch của E3 đến từ hiệu ứng tổng hợp ở mức máy vật lý — xem QĐ-004,
> và phát biểu trong bài phải theo đúng khuôn câu đã chốt ở đó.

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

---

## QĐ-008 — Chính sách xử lý lỗ hổng dữ liệu cho toàn bộ dự án
**Ngày:** 2026-09-08 · **Người quyết:** A · **Trạng thái:** ✅ **CÓ HIỆU LỰC**

Thay thế bản nháp cùng số ngày 2026-09-07. Bản nháp đề xuất "che theo dòng"; khảo
sát định lượng sau đó cho thấy phương án đó chưa tối ưu. Nội dung dưới đây là bản
chốt, đã sửa vào `protocol.md` mục 5, 6, 7, 8.

### Bối cảnh

Bản hiện thực độc lập của protocol phát hiện quy tắc cũ ở mục 6 bước 6 —
*"ffill tối đa 3 bước, còn thiếu thì cắt chuỗi tại đó"* — phá huỷ dữ liệu:

| Môi trường | Dòng huấn luyện h=12 giữ được |
|---|---|
| E1 | 100% |
| E2 | **26%** |
| E3 | **1%** |

Nguyên nhân: mục 6 xếp lọc chuỗi ở bước 5, điền khuyết ở bước 6, nên bộ lọc độ dài
chạy *trước* khi cắt và không bắt được chuỗi bị cắt cụt sau đó. Nguy hiểm hơn là
bảng tổng kết không lộ ra: E3 báo giữ 99,6% số chuỗi trong khi độ dài trung vị chỉ
còn 26 trên tối đa 2.304.

### Bốn phương án đã cân nhắc

Đo trên mẫu cả ba môi trường, số dòng huấn luyện hợp lệ ở h=12, lấy P1 làm mốc 100%:

| Phương án | E1 | E2 | E3 |
|---|---|---|---|
| P0 — ffill(3) rồi cắt chuỗi *(quy tắc cũ)* | 100% | 26% | **1%** |
| P1 — giữ nguyên chuỗi, bỏ dòng chạm NaN | 100% | 100% | 100% |
| P2 — cắt thành đoạn liên tục ≥ 1 ngày | 99% | 96% | **0%** |
| **P4 — nội suy lỗ hổng ≤ 2 điểm rồi bỏ dòng chạm NaN** | **100%** | **102%** | **226%** |

P2 sập trên E3 vì lỗ hổng rải rác khắp nơi, gần như không có đoạn nào liên tục đủ
một ngày — chỉ 8 đoạn sống sót. Cắt đoạn là cách làm chuẩn trong nhiều thư viện dự
báo, nhưng sai với dạng thưa rải rác.

P4 thắng vì với cửa sổ đặc trưng sâu 24 bước, **một điểm NaN đơn lẻ làm hỏng 25
dòng**. Lấp các lỗ hổng một–hai điểm trước rồi mới lọc dòng sẽ thu hồi phần lớn.

### Quyết định

Chính sách gồm bốn phần, áp dụng **thống nhất cho cả ba môi trường**:

1. **Cửa sổ 8 ngày là cửa sổ toàn cục** của từng môi trường, tính từ mốc thời gian
   sớm nhất của môi trường đó — không phải từ điểm đầu của mỗi chuỗi.
2. **Nội suy tuyến tính lỗ hổng dài ≤ K = 2 điểm** (tối đa 10 phút). Lỗ hổng dài
   hơn giữ nguyên NaN. **Không dùng ffill.**
3. **Lọc ở mức dòng, không cắt chuỗi.** Một dòng huấn luyện tại `t` với horizon `h`
   là hợp lệ khi cửa sổ `[t−24, t]` và target `t+h` đều không NaN.
4. **Ngưỡng giữ chuỗi đổi từ "độ dài ≥ 2.000 điểm" sang "≥ 500 dòng hợp lệ ở
   h = 12"**. Ngưỡng cũ mất nghĩa sau khi cắt cửa sổ còn 8 ngày, vì tối đa chỉ còn
   2.304 điểm nên nó thực chất là yêu cầu độ phủ 86,8%, không phải yêu cầu độ dài.

`K` là tham số cấu hình, không phải hằng số chôn trong code.

### Ba lý do chọn phương án này

**Một — không bịa ra động lực học.** ffill 8–12 điểm tạo ra một giờ dữ liệu phẳng,
làm autocorrelation tăng giả tạo. Mà autocorrelation chính là đại lượng trung tâm
của RQ3, nên bịa nó là tự phá hỏng biến phụ thuộc. Nội suy tuyến tính hai điểm giữa
hai giá trị thật thì khác hẳn về mức độ.

Đã đo, không suy đoán. So autocorr tính **chỉ trên các cặp quan sát thật** với
autocorr sau khi nội suy:

| Môi trường | acf lag-1 quan sát | sau nội suy ≤2 | lệch |
|---|---|---|---|
| E1 | 0,6941 | 0,6941 | +0,0000 |
| E2 | 0,6417 | 0,6428 | +0,0011 |
| E3 | 0,7869 | 0,7956 | **+0,0087** |

Trường hợp xấu nhất lệch +0,0087, trong khi khoảng cách autocorr *giữa các môi
trường* — thứ RQ3 cần phân biệt — là 0,64 đến 0,79. Nhiễu do xử lý nhỏ hơn tín hiệu
cần đo khoảng một bậc.

**Hai — thống nhất giữa ba môi trường.** Mọi tham số giống hệt nhau ở E1, E2, E3.
Nếu mỗi môi trường một quy tắc thì chênh lệch hiệu năng ở RQ2 và RQ3 không còn quy
được cho môi trường nữa — đúng loại lỗi mà `tu-bai-cu-den-bai-nay.md` mục 3 mô tả.

**Ba — có đường kiểm chứng độ vững.** Vì `K` là tham số, chạy lại toàn bộ với `K=0`
cho ra kết quả không nội suy chút nào. Kết quả chính báo cáo ở `K=2`, kèm bảng đối
chiếu `K=0` trong phần Limitations. Phản biện hỏi "nội suy có làm đẹp số không" thì
đã có sẵn câu trả lời bằng số.

### Số liệu tham chiếu sau khi áp dụng

Chạy trên toàn bộ dữ liệu, `scripts/reference_gd1.py`, K=2:

| Chỉ số | E1 | E2 | E3 |
|---|---|---|---|
| Chuỗi vào | 1.250 | 500 | 500 |
| Loại — ngoài cửa sổ | 55 | 1 | 0 |
| Loại — gần chết | 454 | 197 | 1 |
| Loại — hằng | 0 | 0 | 0 |
| Loại — ít dòng | 6 | 0 | 0 |
| **Chuỗi còn lại** | **735** (58,8%) | **302** (60,4%) | **499** (99,8%) |
| Dòng hợp lệ h=1 | 1.650.896 | 678.486 | 941.439 |
| Dòng hợp lệ h=12 | 1.642.811 | 673.322 | 919.907 |
| Điểm được nội suy | 272 (0,016%) | 641 (0,092%) | 1.910 (0,183%) |
| Mẫu bị clip trên 100 | 319.082 (2,84%) | 95.137 (2,19%) | 0 |
| Target mean | 13,64 | 9,22 | 38,05 |
| Target p50 | 1,78 | 1,77 | 37,83 |

Tỉ lệ nội suy thực tế **dưới 0,2% ở cả ba môi trường** — thấp hơn nhiều so với ước
lượng ban đầu, vì khảo sát sơ bộ chỉ đọc 6 triệu dòng đầu của Alibaba nên mọi máy
đều bị cắt cụt một cách giả tạo. Trên dữ liệu đầy đủ, E3 lành lặn hơn hẳn.

### Hệ quả

1. `protocol.md` mục 5, 6, 7, 8 đã sửa theo chính sách này.
2. Ba môi trường có 673 nghìn đến 1,64 triệu dòng huấn luyện — thừa sức cho global
   model, và không môi trường nào bị thiệt hại bất thường.
3. **Bảng dữ liệu của paper phải có cột "tỉ lệ điểm được nội suy" cho từng môi
   trường.** Đây là thao tác can thiệp vào dữ liệu, phải khai báo.
4. Bảng lọc phải tách riêng bốn lý do loại, không gộp.
5. Ở GĐ4, chạy thêm một lượt `K=0` cho các cặp transfer chính làm kiểm tra độ vững.
6. E1 mất 55 chuỗi vì "ngoài cửa sổ" — đó là các VM bắt đầu ghi muộn hơn mốc chung
   tới 400 giờ. Đây là hệ quả trực tiếp của việc chọn cửa sổ toàn cục, và là cái giá
   chấp nhận được để mọi chuỗi cùng phủ một khoảng lịch.

### Kiểm tra độ vững — đã chạy, K=0 so với K=2

Chạy lại toàn bộ với `--interp 0`, tức không nội suy điểm nào:

| Môi trường | Chuỗi giữ K=2 | Chuỗi giữ K=0 | Dòng h=12 K=2 | Dòng h=12 K=0 | Chênh |
|---|---:|---:|---:|---:|---:|
| E1 | 735 | **735** | 1.642.811 | 1.636.326 | −0,39% |
| E2 | 302 | **302** | 673.322 | 660.555 | −1,90% |
| E3 | 499 | **499** | 919.907 | 907.772 | −1,32% |

**Số chuỗi được giữ giống hệt nhau ở cả ba môi trường.** Số dòng huấn luyện chênh
dưới 2%. Nghĩa là quyết định nội suy **không** thay đổi tập chuỗi đưa vào nghiên
cứu, và gần như không đổi lượng dữ liệu.

Đây là kết quả mạnh hơn mong đợi: nó cho phép phát biểu trong paper rằng kết luận
không phụ thuộc vào tham số `K`. Bảng này đưa vào phần Limitations.

Tệp: `results/tables/reference_gd1_K0.json`.


---

## QĐ-009 — Đóng băng danh sách 500 máy của E3
**Ngày:** 2026-09-09 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** B nộp E3: 499 chuỗi giữ, 919.526 dòng h=12. Tham chiếu của A: 499
chuỗi, 919.907 dòng. Lệch 0,041% — nằm trong ngưỡng 5% nên vẫn qua cổng.

Truy nguyên bằng cách dựng lại phép chọn mẫu của A rồi so với 500 máy trong catalog
của B:

| Cách chọn | Trùng với B |
|---|---:|
| A (`reference_gd1.py`) | **56/500** |
| Biến thể `qcut` trên giá trị | 56/500 |
| Biến thể sort theo `machine_id` | 146/500 |

**A và B đo hai tập máy khác nhau tới 89%.**

**Nguyên nhân.** Protocol mục 3 ghi `random_state = 42`, nhưng `.sample()` chọn theo
**vị trí**, mà vị trí phụ thuộc **thứ tự** danh sách máy. Thứ tự đó do cách hiện thực
xây bảng trung bình quyết định — A dùng thứ tự máy xuất hiện khi quét tệp, B dùng
thứ tự khác. Cả hai đều đúng đặc tả; **đặc tả mới là thứ thiếu**.

**Quyết định.** Sinh một danh sách 500 máy cố định, commit vào
`config/e3_machines.txt`. Mọi lần chạy E3 đọc đúng tệp đó, không tự chọn lại.

Quy tắc sinh (`scripts/freeze_e3_sample.py`): sort theo `machine_id` → xếp tầng theo
rank CPU trung bình, 5 tầng → 100 máy mỗi tầng, `random_state = 42`.

**Lý do không chọn cách "chỉ cần sort trước khi sample".** Cách đó khắc phục được
nguyên nhân trực tiếp nhưng vẫn để kết quả phụ thuộc hành vi của `pd.qcut` và của
`.sample()` qua các phiên bản pandas. Đóng băng danh sách loại bỏ mọi phụ thuộc, và
quan trọng hơn: **người đọc paper dựng lại được đúng mẫu** mà không cần chạy lại
phép chọn.

**Hệ quả.**

1. Số tham chiếu E3 đổi. Đã sinh lại `results/tables/reference_E3.json`:

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Chuỗi còn lại | 499 | **498** |
| Loại `gan_chet` | 1 | **2** |
| Dòng hợp lệ h=12 | 919.907 | **917.463** |
| Tỉ lệ nội suy | 0,183% | **0,167%** |
| Target mean | 38,0464 | **38,0123** |

2. B phải sửa `io/alibaba.py` đọc danh sách cố định thay vì tự chọn, rồi chạy lại E3.
3. `check_gd1.py` thêm kiểm tra: `series_id` của E3 phải khớp **đúng** danh sách.
4. Bỏ được lượt quét thứ nhất trên tệp 9 GB — E3 chạy nhanh hơn khoảng một nửa.
5. Phần Dữ liệu của paper phải nêu rõ mẫu được đóng băng và tệp nằm trong repo.

**Điều đáng ghi nhận.** Hai mẫu gần như rời nhau mà thống kê gộp chỉ lệch 0,04% là
bằng chứng phép lấy mẫu phân tầng hoạt động đúng. Vấn đề không nằm ở chất lượng mẫu
mà ở **khả năng tái lập**.

---

## QĐ-010 — Đặc trưng lịch, và bốn quy ước còn thiếu ở mục 8

**Ngày:** 2026-09-09 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Khi dựng cổng GĐ2, đo trên chính `data/processed/`:

| Môi trường | bucket đầu | `bucket × 300` | Đọc ra |
|---|---:|---:|---|
| E1 | 4.587.716 | 1.376.314.800 | 2013-08-12T13:40:00Z — giờ thật |
| E2 | 4.584.360 | 1.375.308.000 | 2013-07-31T22:00:00Z — giờ thật |
| E3 | **0** | 0 | 1970-01-01T00:00:00Z — **vô nghĩa** |

`time_stamp` của Alibaba là **giây kể từ lúc bắt đầu trace**, không phải epoch: E3
chạy từ 0 tới 690.900 giây, đúng 8 ngày. Trace không mang thông tin nó bắt đầu vào
ngày nào, giờ nào.

Hệ quả: 4 trong 19 đặc trưng ở mục 8 là lịch. Với E3 chúng sẽ nói "1970-01-01, thứ
Năm" — lệch pha một lượng **không biết được**, và `dow` thì hoàn toàn bịa. Mục 8
không lường trường hợp này.

**Điều quyết định cách xử lý: lệch pha hằng số vô hại với TN-A, chí mạng với TN-B.**
Trong cùng một môi trường, model tự học được pha nên "giờ 0" là lúc nào không quan
trọng. Xuyên môi trường thì `hour_sin = 0,5` của E1 và của E3 là hai thời điểm khác
nhau trong ngày — đúng chỗ RQ3 hỏi thành phần nào transfer được.

**Bằng chứng ủng hộ việc vẫn giữ đặc trưng lịch.** `reference_gd2.py` đo ACF tại lag
288 (24 giờ): E3 **0,5956**, E1 0,1334, E2 0,1271. Chu kỳ ngày của E3 rất rõ và
**đọc được dù mốc thời gian là tương đối** — pha chưa biết không xoá được tính tuần
hoàn. Bỏ đặc trưng lịch của E3 là vứt đi tín hiệu mạnh nhất mà nó có.

**Quyết định.**

1. **E1 và E2 dùng UTC**, không quy về giờ địa phương Hà Lan.
2. **E3 sinh lịch từ mốc tương đối**, khai báo thẳng `hour` của E3 là *"giờ kể từ lúc
   bắt đầu trace"*, pha chưa biết. **Không bịa ngày bắt đầu cho Alibaba**, kể cả khi
   tìm được con số nào đó trên mạng — không kiểm chứng được thì không đưa vào.
3. **TN-B báo cáo cả có và không có 4 đặc trưng lịch.** Nếu bỏ lịch mà transfer tốt
   lên thì bản thân điều đó là finding cho RQ3, và là finding thật.
4. **`dow` của E3 không diễn giải được theo lịch tuần** — ghi rõ trong Limitations.

**Ba quy ước kèm theo**, chốt vì hai bản hiện thực đều "đúng" mà ra số khác nhau:

| Quy ước | Chốt | Vì sao phải chốt |
|---|---|---|
| `ddof` của rolling std và của CV | **1** | pandas mặc định 1, numpy mặc định 0 |
| Gốc của `dow` | epoch 1970-01-01 là **thứ Năm**, `((t // 86400) + 4) % 7` → **0 là Chủ Nhật** | Quy ước nào cũng được, miễn hai bên dùng chung |
| Cụm `NaN` chạm mép cửa sổ | **Không nội suy**, không ngoại suy để hai bên khớp | Đã đúng ở GĐ1, xem `gate-gd1.md` mục 5.5 |

> **Đính chính nhãn `dow` — 2026-09-09, B phát hiện khi viết `tests/test_features.py`.**
> Bản chốt đầu tiên ghi *"→ 0 là thứ Hai"*. Sai nhãn: công thức `+4` cho 0 là **Chủ
> Nhật**. Đo trên chính dữ liệu đã có —
>
> | Mốc | Thứ thật | Công thức ra |
> |---|---|---:|
> | 1970-01-01 (epoch) | thứ Năm | 4 |
> | `b0` của E1 = 4.587.716 → 2013-08-12 | thứ Hai | 1 |
> | `b0` của E2 = 4.584.360 → 2013-07-31 | thứ Tư | 3 |
>
> **Công thức giữ nguyên, chỉ sửa nhãn.** Không con số nào đổi:
> `reference_gd2.py`, `check_gd2.py` và `src/cwp/features/` đều hiện thực công thức
> chứ không dựa vào nhãn, nên `reference_gd2.json` không phải sinh lại. Sửa vì E1 và
> E2 có mốc thời gian thật — đọc theo nhãn cũ thì phần bàn về chu kỳ tuần trong paper
> lệch đúng một ngày. `tests/test_features.py::test_lich_goc_dow_dung_cong_thuc_chot_o_qd010`
> ghim ba con số ở bảng trên để nhãn không trôi lại lần nữa.

**Đính chính một chỗ hiểu sai của chính A.** Khi dựng cổng, A viết rằng luật dòng hợp
lệ *"trùng đúng với điều kiện để 19 đặc trưng tính được"*. **Sai.** 19 đặc trưng chỉ
chạm 15 điểm trong cửa sổ — `t−24`, `t−12..t−1`, và `t`; các điểm `t−23` đến `t−13`
không đặc trưng nào dùng, vì lag nhảy từ 12 sang 24 còn rolling sâu nhất chỉ 12 bước.

Nên **`dropna()` trên ma trận đặc trưng lỏng hơn luật mục 8**. Đo được: thừa 1.513
dòng ở E2 h=1 và 7.461 dòng ở E3 h=1. **E1 khớp kể cả khi làm sai**, nên lỗi không lộ
nếu chỉ thử một môi trường. Luật mục 8 chặt hơn và đó là chủ ý; lọc dòng phải theo
luật cửa sổ, không theo `dropna`.

**Hệ quả.**

1. Mục 8 bổ sung: bảng 19 tên đặc trưng chuẩn, ba quy ước trên, và cảnh báo `dropna`.
2. `scripts/reference_gd2.py` và `scripts/check_gd2.py` hiện thực đúng các quy ước này.
3. Phần Limitations của paper nêu: chu kỳ ngày-đêm của E1/E2 và E3 lệch pha không
   xác định; `dow` của E3 không diễn giải được.
4. TN-B ở GĐ4 chạy hai biến thể, có và không có đặc trưng lịch.

---

## QĐ-011 — Đính chính tài liệu dữ liệu trước khi viết paper

**Ngày:** 2026-09-09 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Trước khi sinh bảng và hình của GĐ2 Bước 4–7 — những thứ đi thẳng vào
paper — B rà lại toàn bộ hành trình dự án và **đo lại** mọi con số trên sản phẩm
thật thay vì đọc tài liệu. Chi tiết: `research-log/2026-09-09-ra-soat-truoc-paper.md`.

Nền móng vững: catalog đúng nguồn gốc một máy một lần chạy, mẫu E3 khớp 500/500 tệp
đóng băng, cửa sổ 8 ngày đúng ở cả 1.535 chuỗi được giữ, `catalog.mean` tính đúng
trên điểm quan sát thật, và 79.200 ô ma trận đặc trưng đối chiếu trực tiếp với
`data/processed/` sai **0 ô**.

Vấn đề nằm ở tài liệu. `docs/data-card.md` — tệp mà phần Dữ liệu của paper sẽ dựa
vào — đo ngày 2026-08-30 **trên mẫu ngẫu nhiên của dữ liệu thô**, trước cửa sổ 8
ngày, trước bộ lọc chuỗi, và trước cả QĐ-003, QĐ-008, QĐ-009. Tệp không nói điều đó
ở bất kỳ đâu, nên đọc vào thì tưởng nó mô tả dữ liệu nghiên cứu.

**Quyết định.** Sáu điểm dưới đây. Điểm 1–4 là đính chính tài liệu; điểm 5 sửa lý do
của một quyết định cũ mà không đảo quyết định đó; điểm 6 là khai báo bổ sung.

### 1. Hai quần thể, hai tên gọi, không được trộn

Từ nay mọi con số về dữ liệu phải nói rõ nó thuộc quần thể nào:

| | **Thô** | **Nghiên cứu** |
|---|---|---|
| Định nghĩa | toàn bộ trace, trước cửa sổ và trước lọc | chuỗi được giữ, trong cửa sổ 8 ngày |
| Nguồn số | `data-card.md`, đo trên mẫu ngẫu nhiên 2026-08-30 | `catalog.parquet` + `data/processed/`, đo trên toàn bộ |
| Dùng để | mô tả nguồn dữ liệu và lý do cắt scope | **mọi bảng và hình của paper** |

Chênh lệch giữa hai quần thể không nhỏ, và không đều giữa các môi trường:

| Chỉ số | E1 thô → nghiên cứu | E2 thô → nghiên cứu | E3 thô → nghiên cứu |
|---|---|---|---|
| Trung bình CPU% | 6,75 → **13,6352** | 6,99 → **9,2199** | 38,13 → **38,0123** |
| Trung vị CPU% | 0,84 → **1,7833** | 1,07 → **1,7667** | 37,0 → **37,8333** |
| ACF lag 1 | 0,675 → **0,6674** | 0,644 → **0,6431** | 0,781 → **0,8634** |

Nguyên nhân đã truy được: bộ lọc `gan_chet` bỏ 36,3% chuỗi E1 và 39,4% chuỗi E2
nhưng chỉ 0,4% chuỗi E3. Lọc gần như chỉ cắt ở đuôi dưới, nên trung bình E1 tăng hơn
gấp đôi còn E3 đứng yên. **Đây là hiệu ứng chọn lọc, phải nêu trong phần Dữ liệu**,
không phải đặc tính tự nhiên của Bitbrains.

### 2. "target" trong bảng mô tả và hình phân phối = phân phối gộp của `y`

`gate-gd2.md` mục 2.2 gọi ba con số 13,6352 / 9,2199 / 38,0123 là *"Target mean /
p50 / std"*. Sai tên: đó là phân phối gộp của `y` trên các chuỗi được giữ, **không
phải** cột `target` của ma trận đặc trưng. Cột `target` thật cho 13,6741 / 9,2667 /
38,3678 — chênh 0,3–0,9%, dưới ngưỡng 2% nên cổng không bắt được.

**Chốt:** bảng thống kê mô tả (Bước 4) và hình phân phối (Bước 5) mô tả
**"CPU% sau tiền xử lý"** — phân phối gộp của `y` trên chuỗi được giữ. Ba lý do:

1. Nó **không phụ thuộc horizon**, nên một bảng và một hình dùng chung cho cả ba `h`.
2. Nó **đã được hai bản hiện thực độc lập kiểm chéo** ở GĐ1, lệch 0,000%.
3. Phần Dữ liệu của paper mô tả **dữ liệu**, không mô tả một dẫn xuất theo `h`.

Thống kê của cột `target` thuộc phần Thiết lập thí nghiệm, báo cáo riêng, lấy từ
`target_mean_h1/h6/h12` đã có sẵn trong `reference_gd2.json`. **Không con số nào
đổi — chỉ đổi tên gọi cho đúng thứ đang được đo.**

**Không sửa nhãn trong nhật ký cũ.** Các log đã đóng (`2026-09-09-ban-giao-gd1.md`,
`2026-09-08-chot-qd008.md`, QĐ-008 và QĐ-009 ở chính tệp này) còn dùng chữ "Target
mean". Đó là bản ghi lịch sử, sửa lại là viết lại quá khứ. Quy tắc áp dụng từ nay về
sau và cho tài liệu còn sống: `protocol.md`, `data-card.md`, `gate-gd2.md`, và mọi
bảng hình của paper.

### 3. Hiệu ứng trần do clip phải khai báo

protocol mục 6 bước 1 clip CPU% về `[0, 100]`, và mục 6 đã đòi báo cáo tỉ lệ clip.
Nhưng chưa ai đo **hệ quả sau khi căn lưới**: tỉ lệ điểm nằm đúng tại trần 100.

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Điểm bằng đúng 100 | **5,1238%** | **2,2788%** | **0,0000%** |
| Phân vị 95 của CPU% | **100,0000** | 60,0667 | 61,2667 |

Phân vị 95 của E1 **chính là trần**. Đây là kiểm duyệt (censoring) và nó **bất đối
xứng giữa đúng ba môi trường đang được đem so sánh**. Ba hệ quả phải nêu:

- Hình phân phối ở Bước 5 sẽ có một cột dựng đứng tại 100 cho E1 và E2. Phải chú
  thích, không để người đọc tự đoán.
- Mọi chỉ số ở vùng tải cao của E1/E2 đo trên dữ liệu đã bị chặn trần. Model dự đoán
  vượt 100 bị phạt dù có thể đúng.
- Lập luận "E3 mượt hơn, dễ dự đoán hơn" có một phần đến từ việc E3 không chạm trần.
  Vào Limitations, không được bỏ qua.

**Không đổi luật clip.** Thang 0–100 là định nghĩa của biến mục tiêu ở mục 4; đổi nó
là đổi bài toán. Chỉ khai báo.

### 4. Hai mô tả phương pháp trong data card đã sai — xoá

| Data card ghi | Thực tế |
|---|---|
| Giá trị thiếu → *"Forward-fill tối đa 3 bước"* | **QĐ-008 đã bãi bỏ ffill.** Nay là nội suy tuyến tính cụm ≤ 2 điểm |
| Độ dài chuỗi → *"Ngưỡng 2.000 điểm"* | QĐ-008 thay bằng `min_valid_rows_h12 = 500` |

Đây không phải số lệch mà là **mô tả sai phương pháp**, và sai đúng chỗ nguy hiểm:
ffill tạo đoạn phẳng làm autocorrelation tăng giả tạo, mà autocorrelation là đại
lượng trung tâm của RQ3. Khai rằng mình đã ffill trong khi code không ffill là tự
tạo ra một lỗ hổng phản biện không có thật.

### 5. Tiền đề ACF của QĐ-005 đã đổi — sửa lý do, **giữ nguyên quyết định**

QĐ-005 biện minh cho ablation N0/N1/N2 bằng câu: *"Autocorr bậc 1 của ba môi trường
nằm cùng vùng, 0,644 đến 0,781. Nghĩa là động lực học có khả năng so sánh được, chỉ
mức tải là lệch."* Đo trên quần thể nghiên cứu, E3 là **0,8634**, tách hẳn khỏi E1
(0,6674) và E2 (0,6431). Vùng nay là 0,643–0,863.

**Quyết định QĐ-005 giữ nguyên hiệu lực, và còn cần hơn trước** — nay hai bên lệch cả
mức tải lẫn mức tự tương quan, nên transfer thô lại càng không nói lên điều gì. Chỉ
câu biện minh phải sửa: động lực học **không** nằm cùng vùng như đã tưởng, và đó
chính là lý do phải tách hai thành phần thay vì đo gộp.

### 6. Đặc trưng lịch là UTC; E1 và E2 vận hành ở UTC+2

QĐ-010 chốt E1/E2 dùng UTC. Đo được một dữ kiện xác nhận cách đọc: `b0` của E2 là
4.584.360 → **2013-07-31T22:00:00Z**, đúng bằng **00:00 giờ Amsterdam mùa hè
(UTC+2)**. Trace bắt đầu đúng nửa đêm giờ địa phương, nên "một ngày" trong dữ liệu
E2 bắt đầu tại giờ UTC 22.

Giữ UTC. Nhưng mọi phát biểu diễn giải giờ trong paper phải ghi rõ **"giờ UTC"**;
giờ vận hành thật của trung tâm dữ liệu Hà Lan là UTC+2, và với `dow` thì lệch này
đủ để đẩy hoạt động nửa đêm sang ngày hôm trước.

**Hệ quả.**

1. `docs/data-card.md`: thêm khai báo quần thể ở đầu tệp, đánh dấu các bảng cũ là
   "thô — mẫu ngẫu nhiên", xoá hai mô tả phương pháp sai, thêm mục
   **"Sau tiền xử lý — quần thể nghiên cứu"** với số đo được trên toàn bộ.
2. `docs/protocol.md` mục 4: khai báo hiệu ứng trần. Mục 8: ghi rõ giờ là UTC.
3. QĐ-005: thêm khối đính chính, giữ nguyên quyết định.
4. `research-log/gate-gd2.md` mục 2.2: đổi nhãn "Target" thành "CPU% sau tiền xử lý".
5. Bước 4 và Bước 5 của `brief-gd2-b.md` làm theo điểm 2; Bước 6 báo tỉ lệ cặp bị bỏ
   cạnh mọi con số ACF của E3 (14,65% ở lag 288).
6. Phần Limitations của paper nhận thêm ba mục: hiệu ứng chọn lọc của bộ lọc
   `gan_chet`, kiểm duyệt tại trần 100 của E1/E2, và tỉ lệ thiếu 9,29% của E3.

---

## QĐ-012 — Phân tầng theo CV ở GĐ3, và ba khai báo đóng lại từ GĐ2

**Ngày:** 2026-09-10 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** GĐ2 chạy hết tám bước và để lại bốn việc chờ quyết (V1–V4 ở
`research-log/2026-09-09-gd2-dac-trung.md`). V1 chặn GĐ3 vì nó quyết định cách đọc
kết quả TN-A; ba việc còn lại là khai báo, không chặn gì.

### 1. Phân tầng theo CV: dùng **phân vị trong từng môi trường**, không dùng ngưỡng chung

Chia ba tầng burstiness bằng **tam phân vị CV tính riêng cho mỗi môi trường**. Ngưỡng
đo được trên quần thể nghiên cứu:

| Môi trường | Ngưỡng thấp/vừa | Ngưỡng vừa/cao |
|---|---:|---:|
| E1 | 0,256 | 0,849 |
| E2 | 0,285 | 0,943 |
| E3 | 0,258 | 0,321 |

**Lý do bác ngưỡng tuyệt đối dùng chung.** Hai thứ đo được, không phải phỏng đoán:

- **Tương quan giữa CV và mức tải đổi dấu giữa các môi trường.** Spearman ρ là
  **+0,375 (E1), +0,249 (E2), −0,692 (E3)**. Ở Bitbrains, VM tải cao thì bursty hơn;
  ở Alibaba thì ngược lại. Một ngưỡng CV chung vì thế chọn ra **hai nhóm máy khác
  loại** ở hai môi trường, và mọi so sánh theo tầng sẽ trộn hai thứ vào nhau.
- **Tam phân vị của E3 chỉ rộng 0,06** (0,258–0,321) và nằm gọn bên trong tầng thấp
  nhất của E1. Ngưỡng chung sẽ dồn gần như toàn bộ E3 vào một tầng, và tầng đó rỗng
  nghĩa so sánh.

**Kèm theo, bắt buộc.** Mỗi bảng phân tầng phải báo cả cột `ti_le_cham_chan` — tỉ lệ
`CV / √((100−m)/m)` — để biết một chuỗi "ít bursty" là do bản chất hay do đã cụng
trần thang đo. Cột này đã có sẵn trong `results/tables/cv_gd2.csv`.

### 2. CV là biến **báo cáo**, không phải đặc trưng, không phải tiêu chí chọn model

Chốt luôn để tránh một chỗ rò rỉ chưa xảy ra.

`cv_gd2.csv` tính CV trên **toàn bộ cửa sổ 8 ngày**, tức có cả phần rơi vào validation
và test. Dùng nó để **phân tầng khi báo cáo kết quả** thì không sao: đó là một cách
nhóm các chuỗi lại để đọc bảng, không phải một đầu vào của model.

Nhưng nếu GĐ3 hay GĐ4 muốn dùng CV làm **đặc trưng**, làm **trọng số huấn luyện**,
hay làm **tiêu chí chọn model theo tầng**, thì con số hiện tại là **rò rỉ** — nó biết
tương lai. Khi đó **bắt buộc tính lại CV chỉ trên cửa sổ train của từng chuỗi**, đúng
nguyên tắc đã áp cho thống kê chuẩn hoá N1 ở mục 14.

### 3. Chặn `CV ≤ √((100−m)/m)` vào Limitations — V2

CPU% bị chặn trong `[0, 100]`, nên một chuỗi có trung bình `m` không thể có phương sai
vượt `m(100 − m)`. Suy ra CV bị chặn cứng bởi **thang đo**, không phải bởi dữ liệu.
Đo trên 1.535 chuỗi: **0 chuỗi vi phạm**, và rìa chéo của đám điểm ở
`results/figures/gd2/09_cv-so-voi-muc-tai.png` trùng khít đường chặn.

Đây là cơ chế **khác** với trần 100 ở QĐ-011 điểm 3: trần kiểm duyệt các *điểm*, chặn
này giới hạn *thống kê phân tán*. Hệ quả đảo ngược cách đọc:

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Mức tải trung vị | 2,71 | 2,57 | 40,15 |
| ⇒ chặn CV tại mức đó | 6,00 | 6,16 | **1,22** |
| CV trung vị thực tế | 0,497 | 0,537 | 0,286 |
| **CV / chặn** | 0,094 | 0,104 | **0,233** |

So với mức biến động mà thang đo cho phép ở mức tải của chính nó, **E3 dùng gấp hơn
hai lần E1/E2**. Câu "E3 ít bursty hơn" chỉ đúng với CV thô, và phải nói kèm chỗ này.

### 4. E1 và E2 **không có chu kỳ ngày** — V3, ảnh hưởng cách đọc TN-B

Đo ở GĐ2 Bước 6: ACF của E1 và E2 không bao giờ xuống âm đáng kể (nhỏ nhất 0,0028 và
−0,0057), và mức nhô tại lag 288 (+0,068 và +0,069 so với hai lag láng giềng) **xấp xỉ
đúng mức nhô của nhịp một giờ** — mà 288 = 24 × 12 cũng là một bội số của 12. Nghĩa là
giá trị tại lag 288 của chúng giải thích hết bằng nhịp giờ, không cần giả định thêm
chu kỳ ngày nào. Chỉ E3 có sóng ngày thật: cắt 0 tại lag 74, đáy −0,4191 tại lag 139
(nửa ngày), đỉnh 0,5956 tại lag 288.

**Hệ quả cho GĐ4.** QĐ-010 chốt TN-B chạy hai biến thể, có và không có 4 đặc trưng
lịch. Kết quả Bước 6 dự báo biến thể "bỏ lịch" sẽ **gần như không đổi gì với E1 và
E2** mà chỉ ảnh hưởng E3. Nếu quan sát được đúng như vậy thì đó là **xác nhận**, không
phải phát hiện mới; nếu bỏ lịch mà E1/E2 đổi nhiều thì phải đi tìm nguyên nhân khác.

### 5. Nhịp một giờ vào phần Dữ liệu — V4

ACF nhô lên tại **24/24 bội số của 12 bucket** trong dải lag 12–288, ở **cả ba** môi
trường. Mức trội trung vị: +0,0618 (E1), +0,0314 (E2), +0,0075 (E3). Đây là quan sát
về **dữ liệu**, không phải về model, nên thuộc phần Dữ liệu; và nó là căn cứ đo được
cho việc giữ `lag_12` và `lag_24` trong bộ đặc trưng của mục 8.

### 6. Đính chính số ở mục 14 — đo lại trên quần thể nghiên cứu

`docs/protocol.md` mục 14 và `docs/giai-thich-chuan-hoa.md` trích bốn con số đo trên
**833 chuỗi Alibaba**, tức trước khi QĐ-009 đóng băng mẫu 500 máy. Quần thể nghiên cứu
hiện tại chỉ có **498 chuỗi**. Đo lại trên `data/features/E3_h1.parquet`, MAE trung vị
theo chuỗi:

| Phép đo | 833 chuỗi (cũ) | **498 chuỗi (quần thể nghiên cứu)** |
|---|---:|---:|
| (a) hằng số bằng mức tải trung bình của E1 | 28,64 | **26,90** |
| (b) hằng số bằng mức tải trung bình của E3 | 10,48 | **10,06** |
| (c) naive persistence trong E3 | 5,76 | **4,35** |
| Phần sai số chỉ là chênh mức tải, `(a−b)/a` | 63,4% | **62,6%** |
| Naive tốt hơn "kết quả transfer" bao nhiêu lần | 5× | **6,2×** |

**Lập luận giữ nguyên, và mạnh hơn một chút.** Một hằng số vẫn đạt MAE ≈ 27 khi
"transfer" E1 sang E3; gần hai phần ba sai số đó vẫn chỉ là chênh lệch mức tải; và
naive persistence trong chính E3 nay tốt hơn 6,2 lần chứ không phải 5 lần. Chỉ các con
số được thay.

**Hệ quả.**

1. `docs/protocol.md` mục 13 nhận mục con về phân tầng CV; mục 14 sửa bốn con số.
2. `docs/giai-thich-chuan-hoa.md` nhận khối đính chính, giữ nguyên số cũ để đối chiếu.
3. `docs/data-card.md` Limitations nhận thêm mục về chặn CV.
4. `config/split.yaml` khai `stratify_by: cv_percentile_within_env`.
5. GĐ3 báo cáo kết quả theo ba tầng burstiness, kèm cột `ti_le_cham_chan`.

---

## QĐ-013 — Năm quy ước của GĐ3 mà mục 9 và 12 chưa nói rõ

**Ngày:** 2026-09-10 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Dựng cổng GĐ3 thì lộ ra: mục 9 viết *"70% train, 15% validation, 15%
test"* và mục 12 liệt năm chỉ số, nhưng cả hai đều thiếu định nghĩa đủ chặt để hai
bản hiện thực độc lập ra cùng con số. Đúng cái bẫy QĐ-010 đã gặp ở GĐ2 — mỗi bên
"đúng" theo cách hiểu của mình rồi số lệch nhau mà không ai sai.

Chốt trước, **trước khi có dòng code GĐ3 nào**, để cổng có neo.

### 1. Ranh giới chia tính theo **bucket**, không theo số dòng

70% của **cửa sổ 2.304 bucket**, không phải 70% của số dòng hợp lệ.

| Tập | Khoảng offset so với `b0` | Số bucket | Tỉ lệ |
|---|---|---:|---:|
| train | `[0, 1612)` | 1.612 | 69,97% |
| validation | `[1612, 1957)` | 345 | 14,97% |
| test | `[1957, 2304)` | 347 | 15,06% |

`n_train = floor(0,70 × 2304) = 1612`, `n_val = floor(0,15 × 2304) = 345`, phần còn
lại là test.

**Lý do.** Cửa sổ 8 ngày là **toàn cục theo môi trường** (mục 7), nên ranh giới theo
bucket là một lát cắt thời gian **giống hệt nhau ở mọi chuỗi**. Chia theo số dòng hợp
lệ thì mỗi chuỗi cắt ở một mốc lịch khác nhau — chuỗi nhiều NaN sẽ có test bắt đầu
muộn hơn — và khi đó "chia theo thời gian" không còn đúng nghĩa.

### 2. Một dòng thuộc tập nào: cả `t` **và** `t+h` phải cùng tập

Dòng có gốc dự đoán `t` và horizon `h` thuộc tập `S` khi **cả `t` và `t+h` đều nằm
trong `S`**. Dòng vắt qua ranh giới bị **loại** (purge).

**Lý do — đây là chống rò rỉ, không phải chuyện thẩm mỹ.** Nếu gán theo `t` thôi thì
một dòng train ở cuối tập train có target `y_{t+h}` rơi vào validation hoặc test.
Huấn luyện trên dòng đó là cho model nhìn thấy nhãn của tương lai thuộc tập đánh giá.

Giá phải trả nhỏ: mất tối đa `h` dòng mỗi ranh giới mỗi chuỗi, tức dưới 1,1% ở `h=12`.

### 3. Mẫu số của MASE

`MASE = MAE / d`, với `d` = **trung bình `|y_t − y_{t−1}|` trên phần train của chính
chuỗi đó**, chỉ lấy các cặp `(t−1, t)` mà **cả hai** đều không NaN.

Hai điều kèm theo:
- Mẫu số tính **chỉ trên train**, đúng nguyên tắc chống rò rỉ đã áp cho N1 ở mục 14.
- Mẫu số **không phụ thuộc horizon** — cùng một `d` dùng cho cả `h = 1, 6, 12`, nên
  MASE ở ba horizon so được với nhau.
- Chuỗi có `d = 0` (train phẳng hoàn toàn) thì MASE không xác định: **loại chuỗi đó
  khỏi phần gộp MASE** và báo số chuỗi bị loại. Không thay bằng 0, không thay bằng
  epsilon.

### 4. SMAPE và R²

`SMAPE = 100 × mean( |y − ŷ| / ((|y| + |ŷ|) / 2) )`, và khi `|y| + |ŷ| = 0` thì số
hạng đó **bằng 0** (dự đoán đúng tuyệt đối tại một điểm bằng 0).

Chỗ này quan trọng với dự án: E1 và E2 có trung vị dưới 2% và rất nhiều điểm gần 0,
nên quy ước xử lý mẫu số nhỏ quyết định con số cuối. QĐ-006 đã bỏ MAPE vì lý do này;
SMAPE vẫn giữ được nhưng phải chốt cách xử lý `0/0`.

`R² = 1 − SS_res / SS_tot` với `SS_tot` tính trên **target của chính chuỗi đó trong
tập đang đánh giá**. Chuỗi có `SS_tot = 0` thì R² không xác định: **loại khỏi phần
gộp** và báo số chuỗi bị loại.

### 5. Gộp kết quả nhiều chuỗi: trung vị của chỉ số **theo từng chuỗi**

Mục 12 đã nói *"gộp bằng trung vị kèm IQR"*. Chốt thêm cho hết mơ hồ: tính chỉ số
**riêng cho từng chuỗi trước**, rồi lấy trung vị và IQR **trên tập chuỗi**. Không gộp
mọi dòng của mọi chuỗi vào một dãy rồi tính một chỉ số.

**Lý do — đã đo được ở GĐ2.** Gộp mọi điểm trước rồi mới tính làm ACF lag 1 của E1 nở
từ 0,6674 lên 0,9586, vì nó trộn phương sai *giữa* các chuỗi vào. Chỉ số lỗi cũng
vướng cùng một cơ chế: chuỗi tải cao đóng góp sai số tuyệt đối lớn hơn và sẽ chi phối
con số gộp. Trung vị theo chuỗi cho mỗi máy một phiếu bằng nhau.

**Hệ quả.**

1. `scripts/reference_gd3.py` hiện thực đúng năm quy ước này và sinh
   `results/tables/reference_gd3.json` — neo của cổng GĐ3.
2. `docs/protocol.md` mục 9 và 12 nhận mục con trỏ về đây.
3. `config/split.yaml` khai `boundary: bucket` và `purge_straddling: true`.
4. Bản hiện thực của B phải ra **cùng con số** ở ba baseline; lệch là có lỗi ở một
   trong hai bên, không phải nhiễu — baseline không có yếu tố ngẫu nhiên nào.

---

## QĐ-014 — Rolling-origin, mẫu con SVR, và bù cho chỗ tính độc lập bị yếu

**Ngày:** 2026-09-10 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** `gate-gd3.md` mục 6 để ngỏ hai điểm, và mục 1 ghi một cảnh báo về tính
độc lập. Cả ba đều nên chốt **trước** khi B viết dòng code GĐ3 đầu tiên, vì cả ba đều
ảnh hưởng tới con số cuối.

### 1. Rolling-origin — expanding, 5 fold chia đều phần validation

Vùng dùng cho chọn siêu tham số là **train + validation**, tức bucket `[0, 1957)`.
Phần validation `[1612, 1957)` dài đúng **345 bucket**, chia hết cho 5 được **69**.

| Fold | train | validation |
|---:|---|---|
| 1 | `[0, 1612)` | `[1612, 1681)` |
| 2 | `[0, 1681)` | `[1681, 1750)` |
| 3 | `[0, 1750)` | `[1750, 1819)` |
| 4 | `[0, 1819)` | `[1819, 1888)` |
| 5 | `[0, 1888)` | `[1888, 1957)` |

**Expanding**, không phải sliding: train của fold sau chứa trọn train của fold trước.

Ba ràng buộc:

- Mỗi fold vẫn áp **luật purge** của QĐ-013 điểm 2: một dòng thuộc train của fold khi
  cả `t` và `t+h` nằm trong khoảng train của fold đó; tương tự cho validation.
- **Test `[1957, 2304)` không được chạm ở bất kỳ fold nào.**
- Fold nào cũng train trên quá khứ và đánh giá trên tương lai của chính nó — không
  fold nào có validation nằm trước train.

**Vì sao expanding chứ không sliding.** Sliding giữ độ dài train cố định nên mỗi fold
vứt đi phần đầu chuỗi. Với cửa sổ chỉ 8 ngày thì dữ liệu là thứ khan hiếm nhất, và
không có lý do nào nghi ngờ dữ liệu cũ mất giá trị trong 8 ngày. Expanding cũng khớp
với cách model cuối cùng được huấn luyện — trên toàn bộ train + validation.

### 2. Mẫu con của SVR — lấy mẫu **dòng huấn luyện**, không lấy mẫu chuỗi

protocol mục 11 cho phép SVR chạy trên mẫu con nếu quá chậm. Chốt cách làm:

**Lấy mẫu con của DÒNG HUẤN LUYỆN. Tập test giữ nguyên 100%.**

- Mẫu con phân tầng theo **ba tầng burstiness** của QĐ-012, giữ đúng tỉ lệ ba tầng.
- `random_state = 42`, và ghi số dòng đã lấy vào `runs/`.
- Cùng một mẫu con dùng cho cả ba horizon.

**Vì sao lấy mẫu dòng chứ không lấy mẫu chuỗi.** Nếu bỏ bớt chuỗi thì SVR được đánh
giá trên một **quần thể khác** với sáu model kia, và cột SVR trong bảng so sánh mất
nghĩa — đúng cái bẫy "hai con số trông so được nhưng đo hai thứ khác nhau" mà
`tu-bai-cu-den-bai-nay.md` mục 3 phân tích. Lấy mẫu dòng huấn luyện thì SVR chỉ **học
ít hơn**, còn **đo trên đúng tập test như mọi model khác**. Bảng vẫn so được, và việc
SVR học ít hơn là một hạn chế **đã khai báo**, không phải một cái bẫy ẩn.

Nếu SVR vẫn quá chậm sau khi lấy mẫu, **bỏ SVR và ghi rõ**, chứ không giảm tập test.

### 3. Tính độc lập của GĐ3 yếu hơn GĐ1 và GĐ2 — bù bằng ba loại phép kiểm

**Nói thẳng vấn đề.** `scripts/reference_gd3.py` do cùng một agent đã viết code B của
GĐ2 soạn ra. Ở GĐ1 và GĐ2, thước đo và bản hiện thực do hai bên khác nhau viết, nên
việc chúng khớp là bằng chứng mạnh. Ở GĐ3 thì bằng chứng đó **yếu hơn**: hai bản có
thể cùng sai một kiểu.

Không sửa được triệt để trong khuôn khổ hiện tại. Cách ít rủi ro nhất là **đừng dựa
vào một loại bằng chứng duy nhất**. `scripts/check_gd3.py` vì thế kiểm **ba loại**:

| Loại | Phụ thuộc tính độc lập? | Bắt được gì |
|---|---|---|
| **A. So với `reference_gd3.json`** | **Có** — yếu ở GĐ3 | Lỗi gõ, lỗi lệch một dòng, dùng sai cột |
| **B. Đẳng thức tự thân** | **Không** | Vi phạm quan hệ mà *mọi* bản hiện thực đúng đều phải thoả |
| **C. Đáp án giải tích trên dữ liệu giả lập** | **Không** | Hiểu sai định nghĩa — kiểu lỗi mà hai bản cùng tác giả dễ cùng mắc |

Loại B và C **không quan tâm hai bản có khớp nhau không**, nên chúng giữ nguyên giá
trị kể cả khi tính độc lập bằng không. Ví dụ:

- **B:** tổng ba tập phải nhỏ hơn tổng dòng hợp lệ **đúng** `n_chuỗi × 2 × h`;
  `MASE = MAE / d` với đúng `d` đã báo; `RMSE ≥ MAE` luôn đúng theo bất đẳng thức
  Jensen; `SMAPE ∈ [0, 200]`.
- **C:** trên một môi trường giả lập tính tay được, MAE của naive phải bằng đúng con
  số suy ra từ công thức, R² của một dự đoán hằng bằng đúng `−SS/SS_tot`.

**Ghi lại để sau này biết:** nếu có điều kiện, phần hiện thực GĐ3 nên do **một phiên
khác** làm, và phiên đó **không đọc `reference_gd3.py`**. Khi ấy loại A lấy lại được
sức mạnh vốn có. Nếu không có điều kiện thì loại B và C là chỗ dựa chính, và log GĐ3
phải **ghi rõ tính độc lập đã yếu** thay vì để người đọc sau này tưởng nó mạnh như hai
giai đoạn trước.

### 4. Hợp đồng tên tệp đầu ra của GĐ3

`check_gd3.py` cần biết đọc ở đâu. Chốt hai tệp:

**`results/tables/splits_gd3.csv`** — cột `env, h, split, n_dong`.

**`results/tables/baselines_gd3.csv`** — cột `env, h, model, split, metric, p25, p50,
p75, iqr, n_chuoi, n_loai, n_dong_dung, n_dong_test`.

`model` nhận `naive | ma6 | seasonal`; `metric` nhận `mae | rmse | smape | mase | r2`;
`split` ở bảng baseline luôn là `test`.

**Hệ quả.**

1. `scripts/check_gd3.py` và `tests/test_check_gd3.py` hiện thực ba loại phép kiểm ở
   điểm 3.
2. `gate-gd3.md` mục 6 khép lại; mục 4 trỏ tới hợp đồng tên tệp ở điểm 4.
3. `brief-gd3-b.md` Bước 1 nhận bảng 5 fold; Bước 5 nhận luật lấy mẫu SVR.
4. `config/split.yaml` khai `cv.mode: expanding` và `cv.n_splits: 5`.

### Đính chính QĐ-014 — 2026-09-10, sau khi viết `tests/test_check_gd3.py`

Test của chính công cụ kiểm tìm ra ba chỗ bản đầu sai. Ghi lại vì hai chỗ đầu là loại
lỗi làm **trượt oan**, khó chẩn đoán hơn lỗi cho qua nhầm.

**1. B1 phải là bất đẳng thức, không phải đẳng thức.** Điểm 3 ở trên viết *"tổng ba
tập phải nhỏ hơn tổng dòng hợp lệ **đúng** `n_chuỗi × 2 × h`"*. Sai. Đẳng thức đó chỉ
đúng khi **mọi** dòng sát hai ranh giới đều hợp lệ. Dữ liệu thật có NaN gần ranh giới
thì những dòng ấy đã bị luật cửa sổ loại từ trước, nên purge lấy đi *ít hơn* `2h` mỗi
chuỗi — và công cụ sẽ báo trượt một bản hiện thực hoàn toàn đúng.

Đổi thành `1 ≤ (hợp_lệ − tổng) ≤ n_chuỗi × 2 × h`. Hướng bắt lỗi không mất gì: quên
purge thì mất **0** dòng, cận dưới `≥ 1` tóm được ngay. Con số chính xác vẫn do loại A
ghim bằng 27 số dòng; B1 chỉ là lưới thứ hai không cần tham chiếu.

**2. Bảng baseline được phép có dòng `train`/`val`.** Điểm 4 viết *"`split` ở bảng
baseline luôn là `test`"*. Nới ra: B được phép báo thêm `train`/`val` để tự theo dõi,
và **công cụ phải lọc `split == "test"` trước khi so** — tham chiếu của A chỉ neo test.
Bản đầu không lọc, nên mỗi tổ hợp có ba dòng và công cụ báo "thiếu dòng". Hai phép
kiểm `B4` (R² ≤ 1) và `B5` (p25 ≤ p50 ≤ p75) thì cố ý **không** lọc: hai bất đẳng thức
ấy phải giữ ở bất kỳ tập nào.

**3. Ca "phải trả NaN" phải hỏi `isnan`, không hỏi `not isfinite`.** `inf` cũng không
hữu hạn. Một bản chia `MAE` cho `d = 0` rồi trả `inf` sẽ **lọt** qua phép kiểm viết
bằng `isfinite` — rồi `inf` trôi vào trung vị và bôi đen cả cột. Đây đúng là loại lỗi
mà loại C sinh ra để bắt, nên để nó lọt thì loại C mất hẳn tác dụng ở ca đó.

**Thêm B7 — ma trận đặc trưng vẫn đúng 22 cột.** `check_gd2.py` đã kiểm điều này khi
đóng GĐ2, nhưng GĐ3 có thể sinh lại `data/features/`, và khi ấy không còn phép kiểm
nào chặn việc thêm một cột ngoài mục 8. B7 đọc schema parquet (không đọc dữ liệu) nên
gần như không tốn gì.

**Ghi lại để lưu ý sau này.** `tests/test_check_gd3.py` chứa sẵn một bản `metrics.py`
để loại C có cái mà gọi, nghĩa là năm công thức chỉ số **có mặt trong tệp B đọc được**.
Chấp nhận, vì QĐ-013 điểm 4 vốn đã đặc tả cả năm công thức lẫn từng ca biên bằng lời —
chép prose ra code không phải chỗ lỗi ẩn náu. Chỗ lỗi ẩn là *áp dụng*: lấy dòng nào,
mẫu số tính trên tập nào, gộp thế nào — và những chỗ đó vẫn được che kín. Nếu sau này
muốn siết, đưa bản mồi ấy ra một tệp riêng ngoài `tests/`.

**Trạng thái bốn hệ quả:** cả bốn đã làm xong ngày 2026-09-10. `check_gd3.py` chạy
được ở trạng thái B chưa bắt đầu (báo thiếu, in tiến độ 0/8, không đổ vỡ);
`tests/test_check_gd3.py` 12/12 xanh, phá chín kiểu đều bị bắt.

---

## QĐ-015 — Đếm 8 model, và khai báo lưới siêu tham số sau khi GĐ3 chạy xong

**Ngày:** 2026-09-11 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** B nêu hai điểm trong log GĐ3 (`2026-09-10-gd3-thi-nghiem-a.md`, mục
Vướng mắc) và đề nghị A quyết trước khi coi GĐ3 là xong.

### 1. "7 model" ở mục 13 so với 8 model ở mục 11

Mục 13 ghi *"3 môi trường x 7 model x 3 horizon"*, mục 11 liệt kê tám model. B chạy
và báo cả tám.

**Nguyên nhân:** bảng ở mục 11 có **7 dòng** nhưng **8 model** — dòng *"Linear
Regression, Ridge"* chứa hai model trong một ô. Con số 7 là đếm dòng bảng.

**Quyết định:** sửa **mục 13** thành `3 × 8 × 3 = 72`. Không sửa mục 11.

Vì sao sửa mục 13 chứ không cắt mục 11 xuống 7: mục 11 liệt kê đích danh năm model ML
(Linear, Ridge, RF, XGBoost, SVR) và `research-plan.md` GĐ3 cũng vậy; cắt xuống 7 sẽ
phải bỏ một model đã chạy xong, tức vứt kết quả thật để chiều một con số gõ nhầm.
Sửa mục 13 không đụng tới bất kỳ sản phẩm nào: `check_gd3.py` không đọc con số này,
`tests/test_config.py` không kiểm nó, và chín bảng kết quả giữ nguyên.

### 2. Lưới siêu tham số không nằm trong giao thức

Mục 11 liệt kê model nhưng không chốt lưới. B tự chọn theo chi phí đo được và khai ở
`src/cwp/models/registry.py`.

**Quyết định: khai báo lưới đã dùng, KHÔNG chạy lại.** Lưới ghi vào mục 11; nguồn
thật vẫn là `registry.py`, tài liệu chỉ để đọc.

| Model | Lưới | Biên **trên** | Biên **dưới** | Chạm biên bất kỳ |
|---|---|---:|---:|---:|
| `ridge` | `alpha ∈ {0,01 … 100}` | 4/9 | **5/9** | **9/9** |
| `rf` | `max_depth ∈ {8, 16}`, 50 cây | **7/9** | 2/9 | 9/9 |
| `xgb` — `depth ∈ {4, 8}` | | **6/9** | 3/9 | 9/9 |
| `xgb` — `n_estimators ∈ {300, 600}` | | 1/9 | **8/9** | 9/9 |
| `svr` | `C ∈ {1, 10}`, mẫu con 10.000 | **7/9** | 2/9 | 9/9 |

> **Đính chính 2026-09-11.** Bản đầu của bảng này chỉ đếm biên **trên** và ghi `ridge`
> 4/9, `xgb` 6/9. Cả hai nói **nhẹ đi**: `ridge` chốt `alpha = 0,01` — tức biên **dưới**
> — ở 5/9 tổ hợp còn lại, nên nó chạm mép lưới **9/9**; còn 6/9 của `xgb` là của trục
> `depth`, trên trục số cây thì 8/9 chọn giá trị **thấp** (300). Hệ quả thực dụng: nới
> `n_estimators` gần như chắc chắn vô ích, còn nới `alpha` phải nới **cả hai đầu**.

**Vì sao không nới lưới rồi chạy lại — đây là phần quan trọng của quyết định này.**

Nới lưới lúc này là nới **sau khi đã biết ML thua naive trên E1 và E2**. Đó đúng là
loại hành vi mục 17 cam kết không làm: *"Không đổi metric sau khi thấy kết quả"*,
*"Không đổi ngưỡng lọc để có bảng đẹp hơn"*. Lưới siêu tham số cùng một họ — nó là
tham số của thí nghiệm, và sửa nó để đổi kết luận thì bảng kết quả mất giá trị chứng
minh, y như chuyện `sample_machines` ở QĐ-009 và đoạn code chỉnh mẫu cho khớp
`gan_chet == 1`.

Đổi lại, **hạn chế phải được nêu thẳng**: với `rf` và `svr` lưới chỉ có **hai** ứng
viên nên **mọi** lựa chọn đều nằm ở mép (biên trên 7/9, biên dưới 2/9); `ridge` chạm
mép 9/9 vì lưới hẹp ở cả hai đầu; và `rf` chỉ chạy 50 cây vì riêng phần dò siêu tham số
của nó đã mất hơn 3 giờ. Nên phát biểu đúng là *"với lưới này và ngân sách này, ML
không vượt naive trên E1 và E2"*.

**Điều này không lung lay kết luận chính.** `lr` và `ridge` thua naive **1,23–2,57 lần**
trên E1 và E2 tuỳ horizon — 1,23–1,35× ở `h = 1`, lên tới 2,33–2,57× ở `h = 12`. Ngay ở
mức hẹp nhất, 1,23×, khoảng cách đó vẫn quá xa để một lưới `alpha` khác khép lại, và
`lr` thì **không có siêu tham số nào** để nới. Chỉ `rf`, `xgb`, `svr` là sát naive đủ
để lưới có thể đổi kết cục.

> **Đính chính 2026-09-11.** Bản đầu ghi *"2,3–2,6 lần"* — đó là con số của riêng
> `h = 12`, không phải của cả ba horizon.

**Nếu muốn kiểm độ vững thì làm ở GĐ5**, theo đúng ba điều kiện: khai báo lưới mới
**trước** khi chạy, giữ nguyên mọi thứ khác, và **báo cáo cả hai kết quả** chứ không
thay thế bảng cũ.

**Hệ quả.**

1. `docs/protocol.md` mục 11 thêm mục "Lưới siêu tham số"; mục 13 sửa `7 → 8`.
2. Không sản phẩm nào phải sinh lại. Chín bảng GĐ3 giữ nguyên. Snapshot khớp bảng
   công bố từng ô là **`runs/20260910-202500_experiments_gd3`** — *không* phải
   `20260910-154617_*` như bản đầu ghi: snapshot ấy chụp **trước** khi mẫu con SVR được
   sửa nên lệch 30 ô (toàn bộ `svr` ở `h = 6` và `h = 12`).
3. Phần Limitations của paper nêu: lưới hẹp, chốt ở biên trên, `rf` 50 cây.
4. GĐ5 có thể thêm một mục kiểm độ vững về lưới, nếu còn thời gian.

---

## QĐ-016 — Năm quy ước của GĐ4 mà mục 14 chưa nói rõ

**Ngày:** 2026-09-11 · **Người quyết:** A · **Trạng thái:** Có hiệu lực

**Bối cảnh.** Mục 14 đặc tả ba chế độ chuẩn hoá bằng lời và `giai-thich-chuan-hoa.md`
giảng rất kỹ *vì sao* cần chúng, nhưng cả hai đều thiếu định nghĩa đủ chặt để hai bản
hiện thực độc lập ra cùng con số. Đúng cái bẫy QĐ-010 gặp ở GĐ2 và QĐ-013 gặp ở GĐ3 —
mỗi bên "đúng" theo cách hiểu của mình rồi số lệch nhau mà không ai sai.

Chốt trước, **trước khi có dòng code GĐ4 nào**, để cổng có neo.

### 1. `mu` và `sd` của N1 lấy từ **cửa sổ train của chính chuỗi đích**

Mục 14 viết *"thống kê chuẩn hoá của N1 chỉ được tính trên cửa sổ train"* — nhưng
không nói **train của ai**. Ở TN-B, chuỗi được chấm nằm ở môi trường **đích**, còn
model học ở môi trường **nguồn**. Hai cách hiểu đều đọc xuôi mục 14:

| Phương án | Nghĩa | Vấn đề |
|---|---|---|
| Thống kê của chuỗi **đích** | Máy đích tự chuẩn hoá bằng lịch sử của chính nó | Không còn là zero-shot thuần |
| Thống kê của môi trường **nguồn** | Transfer thuần tuý | Thất bại vì lệch thang — một lý do tầm thường |

**Quyết định: dùng `mu`, `sd` của chính chuỗi đích, tính trên bucket `[0, 1612)` của
chuỗi đó.**

Ba lý do:

1. **Đó là thứ có thật khi triển khai.** Một máy mới trong datacenter đích luôn có
   lịch sử của chính nó; giả định "không biết gì về máy đích" là giả định không ai
   gặp trong vận hành.
2. **Nó vẫn không nhìn vào test.** Cửa sổ `[0, 1612)` là quá khứ so với
   `[1957, 2304)`, đúng nguyên tắc chống rò rỉ đã áp ở QĐ-013 điểm 1.
3. **Nó tách đúng thứ cần tách.** Câu hỏi của RQ3 là *"hình dạng biến động có
   transfer không"*, và để hỏi được câu đó thì mức tải phải bị loại **ở cả hai đầu**.
   Dùng thống kê nguồn áp lên chuỗi đích thì mức tải của đích vẫn còn nguyên.

**Hệ quả bắt buộc cho cách phát biểu.** RQ3 không được phát biểu là *"zero-shot
transfer"*. Phát biểu đúng là: *"động lực học có transfer được không, khi mỗi chuỗi
đích được chuẩn hoá bằng lịch sử của chính nó"*. Ghi vào Discussion và Limitations.

N2 không có vấn đề này: sai phân `y_{t+h} − y_t` không cần thống kê nào.

### 2. Đặc trưng **được biến đổi theo** target, trừ bốn đặc trưng lịch

19 đặc trưng đều dẫn xuất từ `y`. Nếu chỉ chuẩn hoá **target** mà giữ `lag_*`,
`roll_*`, `diff_1` ở thang gốc thì **mức tải vẫn vào model qua đặc trưng**, và N1
không bỏ được đúng cái nó sinh ra để bỏ.

**Quyết định: biến đổi chuỗi `y` TRƯỚC, rồi sinh lại 19 đặc trưng từ chuỗi đã biến
đổi.** Bốn đặc trưng lịch (`hour_sin`, `hour_cos`, `dow_sin`, `dow_cos`) **giữ
nguyên** — chúng đã nằm trong `[−1, 1]` và không mang thang tải.

Vì sao sinh lại chứ không nhân `mu`/`sd` vào cột có sẵn: với N1 hai cách tương đương
(z-score là affine nên `roll_mean` của z bằng z của `roll_mean`), nhưng với **N2 thì
không** — `roll_std` của chuỗi sai phân khác hẳn `roll_std` của chuỗi gốc. Dùng một
đường đi duy nhất cho cả ba chế độ thì không phải nhớ ngoại lệ.

**Hệ quả:** `data/features/` nhân ba, thành `{env}_{mode}_h{h}.parquet`. Luật dòng hợp
lệ của mục 8 giữ nguyên, áp trên chuỗi đã biến đổi. **Số dòng của N0 phải khớp tuyệt
đối chín neo của GĐ2/GĐ3** — nếu lệch thì đường sinh đặc trưng đã đổi, dừng truy nguyên.

### 3. Siêu tham số **dùng lại** của GĐ3, không dò lại

Mục 9 đòi chọn siêu tham số trên validation. GĐ3 đã làm đúng thế cho từng môi trường.

**Quyết định: GĐ4 dùng lại siêu tham số đã chốt ở GĐ3 theo từng môi trường NGUỒN,
không chạy lại rolling-origin.**

Đo được từ GĐ3, nơi dò siêu tham số chiếm **82%** tổng thời gian máy:

| | ước tính cho cả 5 model ML |
|---|---|
| Dùng lại siêu tham số GĐ3 | **≈ 5,9 giờ** |
| Dò lại cho từng chế độ | **≈ 32,9 giờ** |

Đây là quyết định **khai báo trước**, không phải lối tắt phát hiện giữa chừng. Hạn chế
đi kèm phải nêu trong Limitations: siêu tham số được chọn dưới chế độ **N0**, nên với
N1 và N2 nó có thể không còn tối ưu — cộng thêm cảnh báo ở `gate-gd3.md` mục 5.5 rằng
vùng validation của E1 dễ hơn test hẳn, nên E1-làm-nguồn thừa hưởng chỗ yếu đó.

### 4. Ba baseline là **mốc cố định của môi trường đích**, giống nhau ở cả ba chế độ

Ba baseline không huấn luyện nên "transfer" không có nghĩa với chúng. Chúng có mặt
trong bảng TN-B để làm **mốc**: một model transfer chỉ đáng quan tâm khi nó hơn được
baseline chạy ngay tại môi trường đích.

**Quyết định: tính ba baseline một lần trên tập test của môi trường đích, ở thang CPU%
gốc, và lặp lại cùng con số đó ở cả ba bảng N0/N1/N2.** Con số này **chính là** bảng
baseline của GĐ3 — không tính lại.

Riêng `naive` dưới N2 có một mơ hồ phải đóng: `Δ̂ = 0` (ra đúng persistence) hay
`Δ̂ = Δ_t` (thành model drift)? **Chốt `Δ̂ = 0`**, vì đó là thứ làm N2 so được với N0.

### 5. Ba bất biến làm phép kiểm bắt buộc

`giai-thich-chuan-hoa.md` mục 4 nêu một. Thực ra có **ba**, đều suy ra từ tính affine
và đều chạy được **trước khi có bất kỳ model nào**:

| Bất biến | Vì sao đúng |
|---|---|
| `naive` ở N0 ≡ `naive` ở N1, sau khi map ngược | z-score là affine, persistence bất biến dưới affine |
| **`ma6` ở N0 ≡ `ma6` ở N1** | trung bình của z là z của trung bình — cũng affine |
| **`naive` ở N2 với `Δ̂ = 0` ≡ `naive` ở N0** | `ŷ = y_t + 0 = y_t` |

Cả ba phải **trùng đến ít nhất 9 chữ số thập phân**. Lệch thì code sai ở đúng một
trong ba chỗ mục 5 của tài liệu chuẩn hoá liệt kê: quên map ngược, dùng thống kê toàn
chuỗi thay vì cửa sổ train, hoặc áp `mu`/`sd` của chuỗi này lên chuỗi khác.

Đây là chỗ **rẻ nhất** để bắt lỗi chuẩn hoá — chỗ `research-plan.md` gọi là *"dễ sai
nhất toàn dự án"* — nên chúng vào `tests/test_normalize.py` **trước** khi chạy model.

### Tập đánh giá, nói cho hết

Mọi con số TN-B đo trên **đúng tập test của môi trường đích**, `[1957, 2304)`, với
cùng luật purge của QĐ-013 điểm 2. Nhờ vậy bảng TN-B đặt cạnh bảng TN-A đọc được ngay:
cùng chuỗi, cùng dòng, cùng chỉ số.

**Hệ quả.**

1. `scripts/reference_gd4.py` hiện thực năm quy ước này và sinh
   `results/tables/reference_gd4.json` — neo của cổng GĐ4.
2. `docs/protocol.md` mục 14 nhận mục con trỏ về đây.
3. `config/split.yaml` đã khai `normalize_modes: [N0, N1, N2]` và
   `fit_stats_on: train_only`; QĐ này nói rõ *train của ai*.
4. `research-log/gate-gd4.md` và `research-log/brief-gd4-b.md` neo vào đây.

### Bổ sung 2026-09-11 — GĐ4 làm hai phiên tách bạch

QĐ-014 điểm 3 khuyến nghị *"phần hiện thực nên do một phiên khác làm, và phiên đó không
đọc thước đo"*, nhưng GĐ3 không làm được — hậu quả là `E1_830`: hai bản cùng viết
`ss_tot == 0`, khớp nhau ở 378/405 ô mà **cả hai cùng sai** ở 27 ô còn lại. Loại A khi
ấy không bắt được gì; chỉ loại C mới bắt được kiểu lỗi đó.

**GĐ4 làm được.** Phiên A ngày 2026-09-11 viết thước đo, hồ sơ cổng, phiếu giao việc và
công cụ kiểm; phiên hiện thực là **phiên khác**, và không đọc bốn tệp:

| Tệp | Vì sao |
|---|---|
| `scripts/reference_gd4.py` | thước đo độc lập |
| `results/tables/reference_gd4.json` | đáp án |
| `scripts/_moi_normalize_gd4.py` | một bản `normalize.py` đúng, trọn vẹn |
| `scripts/check_gd4.py` | **chạy được, không đọc** — loại C bày cách dựng ba bất biến |

Kèm một chỗ siết mà QĐ-014 đã đề xuất và GĐ3 chưa làm: bản mồi `normalize.py` của loại
C **tách khỏi `tests/`** ra `scripts/_moi_normalize_gd4.py`, có banner cảnh báo ở dòng
đầu. Ở GĐ3, bản mồi `metrics.py` nằm ngay trong `tests/test_check_gd3.py`.

Nhờ đó loại A của GĐ4 lấy lại **đầy đủ** sức mạnh mà GĐ1 và GĐ2 từng có.
