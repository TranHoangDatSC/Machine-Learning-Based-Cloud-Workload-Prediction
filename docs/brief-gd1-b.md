# Phiếu giao việc GĐ1 — cho B

**Người giao:** A · **Ngày:** 2026-09-08
**Đọc trước:** `protocol.md` mục 5, 6, 6b, 7, 8 · `config/preprocess.yaml`

Mỗi bước có ba phần: **Prompt** để đưa cho agent, **Lệnh** để chạy, **Phải thấy** để
đối chiếu. Làm xong bước nào chạy lệnh bước đó ngay, đừng viết hết rồi mới kiểm.

---

## Lưu ý về tính độc lập

`scripts/reference_gd1.py` là bản hiện thực của A. Giá trị của nó nằm ở chỗ **hai
bản hiện thực độc lập ra cùng con số** — đó mới là bằng chứng đúng.

Vì vậy các prompt dưới đây **chỉ mô tả hành vi và kết quả cần đạt**, cố tình không
nói cách làm. Đừng đưa `reference_gd1.py` cho agent đọc. Nếu code của B là bản sao
cách làm của A thì việc hai bên khớp nhau không chứng minh gì cả.

---

## Bước 0 — Chuẩn bị (không cần agent)

```bash
cd "/home/phat/Documents/Project/Machine Learning/Machine-Learning-Based-Cloud-Workload-Prediction"
conda activate ml-cwp
git pull
python -m pip install -e .
python -c "import cwp; print('cwp', cwp.__version__)"
python tests/test_env.py
python scripts/check_gd1.py
```

**Phải thấy**

```
cwp 0.1.0
...
Khớp: 12/12
ĐẠT. Môi trường khớp requirements.txt...
...
TIẾN ĐỘ GĐ1: 0/11 sản phẩm
```

`import cwp` lỗi thì xem README mục 9, phần "Nếu `import cwp` báo ModuleNotFoundError".

---

## Bước 0b — Dữ liệu thô (không cần agent)

**`data/raw/` không nằm trong Git.** Clone repo về là chưa có 11 GB dữ liệu. Không
có nó thì không làm được bước nào phía dưới.

```bash
python scripts/check_data.py
```

**Phải thấy**

```
Bitbrains-fastStorage/08-2013          1250   1250     1,246,581,540  ok
Bitbrains-Rnd/2013-7                    500    500       455,268,745  ok
Bitbrains-Rnd/2013-8                    500    500       512,809,689  ok
Bitbrains-Rnd/2013-9                    500    500       498,977,308  ok
machine_usage.csv  8,996,532,344 bytes  ok
...
KHỚP — dữ liệu thô giống hệt bản của A. Chạy được GĐ1.
```

Chưa khớp thì xem README mục 10. Cách nhanh nhất là chép thẳng thư mục `data/raw/`
từ máy A qua ổ cứng ngoài, giữ nguyên cấu trúc.

Bước này phải KHỚP trước khi làm tiếp — hai máy chạy trên hai bộ dữ liệu khác nhau
thì mọi con số đối chiếu ở cổng đều vô nghĩa.

---

## Bước 1 — `src/cwp/io/bitbrains.py`

### Prompt

```
Đọc docs/protocol.md mục 6b và config/preprocess.yaml trước khi viết.
KHÔNG đọc scripts/reference_gd1.py.

Viết src/cwp/io/bitbrains.py, hai hàm:

1) load_raw(path) -> pd.DataFrame
   - Đọc CSV Bitbrains, phân tách bằng ";\t"
   - Trả DataFrame đúng 2 cột: time_s (int64), cpu_pct (float64)
   - Nguồn: cột "Timestamp [ms]" và "CPU usage [%]"
   - QUAN TRỌNG: giá trị cột "Timestamp [ms]" thực tế là GIÂY dù tên cột ghi ms.
     Không nhân, không chia 1000.
   - Giá trị cpu_pct không parse được thành số thì bỏ dòng đó.
   - Tên cột trong file có thể lẫn ký tự tab; phải strip trước khi so khớp.

2) make_series_id(env, path, month=None) -> str
   Theo đúng quy tắc ở protocol.md mục 6b. E2 bắt buộc có tháng.

Viết docstring tiếng Việt ngắn gọn. Không hardcode tham số đã có trong config.
```

### Lệnh

