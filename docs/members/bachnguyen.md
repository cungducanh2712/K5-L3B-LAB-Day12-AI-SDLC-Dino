# Phản tư cá nhân — Nguyễn Ngọc Bách

- **GitHub handle:** `bachnguyen`
- **Module chính phụ trách:** `sim/gather` (độ tươi & LIFO cá thể, current dòng nước lũ), `sim/quan` (kho cá thể, spoil, giữ chỗ id, chốt giá fresh), `inventory` (Contract v1.2, schema items mảng cá thể), `bench/soak` (Benchmark render chuẩn, soak 10 days), QA & Release (Phase 3 & 4).

## 1. Phần việc đã làm trong Phase 3 & 4
- **Phase 3:**
  - Nâng cấp `game.contract.json` lên Test Contract v1.2 (`contract_version: "1.2"`), cấu hình độ tươi `freshness` (initial 100, gather_decay 0.5/s, quan_decay 0.25/s, spoiled_below 30).
  - Cải tiến toàn diện module `chonoi/inventory.py` hỗ trợ kho cá thể `{ "items": [ {"id": ..., "kind": ..., "fresh": ...} ] }`, tự động sinh mã lỗi 2 cho kho cũ hoặc sai schema.
  - Hiện thực logic hao tươi, phát sinh sự kiện `spoiled` (đúng một lần khi rơi từ >=30 xuống <30), cơ chế giữ chỗ nguyên liệu theo cá thể tươi nhất và fallback re-reserve trong `sim/quan.py`.
  - Triển khai tính giá động: chốt `base_price = floor(giá niêm yết * trung bình fresh / 100)` và tính tip trên giá đã chốt.
  - Xây dựng mở rộng Dòng Nước Lũ (`current`) chu kỳ 1800 tick với warning trước 120 tick, lực đẩy 1.5 m/s ở độ sâu $d \ge 10$.
  - Viết bộ kiểm thử toàn diện `tests/test_p3.py` và lưu trữ bằng chứng tại `docs/proof/phase-3/`.
- **Phase 4:**
  - Nâng cấp `game.contract.json` lên Test Contract v1.3 (`contract_version: "1.3"`), khai báo `bench_cmd` và `soak_cmd`.
  - Viết module `chonoi/bench.py` đo FPS, 1% low FPS, thời gian load theo chuẩn yêu cầu.
  - Viết module `chonoi/soak.py` kiểm thử độ bền bỉ 10 ngày headless không crash.
  - Bổ sung cảnh báo dễ nhận biết trên giao diện web (Cá sấu gần, oxy thấp, khách sắp giận) và chế độ High Contrast.
  - Viết bộ kiểm thử `tests/test_p4.py`, xuất kết quả benchmark tại `docs/proof/phase-4/`.

## 2. Phối hợp nhóm & Hỗ trợ
- Tiếp nhận bàn giao trơn tru từ Thành viên 1 (Cung Đức Anh) sau Phase 2, kế thừa kiến trúc sạch và 49 tests ban đầu.
- Giữ vững quy tắc Test-Driven Development (TDD) và bảo đảm tính tương thích hồi quy (backward compatibility), duy trì 100% tests xanh.

## 3. Lỗi AI phát hiện và cách khắc phục
- Khi AI hỗ trợ viết thuật toán hao độ tươi ở ngưỡng 30, AI từng dùng phép chia float thông thường dẫn đến sai số số thực (vd: 29.999999999999996 thay vì 30.0). Tôi đã phát hiện và chuẩn hóa dùng đơn vị nguyên hoặc làm tròn `round(..., 4)` kèm so sánh ngưỡng chính xác để sự kiện `spoiled` luôn phát đúng tick biên.

## 4. Bài học rút ra
- Kiểm soát hợp đồng (Test Contract) chặt chẽ giữa các bên giúp việc tích hợp giữa các ca làm việc lệch giờ diễn ra hoàn toàn không có xung đột.
