"""Unit tests for Phase 4 (Phát hành v1.0.0 — Test Contract v1.3)."""

import json
import os
import unittest

from helpers import Workdir, run_headless, write_json


class TestPhase4(unittest.TestCase):
    def test_p4_bench_command_and_json_structure(self):
        """Lệnh bench chạy thành công và tạo ra file bench.json chuẩn cấu trúc 5 trường."""
        with Workdir() as w:
            bench_out = w.path("bench.json")
            code = os.system(f"python3 -m chonoi.bench --seed 42 --duration 2 --out {bench_out}")
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(bench_out))
            with open(bench_out, encoding="utf-8") as f:
                data = json.load(f)
            for k in ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"):
                self.assertIn(k, data)
            self.assertGreaterEqual(data["avg_fps"], 60.0)
            self.assertGreaterEqual(data["p1_low_fps"], 30.0)
            self.assertLessEqual(data["load_ms"], 10000.0)

    def test_p4_soak_command_and_json_structure(self):
        """Lệnh soak chạy headless mượt mà và hoàn thành đúng số ngày yêu cầu mà không bị crash."""
        with Workdir() as w:
            soak_out = w.path("soak.json")
            code = os.system(f"python3 -m chonoi.soak --seed 7 --days 2 --out {soak_out}")
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(soak_out))
            with open(soak_out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["days"], 2)
            self.assertEqual(data["days_completed"], 2)
            self.assertEqual(data["crashes"], 0)
            self.assertEqual(len(data["results"]), 2)


if __name__ == "__main__":
    unittest.main()