```bash
python -c "
from pathlib import Path
from cwp.io.bitbrains import load_raw, make_series_id
d = load_raw('data/raw/Bitbrains-Rnd/2013-8/1.csv')
print(d.shape, list(d.columns))
print('dtypes:', d['time_s'].dtype, d['cpu_pct'].dtype)
print('time_s[0] =', d['time_s'].iloc[0])
print(make_series_id('E2', Path('data/raw/Bitbrains-Rnd/2013-8/1.csv'), '2013-8'))
print(make_series_id('E1', Path('data/raw/Bitbrains-fastStorage/08-2013/137.csv')))
"
```

### Phải thấy

```
(8627, 2) ['time_s', 'cpu_pct']
dtypes: int64 float64
time_s[0] = 1375308176
E2_2013-8_1
E1_137
```

`time_s[0]` ra `1375308176000` là đã nhân 1000 vì tin vào tên cột. Sai.

---

## Bước 2 — `src/cwp/preprocess/clean.py`

### Prompt

```
Đọc docs/protocol.md mục 6 bước 1–3 và config/preprocess.yaml.
KHÔNG đọc scripts/reference_gd1.py.

Viết src/cwp/preprocess/clean.py:

clip_cpu(s: pd.Series, cfg: dict | None = None) -> tuple[pd.Series, int, int]
  - Clip theo khoảng lấy từ config/preprocess.yaml khoá `clip`
  - Trả (chuỗi đã clip, số mẫu bị clip lên trên, số mẫu bị clip xuống dưới)
  - cfg=None thì tự đọc config bằng yaml.safe_load
  - Không hardcode [0, 100]

mask_sentinel(df: pd.DataFrame, cfg=None) -> pd.DataFrame
  - Cho các cột khai trong config khoá `sentinel`, giá trị nằm trong danh sách
    sentinel thì đổi thành NaN
```

### Lệnh

```bash
python -c "
import pandas as pd
from cwp.preprocess.clean import clip_cpu
s = pd.Series([-5., 0., 50., 100., 111.07])
out, hi, lo = clip_cpu(s)
print('ra       :', out.tolist())
print('clip trên:', hi, ' clip dưới:', lo)
"
```

### Phải thấy

```
ra       : [0.0, 0.0, 50.0, 100.0, 100.0]
clip trên: 1  clip dưới: 1
```

---

## Bước 3 — `src/cwp/preprocess/resample.py`

Bước nặng nhất. Ba hàm, kiểm riêng từng cái.

### Prompt

```
Đọc docs/protocol.md mục 5, 6 bước 4–6, mục 7 và config/preprocess.yaml.
KHÔNG đọc scripts/reference_gd1.py.

Viết src/cwp/preprocess/resample.py, ba hàm:

1) to_grid(time_s, cpu_pct, grid=None) -> pd.Series
   - Bucket = floor(time_s / grid_seconds), grid_seconds lấy từ config
   - Giá trị mỗi bucket = TRUNG BÌNH các mẫu rơi vào bucket đó
   - Index là số hiệu bucket, LIÊN TỤC từ min tới max
   - Bucket không có mẫu nào thì để NaN. Tuyệt đối không nội suy ở bước này.

2) apply_window(s: pd.Series, b0: int, n_buckets=None) -> pd.Series
   - Giữ đúng các bucket trong [b0, b0 + n_buckets)
   - n_buckets mặc định = window.days * 86400 / grid_seconds  (lấy từ config)
   - Chuỗi không có bucket nào trong cửa sổ thì trả Series rỗng
   - b0 là mốc TOÀN CỤC của môi trường, hàm này chỉ nhận vào, không tự tính

3) interpolate_short(s: pd.Series, k=None) -> tuple[pd.Series, int]
   - Nội suy TUYẾN TÍNH những cụm NaN liên tiếp dài <= k, k lấy từ
     config khoá gap.max_len
   - Cụm dài hơn k giữ nguyên NaN
   - Cụm NaN ở đầu hoặc cuối chuỗi (không có điểm neo cả hai phía) giữ nguyên NaN
   - k = 0 nghĩa là không nội suy gì
   - TUYỆT ĐỐI KHÔNG dùng forward-fill hay backward-fill
   - Trả (chuỗi kết quả, số điểm đã được nội suy)
```

### Lệnh

