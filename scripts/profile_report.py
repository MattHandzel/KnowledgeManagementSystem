#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def load_json(path):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    with p.open("r") as f:
        return json.load(f)

def render_table(title, rust, py):
    lines = []
    lines.append(f"### {title}")
    lines.append("")
    lines.append("| Endpoint | Impl | p50 (ms) | p95 (ms) | avg (ms) |")
    lines.append("|---|---:|---:|---:|---:|")
    endpoints = set()
    if rust:
        endpoints.update(rust.keys())
    if py:
        endpoints.update(py.keys())
    for ep in sorted(endpoints):
        if rust and ep in rust:
            r = rust[ep]
            lines.append(f"| {ep} | Rust | {r['p50']:.2f} | {r['p95']:.2f} | {r['avg']:.2f} |")
        if py and ep in py:
            p = py[ep]
            lines.append(f"| {ep} | Python | {p['p50']:.2f} | {p['p95']:.2f} | {p['avg']:.2f} |")
    lines.append("")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rust", required=False, help="Path to Rust JSON results")
    ap.add_argument("--python", required=False, help="Path to Python JSON results")
    ap.add_argument("--out", required=False, default="scripts/perf_report.md")
    args = ap.parse_args()

    rust = load_json(args.rust)
    py = load_json(args.python)

    lines = []
    lines.append("# Performance Comparison Report")
    lines.append("")
    lines.append("This report compares baseline Python/FastAPI vs. Tauri/Rust implementations for key endpoints.")
    lines.append("")
    if rust is None and py is None:
        lines.append("_No data available._")
    else:
        if py is None:
            lines.append("> Note: Python baseline metrics are not available yet due to environment constraints (PortAudio missing).")
            lines.append("")
        lines.append(render_table("Endpoint Latency", rust, py))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines))

if __name__ == "__main__":
    main()
