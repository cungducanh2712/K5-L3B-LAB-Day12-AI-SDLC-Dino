"""Unit tests for Gather Sim (Buổi sáng: Lặn & Hái)."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestGatherSim(unittest.TestCase):
    def test_dive_and_surface(self):
        """Kiểm tra sự kiện dive và surface khi bơi qua lại ranh giới mặt nước (d = 0.5)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 0]}}})
            # frame 0: lặn xuống d tăng; frame 10: ngoi lên
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 10, "move": [0, -1]},
                {"tick": 20, "move": [0, 0]}
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "25",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dive_evs = events(rows, "dive")
            surface_evs = events(rows, "surface")
            self.assertGreaterEqual(len(dive_evs), 1, "Phải có sự kiện dive")
            self.assertGreaterEqual(len(surface_evs), 1, "Phải có sự kiện surface")
            self.assertIn("pos", dive_evs[0]["data"])

    def test_oxygen_depletion_and_empty_event(self):
        """Dưới nước oxy giảm 1 tick/tick, phát oxygen_empty khi chạm 0."""
        with Workdir() as w:
            # Cho oxy còn 3 tick, đang ở d = 2.0 (dưới nước)
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 2.0], "oxygen_ticks": 3}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empty_evs = events(rows, "oxygen_empty")
            self.assertEqual(len(empty_evs), 1)
            self.assertEqual(empty_evs[0]["tick"], 3)
            self.assertEqual(empty_evs[0]["data"]["oxygen_ticks"], 0)

    def test_choke_and_faint_lifo(self):
        """Dưới nước với oxy = 0: đếm đủ 60 tick bị ngạt (-1 HP). Khi HP = 0 thì ngất (faint), mất giỏ LIFO."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5.0], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
                "hold": ["ca_loc", "bong_sung", "ca_linh"]
            }})
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            choke_evs = events(rows, "choke")
            self.assertEqual(len(choke_evs), 1)
            self.assertEqual(choke_evs[0]["data"]["hp"], 0)

            faint_evs = events(rows, "faint")
            self.assertEqual(len(faint_evs), 1)
            self.assertEqual(faint_evs[0]["data"]["cause"], "choke")
            # Thứ tự nhặt: ca_loc, bong_sung, ca_linh -> LIFO mất theo thứ tự: ca_linh, bong_sung, ca_loc
            self.assertEqual(faint_evs[0]["data"]["lost"], ["ca_linh", "bong_sung", "ca_loc"])
            self.assertEqual(faint_evs[0]["data"]["hp"], 0)

            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "fainted")
            self.assertEqual(end_evs[0]["data"]["inventory"], {"items": {}})

            # File kho phải rỗng
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})

    def test_surface_refill_oxygen(self):
        """Ở mặt nước (d <= 0.5), oxy hồi 6 tick/tick."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 0.0], "oxygen_ticks": 10}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snaps = snapshots(rows)
            # Tick 1: oxy từ 10 + 6 = 16
            self.assertEqual(snaps[1]["player"]["oxygen_ticks"], 16)

    def test_gather_node_and_regrow(self):
        """Hái nút tại mặt nước: thêm nguyên liệu, đặt đếm ngược mọc lại; khi về 0 phát node_regrown."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [12, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}]
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False}
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g_evs = events(rows, "gather")
            self.assertEqual(len(g_evs), 1)
            self.assertEqual(g_evs[0]["data"]["node_id"], "N1")
            self.assertEqual(g_evs[0]["data"]["kind"], "bong_dien_dien")
            self.assertEqual(g_evs[0]["data"]["amount"], 1)

    def test_gather_hold_full(self):
        """Khi giỏ đầy (12/12): hái nút phát sự kiện hold_full, nút giữ nguyên."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [12, 0]},
                "hold": ["ca_loc"] * 12,
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}]
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            hf_evs = events(rows, "hold_full")
            self.assertEqual(len(hf_evs), 1)
            self.assertEqual(hf_evs[0]["data"]["action"], "gather")
            self.assertEqual(hf_evs[0]["data"]["node_id"], "N1")
            self.assertEqual(hf_evs[0]["data"]["required"], 1)
            self.assertEqual(hf_evs[0]["data"]["free"], 0)

    def test_catch_fish_and_cooldown(self):
        """Bắt cá dưới nước: xóa đàn cá, thêm yield vào giỏ, đặt hồi chiêu."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [15, 5]},  # tại vị trí cá F1 ca_linh
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5]}],
                "random_fish": False
            }})
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False}
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            c_evs = events(rows, "fish_caught")
            self.assertEqual(len(c_evs), 1)
            self.assertEqual(c_evs[0]["data"]["fish_id"], "F1")
            self.assertEqual(c_evs[0]["data"]["kind"], "ca_linh")
            self.assertEqual(c_evs[0]["data"]["yield"], 3)
            # Đàn cá đã bị xóa khỏi snapshot cuối
            last_snap = snapshots(rows)[-1]
            self.assertEqual(len(last_snap["fish"]), 0)
            self.assertEqual(last_snap["hold"], ["ca_linh", "ca_linh", "ca_linh"])


if __name__ == "__main__":
    unittest.main()
