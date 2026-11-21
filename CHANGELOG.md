# CHANGELOG

## [v1.0.0] - Phase 4 (2026-11-21)
### Added
- Khai báo Test Contract v1.3: hỗ trợ các lệnh kiểm chứng tự động `bench_cmd` và `soak_cmd`.
- Module benchmark `chonoi/bench.py` đo 5 chỉ số hiệu năng chuẩn: FPS trung bình, 1% low FPS, frames, thời gian đo và load_ms.
- Module soak test `chonoi/soak.py` kiểm thử độ bền 10 ngày liên tục không crash, bảo toàn điểm số và trạng thái.
- Cảnh báo trực quan (Cá sấu gần, oxy thấp, khách sắp giận) và chế độ High Contrast trên giao diện web.
- Bộ test suite `tests/test_p4.py` và bằng chứng nghiệm thu tại `docs/proof/phase-4/`.

## [Phase 3] - Mùa Nước Nổi (2026-11-21)
### Added
- Nâng cấp Test Contract v1.2: chuyển đổi sang schema kho cá thể `{"items": [{"id": ..., "kind": ..., "fresh": ...}]}`.
- Cơ chế hao độ tươi (0.5/s ở gather, 0.25/s ở quán); phát sự kiện `spoiled` khi `fresh < 30`.
- Cơ chế giữ chỗ theo cá thể tươi nhất và tự động re-reserve khi cá thể đang giữ bị ươn.
- Chốt giá động theo độ tươi: `base_price = floor(giá niêm yết * trung bình fresh / 100)`.
- Mở rộng Dòng Nước Lũ (`current`): cảnh báo trước 120 tick, lực đẩy 1.5 m/s ở độ sâu $d \ge 10$.
- Bộ test suite `tests/test_p3.py` và bằng chứng nghiệm thu tại `docs/proof/phase-3/`.

### Breaking Changes
- File kho `inventory.json` đếm v1.0 bị từ chối với mã lỗi 2, bắt buộc dùng schema mảng cá thể.

## [Phase 2] - Một ngày ở chợ nổi (2026-11-21)
### Added
- Test Contract v1.1: 6 loại nguyên liệu, thực đơn 6 món ăn.
- Cá bơi 1.5 m/s, đổi hướng và phản xạ mép; sinh cá định kỳ mỗi 360 tick.
- Quái vật Cá Sấu Năm Chèo (M1, M2): tuần tra, truy đuổi, cắn mất máu và nửa giỏ LIFO.
- Chế độ Day loop (`--mode day`), shop nâng cấp bình oxy và phao cứu sinh, cơ chế Pause / Resume toàn cục.

## [Phase 1] - Khởi động (2026-11-21)
### Added
- Lõi mô phỏng Gather: lặn, bơi, oxy, ngạt thở, hái nút và bắt cá.
- Lõi mô phỏng Quán: khách đến, giữ chỗ nguyên liệu, nấu nướng, phục vụ, boa và tính uy tín.
- Bộ test kiểm tra Test Contract v1.0 (44 tests).
