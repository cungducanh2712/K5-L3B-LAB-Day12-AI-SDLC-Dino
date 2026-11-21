"""Vòng tick (Contract B, mô hình tick).

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    elif mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    elif mode == "day":
        return DaySim(tuning, scenario, streams, ids, total_days=days)
    raise ValueError(f"mode không hợp lệ: {mode}")


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": getattr(sim, "time_left_ticks", 0),
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        if self.paused or getattr(self.sim, "paused", False):
            state = "paused"
        elif self.sim.done:
            state = "finished"
        else:
            state = "playing"

        phase_tick = getattr(self.sim, "phase_tick", self.tick)
        s = _common(self.sim, self.tick, self.tick, phase_tick, self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        events = []
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": "paused", "data": {}}
                if self.mode == "day":
                    row["day"] = self.sim.current_day
                return [row]
            else:
                self.paused = False
                row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": "resumed", "data": {}}
                if self.mode == "day":
                    row["day"] = self.sim.current_day
                events.append(row)

        if self.paused:
            return []

        sim_events = self.sim.step(inp)
        for name, data in sim_events:
            row = {"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
            if self.mode == "day":
                row["day"] = self.sim.current_day
            events.append(row)
        return events

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.tick, self.tick, self.tuning, "")["score"]
        row = {
            "type": "end", "ticks": self.tick, "sim_tick": self.tick, "mode": sim.mode,
            "state": "finished" if sim.done else "playing",
            "reason": sim.reason if sim.done else "tick_limit",
            "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score,
        }
        if self.mode == "day":
            row["days_completed"] = getattr(sim, "days_completed", 0)
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        # Nếu là mode day: ghi các event ban đầu (day_start, day_plan, phase_start)
        if mode == "day" and hasattr(sess.sim, "initial_events"):
            for name, data in sess.sim.initial_events():
                w.write({
                    "type": "event", "tick": 0, "phase": sess.sim.phase,
                    "day": sess.sim.current_day, "name": name, "data": data,
                })

        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
