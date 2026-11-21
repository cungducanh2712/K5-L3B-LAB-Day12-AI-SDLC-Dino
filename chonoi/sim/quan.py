"""Buổi tối — Mở Quán (`quan`) v1.2.

Contract v1.2:
  - Kho cá thể: stock là danh sách [{id, kind, fresh}].
  - Hao tươi: kho quán giảm 0.25/s (0.25/60 mỗi tick), kẹp đáy 0.
  - Ươn: fresh < 30, phát `spoiled` theo thứ tự id.
  - Giữ chỗ theo cá thể: lấy các cá thể khả dụng tươi nhất (fresh cao nhất, hòa theo id).
  - Giữ lại khi ươn: nếu cá thể đang giữ bị ươn, nhả toàn bộ đơn và thử giữ lại đúng một lần.
    Xử lý các đơn bị ảnh hưởng theo order_tick rồi id bàn.
  - Giá động: base_price = floor(giá niêm yết * trung bình fresh của các cá thể dùng / 100).
    Tip tính floor(base_price * 0.2) trên giá đã chốt.
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
        self.tuning = tuning
        self.menu = tuning["menu"]
        self.allowed_dishes = allowed_dishes
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        # Cấu hình độ tươi
        fness = tuning.get("freshness", {})
        self.initial_fresh = float(fness.get("initial", 100))
        self.decay_per_tick = float(fness.get("quan_decay_per_s", 0.25)) / TICK
        self.spoiled_threshold = float(fness.get("spoiled_below", 30))

        # Kho quán: list các dict {id, kind, fresh, spoiled_emitted}
        raw_stock = inventory if inventory is not None else scenario.get("stock", [])
        self.stock = []
        if isinstance(raw_stock, list):
            for it in raw_stock:
                iid = it.get("id") or self.ids.new("I")
                self.ids.reserve(iid)
                fresh_val = float(it.get("fresh", self.initial_fresh))
                self.stock.append({
                    "id": iid,
                    "kind": it["kind"],
                    "fresh": fresh_val,
                    "spoiled_emitted": fresh_val < self.spoiled_threshold
                })
        elif isinstance(raw_stock, dict):
            for k, count in raw_stock.items():
                for _ in range(count):
                    iid = self.ids.new("I")
                    self.stock.append({
                        "id": iid,
                        "kind": k,
                        "fresh": self.initial_fresh,
                        "spoiled_emitted": False
                    })

        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.random_customers = scenario.get("random_customers", True)
        self.phase_tick = 0
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))

        # Khách
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
            
            # Reserved cá thể (mảng item_id)
            if item["order_status"] == "reserved":
                if "reserved" not in item:
                    # Tự động gán cá thể khả dụng tươi nhất
                    recipe = self.menu[dish_id]["recipe"]
                    reserved_ids = self._try_reserve_items(recipe)
                    item["reserved"] = reserved_ids if reserved_ids is not None else []
                elif isinstance(item["reserved"], dict):
                    # Chuyển đổi từ dict sang list id
                    reserved_ids = self._try_reserve_items(item["reserved"])
                    item["reserved"] = reserved_ids if reserved_ids is not None else []
            else:
                item.setdefault("reserved", [])
            self.customers.append(item)
            ids.reserve(item["id"])

        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    def _get_item_by_id(self, item_id):
        for it in self.stock:
            if it["id"] == item_id:
                return it
        return None

    def _available_stock_items(self):
        """Các cá thể chưa ươn và chưa bị đơn nào giữ chỗ."""
        reserved_set = set()
        for c in self.customers:
            for iid in c.get("reserved", []):
                reserved_set.add(iid)
        return [
            it for it in self.stock
            if it["id"] not in reserved_set and it["fresh"] >= self.spoiled_threshold
        ]

    def _try_reserve_items(self, recipe):
        """Tìm cá thể tươi nhất cho recipe. Trả về list item_id hoặc None nếu thiếu."""
        avail = self._available_stock_items()
        chosen = []
        for kind, req_qty in recipe.items():
            kind_items = [it for it in avail if it["kind"] == kind and it["id"] not in chosen]
            if len(kind_items) < req_qty:
                return None
            # Sắp theo fresh giảm dần, hòa theo id tăng dần
            kind_items.sort(key=lambda it: (-it["fresh"], id_key(it["id"])))
            for i in range(req_qty):
                chosen.append(kind_items[i]["id"])
        return chosen

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
            "stock": [
                {"id": it["id"], "kind": it["kind"], "fresh": round(float(it["fresh"]), 4)}
                for it in sort_by_id(self.stock)
            ],
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in sort_by_id(self.stoves)],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                       for tb in sort_by_id(self.tables)],
            "customers": [
                {
                    "id": c["id"],
                    "table_id": c["table_id"],
                    "dish_id": c["dish_id"],
                    "order_tick": c.get("order_tick", 0),
                    "state": c.get("state", "waiting"),
                    "patience_ticks_left": c.get("patience_ticks_left", 0),
                    "eat_ticks_left": c.get("eat_ticks_left", 0),
                    "order_status": c.get("order_status", "reserved"),
                    "reserved": list(c.get("reserved", [])),
                    "base_price": c.get("base_price", self.menu[c["dish_id"]]["price"]),
                    "tip": c.get("tip", 0),
                }
                for c in sort_by_id(self.customers)
            ],
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Đồng hồ và timer -> hao tươi kho thô, phát hết spoiled theo id
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

        # Hao tươi kho quán
        spoiled_items = []
        for it in self.stock:
            it["fresh"] = max(0.0, it["fresh"] - self.decay_per_tick)
            if not it.get("spoiled_emitted", False) and it["fresh"] < self.spoiled_threshold:
                it["spoiled_emitted"] = True
                spoiled_items.append(it)

        if spoiled_items:
            for it in sort_by_id(spoiled_items):
                events.append(("spoiled", {
                    "item_id": it["id"],
                    "kind": it["kind"],
                    "location": "stock"
                }))

        # Xử lý giữ chỗ bị ươn (Re-reserve logic)
        affected_customers = []
        for c in self.customers:
            if c.get("order_status") == "reserved" and c.get("reserved"):
                # Kiểm tra xem có cá thể nào trong reserved bị ươn (<30) không
                has_spoiled = any(
                    (self._get_item_by_id(iid) and self._get_item_by_id(iid)["fresh"] < self.spoiled_threshold)
                    for iid in c["reserved"]
                )
                if has_spoiled:
                    affected_customers.append(c)

        if affected_customers:
            # Sắp theo order_tick rồi id bàn
            affected_customers.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
            # Nhả toàn bộ reserved của các đơn bị ảnh hưởng trước
            for c in affected_customers:
                c["reserved"] = []

            # Thử giữ lại đúng một lần
            for c in affected_customers:
                recipe = self.menu[c["dish_id"]]["recipe"]
                new_reserved = self._try_reserve_items(recipe)
                if new_reserved:
                    c["reserved"] = new_reserved
                else:
                    c["order_status"] = "unfulfillable"

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
                        res_custs = [c for c in self.customers if c.get("order_status") == "reserved" and c.get("reserved")]
                        if res_custs:
                            res_custs.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
                            target_c = res_custs[0]
                            reserved_ids = list(target_c["reserved"])
                            
                            # Tiêu đúng các id đang giữ
                            consumed_items = [self._get_item_by_id(iid) for iid in reserved_ids]
                            self.stock = [it for it in self.stock if it["id"] not in reserved_ids]

                            # Chốt giá theo tươi: floor(giá niêm yết * avg(fresh) / 100)
                            list_price = self.menu[target_c["dish_id"]]["price"]
                            avg_fresh = sum(it["fresh"] for it in consumed_items) / len(consumed_items) if consumed_items else 100.0
                            chapped_price = int(math.floor(list_price * avg_fresh / 100.0))

                            target_c["reserved"] = []
                            target_c["order_status"] = "assigned"
                            target_c["base_price"] = chapped_price

                            s["state"] = "cooking"
                            cook_ticks = int(round(self.menu[target_c["dish_id"]]["cook_s"] * TICK))
                            s["cook_ticks_left"] = cook_ticks
                            s["ready_ticks"] = 0
                            s["dish"] = {
                                "order_id": target_c["id"],
                                "dish_id": target_c["dish_id"],
                                "base_price": chapped_price,
                            }
                            # Sắp theo kind rồi id
                            sorted_consumed = sorted(consumed_items, key=lambda it: (it["kind"], id_key(it["id"])))
                            events.append(("cook_started", {
                                "stove_id": s["id"],
                                "order_id": target_c["id"],
                                "dish_id": target_c["dish_id"],
                                "items": [
                                    {"id": it["id"], "kind": it["kind"], "fresh": round(float(it["fresh"]), 4)}
                                    for it in sorted_consumed
                                ],
                                "base_price": chapped_price,
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

                    # Món nấu được với kho chưa ươn và khả dụng
                    menu_ids = sorted(self.allowed_dishes if self.allowed_dishes is not None else self.menu.keys())
                    affordable = [
                        m_id for m_id in menu_ids
                        if self._try_reserve_items(self.menu[m_id]["recipe"]) is not None
                    ]
                    if not affordable:
                        events.append(("no_dish", {}))
                    else:
                        chosen_dish = self.rng.get("customer").choice(affordable)
                        cust_id = self.ids.new("C")
                        recipe = self.menu[chosen_dish]["recipe"]
                        reserved_ids = self._try_reserve_items(recipe)
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
                            "reserved": list(reserved_ids),
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
