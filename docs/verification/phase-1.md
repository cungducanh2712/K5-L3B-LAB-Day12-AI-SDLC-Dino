# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| **AC-P1-01** (Gather: Bơi, lặn, dive, surface) | Chạy test `test_dive_and_surface` trong `tests/test_gather.py` | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-02** (Gather: Tiêu hao oxy, hồi oxy mặt nước) | Chạy test `test_oxygen_depletion_and_empty_event` và `test_surface_refill_oxygen` | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-03** (Gather: Ngạt choke, ngất faint, giỏ LIFO) | Chạy test `test_choke_and_faint_lifo` kiểm tra mất giỏ theo LIFO và kho rỗng | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-04** (Gather: Hái nút, mọc lại, giỏ đầy) | Chạy test `test_gather_node_and_regrow` và `test_gather_hold_full` | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-05** (Gather: Bắt cá, cooldown, giỏ đầy) | Chạy test `test_catch_fish_and_cooldown` kiểm tra xóa đàn và tăng nguyên liệu | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-06** (Quán: Lịch khách, giữ chỗ, no_dish) | Chạy test `test_customer_arrival_and_no_dish` và `test_customer_arrival_with_stock` | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-07** (Quán: Nấu, bưng món, phục vụ, boa) | Chạy test `test_cooking_and_serving_flow` và `test_serving_and_eating_paid` | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-08** (Quán: Khách hết kiên nhẫn bỏ về) | Chạy test `test_customer_left_when_patience_expires` kiểm tra giảm uy tín | `docs/proof/phase-1/test-results.txt` | **Đạt** |
| **AC-P1-09** (Tích hợp: Gather cập bến xuất kho -> Quán nạp) | Chạy lệnh headless nối 2 tiến trình bằng `dock.json` và `catch.json` | `docs/proof/phase-1/catch.json`, `docs/proof/phase-1/quan.jsonl` | **Đạt** |
| **AC-P1-10** (Test Contract v1.0) | Toàn bộ 44 unit & contract tests pass 100% | `docs/proof/phase-1/test-results.txt` | **Đạt** |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:**
  - Toàn bộ các yêu cầu lõi PRD-0 của Phase 1 cho cả Buổi sáng (Lát 1 + Lát 2) và Buổi tối (Lát 3 + Lát 4) đều đã hoàn thành và kiểm chứng thành công.
  - Tích hợp liên tiến trình thông qua file kho `catch.json` hoạt động chính xác theo Test Contract v1.0.
- **Điều cần chỉnh cho phase sau:**
  - Chuẩn bị tiếp nhận yêu cầu Phase 2 (mở rộng cơ chế bơi đàn cá / các món mới hoặc kịch bản nhiều bàn bếp hơn).
  - Bàn giao context cho thành viên thứ 2 qua `docs/standup.md`.
