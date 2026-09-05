# Từ hai bài cũ đến bài này

**Dùng để:** nối những gì đã quen từ hai nghiên cứu trước sang bài toán hiện tại.
**Đọc cùng:** `protocol.md`, `giai-thich-chuan-hoa.md`.

Hai bài trước — bài HJS về ví điện tử và báo cáo đồ án về gian lận thẻ — đã dựng
được nhiều thói quen tốt: giải thích domain trước khi vào thuật toán, bảng siêu
tham số luôn có cột lý do, phần Hạn chế viết thật.

Tài liệu này làm hai việc. Một là bắc cầu: khái niệm cũ tương ứng với cái gì trong
bài mới. Hai là chỉ ra chỗ **phép bắc cầu đó gãy** — vì mỗi lần một khái niệm được
mang sang bài toán khác, nó thường mang theo một giả định mà không ai để ý.

Cách đọc: mỗi mục có ba phần — *Chỗ giống*, *Chỗ phép so sánh gãy*, *Bản chất*.

---

## 1. Từ phân loại giao dịch sang dự đoán chuỗi thời gian

### Chỗ giống
Vẫn `fit` rồi `predict`. Vẫn chia train/test. Vẫn Random Forest, XGBoost — đúng
những model đã dùng trong báo cáo đồ án.

### Chỗ phép so sánh gãy

Trong bài cũ, mỗi dòng là một giao dịch **độc lập**. Giao dịch thứ 4.000.000 không
phụ thuộc giao dịch thứ 3.999.999. Vì vậy `train_test_split` có `shuffle=True` và
`stratify=isFraud` là **hoàn toàn đúng** — thậm chí là cách làm chuẩn, vì nó bảo
toàn tỉ lệ lớp ở cả hai tập.

Trong bài này, cùng dòng lệnh đó sẽ **phá huỷ toàn bộ nghiên cứu**.

```text
Bai cu — giao dich doc lap
  [g1][g2][g3][g4][g5][g6]     xao tron -> van hop le
   ^binh thuong    ^gian lan

Bai moi — chuoi thoi gian
  y1 -> y2 -> y3 -> y4 -> y5    xao tron -> mo hinh nhin thay tuong lai
        (moi diem phu thuoc diem truoc)
```

Nếu xáo trộn, điểm lúc 10:15 có thể rơi vào tập train trong khi điểm 10:10 rơi vào
test. Model học từ tương lai để đoán quá khứ. Kết quả sẽ rất đẹp và hoàn toàn vô giá
trị.

### Bản chất

Thứ quyết định không phải thuật toán, mà là **giả định về tính độc lập của mẫu**.

Cùng một `RandomForestClassifier`, cùng một cách gọi hàm, nhưng đổi giả định thì
cách chia dữ liệu phải đổi theo. Khi mang một kỹ thuật từ bài toán này sang bài
toán khác, câu hỏi đầu tiên luôn là: *giả định nào đi kèm kỹ thuật này, và giả định
đó còn đúng không?*

Đây là lý do `protocol.md` mục 9 viết in đậm **"Tuyệt đối không shuffle"** — không
phải vì shuffle xấu, mà vì giả định đã đổi.

---

## 2. Từ AUC-ROC và F1 sang MAE và MASE

### Chỗ giống
Đều là con số đo chất lượng model. Càng tốt càng đáng tin.

### Chỗ phép so sánh gãy

Bảng 3 của báo cáo đồ án có một dòng đáng để dừng lại rất lâu:

| Mô hình | F1-Score | AUC-ROC | Báo nhầm (FP) |
|---|---|---|---|
| Decision Tree | 0,9912 | 0,9939 | 24 |
| **Naïve Bayes** | **0,0066** | **0,9567** | **493.089** |

Naïve Bayes có **AUC 0,9567** — nghe như một model rất tốt, tốt hơn phần lớn model
trong các paper. Nhưng F1 của nó là **0,0066**, và nó báo nhầm gần **nửa triệu**
giao dịch.

Cùng một model. Hai chỉ số. Hai kết luận trái ngược hoàn toàn.

Không phải chỉ số nào sai. Chúng đo hai thứ khác nhau:

```text
AUC-ROC  do kha nang XEP HANG o MOI nguong
         "neu lay diem so cua model, giao dich gian lan co xep tren khong?"
         --> Naive Bayes xep hang kha tot: 0,9567

F1       do mot DIEM VAN HANH cu the
         "voi nguong dang dung, model bao dung bao nhieu?"
         --> Naive Bayes o nguong do: tham hoa
```

Model xếp hạng tốt nhưng đặt ngưỡng sai vẫn vô dụng trong thực tế.

### Bản chất

Một chỉ số không đo "model tốt". Nó đo **"model tốt theo nghĩa nào"**. Đổi nghĩa thì
thứ hạng đảo lộn.

