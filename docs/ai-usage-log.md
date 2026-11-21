# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Lên kế hoạch, chia việc 2 người, cấu hình môi trường Windows python3 | ~15,000 tokens | Không có lỗi logic lớn |
| Phase 1 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Hiện thực `sim/gather.py` (Lát 1 + Lát 2: oxy, ngạt, LIFO, hái, bắt cá) | ~25,000 tokens | AI viết test ban đầu đặt `zero_oxy_ticks: 30` ở mặt nước làm `scenario.py` bắt lỗi mã 2; phát hiện qua unittest và sửa lại test hợp lệ |
| Phase 1 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Hiện thực `sim/quan.py` (Lát 3 + Lát 4: khách, bếp, bưng bê, tip, rời bàn) | ~30,000 tokens | Khớp hoàn toàn contract |
| Phase 1 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Viết bộ test `test_gather.py`, `test_quan.py` và tạo bằng chứng proof | ~20,000 tokens | Không có lỗi |
| Phase 2 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Cập nhật contract v1.1, schema 6 nguyên liệu 6 món, nodes N5-N6 | ~20,000 tokens | Khớp chính xác ticket P2 |
| Phase 2 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Nâng cấp `sim/gather.py`: đàn cá bơi/phản xạ, lịch sinh cá, Cá Sấu Năm Chèo | ~35,000 tokens | Tính toán phản xạ vector tại biên chuẩn xác |
| Phase 2 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Hiện thực `DaySim`, Shop nâng cấp và cơ chế Pause/Resume toàn cục | ~30,000 tokens | AI ban đầu chỉ cài Pause ở DaySim và đổi default `load_frames` làm fail 2 test P1; phát hiện qua test suite và refactor lên Session |
| Phase 2 | Cung Đức Anh (Thành viên 1) | Antigravity (Gemini 3.8 Flash) | Viết `tests/test_p2.py`, tạo bằng chứng proof và chuẩn bị bàn giao | ~15,000 tokens | 49/49 tests PASS |
| Phase 3 | Nguyễn Ngọc Bách (Thành viên 2) | Antigravity (Gemini 3.8 Flash) | Nâng cấp Test Contract v1.2, kho cá thể, logic hao tươi và ươn | ~25,000 tokens | AI ban đầu so sánh chuỗi ngày và float rounding làm lệch 1 tick event spoiled; phát hiện qua unit test và sửa chính xác |
| Phase 3 | Nguyễn Ngọc Bách (Thành viên 2) | Antigravity (Gemini 3.8 Flash) | Triển khai re-reserve khi nguyên liệu giữ bị ươn, chốt giá theo fresh | ~30,000 tokens | Không có lỗi lớn |
| Phase 3 | Nguyễn Ngọc Bách (Thành viên 2) | Antigravity (Gemini 3.8 Flash) | Mở rộng Dòng Nước Lũ (`current`), viết `tests/test_p3.py` | ~25,000 tokens | AI quên khai báo cờ scenario `current_direction` làm test báo mã 2; sửa lại `GATHER_KEYS` |
| Phase 4 | Nguyễn Ngọc Bách (Thành viên 2) | Antigravity (Gemini 3.8 Flash) | Test Contract v1.3, xây dựng `chonoi/bench.py` và `chonoi/soak.py` | ~25,000 tokens | AI gọi nhầm `Streams.get("current", ...)` với 2 đối số; phát hiện qua benchmark và sửa lại |
| Phase 4 | Nguyễn Ngọc Bách (Thành viên 2) | Antigravity (Gemini 3.8 Flash) | Cảnh báo đồ họa & High Contrast, hoàn thiện Release v1.0.0 & tài liệu | ~20,000 tokens | Khớp 100% tiêu chí nghiệm thu |
