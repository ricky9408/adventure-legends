import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tests/trust/persistence_probe.c"
SOURCES = (
    "save4.c", "save5.c", "creatures.c", "creature_data.c", "equipment.c",
    "equipment_data.c", "economy.c", "story_rewards.c", "progression_events.c",
)
EVIDENCE = []


def require_check_failure(result, function, condition):
    diagnostic = re.escape(function) + r":\d+: " + re.escape(condition)
    if result.returncode != 1 or result.stdout or not re.fullmatch(diagnostic, result.stderr.strip()):
        raise AssertionError(f"Expected CHECK failure in {function}: {condition}; got {result.returncode}: {result.stderr}")


class PersistenceProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="persistence-properties-")
        cls.directory = Path(cls.temporary.name).resolve()
        cls.compiler = shutil.which(os.environ.get("HOST_CC", "cc"))
        if cls.compiler is None:
            raise RuntimeError("A C compiler is required; persistence verification cannot be skipped")
        cls.binary = cls.compile_probe("production")

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @classmethod
    def compile_probe(cls, name, replacement=None):
        output = cls.directory / name
        source_paths = []
        for filename in SOURCES:
            source_paths.append(str(replacement[1] if replacement and replacement[0] == filename else ROOT / "src" / filename))
        command = [
            cls.compiler, "-std=c99", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            "-DSAVE4_HOST_TEST", "-DSAVE5_HOST_TEST", "-I", str(ROOT / "src"),
            str(PROBE), *source_paths, "-o", str(output),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        if completed.returncode:
            raise AssertionError("Production-linked probe did not compile:\n" + completed.stderr)
        return output

    def check_case(self, case):
        completed = subprocess.run([str(self.binary), case], cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("passed", result["status"])
        self.assertGreater(result["iterations"], 0)
        EVIDENCE.append(result)

    def test_each_interrupted_byte_write_preserves_the_last_committed_save(self):
        self.check_case("powerfail")

    def test_every_single_byte_corruption_in_new_bank_falls_back_to_prior_save(self):
        self.check_case("corruption")

    def test_valid_checksums_do_not_authorize_impossible_persistent_states(self):
        self.check_case("malformed")

    def test_independently_encoded_starters_migrate_without_new_rewards_for_each_revision(self):
        self.check_case("history")

    def test_writer_snapshot_and_loader_publication_are_atomic(self):
        self.check_case("snapshot")

    def test_nonzero_bytes_in_any_empty_roster_record_never_reach_sram(self):
        self.check_case("invalid-ram")

    def test_purchase_consumption_and_failure_preserve_money_and_inventory(self):
        self.check_case("economy")

    def test_replayed_credit_and_invalid_identity_never_duplicate_progress(self):
        self.check_case("credits")

    def test_party_mapping_and_unique_gear_preserve_identity_and_history(self):
        self.check_case("gear")

    def test_story_rewards_and_quest_slots_are_idempotent_and_bounded(self):
        self.check_case("story")

    def test_properties_reject_seeded_production_defects(self):
        mutations = (
            (
                "overwrite-current-save", "save5.c", "atomic",
                "atomic_save5_smoke", "save5_load(&loaded)",
                "writer_destination = active == 0 ? SAVE5_BANK_B : SAVE5_BANK_A;",
                "writer_destination = active == 0 ? SAVE5_BANK_A : SAVE5_BANK_B;",
            ),
            (
                "duplicate-event-credit", "creatures.c", "credits",
                "creature_credits", "creatures_credit_event(&roster, event, UINT_MAX, CREATURE_CREDIT_ENCOUNTER) == 0",
                "if (bit_get(r->expedition_events, event)) return 0;",
                "if (0) return 0;",
            ),
            (
                "duplicate-unique-purchase", "equipment.c", "gear",
                "party_and_gear", "equipment_purchase(&gear, 2, 0) == EQUIPMENT_DUPLICATE",
                "if(equipment_seen(s,id))return EQUIPMENT_DUPLICATE;",
                "if(0)return EQUIPMENT_DUPLICATE;",
            ),
            (
                "publish-purchase-before-save", "economy.c", "economy",
                "economy_transactions", "!memcmp(&original, &before, sizeof before)",
                "transaction.live=s;transaction.operation=operation;",
                "s->economy=transaction.next;transaction.live=s;transaction.operation=operation;",
            ),
        )
        for name, filename, case, function, condition, original, changed in mutations:
            with self.subTest(mutation=name):
                source = (ROOT / "src" / filename).read_text()
                self.assertEqual(1, source.count(original), "Mutation must alter one intended production statement")
                mutant = self.directory / (name + ".c")
                mutant.write_text(source.replace(original, changed, 1))
                binary = self.compile_probe(name, (filename, mutant))
                completed = subprocess.run([str(binary), case], cwd=ROOT, capture_output=True, text=True, timeout=120)
                require_check_failure(completed, function, condition)
                EVIDENCE.append({"mutation": name, "status": "rejected", "case": case, "diagnostic": completed.stderr.strip()})

    def test_unrelated_failures_do_not_count_as_seeded_defect_detection(self):
        for code, stdout, stderr in (
            (0, "", "atomic_save5_smoke:98: save5_load(&loaded)\n"),
            (-11, "", "Segmentation fault: 11\n"),
            (1, "", "ERROR: AddressSanitizer: heap-buffer-overflow\n"),
            (1, "", "save5.c:98: runtime error: index out of bounds\n"),
            (1, "", "atomic_save5_smoke:98: loaded.money == 7\n"),
            (1, "", "another_case:98: save5_load(&loaded)\n"),
            (1, "passed\n", "atomic_save5_smoke:98: save5_load(&loaded)\n"),
        ):
            with self.subTest(code=code, stderr=stderr):
                result = subprocess.CompletedProcess([], code, stdout, stderr)
                with self.assertRaises(AssertionError):
                    require_check_failure(result, "atomic_save5_smoke", "save5_load(&loaded)")


def write_report(result):
    destination = Path(os.environ.get("TRUST_EVIDENCE_DIR", str(ROOT / "build/trust-review")))
    destination.mkdir(parents=True, exist_ok=True)
    files = [PROBE, Path(__file__).resolve(), *(ROOT / "src" / name for name in SOURCES)]
    report = {
        "scope": "Fresh production-linked persistence, roster, gear, economy and story review",
        "status": "passed" if result.wasSuccessful() else "failed",
        "tests": result.testsRun,
        "sanitizers": ["address", "undefined"],
        "prior_tests_or_prose_used_as_oracle": False,
        "findings": [],
        "evidence": EVIDENCE,
        "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
        "gaps": [
            "Host SRAM byte-write failure injection is not physical cartridge power-loss testing.",
            "Historical revisions 1 through 13 have independently encoded starter-state migration coverage, not exhaustive authored-region histories.",
            "No blanket claim over all authored quest solutions or every populated roster state.",
            "progression.c and quickparty.c received source review; rendered input behavior belongs to the native runtime verification.",
        ],
    }
    (destination / "persistence-review.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PersistenceProperties)
    outcome = unittest.TextTestRunner(verbosity=2).run(suite)
    write_report(outcome)
    sys.exit(0 if outcome.wasSuccessful() else 1)
