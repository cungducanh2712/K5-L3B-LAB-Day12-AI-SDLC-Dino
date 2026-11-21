"""Unit tests for Phase 3 (Mùa Nước Nổi — Test Contract v1.2)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestPhase3(unittest.TestCase):
    def test_p3_spoiled_threshold_gather(self):
        """Chạy gather một bước không input: cá thể fresh=30 hao tươi xuống <30 phát spoiled."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                    "random_fish": False,
                    "monsters": []
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp_evs = events(rows, "spoiled")
            self.assertEqual(len(sp_evs), 1)
            self.assertEqual(sp_evs[0]["tick"], 1)
            self.assertEqual(sp_evs[0]["data"]["item_id"], "I1")
            self.assertEqual(sp_evs[0]["data"]["kind"], "ca_linh")
            self.assertEqual(sp_evs[0]["data"]["location"], "hold")

    def test_p3_smoke_inventory_transfer_file(self):
        """Smoke bàn giao file v1.2: gather cập bến ghi kho cá thể, quán đọc chính xác id và độ tươi."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                    "random_fish": False,
                    "monsters": []
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--inventory-out", inv,
                                     "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertIn("items", saved)
            self.assertEqual(len(saved["items"]), 1)
            self.assertEqual(saved["items"][0]["id"], "I1")
            self.assertEqual(saved["items"][0]["kind"], "ca_linh")
            # Hao ở tick 1: 100 - 0.5/60 = 99.9917
            self.assertAlmostEqual(saved["items"][0]["fresh"], 100.0 - (0.5 / 60.0), places=2)

            # Quán đọc kho này
            code, err = run_headless("--mode", "quan", "--seed", "42", "--ticks", "0",
                                     "--inventory", inv, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            snap = snapshots(read_jsonl(w.path("q.jsonl")))[0]
            self.assertEqual(len(snap["stock"]), 1)
            self.assertEqual(snap["stock"][0]["id"], "I1")
            self.assertEqual(snap["stock"][0]["kind"], "ca_linh")
            self.assertAlmostEqual(snap["stock"][0]["fresh"], saved["items"][0]["fresh"], places=3)

    def test_p3_quan_re_reserve_when_item_spoils(self):
        """Nếu cá thể đang giữ bị ươn (<30), quán nhả ra và giữ lại cá thể tươi nhất khả dụng."""
        with Workdir() as w:
            # Kho có I1 (fresh=30.003 - sắp ươn sau 1 tick) và I2 (fresh=90.0)
            # Khách C1 cần 1 cá lóc, ban đầu được giữ I1
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 30.002},
                        {"id": "I2", "kind": "ca_loc", "fresh": 90.0}
                    ],
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                         "order_status": "reserved", "reserved": ["I1"]}
                    ]
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp_evs = events(rows, "spoiled")
            self.assertEqual(len(sp_evs), 1)
            self.assertEqual(sp_evs[0]["data"]["item_id"], "I1")

            # Ở tick 2, khách C1 phải được re-reserve sang I2
            last_snap = snapshots(rows)[-1]
            c1 = next(c for c in last_snap["customers"] if c["id"] == "C1")
            self.assertEqual(c1["reserved"], ["I2"])
            self.assertEqual(c1["order_status"], "reserved")

    def test_p3_dynamic_pricing_by_freshness(self):
        """Bắt đầu nấu: chốt base_price = floor(giá niêm yết * trung bình fresh / 100)."""
        with Workdir() as w:
            # Món ca_loc_nuong_trui giá niêm yết 60, cá lóc có fresh = 80.01 -> sau 1 tick hao 0.25/60 ~= 0.00416, fresh > 80.0 -> base_price = floor(60 * 80.00... / 100) = 48
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 8]},
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 80.01}],
                    "customers": [
                        {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                         "order_status": "reserved", "reserved": ["I1"]}
                    ]
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            cook_evs = events(rows, "cook_started")
            self.assertEqual(len(cook_evs), 1)
            self.assertEqual(cook_evs[0]["data"]["base_price"], 48)

    def test_p3_extension_current_water_flow(self):
        """Mở rộng Dòng Nước Lũ (current): cảnh báo t-120, lực đẩy 1.5 m/s ở d >= 10."""
        with Workdir() as w:
            # Kích hoạt current với direction = 1 (+x), bắt đầu ngay khi tick=1800
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "player": {"pos": [50.0, 15.0]},  # d = 15 >= 10
                    "time_left_ticks": 1900,
                    "current_direction": 1
                }
            })
            # Chạy qua mốc 1680 (warning) và 1800 (start)
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1805",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            warn_evs = events(rows, "current_warning")
            start_evs = events(rows, "current_start")
            self.assertGreaterEqual(len(warn_evs), 1)
            self.assertGreaterEqual(len(start_evs), 1)
            self.assertEqual(start_evs[0]["data"]["direction"], 1)


if __name__ == "__main__":
    unittest.main()
