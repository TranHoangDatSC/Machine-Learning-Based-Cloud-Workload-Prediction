# Giải thích mục 14 — Ba chế độ chuẩn hoá

**Dùng để:** A giảng cho B trước khi bắt đầu GĐ1.
**Liên quan:** `protocol.md` mục 14, `decisions.md` QĐ-005.

Đây là phần khó hiểu nhất của giao thức, và cũng là phần quyết định paper có đóng
góp thật hay không. Tài liệu này giải thích bằng số thật đo trên chính dữ liệu của
dự án, không dùng ví dụ giả định.

---

## 1. Vấn đề bằng một câu

Bitbrains và Alibaba chạy ở hai mức tải hoàn toàn khác nhau.

```text
Muc tai trung binh (sau khi loc theo protocol muc 6)

E1 Bitbrains  ####                                    11,3%
E3 Alibaba    ##############################          38,5%
                                                 chenh 27,3 diem
```

Nếu train model trên E1 rồi đem sang E3, model sẽ đoán quanh mức 11% trong khi thực
tế là 38%. Sai khoảng 27 điểm ở **mọi** dự đoán, bất kể model tốt đến đâu.

---

## 2. Thí nghiệm chứng minh

Câu hỏi đặt ra: con số MAE lớn khi transfer có thật sự nói lên điều gì về chất lượng
model không?

Bốn phép đo dưới đây chạy trên 833 chuỗi Alibaba đã lọc, horizon 1 bước, lấy trung
vị. Script: `research-log/scratch/demo-chuan-hoa.py`. Số liệu gốc lưu trong
`research-log/2026-09-05-giang-muc-14.md` phòng khi `scratch/` bị dọn.

| # | Bộ dự đoán | Học được gì | MAE trên E3 |
|---|---|---|---|
| **a** | Hằng số bằng mức tải trung bình của **E1** | **Không gì cả** | **28,64** |
| b | Hằng số bằng mức tải trung bình của chính E3 | Không gì cả | 10,48 |
| c | Naive persistence trong E3 (`ŷ = y_t`) | Không gì cả | 5,76 |
| d | Naive persistence sau z-score, map ngược | Không gì cả | 5,76 |

### Đọc bảng này

**Dòng (a) là điểm mấu chốt.** Con số 28,64 đạt được bởi **một hằng số**. Không có
model nào, không có đặc trưng nào, không có huấn luyện nào.

Nghĩa là nếu chạy transfer thô E1 sang E3 và thu được MAE khoảng 28, ta **không biết
được gì cả**: con số đó có thể đến hoàn toàn từ việc model đoán ở sai mức tải, chứ
không phản ánh việc model có học được quy luật biến động hay không.

Viết trong bài rằng "cross-environment transfer thất bại, MAE = 28,6" là một phát
biểu đúng nhưng rỗng. Phản biện chỉ cần hỏi: *"Một hằng số cũng cho 28,6. Vậy model
của bạn đóng góp gì?"*

**So (a) với (b):** đổi hằng số từ mức tải E1 sang mức tải E3, sai số rơi từ 28,64
xuống 10,48. Vậy **18,16 điểm — tức 63,4% của toàn bộ sai số — chỉ là chênh lệch mức
tải.** Phần này không liên quan gì đến chất lượng dự đoán.

**So với (c):** naive persistence, thứ không học gì và chỉ lặp lại giá trị trước đó,
đạt 5,76 — tốt gấp 5 lần cái gọi là "kết quả transfer".

---

## 3. Ba chế độ giải quyết vấn đề này thế nào

```text
Tin hieu workload
        │
        ├── MUC TAI (level)      moi truong nay chay o 38%, moi truong kia 11%
        │                        --> khac nhau, biet truoc duoc, khong thu vi
        │
        └── DONG LUC HOC         tang/giam ra sao, bien dong manh khong,
            (dynamics)           co chu ky khong
                                 --> day moi la cai dang hoi co transfer khong
```

| Chế độ | Target | Bỏ đi cái gì | Trả lời câu hỏi gì |
|---|---|---|---|
| **N0** | CPU% nguyên bản | Không bỏ gì | Đối chứng. Cho thấy transfer thô thất bại thế nào |
| **N1** | z-score từng chuỗi | Bỏ mức tải và biên độ | Hình dạng tương đối có transfer không |
| **N2** | Sai phân `y_{t+h} − y_t` | Bỏ mức tải, giữ biên độ tuyệt đối | Quy luật thay đổi có transfer không |

