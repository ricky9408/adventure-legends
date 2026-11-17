from __future__ import annotations

import hashlib
import json
import math
import os
import re
import signal
import stat
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


class TrustError(Exception):
    pass


class _RunInterrupted(TrustError):
    pass


_ID = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OUTPUT = ".trust/runs"


def _json_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise TrustError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_pairs)
    except (OSError, UnicodeError, ValueError) as exc:
        raise TrustError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TrustError(f"JSON must contain an object: {path}")
    return value


def _fields(value: object, required: set[str], optional: set[str], where: str) -> None:
    if not isinstance(value, dict):
        raise TrustError(f"{where} must be an object")
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing or unknown:
        raise TrustError(f"{where}: missing fields {sorted(missing)}, unknown fields {sorted(unknown)}")


def _text(value: object, where: str) -> None:
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        raise TrustError(f"{where} must be a nonempty string without NUL")


def _identifier(value: object, where: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise TrustError(f"{where} must match [a-z][a-z0-9_-]{{0,63}}")


def _relative_file(value: object, where: str) -> None:
    _text(value, where)
    if "\\" in value or value.startswith("/") or any(part in ("", ".", "..") for part in value.split("/")):
        raise TrustError(f"{where} must be a normalized relative POSIX file path")
    if PurePosixPath(value).name in {"receipt.json", "stdout.log", "stderr.log"}:
        raise TrustError(f"{where} uses a reserved filename")


def load_policy(path: Path) -> dict:
    policy = _load_json(Path(path))
    _fields(policy, {"version", "project", "checks", "features"}, set(), "policy")
    if type(policy["version"]) is not int or policy["version"] != 1:
        raise TrustError("policy.version must be integer 1")
    _text(policy["project"], "policy.project")
    if not isinstance(policy["checks"], list) or not policy["checks"]:
        raise TrustError("policy.checks must be a nonempty list; configure static and runtime checks")
    checks = {}
    for check in policy["checks"]:
        _fields(check, {"id", "layer", "command", "timeout_seconds"}, {"artifacts"}, "check")
        _identifier(check["id"], "check.id")
        if check["id"] in checks:
            raise TrustError(f"Duplicate check id: {check['id']}")
        if check["layer"] not in ("static", "runtime", "formal"):
            raise TrustError(f"Unknown check layer: {check['layer']}")
        if not isinstance(check["command"], list) or not check["command"]:
            raise TrustError(f"{check['id']}.command must be a nonempty argv list")
        for argument in check["command"]:
            _text(argument, f"{check['id']}.command argument")
        timeout = check["timeout_seconds"]
        if type(timeout) not in (int, float) or not 0 < timeout <= 3600 or not math.isfinite(timeout):
            raise TrustError(f"{check['id']}.timeout_seconds must be finite and in (0, 3600]")
        artifacts = check.setdefault("artifacts", [])
        if not isinstance(artifacts, list):
            raise TrustError(f"{check['id']}.artifacts must be a list")
        seen = set()
        for artifact in artifacts:
            _relative_file(artifact, f"{check['id']}.artifact")
            if artifact in seen:
                raise TrustError(f"Duplicate artifact: {artifact}")
            seen.add(artifact)
        if check["layer"] == "runtime" and not artifacts:
            raise TrustError(f"Runtime check {check['id']} must declare at least one artifact")
        checks[check["id"]] = check
    if not {"static", "runtime"}.issubset({check["layer"] for check in checks.values()}):
        raise TrustError("Policy must contain both static and runtime checks")
    if not isinstance(policy["features"], list) or not policy["features"]:
        raise TrustError("policy.features must be a nonempty list")
    feature_ids = set()
    for feature in policy["features"]:
        _fields(feature, {"id", "user_path", "expectation", "checks"}, set(), "feature")
        _identifier(feature["id"], "feature.id")
        if feature["id"] in feature_ids:
            raise TrustError(f"Duplicate feature id: {feature['id']}")
        feature_ids.add(feature["id"])
        _text(feature["user_path"], "feature.user_path")
        _text(feature["expectation"], "feature.expectation")
        refs = feature["checks"]
        if not isinstance(refs, list) or not refs:
            raise TrustError(f"{feature['id']}.checks must be a nonempty list")
        for ref in refs:
            _identifier(ref, "feature check reference")
            if ref not in checks:
                raise TrustError(f"Feature {feature['id']} references unknown check: {ref}")
        if len(refs) != len(set(refs)):
            raise TrustError(f"Feature {feature['id']} contains duplicate check references")
        if not any(checks[ref]["layer"] == "runtime" for ref in refs):
            raise TrustError(f"Feature {feature['id']} requires a runtime check")
    return policy


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            while block := stream.read(1024 * 1024):
                digest.update(block)
            return digest.hexdigest()
    except OSError as exc:
        raise TrustError(f"Cannot hash {path}: {exc}") from exc


def _git(root: Path, *arguments: str, allow_failure: bool = False) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TrustError(f"Git inspection failed: {exc}") from exc
    if result.returncode and not allow_failure:
        raise TrustError(f"Git inspection failed: {result.stderr.decode(errors='replace').strip()}")
    return result


def _root(root: Path) -> Path:
    root = Path(root).resolve()
    discovered = _git(root, "rev-parse", "--show-toplevel").stdout.rstrip(b"\n")
    if Path(os.fsdecode(discovered)).resolve() != root:
        raise TrustError("--root must be the Git worktree root")
    return root


def _head(root: Path) -> str | None:
    result = _git(root, "rev-parse", "--verify", "HEAD", allow_failure=True)
    if not result.returncode:
        return result.stdout.decode().strip()
    reference = _git(root, "symbolic-ref", "-q", "HEAD", allow_failure=True)
    if not reference.returncode:
        exists = _git(root, "show-ref", "--verify", "--quiet", reference.stdout.decode().strip(), allow_failure=True)
        if exists.returncode == 1:
            return None
    raise TrustError("Cannot resolve Git HEAD")


def _parents_without_symlinks(path: Path, boundary: Path) -> None:
    try:
        parts = path.relative_to(boundary).parts
    except ValueError as exc:
        raise TrustError(f"Path escapes its directory: {path}") from exc
    current = boundary
    if current.is_symlink():
        raise TrustError(f"Symlink directory is not allowed: {current}")
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise TrustError(f"Symlink parent is not allowed: {current}")


def snapshot(root: Path) -> dict:
    root = _root(root)
    entries = _git(root, "ls-files", "--stage", "-z").stdout.split(b"\0")
    tracked = set()
    for entry in entries:
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, _object, stage = metadata.split(b" ")
        if mode == b"160000":
            raise TrustError("Submodules are unsupported; verify them separately before adopting this toolkit")
        if stage != b"0":
            raise TrustError("Resolve unmerged index entries before verification")
        filename = os.fsdecode(name)
        if filename == _OUTPUT or filename.startswith(_OUTPUT + "/"):
            raise TrustError("Evidence under .trust/runs must not be tracked")
        tracked.add(filename)
    others = {os.fsdecode(name) for name in _git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout.split(b"\0") if name}
    records = []
    for name in sorted(tracked | others):
        if name == _OUTPUT or name.startswith(_OUTPUT + "/"):
            continue
        path = root / name
        _parents_without_symlinks(path, root)
        try:
            info = path.lstat()
        except FileNotFoundError:
            records.append([name, "deleted"])
            continue
        except OSError as exc:
            raise TrustError(f"Cannot inspect {name}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            records.append([name, "symlink", os.readlink(path)])
        elif stat.S_ISREG(info.st_mode):
            records.append([name, "file", bool(info.st_mode & 0o111), _sha_file(path)])
        else:
            raise TrustError(f"Unsupported Git-visible file type: {name}")
    digest = _sha_bytes(json.dumps(records, ensure_ascii=True, separators=(",", ":")).encode())
    return {"root": str(root), "head": _head(root), "digest": digest, "file_count": len(records)}


def _regular_digest(path: Path, boundary: Path, *, allow_empty: bool = False) -> str:
    _parents_without_symlinks(path, boundary)
    try:
        info = path.lstat()
    except OSError as exc:
        raise TrustError(f"Missing evidence file {path.name}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise TrustError(f"Evidence must be a regular file, not a symlink: {path}")
    if not allow_empty and info.st_size == 0:
        raise TrustError(f"Evidence file is empty: {path}")
    return _sha_file(path)


def _terminate(process: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=0.25)
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait()


def _run_check(root: Path, run_dir: Path, check: dict) -> dict:
    evidence = run_dir / check["id"]
    evidence.mkdir()
    stdout = evidence / "stdout.log"
    stderr = evidence / "stderr.log"
    started = time.monotonic()
    returncode = None
    reasons = []
    environment = dict(os.environ, TRUST_EVIDENCE_DIR=str(evidence), PYTHONDONTWRITEBYTECODE="1")
    process = None
    completed = False
    cancelled = False
    interruptible = False

    def interrupted(_signal, _frame):
        nonlocal cancelled
        cancelled = True
        # Raising during spawn can lose the child handle; raising during cleanup can strand descendants.
        if interruptible:
            raise _RunInterrupted("Run interrupted by SIGTERM")

    previous_handler = None
    if threading.current_thread() is threading.main_thread():
        previous_handler = signal.signal(signal.SIGTERM, interrupted)
    try:
        with stdout.open("wb") as out, stderr.open("wb") as err:
            process = subprocess.Popen(check["command"], cwd=root, env=environment, stdout=out, stderr=err, shell=False, start_new_session=os.name == "posix")
            interruptible = True
            if cancelled:
                raise _RunInterrupted("Run interrupted by SIGTERM")
            try:
                returncode = process.wait(timeout=check["timeout_seconds"])
                completed = True
                if returncode:
                    reasons.append(f"Command exited with status {returncode}")
            except subprocess.TimeoutExpired:
                reasons.append(f"Command timed out after {check['timeout_seconds']} seconds")
    except (OSError, ValueError) as exc:
        reasons.append(f"Command could not run: {exc}")
    finally:
        interruptible = False
        try:
            if process is not None and (not completed or cancelled):
                _terminate(process)
                returncode = process.returncode
        finally:
            if previous_handler is not None:
                signal.signal(signal.SIGTERM, previous_handler)
    if cancelled:
        raise _RunInterrupted("Run interrupted by SIGTERM")
    artifacts = {}
    for artifact in check["artifacts"]:
        relative = f"{check['id']}/{artifact}"
        try:
            artifacts[relative] = _regular_digest(run_dir / relative, run_dir)
        except TrustError as exc:
            reasons.append(str(exc))
    log_hashes = {}
    for name, path in (("stdout", stdout), ("stderr", stderr)):
        try:
            log_hashes[f"{name}_sha256"] = _regular_digest(path, run_dir, allow_empty=True)
        except TrustError as exc:
            log_hashes[f"{name}_sha256"] = None
            reasons.append(str(exc))
    return {
        "id": check["id"], "layer": check["layer"], "command": check["command"],
        "status": "failed" if reasons else "passed", "returncode": returncode,
        "reason": "; ".join(reasons), "duration_seconds": round(time.monotonic() - started, 6),
        "stdout": f"{check['id']}/stdout.log", "stderr": f"{check['id']}/stderr.log",
        **log_hashes, "artifacts": artifacts,
    }


def run_checks(root: Path, policy_path: Path, runs_dir: Path) -> Path:
    root = _root(root)
    policy_path = Path(policy_path).absolute()
    policy = load_policy(policy_path)
    policy_hash = _sha_file(policy_path)
    engine_hash = _sha_file(Path(__file__))
    before = snapshot(root)
    runs_dir = Path(runs_dir).absolute()
    if runs_dir.resolve().is_relative_to(root) and runs_dir != root / _OUTPUT:
        raise TrustError("Custom runs directories must be outside the worktree")
    _parents_without_symlinks(runs_dir / "placeholder", Path(runs_dir.anchor))
    try:
        runs_dir.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=runs_dir))
    except OSError as exc:
        raise TrustError(f"Cannot create evidence directory: {exc}") from exc
    checks = [_run_check(root, run_dir, check) for check in policy["checks"]]
    try:
        after = snapshot(root)
        unchanged_policy = policy_hash == _sha_file(policy_path)
        unchanged_engine = engine_hash == _sha_file(Path(__file__))
    except TrustError as exc:
        after = {"error": str(exc)}
        unchanged_policy = unchanged_engine = False
    receipt = {
        "version": 1, "project": policy["project"], "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root), "head": before["head"], "snapshot_before": before, "snapshot_after": after,
        "policy_sha256": policy_hash, "engine_sha256": engine_hash,
        "passed": before == after and unchanged_policy and unchanged_engine and all(check["status"] == "passed" for check in checks),
        "checks": checks,
    }
    receipt_path = run_dir / "receipt.json"
    try:
        with receipt_path.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
            stream.write("\n")
    except OSError as exc:
        raise TrustError(f"Cannot write receipt: {exc}") from exc
    return receipt_path


def _valid_digest(value: object) -> bool:
    return isinstance(value, str) and bool(_SHA.fullmatch(value))


def check_receipt(root: Path, policy_path: Path, receipt_path: Path, max_age_seconds: int = 86400) -> list[str]:
    if type(max_age_seconds) is not int or max_age_seconds <= 0:
        raise TrustError("max_age_seconds must be a positive integer")
    root = _root(root)
    policy_path = Path(policy_path).absolute()
    policy = load_policy(policy_path)
    receipt_path = Path(receipt_path).absolute()
    problems = []
    try:
        if receipt_path.name != "receipt.json":
            raise TrustError("Receipt must be named receipt.json")
        _regular_digest(receipt_path, Path(receipt_path.anchor))
        receipt = _load_json(receipt_path)
        _fields(receipt, {"version", "project", "created_at", "root", "head", "snapshot_before", "snapshot_after", "policy_sha256", "engine_sha256", "passed", "checks"}, set(), "receipt")
        if type(receipt["version"]) is not int or receipt["version"] != 1:
            raise TrustError("Unsupported receipt version")
        if receipt["passed"] is not True:
            problems.append("Run did not pass")
        if receipt["project"] != policy["project"] or receipt["root"] != str(root):
            problems.append("Receipt belongs to a different project or worktree")
        if receipt["policy_sha256"] != _sha_file(policy_path):
            problems.append("Policy changed since verification")
        if receipt["engine_sha256"] != _sha_file(Path(__file__)):
            problems.append("Verification engine changed since verification")
        try:
            created = datetime.fromisoformat(receipt["created_at"])
            if created.tzinfo is None or created.utcoffset() != timezone.utc.utcoffset(created):
                raise ValueError("Timestamp must be UTC")
            age = (datetime.now(timezone.utc) - created).total_seconds()
            if age < 0:
                problems.append("Receipt timestamp is in the future")
            elif age > max_age_seconds:
                problems.append("Receipt has expired")
        except (TypeError, ValueError):
            problems.append("Invalid receipt timestamp")
        current = snapshot(root)
        for label in ("snapshot_before", "snapshot_after"):
            recorded = receipt[label]
            if not isinstance(recorded, dict) or set(recorded) != {"root", "head", "digest", "file_count"} or recorded != current:
                problems.append(f"{label} does not match current Git-visible workspace")
        if receipt["head"] != current["head"]:
            problems.append("Git HEAD changed since verification")
        recorded_checks = receipt["checks"]
        if not isinstance(recorded_checks, list) or len(recorded_checks) != len(policy["checks"]):
            raise TrustError("Receipt check coverage does not match policy")
        required_fields = {"id", "layer", "command", "status", "returncode", "reason", "duration_seconds", "stdout", "stderr", "stdout_sha256", "stderr_sha256", "artifacts"}
        for expected, recorded in zip(policy["checks"], recorded_checks):
            _fields(recorded, required_fields, set(), "receipt check")
            check_id = expected["id"]
            if any(recorded[key] != expected[key] for key in ("id", "layer", "command")):
                problems.append(f"Check definition mismatch: {check_id}")
            if recorded["status"] != "passed" or type(recorded["returncode"]) is not int or recorded["returncode"] != 0:
                problems.append(f"Check did not pass: {check_id}")
            if recorded["reason"] != "":
                problems.append(f"Check has a failure reason: {check_id}")
            duration = recorded["duration_seconds"]
            if type(duration) not in (int, float) or not 0 <= duration <= 86400 or not math.isfinite(duration):
                problems.append(f"Invalid check duration: {check_id}")
            artifacts = recorded["artifacts"]
            expected_artifacts = {f"{check_id}/{name}" for name in expected["artifacts"]}
            if not isinstance(artifacts, dict) or set(artifacts) != expected_artifacts:
                problems.append(f"Artifact coverage does not match policy: {check_id}")
                artifacts = {}
            files = [(name, digest, False) for name, digest in artifacts.items()]
            for log in ("stdout", "stderr"):
                relative = f"{check_id}/{log}.log"
                if recorded[log] != relative:
                    problems.append(f"Unexpected {log} path: {check_id}")
                files.append((relative, recorded[f"{log}_sha256"], True))
            for name, expected_digest, allow_empty in files:
                if not _valid_digest(expected_digest):
                    problems.append(f"Invalid evidence digest: {name}")
                    continue
                try:
                    actual = _regular_digest(receipt_path.parent / name, receipt_path.parent, allow_empty=allow_empty)
                    if actual != expected_digest:
                        problems.append(f"Evidence changed: {name}")
                except TrustError as exc:
                    problems.append(str(exc))
    except TrustError as exc:
        problems.append(str(exc))
    return problems
