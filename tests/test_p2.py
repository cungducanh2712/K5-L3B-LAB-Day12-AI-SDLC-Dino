"""Unit tests for Phase 2 (Test Contract v1.1)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestPhase2(unittest.TestCase):
    def test_monster_chase_and_hit(self):
        """Cá Sấu Năm Chèo tuần tra, phát hiện người chơi chuyển chase, cắn trúng làm mất 1 Máu và nửa giỏ LIFO."""
        with Workdir() as w:
            # Người chơi ở [60, 20] (d >= 10), mang 4 con cá
            # Cá Sấu M1 ở [60, 24] (cách 4m <= 10m -> chase ngay)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [60, 22.8], "hp": 3},  # cách cá sấu 1.2m <= 1.5m
                "hold": ["ca_loc", "ca_linh", "ca_keo", "bong_sung"],
                "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60, 24], "waypoints": [[60, 24], [64, 24]]}],
                "random_fish": False
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hits = events(rows, "monster_hit")
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["data"]["monster_id"], "M1")
            self.assertEqual(hits[0]["data"]["hp"], 2)
            # Rơi floor(4/2) = 2 con: bong_sung, ca_keo (LIFO)
            self.assertEqual(hits[0]["data"]["lost"], ["bong_sung", "ca_keo"])

    def test_fish_swimming_and_turning(self):
        """Đàn cá bơi và phản xạ mép x ∈ [4, 96]."""
        with Workdir() as w:
            # Cá lóc F1 ở sát mép [95.9, 10], hướng 0 độ (về phía +x)
            sc = write_json(w.path("sc.json"), {"gather": {
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [95.9, 10], "heading_deg": 0.0, "age_ticks": 0}],
                "random_fish": False
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snaps = snapshots(rows)
            # Sau khi chạm 96, cá phải phản xạ quay lại (x < 96)
            last_fish = snaps[-1]["fish"][0]
            self.assertLessEqual(last_fish["pos"][0], 96.0)
            self.assertGreaterEqual(last_fish["pos"][0], 4.0)

    def test_day_mode_flow(self):
        """Mode day: công bố day_plan, bắt đầu gather, cập bến chuyển quán, hết ca chuyển shop."""
        with Workdir() as w:
            # Bắt đầu tại bến, tick 0 interact cập bến ngay
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False}
            ))
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "2",
                                     "--inputs", inp, "--days", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            names = [r["name"] for r in rows if r["type"] == "event"]
            self.assertIn("day_start", names)
            self.assertIn("day_plan", names)
            self.assertIn("phase_start", names)

    def test_shop_buy_oxygen_upgrade(self):
        """Trong Shop, người chơi mua nâng cấp bình oxy cấp 1 với 200k."""
        with Workdir() as w:
            # Tạo tình huống ở Shop với money = 300
            sc = write_json(w.path("sc.json"), {
                "day": {"money": 300, "earned": 300},
                "gather": {"time_left_ticks": 1},
                "quan": {"time_left_ticks": 1}
            })
            # Sau 2 tick (gather 1 tick hết, quan 1 tick hết), bước vào Shop
            # Tick 2: gửi lệnh mua oxy cấp 1 (giá 200)
            inp = write_json(w.path("in.json"), frames(
                {"tick": 2, "buy": "oxygen"},
                {"tick": 3, "shop_done": True}
            ))
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--days", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            bought_evs = events(rows, "bought")
            self.assertEqual(len(bought_evs), 1)
            self.assertEqual(bought_evs[0]["data"]["upgrade"], "oxygen")
            self.assertEqual(bought_evs[0]["data"]["level"], 1)
            self.assertEqual(bought_evs[0]["data"]["price"], 200)
            self.assertEqual(bought_evs[0]["data"]["money"], 100)

    def test_pause_and_resume(self):
        """Nút pause tạm dừng game (state: paused), bấm tiếp tục (resumed)."""
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames(
                {"tick": 1, "pause": True},
                {"tick": 2, "pause": False},
                {"tick": 3, "pause": True},
                {"tick": 4, "pause": False}
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "6",
                                     "--inputs", inp, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            p_evs = events(rows, "paused")
            r_evs = events(rows, "resumed")
            self.assertEqual(len(p_evs), 1)
            self.assertEqual(len(r_evs), 1)


if __name__ == "__main__":
    unittest.main()
