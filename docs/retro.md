# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Hoàn thành đúng hạn toàn bộ Lõi Phase 2 (Cá bơi/sinh, Cá Sấu Năm Chèo, 2 bếp 4 bàn, 6 món, Day loop, Shop, Pause) và 100% 49/49 tests pass. Kiến trúc modul hóa rõ ràng, dễ bàn giao.
- Điều tệ: Nhóm 2 người làm lệch giờ nên Thành viên 1 phải dồn sức làm liên tục cả 2 phase đầu, chưa thử nghiệm được các mở rộng tuỳ chọn.
- 1 hành động cho Phase 3: Thành viên 2 pull code từ main, đọc kỹ `docs/standup.md` và tạo branch riêng để phát triển tiếp Phase 3, đảm bảo có tối thiểu 3 commit chất lượng.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2:** Thành viên 2 đã tiếp nhận đúng kế hoạch, tạo branch `feature/phase-3-4`, hoàn thành toàn bộ Phase 3 và Phase 4 với nhiều commit có nội dung thật và chất lượng cao.
- **Điều tốt / điều tệ:**
  - *Điều tốt:* Tốc độ phát triển cực nhanh nhờ kiến trúc contract chặt chẽ; 56/56 unit tests pass 100%; benchmark đạt >27,000 FPS; soak test 10 ngày hoàn hảo không crash.
  - *Điều tệ:* Thời gian ngắn nên việc trao đổi trực tiếp bị hạn chế, phần lớn dựa vào tài liệu chuyển giao và issue tracking.
- **Số liệu:**
  - Số commit theo người: Thành viên 1 (Cung Đức Anh) ≥ 5 commits; Thành viên 2 (Nguyễn Ngọc Bách) ≥ 4 commits.
  - Cách đọc code của nhau: Đọc qua git log, ma trận truy vết `docs/verification/` và biên bản chuyển giao `docs/standup.md`.
  - Token ước tính: Thành viên 1: ~135,000 tokens; Thành viên 2: ~125,000 tokens.
- **Một lần AI sai và cách nhóm phát hiện:**
  - Trong Phase 4, AI đã gọi hàm `self.rng.get("current", self.rng.get("fish"))` với 2 tham số vị trí, trong khi `Streams.get(name)` chỉ nhận 1 tham số. Lỗi này làm crash benchmark và lập tức được phát hiện nhờ việc chạy thử nghiệm lệnh CLI trực tiếp thay vì chỉ tin vào code AI sinh ra.
- **Nếu làm lại, đổi gì:**
  - Sẽ thiết lập CI/CD pipeline tự động ngay từ Phase 1 để chạy regression test sau mỗi lần push branch, giảm bớt thời gian test thủ công cục bộ.
