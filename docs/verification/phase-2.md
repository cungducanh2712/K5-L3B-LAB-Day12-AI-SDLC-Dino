# Ma trận truy vết Phase 2

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| **AC-P2-01** (Contract v1.1 & Cấu hình chuẩn) | Đọc `game.contract.json`, 6 nguyên liệu, 6 món, N1-N6, B1-B2, T1-T4 | `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-02** (Gather: Cá bơi, đổi hướng, phản xạ mép) | Chạy test `test_fish_swimming_and_turning` trong `tests/test_p2.py` | `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-03** (Gather: Cá Sấu Năm Chèo tuần tra, chase, cắn mất Máu và nửa giỏ LIFO, recoil) | Chạy test `test_monster_chase_and_hit` trong `tests/test_p2.py` | `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-04** (Quán: 2 bếp, 4 bàn, 6 món ăn, lọc món theo day_plan) | Kiểm thử tích hợp Quán và chạy unit tests trong `tests/test_quan.py` | `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-05** (Vòng ngày: Day mode, day_plan D1-D5, luồng Gather -> Quán -> Shop) | Chạy test `test_day_mode_flow` và chạy headless `--mode day --days 1` | `docs/proof/phase-2/day-1.jsonl`, `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-06** (Shop: Mua nâng cấp oxy/hp, hiệu lực ngày kế tiếp) | Chạy test `test_shop_buy_oxygen_upgrade` kiểm tra event `bought` và trừ tiền | `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-07** (Pause / Resume: Dừng mọi gameplay timer, bấm tiếp tục) | Chạy test `test_pause_and_resume` kiểm tra phát sự kiện `paused` và `resumed` | `docs/proof/phase-2/test-results.txt` | **Đạt** |
| **AC-P2-08** (Hồi quy P1): Toàn bộ 49 unit tests đều xanh sạch | Chạy `python3 -m unittest discover -s tests -v` | `docs/proof/phase-2/test-results.txt` | **Đạt** |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:**
  - Hoàn thành đầy đủ 100% yêu cầu cốt lõi của Phase 2 (Test Contract v1.1).
  - Toàn bộ cơ chế cá bơi, quái Cá Sấu, Shop nâng cấp và Vòng ngày Day chạy mượt mà, độc lập và tất định.
- **Điều cần chỉnh cho phase sau (Bàn giao Thành viên 2):**
  - Chuyển giao toàn bộ source code đã pass test cho Thành viên 2 tiếp quản.
  - Sẵn sàng mở rộng kịch bản Phase 3 (các sự kiện biến cố ngày, thử thách thời tiết hoặc cơ chế nâng cao).
