"""C1/C2 handoff gates for 241880353 (A-side E13).

Refs: https://github.com/ZaneOw0/devops-e7-buildchecker/issues/17
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from handoff_a_to_b import make_handoff


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path, root, job_id):
    data = path.read_bytes()
    return {
        "uri": f"artifact://{job_id}/{path.relative_to(root).as_posix()}",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


class StudentE13Handoff241880353(unittest.TestCase):
    """A-side C1 must produce a live report; C2 must refuse a base-commit report."""

    TARGET = "745ecf2621c8221b97bf0a5435ace50150ef57d4"
    BASE = "0b62c79a6adb4cd913a814068074575afdbbd18b"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job = "job-241880353-c1"
        self.trace = "trace-241880353-c1"
        inner = self.root / "incremental-report.json"
        inner.write_text(
            json.dumps({"commit": self.TARGET, "findings": [{"type": "MISSING", "target": "helper.o", "dependency": "output_format.h"}]})
            + "\n"
        )
        stage = {
            "schema_version": "e11e12-1",
            "kind": "incremental-check",
            "status": "SUCCEEDED",
            "commit": self.TARGET,
            "job_id": self.job,
            "trace_id": self.trace,
            "data": {
                "commit": self.TARGET,
                "findings": [{"type": "MISSING", "target": "helper.o", "dependency": "output_format.h"}],
            },
            "artifacts": [artifact(inner, self.root, self.job)],
        }
        stage_path = self.root / "incremental-check.json"
        stage_path.write_text(json.dumps(stage) + "\n")
        result = {
            "schema_version": "e11e12-1",
            "status": "SUCCEEDED",
            "target_commit": self.TARGET,
            "job_id": self.job,
            "trace_id": self.trace,
            "stages": [
                {"name": "incremental-check", "artifact": artifact(stage_path, self.root, self.job)}
            ],
        }
        self.result_path = self.root / "result.json"
        self.result_path.write_text(json.dumps(result) + "\n")
        self.stage_path = stage_path

    def test_live_c1_report_keeps_job_and_artifact_sha(self):
        handoff = make_handoff(self.result_path, self.TARGET)
        self.assertEqual(handoff["kind"], "fixed-md")
        self.assertEqual(handoff["commit"], self.TARGET)
        self.assertEqual(handoff["source_report"]["job_id"], self.job)
        self.assertEqual(handoff["source_report"]["trace_id"], self.trace)
        self.assertEqual(handoff["source_report"]["sha256"], digest(self.stage_path))
        self.assertEqual(
            handoff["data"]["findings"],
            [{"type": "MISSING", "target": "helper.o", "dependency": "output_format.h"}],
        )

    def test_c2_stale_base_commit_report_is_rejected(self):
        stage = json.loads(self.stage_path.read_text())
        stage["commit"] = self.BASE
        stage["data"]["commit"] = self.BASE
        self.stage_path.write_text(json.dumps(stage) + "\n")
        result = json.loads(self.result_path.read_text())
        result["stages"][0]["artifact"] = artifact(self.stage_path, self.root, self.job)
        self.result_path.write_text(json.dumps(result) + "\n")
        with self.assertRaisesRegex(ValueError, "identity or target mismatch"):
            make_handoff(self.result_path, self.TARGET)

    def test_c2_wrong_target_request_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "another target commit"):
            make_handoff(self.result_path, "90646db8b8ad932da1a959d152942f987aaffff2")


if __name__ == "__main__":
    unittest.main()
