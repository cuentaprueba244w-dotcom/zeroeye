#!/usr/bin/env python3
"""Verify build.py creates diagnostic artifacts even on failure."""
import json, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIAG_DIR = ROOT / "diagnostic"

def main() -> int:
    """Check diagnostic files exist and are valid."""
    if not DIAG_DIR.is_dir():
        print("FAIL: diagnostic/ dir missing"); return 1
    jfiles = sorted(DIAG_DIR.glob("*.json"))
    lfiles = sorted(DIAG_DIR.glob("*.logd"))
    if not jfiles:
        print("FAIL: no .json"); return 1
    if not lfiles:
        print("FAIL: no .logd"); return 1
    with open(jfiles[0]) as f:
        rpt = json.load(f)
    for k in ["commit","generated_at","modules","passed","failed"]:
        if k not in rpt:
            print(f"FAIL: missing {k}"); return 1
    print(f"OK: {len(jfiles)} JSON, {len(lfiles)} .logd")
    print(f"  {rpt["passed"]} passed / {rpt["failed"]} failed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
