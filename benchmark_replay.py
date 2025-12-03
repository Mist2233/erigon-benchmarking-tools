#!/usr/bin/env python3
"""Benchmark RPC latency for Erigon debug tracing endpoints."""

import argparse
import json
import sys
import time
from typing import Any, Dict, Optional

import requests
try:
    from tqdm import tqdm
    HAS_TQDM = True
except Exception:
    HAS_TQDM = False
    tqdm = None

DEFAULT_TRACER = "callTracer"
DEFAULT_TIMEOUT = "600s"


def parse_block_number(value: str) -> int:
    """Parse block number from decimal or hexadecimal representation."""
    if value.startswith("0x") or value.startswith("0X"):
        return int(value, 16)
    return int(value)


def build_trace_payload(block_number: int, tracer: str, timeout: str, request_id: int) -> Dict[str, Any]:
    block_hex = hex(block_number)
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "debug_traceBlockByNumber",
        "params": [block_hex, {"tracer": tracer, "timeout": timeout}],
    }


def benchmark(args: argparse.Namespace) -> None:
    session = requests.Session()

    if not args.no_warmup:
        try:
            session.post(
                args.rpc,
                json={"jsonrpc": "2.0", "id": "warmup", "method": "eth_blockNumber", "params": []},
                timeout=args.http_timeout,
            )
        except requests.RequestException as exc:
            print(f"⚠️  Warm-up request failed: {exc}")

    total_duration = 0.0
    request_count = 0
    success_count = 0
    latencies = []
    num_blocks = (args.end_block - args.start_block + 1)
    expected_requests = num_blocks * args.repeat

    print(
        f"🚀 Starting benchmark: blocks {args.start_block:,} -> {args.end_block:,} "
        f"(repeat {args.repeat}× per block) on {args.rpc}"
    )

    pbar = None
    if not args.no_progress and HAS_TQDM:
        pbar = tqdm(total=expected_requests, desc="🔬 RPC requests", unit="req")
    elif not args.no_progress and not HAS_TQDM:
        print("💡 Tip: Install tqdm for progress bar: pip install tqdm")

    for block_number in range(args.start_block, args.end_block + 1):
        for iteration in range(args.repeat):
            payload = build_trace_payload(block_number, args.tracer, args.timeout, request_count)
            try:
                t0 = time.perf_counter()
                response = session.post(
                    args.rpc,
                    json=payload,
                    timeout=args.http_timeout,
                )
                t1 = time.perf_counter()
            except requests.RequestException as exc:
                print(f"❌ Request failed for block {block_number} (iter {iteration + 1}): {exc}")
                if pbar is not None:
                    pbar.update(1)
                continue

            duration = t1 - t0
            total_duration += duration
            latencies.append(duration)
            request_count += 1
            if pbar is not None:
                pbar.update(1)

            if response.status_code != 200:
                print(
                    f"❌ HTTP {response.status_code} for block {block_number} "
                    f"(iter {iteration + 1}): {response.text[:200]}"
                )
                continue

            try:
                data = response.json()
            except json.JSONDecodeError as exc:
                print(f"❌ Invalid JSON response for block {block_number}: {exc}")
                continue

            if "error" in data:
                print(
                    f"❌ RPC error for block {block_number} (iter {iteration + 1}): {data['error']}"
                )
                continue

            success_count += 1

            if args.verbose:
                print(
                    f"✓ Block {block_number} iteration {iteration + 1} completed in {duration:.4f}s"
                )

    if request_count == 0:
        print("No requests were executed. Check your parameters.")
        if pbar is not None:
            pbar.close()
        return

    print("\n=== Benchmark Summary ===")
    print(f"Total requests: {request_count}")
    print(f"Successful responses: {success_count}")

    if total_duration > 0:
        avg_latency = total_duration / request_count
        tps = request_count / total_duration
    else:
        avg_latency = 0.0
        tps = 0.0

    print(f"Total RPC Time: {total_duration:.4f} s")
    print(f"Average Latency: {avg_latency * 1000:.2f} ms")
    print(f"Throughput (TPS): {tps:.2f} tx/s")

    if latencies:
        print(f"Fastest request: {min(latencies):.4f} s")
        print(f"Slowest request: {max(latencies):.4f} s")
    if pbar is not None:
        pbar.close()


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Erigon RPC latency")
    parser.add_argument("--rpc", default="http://127.0.0.1:8545", help="RPC endpoint URL")
    parser.add_argument("--start-block", type=parse_block_number, required=True)
    parser.add_argument("--end-block", type=parse_block_number, required=True)
    parser.add_argument("--repeat", type=int, default=1, help="Number of repetitions per block")
    parser.add_argument("--tracer", default=DEFAULT_TRACER, help="Tracer name to use")
    parser.add_argument("--timeout", default=DEFAULT_TIMEOUT, help="Tracer timeout value")
    parser.add_argument("--http-timeout", type=float, default=600.0, help="HTTP client timeout (seconds)")
    parser.add_argument("--no-warmup", action="store_true", help="Skip warm-up request")
    parser.add_argument("--verbose", action="store_true", help="Print per-request latency")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.start_block > args.end_block:
        print("start-block must be <= end-block")
        return 1

    if args.repeat < 1:
        print("repeat must be >= 1")
        return 1

    try:
        benchmark(args)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
