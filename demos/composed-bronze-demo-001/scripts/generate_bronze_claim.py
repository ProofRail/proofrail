#!/usr/bin/env python3
"""Demo wrapper for the reusable ProofRail Bronze v0.1.1 generator."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DEMO_ROOT.parents[1]
GENERATOR = REPO_ROOT / "tools" / "claims" / "generate_bronze_claim_v0_1_1.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(GENERATOR), str(DEMO_ROOT)],
        cwd=str(REPO_ROOT),
    )
)
