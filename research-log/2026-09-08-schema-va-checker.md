# 2026-09-08 — Đặc tả schema và tự động hoá kiểm cổng GĐ1

**Người thực hiện:** A
**Giai đoạn:** GĐ1 (phần A)
**Thời lượng:** ~1,5 giờ

## Mục tiêu phiên
Bịt lỗ hổng đặc tả đang chặn B, và biến buổi nghiệm thu GĐ1 thành một lệnh.

## Đã làm
- Sửa đoạn conda trong README mục 9 mà B thêm ở nhánh `dev/phat`
- Đặc tả schema `data/processed/` và `data/catalog.parquet` — protocol mục 6b
- Viết `scripts/check_gd1.py` — kiểm cổng tự động
- Viết `tests/test_check_gd1.py` — test cho chính công cụ kiểm
- Cập nhật `gate-gd1.md` mục 4 và checklist GĐ1

## Phát hiện

**Lỗ hổng đặc tả đang chặn B.** Kế hoạch chỉ ghi "sinh `catalog.parquet`, một dòng
mỗi chuỗi". Không cột nào được nêu. Trong khi đó lệnh nghiệm thu tôi viết hôm qua
lại giả định các cột `series_id`, `env`, `valid_rows_h12`, `mean`. B đang code hôm
nay — nếu đặt tên cột khác thì lệnh kiểm gãy, và A với B lại đo hai thứ khác nhau.
Đã đặc tả 13 cột cho catalog, 5 cột cho processed.

**Đoạn conda của B đặt sai chỗ.** B chèn `conda activate ml-cwp` vào giữa luồng
venv, với chú thích "Tạo môi trường ảo". Làm theo đúng thứ tự sẽ chồng conda env lên
venv — đúng kiểu lỗi đã làm hỏng `.venv` của A hôm 07-09. Đã tách thành một nhánh
riêng "Dùng conda thay cho venv", kèm bước tạo env mà bản của B thiếu.

**Công cụ kiểm tự nó báo trượt oan.** Khi tự kiểm chứng, `check_gd1.py` báo TRƯỢT ở
tình huống catalog khớp hoàn toàn. Nguyên nhân: check bẫy Rnd chạy `.all()` trên mọi
chuỗi E2 kể cả chuỗi bị loại. Đã sửa thành chỉ bắt buộc với chuỗi được giữ, chuỗi bị
loại chỉ cảnh báo.

Nếu không tự kiểm chứng thì lỗi này sẽ nổ ra đúng lúc nghiệm thu, và nhiều khả năng
bị quy oan cho B.

## Kiểm chứng công cụ

`tests/test_check_gd1.py` sinh catalog giả lập từ chính số liệu tham chiếu:

| Tình huống | Kỳ vọng | Thực tế |
|---|---|---|
| Catalog khớp tham chiếu | ĐẠT | ĐẠT |
| Số dòng h=12 chỉ bằng 50% | TRƯỢT | TRƯỢT, bắt đúng mục |
| E2 thiếu tháng trong `series_id` | TRƯỢT | TRƯỢT, bắt đúng bẫy Rnd |
| Thiếu cột `n_interp` | TRƯỢT | TRƯỢT |

4 test xanh. Đây là quy tắc mới cho dự án: **công cụ cổng nào cũng phải có test
chứng minh nó phân biệt được đạt với trượt**, vì `test_env.py` đã hai lần báo đạt
trên môi trường hỏng.

## Quyết định
Không mở mục mới trong `decisions.md` — đây là bổ sung đặc tả và công cụ, không đổi
giao thức nghiên cứu.

## Việc tiếp theo
- [ ] B triển khai GĐ1 theo protocol mục 6b, chạy `check_gd1.py` tới khi ĐẠT
- [ ] A nghiệm thu bằng cùng lệnh đó

## File sinh ra
- `scripts/check_gd1.py`, `tests/test_check_gd1.py`
- Cập nhật `README.md`, `docs/protocol.md` (mục 6b), `docs/gate-gd1.md`,
  `docs/research-plan.md`
