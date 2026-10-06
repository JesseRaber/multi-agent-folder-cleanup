#!/usr/bin/env python3
"""Reproducible dependency-gated unittest runner."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import sys
import unittest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--powershell", choices=("powershell.exe", "pwsh"), required=True)
    parser.add_argument("--verbosity", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()

    if importlib.util.find_spec("yaml") is None:
        print("blocked: PyYAML missing; install the pinned test dependency with "
              f"{sys.executable} -m pip install -r requirements-dev.txt", file=sys.stderr)
        return 2
    engine = shutil.which(args.powershell)
    if engine is None:
        print(f"blocked: requested PowerShell engine not found: {args.powershell}", file=sys.stderr)
        return 2

    os.environ["AUDIT_TEST_POWERSHELL"] = engine
    repo = Path(__file__).resolve().parents[1]
    suite = unittest.defaultTestLoader.discover(str(repo / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
