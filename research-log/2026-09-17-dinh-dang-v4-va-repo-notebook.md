# 2026-09-17 — Rà định dạng theo template HJS, bản thảo v4, repo notebook

**Người thực hiện:** một phiên đóng cả hai vai, theo yêu cầu của A.
**Giai đoạn:** GĐ5
**Thời lượng:** ~5 giờ (phần lớn là chạy lại quy trình trong repo mới)

## Mục tiêu phiên

1. Rà `ban-thao-v3.docx` (bản A đã sửa trong Word) xem định dạng có khớp `paper/sample/HJS@Template-OTH.docx` không.
2. A cho biết đã định dạng lại tài liệu tham khảo bằng Word citation.
3. Kiểm lại toàn bộ nội dung.
4. Lập kế hoạch và dựng một repo mới gồm các notebook có đủ kết quả, kèm hướng dẫn đưa lên GitHub từng notebook một.

## 1. Định dạng so với template

Khớp template:

- khổ giấy 20,5 × 28,5 cm;
- lề trên 2,2 cm, các lề khác 1,8 cm;
- header 1,4 cm, footer 1 cm;
- header phân biệt trang đầu và trang chẵn lẻ;
- 12 style chính trùng hệ với template; Heading1 chỉ thêm `uiPriority`, do Word tự chèn.

Lệch template, đã sửa trong v4:

| Chỗ | v3 | Template | v4 |
|---|---|---|---|
| Danh mục tài liệu tham khảo | trường BIBLIOGRAPHY kiểu IEEE, font Times, năm ở cuối | style `reference`, Cambria 10, đánh số `[n]`, năm ngay sau tên tác giả (như hai bài HJS đã đăng của nhóm) | danh mục tĩnh đúng mẫu HJS |
| Sau tiêu đề "Tài liệu tham khảo" | một Heading1 rỗng hiện thành *"VIII."* | không có | bỏ |
| Tác giả liên hệ | chỉ có `*` ở phần tiếng Anh | `*` ở dòng tác giả tiếng Việt, chú thích chân trang *"Corresponding Author"* | thêm |
| Dòng trống giữa email và TÓM TẮT | không có | có | thêm |
| Dấu — sau TÓM TẮT, Từ khóa, ABSTRACT, Keywords | in đậm | không đậm | bỏ đậm |
| Nội dung ô bảng | cách trước sau 1 pt | *"Single, không có khoảng cách dòng trước sau"* | 0 pt |

## 2. Trích dẫn Word

A nhập 19 nguồn, nhưng tên tác giả bị dồn vào **một** người, ví dụ `Last = "R. N. Calheiros"`, `Middle = "Masoumi, R. Ranjan, R. Buyya"`. Word vì vậy in ra *"E. M. R. R. R. B. R. N. Calheiros"*.

Các lỗi khác:

- *"P. e. al."* cho Pedregosa; Holm thiếu tên *"S."*; *"EEE/ACM"* thiếu chữ I;
- trang ghi *"p."* thay vì *"pp."*, do Word gặp gạch nối dài;
- thiếu số trang ở Shen, Guo, Chen, Drucker; thiếu *"3rd ed."* ở hai sách.

Đã sửa trong `customXml` của v4:

- mỗi tác giả một mục riêng; Pedregosa đủ 16 tác giả;
- số trang dùng gạch nối thường;
- thêm tái bản lần 3, sửa *"IEEE"*, sửa Holm.

Sau khi Word cập nhật trường, 34 trích dẫn trong bài vẫn đánh đúng `[1]` đến `[19]`. Danh mục cuối bài chuyển thành văn bản tĩnh theo mẫu HJS. Nếu sau này thêm tài liệu thì cập nhật trích dẫn rồi sửa danh mục cho khớp.

## 3. Nội dung

So từng đoạn v3 của A với bản v3 đã giao. Thay đổi của A giữ nguyên:

- bỏ tác giả thứ ba;
- bỏ in nghiêng ở ngoặc kép;
- viết hoa sau dấu hai chấm;
- gộp ba kết luận thành một đoạn;
- viết lại đoạn MAE, Wilcoxon, tự tương quan.

Đã sửa trong v4:

- *"30%–50%"* → *"từ 30% đến 50%"*, vì A không muốn dùng gạch ngang;
- viết hoa sau dấu chấm phẩy (hai chỗ);
- *"... là hiệu ứng tổng hợp là do ..."* → *"... là hiệu ứng tổng hợp: ..."*; *"mức độ tương đồng"* → *"mức độ tương quan"* cho đúng nghĩa tự tương quan;
- câu MAPE bị dính hai mệnh đề, tách lại; *"một số sai số rất lớn hơn"* → *"một vài sai số rất lớn"*;
- *"Tuy nhiên không vì thế mà nhóm sẽ phát biểu"* → *"Tuy nhiên, nhóm không vì thế mà phát biểu"*;
- *"MAE [5]"* gõ tay, không phải trường trích dẫn → đổi thành trường Word;
- tách ba đoạn bị gộp khác chủ đề:
  - khoảng trống thứ hai / hệ quả cho người vận hành / ba câu hỏi;
  - bộ lọc / 19 đặc trưng;
  - kết quả chính của câu hỏi 3 / ba tính chất kiểm tra.

