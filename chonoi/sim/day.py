"""Vòng ngày (mode `day`) — Contract v1.2.

Flow:
  DayIntro -> gather -> EveningIntro -> quan -> DayResult -> Shop -> DayIntro (cho tới khi hết số ngày).
"""

import copy
import math

from ..ids import sort_by_id
from .gather import GatherSim
from .quan import QuanSim

TICK = 60.0


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, total_days=1):
        self.tuning = tuning
        self.scenario = scenario
        self.rng = streams
        self.ids = ids
        self.total_days = total_days
        self.current_day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0
        self.paused = False

        day_sc = scenario.get("day", {})
        self.money = day_sc.get("money", 0)
        self.earned = day_sc.get("earned", 0)
        self.reputation = day_sc.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = dict(day_sc.get("upgrades", {}))
        self.active_upgrades = dict(self.upgrades)

        # Kế hoạch ngày
        self.day_plan = list(tuning.get("day_plan", []))
        if "day_plan" in day_sc:
            self.day_plan = list(day_sc["day_plan"])

        self.gather_sim = None
        self.quan_sim = None
        self.shop_time_left = 0
        self.stock_surplus = []

        self.done = False
        self.reason = None

        # Khởi động Day 1
        self._init_current_day()

    @property
    def current_plan(self):
        for p in self.day_plan:
            if p["day"] == self.current_day:
                return p
        return {"day": self.current_day, "dishes": {}, "ingredients": {}}

    def _init_current_day(self):
        self.phase = "gather"
        self.phase_tick = 0
        t_gather = copy.deepcopy(self.tuning)
        # Áp dụng active_upgrades
        if self.active_upgrades.get("oxygen", 0) == 1:
            t_gather["gather"]["oxygen_max_s"] = 45
        elif self.active_upgrades.get("oxygen", 0) == 2:
            t_gather["gather"]["oxygen_max_s"] = 60

        if self.active_upgrades.get("hp", 0) == 1:
            t_gather["gather"]["hp_max"] = 4
        elif self.active_upgrades.get("hp", 0) == 2:
            t_gather["gather"]["hp_max"] = 5

        sc_gather = dict(self.scenario.get("gather", {}))
        sc_gather["day"] = self.current_day
        self.gather_sim = GatherSim(t_gather, sc_gather, self.rng, self.ids, day=self.current_day)

    def initial_events(self):
        plan = self.current_plan
        return [
            ("day_start", {}),
            ("day_plan", {"dishes": plan["dishes"], "ingredients": plan["ingredients"]}),
            ("phase_start", {}),
        ]

    def snapshot(self) -> dict:
        snap = {
            "day": self.current_day,
            "day_plan": self.current_plan,
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
            "phase": self.phase,
            "phase_tick": self.phase_tick,
        }
        if self.phase == "gather" and self.gather_sim:
            s = self.gather_sim.snapshot()
            snap.update(s)
            snap["time_left_ticks"] = self.gather_sim.time_left_ticks
        elif self.phase == "quan" and self.quan_sim:
            s = self.quan_sim.snapshot()
            snap.update(s)
            snap["time_left_ticks"] = self.quan_sim.time_left_ticks
        elif self.phase == "shop":
            snap["stock"] = [
                {"id": it["id"], "kind": it["kind"], "fresh": round(float(it["fresh"]), 4)}
                for it in sort_by_id(self.stock_surplus)
            ]
            snap["time_left_ticks"] = self.shop_time_left
        return snap

    def step(self, inp):
        events = []
        self.phase_tick += 1

        if self.phase == "gather":
            sub_evs = self.gather_sim.step(inp)
            events.extend(sub_evs)
            if self.gather_sim.done:
                catch = self.gather_sim.inventory_items()
                self.phase = "quan"
                self.phase_tick = 0
                events.append(("phase_start", {}))
                sc_quan = dict(self.scenario.get("quan", {}))
                plan = self.current_plan
                # Kho quán nhận trọn số lượng và độ tươi từ giỏ
                self.quan_sim = QuanSim(self.tuning, sc_quan, self.rng, self.ids,
                                        inventory=catch, allowed_dishes=plan["dishes"])
                self.quan_sim.money = self.money
                self.quan_sim.earned = self.earned
                self.quan_sim.reputation = self.reputation

        elif self.phase == "quan":
            sub_evs = self.quan_sim.step(inp)
            events.extend(sub_evs)
            if self.quan_sim.done:
                self.money = self.quan_sim.money
                self.earned = self.quan_sim.earned
                self.reputation = self.quan_sim.reputation
                self.stock_surplus = list(self.quan_sim.stock)
                self.phase = "shop"
                self.phase_tick = 0
                self.shop_time_left = self.tuning["shop"]["max_ticks"]
                events.append(("phase_start", {}))

        elif self.phase == "shop":
            self.shop_time_left = max(0, self.shop_time_left - 1)
            # Xử lý buy
            if inp.buy:
                u_name = inp.buy
                if u_name not in ("oxygen", "hp"):
                    events.append(("buy_failed", {"action": u_name, "reason": "unknown"}))
                else:
                    cur_level = self.upgrades.get(u_name, 0)
                    tiers = self.tuning["shop"]["upgrades"][u_name]
                    if cur_level >= len(tiers):
                        events.append(("buy_failed", {"action": u_name, "reason": "max_level"}))
                    else:
                        tier = tiers[cur_level]
                        price = tier["price"]
                        if self.money < price:
                            events.append(("buy_failed", {"action": u_name, "reason": "funds"}))
                        else:
                            self.money -= price
                            new_lvl = cur_level + 1
                            self.upgrades[u_name] = new_lvl
                            events.append(("bought", {
                                "upgrade": u_name,
                                "level": new_lvl,
                                "price": price,
                                "money": self.money,
                            }))

            # Đóng shop
            if inp.pressed("shop_done") or self.shop_time_left <= 0:
                reason = "done" if inp.pressed("shop_done") else "time"
                events.append(("shop_end", {"reason": reason}))
                self.days_completed += 1
                if self.days_completed >= self.total_days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.current_day += 1
                    self.active_upgrades = dict(self.upgrades)
                    self._init_current_day()
                    events.extend(self.initial_events())

        return events
