# 2026-09-07 — Dựng thước đo cổng GĐ1, phát hiện khuyết tật protocol mục 6

**Người thực hiện:** A
**Giai đoạn:** GĐ1 (phần A, làm trước khi B nộp)
**Thời lượng:** ~2 giờ

## Mục tiêu phiên
B đã qua 12/12 môi trường, GĐ0 đóng. Chuẩn bị phần việc của A cho GĐ1: dựng thước
đo để nghiệm thu sản phẩm của B.

## Đã làm
- Đóng cổng GĐ0
- Viết `scripts/reference_gd1.py` — bản hiện thực độc lập của protocol mục 5–7
- Chạy tham chiếu cho cả ba môi trường
- Viết `docs/gate-gd1.md` — hồ sơ cổng
- Ghi QĐ-008 ở trạng thái đề xuất
- Bổ sung phần A cho GĐ1 trong `research-plan.md`, phần này trước đây thiếu hẳn

## Phát hiện

### 1. Điều kiện qua cổng GĐ1 vốn không dùng được

Kế hoạch ghi "A đối chiếu bảng của B với `2026-08-30-tham-dinh-du-lieu.md`". Nhưng
số liệu ngày 30-08 đo trên mẫu ngẫu nhiên 150–250 VM, chưa lọc, chưa cắt cửa sổ 8
ngày. B sẽ nộp số trên toàn bộ dữ liệu đã áp đủ quy tắc. Hai bên đo hai thứ khác
nhau.

Đây đúng là lỗi mà `tu-bai-cu-den-bai-nay.md` mục 3 phân tích, lần này xuất hiện
trong chính kế hoạch của A. Đã thay bằng bản hiện thực độc lập.

### 2. Protocol mục 6 bước 6 phá huỷ dữ liệu — chặn GĐ1

Quy tắc "còn thiếu thì cắt chuỗi tại đó" xoá phần lớn E2 và gần như toàn bộ E3.

| Môi trường | Tỉ lệ NaN | Luật hiện tại giữ | Phương án đề xuất giữ |
|---|---|---|---|
| E1 | 0,00% | 100% | 98,4% |
| E2 | 0,43% | **20,9%** | **94,5%** |
| E3 | 12,11% | **1,1%** | **34,9%** |

Nguyên nhân: mục 6 xếp lọc chuỗi ở bước 5, điền khuyết ở bước 6. Bộ lọc độ dài chạy
trước khi cắt nên không bắt được chuỗi bị cắt cụt sau đó.

E2 chỉ có 0,43% NaN nhưng mất 79% dữ liệu vì lỗ hổng đi thành cụm 8–12 điểm liên
tiếp; 37/40 chuỗi mẫu có ít nhất một cụm, lần đầu quanh vị trí 480.

**Điểm nguy hiểm nhất: bảng tổng kết không lộ ra.** E3 báo giữ 99,6% số chuỗi trong
khi độ dài trung vị chỉ còn 26 trên tối đa 2.304. Nếu chỉ nhìn cột "tỉ lệ giữ" thì
cổng được cho qua và GĐ3, GĐ4 chạy trên dữ liệu hỏng.

Đã thêm cột "độ dài trung vị" vào danh sách cột bắt buộc của bảng B nộp.

### 3. Hai điểm mơ hồ trong protocol

- Cửa sổ 8 ngày tính từ điểm đầu của từng chuỗi hay mốc sớm nhất của toàn môi
  trường? A tạm dùng từng chuỗi.
- Ngưỡng 2.000 điểm mất nghĩa sau khi cắt cửa sổ: tối đa chỉ còn 2.304 điểm nên
  ngưỡng thực chất là yêu cầu độ phủ 86,8%.

## Số liệu tham chiếu (theo luật hiện tại, chỉ dùng để chứng minh khuyết tật)

| Chỉ số | E1 | E2 | E3 |
|---|---|---|---|
| Chuỗi vào | 1.250 | 500 | 500 |
| Loại vì độ dài | 32 | 0 | 1 |
| Loại vì gần chết | 473 | 198 | 1 |
| Chuỗi còn lại | 745 | 302 | 498 |
| Tỉ lệ giữ | 59,6% | 60,4% | 99,6% |
| Độ dài trung vị | 2.304 | 484 | 26 |
| Mẫu clip trên 100 | 319.082 (2,84%) | 95.137 (2,19%) | 0 |
| Target mean | 13,88 | 8,59 | 30,15 |
| Target p50 | 1,78 | 1,73 | 29,78 |

Tệp: `results/tables/reference_E1.json`, `reference_E2.json`, `reference_E3.json`.

## Quyết định
- QĐ-008 ghi ở trạng thái **đề xuất**, `protocol.md` **chưa sửa**. Đây là quyết định
  khoa học, phải do A duyệt tường minh.

## Vướng mắc
QĐ-008 đang chặn. B không nên viết `filter.py` trước khi chốt, vì quy tắc lọc sẽ đổi.

## Việc tiếp theo
- [ ] A duyệt hoặc bác QĐ-008
- [ ] Chốt hai điểm mơ hồ
- [ ] Sinh lại tham chiếu sau khi chốt
- [ ] A dựng venv ghim để tham chiếu cùng môi trường với B

## File sinh ra
- `scripts/reference_gd1.py`, `docs/gate-gd1.md`
- `results/tables/reference_E{1,2,3}.json`
- Cập nhật `docs/decisions.md` (QĐ-008), `docs/research-plan.md`
