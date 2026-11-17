import argparse
import json
import sys
from pathlib import Path

from .engine import TrustError, check_receipt, load_policy, run_checks, snapshot


ONBOARDING = """# Project verification contract

1. Add existing static checks (types, lints, architecture boundaries) to policy.json.
2. Add runtime checks that exercise user-visible behavior. Each writes evidence
   under its TRUST_EVIDENCE_DIR. Use screenshots, traces, or observed results.
3. Map each important feature to its user path, expected result and runtime checks.
4. Run the toolkit and inspect the evidence. An empty starter policy cannot pass.

Use argument arrays for commands; shell syntax is not interpreted. Commands run
with your permissions and environment, so review a policy before executing it.
Keep credentials out of logs and evidence. Evidence stays local unless you share it.
Passing checks is evidence for review; release authorization is a separate decision.
Protect runner, policy, tests and CI configuration outside an agent's release authority.
"""


def initialize(root: Path) -> Path:
    snapshot(root)
    directory = root / ".trust"
    if directory.is_symlink():
        raise TrustError(".trust must be a directory inside the project, not a symlink")
    files = {
        "policy.json": json.dumps(
            {"version": 1, "project": root.name, "checks": [], "features": []},
            indent=2,
        ) + "\n",
        "README.md": ONBOARDING,
        ".gitignore": "/runs/\n",
    }
    for name in files:
        destination = directory / name
        if destination.exists() or destination.is_symlink():
            raise TrustError(f"refusing to overwrite {destination}")
    directory.mkdir(exist_ok=True)
    for name, contents in files.items():
        with (directory / name).open("x", encoding="utf-8") as stream:
            stream.write(contents)
    return directory / "policy.json"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="trust", description="Run project verification and check the resulting evidence."
    )
    commands = result.add_subparsers(dest="action", required=True)
    for action in ("init", "inspect", "run", "gate"):
        command = commands.add_parser(action)
        command.add_argument("--root", type=Path, default=Path.cwd())
        if action != "init":
            command.add_argument("--policy", type=Path)
        if action == "run":
            command.add_argument("--runs-dir", type=Path)
        if action == "gate":
            command.add_argument("--receipt", type=Path, required=True)
            command.add_argument("--max-age-seconds", type=int, default=86400)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.action == "init":
            path = initialize(root)
            print(f"Created {path}; add static checks, runtime checks and features before running.")
            return 0
        policy_path = args.policy or root / ".trust" / "policy.json"
        if args.action == "inspect":
            policy = load_policy(policy_path)
            print(json.dumps(policy, indent=2))
            return 0
        if args.action == "run":
            runs_dir = args.runs_dir or root / ".trust" / "runs"
            receipt_path = run_checks(root, policy_path, runs_dir)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            print(receipt_path)
            return 0 if receipt["passed"] else 1
        problems = check_receipt(root, policy_path, args.receipt, args.max_age_seconds)
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}", file=sys.stderr)
            return 1
        print("PASS: current evidence; release authorization is separate")
        return 0
    except (TrustError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
