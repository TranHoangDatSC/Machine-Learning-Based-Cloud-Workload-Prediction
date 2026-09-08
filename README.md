# ML-CWP-Cloud

## Machine Learning-Based Cloud Workload Prediction: A Comparative Study Across Public Cloud Traces

Nghiên cứu thực nghiệm về **dự đoán tải hệ thống đám mây (cloud workload prediction)** bằng Machine Learning trên nhiều bộ dữ liệu cloud trace công khai, với trọng tâm là khả năng **khái quát hóa mô hình giữa các môi trường khác nhau**.

**Đích nhắm:** đồ án môn học Machine Learning và phát triển thành một bài báo tạp chí trong nước.

---

## 1. Dự án này đang giải quyết vấn đề gì?

Một hệ thống cloud không có mức tải cố định.

CPU của một máy chủ hoặc máy ảo có thể đang ở 15%, vài phút sau tăng lên 70%, rồi lại giảm xuống 20%. Khi hàng trăm hoặc hàng nghìn máy cùng hoạt động, việc biết **hệ thống đang tải bao nhiêu ở hiện tại** là chưa đủ.

Điều hữu ích hơn là biết:

> **Trong 5, 10 hoặc 30 phút tới, workload có khả năng thay đổi như thế nào?**

Đó là bài toán **Cloud Workload Prediction**.

Trong dự án này, workload được biểu diễn chủ yếu bằng **CPU utilization (%)**. Từ chuỗi CPU trong quá khứ, mô hình Machine Learning học các quy luật biến động để dự đoán tải trong tương lai.

Ví dụ đơn giản:

```text
Thời gian     CPU thực tế
10:00           24%
10:05           27%
10:10           35%
10:15           48%
10:20           63%
10:25            ?
```

Một hệ thống dự đoán tốt có thể nhận ra xu hướng tăng và ước lượng CPU ở `10:25` **trước khi thời điểm đó thực sự xảy ra**.

---

## 2. Dự đoán workload để làm gì trong thực tế?

Cloud workload prediction không chỉ là bài toán dự đoán time series. Kết quả dự đoán có thể trở thành đầu vào cho nhiều cơ chế quản trị tài nguyên trong cloud.

### Autoscaling — cấp tài nguyên trước khi quá tải

Giả sử một dịch vụ thường tăng tải mạnh vào một số thời điểm.

Nếu chỉ phản ứng sau khi CPU đã lên 95%, hệ thống mới bắt đầu tạo thêm VM/container thì có thể đã quá muộn: người dùng phải chờ, request bị timeout hoặc dịch vụ bị nghẽn.

Nếu dự đoán trước:

```text
Hiện tại:       CPU = 55%
Dự đoán +10m:   CPU ≈ 85%
                      ↓
              Scale-out sớm
                      ↓
            Thêm VM / container
```

Đây là **predictive autoscaling**: mở rộng tài nguyên dựa trên tải dự kiến thay vì chỉ phản ứng với tải hiện tại.

### Resource provisioning — tránh cấp thừa tài nguyên

Cloud provider cũng không muốn giữ quá nhiều CPU/RAM nhàn rỗi.

Nếu dự đoán cho thấy workload sắp giảm:

```text
Dự đoán tải giảm
       ↓
Giảm tài nguyên dư thừa
       ↓
Giảm chi phí vận hành
```

Dự báo workload vì vậy có thể hỗ trợ cân bằng giữa hai mục tiêu:

* **Under-provisioning:** thiếu tài nguyên → chậm, nghẽn, vi phạm SLA.
* **Over-provisioning:** dư tài nguyên → lãng phí và tăng chi phí.

### Scheduling và load balancing

Nếu biết trước máy nào sắp chịu tải cao, scheduler có thể tránh đưa thêm workload vào máy đó và chuyển workload sang các node khác.

Ví dụ:

```text
Server A → dự đoán 91% CPU
Server B → dự đoán 43% CPU
Server C → dự đoán 37% CPU

Job mới → ưu tiên B hoặc C
```

