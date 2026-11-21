"""Buổi tối — Mở Quán.

PRD-0 mục F, Quán:
  Lát 3: khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
         bỏ đi (customer_left), no_dish, vòng đời khách.
  Lát 4: interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
         ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.allowed_dishes = allowed_dishes
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        
        self.customers = []
        for c in scenario.get("customers", []):
            item = dict(c)
            dish_id = item["dish_id"]
            price = self.menu[dish_id]["price"]
            item.setdefault("state", "waiting")
            item.setdefault("order_tick", 0)
            item.setdefault("order_status", "reserved")
            item.setdefault("patience_ticks_left", int(round(t["patience_s"] * TICK)))
            item.setdefault("eat_ticks_left", int(round(t["eat_s"] * TICK)) if item.get("state") == "eating" else 0)
            item.setdefault("base_price", price)
            item.setdefault("tip", 0)
            if item["order_status"] == "reserved" and "reserved" not in item:
                item["reserved"] = dict(self.menu[dish_id]["recipe"])
            else:
                item.setdefault("reserved", {})
            self.customers.append(item)
            ids.reserve(item["id"])

        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Bếp và khách cập nhật timer đầu bước
        for s in sort_by_id(self.stoves):
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] -= 1
                if s["cook_ticks_left"] == 0:
                    s["state"] = "ready"
                    s["ready_ticks"] = 0
                    events.append(("dish_ready", {
                        "stove_id": s["id"],
                        "order_id": s["dish"]["order_id"],
                        "dish_id": s["dish"]["dish_id"],
                    }))

        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] -= 1
            elif c["state"] == "waiting":
                c["patience_ticks_left"] -= 1

        # 2. Di chuyển
        self._move(inp)

        # 3. Tương tác (tối đa 1 interact, khoảng cách, bếp trước bàn, id)
        if inp.pressed("interact"):
            candidates = []
            for s in self.stoves:
                d = math.dist(self.pos, s["pos"])
                if d <= self.t["interact_radius"]:
                    candidates.append((d, 0, id_key(s["id"]), "stove", s))
            for tb in self.tables:
                d = math.dist(self.pos, tb["pos"])
                if d <= self.t["interact_radius"]:
                    candidates.append((d, 1, id_key(tb["id"]), "table", tb))

            if candidates:
                candidates.sort(key=lambda x: (x[0], x[1], x[2]))
                target_type = candidates[0][3]
                target = candidates[0][4]

                if target_type == "stove":
                    s = target
                    if s["state"] == "idle":
                        # Đơn reserved cũ nhất theo order_tick rồi id bàn
                        res_custs = [c for c in self.customers if c["order_status"] == "reserved"]
                        if res_custs:
                            res_custs.sort(key=lambda c: (c["order_tick"], id_key(c["table_id"])))
                            target_c = res_custs[0]
                            recipe = self.menu[target_c["dish_id"]]["recipe"]
                            for k, q in recipe.items():
                                self.stock[k] = self.stock.get(k, 0) - q
                            target_c["reserved"] = {}
                            target_c["order_status"] = "assigned"
                            s["state"] = "cooking"
                            cook_ticks = int(round(self.menu[target_c["dish_id"]]["cook_s"] * TICK))
                            s["cook_ticks_left"] = cook_ticks
                            s["ready_ticks"] = 0
                            s["dish"] = {
                                "order_id": target_c["id"],
                                "dish_id": target_c["dish_id"],
                                "base_price": target_c["base_price"],
                            }
                            items_list = []
                            for k in sorted(recipe.keys()):
                                items_list.extend([k] * recipe[k])
                            events.append(("cook_started", {
                                "stove_id": s["id"],
                                "order_id": target_c["id"],
                                "dish_id": target_c["dish_id"],
                                "items": items_list,
                                "base_price": target_c["base_price"],
                            }))
                    elif s["state"] == "ready":
                        if self.hand is None:
                            self.hand = s["dish"]
                            d_order_id = s["dish"]["order_id"]
                            d_dish_id = s["dish"]["dish_id"]
                            s["state"] = "idle"
                            s["dish"] = None
                            s["ready_ticks"] = 0
                            events.append(("dish_picked", {
                                "stove_id": s["id"],
                                "order_id": d_order_id,
                                "dish_id": d_dish_id,
                            }))

                elif target_type == "table":
                    tb = target
                    if self.hand is not None:
                        cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
                        if cust and cust["id"] == self.hand["order_id"] and cust["state"] == "waiting":
                            cust["state"] = "eating"
                            cust["order_status"] = "served"
                            cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                            patience_max_ticks = self.t["patience_s"] * TICK
                            ratio = cust["patience_ticks_left"] / patience_max_ticks
                            if ratio >= self.t["tip_min_patience_ratio"]:
                                tip = int(math.floor(cust["base_price"] * self.t["tip_rate"]))
                            else:
                                tip = 0
                            cust["tip"] = tip
                            events.append(("served", {
                                "order_id": cust["id"],
                                "table_id": tb["id"],
                                "dish_id": cust["dish_id"],
                                "patience_ticks_left": cust["patience_ticks_left"],
                                "base_price": cust["base_price"],
                                "tip": tip,
                            }))
                            self.hand = None

        # 4. Khách rời bàn / thanh toán theo id bàn
        if self.time_left_ticks > 0:
            for c in sort_by_id(list(self.customers), key=lambda x: x["table_id"]):
                if c["state"] == "eating" and c["eat_ticks_left"] <= 0:
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if c["tip"] > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": "finished_eating",
                    }))
                    self.customers.remove(c)
                elif c["state"] == "waiting" and c["patience_ticks_left"] <= 0:
                    self.reputation = max(self.t["reputation_min"], self.reputation + self.t["left_reputation_delta"])
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "patience",
                        "reputation": round(self.reputation, 2),
                    }))
                    # Nhả phần giữ, hủy món của đơn đang nấu/ready/trên tay
                    for s in self.stoves:
                        if s.get("dish") and s["dish"].get("order_id") == c["id"]:
                            s["dish"] = None
                            s["state"] = "idle"
                            s["cook_ticks_left"] = 0
                            s["ready_ticks"] = 0
                    if self.hand and self.hand.get("order_id") == c["id"]:
                        self.hand = None
                    self.customers.remove(c)
        else:
            # Hết ca (closing)
            for c in sort_by_id(list(self.customers), key=lambda x: x["table_id"]):
                if c["state"] == "eating":
                    amount = c["base_price"] + c["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if c["tip"] > 0:
                        self.reputation = min(self.t["reputation_max"], self.reputation + self.t["tip_reputation"])
                    events.append(("paid", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "base_price": c["base_price"],
                        "tip": c["tip"],
                        "amount": amount,
                        "reason": "closing",
                    }))
                elif c["state"] == "waiting":
                    events.append(("customer_left", {
                        "order_id": c["id"],
                        "table_id": c["table_id"],
                        "reason": "closing",
                        "reputation": round(self.reputation, 2),
                    }))
            for s in self.stoves:
                s["dish"] = None
                s["state"] = "idle"
                s["cook_ticks_left"] = 0
                s["ready_ticks"] = 0
            self.hand = None
            self.customers = []
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))
            return events

        # 5. Khách mới theo lịch (first_customer_tick, customer_interval_s)
        if self.time_left_ticks > 0 and self.random_customers:
            interval_ticks = int(round(self.t["customer_interval_s"] * TICK))
            if (self.phase_tick >= self.t["first_customer_tick"] and
                    (self.phase_tick - self.t["first_customer_tick"]) % interval_ticks == 0):
                occupied_tables = {c["table_id"] for c in self.customers}
                empty_tables = [tb for tb in self.tables if tb["id"] not in occupied_tables]
                if empty_tables:
                    empty_tables.sort(key=lambda tb: id_key(tb["id"]))
                    target_table = empty_tables[0]
                    # Tính tồn kho khả dụng (tồn vật lý trừ phần giữ)
                    avail = dict(self.stock)
                    for c in self.customers:
                        for k, q in c.get("reserved", {}).items():
                            avail[k] = avail.get(k, 0) - q
                    menu_ids = sorted(self.allowed_dishes if self.allowed_dishes is not None else self.menu.keys())
                    affordable = [
                        m_id for m_id in menu_ids
                        if all(avail.get(k, 0) >= q for k, q in self.menu[m_id]["recipe"].items())
                    ]
                    if not affordable:
                        events.append(("no_dish", {}))
                    else:
                        chosen_dish = self.rng.get("customer").choice(affordable)
                        cust_id = self.ids.new("C")
                        recipe = self.menu[chosen_dish]["recipe"]
                        price = self.menu[chosen_dish]["price"]
                        patience_ticks = int(round(self.t["patience_s"] * TICK))
                        new_cust = {
                            "id": cust_id,
                            "table_id": target_table["id"],
                            "dish_id": chosen_dish,
                            "order_tick": self.phase_tick,
                            "state": "waiting",
                            "patience_ticks_left": patience_ticks,
                            "eat_ticks_left": 0,
                            "order_status": "reserved",
                            "reserved": dict(recipe),
                            "base_price": price,
                            "tip": 0,
                        }
                        self.customers.append(new_cust)
                        events.append(("customer_arrived", {
                            "order_id": cust_id,
                            "table_id": target_table["id"],
                            "dish_id": chosen_dish,
                        }))

        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
