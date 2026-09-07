# 2026-09-07 — A review cổng GĐ0, làm rõ báo cáo "đã xong giai đoạn 1"

**Người thực hiện:** A
**Giai đoạn:** GĐ0 (cổng)
**Thời lượng:** ~1 giờ

## Mục tiêu phiên
B báo đã xong "giai đoạn 1". Đối chiếu báo cáo với bằng chứng thực tế trong repo
trước khi cho qua cổng.

## Kết luận

**B chưa xong GĐ1. B xong phần lớn GĐ0.** Đây là lệch cách gọi tên, không phải B
báo sai ý.

Chính log của B ghi rõ: tiêu đề "hoàn thành Giai đoạn 0", trường **Giai đoạn: GĐ0**,
và mục cuối "Việc tiếp theo (Bắt đầu Giai đoạn 1)" với ba ô còn trống. Vậy B hiểu
đúng vị trí của mình; chỉ khi báo miệng thì "giai đoạn 1" bị hiểu thành "giai đoạn
đầu tiên" thay vì mã GĐ1.

## Bằng chứng đã kiểm

| Hạng mục GĐ1 | Trạng thái thực tế |
|---|---|
| `src/cwp/io/bitbrains.py` | Không tồn tại |
| `src/cwp/io/alibaba.py` | Không tồn tại |
| `src/cwp/preprocess/{clean,resample,filter}.py` | Không tồn tại |
| `data/processed/` | Chỉ có `.gitkeep` |
| `data/catalog.parquet` | Không tồn tại |
| `tests/test_io.py`, `tests/test_resample.py` | Không tồn tại |

Toàn bộ `src/` chỉ có tám tệp `.gitkeep`. `git status` sạch, không có việc chưa
commit. Commit gần nhất `8b6ac6e` chỉ thêm log GĐ0.

## Phần B làm được — đánh giá thật

Bốn câu trả lời sát hạch **đều đúng bản chất**, không phải chép lại tài liệu:

- **Câu 1** — đúng. Nắm được rằng 28,64 đạt bởi một hằng số nên không kết luận được
  gì về model.
- **Câu 2** — đúng, số học kiểm lại khớp: 28,64 − 10,48 = 18,16; 18,16 / 28,64 =
  63,4%. B còn tự nhận ra phần còn lại 36,6% là biến thiên nội tại của E3, chỗ này
  tài liệu không nói thẳng.
- **Câu 3** — đúng. Gọi được tên "biến đổi affine" và chứng minh
  `ŷ = z_t·σ + μ = y_t`.
- **Câu 4** — đúng phần hệ quả và đúng dấu hiệu phát hiện qua N0.

Phần tóm tắt giao thức bằng lời của B cũng chính xác, kể cả hai chi tiết dễ trượt:
`.shift(1)` cho rolling, và thống kê chuẩn hoá chỉ tính trên cửa sổ train.

**Kết luận cổng: ĐẠT phần hiểu bài.**

## Vấn đề phát hiện

**1. Môi trường chưa cài — chặn thẳng GĐ1.** A kiểm bằng `importlib.metadata`:
0/12 gói khớp `requirements.txt`.

| Nhóm | Gói | Ghi chú |
|---|---|---|
| Thiếu hẳn | `pyarrow`, `xgboost`, `lightgbm`, `tqdm` | **Không có `pyarrow` thì không ghi được parquet** — tức không ra được sản phẩm chính của GĐ1 |
| Lệch phiên bản | pandas 2.3.3 (cần 2.2.3), numpy 2.4.4 (cần 2.1.3), scikit-learn 1.8.0 (cần 1.5.2), scipy, matplotlib, pyyaml, pytest, jupyterlab | Đang chạy trên Python toàn cục, không có venv |

Log của B mâu thuẫn ở chỗ này: mục tiêu phiên số 4 ghi "Chuẩn bị môi trường thực thi
theo requirements.txt", nhưng "Việc tiếp theo" lại liệt kê chính việc đó là chưa làm.

**2. B tự thu hẹp GĐ1 còn ba việc.** Kế hoạch có chín. B bỏ sót: sinh
`data/processed/`, sinh `catalog.parquet`, hai tệp test, và **bảng số chuỗi vào /
bị loại theo từng điều kiện / còn lại** — mà bảng đó chính là điều kiện qua cổng GĐ1.

**3. Câu 4 gộp nhầm hai bài kiểm tra.** B mô tả bài test ở Câu 3 thành "kiểm tra
xem giá trị chuẩn hoá có thay đổi khi bổ sung dữ liệu ngoài train". Đó là một test
khác — cũng hợp lệ và đáng viết — nhưng không phải test ở Câu 3. Test ở Câu 3 là:
naive persistence chạy ở N0 và ở N1 rồi map ngược phải cho MAE trùng nhau đến sáu
chữ số thập phân. Nên viết **cả hai**, thành hai hàm test riêng.

## Quyết định
- GĐ0 **chưa đóng**. Chỉ còn treo ô môi trường.
- Bổ sung quy ước đánh số giai đoạn vào `research-plan.md` để chặn tái diễn: luôn
  dùng mã `GĐ<n>`, không nói "giai đoạn đầu".
- Chưa mở mục trong `decisions.md` — chưa có gì đổi giao thức. Nếu A chốt dùng phiên
  bản thư viện mới hơn thay vì ghim, khi đó mới cần một mục QĐ.

## Việc tiếp theo
- [ ] B tạo venv riêng, cài đúng phiên bản ghim, chạy lại kiểm tra 12/12
- [ ] A quyết: ghim đúng `requirements.txt`, hay cập nhật tệp đó theo phiên bản mới
- [ ] B đọc lại checklist GĐ1 đầy đủ chín mục trước khi bắt đầu

## File sinh ra
- Cập nhật `docs/research-plan.md`: trạng thái cổng GĐ0, quy ước đánh số giai đoạn