Sang bài này, cái bẫy đổi hình dạng nhưng cùng bản chất: MAE thấp **không** có nghĩa
model tốt, nếu naive persistence cũng đạt MAE thấp tương đương. Trên chuỗi CPU 5
phút, persistence rất mạnh — đo được 5,76 trên Alibaba.

Vì vậy `protocol.md` mục 12 lấy **MASE** làm chỉ số chính khi so sánh giữa các môi
trường: MASE chia MAE của model cho MAE của naive, nên nó trả lời thẳng câu
*"model có hơn được cái không học gì không"*.

Cũng có thể hiểu MASE sinh ra để loại bỏ "ảo tưởng" của MAE:
- Nếu $\text{MASE} < 1$: Mô hình ML tốt hơn mô hình ngây thơ (chủ động học được tri thức).
- Nếu $\text{MASE} = 1$: Mô hình ML chỉ bằng cái "không học gì" (Naive).
- Nếu $\text{MASE} > 1$: Mô hình ML tệ hơn cả cái "không học gì".

Và cũng vì vậy mục 11 bắt **chạy baseline trước tiên**, trước mọi model ML.

---

## 3. Bài học lớn nhất: Bảng 6 của bài HJS

Đây là mục quan trọng nhất của tài liệu này, vì lỗi trong Bảng 6 **cùng loại** với
cái bẫy mà cả protocol hiện tại đang được thiết kế để tránh.

### Bảng 6 đã so sánh thế nào

| | Bài HJS | Gillespie | S. Ounacer |
|---|---|---|---|
| Bộ dữ liệu | Paysim 6.362.621 | Paysim 6.362.621 | CCFD 284.807 |
| Tập thử nghiệm | 30% | 20% | 30% |
| **Đo trên** | **Toàn bộ giao dịch** | **1000 giao dịch bất thường nhất** | Toàn bộ |
| AUC-ROC | 0,9160 | 0,830 / 0,845 / 0,784 | 0,9168 |

Bài viết kết luận: *"vượt trội đáng kể so với các mốc cấu hình của tác giả này"*, và
thêm rằng đạt AUC cao hơn với ít dữ liệu huấn luyện hơn *"là minh chứng cho sự tối
ưu hóa thành công các siêu tham số"*.

### Chỗ phép so sánh gãy

Ba vấn đề, xếp theo mức nghiêm trọng:

**Một — khác tập đánh giá.** Đây là vấn đề lớn nhất. Con số 0,9160 đo trên *toàn bộ*
giao dịch. Ba con số của Gillespie đo trên *1000 giao dịch bất thường nhất*.

Đó là hai bài toán khác nhau. Phân biệt gian lận với toàn bộ dân số giao dịch — nơi
99,87% là giao dịch bình thường và phần lớn rất dễ loại — dễ hơn nhiều so với phân
biệt gian lận trong nhóm 1000 ca *đã khó nhất*. Nhóm sau là phần đuôi phân phối, nơi
mọi model đều vật lộn.

Nói cách khác: 0,9160 và 0,830 không phải hai điểm số của cùng một kỳ thi.

**Hai — khác tỉ lệ chia.** 30% so với 20%. Nhỏ hơn nhưng vẫn làm kết luận yếu đi.

**Ba — khác cả bộ dữ liệu.** Cột S. Ounacer dùng CCFD, 284.807 dòng dữ liệu thật.
Bài viết có thừa nhận điều này, nhưng rồi vẫn rút ra kết luận về năng lực: *"Việc
duy trì độ chính xác cao trên một tập dữ liệu khổng lồ chứng minh khả năng mở rộng
vượt trội"*. Dữ liệu lớn hơn không đồng nghĩa khó hơn — Paysim là mô phỏng và, như
chính báo cáo đồ án đã tự nhận xét, *"quá sạch và có tính quy luật cao"*.

Còn câu *"AUC cao hơn với ít dữ liệu hơn chứng minh siêu tham số tối ưu"* là một suy
luận **nhân quả** rút ra từ một so sánh **không kiểm soát**. Muốn kết luận đó đứng
được thì phải chạy đúng cấu hình của Gillespie trên đúng tập của mình rồi mới đổi
siêu tham số — tức là kiểm soát mọi thứ trừ đúng cái đang muốn đo.

### Bản chất

> Hai con số chỉ so được với nhau khi chúng **đo cùng một thứ, trên cùng một tập,
> theo cùng một giao thức**. Thiếu một trong ba, phép so là vô nghĩa — dù con số có
> đẹp đến đâu.

### Nối thẳng sang bài này

Cái bẫy trong Bảng 6 và cái bẫy ở RQ3 là **cùng một cái**, chỉ mặc áo khác:

