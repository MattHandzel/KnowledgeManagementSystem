#!/usr/bin/env python3
import time
import statistics
from pathlib import Path
import requests


def time_call(url, method="GET", data=None, files=None):
    t0 = time.perf_counter()
    if method == "GET":
        r = requests.get(url)
    else:
        r = requests.post(url, data=data, files=files)
    dt = (time.perf_counter() - t0) * 1000.0
    return dt, r.status_code


def profile(base="http://localhost:7123"):
    endpoints = [
        ("GET", "/api/config"),
        ("GET", "/api/clipboard"),
        ("POST", "/api/screenshot"),
    ]
    results = {}
    for method, path in endpoints:
        samples = []
        for _ in range(5):
            dt, _ = time_call(base + path, method=method)
            samples.append(dt)
            time.sleep(0.1)
        results[path] = {
            "p50": statistics.median(samples),
            "p95": sorted(samples)[int(len(samples) * 0.95) - 1],
            "avg": sum(samples) / len(samples),
        }

    samples = []
    for _ in range(5):
        dt, _ = time_call(
            base + "/api/capture",
            method="POST",
            data={
                "content": "hello",
                "context": "work",
                "tags": "a,b",
                "sources": "s1",
                "modalities": "text",
            },
        )
        samples.append(dt)
        time.sleep(0.1)
    results["/api/capture"] = {
        "p50": statistics.median(samples),
        "p95": sorted(samples)[int(len(samples) * 0.95) - 1],
        "avg": sum(samples) / len(samples),
    }
    return results


if __name__ == "__main__":
    import json

    print(json.dumps(profile(), indent=2))
