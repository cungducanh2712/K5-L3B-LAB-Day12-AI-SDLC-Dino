# Kế hoạch Phase 2 (Một ngày ở chợ nổi — Test Contract v1.1)

## Mục tiêu
- Nâng cấp game lên Test Contract v1.1, số liệu chuẩn và mở rộng hệ sinh thái.
- **Buổi sáng (`gather`):**
  - Đàn cá bơi 1.5 m/s, đổi hướng mỗi 120 tick, phản xạ mép $x \in [4, 96]$ và dải độ sâu.
  - Sinh cá theo lịch mỗi 360 tick (trần 12 đàn, clearance > 1m, tỷ lệ 4:3:3).
  - Xuất hiện Cá Sấu Năm Chèo (M1 từ Day 1, M2 từ Day 3): tuần tra 1.0 m/s, truy đuổi 3.0 m/s khi phát hiện người chơi ở $d \ge 10$, cắn trúng mất 1 Máu và $\lfloor n/2 \rfloor$ giỏ LIFO, recoil 60 tick.
  - Bổ sung nguyên liệu cá kèo (`ca_keo`) và nút kèo nèo (`keo_neo` N5, N6).
- **Buổi tối (`quan`):**
  - 2 bếp B1, B2 và 4 bàn T1-T4.
  - Thực đơn 6 món ăn đặc trưng miền Tây Nam Bộ.
  - Lọc món theo kế hoạch ngày (`day_plan`) khi chạy mode `day`.
- **Vòng ngày & Shop (`day`):**
  - Chạy trọn vòng ngày qua CLI `--mode day --days <N>`.
  - Công bố kế hoạch ngày D1-D5, chuyển ca mượt mà giữa Gather -> Quán -> Shop.
  - Mua nâng cấp bình oxy (`oxygen`) và phao cứu sinh (`hp`), áp dụng hiệu lực từ Ngày tiếp theo.
  - Cơ chế Pause / Resume toàn cục cho mọi mode.

## Phân công công việc (Bàn giao kết thúc ca làm của Thành viên 1)
- **Thành viên 1 (Hoàn thành Phase 1 & 2):**
  - Cập nhật cấu hình `game.contract.json` lên v1.1.
  - Hiện thực logic Cá bơi, sinh cá và Cá Sấu Năm Chèo trong `sim/gather.py`.
  - Mở rộng Quán sim 2 bếp 4 bàn và lọc món theo day_plan trong `sim/quan.py`.
  - Xây dựng `DaySim`, cơ chế Shop và Pause trong `sim/day.py` và `runner.py`.
  - Viết bộ test `tests/test_p2.py`, sinh bằng chứng `docs/proof/phase-2/`.
  - Cập nhật ma trận truy vết `docs/verification/phase-2.md`, ghi retro Phase 2 và chuẩn bị tài liệu bàn giao `docs/standup.md`.
- **Thành viên 2 (Sẵn sàng tiếp nhận Phase 3 & 4):**
  - Pull code từ nhánh main (đã tag `phase-2`).
  - Mở PR phát triển tiếp Phase 3 theo PRD mới.

## Rủi ro & Giải pháp
- **Rủi ro hồi quy (Regression):** Nâng cấp từ 6 đàn cá ban đầu lên 8 đàn cá có thể làm fail các test snapshot cũ của P1.
  - *Giải pháp:* Cập nhật assertion test smoke P1 tương ứng với hợp đồng v1.1, đảm bảo toàn bộ 49 tests đều xanh (100% PASS).