Số liệu: A không đổi con số nào. `doi_chieu_so_lieu_bai_bao.py` vẫn 175 số, 0 lệch.

Kết quả: `paper/ban-thao-v4.docx`, 11 trang, `validate.py` đạt. `ban-thao-v3.docx` của A giữ nguyên.

## 4. Repo notebook

Thư mục `D:\Research 2026\CWP-Cloud-Notebooks`, ngoài repo này:

- `src/`, `scripts/` (bỏ `tao_docx.py`), `config/` chép nguyên;
- `data/raw` là junction trỏ về dữ liệu thô của repo này, không chép 11 GB.

Chín notebook, mỗi bước gọi đúng script gốc:

1. dữ liệu và tiền xử lý
2. khám phá dữ liệu
3. đặc trưng và chia dữ liệu
4. Thí nghiệm 1
5. ba cách chuẩn hoá
6. Thí nghiệm 2
7. máy giả
8. hai lỗi của bước chuẩn hoá
9. tổng hợp và đối chiếu số

Bốn bước huấn luyện nặng (GĐ3, GĐ4 cùng D1, D2, QĐ-018 cùng QĐ-019; cộng khoảng 30 giờ máy) có cờ `CHAY_LAI`:

- mặc định nạp kết quả của lần chạy gốc từ `results/ket_qua_chay_goc/`, kèm `meta_*.json`;
- mọi bước còn lại tính lại thật.

Hướng dẫn `HUONG_DAN_DUA_LEN_GITHUB.md`: mười một commit, mỗi notebook một commit. Hướng dẫn ghi rõ:

- không chỉnh ngày commit;
- không dựng lịch sử;
- có mẫu khai báo dùng AI.

### Lỗi phát hiện nhờ chạy lại từ đầu

`scripts/build_features.py` chạy **không có** `--modes` (đường GĐ2/GĐ3, sinh `{env}_h{h}.parquet`) đã hỏng từ GĐ4, ở hai chỗ:

1. `bien_doi_bang(df, None)` báo *"Chế độ không hợp lệ: None"*.
2. Bảng báo cáo định dạng `None` bị lỗi; bước đối chiếu số dòng với catalog chỉ áp cho `"N0"` nên đường `None` bị bỏ qua.

Không ảnh hưởng kết quả đã công bố: các tệp `{env}_h{h}.parquet` sinh từ GĐ3, trước khi có thay đổi, và trùng tuyệt đối với `{env}_N0_h{h}.parquet` (kiểm `E2_h6`: `equals` = True).

Sửa ở cả hai repo:

- `None` đi đường của N0 và được đối chiếu với catalog;
- bảng in `-` cho chế độ.

Chạy lại E2 h = 1, 6: khớp neo GĐ1; `tests/test_qd019.py` 8/8 đạt.

### Kết quả chạy lại từ đầu trong repo mới

Xoá sạch `data/processed`, `data/features*`, `results/tables`, `runs` rồi chạy 9 notebook, tổng khoảng 25 phút.

- Trước đó, chạy thử bằng script: 51 bảng sinh lại **trùng từng byte** với `results/tables/` của repo này.
- Notebook 02: Bảng 1 trùng từng số.
- Notebook 03: số dòng Train, Validation, Test trùng `splits_gd3`.
- Notebook 04: MAE naïve 0,408 / 0,466 / 0,449; vượt naïve 0/2/11; tỉ số từ 1,30 đến 2,66 và từ 0,84 đến 0,94.
- Notebook 05: ba tính chất đạt, sai lệch lớn nhất 4,26e−14.
- Notebook 06: cột N0 trùng Bảng 4.
- Notebook 07: máy giả, tự tương quan bậc 1 là 0,91 / 0,85 và ở 24 giờ là 0,03 / 0,46.
- Notebook 08:
  - Bảng 5 trùng;
  - N2 so với naïve: bản sai 0,997 / 1,011, bản đúng 0,873 / 0,927;
  - `check_qd019` nhóm K (4/4) và nhóm R (3/3) đạt.
- Notebook 09: Bảng 4 trùng; bất đối xứng 30/28/26; máy giả 8/15 và 6/15; `doi_chieu_so_lieu_bai_bao.py` **175 số, 0 lệch**.

Sửa trong lúc chạy:

- notebook 07 dùng nhãn `E1a` không có trong `bo_sung_cum.csv`, đổi thành `E1`;
- lọc thanh tiến trình khỏi output;
- định dạng Bảng 1;
- thêm kiểm nhóm R sau khi nạp kết quả QĐ-019.

## Việc tiếp theo

- [ ] A đọc `ban-thao-v4.docx`, xác nhận việc bỏ tác giả thứ ba là có chủ ý
- [ ] A xem 9 notebook, rồi đưa lên GitHub theo hướng dẫn
- [ ] Commit repo này
