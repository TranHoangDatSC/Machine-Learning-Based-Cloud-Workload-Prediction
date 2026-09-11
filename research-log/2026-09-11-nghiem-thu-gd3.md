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
Bảng công bố là hợp của **5 lần chạy**; snapshot khớp bảng công bố **từng ô** là
`runs/20260910-202500_experiments_gd3` (lần chạy lại `svr` sau khi B sửa mẫu con).
Lần chạy dài nhất, `20260910-154617`, mất 271,7 phút.

> **Đính chính 2026-09-11.** Bản đầu trỏ `20260910-154617` là "lần chạy cuối, đủ 8
> model". Snapshot đó đủ 72 tổ hợp thật, nhưng **lệch bảng công bố 30 ô** vì nó chụp
> trước khi mẫu con SVR được sửa. Protocol mục 16 đòi truy ngược được về **một** thư
> mục cụ thể, nên con trỏ đúng là `20260910-202500`.

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

Chuỗi `E1_830` có **346** dòng test mang **đúng một giá trị** `1,1333333333333333`.
Toán học thì `SS_tot = 0`, nhưng `ȳ = sum/n` ra `1,133333333333333` nên
`sum((y−ȳ)²) = 1,71 × 10⁻²⁹ > 0`.

> **Đính chính 2026-09-11.** Bản đầu ghi *347 dòng* và `6,84 × 10⁻²⁹`. Hai số đó đi
> với nhau và **đúng cho n = 347**, tức phép chẩn đoán đã cắt cửa sổ test `[1957, 2304)`
> mà quên áp luật purge (với `h = 1`, purge bỏ đúng một bucket). Số đúng: 254.310 dòng
> test của E1 `h = 1` chia 735 chuỗi ra **346,0**. `reference_gd3.py` cắt đúng nên
> `reference_gd3.json` không bị ảnh hưởng.
>
> Và chính chỗ lệch này là lập luận mạnh nhất cho `min == max`: **cùng một số 0 toán
> học hiện ra thành `1,7e−29` hay `6,8e−29` chỉ tuỳ cách cắt và cách cộng dồn.** Không
> ngưỡng epsilon nào đúng cho mọi bản hiện thực. Bản của A kiểm `sstot > 0` nên **chấm R² = 1,0** cho
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

### 3. Siêu tham số chốt ở mép lưới — cả hai đầu

Đếm đủ **cả hai đầu** lưới: `rf` 7/9 trên + 2/9 dưới, `svr` 7/9 + 2/9, `xgb` trục
`depth` 6/9 + 3/9, `ridge` 4/9 + 5/9. Tức **9/9 tổ hợp chạm mép** ở cả bốn model —
`rf` và `svr` chỉ có hai ứng viên nên điều đó là tất yếu. Ngoại lệ: trục `n_estimators`
của `xgb` nghiêng về giá trị **thấp** (8/9 chọn 300), nới số cây gần như vô ích. Cộng
với `rf` chỉ chạy 50 cây. Nghĩa là ML đang bị giới hạn bởi **lưới và ngân sách**, không
phải bởi dữ liệu → QĐ-015.

> **Đính chính 2026-09-11.** Bản đầu chỉ đếm biên trên (`ridge` 4/9, `xgb` 6/9), nói
> nhẹ đi so với sự thật.

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

Hai điểm B nêu ở GĐ3 đã đóng bằng QĐ-015. **Nhưng GĐ4 chưa mở được**: mục 14 còn hai
điểm chặn (N1 lấy `mu`/`sd` của chuỗi nào; đặc trưng có được biến đổi theo không) mà
nếu để B tự hiểu thì hai bản hiện thực đều "đúng đặc tả" vẫn ra số khác hẳn. Danh sách
đầy đủ ở mục **Chuẩn bị GĐ4** bên dưới, chờ chốt thành QĐ-016.

## Việc tiếp theo

- [x] Sửa sáu chỗ sai trong tài liệu GĐ3 — 2026-09-11, xem mục "Đính chính" bên dưới
- [x] Tick checklist GĐ3 ở `docs/research-plan.md`, đóng khối GĐ3
- [ ] A: chốt các điểm mơ hồ của mục 14 (ba chế độ chuẩn hoá N0/N1/N2) thành **QĐ-016**
      — **chặn GĐ4**, danh sách điểm phải chốt đã soạn sẵn ở mục "Chuẩn bị GĐ4" bên dưới
- [ ] A: dựng `gate-gd4.md`, `brief-gd4-b.md`, `scripts/reference_gd4.py` trước khi B
      bắt đầu — đúng nhịp đã chạy ba lần; làm **sau** QĐ-016 vì thước đo phụ thuộc nó
