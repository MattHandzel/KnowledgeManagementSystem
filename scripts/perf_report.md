# Performance Comparison Report

This report compares baseline Python/FastAPI vs. Tauri/Rust implementations for key endpoints.

> Note: Python baseline metrics are not available yet due to environment constraints (PortAudio missing).

### Endpoint Latency

| Endpoint | Impl | p50 (ms) | p95 (ms) | avg (ms) |
|---|---:|---:|---:|---:|
| /api/capture | Rust | 10.14 | 11.34 | 13.08 |
| /api/clipboard | Rust | 2.37 | 2.43 | 2.38 |
| /api/config | Rust | 1.79 | 1.81 | 1.79 |
| /api/screenshot | Rust | 2.36 | 2.41 | 2.44 |
