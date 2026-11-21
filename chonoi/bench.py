"""Benchmark cảnh đo Buổi sáng (Phase 4 — Test Contract v1.3).

Lệnh:
    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Đo:
    Làm nóng 3 s, đo 30 s cảnh Buổi sáng lõi (cá bơi, cá sấu, độ tươi).
    Xuất JSON: avg_fps, p1_low_fps, frames, measured_s, load_ms.
"""

import argparse
import json
import math
import sys
import time

from .contract import load_contract
from .inputs import LiveInputs
from .runner import Session


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def main(argv=None) -> int:
    start_init = time.perf_counter()
    p = _Parser(prog="chonoi.bench")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--duration", type=int, default=30)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    contract = load_contract()
    tuning = contract["tuning"]
    sess = Session("gather", tuning, {}, a.seed)
    live_in = LiveInputs()
    inp = live_in.advance()

    # Đo load_ms: từ lúc bắt đầu chạy đến tick đầu tiên
    load_ms = round((time.perf_counter() - start_init) * 1000.0, 2)

    # 1. Warm-up (Làm nóng 3 giây = 180 ticks)
    for _ in range(180):
        sess.step(inp)

    # 2. Benchmark (Đo theo duration giây)
    target_frames = a.duration * 60
    frame_durations = []
    t_measure_start = time.perf_counter()

    for _ in range(target_frames):
        t0 = time.perf_counter()
        sess.step(inp)
        t1 = time.perf_counter()
        frame_durations.append(t1 - t0)

    t_measure_end = time.perf_counter()
    measured_s = round(t_measure_end - t_measure_start, 4)
    total_frames = len(frame_durations)
    avg_fps = round(total_frames / measured_s, 2)

    # 1% low fps
    p1_count = max(1, math.ceil(0.01 * total_frames))
    slowest_frames = sorted(frame_durations, reverse=True)[:p1_count]
    avg_slowest_duration = sum(slowest_frames) / len(slowest_frames)
    p1_low_fps = round(1.0 / avg_slowest_duration, 2) if avg_slowest_duration > 0 else avg_fps

    # Kết quả
    bench_data = {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frames": total_frames,
        "measured_s": measured_s,
        "load_ms": load_ms,
    }

    try:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(bench_data, f, indent=2)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi file bench: {e}\n")
        return 1

    print(f"Benchmark xong: avg_fps={avg_fps}, p1_low_fps={p1_low_fps}, load_ms={load_ms}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
