"""Unit tests for Quán Sim (Buổi tối: Mở Quán)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestQuanSim(unittest.TestCase):
    def test_customer_arrival_and_no_dish(self):
        """Khi đến first_customer_tick (tick 120): nếu không có nguyên liệu -> phát no_dish."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {}}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "125",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            no_dish_evs = events(rows, "no_dish")
            self.assertEqual(len(no_dish_evs), 1)

    def test_customer_arrival_with_stock(self):
        """Khi có nguyên liệu: khách đến tại tick 120, đặt món và giữ chỗ nguyên liệu."""
        with Workdir() as w:
            # cá lóc nướng trui: cần 1 cá lóc
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 2}}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "125",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            arr_evs = events(rows, "customer_arrived")
            self.assertEqual(len(arr_evs), 1)
            self.assertEqual(arr_evs[0]["data"]["table_id"], "T1")
            self.assertEqual(arr_evs[0]["data"]["dish_id"], "ca_loc_nuong_trui")

    def test_cooking_and_serving_flow(self):
        """Khách ngồi bàn T1 chờ cá lóc nướng trui -> Út Sen nấu tại B1 -> bưng món -> phục vụ -> khách ăn và trả tiền."""
        with Workdir() as w:
            # Bếp B1 ở [2, 8], Bàn T1 ở [9, 2]
            # Dựng tình huống: Khách C1 đã ngồi bàn T1, stock có 1 ca_loc
            sc = write_json(w.path("sc.json"), {"quan": {
                "player": {"pos": [2, 8]},  # đứng ngay tại bếp B1
                "stock": {"ca_loc": 1},
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved"}]
            }})
            # tick 0: bấm interact tại bếp B1 (bắt đầu nấu, mất 6s = 360 ticks)
            # tick 365: bếp đã chín -> bấm interact bốc món lên tay
            # sau đó di chuyển sang bàn T1 [9, 2] và bấm interact phục vụ
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 365, "interact": True},
                {"tick": 366, "interact": False}
            ))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "370",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))

            cook_evs = events(rows, "cook_started")
            self.assertEqual(len(cook_evs), 1)
            self.assertEqual(cook_evs[0]["data"]["stove_id"], "B1")
            self.assertEqual(cook_evs[0]["data"]["dish_id"], "ca_loc_nuong_trui")

            ready_evs = events(rows, "dish_ready")
            self.assertEqual(len(ready_evs), 1)
            self.assertEqual(ready_evs[0]["tick"], 361)

            pick_evs = events(rows, "dish_picked")
            self.assertEqual(len(pick_evs), 1)
            self.assertEqual(pick_evs[0]["data"]["order_id"], "C1")

            # Món đang trên tay ở snapshot cuối
            last_snap = snapshots(rows)[-1]
            self.assertIsNotNone(last_snap["hand"])
            self.assertEqual(last_snap["hand"]["dish_id"], "ca_loc_nuong_trui")

    def test_serving_and_eating_paid(self):
        """Út Sen đang cầm món đứng tại bàn T1 -> interact giao món -> khách ăn xong trả tiền + boa."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {
                "player": {"pos": [9, 2]},  # tại bàn T1
                "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60},
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                               "state": "waiting", "order_status": "assigned", "patience_ticks_left": 3000}]
            }})
            # tick 0: interact giao món. Món ăn cần 10s = 600 ticks ăn xong
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False}
            ))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "605",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))

            serv_evs = events(rows, "served")
            self.assertEqual(len(serv_evs), 1)
            self.assertEqual(serv_evs[0]["data"]["table_id"], "T1")
            # Boa: base_price = 60, tip_rate = 0.2 -> 12
            self.assertEqual(serv_evs[0]["data"]["tip"], 12)

            paid_evs = events(rows, "paid")
            self.assertEqual(len(paid_evs), 1)
            self.assertEqual(paid_evs[0]["data"]["amount"], 72)
            self.assertEqual(paid_evs[0]["data"]["reason"], "finished_eating")

    def test_customer_left_when_patience_expires(self):
        """Khách chờ hết kiên nhẫn (patience_ticks_left = 1) -> rời bàn, bị trừ uy tín."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                               "state": "waiting", "patience_ticks_left": 2}],
                "reputation": 3.0
            }})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))

            left_evs = events(rows, "customer_left")
            self.assertEqual(len(left_evs), 1)
            self.assertEqual(left_evs[0]["data"]["reason"], "patience")
            # Uy tín giảm 0.5 (từ 3.0 còn 2.5)
            self.assertEqual(left_evs[0]["data"]["reputation"], 2.5)


if __name__ == "__main__":
    unittest.main()