N0 **không phải** thứ bỏ đi. Nó là đối chứng bắt buộc: có N0 mới chứng minh được
rằng N1 và N2 thực sự cải thiện điều gì đó.

---

## 4. Bài kiểm tra bắt buộc cho B

Dòng (c) và (d) trong bảng trên **bằng nhau chính xác: 5,76**.

Đây không phải trùng hợp. z-score là phép biến đổi affine, còn persistence bất biến
dưới phép biến đổi affine. Cụ thể:

```text
z_t = (y_t - mu) / sd
du doan trong khong gian z:  z_hat = z_t
map nguoc:                   y_hat = z_t * sd + mu = y_t
```

Kết quả đúng bằng persistence trên thang gốc.

**Đây là bài kiểm tra đơn vị cho code chuẩn hoá của B.** Sau khi viết
`src/cwp/preprocess/normalize.py`:

- [ ] Chạy naive persistence ở chế độ N0, ghi lại MAE
- [ ] Chạy naive persistence ở chế độ N1, map ngược về thang gốc, ghi lại MAE
- [ ] Hai con số phải **trùng khớp đến ít nhất 6 chữ số thập phân**

Nếu lệch thì code sai ở một trong ba chỗ:
1. Quên map ngược về thang gốc trước khi tính chỉ số
2. Dùng `mu` và `sd` của toàn chuỗi thay vì chỉ cửa sổ train — **đây là rò rỉ dữ liệu**
3. Áp `mu`, `sd` của chuỗi này lên chuỗi khác

Đưa bài kiểm tra này vào `tests/test_normalize.py`.

---

## 5. Điều dễ làm sai nhất

**Thống kê chuẩn hoá của N1 chỉ được tính trên cửa sổ train.**

```text
SAI                                DUNG
mu, sd = toan bo chuoi             mu, sd = chi phan train
        │                                  │
        └── da nhin thay tuong lai          └── khong nhin thay tuong lai
```

Tính `mu` và `sd` trên toàn chuỗi nghĩa là đã dùng thông tin của tập test để chuẩn
hoá tập train. Kết quả sẽ đẹp bất thường và toàn bộ thí nghiệm B mất giá trị.

Đây là lỗi khó phát hiện vì nó không làm chương trình báo lỗi, chỉ làm số liệu tốt
lên. Dấu hiệu nhận biết: nếu N0 **không** thất bại nặng ở cặp Bitbrains và Alibaba
thì gần như chắc chắn có rò rỉ ở đâu đó — dừng lại truy nguyên, đừng đi tiếp.

---

## 6. Câu hỏi kiểm tra hiểu bài

B trả lời được cả bốn câu mà không mở lại tài liệu thì qua cổng GĐ0.

1. Vì sao con số MAE 28,64 khi transfer E1 sang E3 lại **không** chứng minh được
   rằng model kém?
2. Trong 28,64 đó, bao nhiêu phần trăm chỉ là chênh lệch mức tải? Con số này lấy ở
   đâu ra?
3. Vì sao naive persistence cho kết quả giống hệt nhau ở N0 và N1? Điều đó dùng để
   kiểm tra cái gì?
4. Nếu tính `mu` và `sd` trên toàn chuỗi thay vì chỉ phần train thì chuyện gì xảy ra,
   và làm sao phát hiện?

---

## 6b. Cái bẫy này bạn đã gặp một lần rồi

Bảng 6 của bài HJS so AUC 0,9160 của nhóm với 0,830 / 0,845 / 0,784 của Gillespie và
kết luận "vượt trội đáng kể". Nhưng con số của nhóm đo **trên toàn bộ giao dịch**,
còn ba con số kia đo **trên 1000 giao dịch bất thường nhất** — hai tập đánh giá khác
nhau, tức hai bài toán khác nhau.

Đó chính xác là cái bẫy ở đây, chỉ mặc áo khác:

| | Bảng 6 bài HJS | Mục 14 bài này |
|---|---|---|
| Trông như | Model của ta tốt hơn | Transfer thất bại |
| Thực chất đang đo | Hai tập đánh giá khác nhau | Hai mức tải khác nhau |
| Câu hỏi cứu được | Hai số này có đo cùng một thứ không? | Con số 28,64 này đo cái gì? |

Phân tích đầy đủ: `tu-bai-cu-den-bai-nay.md` mục 3.

---

## 7. Tóm tắt một câu để nhớ

> Transfer thô đo **chênh lệch mức tải**, thứ biết trước được mà không cần model.
> Chuẩn hoá rồi mới transfer thì mới đo được **quy luật biến động**, thứ chưa ai
> biết câu trả lời — và đó là lý do bài này đáng viết.
