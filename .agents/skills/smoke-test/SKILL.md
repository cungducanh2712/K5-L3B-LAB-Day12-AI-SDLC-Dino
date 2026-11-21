---
name: smoke-test
description: Chạy smoke test tích hợp 2 tiến trình độc lập Gather -> Quán và xuất kết quả bằng chứng
---

# Skill: Smoke Test 2 Tiến Trình

Sử dụng skill này để tạo bằng chứng tích hợp liên tiến trình cho `docs/proof/`:

1. Chạy Gather cập bến để xuất kho:
   ```bash
   python3 -m chonoi.headless --mode gather --seed 42 --scenario docs/proof/phase-1/dock.json --inputs docs/proof/phase-1/dock-inputs.json --ticks 1 --out docs/proof/phase-1/gather.jsonl --inventory-out docs/proof/phase-1/catch.json
   ```
2. Chạy Quán đọc file kho vừa xuất:
   ```bash
   python3 -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-1/catch.json --ticks 0 --out docs/proof/phase-1/quan.jsonl
   ```
3. Xác nhận `catch.json` và `stock` trong `quan.jsonl` khớp nhau từng byte.
