"""Buổi sáng — Lặn & Hái (`gather`) v1.1.

Contract v1.1:
  - Bơi, oxy, ngạt, LIFO giỏ.
  - Hái bông điên điển, bông súng, kèo nèo (N1-N6).
  - Bắt cá linh (3), cá lóc (1), cá kèo (2).
  - Đàn cá bơi 1.5 m/s, đổi hướng mỗi 120 tick, phản xạ mép.
  - Sinh cá theo lịch mỗi 360 tick (trần 12 đàn).
  - Cá Sấu Năm Chèo (monsters M1, M2): tuần tra, đuổi theo, cắn mất 1 Máu và nửa giỏ LIFO, recoil 60 bước.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")

SPAWN_X = [15, 30, 45, 60, 75, 90]
SPAWN_DEPTHS = {
    "ca_linh": [5, 10],
    "ca_loc": [10, 16],
    "ca_keo": [24, 27],
}
SWIM_DEPTHS = {
    "ca_linh": [3, 12],
    "ca_loc": [8, 20],
    "ca_keo": [22, 28],
}
FISH_WEIGHTS = {
    "ca_linh": 0.4,
    "ca_loc": 0.3,
    "ca_keo": 0.3,
}


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day=1):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = scenario.get("day", day)
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0

        # Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        # Đàn cá ban đầu
        self.random_fish = scenario.get("random_fish", True)
        if "fish" in scenario:
            self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                          "heading_deg": f.get("heading_deg", 0.0), "age_ticks": f.get("age_ticks", 0)}
                         for f in scenario["fish"]]
        elif self.random_fish:
            if isinstance(t.get("fish_initial"), int):
                self.fish = self._generate_initial_fish(t["fish_initial"])
            elif isinstance(t.get("fish_initial"), list):
                self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                              "heading_deg": f.get("heading_deg", 0.0), "age_ticks": f.get("age_ticks", 0)}
                             for f in t["fish_initial"]]
            else:
                self.fish = []
        else:
            self.fish = []

        # Quái vật (Cá Sấu Năm Chèo)
        if "monsters" in scenario:
            self.monsters = [self._init_monster(m) for m in scenario["monsters"]]
        else:
            spawns = t.get("monsters", {}).get("spawns", [])
            active_spawns = [s for s in spawns if s.get("from_day", 1) <= self.day]
            self.monsters = [self._init_monster(s) for s in active_spawns]

        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _init_monster(self, data):
        wps = data.get("waypoints", [[data["pos"][0], data["pos"][1]], [data["pos"][0] + 4, data["pos"][1]]])
        return {
            "id": data["id"],
            "kind": data.get("kind", "ca_sau"),
            "pos": [float(c) for c in data["pos"]],
            "waypoints": [[float(c) for c in w] for w in wps],
            "target_idx": data.get("target_idx", 1),
            "state": data.get("state", "patrol"),
            "recoil_ticks_left": data.get("state_ticks_left", 0),
            "recoil_dir": data.get("recoil_dir"),
        }

    def _generate_initial_fish(self, count):
        # 36 cặp loài-vị trí
        candidates = []
        for kind, depths in SPAWN_DEPTHS.items():
            for x in SPAWN_X:
                for d in depths:
                    candidates.append((kind, [float(x), float(d)]))

        f_list = []
        occupied_positions = set()
        for _ in range(min(count, len(candidates))):
            avail_by_kind = {}
            for k in FISH_WEIGHTS:
                pts = [pt for kind, pt in candidates if kind == k and tuple(pt) not in occupied_positions]
                if pts:
                    avail_by_kind[k] = pts
            if not avail_by_kind:
                break
            kinds = list(avail_by_kind.keys())
            weights = [FISH_WEIGHTS[k] for k in kinds]
            chosen_kind = self.rng.get("fish_spawn").choices(kinds, weights=weights)[0]
            chosen_pt = self.rng.get("fish_spawn").choice(avail_by_kind[chosen_kind])
            occupied_positions.add(tuple(chosen_pt))
            heading = self.rng.get("fish").uniform(0, 360)
            f_list.append({
                "id": self.ids.new("F"),
                "kind": chosen_kind,
                "pos": list(chosen_pt),
                "heading_deg": heading,
                "age_ticks": 0,
            })
        return f_list

    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "pos": m["pos"], "kind": m["kind"], "state": m["state"]}
                         for m in sort_by_id(self.monsters)],
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1

        # 1. Đồng hồ, cooldown, giảm bất tử và hồi nút
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        # 2. Bơi, oxy, ngạt
        was_at_surface = self._at_surface()
        self._move(inp)
        now_at_surface = self._at_surface()
        if was_at_surface and not now_at_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_at_surface and now_at_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        if now_at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
        else:
            old_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if old_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                if self.zero_oxy_ticks >= self.t["choke_interval_ticks"]:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = list(reversed(self.hold))
                        self.hold = []
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 3. Cập nhật quái theo id rồi xét tối đa một hit
        for m in sort_by_id(self.monsters):
            self._step_monster(m)

        # Hit detection
        if self.pos[1] >= 10.0 and self.invuln_ticks == 0:
            hit_candidates = []
            for m in self.monsters:
                if m["state"] != "recoil" and math.dist(self.pos, m["pos"]) <= 1.5:
                    hit_candidates.append((math.dist(self.pos, m["pos"]), id_key(m["id"]), m))
            if hit_candidates:
                hit_candidates.sort(key=lambda x: (x[0], x[1]))
                target_m = hit_candidates[0][2]
                self.hp -= 1
                drop_count = len(self.hold) // 2
                lost = []
                for _ in range(drop_count):
                    lost.append(self.hold.pop())  # LIFO
                self.invuln_ticks = 90
                target_m["state"] = "recoil"
                target_m["recoil_ticks_left"] = 60
                dx = target_m["pos"][0] - self.pos[0]
                dd = target_m["pos"][1] - self.pos[1]
                dlen = math.hypot(dx, dd)
                target_m["recoil_dir"] = [dx / dlen, dd / dlen] if dlen > 0 else [1.0, 0.0]
                events.append(("monster_hit", {
                    "monster_id": target_m["id"],
                    "hp": self.hp,
                    "lost": lost,
                    "pos": list(self.pos),
                }))
                if self.hp <= 0:
                    faint_lost = list(reversed(self.hold))
                    self.hold = []
                    events.append(("faint", {"cause": "monster", "lost": faint_lost, "hp": 0}))
                    self._finish("fainted", events)
                    return events

        # 4. Tương tác (bến trước, rồi hái)
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_at_surface:
                candidates = [
                    n for n in self.nodes
                    if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= self.t["interact_radius"]
                ]
                if candidates:
                    candidates.sort(key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
                    target = candidates[0]
                    yield_amount = self.t.get("node_yield", 1)
                    free_space = self.t["hold_capacity"] - len(self.hold)
                    if free_space >= yield_amount:
                        self.hold.extend([target["kind"]] * yield_amount)
                        target["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {
                            "node_id": target["id"],
                            "kind": target["kind"],
                            "amount": yield_amount,
                        }))
                    else:
                        events.append(("hold_full", {
                            "action": "gather",
                            "node_id": target["id"],
                            "required": yield_amount,
                            "free": free_space,
                        }))

        # 5. Bắt cá theo vị trí cá trước khi bơi
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and not now_at_surface:
                candidates = [
                    f for f in self.fish
                    if math.dist(self.pos, f["pos"]) <= self.t["catch_radius"]
                ]
                if candidates:
                    candidates.sort(key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
                    target = candidates[0]
                    yield_amount = self.t["fish_yield"][target["kind"]]
                    free_space = self.t["hold_capacity"] - len(self.hold)
                    if free_space >= yield_amount:
                        self.hold.extend([target["kind"]] * yield_amount)
                        self.fish.remove(target)
                        events.append(("fish_caught", {
                            "fish_id": target["id"],
                            "kind": target["kind"],
                            "yield": yield_amount,
                        }))
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                    else:
                        events.append(("hold_full", {
                            "action": "catch",
                            "fish_id": target["id"],
                            "required": yield_amount,
                            "free": free_space,
                        }))

        # 6. Hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 7. Nếu còn giờ: đàn cá bơi & sinh thêm theo lịch
        if self.random_fish:
            for f in sort_by_id(self.fish):
                f["age_ticks"] = f.get("age_ticks", 0) + 1
                if f["age_ticks"] % 120 == 0:
                    f["heading_deg"] = self.rng.get("fish").uniform(0, 360)
                self._move_fish(f)

            # Sinh cá theo lịch mỗi 360 tick
            if self.phase_tick % 360 == 0 and len(self.fish) < 12:
                self._spawn_fish_if_possible(events)

        return events

    def _step_monster(self, m):
        dist_to_player = math.dist(self.pos, m["pos"])
        player_in_zone = self.pos[1] >= 10.0

        if m["state"] == "patrol":
            if player_in_zone and dist_to_player <= 10.0:
                m["state"] = "chase"
                self._move_monster_toward(m, self.pos, 3.0)
            else:
                target = m["waypoints"][m["target_idx"]]
                reached = self._move_monster_toward(m, target, 1.0)
                if reached:
                    m["target_idx"] = 1 - m["target_idx"]

        elif m["state"] == "chase":
            if dist_to_player > 16.0 or not player_in_zone:
                m["state"] = "patrol"
                target = m["waypoints"][m["target_idx"]]
                reached = self._move_monster_toward(m, target, 1.0)
                if reached:
                    m["target_idx"] = 1 - m["target_idx"]
            else:
                self._move_monster_toward(m, self.pos, 3.0)

        elif m["state"] == "recoil":
            r_speed = 2.0  # 2/60 m mỗi bước
            if m["recoil_dir"]:
                m["pos"][0] += m["recoil_dir"][0] * (r_speed / TICK)
                m["pos"][1] += m["recoil_dir"][1] * (r_speed / TICK)
            m["recoil_ticks_left"] -= 1
            if m["recoil_ticks_left"] <= 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None

        # Chặn Cá Sấu theo biên map [0, 100] và dải độ sâu [10, 30]
        m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
        m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))

    def _move_monster_toward(self, m, target, speed):
        step_dist = speed / TICK
        d = math.dist(m["pos"], target)
        if d <= step_dist:
            m["pos"] = [float(target[0]), float(target[1])]
            return True
        dx = (target[0] - m["pos"][0]) / d
        dd = (target[1] - m["pos"][1]) / d
        m["pos"][0] += dx * step_dist
        m["pos"][1] += dd * step_dist
        return False

    def _move_fish(self, f):
        dist = 1.5 / TICK  # 1.5 m/s
        rad = math.radians(f["heading_deg"])
        dx = dist * math.cos(rad)
        dd = dist * math.sin(rad)

        x, d = f["pos"]
        x_min, x_max = 4.0, 96.0
        d_min, d_max = SWIM_DEPTHS.get(f["kind"], [3.0, 28.0])

        x_new = x + dx
        if x_new < x_min:
            overshoot = x_min - x_new
            x = x_min + overshoot
            dx = -dx
        elif x_new > x_max:
            overshoot = x_new - x_max
            x = x_max - overshoot
            dx = -dx
        else:
            x = x_new

        d_new = d + dd
        if d_new < d_min:
            overshoot = d_min - d_new
            d = d_min + overshoot
            dd = -dd
        elif d_new > d_max:
            overshoot = d_new - d_max
            d = d_max - overshoot
            dd = -dd
        else:
            d = d_new

        f["pos"] = [x, d]
        f["heading_deg"] = math.degrees(math.atan2(dd, dx)) % 360

    def _spawn_fish_if_possible(self, events):
        candidates = []
        for kind, depths in SPAWN_DEPTHS.items():
            for x in SPAWN_X:
                for d in depths:
                    pt = [float(x), float(d)]
                    # Cách mọi đàn đang sống > 1 m
                    if all(math.dist(pt, f["pos"]) > 1.0 for f in self.fish):
                        candidates.append((kind, pt))

        if not candidates:
            return

        avail_by_kind = {}
        for k in FISH_WEIGHTS:
            pts = [pt for kind, pt in candidates if kind == k]
            if pts:
                avail_by_kind[k] = pts

        if not avail_by_kind:
            return

        kinds = list(avail_by_kind.keys())
        weights = [FISH_WEIGHTS[k] for k in kinds]
        chosen_kind = self.rng.get("fish_spawn").choices(kinds, weights=weights)[0]
        chosen_pt = self.rng.get("fish_spawn").choice(avail_by_kind[chosen_kind])
        heading = self.rng.get("fish").uniform(0, 360)
        new_fish = {
            "id": self.ids.new("F"),
            "kind": chosen_kind,
            "pos": list(chosen_pt),
            "heading_deg": heading,
            "age_ticks": 0,
        }
        self.fish.append(new_fish)
        events.append(("fish_spawned", {
            "id": new_fish["id"],
            "kind": new_fish["kind"],
            "pos": new_fish["pos"],
        }))

    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