### Capacity planning

Ở quy mô dài hạn, dự báo workload còn giúp trả lời những câu hỏi như:

* Cụm hiện tại còn đủ tài nguyên không?
* Khi nào cần bổ sung capacity?
* Workload có chu kỳ ngày/tuần không?
* Tài nguyên đang được sử dụng hiệu quả đến mức nào?

Nói ngắn gọn:

> **Mục tiêu thực tế của workload prediction là chuyển quản trị cloud từ “thấy quá tải rồi mới phản ứng” sang “dự đoán trước và chuẩn bị tài nguyên”.**

Dự án này **không trực tiếp xây dựng một autoscaler hoàn chỉnh**. Nó nghiên cứu phần đứng trước autoscaler: **mô hình dự báo workload có đủ chính xác và đủ khả năng generalize để làm tín hiệu cho các quyết định quản trị tài nguyên hay không.**

---

## 3. Vấn đề nghiên cứu

Một câu hỏi tự nhiên là:

> Nếu Machine Learning dự đoán workload tốt trên một cloud, liệu đem model đó sang cloud khác có còn tốt không?

Đây là vấn đề khó hơn việc đơn thuần tìm model có MAE/RMSE thấp nhất.

Các cloud trace có đặc tính rất khác nhau. Ví dụ, trong dữ liệu đang nghiên cứu, mức CPU trung vị giữa Bitbrains và Alibaba chênh lệch rất lớn:

```text
Bitbrains ≈ 0,84%
Alibaba   ≈ 37,0%
```

Nếu train model trên môi trường A rồi trực tiếp đem sang B, model có thể thất bại chỉ vì **mức tải cơ bản (load level)** của hai môi trường khác nhau.

Một kết luận kiểu:

> “Cross-environment transfer không hoạt động.”

khi đó chưa thực sự thú vị, vì model có thể chỉ đang gặp **distribution shift về scale/level**.

Do đó dự án đặt câu hỏi sâu hơn:

> **Nếu tách mức tải tuyệt đối khỏi động lực học của workload, phần quy luật biến động nào vẫn có thể transfer giữa các cloud khác nhau?**

Đây là trọng tâm và cũng là đóng góp nghiên cứu chính của dự án.

---

## 4. Câu hỏi nghiên cứu

| Mã      | Câu hỏi                                                                                                                                |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **RQ1** | Mô hình ML nào dự đoán cloud workload tốt nhất, và có thực sự vượt các baseline đơn giản như naive prediction không?                   |
| **RQ2** | Hiệu năng của các mô hình thay đổi như thế nào giữa những môi trường cloud khác nhau?                                                  |
| **RQ3** | Model train trên môi trường A có generalize sang môi trường B không, và **thành phần nào của tín hiệu workload có khả năng transfer?** |

### Trọng tâm: RQ3

RQ3 không chỉ thực hiện phép thử đơn giản:

```text
Train A → Test B
```

mà phân biệt giữa:

```text
Workload signal
      │
      ├── Load level
      │   Mức tải cơ bản của môi trường
      │
      └── Dynamics
          Cách workload biến động theo thời gian
```

Mục tiêu là xác định liệu các **dynamics** như xu hướng, biến động, tính chu kỳ hoặc quan hệ temporal có mang tính tổng quát hơn mức CPU tuyệt đối hay không.

Nếu có, kết quả này có ý nghĩa cho việc xây dựng các workload predictor có khả năng thích nghi với môi trường mới thay vì phải học lại hoàn toàn từ đầu.

---

## 5. Dữ liệu

Nghiên cứu sử dụng ba môi trường từ các **public cloud traces**:

| Mã     | Môi trường                  |           Quy mô |     Số dòng |
| ------ | --------------------------- | ---------------: | ----------: |
| **E1** | Bitbrains fastStorage       |         1.250 VM |  11.221.800 |
| **E2** | Bitbrains Rnd               | 500 VM × 3 tháng |  12.496.728 |
| **E3** | Alibaba cluster-trace-v2018 |        4.023 máy | 246.934.820 |

