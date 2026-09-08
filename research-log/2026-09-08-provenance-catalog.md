# 2026-09-08 — Thêm nguồn gốc vào catalog; xác nhận hai bản hiện thực khớp tuyệt đối

**Người thực hiện:** A
**Giai đoạn:** GĐ1
**Thời lượng:** ~1 giờ

## Mục tiêu phiên
B nộp Bước 1–5. Chạy kiểm cổng, truy nguyên các mục trượt, và bịt lỗ hổng nguồn gốc
dữ liệu phát hiện được.

## Kết quả quan trọng nhất

**Hai bản hiện thực độc lập ra cùng con số tuyệt đối.**

| | B tính (`build.py`) | A tham chiếu (`reference_gd1.py`) |
|---|---:|---:|
| E1 chuỗi giữ | 735 | 735 |
| E1 dòng h=12 | 1.642.811 | 1.642.811 |
| E1 `ngoai_cua_so` | 55 | 55 |
| E2 chuỗi giữ | 302 | 302 |
| E2 dòng h=12 | 673.322 | 673.322 |

Khớp đến từng dòng, kể cả `ngoai_cua_so = 55` — cái bẫy cửa sổ toàn cục mà A lo nhất
và đã cảnh báo trước trong phiếu giao việc. Đây là bằng chứng mạnh nhất có thể có
rằng cả hai bản đều đúng, và biện minh cho công sức viết bản tham chiếu độc lập.

## Truy nguyên 8 mục trượt

Không có mục nào là bug của B.

**Sáu mục + một cảnh báo — E3 chưa làm.** `src/cwp/io/alibaba.py` không tồn tại;
Bước 6 của phiếu chưa tới. Đúng tiến độ.

**Một mục — `data/processed/E1.parquet` thiếu trên máy A.** A chỉ chạy `--env E2`
local. Dòng E1 trong catalog đến từ máy B qua Git.

## Phát hiện: catalog là khảm từ hai máy

`catalog.parquet` **được commit**, `data/processed/*.parquet` **bị gitignore**. Hệ
quả: bảng tổng hợp đi được giữa hai máy nhưng dữ liệu thì không.

Trạng thái thực tế lúc kiểm: catalog 1.750 dòng, trong đó E1 do **máy B** tính, E2
do **máy A** vừa ghi đè khi chạy local. Cả hai đều khớp tham chiếu nên **không có gì
lộ ra**. Về nguyên tắc tái lập thì đó là một bảng không xác định được nguồn gốc.

Đây là loại lỗi im lặng: không sai số, không thông báo, chỉ mất khả năng truy vết.

## Đã sửa

Thêm hai cột vào schema `catalog.parquet` (protocol mục 6b, giờ 15 cột):

| Cột | Nguồn |
|---|---|
| `built_on` | `platform.node()` |
| `built_at` | `datetime.now().isoformat(timespec="seconds")` |

`check_gd1.py` thêm mục **1b. Nguồn gốc catalog**, phân biệt ba tình huống:

| Tình huống | Xử lý |
|---|---|
| Một lệnh `--env all`, một máy | ĐẠT |
| Cùng máy, chạy từng env khác thời điểm | CẢNH BÁO |
| **Nhiều máy khác nhau** | **TRƯỢT** |

Phân biệt như vậy vì chạy từng env là bình thường lúc đang làm, còn khảm nhiều máy
thì mất hẳn khả năng xác định kết quả sinh trong môi trường nào.

## Kiểm chứng công cụ

Thêm hai test vào `tests/test_check_gd1.py`:
- `test_catalog_kham_nhieu_may_thi_truot` — dựng catalog có E1 từ `may-B`, E2 từ
  `may-A`, xác nhận checker TRƯỢT. Đây chính là tình huống đã xảy ra thật.
- `test_cung_may_khac_thoi_diem_chi_canh_bao` — xác nhận không đánh trượt oan.

Toàn bộ: **11 test xanh**.

Chạy checker trên catalog thật hiện tại: TRƯỢT ở schema, thiếu `built_on`,
`built_at`. Đúng như mong đợi — B phải cập nhật `build.py`.

## Việc tiếp theo
- [ ] B thêm hai cột vào `build.py`, làm Bước 6 (`io/alibaba.py`)
- [ ] B chạy `--env all` một lệnh, không ghép từng env
- [ ] A nghiệm thu bằng `check_gd1.py`

## File sinh ra
- Cập nhật `docs/protocol.md` (mục 6b), `docs/gate-gd1.md` (mục 3.4b),
  `docs/brief-gd1-b.md` (Bước 5), `scripts/check_gd1.py`,
  `tests/test_check_gd1.py`