- [ ] GĐ5: cân nhắc kiểm độ vững về lưới siêu tham số, nếu còn thời gian

## Đính chính 2026-09-11 — sáu chỗ sai trong tài liệu GĐ3

Rà lại sau khi đóng cổng. **Không chỗ nào đụng tới sản phẩm**: `check_gd3.py` vẫn ĐẠT,
`reference_gd3.json` không sinh lại, chín bảng kết quả giữ nguyên từng ô. Sáu chỗ đều
nằm ở **câu chữ mô tả**, nhưng năm trong sáu chỗ nói **nhẹ đi** một hạn chế hoặc chỉ
sai chỗ để truy vết, nên phải sửa trước khi viết paper.

| # | Chỗ sai | Sửa thành | Vì sao quan trọng |
|---|---|---|---|
| 1 | Trỏ `runs/20260910-154617` là snapshot của bảng công bố | `runs/20260910-202500` | Snapshot cũ **lệch 30 ô** (toàn bộ `svr` ở `h = 6`, `h = 12`) vì chụp trước khi sửa mẫu con SVR. Protocol mục 16 đòi truy ngược được về **một** thư mục cụ thể |
| 2 | `E1_830` có *347* dòng test, `ss_tot = 6,84e−29` | **346** dòng, `1,71e−29` | 254.310 ÷ 735 = 346,0 — số bị ép bởi số học. Hai số cũ đúng cho `n = 347`, tức phép chẩn đoán đã cắt cửa sổ test mà quên purge |
| 3 | `ridge` chốt ở biên lưới *4/9* | **9/9** (4 trên + 5 dưới) | Bản cũ chỉ đếm biên trên. `alpha` hẹp ở **cả hai** đầu, nên muốn nới phải nới cả hai |
| 4 | `xgb` chốt ở biên trên *6/9* | 6/9 ở trục `depth`; **1/9** ở trục `n_estimators` | Trên trục số cây thì 8/9 chọn giá trị **thấp** — nới số cây gần như chắc chắn vô ích. Gộp hai trục làm một che mất điều đó |
| 5 | `lr`/`ridge` thua naive *2,3–2,6 lần* | **1,23–2,57 lần** tuỳ horizon | 2,3–2,6 là con số của riêng `h = 12`. Lấy trường hợp xấu nhất làm đại diện |
| 6 | Gate mục 5: đầu ghi `275 passed`, cuối ghi `277`; L2 ghi *15 lần chạm test* | 277; **55 lần trên 45 tổ hợp** | 15 là của riêng một run. Con số đầy đủ và lý do chênh nay ở gate mục **5.6** |

Chỗ số 2 hoá ra là bài học đáng giá nhất trong sáu chỗ: **cùng một số 0 toán học hiện
ra thành `1,7e−29` hay `6,8e−29` chỉ tuỳ cách cắt dữ liệu và thứ tự cộng dồn.** Không
ngưỡng epsilon nào đúng cho mọi bản hiện thực — đó chính là lý do `min == max` là phép
so duy nhất đúng, và lý do lỗi `E1_830` xứng đáng được ghi kỹ thay vì sửa lặng lẽ.

Chú thích trong `scripts/reference_gd3.py` cũng ghép nhầm (`346 bản sao` đi với
`6,8e−29`) — đã sửa, **chỉ chú thích, không đụng logic**.

## Chuẩn bị GĐ4 — danh sách phải chốt thành QĐ-016

> Đây là **chương trình nghị sự**, không phải quyết định. Mỗi mục dưới đây là chỗ hai
> bản hiện thực "đều đúng đặc tả" sẽ ra số khác hẳn nhau — đúng loại bẫy mà QĐ-010 gặp
> ở GĐ2 và QĐ-013 gặp ở GĐ3. Phải chốt **trước** khi B viết dòng code GĐ4 đầu tiên.

### Hai điểm CHẶN

**1. N1 lấy `mu`, `sd` của chuỗi nào?** Mục 14 chỉ nói *"chỉ tính trên cửa sổ train"*
mà không nói **train của ai**. Chuỗi đích thuộc môi trường đích, còn model học ở môi
trường nguồn:

| Phương án | Nghĩa là gì | Rủi ro |
|---|---|---|
| Thống kê của **chính chuỗi đích** | Thực tế khi triển khai: máy mới có sẵn lịch sử của chính nó | **Không còn là zero-shot** — đã dùng dữ liệu đích |
| Thống kê của **môi trường nguồn** | Transfer thuần | Có thể thất bại vì lý do tầm thường là lệch thang |