Target chung:

```text
CPU utilization (%)
Range: 0–100
Time grid: 5 phút
```

Việc đưa các trace về cùng target và time grid cho phép thực hiện so sánh có kiểm soát giữa các môi trường.

Chi tiết về nguồn dữ liệu, schema, preprocessing và các lưu ý khi sử dụng:

`docs/data-card.md`

---

## 6. Một thí nghiệm điển hình trông như thế nào?

Ví dụ với một môi trường:

```text
Raw cloud trace
       ↓
Parser + preprocessing
       ↓
Chuỗi CPU trên time grid 5 phút
       ↓
Feature engineering
       ↓
Train / validation / test
       ↓
Naive baseline ──┐
ML model ────────┼──→ Metrics
                 ↓
             So sánh
```

Với RQ3, quy trình mở rộng thành:

```text
Environment A
      ↓
    Train
      ↓
    Model
      │
      ├────────────→ Test A
      │              In-domain
      │
      └────────────→ Test B
                     Cross-domain
                          ↓
                Phân tích transfer
```

Sau đó các biến thể normalization/decomposition được sử dụng để kiểm tra xem thất bại khi transfer đến từ **khác biệt mức tải** hay từ **khác biệt dynamics thực sự**.

---

## 7. Bắt đầu từ đâu?

Không cần đọc toàn bộ repository ngay từ đầu.

| Bạn là                   | Đọc theo thứ tự                                                         |
| ------------------------ | ----------------------------------------------------------------------- |
| **Người mới vào dự án**  | `README.md` → `docs/research-plan.md` → `docs/protocol.md`              |
| **Đã quen ML từ đề tài khác** | `docs/tu-bai-cu-den-bai-nay.md` → `docs/protocol.md`               |
| **Người triển khai (B)** | `docs/tu-bai-cu-den-bai-nay.md` → `docs/protocol.md` → `docs/giai-thich-chuan-hoa.md` → `data/raw/*/explain.md` → `research-log/README.md` |
| **Người review**         | `docs/decisions.md` → `research-log/INDEX.md`                           |

Danh mục tài liệu trong `docs/`:

| Tệp | Nội dung |
| --- | --- |
| `protocol.md` | Giao thức đã chốt. Luật chơi của toàn bộ thí nghiệm |
| `research-plan.md` | Kế hoạch 6 giai đoạn, phân vai A/B, checklist |
| `data-card.md` | Nguồn, schema, số liệu đã kiểm chứng, giới hạn |
| `decisions.md` | Nhật ký quyết định. Mọi thay đổi giao thức đi qua đây |
| `giai-thich-chuan-hoa.md` | Giải thích mục 14 kèm số liệu chứng minh |
| `tu-bai-cu-den-bai-nay.md` | Nối kiến thức ML sẵn có sang bài toán này, và chỉ ra chỗ phép loại suy gãy |

> **`docs/protocol.md` đã chốt.**
>
> Không sửa trực tiếp protocol trong quá trình triển khai. Mọi thay đổi phải được ghi nhận và giải thích thông qua `docs/decisions.md`.

Điều này nhằm tránh việc thay đổi thiết kế thí nghiệm sau khi đã nhìn thấy kết quả mà không để lại dấu vết.

---

## 8. Cấu trúc repository

```text
ML-CWP-Cloud/
│
├── config/
│   └── Tham số thí nghiệm, tách khỏi code
│
├── data/
│   ├── raw/          Dữ liệu gốc — bất biến
│   ├── interim/      Dữ liệu trung gian
│   └── processed/    Dữ liệu sẵn sàng cho thí nghiệm
│
├── docs/
│   ├── protocol
│   ├── research plan
│   ├── data card
│   └── decision log
│
├── research-log/
│   ├── Nhật ký nghiên cứu theo phiên
│   └── scratch/      File tạm
│
├── notebooks/
│   └── Khám phá dữ liệu; không chứa logic chính
│
├── src/cwp/
│   └── Python package chính
│
├── runs/
│   └── Output của từng experiment + snapshot config
│
├── results/
│   └── Bảng và hình đã được chọn lọc
│
├── paper/
│   └── Bản thảo LaTeX
│
└── tests/
    └── Test parser, preprocessing và metrics
```