```bash
python -c "
import numpy as np, pandas as pd
from cwp.preprocess.resample import to_grid, apply_window, interpolate_short

t = np.array([0,100,200,300,400,900]); v = np.array([1.,2,3,4,5,6])
g = to_grid(t, v, grid=300)
print('to_grid index :', list(g.index))
print('to_grid values:', [None if pd.isna(x) else round(x,2) for x in g.tolist()])

s = pd.Series(range(10), index=pd.RangeIndex(5,15), dtype=float)
print('window [5,9)  :', apply_window(s, 5, 4).tolist())
s2 = pd.Series(range(3), index=pd.RangeIndex(100,103), dtype=float)
print('ngoài cửa sổ  :', len(apply_window(s2, 5, 4)) == 0)

x = pd.Series([1.,np.nan,np.nan,4., np.nan,np.nan,np.nan,8.])
out, n = interpolate_short(x, k=2)
print('nội suy       :', [None if pd.isna(v) else round(v,1) for v in out.tolist()], '| n =', n)
out0, n0 = interpolate_short(x, k=0)
print('k=0 giữ nguyên:', out0.isna().sum() == x.isna().sum(), '| n =', n0)
"
```

### Phải thấy

```
to_grid index : [0, 1, 2, 3]
to_grid values: [2.0, 4.5, None, 6.0]
window [5,9)  : [0.0, 1.0, 2.0, 3.0]
ngoài cửa sổ  : True
nội suy       : [1.0, 2.0, 3.0, 4.0, None, None, None, 8.0] | n = 2
k=0 giữ nguyên: True | n = 0
```

Bucket 2 phải là `None`. Ra số nghĩa là đã nội suy sai chỗ.
Index 4–6 phải là `None`. Ra số nghĩa là K sai hoặc đang dùng ffill.

---

## Bước 4 — `src/cwp/preprocess/filter.py`

### Prompt

```
Đọc docs/protocol.md mục 6 bước 7–8, mục 8 và config/preprocess.yaml.
KHÔNG đọc scripts/reference_gd1.py.

Viết src/cwp/preprocess/filter.py, hai hàm:

1) count_valid_rows(s: pd.Series, max_lag=None, h=1) -> int
   Đếm số dòng huấn luyện hợp lệ theo đúng định nghĩa ở protocol.md mục 8.
   max_lag mặc định lấy từ config khoá row_validity.max_lag.

2) judge(s: pd.Series, cfg=None) -> str | None
   Trả về mã lý do loại, hoặc None nếu chuỗi được giữ.
   Bốn mã đúng như protocol.md mục 6 bước 7:
       "ngoai_cua_so", "gan_chet", "hang", "it_dong"
   Thứ tự xét đúng như protocol liệt kê.
   Ngưỡng lấy từ config khoá filter, không hardcode.
```

### Lệnh

```bash
python -c "
import numpy as np, pandas as pd
from cwp.preprocess.filter import count_valid_rows, judge

s = pd.Series(np.arange(100, dtype=float))
print('sạch, h=1        :', count_valid_rows(s, 24, 1))
s2 = s.copy(); s2[50] = np.nan
print('1 NaN idx50, h=1 :', count_valid_rows(s2, 24, 1))
print('sạch, h=12       :', count_valid_rows(s, 24, 12))

print('rỗng      ->', judge(pd.Series([], dtype=float)))
print('tải thấp  ->', judge(pd.Series([0.1]*3000)))
print('hằng số   ->', judge(pd.Series([50.0]*3000)))
print('quá ngắn  ->', judge(pd.Series(np.random.rand(100)*50)))
"
```

### Phải thấy

```
sạch, h=1        : 75
1 NaN idx50, h=1 : 49
sạch, h=12       : 64
rỗng      -> ngoai_cua_so
tải thấp  -> gan_chet
hằng số   -> hang
quá ngắn  -> it_dong
```

`49` chứ không phải `50`: cửa sổ `[t−24,t]` hỏng 25 dòng, cộng dòng `t=49` vì
target `t+1` rơi trúng NaN. Tổng 26 dòng mất.

---

## Bước 5 — `src/cwp/preprocess/build.py`

### Prompt

