#!/usr/bin/env python3
"""Run BI Joe without installing it: python scripts/run_bijoe.py <command> ...

Works from any folder. Needs Python 3.9+. CSV and SQLite need nothing else;
Excel needs `openpyxl`; other databases need `sqlalchemy` plus a driver.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bijoe.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
