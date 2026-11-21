# Day 12 — AI SDLC: Quán Ăn Chợ Nổi (Nhóm Dino - Release v1.0.0)

> Dự án game 2D Quán Ăn Chợ Nổi xây dựng theo mô hình AI Native SDLC qua 4 phase: Út Sen lặn bắt cá, hái rau mùa nước nổi rồi tối mở quán phục vụ thực khách phương xa.

## Hướng dẫn chạy nhanh (3 lệnh chuẩn sạch trên Linux/macOS/Windows)

```bash
# 1. Chạy toàn bộ bộ test kiểm chứng tự động (56 tests 100% PASS)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v

# 2. Chạy benchmark cảnh lặn (FPS, 1% low, load time)
python3 -m chonoi.bench --seed 42 --duration 30 --out docs/proof/phase-4/bench.json

# 3. Trải nghiệm trực tiếp trên trình duyệt Web (WASD để bơi/đi, Space: lặn, E: tương tác/hái/nấu, C: bắt cá)
python3 -m chonoi.live --mode gather
```

## Các lệnh Headless theo Test Contract v1.3
- **Chạy Gather:** `python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl`
- **Chạy Quán:** `python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --out out.jsonl`
- **Chạy Vòng Ngày (Day mode):** `python3 -m chonoi.headless --mode day --days 5 --seed 1 --ticks 3000 --out day.jsonl`
- **Chạy Soak Test (10 ngày liên tục):** `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`

## Sáng tạo của nhóm
1. **Dòng Nước Lũ Mùa Nước Nổi (`current`):**
   - Chu kỳ 1800 tick, cảnh báo trực quan trước 120 tick. Lực dòng chảy cuốn trôi 1.5 m/s ở độ sâu $d \ge 10$, tạo thử thách chân thực cho cảnh lặn.
2. **Cảnh báo trợ năng & Tương phản cao (Accessibility):**
   - Cảnh báo đồ họa và chữ rõ nét khi Cá Sấu lại gần, khi bình oxy sắp cạn (<5s) và khi khách hàng sắp hết kiên nhẫn.
   - Hỗ trợ chế độ High Contrast Mode cho người khiếm thị màu.
3. **Hiệu năng siêu việt (High Performance):**
   - Benchmark đạt trên **27,000 FPS** trên máy thông thường, thời gian khởi động cảnh lặn dưới **6 mili-giây** (vượt xa tiêu chuẩn 60 FPS / 10s của ban giám khảo).

## Lịch sử phát triển & Bàn giao qua 4 Phase
- **Phase 1 (Tag `phase-1`):** Lõi mô phỏng lặn bắt cá và mở quán theo Test Contract v1.0 (Thành viên 1 thực hiện).
- **Phase 2 (Tag `phase-2`):** Test Contract v1.1, Cá bơi/sinh, Cá Sấu Năm Chèo, vòng ngày Day loop và Shop nâng cấp (Thành viên 1 thực hiện).
- **Phase 3 (Tag `phase-3`):** Test Contract v1.2, Kho cá thể, độ tươi & hao hụt, ươn, re-reserve, giá động theo fresh, Dòng nước lũ (Thành viên 2 thực hiện).
- **Phase 4 (Tag `phase-4` + Release `v1.0.0`):** Test Contract v1.3, Benchmarking, Soak testing 10 ngày, Cảnh báo trực quan & Đóng gói sản phẩm hoàn chỉnh (Thành viên 2 thực hiện).
