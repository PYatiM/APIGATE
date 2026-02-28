from __future__ import annotations

import statistics
import time
from collections import deque


class Stats:
    def __init__(self, max_samples: int = 500) -> None:
        self.start_time = time.time()
        self.total_requests = 0
        self.total_errors = 0
        self.rate_limited = 0
        self.latencies_ms: deque[float] = deque(maxlen=max_samples)

    def record(self, status_code: int, latency_ms: float, rate_limited: bool) -> None:
        self.total_requests += 1
        if status_code >= 500:
            self.total_errors += 1
        if rate_limited:
            self.rate_limited += 1
        self.latencies_ms.append(latency_ms)

    def snapshot(self) -> dict:
        latency_list = list(self.latencies_ms)
        avg_latency = round(statistics.fmean(latency_list), 2) if latency_list else 0.0
        p95_latency = 0.0
        if latency_list:
            latency_list.sort()
            index = int(0.95 * (len(latency_list) - 1))
            p95_latency = round(latency_list[index], 2)
        return {
            "uptime_seconds": int(time.time() - self.start_time),
            "requests_total": self.total_requests,
            "errors_total": self.total_errors,
            "rate_limited_total": self.rate_limited,
            "latency_avg_ms": avg_latency,
            "latency_p95_ms": p95_latency,
        }


stats = Stats()