Chọn cách nào cũng được, nhưng **phải chọn trước** và phát biểu RQ3 theo đúng cách đã
chọn. Đây là điểm quyết định ý nghĩa của toàn bộ TN-B.

**2. Đặc trưng có được biến đổi theo không?** 19 đặc trưng đều dẫn xuất từ `y`. Nếu chỉ
chuẩn hoá **target** mà giữ `lag_*`, `roll_*` ở thang gốc thì **mức tải vẫn vào model
qua đặc trưng**, và N1 không bỏ được đúng cái nó sinh ra để bỏ. Phải chốt: biến đổi `y`
trước rồi **sinh lại đặc trưng cho từng chế độ** (hệ quả: `data/features/` nhân ba), hay
áp cùng `mu`/`sd` lên các cột lag/rolling. Kèm theo: **4 đặc trưng lịch không được
chuẩn hoá** — chúng đã nằm trong `[−1, 1]` và không mang thang tải.

### Ba điểm nên chốt cùng lúc

**3. Phạm vi và ngân sách.** `research-plan.md` ghi *"6 cặp × 3 chế độ"*, nhưng mục 8
còn đòi **hai biến thể có/không có đặc trưng lịch**, và còn 3 horizon × 8 model. Chạy
đủ lưới là 2.592 ô. Đo từ thời gian thật của GĐ3:

| | ước tính cho cả 5 model ML |
|---|---|
| **Dùng lại** siêu tham số đã chốt ở GĐ3 | **≈ 5,9 giờ** |
| **Dò lại** siêu tham số cho từng chế độ | **≈ 32,9 giờ** |

Ở GĐ3, dò siêu tham số chiếm **82%** tổng thời gian máy. Khuyến nghị: khai báo trước
rằng GĐ4 **dùng lại** siêu tham số của GĐ3 theo từng môi trường nguồn — như một quyết
định có lý do, không phải lối tắt phát hiện giữa chừng. Kèm cảnh báo ở mục 5.5 của
gate: siêu tham số của E1 được chọn trên vùng validation dễ hơn test hẳn, nên E1-làm-
nguồn thừa hưởng chỗ yếu đó.

**4. Ba baseline định nghĩa trong không gian nào.** Dưới N1 không quan trọng (z-score
là affine). Dưới **N2 thì quan trọng**: `naive` là `Δ̂ = 0` (ra đúng persistence) hay
`Δ̂ = Δ_t` (thành model drift)? Hai cách cho hai bảng khác nhau.

**5. Tập đánh giá trên môi trường đích** nên chốt là **đúng tập test** `[1957, 2304)`
với cùng luật purge của QĐ-013 điểm 2 — có thế bảng TN-B mới đặt cạnh bảng TN-A đọc
được.

### Ba bất biến làm test miễn phí cho `reference_gd4.py`

`giai-thich-chuan-hoa.md` mục 4 nêu một; thực ra có ba, đều **không cần huấn luyện gì**
và đều bắt được trọn ba lỗi mà mục 5 của tài liệu đó liệt kê:

| Bất biến | Vì sao đúng |
|---|---|
| `naive` ở N0 ≡ `naive` ở N1 (sau khi map ngược) | z-score là affine, persistence bất biến dưới affine |
| **`ma6` ở N0 ≡ `ma6` ở N1** | trung bình của z là z của trung bình — cũng affine |
| **`naive` ở N2 với `Δ̂ = 0` ≡ `naive` ở N0** | `ŷ = y_t + 0 = y_t` |

Ba đẳng thức này chạy được **trước khi có bất kỳ model nào**, nên chúng là chỗ rẻ nhất
để bắt lỗi chuẩn hoá — chỗ `research-plan.md` gọi là *"dễ sai nhất toàn dự án"*.

## File sinh ra

- `scripts/reference_gd3.py` — sửa điều kiện chuỗi hằng của R²
- `results/tables/reference_gd3.json` — sinh lại
- `research-log/gate-gd3.md` — điền mục 5, kết luận ĐẠT
- `docs/decisions.md` — thêm QĐ-015
- `docs/protocol.md` — mục 11 thêm lưới siêu tham số, mục 13 sửa 7 → 8

**Sửa thêm 2026-09-11 (đính chính, xem mục trên):** `research-log/gate-gd3.md` (6 chỗ,
thêm mục 5.6), `docs/decisions.md` QĐ-015, `docs/protocol.md` mục 11,
`scripts/reference_gd3.py` (chú thích), `docs/research-plan.md` (tick khối GĐ3),
`research-log/2026-09-10-gd3-thi-nghiem-a.md` (tick 2 checkbox).