`data/` và `runs/` không được đưa lên Git.

---

## 9. Cài đặt môi trường

Phiên bản thư viện **đã ghim** trong `requirements.txt`. Không nâng cấp gói khi chưa
qua `docs/decisions.md` (QĐ-007) — vì `protocol.md` mục 16 lấy phiên bản ghim làm
một phần của cam kết tái lập.

**Python yêu cầu: 3.10 đến 3.12.**
Trần 3.12 vì scikit-learn 1.5.2 và matplotlib 3.9.2 chưa có wheel cho 3.13.
Sàn 3.10 vì scipy 1.14.1 đã bỏ Python 3.9.

### Cách 1 — Linux Mint (dùng cho máy của B)

Mint 21.x có sẵn Python 3.10, Mint 22.x có sẵn 3.12. Cả hai đều hợp lệ, không cần
cài thêm Python.

```bash
# 0. Xem máy đang có Python nào
python3 --version

# 1. Gói hệ thống. Mint không cài sẵn python3-venv.
#    libgomp1 là OpenMP runtime, XGBoost và LightGBM cần nó.
sudo apt update
sudo apt install -y python3-venv python3-pip libgomp1

# 2. Vào thư mục repo
cd ~/ML-CWP-Cloud

# 3. Tạo môi trường ảo ngay trong repo
python3 -m venv .venv

# 4. Kích hoạt. Dấu hiệu thành công: dòng nhắc lệnh có tiền tố (.venv)
source .venv/bin/activate

# 5. Nâng pip trước khi cài
python -m pip install --upgrade pip

# 6. Cài đúng phiên bản đã ghim
pip install -r requirements.txt

# 7. Xác minh. Phải ra "Khớp: 12/12" và "ĐẠT"
python tests/test_env.py
```

Bước 7 là bắt buộc. Chưa ra 12/12 thì chưa được bắt đầu GĐ1.

#### Dùng conda thay cho venv

Máy đã có sẵn conda thì dùng conda cũng được, `tests/test_env.py` chấp nhận cả hai.
**Thay** bước 3 và 4 ở trên bằng hai lệnh sau, các bước còn lại giữ nguyên:

```bash
conda create -n ml-cwp python=3.11 -y
conda activate ml-cwp
```

Không chạy cả hai. Kích hoạt conda env rồi lại `source .venv/bin/activate` là chồng
hai môi trường lên nhau, gói sẽ cài lẫn lộn và `test_env.py` sẽ báo lỗi import.

Không dùng conda `base` — đó là môi trường dùng chung, `test_env.py` từ chối.

**Mỗi lần mở terminal mới đều phải kích hoạt lại:**

```bash
cd ~/ML-CWP-Cloud
source .venv/bin/activate
```

Thoát môi trường: `deactivate`.

#### Nếu `python3 --version` không nằm trong 3.10–3.12

Chỉ khi rơi vào trường hợp này mới cần cài thêm Python:

```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv

# Tạo venv bằng đúng bản 3.12, không dùng python3 mặc định nữa
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python tests/test_env.py
```

#### Lỗi hay gặp

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| `ensurepip is not available` | Thiếu `python3-venv` | `sudo apt install python3-venv` |
| `libgomp.so.1: cannot open shared object file` | Thiếu OpenMP runtime | `sudo apt install libgomp1` |
| `test_env.py` báo "chưa kích hoạt venv" | Quên `source` | `source .venv/bin/activate` |
| Cài xong vẫn lệch phiên bản | Cài nhầm vào Python toàn cục | Kích hoạt venv rồi `pip install -r requirements.txt` lại |
| `externally-managed-environment` | pip bị chặn cài ngoài venv | Đúng như thiết kế — phải cài trong venv |

### Cách 2 — Conda trên Linux

