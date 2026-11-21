# Standup & Biên bản bàn giao giữa các Phase

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Thành viên 1 (Làm trước) | Setup repo, fix python3 Windows, xong Lát 1-4 (Gather + Quán), pass 44 tests, tag `phase-1` | Triển khai Phase 2 | Không |
| Phase 2 | Thành viên 1 (Làm trước) | Nâng cấp v1.1: Cá bơi/sinh, Cá Sấu Năm Chèo, 2 bếp 4 bàn 6 món, Day loop & Shop, pass 49 tests, tag `phase-2` | Bàn giao trọn vẹn cho Thành viên 2 | Không |
| Phase 3 | Thành viên 2 (Làm sau) | Nhận bàn giao từ main, tạo branch `feature/phase-3`, đọc spec Phase 3 | Triển khai Phase 3 và chuẩn bị Phase 4 | Chờ đề Phase 3 từ giảng viên |

---

## 📌 Hướng dẫn bàn giao cho Thành viên 2 (Bắt đầu từ Phase 3)

Chào bạn, tôi (Thành viên 1) đã hoàn thành toàn bộ nền tảng cho **Phase 1** và **Phase 2**, toàn bộ **49/49 unit & contract tests** đều đã PASS 100% trên commit này.

### Các bước bạn cần làm khi bắt đầu:
1. **Pull code mới nhất:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Kiểm tra môi trường tại máy bạn:**
   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```
   (Đảm bảo in ra `Ran 49 tests ... OK`).
3. **Tạo branch làm việc riêng cho Phase 3:**
   ```bash
   git checkout -b feature/phase-3
   ```
4. **Điền file phản tư cá nhân của bạn:**
   - Tạo file `docs/members/<github-handle-cua-ban>.md` theo mẫu `docs/members/TEMPLATE.md`.
5. **Đọc yêu cầu Phase 3:**
   - Nhận tài liệu Phase 3 từ giảng viên / lab board.
   - Thêm các tính năng mới vào `chonoi/sim/` và viết test trong `tests/test_p3.py`.
   - Cam kết tối thiểu **3 commits có nội dung thật** từ tài khoản GitHub của bạn.
   - Mở PR merge vào `main` và gắn tag `phase-3`.
