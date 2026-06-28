#!/usr/bin/env python3
"""ProofRail Gold Local Minimal Profile validator v0.1.0.

Validates the `gold.local.minimal` profile conformance of the
ProofRail repository per:

  schemas/gold-local-minimal-profile-v0.1.0.md
  profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md

This is a VALIDATOR-ONLY tool (no builder). It does not build,
write, or publish any artifact. It emits a single closed-vocabulary
text result on stdout/stderr plus an exit code.

Closed v0.4.6-owned reason surface (R62..R66), all under the
`gold_local_minimal_profile_*` namespace:

  R62 gold_local_minimal_profile_required_artifact_missing
  R63 gold_local_minimal_profile_required_make_target_missing
  R64 gold_local_minimal_profile_required_verifier_failed
  R65 gold_local_minimal_profile_required_non_claim_missing
  R66 gold_local_minimal_profile_descriptor_invalid

Inherited closed reason surface R01..R61 is relayed verbatim when
an invoked inherited verifier exits nonzero and emits a recognized
`FAIL: <snake_case_reason>:` line on its output. The v0.4.6
validator never wraps, prepends, paraphrases, or appends to the
inherited reason line; R64 does not fire in that case.

Check order (locked):

  R62 -> R63 -> R65 -> R66 -> R64

Exit codes:

  0  conformance PASS
  1  conformance FAIL (R62..R66, or relayed inherited R01..R61)
  3  INFRA failure (non-reason-shaped)
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# -- Profile identity ------------------------------------------------

PROFILE_NAME = "gold.local.minimal"
PROFILE_VERSION = "v0.1.0"
PROOFRAIL_RELEASE = "gold.local_minimal_profile.v0.4.6"

SCHEMA_REL_PATH = "schemas/gold-local-minimal-profile-v0.1.0.md"
DESCRIPTOR_REL_PATH = (
    "profiles/gold/GOLD_LOCAL_MINIMAL_PROFILE_v0.1.0.md"
)


# -- Closed required-artifact set (R62; 46 paths) --------------------

REQUIRED_ARTIFACTS = (
    # 15 Gold schemas
    "schemas/gold-governed-reliance-package-v0.1.0.md",
    "schemas/gold-governed-reliance-package-manifest-v0.1.0.md",
    "schemas/gold-governed-reliance-conformance-report-v0.1.0.md",
    "schemas/gold-governed-reliance-decision-report-v0.1.0.md",
    "schemas/gold-decision-report-package-manifest-v0.1.0.md",
    "schemas/gold-policy-evaluation-matrix-v0.1.0.md",
    "schemas/gold-policy-evaluation-matrix-package-manifest-v0.1.0.md",
    "schemas/gold-policy-evaluation-report-v0.1.0.md",
    "schemas/gold-challenge-lifecycle-records-v0.1.0.md",
    "schemas/gold-challenge-lifecycle-report-v0.1.0.md",
    "schemas/gold-challenge-lifecycle-package-manifest-v0.1.0.md",
    "schemas/gold-reliance-package-index-v0.1.0.md",
    "schemas/gold-reliance-package-index-manifest-v0.1.0.md",
    "schemas/gold-multi-case-reliance-index-v0.1.0.md",
    "schemas/gold-multi-case-reliance-package-manifest-v0.1.0.md",
    # 12 Gold tools (6 build/verify pairs)
    "tools/gold/build_gold_governed_reliance_demo_v0_1_0.py",
    "tools/gold/verify_gold_governed_reliance_demo_v0_1_0.py",
    "tools/gold/build_gold_decision_report_hardening_v0_1_0.py",
    "tools/gold/verify_gold_decision_report_hardening_v0_1_0.py",
    "tools/gold/build_gold_policy_evaluation_matrix_v0_1_0.py",
    "tools/gold/verify_gold_policy_evaluation_matrix_v0_1_0.py",
    "tools/gold/build_gold_challenge_lifecycle_lite_v0_1_0.py",
    "tools/gold/verify_gold_challenge_lifecycle_lite_v0_1_0.py",
    "tools/gold/build_gold_reliance_package_index_v0_1_0.py",
    "tools/gold/verify_gold_reliance_package_index_v0_1_0.py",
    "tools/gold/build_gold_multi_case_reliance_v0_1_0.py",
    "tools/gold/verify_gold_multi_case_reliance_v0_1_0.py",
    # 6 Gold harness scripts
    "tests/test_gold_governed_reliance_v0_4_0.sh",
    "tests/test_gold_decision_report_hardening_v0_4_1.sh",
    "tests/test_gold_policy_evaluation_matrix_v0_4_2.sh",
    "tests/test_gold_challenge_lifecycle_lite_v0_4_3.sh",
    "tests/test_gold_reliance_package_index_v0_4_4.sh",
    "tests/test_gold_multi_case_reliance_v0_4_5.sh",
    # 7 Gold long-form docs
    "docs/gold/minimal-gold-governed-reliance-v0.4.0.md",
    "docs/gold/gold-decision-report-hardening-v0.4.1.md",
    "docs/gold/gold-policy-evaluation-matrix-v0.4.2.md",
    "docs/gold/gold-challenge-lifecycle-lite-v0.4.3.md",
    "docs/gold/gold-reliance-package-index-v0.4.4.md",
    "docs/gold/gold-multi-case-reliance-v0.4.5.md",
    "docs/gold/gold-boundary-v0.2.5.md",
    # 6 Gold demo READMEs
    "demos/gold-demo-001-governed-reliance/README.md",
    "demos/gold-demo-002-decision-report-hardening/README.md",
    "demos/gold-demo-003-policy-evaluation-matrix/README.md",
    "demos/gold-demo-004-challenge-lifecycle-lite/README.md",
    "demos/gold-demo-005-reliance-package-index/README.md",
    "demos/gold-demo-006-multi-case-reliance/README.md",
)


# -- Closed required Make-target set (R63; 7 targets) ----------------

REQUIRED_TARGETS = (
    "verify-gold-governed-reliance-v0-4-0",
    "verify-gold-decision-report-hardening-v0-4-1",
    "verify-gold-policy-evaluation-matrix-v0-4-2",
    "verify-gold-challenge-lifecycle-lite-v0-4-3",
    "verify-gold-reliance-package-index-v0-4-4",
    "verify-gold-multi-case-reliance-v0-4-5",
    "verify-gold-all",
)


# -- R64 execution set (6 inherited verify targets only) -------------
#
# verify-gold-all is intentionally EXCLUDED from the R64 execution
# set. Reasons:
#   1. It is an aggregator over the 6 inherited verify targets,
#      not itself an inherited verifier.
#   2. Phase 4 of v0.4.6 extends verify-gold-all to include
#      verify-gold-local-minimal-profile-v0-4-6 itself; invoking
#      verify-gold-all from inside this validator would create
#      recursion after Phase 4.
# The Phase 1 schema/descriptor language "inherited verifier
# subprocess sweep over [the required targets]" naturally
# restricts to actual inherited verifiers, which is exactly this
# 6-target set.

R64_EXECUTION_TARGETS = (
    "verify-gold-governed-reliance-v0-4-0",
    "verify-gold-decision-report-hardening-v0-4-1",
    "verify-gold-policy-evaluation-matrix-v0-4-2",
    "verify-gold-challenge-lifecycle-lite-v0-4-3",
    "verify-gold-reliance-package-index-v0-4-4",
    "verify-gold-multi-case-reliance-v0-4-5",
)


# -- Closed required non-claim set (R65; 8 exact phrases) ------------

REQUIRED_NON_CLAIMS = (
    "no certification",
    "no legal adjudication",
    "no production reliance transfer",
    "no federation",
    "no live registry trust",
    "no verifier revocation semantics",
    "no stale-registry semantics",
    (
        "no claim that local demo conformance equals "
        "institutional assurance"
    ),
)


# -- Closed required descriptor section layout (R66; 9 sections) -----

REQUIRED_DESCRIPTOR_SECTIONS = (
    "## 1. Profile Identity",
    "## 2. Scope and Boundary",
    "## 3. Required Inherited Gold Artifacts",
    "## 4. Required Makefile Targets",
    "## 5. Validator Reason Surface",
    "## 6. Required Non-Claims",
    "## 7. Validator Surface",
    "## 8. Conformance Output",
    "## 9. Changelog",
)

# Schema section markers used to bound bullet enumerations under
# R66 schema-parity checks.
SCHEMA_ARTIFACTS_HEADING = (
    "## 4. Required inherited Gold artifacts (R62 scope)"
)
SCHEMA_TARGETS_HEADING = (
    "## 5. Required Makefile targets (R63 scope)"
)
SCHEMA_NEXT_AFTER_TARGETS = (
    "## 6. Validator reason surface (closed)"
)


# -- Recognized inherited FAIL pattern -------------------------------
#
# Inherited ProofRail Gold verifiers (R01..R61, established across
# v0.4.0..v0.4.5) all emit failure lines in the closed
# `FAIL: <snake_case_reason>:` shape. The v0.4.6 validator
# recognizes any such line on stderr or stdout of an invoked
# inherited verifier as an inherited reason and relays it verbatim
# WITHOUT WRAPPING (and does NOT emit R64). R64 fires only when
# the invoked verifier exits nonzero AND no recognized
# `FAIL: <reason>:` line is present.

INHERITED_FAIL_RE = re.compile(r"^FAIL:\s+[a-z][a-z0-9_]*:")


# -- v0.4.6-owned reason tokens --------------------------------------

R62 = "gold_local_minimal_profile_required_artifact_missing"
R63 = "gold_local_minimal_profile_required_make_target_missing"
R64 = "gold_local_minimal_profile_required_verifier_failed"
R65 = "gold_local_minimal_profile_required_non_claim_missing"
R66 = "gold_local_minimal_profile_descriptor_invalid"


# -- Emission helpers ------------------------------------------------


def emit_fail(reason: str, diagnostic: str) -> None:
    print(f"FAIL: {reason}: {diagnostic}", file=sys.stderr)


def emit_infra(message: str) -> None:
    print(f"INFRA: {message}", file=sys.stderr)


def emit_pass() -> None:
    print("PASS: gold_local_minimal_profile_conformance")


# -- Text helpers ----------------------------------------------------


def normalize_ws(line: str) -> str:
    """Whitespace-normalize for R65 phrase comparison.

    Trims leading/trailing whitespace and collapses any internal
    run of whitespace to a single ASCII space.
    """
    return re.sub(r"\s+", " ", line.strip())


def read_text_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_section(
    text: str, heading: str, next_heading: str | None
) -> str:
    """Return text from `heading` up to (but not including)
    `next_heading`. If `next_heading` is None, returns to EOF.
    Returns empty string if `heading` is not found.
    """
    start = text.find(heading)
    if start < 0:
        return ""
    if next_heading is None:
        return text[start:]
    end = text.find(next_heading, start + len(heading))
    if end < 0:
        return text[start:]
    return text[start:end]


def extract_bullet_paths(section_text: str) -> list[str]:
    """Extract bulleted backtick-quoted items: `- \`item\``.

    Used for parsing both the descriptor and schema enumerations
    of required artifacts and Make targets.
    """
    items: list[str] = []
    for line in section_text.splitlines():
        m = re.match(r"^-\s+`([^`]+)`\s*$", line)
        if m:
            items.append(m.group(1))
    return items


# -- INFRA error class -----------------------------------------------


class InfraError(Exception):
    pass


# -- R62: required-artifact existence -------------------------------


def check_r62(repo_root: Path) -> str | None:
    for rel in REQUIRED_ARTIFACTS:
        p = repo_root / rel
        if not p.is_file() or not os.access(p, os.R_OK):
            return rel
    return None


# -- R63: required-Make-target declaration --------------------------


def check_r63(makefile_text: str) -> str | None:
    for target in REQUIRED_TARGETS:
        phony_pat = re.compile(
            rf"^\.PHONY:\s+{re.escape(target)}\s*$",
            re.MULTILINE,
        )
        rule_pat = re.compile(
            rf"^{re.escape(target)}:", re.MULTILINE
        )
        if not phony_pat.search(makefile_text):
            return target
        if not rule_pat.search(makefile_text):
            return target
    return None


# -- R65: required non-claim phrase scan ----------------------------


def check_r65(descriptor_text: str) -> str | None:
    section = extract_section(
        descriptor_text,
        "## 6. Required Non-Claims",
        "## 7. Validator Surface",
    )
    normalized_lines = {
        normalize_ws(line)
        for line in section.splitlines()
        if line.strip()
    }
    for phrase in REQUIRED_NON_CLAIMS:
        if normalize_ws(phrase) not in normalized_lines:
            return phrase
    return None


# -- R66: descriptor self-integrity ---------------------------------


def check_r66(
    descriptor_text: str, schema_text: str
) -> str | None:
    # 1. Each required section appears exactly once, in order.
    positions: list[int] = []
    for heading in REQUIRED_DESCRIPTOR_SECTIONS:
        pat = re.compile(
            rf"^{re.escape(heading)}\s*$", re.MULTILINE
        )
        matches = list(pat.finditer(descriptor_text))
        if len(matches) == 0:
            return (
                f"descriptor missing required section: {heading}"
            )
        if len(matches) > 1:
            return (
                "descriptor has duplicate required section: "
                f"{heading}"
            )
        positions.append(matches[0].start())
    if positions != sorted(positions):
        return "descriptor required sections are out of order"

    expected_artifacts = set(REQUIRED_ARTIFACTS)
    expected_targets = set(REQUIRED_TARGETS)

    # 2. Descriptor section 3 enumeration parity.
    desc_artifacts = set(
        extract_bullet_paths(
            extract_section(
                descriptor_text,
                "## 3. Required Inherited Gold Artifacts",
                "## 4. Required Makefile Targets",
            )
        )
    )
    if desc_artifacts != expected_artifacts:
        missing = expected_artifacts - desc_artifacts
        extra = desc_artifacts - expected_artifacts
        if missing:
            return (
                "descriptor section 3 missing required path: "
                f"{sorted(missing)[0]}"
            )
        return (
            "descriptor section 3 has unexpected path: "
            f"{sorted(extra)[0]}"
        )

    # 3. Descriptor section 4 enumeration parity.
    desc_targets = set(
        extract_bullet_paths(
            extract_section(
                descriptor_text,
                "## 4. Required Makefile Targets",
                "## 5. Validator Reason Surface",
            )
        )
    )
    if desc_targets != expected_targets:
        missing = expected_targets - desc_targets
        extra = desc_targets - expected_targets
        if missing:
            return (
                "descriptor section 4 missing required target: "
                f"{sorted(missing)[0]}"
            )
        return (
            "descriptor section 4 has unexpected target: "
            f"{sorted(extra)[0]}"
        )

    # 4. Schema section 4 enumeration parity.
    schema_artifacts = set(
        extract_bullet_paths(
            extract_section(
                schema_text,
                SCHEMA_ARTIFACTS_HEADING,
                SCHEMA_TARGETS_HEADING,
            )
        )
    )
    if schema_artifacts != expected_artifacts:
        missing = expected_artifacts - schema_artifacts
        extra = schema_artifacts - expected_artifacts
        if missing:
            return (
                "schema section 4 missing required path: "
                f"{sorted(missing)[0]}"
            )
        return (
            "schema section 4 has unexpected path: "
            f"{sorted(extra)[0]}"
        )

    # 5. Schema section 5 enumeration parity.
    schema_targets = set(
        extract_bullet_paths(
            extract_section(
                schema_text,
                SCHEMA_TARGETS_HEADING,
                SCHEMA_NEXT_AFTER_TARGETS,
            )
        )
    )
    if schema_targets != expected_targets:
        missing = expected_targets - schema_targets
        extra = schema_targets - expected_targets
        if missing:
            return (
                "schema section 5 missing required target: "
                f"{sorted(missing)[0]}"
            )
        return (
            "schema section 5 has unexpected target: "
            f"{sorted(extra)[0]}"
        )

    return None


# -- R64: inherited verifier subprocess sweep ------------------------


def run_r64(
    repo_root: Path, make_binary: str
) -> tuple[str | None, str | None]:
    """Run the 6 inherited verify targets in declared order.

    Returns:
        (relay_line, r64_diagnostic)

        relay_line: a verbatim recognized inherited
            `FAIL: <reason>:` line to emit on stderr with no
            wrapping (exit 1). None if no inherited reason was
            recognized.
        r64_diagnostic: a human-readable diagnostic to attach to
            the R64 reason when the invoked verifier exited
            nonzero without emitting a recognized inherited
            reason line.

        (None, None) means all 6 inherited verifiers passed.

    Raises InfraError for subprocess execution faults.
    """
    for target in R64_EXECUTION_TARGETS:
        try:
            proc = subprocess.run(
                [make_binary, "-C", str(repo_root), target],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as e:
            raise InfraError(
                f"make binary not executable: {make_binary}: {e}"
            )
        except OSError as e:
            raise InfraError(
                "subprocess execution failed for target "
                f"{target!r}: {e}"
            )

        if proc.returncode == 0:
            continue

        # Nonzero exit. Scan stderr first (canonical reason
        # channel), then stdout, for a recognized inherited
        # `FAIL: <snake>:` line. Relay the first match verbatim.
        for stream_text in (proc.stderr, proc.stdout):
            for line in stream_text.splitlines():
                if INHERITED_FAIL_RE.match(line):
                    return (line, None)

        # No recognized inherited reason line: R64 fires.
        diag = (
            f"inherited verifier target {target!r} exited "
            f"{proc.returncode} without a recognized inherited "
            "FAIL: <reason>: line"
        )
        return (None, diag)

    return (None, None)


# -- Main ------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="verify_gold_local_minimal_profile_v0_1_0.py",
        description=(
            "ProofRail Gold Local Minimal Profile validator. "
            "Profile name: gold.local.minimal; profile version: "
            "v0.1.0; release token: "
            "gold.local_minimal_profile.v0.4.6. Validator-only "
            "(no builder); emits no runtime artifact; emits no "
            "JSON conformance certificate."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Path to repository root containing the profile "
            "descriptor, schema, required inherited Gold "
            "artifacts, and Makefile. Default: current working "
            "directory."
        ),
    )
    parser.add_argument(
        "--make-binary",
        default="make",
        help=(
            "Path or PATH-resolvable name of the make binary "
            "used for the R64 inherited-verifier subprocess "
            "sweep. Default: 'make'."
        ),
    )
    parser.add_argument(
        "--skip-make",
        action="store_true",
        help=(
            "Skip the R64 inherited-verifier subprocess sweep "
            "(R62/R63/R65/R66 still run). Under --skip-make the "
            "R64 reason cannot fire and inherited reason relay "
            "is unreachable, by design."
        ),
    )
    args = parser.parse_args()

    try:
        # Resolve repo root.
        if args.repo_root is None:
            repo_root = Path.cwd()
        else:
            repo_root = Path(args.repo_root)
        if not repo_root.is_dir():
            raise InfraError(
                f"repo root not a readable directory: "
                f"{repo_root}"
            )

        # Descriptor + schema must be present and UTF-8 readable.
        # These are v0.4.6-owned files (not inherited Gold
        # artifacts), so their absence/illegibility is INFRA,
        # not R62.
        descriptor_path = repo_root / DESCRIPTOR_REL_PATH
        schema_path = repo_root / SCHEMA_REL_PATH
        if not descriptor_path.is_file():
            raise InfraError(
                f"descriptor file not found: "
                f"{DESCRIPTOR_REL_PATH}"
            )
        if not schema_path.is_file():
            raise InfraError(
                f"schema file not found: {SCHEMA_REL_PATH}"
            )
        try:
            descriptor_text = read_text_utf8(descriptor_path)
        except UnicodeDecodeError as e:
            raise InfraError(f"descriptor not valid UTF-8: {e}")
        try:
            schema_text = read_text_utf8(schema_path)
        except UnicodeDecodeError as e:
            raise InfraError(f"schema not valid UTF-8: {e}")

        # Makefile must be present and UTF-8 readable for R63.
        makefile_path = repo_root / "Makefile"
        if not makefile_path.is_file():
            raise InfraError("Makefile not found at repo root")
        try:
            makefile_text = read_text_utf8(makefile_path)
        except UnicodeDecodeError as e:
            raise InfraError(f"Makefile not valid UTF-8: {e}")

        # R62
        missing_artifact = check_r62(repo_root)
        if missing_artifact is not None:
            emit_fail(R62, missing_artifact)
            return 1

        # R63
        missing_target = check_r63(makefile_text)
        if missing_target is not None:
            emit_fail(R63, missing_target)
            return 1

        # R65
        missing_phrase = check_r65(descriptor_text)
        if missing_phrase is not None:
            emit_fail(R65, missing_phrase)
            return 1

        # R66
        descriptor_issue = check_r66(descriptor_text, schema_text)
        if descriptor_issue is not None:
            emit_fail(R66, descriptor_issue)
            return 1

        # R64 (skipped under --skip-make).
        if not args.skip_make:
            # Resolve make binary. shutil.which handles both bare
            # names (PATH search) and absolute/relative paths.
            if shutil.which(args.make_binary) is None:
                raise InfraError(
                    "make binary not found on PATH or as a "
                    f"file: {args.make_binary}"
                )
            relay_line, r64_diag = run_r64(
                repo_root, args.make_binary
            )
            if relay_line is not None:
                # Verbatim relay of inherited FAIL line. No
                # wrapper, no prefix, no suffix.
                print(relay_line, file=sys.stderr)
                return 1
            if r64_diag is not None:
                emit_fail(R64, r64_diag)
                return 1

        emit_pass()
        return 0

    except InfraError as e:
        emit_infra(str(e))
        return 3


if __name__ == "__main__":
    sys.exit(main())
