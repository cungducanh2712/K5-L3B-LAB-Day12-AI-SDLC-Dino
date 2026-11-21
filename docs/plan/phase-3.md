# Kế hoạch Phase 3 (Mùa Nước Nổi — Test Contract v1.2)

## Mục tiêu
- Nâng cấp game lên Test Contract v1.2:
  - **Kho cá thể:** Chuyển đổi mô hình lưu trữ nguyên liệu từ object đếm theo loại `{ca_loc: 2}` sang mảng cá thể `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`.
  - **Độ tươi & Hao hụt (Freshness & Decay):**
    - Initial fresh = 100 lúc hái/bắt, hao từ tick kế tiếp.
    - Giỏ gather hao 0.5/s (0.5/60 mỗi tick), Quán hao 0.25/s (0.25/60 mỗi tick).
    - Ngưỡng ươn: `fresh < 30`, phát sự kiện `spoiled` đúng một lần theo thứ tự id.
  - **Giữ chỗ & Giá động:**
    - Quán giữ chỗ theo cá thể tươi nhất khả dụng.
    - Khi cá thể đang giữ bị ươn: nhả toàn bộ đơn và thử giữ lại đúng 1 lần theo `order_tick` và id bàn.
    - Giá chốt: `base_price = floor(giá niêm yết * avg(fresh) / 100)`. Tip tính trên giá chốt.
  - **Mở rộng Dòng nước lũ (`current`):**
    - Chu kỳ 1800 tick, cảnh báo trước 120 tick (`current_warning`).
    - Kéo dài 480 tick, lực đẩy 1.5 m/s theo hướng ngẫu nhiên hoặc cố định nếu $d \ge 10$.
    - Kết thúc phát `current_end`.

## Phân công (Thành viên 2 — Nguyễn Ngọc Bách)
- Nâng cấp `chonoi/contract.py` và `chonoi/inventory.py`.
- Nâng cấp `chonoi/sim/gather.py`, `chonoi/sim/quan.py`, `chonoi/sim/day.py`.
- Viết test suite `tests/test_p3.py`, sinh bằng chứng `docs/proof/phase-3/`.
- Cập nhật ma trận `docs/verification/phase-3.md`, nhật ký `ai-usage-log.md` và `CHANGELOG.md`.