```
Đọc docs/protocol.md mục 5, 6, 6b, 7, 8, config/datasets.yaml và
config/preprocess.yaml. KHÔNG đọc scripts/reference_gd1.py.

Viết src/cwp/preprocess/build.py — driver chạy được bằng:
    python -m cwp.preprocess.build --env E1
    python -m cwp.preprocess.build --env all

Luồng cho mỗi môi trường:
  1. Liệt kê nguồn theo config/datasets.yaml
  2. Nạp từng chuỗi (dùng cwp.io.*), clip, căn lưới 5 phút
  3. Tính b0 = bucket NHỎ NHẤT trên TOÀN BỘ chuỗi của môi trường đó.
     Đây là mốc TOÀN CỤC. Phải quét hết mới biết b0, nên cần hai lượt hoặc
     giữ kết quả lượt một trong bộ nhớ. Không được cắt cửa sổ theo từng chuỗi.
  4. Cắt cửa sổ [b0, b0+2304) cho mọi chuỗi
  5. Nội suy cụm ngắn
  6. Lọc chuỗi, ghi lại lý do loại
  7. Tính số dòng hợp lệ cho h = 1, 6, 12

Xuất đúng schema ở protocol.md mục 6b:
  - data/processed/<ENV>.parquet  (5 cột)
  - data/catalog.parquet          (15 cột, GỒM CẢ chuỗi bị loại)
    Hai cột cuối là nguồn gốc, mọi dòng của một lần chạy mang cùng giá trị:
      built_on = platform.node()
      built_at = datetime.now().isoformat(timespec="seconds")
    Chạy --env all thì catalog gộp cả ba môi trường.
    Chạy từng env thì phải giữ lại phần của env khác đã có, không ghi đè mất.

In ra cuối mỗi env: số chuỗi vào, số bị loại theo từng lý do, số còn lại,
số dòng hợp lệ h=12, tỉ lệ nội suy, tỉ lệ clip.

Dùng tqdm cho vòng lặp dài. Đọc config bằng yaml.safe_load.
```

### Lệnh — E2 trước, nhỏ và nhanh nhất

```bash
python -m cwp.preprocess.build --env E2
python scripts/check_gd1.py
```

### Phải thấy

```
Chuỗi vào       : 500
Loại ngoai_cua_so: 1
Loại gan_chet   : 197
Chuỗi còn lại   : 302
Dòng hợp lệ h=12: 673322
```

`check_gd1.py` lúc này còn báo trượt vì thiếu E1, E3 — bình thường. Nhưng phần
đối chiếu số của E2 phải xanh hết.

### Rồi tới E1

```bash
python -m cwp.preprocess.build --env E1
python scripts/check_gd1.py
```

### Phải thấy

```
Chuỗi vào       : 1250
Loại ngoai_cua_so: 55
Loại gan_chet   : 454
Loại it_dong    : 6
Chuỗi còn lại   : 735
Dòng hợp lệ h=12: 1642811
```

> **`ngoai_cua_so = 55` là chỉ báo nhạy nhất của cả GĐ1.**
> Ra **0** nghĩa là đang cắt cửa sổ theo từng chuỗi thay vì mốc toàn cục — sai
> protocol mục 7. Quay lại bước 3 của prompt trên.

---

## Bước 6 — `src/cwp/io/alibaba.py`

### Prompt

```
Đọc docs/protocol.md mục 3, 6b, config/datasets.yaml.
KHÔNG đọc scripts/reference_gd1.py.

Viết src/cwp/io/alibaba.py xử lý data/raw/Alibaba-Cluster-Trace/machine_usage.csv
(8,99 GB, 246.934.820 dòng).

Ràng buộc:
- File KHÔNG có dòng header. Phải truyền names=[...] thủ công, đủ 9 cột theo
  config/datasets.yaml. Quên là nuốt mất dòng dữ liệu đầu tiên.
- Chỉ cần 3 cột: machine_id, time_stamp, cpu_util_percent
- Đọc theo chunk, tuyệt đối không nạp cả file vào RAM

Hai hàm:

1) machine_means(path, chunksize=...) -> pd.Series
   Lượt quét thứ nhất: CPU trung bình của từng máy, index là machine_id.

2) load_machines_frozen() -> list[str]
   ĐỌC danh sách 500 máy cố định từ config/e3_machines.txt.
   Bỏ dòng trống và dòng bắt đầu bằng '#'.
   TUYỆT ĐỐI KHÔNG tự chọn mẫu lại. protocol.md mục 3 đã đóng băng danh sách
   này (QĐ-009) vì phép chọn cũ phụ thuộc thứ tự quét tệp, khiến hai bản hiện
   thực đúng đặc tả vẫn ra hai tập máy khác nhau tới 89%.
   Có sẵn hàm load_frozen() trong scripts/freeze_e3_sample.py, dùng lại được.

   Hệ quả: KHÔNG cần lượt quét thứ nhất nữa. Chỉ còn một lượt đọc 9 GB.

3) load_machines(path, machines, chunksize=...) -> pd.DataFrame
   Lượt quét thứ hai: chỉ giữ dòng của các máy đã chọn.

In tiến trình bằng tqdm — lượt quét mất vài phút.
```

### Lệnh

```bash
python -c "
from cwp.io.alibaba import load_machines_frozen
sel = load_machines_frozen()
print('số máy đọc được:', len(sel), '| trùng lặp:', len(sel) != len(set(sel)))
print('máy đầu:', sel[0])
"
```

### Phải thấy

```
số máy đọc được: 500 | trùng lặp: False
```

