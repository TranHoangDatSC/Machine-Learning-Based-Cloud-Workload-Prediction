# 2026-09-07 — Chốt ghim môi trường, soạn lệnh cài cho B

**Người thực hiện:** A
**Giai đoạn:** GĐ0 (đóng cổng)
**Thời lượng:** ~30 phút

## Mục tiêu phiên
Xử lý ô còn treo của cổng GĐ0: môi trường. A chốt hướng ghim đúng phiên bản và soạn
lệnh cài chính xác cho máy Linux Mint của B.

## Đã làm
- Chốt QĐ-007: ghim đúng phiên bản, không hạ chuẩn theo máy
- Xác định ràng buộc Python 3.10–3.12 và lý do của cả trần lẫn sàn
- Thêm phần đầu `requirements.txt` ghi rõ ràng buộc và cách xác minh
- Viết `tests/test_env.py`, chạy được cả standalone lẫn pytest
- Viết README mục 9 Cách 1 dành riêng cho Linux Mint, kèm bảng lỗi hay gặp

## Số liệu thu được

Chạy `tests/test_env.py` trên máy A (Windows):

| Chỉ số | Giá trị |
|---|---|
| Python | 3.13.13 — **ngoài khoảng 3.10–3.12** |
| venv | Không, đang dùng Python toàn cục |
| Gói khớp | **0/12** |
| Thiếu hẳn | `pyarrow`, `xgboost`, `lightgbm`, `tqdm` |
| Lệch phiên bản | 8 gói còn lại |

## Phát hiện

**Máy của A cũng không đạt chuẩn.** Python 3.13.13 nằm ngoài trần 3.12. Trước đây
mặc định rằng chỉ máy B có vấn đề, nhưng script cho thấy cả hai máy đều lệch. A không
chạy thí nghiệm nên việc này không chặn tiến độ, nhưng đã ghi vào QĐ-007 mục hệ quả:
nếu A cần chạy lại để đối chiếu số của B thì phải dựng venv cùng chuẩn, nếu không sẽ
so hai kết quả sinh ra từ hai môi trường khác nhau — đúng loại lỗi mà cả dự án đang
tránh.

**Ràng buộc Python trước đây chưa được khai ở đâu cả.** `requirements.txt` chỉ ghim
gói, không ghim Python. Đó là lỗ hổng thật: cùng một `requirements.txt` cài trên
3.13 sẽ hoặc lỗi, hoặc pip tự lùi về phiên bản khác mà không ai để ý. Đã bổ sung.

## Quyết định
- QĐ-007 → `docs/decisions.md`
- Cổng GĐ0 phần môi trường chỉ đóng khi `python tests/test_env.py` ra 12/12

## Việc tiếp theo
- [ ] B chạy khối lệnh ở README mục 9 Cách 1, báo lại kết quả `test_env.py`
- [ ] Ra 12/12 thì đóng cổng GĐ0, bắt đầu GĐ1 với đủ chín mục checklist

## File sinh ra
- `tests/test_env.py`
- Cập nhật `requirements.txt`, `README.md` mục 9, `docs/decisions.md`
