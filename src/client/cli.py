"""Command-line client for the agent server."""

from __future__ import annotations

import argparse
import json
import sys

import httpx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the A2A agent server")
    parser.add_argument("query", help="User query")
    parser.add_argument("--agent-url", default="http://localhost:7002", help="Agent server base URL")
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout seconds")
    parser.add_argument("--verbose", action="store_true", help="Print tool calls and trace id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    url = f"{args.agent_url}/v1/ask"
    payload = {"query": args.query}

    # Avoid inheriting system proxy settings that can break localhost calls.
    try:
        with httpx.Client(timeout=args.timeout, trust_env=False) as client:
            resp = client.post(url, json=payload)
    except httpx.ReadTimeout:
        print("Request timed out. The server may still be processing the request.")
        print("Try again with a longer timeout, e.g. --timeout 120")
        return 1
    if resp.status_code >= 400:
        print(f"Request failed: {resp.status_code}")
        print(resp.text)
        return 1

    data = resp.json()
    print(data.get("answer", ""))

    if args.verbose:
        # Debug view to inspect tool usage and trace_id.
        print("\n--- trace_id ---")
        print(data.get("trace_id"))
        print("\n--- tool_calls ---")
        print(json.dumps(data.get("tool_calls", []), ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