| | Bảng 6 bài HJS | RQ3 bài này |
|---|---|---|
| Con số | AUC 0,9160 vs 0,830 | MAE 28,64 khi E1 → E3 |
| Trông như | Model của ta tốt hơn | Transfer thất bại |
| Thực chất đang đo | Hai tập đánh giá khác nhau | Hai mức tải khác nhau |
| Kết luận đúng ra | Chưa so được | Chưa kết luận được gì |
| Cách sửa | Chạy lại cùng giao thức | Chuẩn hoá trước khi transfer |

Bằng chứng cho cột phải: một **hằng số** bằng mức tải trung bình của E1, áp lên E3,
cũng cho MAE 28,64. Không model, không đặc trưng, không huấn luyện. Chi tiết trong
`giai-thich-chuan-hoa.md`.

Nếu Bảng 6 từng lọt qua được thì đó là vì không ai hỏi *"hai con số này có đo cùng
một thứ không"*. Ở bài này, câu hỏi đó được cài sẵn vào protocol mục 14 để không thể
bỏ qua.

---

## 4. Từ errorBalance sang lag features

### Chỗ giống
Cả hai đều là feature engineering: tạo biến mới từ biến có sẵn để model học tốt hơn.
`errorBalanceOrig = (oldbalanceOrg − newbalanceOrig) − amount` là một đặc trưng
thông minh, và báo cáo đúng khi coi nó là đóng góp phương pháp luận.

### Chỗ phép so sánh gãy

Báo cáo đồ án ghi hai quan sát, ở hai chỗ cách xa nhau:

1. F1-Score đạt **0,9912**, Recall **0,9970**, chỉ 24 ca báo nhầm.
2. *"hơn 95% trường hợp gian lận đều là dẫn đến cạn kiệt tài khoản gửi tiền"*.

Nối hai câu này lại thì ra một kết luận mà báo cáo chưa rút: Paysim **sinh** gian lận
bằng một quy tắc, và quy tắc đó là rút cạn tài khoản. Đặc trưng `isOrigEmptyAfterTx`
vì thế gần như là **nhãn được viết lại dưới dạng khác**.

Con số 0,9912 phần lớn không đo năng lực phát hiện gian lận. Nó đo **năng lực học
thuộc quy tắc của trình mô phỏng**.

Báo cáo có nhận ra vấn đề ở tầng hiện tượng — *"kết quả này vẫn chủ yếu mang nặng
tính lý thuyết"* — nhưng chưa chỉ ra cơ chế. Biết cơ chế thì phần Hạn chế mạnh hơn
hẳn, và người phản biện sẽ đánh giá cao thay vì bắt lỗi.

### Bản chất

Một đặc trưng mạnh **bất thường** luôn phải bị chất vấn: *nó có đang mã hoá nhãn
không?* Điểm số gần hoàn hảo trên dữ liệu mô phỏng hầu như luôn là dấu hiệu của rò
rỉ, không phải dấu hiệu của thành công.

Ở bài này, rò rỉ mặc áo khác — kín đáo hơn nhiều:

```text
SAI                                    DUNG
rolling_mean(window=6)                 rolling_mean(window=6).shift(1)
  bao gom chinh diem hien tai            chi dung qua khu
  --> dac trung chua san dap an          --> khong nhin thay tuong lai
```

Và một dạng thứ hai, tinh vi hơn: tính `mu`, `sd` để chuẩn hoá trên **toàn chuỗi**
thay vì chỉ cửa sổ train. Loại này không làm chương trình báo lỗi, chỉ làm số liệu
đẹp lên. Đó là lý do `protocol.md` mục 8 yêu cầu mọi thống kê rolling chỉ tính trên
quá khứ, và mục 14 yêu cầu thống kê chuẩn hoá chỉ tính trên train.

---

## 5. Điều cả hai bài cũ đều thiếu: baseline

Không bài nào báo cáo một baseline tầm thường.

Với Paysim, một quy tắc thuần tuý — *"cảnh báo mọi giao dịch TRANSFER hoặc CASH_OUT
làm cạn tài khoản gửi"* — nhiều khả năng đạt Recall rất cao, vì đó gần đúng là quy
tắc sinh dữ liệu. Nếu quy tắc một dòng đó đạt F1 chẳng hạn 0,95, thì con số 0,9912
của Decision Tree mang ý nghĩa hoàn toàn khác so với khi đọc nó một mình.

Không có mốc so, một con số không có nghĩa. Nó chỉ có nghĩa **so với cái gì đó**.

Đây là lý do `protocol.md` mục 11 liệt kê ba baseline và ghi *"Mốc bắt buộc. Mọi con
số đều so với nó"*, và mục 3 của lộ trình bắt chạy baseline **trước tiên**, trước
Linear Regression, trước Random Forest, trước tất cả.

