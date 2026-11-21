---
name: verify-phase
description: Chạy kiểm thử toàn bộ hệ thống (unit tests và team validation) trước khi gắn tag phase
---

# Skill: Verify Phase

Sử dụng skill này trước khi commit hoặc gắn tag cho mỗi phase để đảm bảo không làm gãy test contract:

1. Chạy toàn bộ test suite:
   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```
2. Kiểm tra danh sách thành viên và hợp đồng:
   ```bash
   python3 tools/check_team.py
   ```
3. Đảm bảo 100% tests PASS trước khi push hoặc gắn tag git.
