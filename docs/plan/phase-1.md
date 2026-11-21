# Kế hoạch Phase 1 (Buổi sáng & Buổi tối — Quán Ăn Chợ Nổi)

## Mục tiêu
- Xây dựng hoàn chỉnh lõi Gameplay Phase 1 theo PRD-0 và Test Contract v1.0.
- Buổi sáng (`gather`): Bơi, lặn, tiêu hao & hồi phục oxy, mất máu do ngạt (choke), ngất (faint) mất giỏ LIFO, hái bông súng/điên điển mọc lại, bắt cá linh/cá lóc có hồi chiêu, cập bến xuất kho.
- Buổi tối (`quan`): Khách đến bàn T1 theo lịch, giữ chỗ nguyên liệu, nấu tại bếp B1, bưng món và phục vụ, tính tiền và tiền boa (tip), khách bỏ về khi hết kiên nhẫn làm giảm uy tín, ca kết thúc đóng cửa (closing).
- Kết nối hai tiến trình độc lập qua file kho `catch.json`.

## Phân công công việc (Nhóm 2 người - Triển khai tuần tự)
- **Thành viên 1 (Làm trước - Phụ trách Phase 1 & 2):**
  - Setup repo, sửa `game.contract.json`, kiểm tra môi trường chạy `python3`.
  - Hiện thực logic Buổi sáng (`chonoi/sim/gather.py` - Lát 1 + Lát 2).
  - Hiện thực logic Buổi tối (`chonoi/sim/quan.py` - Lát 3 + Lát 4).
  - Viết bộ unit test `tests/test_gather.py` và `tests/test_quan.py`.
  - Chạy smoke test hộp đen, trích xuất bằng chứng tại `docs/proof/phase-1/`.
  - Cập nhật tài liệu Phase 1, gắn tag `phase-1` và bàn giao tại `docs/standup.md`.
- **Thành viên 2 (Làm sau - Nhận bàn giao Phase 3 & 4):**
  - Nhận bàn giao từ `docs/standup.md`, pull code từ main.
  - Phụ trách mở rộng Phase 3, Phase 4, Retro nhóm và Release final `v1.0.0`.

## Rủi ro & Giải pháp
- **Rủi ro môi trường Windows:** Lệnh `python3` trỏ vào Windows Store alias thay vì Python 3.11 thực tế.
  - *Giải pháp:* Tạo file alias `python3.exe` trong thư mục cài Python để tương thích cả máy local và CI Linux.
- **Rủi ro sai lệch Test Contract:** Bất đồng bộ schema file kho hoặc thứ tự sự kiện JSONL.
  - *Giải pháp:* Tuân thủ nghiêm ngặt PRD-0 mục E & G, kiểm thử tự động với 44 unit tests và smoke test hai tiến trình độc lập.
