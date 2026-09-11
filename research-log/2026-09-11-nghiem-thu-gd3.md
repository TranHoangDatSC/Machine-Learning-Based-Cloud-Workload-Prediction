# 2026-09-11 — A nghiệm thu GĐ3, đóng cổng, chốt QĐ-015

**Người thực hiện:** A
**Giai đoạn:** GĐ3
**Thời lượng:** ~2 giờ (chưa kể 4,5 giờ máy chạy `rf`/`svr`)

## Mục tiêu phiên

Nghiệm thu GĐ3 theo `gate-gd3.md` mục 3, và đóng hai điểm B nêu trong mục Vướng mắc
của `2026-09-10-gd3-thi-nghiem-a.md`.

## Đã làm

- Rà toàn bộ GĐ3 hai vòng: vòng một 2026-09-10 (trượt, thiếu sản phẩm), vòng hai
  2026-09-11 sau khi B chạy nốt `rf`, `svr` và Bước 6
- Sửa lỗi R² trong `scripts/reference_gd3.py`, sinh lại `reference_gd3.json`
- Điền `gate-gd3.md` mục 5 — **kết luận ĐẠT**
- Chốt **QĐ-015**: đếm 8 model, khai báo lưới siêu tham số, không chạy lại

## Số liệu thu được

`check_gd1/2/3.py` đều thoát 0. `pytest tests/` **277 passed, 1 skipped**.
Lần chạy cuối `runs/20260910-154617_experiments_gd3`: 271,7 phút, đủ **8 model × 3
môi trường × 3 horizon**.

### RQ1 — số ô ML vượt naive (Wilcoxon + Holm, hướng lấy từ trung vị của hiệu)

| | ML vượt naive | Chi tiết |
|---|---|---|
| E1 | **0 / 15** | Không model ML nào vượt ở bất kỳ horizon nào |
| E2 | **2 / 15** | Chỉ `svr`, ở h=6 và h=12 |
| E3 | **11 / 15** | `lr`, `ridge`, `rf` ở h=1; thêm `xgb` ở h=6 và h=12 |

## Phát hiện

### 1. Lỗi R² của tham chiếu — lần thứ ba A sai, B đúng

B báo 27 ô R² của E1 lệch và **từ chối sửa code cho khớp tham chiếu**, kèm đề nghị A
quyết. Truy nguyên xác nhận B đúng.

Chuỗi `E1_830` có 347 dòng test mang **đúng một giá trị** `1,1333333333333333`. Toán
học thì `SS_tot = 0`, nhưng `ȳ = sum/n` ra `1,1333333333333329` nên
`sum((y−ȳ)²) = 6,84 × 10⁻²⁹ > 0`. Bản của A kiểm `sstot > 0` nên **chấm R² = 1,0** cho
một chuỗi hằng mà naive đoán trúng tầm thường. Bốn chuỗi hằng còn lại của E1 có hằng
số biểu diễn được chính xác nên bị loại bình thường — chỉ đúng chuỗi này lọt.

Đã sửa sang `min == max`. Đây là lần thứ ba thước đo của A sai còn sản phẩm của B
đúng (GĐ1 lỗi đếm điểm nội suy, GĐ2 `dropna` thay luật cửa sổ, GĐ3 chuỗi này).

### 2. A cảnh báo quá phạm vi về lỗi hướng Wilcoxon — đính chính

Vòng một A phát hiện `kiem_dinh_cap` lấy p-value từ Wilcoxon ghép cặp nhưng lấy hướng
từ hiệu hai trung vị, và cảnh báo rằng `ml_vs_naive_gd3.csv` sẽ khẳng định ngược dữ
liệu.

**Cảnh báo đó rộng hơn sự thật.** Hàm `bang_ml_vs_naive` vốn đã dùng đúng thống kê
ghép cặp ngay từ đầu; lỗi chỉ nằm ở cột `tot_hon` của `wilcoxon_gd3.csv`. A đọc một
hàm rồi suy cho cả hai.

B đã tự sửa trước khi chạy Bước 6, tách rõ hai vai trò: `delta_p50` để báo cáo,
`hieu_p50` để gán hướng. Kiểm lại bảng đã sinh: **252/252 cặp đúng hướng**.

### 3. Siêu tham số chốt ở biên trên của lưới

`rf` 7/9 tổ hợp, `svr` 7/9, `xgb` 6/9, `ridge` 4/9. Cộng với `rf` chỉ chạy 50 cây.
Nghĩa là ML đang bị giới hạn bởi **lưới và ngân sách**, không phải bởi dữ liệu → QĐ-015.

### 4. Một quan sát cho GĐ4

Trên **E1**, validation dễ hơn hẳn test: MAE của naive là 0,2185 trên val so với
0,4077 trên test (h=1). E2 và E3 không có khoảng cách này. Không phải rò rỉ, nhưng
siêu tham số của E1 được chọn trên một vùng thời gian không đại diện. Ghi vào
Limitations và cân nhắc khi thiết kế GĐ4.

## Quyết định

- **QĐ-015** — đếm 8 model (sửa mục 13), khai báo lưới siêu tham số, **không chạy
  lại** → `docs/decisions.md`, đã sửa vào `docs/protocol.md` mục 11 và 13.

Phần đáng ghi của QĐ-015: nới lưới lúc này là nới **sau khi đã biết ML thua**, cùng họ
với điều mục 17 cam kết không làm. Muốn kiểm độ vững thì làm ở GĐ5, khai báo lưới mới
**trước** khi chạy và **báo cáo cả hai** kết quả.

## Vướng mắc

Không còn. Hai điểm B nêu đã đóng bằng QĐ-015.

## Việc tiếp theo

- [ ] A: dựng `gate-gd4.md`, `brief-gd4-b.md`, `scripts/reference_gd4.py` trước khi B
      bắt đầu — đúng nhịp đã chạy ba lần
- [ ] A: chốt các điểm mơ hồ của mục 14 (ba chế độ chuẩn hoá N0/N1/N2) thành QĐ-016
- [ ] GĐ5: cân nhắc kiểm độ vững về lưới siêu tham số, nếu còn thời gian

## File sinh ra

- `scripts/reference_gd3.py` — sửa điều kiện chuỗi hằng của R²
- `results/tables/reference_gd3.json` — sinh lại
- `research-log/gate-gd3.md` — điền mục 5, kết luận ĐẠT
- `docs/decisions.md` — thêm QĐ-015
- `docs/protocol.md` — mục 11 thêm lưới siêu tham số, mục 13 sửa 7 → 8
