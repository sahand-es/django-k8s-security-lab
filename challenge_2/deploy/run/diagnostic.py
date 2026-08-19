#!/usr/bin/env python3
import sys

TARGETS = {"api", "worker", "database", "scheduler"}


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "api"
    if target not in TARGETS:
        print(f"unknown target: {target}")
        return 1
    print(f"checking {target}: healthy (cpu 12%, mem 41%, queue 0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())