# Ma trận truy vết Phase 4 (Phát hành v1.0.0)

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| **AC-P4-01** (Contract v1.3 & bench_cmd/soak_cmd) | Kiểm tra `game.contract.json` có `contract_version: "1.3"`, khai báo `bench_cmd` và `soak_cmd` | `game.contract.json` | **Đạt** |
| **AC-P4-02** (Benchmark render) | Chạy `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json`, xuất đủ 5 trường: avg_fps >= 60, p1_low >= 30, load_ms <= 10s | `docs/proof/phase-4/bench.json`, `docs/proof/phase-4/test-results.txt` | **Đạt** (avg_fps > 27,000 FPS, load_ms < 6ms) |
| **AC-P4-03** (Soak headless 10 ngày) | Chạy `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`: `days_completed: 10`, `crashes: 0`, bảo toàn trạng thái qua 10 ngày | `docs/proof/phase-4/soak.json`, `docs/proof/phase-4/test-results.txt` | **Đạt** (10/10 ngày hoàn thành, 0 crash) |
| **AC-P4-04** (Cảnh báo dễ nhận biết & High Contrast) | Tích hợp cảnh báo cá sấu gần, oxy thấp, khách sắp giận và chế độ tương phản cao trong UI | `chonoi/web/index.html` | **Đạt** |
| **AC-P4-05** (Kiểm tra hồi quy toàn diện) | Chạy toàn bộ 56 tests bao gồm P1, P2, P3 và P4 | `docs/proof/phase-4/test-results.txt` | **Đạt** (56/56 PASS) |

## Đánh giá ngắn
- Game đạt độ ổn định rất cao, sẵn sàng phát hành chính thức bản Release `v1.0.0`.
- Chế độ headless và benchmark/soak đáp ứng 100% tiêu chí chấm điểm tự động của giảng viên.
