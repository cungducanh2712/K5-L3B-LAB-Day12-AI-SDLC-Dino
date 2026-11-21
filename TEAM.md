# TEAM

**Tên nhóm:** Dino  **Số người:** 2  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Cung Đức Anh (Ca 1 - làm trước) | `cungducanh2712` | `sim/gather`, `sim/quan`, `day loop` (Phase 1, 2) | PO, Integrator (tag phase-1, 2) | Nguyễn Ngọc Bách |
| Nguyễn Ngọc Bách (Ca 2 - làm sau) | `bachnguyen` | `sim/gather`, `sim/quan`, `inventory`, `bench/soak`, QA (Phase 3, 4) | QA lead, Release (tag phase-3, 4) | Cung Đức Anh |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Có thể kiêm.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Kênh chat chính của nhóm (Zalo / Discord), cập nhật trạng thái khi chuyển giao ca.
- Phân chia ca: Thành viên 1 làm trước (Phase 1 & Phase 2: Core simulation, headless, contract, test suite); Thành viên 2 làm ca tiếp theo (Phase 3 & Phase 4: UI, mở rộng tính năng, sáng tạo và QA cuối).
- Khi bất đồng về thiết kế: Bám sát `game.contract.json` và PRD; người đang trực tiếp chạy ca đó đưa ra quyết định cuối cùng để đảm bảo tiến độ.
- Khi vướng mắc hoặc trễ: Thông báo ngay lên nhóm chat trong vòng 10 phút, ghi chú lại điểm nghẽn vào `docs/standup.md` để người kia hỗ trợ.
- Giờ standup giữa phase: Họp nhanh 5 phút khi bàn giao giữa Phase 2 và Phase 3 để chuyển giao mã nguồn và hướng dẫn chạy test.
- Cách đọc code của nhau: Review trực tiếp qua git log và các tài liệu nghiệm thu trong `docs/verification/` & `docs/proof/`.
- Cách làm việc với Git: Nhóm 2 người làm việc tuần tự theo ca trên nhánh `main`, commit rõ ràng theo Conventional Commits (tối thiểu 3 commit/phase), bảo đảm test pass 100% trước khi tạo tag `phase-X` và push.