---

## 6. Bảng đối chiếu

| Khái niệm | Bài cũ | Bài này | Chỗ dễ mang nhầm giả định |
|---|---|---|---|
| Đơn vị dữ liệu | Một giao dịch | Một điểm thời gian của một chuỗi | Các điểm **không** độc lập |
| Nhãn | `isFraud` 0/1 có sẵn | Không có nhãn; target là giá trị tương lai của chính chuỗi | Tự sinh nhãn bằng cách dịch chuỗi |
| Chia dữ liệu | Stratified + shuffle | Cắt theo thời gian, không shuffle | Shuffle ở đây là rò rỉ |
| Mất cân bằng lớp | Vấn đề trung tâm (0,1291%) | Không tồn tại | Nhưng có vấn đề tương đương: 42,5% chuỗi gần chết |
| Chỉ số | F1, AUC-ROC | MAE, RMSE, SMAPE, **MASE** | AUC cao vẫn có thể vô dụng — xem mục 2 |
| Baseline | Không có | Naive, MA, Seasonal naive — bắt buộc | Thiếu baseline thì con số không có nghĩa |
| Feature engineering | errorBalance | lag, rolling, calendar | Rolling phải `.shift(1)` |
| Rò rỉ | Đặc trưng mã hoá nhãn | Nhìn thấy tương lai qua rolling hoặc chuẩn hoá | Cùng bản chất, khác hình dạng |
| So với bài khác | Bảng 6, khác giao thức | Chỉ so trong cùng giao thức | Xem mục 3 |

---

## 7. Điều **không** nên khái quát hoá từ tài liệu này

Phần này quan trọng ngang phần trên. Rút bài học quá rộng cũng sai như không rút gì.

**Đừng kết luận "so sánh với nghiên cứu khác là vô nghĩa".**
Nó có nghĩa, và trong paper thì gần như bắt buộc phải có. Vấn đề của Bảng 6 không
phải là *có so*, mà là *so mà không nêu điều kiện, rồi rút kết luận mạnh hơn mức dữ
liệu cho phép*. Cách làm đúng: vẫn để bảng đó, nhưng ghi rõ "không so trực tiếp được
vì khác tập đánh giá", và hạ mức phát biểu từ "vượt trội" xuống "cùng khoảng".

**Đừng kết luận "chỉ số cao là đáng ngờ".**
Có bài toán vốn dễ, và điểm cao là thật. Dấu hiệu đáng ngờ không phải bản thân con
số cao, mà là **con số cao đi kèm một đặc trưng liên quan chặt tới cơ chế sinh nhãn**.
Hỏi cơ chế, đừng hỏi độ lớn.

**Đừng kết luận "Decision Tree tốt hơn XGBoost".**
Báo cáo đồ án cho thấy DT thắng trên Paysim. Điều đó đúng **trên Paysim, với bộ đặc
trưng đó, ở ngưỡng đó**. Trên dữ liệu nhiễu hơn thứ hạng thường đảo. Cũng vì vậy bài
này dùng kiểm định Wilcoxon: chênh lệch nhỏ giữa hai model rất có thể chỉ là nhiễu.

**Đừng kết luận "dữ liệu mô phỏng thì vô dụng".**
Paysim là lựa chọn hợp lý khi không tiếp cận được dữ liệu thật, và cả hai bài đều nêu
lý do đúng. Vấn đề chỉ là **mức phát biểu**: kết quả trên mô phỏng chứng minh tính
khả thi của quy trình, không chứng minh hiệu năng trong thực tế.

**Đừng biến "phải có baseline" thành nghi thức.**
Baseline có ích khi nó là *đối thủ nghiêm túc* của model. Naive persistence trên chuỗi
CPU là đối thủ thật, vì nó thực sự mạnh. Một baseline dựng lên cho có, yếu sẵn, chỉ
làm bảng kết quả đẹp lên một cách giả tạo — đó là một dạng tự lừa khác.

---

## 8. Một câu để mang theo

Cả bốn cái bẫy ở trên đều là một câu hỏi duy nhất, hỏi ở bốn chỗ khác nhau:

> **Con số này thật ra đang đo cái gì?**

Bảng 6 hỏi câu đó thì thấy hai tập đánh giá khác nhau. F1 0,9912 hỏi câu đó thì thấy
quy tắc của trình mô phỏng. AUC 0,9567 của Naïve Bayes hỏi câu đó thì thấy xếp hạng
chứ không phải quyết định. Và MAE 28,64 ở bài này hỏi câu đó thì thấy chênh lệch mức
tải.

Toàn bộ `protocol.md` chỉ là nỗ lực buộc phải trả lời câu hỏi đó **trước** khi nhìn
thấy kết quả, thay vì sau.
