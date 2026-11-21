"""Soak test headless (Phase 4 — Test Contract v1.3).

Lệnh:
    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Đo:
    10 ngày trong một tiến trình headless xuyên suốt.
    Kế hoạch D1-D5 lặp ở Ngày 6-10.
    Tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt.
    Xuất soak.json: days, days_completed, crashes, results, duration_s.
"""

import argparse
import json
import sys
import time
import traceback

from .contract import load_contract
from .inputs import LiveInputs
from .runner import Session


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def main(argv=None) -> int:
    t_start = time.perf_counter()
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--days", type=int, default=10)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    contract = load_contract()
    tuning = contract["tuning"]

    # Mở rộng day_plan nếu cần chạy > 5 ngày (lặp D1-D5)
    base_plans = list(tuning.get("day_plan", []))
    expanded_plans = []
    for d in range(1, a.days + 1):
        idx = (d - 1) % len(base_plans)
        plan_copy = dict(base_plans[idx])
        plan_copy["day"] = d
        expanded_plans.append(plan_copy)
    tuning["day_plan"] = expanded_plans

    results = []
    crashes = 0
    days_completed = 0

    try:
        sess = Session("day", tuning, {}, a.seed, days=a.days)
        live_in = LiveInputs()

        # Bot đơn giản: mô phỏng các ngày
        # Mỗi phase chạy tới khi xong
        while not sess.sim.done:
            # Nếu đang ở shop, tự động đóng shop để qua ngày kế tiếp
            if sess.sim.phase == "shop":
                live_in.set(shop_done=True)
            else:
                live_in.set(shop_done=False)

            inp = live_in.advance()
            sess.step(inp)

            # Bắt sự kiện shop_end để ghi nhận kết quả ngày
            if sess.sim.phase == "gather" and sess.sim.days_completed > days_completed:
                days_completed = sess.sim.days_completed
                mult = tuning["score"]["reputation_multiplier"]
                results.append({
                    "day": days_completed,
                    "earned": sess.sim.earned,
                    "reputation": round(sess.sim.reputation, 2),
                    "score": sess.sim.earned + int(mult * math.floor(sess.sim.reputation)),
                })

        days_completed = sess.sim.days_completed
        if len(results) < days_completed:
            mult = tuning["score"]["reputation_multiplier"]
            results.append({
                "day": days_completed,
                "earned": sess.sim.earned,
                "reputation": round(sess.sim.reputation, 2),
                "score": sess.sim.earned + int(mult * math.floor(sess.sim.reputation)),
            })

    except Exception:
        crashes += 1
        traceback.print_exc()

    duration_s = round(time.perf_counter() - t_start, 4)

    soak_data = {
        "days": a.days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }

    try:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(soak_data, f, indent=2)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi file soak: {e}\n")
        return 1

    print(f"Soak hoàn thành: days_completed={days_completed}/{a.days}, crashes={crashes}, duration_s={duration_s}")
    return 0


if __name__ == "__main__":
    import math
    sys.exit(main())