Khuyến nghị nếu chạy trên Linux workstation/server hoặc thường xuyên làm việc với môi trường nghiên cứu ML.

```bash
git clone <repository-url>
cd ML-CWP-Cloud

conda create -n ml-cwp-cloud python=3.11 -y   # 3.11 nằm trong khoảng cho phép
conda activate ml-cwp-cloud

pip install -r requirements.txt
```

Các lần làm việc sau chỉ cần:

```bash
conda activate ml-cwp-cloud
```

Kiểm tra môi trường:

```bash
python --version
which python
```

### Cách 3 — Python venv trên Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Cách 4 — Python venv trên Windows

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Không commit `.venv/`, Conda environment hoặc dữ liệu thô vào repository.

---

## 10. Chuẩn bị dữ liệu

Dữ liệu thô **không đi kèm repository** do kích thước lớn và điều kiện phân phối của từng dataset.

Tải dữ liệu theo hướng dẫn tại:

```text
data/raw/*/about.md
```

sau đó đặt dữ liệu vào đúng đường dẫn được mô tả trong:

```text
docs/data-card.md
```

Nguyên tắc quan trọng:

```text
data/raw/
```

là **read-only về mặt quy trình nghiên cứu**.

Không chỉnh sửa, overwrite hoặc “clean trực tiếp” dữ liệu nguồn.

Mọi biến đổi phải đi theo:

```text
raw
 ↓
interim
 ↓
processed
```

Nhờ vậy khi preprocessing có vấn đề, toàn bộ pipeline có thể chạy lại từ dữ liệu gốc.

---

## 11. Quy ước nghiên cứu

### Dữ liệu gốc bất biến

`data/raw/` chỉ chứa dữ liệu nguồn. Mọi preprocessing ghi sang `interim/` hoặc `processed/`.

### Notebook không phải implementation chính

Notebook được dùng để:

* khám phá dữ liệu;
* kiểm tra giả thuyết;
* visualization;
* prototype nhanh.

Logic được sử dụng trong thí nghiệm chính phải nằm trong:

```text
src/cwp/
```

Notebook sẽ `import` logic từ package thay vì duy trì một implementation riêng.

### Mỗi experiment phải truy vết được

Mỗi lần chạy chính thức sinh một thư mục riêng trong:

```text
runs/
```

bao gồm ít nhất thông tin cần thiết để xác định:

```text
Experiment
├── config snapshot
├── environment / dataset
├── model
├── seed
├── preprocessing
├── metrics
└── output
```

Nguyên tắc:

> **Mọi con số xuất hiện trong paper phải truy ngược được về một experiment cụ thể.**

### Không sửa protocol âm thầm

`docs/protocol.md` mô tả giao thức nghiên cứu đã chốt.

Nếu trong quá trình triển khai phát hiện cần thay đổi thiết kế, không chỉnh protocol rồi coi như quyết định đó luôn tồn tại.

Thay vào đó ghi:

```text
docs/decisions.md
```

với:

* vấn đề gặp phải;
* quyết định thay đổi;
* lý do;
* ảnh hưởng đến thí nghiệm;
* experiment nào bị tác động.

### Nhật ký nghiên cứu có một nơi duy nhất

Ghi chú quá trình nằm trong:

```text
research-log/
```

Không tạo các file kiểu:

```text
note.txt
todo2.md
temp-result.md
final-final-note.md
```

rải rác ở gốc repository.

Gốc repo chỉ giữ `README.md` và các file cấu hình dự án thực sự cần thiết.

---

## 12. Phân vai

### A — Research lead

Phụ trách:

* xác định câu hỏi nghiên cứu;
* thiết kế thí nghiệm;
* chốt protocol;
* review implementation và kết quả;
* phân tích kết quả;
* viết paper.

### B — Implementation & Experiment

Phụ trách:

* parser và preprocessing;
* triển khai pipeline;
* triển khai baseline/model;
* chạy thí nghiệm;
* lưu artifact;
* ghi research log;
* báo cáo anomaly hoặc vấn đề dữ liệu.

