# Nhật ký nghiên cứu

Thư mục này là **nơi duy nhất** được phép chứa ghi chú quá trình. Mục đích: khi dùng
agent AI hỗ trợ nghiên cứu, mọi thứ agent sinh ra đều có chỗ đứng rõ ràng, không
vương vãi ra gốc repo.

## Luật

1. **Mỗi phiên làm việc một file.** Đặt tên `YYYY-MM-DD-slug.md`.
   Ví dụ: `2026-09-03-parser-bitbrains.md`.
2. **Không sửa log cũ.** Sai thì viết log mới đính chính và link ngược lại.
   Log là bằng chứng thời điểm, không phải tài liệu sống.
3. **Kết luận đã chốt thì chuyển đi.** Log ghi *quá trình*. Khi một điều trở thành
   luật của dự án thì chuyển vào `docs/protocol.md`, quyết định kiến trúc chuyển vào
   `docs/decisions.md`. Log giữ lại đường dẫn.
4. **File tạm để trong `scratch/`.** Mọi script dùng một lần, CSV thử nghiệm, hình
   nháp đều nằm ở `research-log/scratch/`. Thư mục này bị Git bỏ qua và **được phép
   xoá bất cứ lúc nào**. Không có gì quan trọng được để ở đây.
5. **Không tạo file .md ở gốc repo.** Gốc repo chỉ có `README.md`.

## Chỉ dẫn cho agent AI

Khi giao việc cho agent, dán đoạn này vào prompt:

> Ghi chú quá trình vào `research-log/YYYY-MM-DD-slug.md` theo mẫu
> `research-log/_template.md`. File tạm để trong `research-log/scratch/`.
> Không tạo file mới ở gốc repo. Không sửa file log đã có.

## Cấu trúc

```
research-log/
├── README.md          quy ước (file này)
├── _template.md       mẫu cho mỗi phiên
├── INDEX.md           mục lục, cập nhật thủ công
├── scratch/           file tạm, Git bỏ qua, xoá được
└── YYYY-MM-DD-*.md    các phiên
```