Ra khác 500 là đọc sai tệp, hoặc chưa `git pull`.

### Rồi chạy E3

```bash
python -m cwp.preprocess.build --env E3
python scripts/check_gd1.py
```

### Phải thấy

```
Chuỗi vào       : 500
Loại gan_chet   : 2
Chuỗi còn lại   : 498
Dòng hợp lệ h=12: 917463
...
ĐẠT — sản phẩm GĐ1 khớp tham chiếu trong ngưỡng cho phép.
```

---

## Bước 7 — `tests/test_io.py`

### Prompt

```
Viết tests/test_io.py bằng pytest, kiểm cwp.io.bitbrains và cwp.io.alibaba.

Bắt buộc có các test sau:
- load_raw trả đúng 2 cột time_s (int64) và cpu_pct (float64)
- time_s nằm trong khoảng 1.3e9 đến 1.5e9, tức là GIÂY không phải mili-giây
- make_series_id cho E2 luôn chứa tháng, khớp regex ^E2_\d{4}-\d+_
- Tên cột đọc ra không còn ký tự tab hay khoảng trắng thừa

Test nào cần file dữ liệu thật thì dùng
data/raw/Bitbrains-Rnd/2013-8/1.csv, và pytest.skip nếu file không tồn tại,
để test vẫn chạy được trên máy chưa tải dữ liệu.
Không test cwp.io.alibaba trên file 9 GB — chỉ test logic sample_machines
bằng dữ liệu tự tạo.
```

### Lệnh
```bash
pytest tests/test_io.py -v
```
### Phải thấy — tất cả PASSED

---

## Bước 8 — `tests/test_resample.py`

### Prompt

```
Viết tests/test_resample.py bằng pytest, kiểm cwp.preprocess.resample
và cwp.preprocess.filter. Không cần dữ liệu thật, tự tạo chuỗi nhỏ.

Bắt buộc có:
- to_grid: bucket rỗng phải là NaN, không được tự lấp
- to_grid: index liên tục từ min tới max, không nhảy cóc
- apply_window: chuỗi nằm ngoài cửa sổ trả về rỗng
- interpolate_short: cụm NaN dài 2 được nội suy, cụm dài 3 giữ nguyên NaN
- interpolate_short: k=0 thì không nội suy gì
- interpolate_short: cụm NaN ở đầu và cuối chuỗi không bị nội suy
- interpolate_short: KHÔNG được tạo ra đoạn phẳng kiểu ffill — nội suy cụm 2
  điểm giữa 1.0 và 4.0 phải ra 2.0 và 3.0, không phải 1.0 và 1.0
- count_valid_rows: chuỗi sạch 100 điểm, max_lag=24, h=1 -> đúng 75
- count_valid_rows: thêm 1 NaN ở index 50 -> đúng 49
- judge: trả đúng bốn mã lý do trong bốn tình huống tương ứng
```

### Lệnh
```bash
pytest tests/test_resample.py -v
```
### Phải thấy — tất cả PASSED

---

## Bước 9 — Nộp

```bash
pytest tests/ -v
python scripts/check_gd1.py
```

**Phải thấy:** toàn bộ test PASSED, và

```
TIẾN ĐỘ GĐ1: 11/11 sản phẩm
...
ĐẠT — sản phẩm GĐ1 khớp tham chiếu trong ngưỡng cho phép.
```

Rồi viết log phiên theo `research-log/_template.md`, kèm bảng lọc đầy đủ, và:

```bash
git add -A
git commit -m "GD1: tien xu ly ba moi truong"
git push
```

Báo A nghiệm thu.

---

## Bảng đối chiếu nhanh

| | E1 | E2 | E3 |
|---|---:|---:|---:|
| Chuỗi vào | 1.250 | 500 | 500 |
| `ngoai_cua_so` | **55** | 1 | 0 |
| `gan_chet` | 454 | 197 | 2 |
| `hang` | 0 | 0 | 0 |
| `it_dong` | 6 | 0 | 0 |
| Chuỗi còn lại | 735 | 302 | 498 |
| Dòng hợp lệ h=1 | 1.650.896 | 678.486 | 938.933 |
| Dòng hợp lệ h=12 | 1.642.811 | 673.322 | 917.463 |
| Tỉ lệ nội suy | 0,016% | 0,092% | 0,167% |
| Tỉ lệ clip | 2,8434% | 2,1933% | 0% |
| Target mean | 13,6352 | 9,2199 | 38,0123 |

Ngưỡng cho phép ở `gate-gd1.md` mục 3.3. Chuỗi vào phải khớp **tuyệt đối**.