Checklist cụ thể của từng giai đoạn:

```text
docs/research-plan.md
```

---

## 13. Khi nào một kết quả được xem là có ý nghĩa?

Mục tiêu của dự án **không phải đơn thuần tìm model phức tạp nhất hoặc model có RMSE thấp nhất**.

Một model chỉ thực sự đáng quan tâm khi trả lời được các câu hỏi:

```text
Nó có hơn naive baseline không?
            ↓
Có ổn định trên nhiều environment không?
            ↓
Sang environment khác còn hoạt động không?
            ↓
Nếu thất bại, tại sao?
            ↓
Do khác load level hay khác dynamics?
            ↓
Có thành phần nào của workload transfer được không?
```

Vì vậy, một kết quả như:

> “Model X đạt RMSE thấp nhất trên Alibaba.”

chưa phải kết luận quan trọng nhất.

Một kết quả dạng:

> “Raw cross-environment prediction thất bại mạnh, nhưng sau khi loại bỏ khác biệt về load level, một phần temporal dynamics vẫn transfer được giữa các environment.”

sẽ gần với câu hỏi khoa học trung tâm của dự án hơn nhiều.

Ngay cả trường hợp **không có dynamics nào transfer tốt** cũng là một kết quả có giá trị nếu thí nghiệm đủ chặt chẽ để chỉ ra điều đó.

---

## 14. Từ nghiên cứu đến ứng dụng thực tế

Dự án hiện dừng ở lớp **prediction**:

```text
Cloud trace
     ↓
Workload predictor       ← ML-CWP-Cloud
     ↓
Predicted workload
```

Trong một hệ thống production, kết quả có thể được nối tiếp:

```text
Cloud monitoring
       ↓
Historical workload
       ↓
Workload predictor
       ↓
Predicted future load
       ↓
Decision / Controller
       │
       ├── Autoscaling
       ├── Resource provisioning
       ├── Job scheduling
       ├── Load balancing
       └── Capacity planning
       ↓
Cloud infrastructure
```

Do đó nghiên cứu này không tuyên bố rằng **“dự đoán CPU tốt hơn đồng nghĩa cloud tốt hơn”**.

Prediction chỉ là một thành phần của hệ thống quản trị tài nguyên. Giá trị thực tế của nó phụ thuộc vào việc prediction có đủ chính xác, ổn định và tổng quát để controller sử dụng hay không.

Đặc biệt, nếu một predictor có thể giữ được một phần khả năng dự đoán khi chuyển sang môi trường mới, nó có tiềm năng giảm lượng dữ liệu và chi phí huấn luyện lại cần thiết khi triển khai trên hạ tầng khác.

---

## 15. Trích dẫn dữ liệu

Cả ba cloud trace đều yêu cầu ghi nhận nguồn.

Thông tin nguồn, citation và yêu cầu sử dụng được ghi tại mục **Cách trích dẫn** trong:

```text
docs/data-card.md
```

Khi viết báo cáo, đồ án hoặc paper, không trích dẫn repository này thay cho nguồn dataset gốc.

---

## Tóm tắt

**ML-CWP-Cloud** nghiên cứu ba câu hỏi tăng dần về độ khó:

```text
RQ1
Machine Learning có dự đoán workload tốt hơn baseline đơn giản không?
                         ↓
RQ2
Kết quả đó có giữ được trên những cloud environment khác nhau không?
                         ↓
RQ3
Nếu chuyển model từ cloud A sang cloud B,
thứ gì thực sự transfer được?
                         ↓
          Load level hay workload dynamics?
```

RQ1 cho biết **model có hữu ích hay không**.

RQ2 cho biết **kết quả có phụ thuộc dataset hay không**.

RQ3 đi vào vấn đề khó hơn và là trọng tâm của nghiên cứu:

> **Liệu tồn tại những quy luật động học của cloud workload có thể khái quát hóa xuyên môi trường, sau khi loại bỏ khác biệt tầm thường về mức tải?**
