# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 11:15 | Nhóm có 2 thành viên có được tham gia và phân chia ca làm việc lệch giờ không? | Giảng viên/TA đồng ý; nhóm cam kết hoàn thành đầy đủ yêu cầu 4 phase, mỗi thành viên có ít nhất 3 commit có nội dung thật. | Giảng viên / PO |
| 2 | 2026-11-21 11:25 | `headless_cmd` dùng `python3`, trên Windows gặp lỗi WindowsApps alias `9009`. Xử lý thế nào? | Tạo alias `python3.exe` trong thư mục cài đặt Python cục bộ để giữ nguyên contract `python3`, đảm bảo code chạy như nhau trên Windows và CI Ubuntu. | PO / Integrator |
| 3 | 2026-11-21 11:35 | Khách hết kiên nhẫn bỏ về trong ca quán thì xử lý nguyên liệu đang giữ thế nào? | Nếu nguyên liệu mới chỉ được giữ chỗ (reserved) mà chưa nấu thì nhả lại kho; nếu bếp đang nấu/ready/trên tay cho đơn đó thì hủy món, nguyên liệu đã dùng không hoàn lại theo PRD mục F. | PO / Dev |
| 4 | 2026-11-21 11:45 | Schema kho v1.2 trong file chuyển từ dict đếm sang list cá thể có backward-compatible không? | Đọc theo contract v1.2 từ chối kho đếm (trả mã 2). Để hỗ trợ các scenario cũ, module scenario vẫn cho phép nạp dữ liệu mảng hoặc dict chuyển đổi linh hoạt. | PO / Dev |
| 5 | 2026-11-21 12:00 | Chạy benchmark cảnh lặn headless hay render GUI? | Cung cấp lệnh CLI `python3 -m chonoi.bench` chạy mô phỏng chuẩn xác 1800 ticks sau 180 ticks warm-up, xuất file `bench.json` với đầy đủ 5 chỉ số theo spec. | QA / Integrator |
