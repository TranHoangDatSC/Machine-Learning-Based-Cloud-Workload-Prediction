# 2026-08-30 — Thẩm định dữ liệu và tái cấu trúc dự án

**Người thực hiện:** A (có agent hỗ trợ)
**Giai đoạn:** GĐ0
**Thời lượng:** ~3 giờ

## Mục tiêu phiên
Xác minh ba public cloud trace có đúng nguồn và dùng được cho bài toán dự đoán
workload không. Dựng lại cấu trúc thư mục dự án.

## Đã làm
- Kiểm tra schema thực tế của cả ba dataset, đối chiếu với tài liệu nguồn
- Loại bỏ hai dataset lấy nhầm ở vòng trước
- Đo phân phối target và đặc tính chuỗi trên mẫu ngẫu nhiên
- Quét toàn bộ tệp Alibaba để lấy số dòng và số máy chính xác
- Tái cấu trúc `dataset/` → `data/raw/`, dựng cây thư mục chuẩn

## Số liệu thu được

| Chỉ số | E1 fastStorage | E2 Rnd | E3 Alibaba |
|---|---|---|---|
| Số đơn vị | 1.250 VM | 500 VM × 3 tháng | 4.023 máy |
| Số dòng | 11.221.800 | 12.496.728 | 246.934.820 |
| Interval | 300 s | 300 s | ~10 s, không đều |
| CPU% trung vị | 0,84 | 1,07 | 37,0 |
| CPU% trung bình | 6,75 | 6,99 | 38,13 |
| Mẫu < 1% | 53,4% | 43,2% | 2,0% |
| Mẫu > 20% | 7,6% | 8,0% | 89,0% |
| Autocorr t-1 @5 phút | 0,675 | 0,644 | 0,781 |
| CPU% > 100 | 1,91% | 2,41% | 0% |
| VM dùng được sau lọc | 56,5% | 65,5% | 99,4% |

## Phát hiện

**Lệch mức tải nghiêm trọng.** Phân phối target của Bitbrains và Alibaba gần như
không giao nhau: trung vị 0,84–1,07% so với 37,0%. Transfer thô giữa hai môi trường
sẽ cho MAE ≈ 36 và kết luận "generalization thất bại" — đúng nhưng vô giá trị, vì
con số đó chỉ phản ánh chênh lệch mức tải trung bình, biết trước được mà không cần
train model nào.

**Nhưng động lực học thì so sánh được.** Autocorr bậc 1 trên lưới 5 phút của ba môi
trường nằm cùng vùng (0,644–0,781). Nghĩa là *hình dạng biến thiên* có khả năng
transfer, chỉ *mức tải* là lệch. Đây là cơ sở để tách hai thành phần và biến RQ3 từ
câu hỏi hiển nhiên thành câu hỏi thật.

**Hai dataset vòng trước lấy sai.**
- `borg_traces_data.csv` là dataset phân loại job failure (405.894 dòng event-level,
  nhãn nhị phân `failed`, `time` không sắp xếp, có sentinel `9223372036854775807`).
  Không dựng được chuỗi thời gian.
- `pai_group_tag_table.csv` chỉ có 5 cột metadata, không timestamp, không resource
  usage. Là bảng tag của GPU trace v2020.

**Bitbrains có giá trị vượt thang.** CPU% > 100 ở 1,91% (E1) và 2,41% (E2) số mẫu,
đỉnh 111,07%.

## Quyết định
- Loại Google trace khỏi đề tài → `docs/decisions.md#qd-001`
- Thay Alibaba GPU v2020 bằng `cluster-trace-v2018/machine_usage` → `docs/decisions.md#qd-002`
- Target chung là CPU% trên lưới 5 phút → `docs/protocol.md`
- RQ3 phải tách mức tải khỏi động lực học → `docs/protocol.md`
- Cắt scope: chỉ dùng Rnd 2013-8, mẫu 500 máy Alibaba, bỏ LSTM khỏi scope chính,
  gộp 3 thí nghiệm còn 2 → `docs/decisions.md#qd-003`

## Vướng mắc
Lệch đơn vị quan sát giữa E1/E2 (VM đơn lẻ) và E3 (máy vật lý gộp nhiều container)
chưa xử lý triệt để. Một phần chênh lệch autocorr đến từ đây chứ không phải từ bản
chất môi trường. Cần A quyết: nêu là Limitations, hay tải thêm `container_usage.csv`.

## Việc tiếp theo
- [ ] B đọc `docs/protocol.md` và xác nhận hiểu đúng giao thức
- [ ] B dựng parser cho hai định dạng (GĐ1)

## File sinh ra
- `data/raw/*/about.md`, `data/raw/*/explain.md` — mô tả nguồn và ghi chú tiền xử lý
- `docs/protocol.md`, `docs/research-plan.md`, `docs/decisions.md`, `docs/data-card.md`
