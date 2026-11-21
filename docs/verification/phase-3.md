# Ma trận truy vết Phase 3

| AC | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| **AC-P3-01** (Contract v1.2 Kho cá thể) | Đọc `game.contract.json`, kiểm tra schema `{items: [{id, kind, fresh}]}` trong `chonoi/inventory.py` | `docs/proof/phase-3/test-results.txt` | **Đạt** |
| **AC-P3-02** (Hao tươi & Ươn) | Chạy test `test_p3_spoiled_threshold_gather` (fresh < 30 phát spoiled) | `docs/proof/phase-3/test-results.txt` | **Đạt** |
| **AC-P3-03** (Bàn giao file nguyên tử) | Chạy test `test_p3_smoke_inventory_transfer_file` (gather cập bến ghi kho cá thể, quán đọc nguyên vẹn id và fresh) | `docs/proof/phase-3/test-results.txt` | **Đạt** |
| **AC-P3-04** (Giữ chỗ cá thể & Giữ lại khi ươn) | Chạy test `test_p3_quan_re_reserve_when_item_spoils` | `docs/proof/phase-3/test-results.txt` | **Đạt** |
| **AC-P3-05** (Chốt giá theo tươi) | Chạy test `test_p3_dynamic_pricing_by_freshness` (base_price = floor(giá niêm yết * avg(fresh) / 100)) | `docs/proof/phase-3/test-results.txt` | **Đạt** |
| **AC-P3-06** (Mở rộng Dòng Nước Lũ) | Chạy test `test_p3_extension_current_water_flow` (cảnh báo 120 tick, lực đẩy 1.5 m/s ở d >= 10) | `docs/proof/phase-3/test-results.txt` | **Đạt** |
| **AC-P3-07** (Hồi quy P1-P2) | Chạy 54/54 tests trong test suite | `docs/proof/phase-3/test-results.txt` | **Đạt** (54/54 PASS) |

## Đánh giá ngắn
- Toàn bộ yêu cầu cốt lõi của Phase 3 (Test Contract v1.2) cùng tính năng mở rộng Dòng Nước Lũ đã được kiểm chứng thành công.
- Không có lỗi hồi quy đối với các tính năng Phase 1 và Phase 2.
