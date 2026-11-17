"""Personal tests for 241880617 (A05, A track): incremental reuse plus repair-stage contracts."""
import tempfile
import unittest
from pathlib import Path

import lab
import pipeline
from draft.autobuild import prepare_candidate

DIGEST = '7' * 64

BROKEN_PINNED = f"""FROM python:3.13-slim@sha256:{DIGEST}
WORKDIR /work
COPY main.c helper.c *.h Makefile ./
RUN make app
CMD ["./app"]
"""

CANDIDATE = BROKEN_PINNED.replace(
    'RUN make app',
    'RUN apt-get update && apt-get install -y --no-install-recommends gcc make\nRUN make app')


class Reuse241880617(unittest.TestCase):
    """Reuse is decided by the composite key: directives, recipes, flags, compiler."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / 'sample'
        lab.fixture(self.project)

    def test_same_key_reuses_every_object(self):
        baseline = lab.scan(self.project)
        again = lab.scan(self.project, baseline)
        self.assertEqual(again['key'], baseline['key'])
        self.assertEqual(again['reused'], ['main.o', 'helper.o'])
        self.assertEqual(again['refreshed'], [])
        self.assertEqual(again['added'], [])
        self.assertEqual(again['resolved'], [])

    def test_project_include_change_refreshes_all_and_reports_missing(self):
        baseline = lab.scan(self.project)
        (self.project / 'main.c').write_text(
            '#include "extra.h"\n' + (self.project / 'main.c').read_text(encoding='utf-8'),
            encoding='utf-8')
        lab.commit(self.project, 'C1 add project include')
        incremental = lab.scan(self.project, baseline)
        self.assertNotEqual(incremental['key'], baseline['key'])
        self.assertEqual(incremental['reused'], [])
        self.assertEqual(sorted(incremental['refreshed']), ['helper.o', 'main.o'])
        self.assertEqual(incremental['added'], [['MISSING', 'main.o', 'extra.h']])
        self.assertEqual(
            pipeline.normalized(incremental['findings']),
            pipeline.normalized(lab.scan(self.project)['findings']))

    def test_recipe_change_alone_refreshes_all(self):
        baseline = lab.scan(self.project)
        makefile = (self.project / 'Makefile').read_text(encoding='utf-8')
        changed = makefile.replace('-c helper.c -o helper.o', '-Wall -c helper.c -o helper.o')
        self.assertNotEqual(makefile, changed)
        (self.project / 'Makefile').write_text(changed, encoding='utf-8')
        lab.commit(self.project, 'C1 recipe change')
        incremental = lab.scan(self.project, baseline)
        self.assertEqual(incremental['reused'], [])
        self.assertEqual(sorted(incremental['refreshed']), ['helper.o', 'main.o'])
        self.assertEqual(incremental['added'], [])


class Contract241880617(unittest.TestCase):
    """The repair stage may only consume an upstream report whose bytes match the manifest."""

    def test_manifest_hash_guards_repair_consumption(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            report = out / 'incremental-check.json'
            pipeline.save(report, {
                'schema_version': 'e11e12-1', 'job_id': 'job-student-241880617',
                'trace_id': 'trace-student-241880617', 'kind': 'incremental-check',
                'commit': 'a' * 40, 'status': 'SUCCEEDED', 'data': {'findings': []},
                'artifacts': []})
            reference = pipeline.artifact(report, out, 'job-student-241880617')
            self.assertEqual(
                reference['uri'], 'artifact://job-student-241880617/incremental-check.json')
            envelope = pipeline.load_artifact(report, reference['sha256'])
            pipeline.check_envelope(envelope, 'a' * 40, 'incremental-check')
            report.write_text(report.read_text(encoding='utf-8') + ' \n', encoding='utf-8')
            with self.assertRaises(pipeline.Failure) as ctx:
                pipeline.load_artifact(report, reference['sha256'])
            self.assertEqual(ctx.exception.code, 'ARTIFACT_HASH_MISMATCH')
            self.assertIn('transfer', str(ctx.exception))


class Candidate241880617(unittest.TestCase):
    """A pinned Dockerfile.broken must still accept a candidate that keeps the same digest."""

    def test_pinned_broken_accepts_added_run_layer(self):
        baseline = prepare_candidate(BROKEN_PINNED, CANDIDATE)
        self.assertEqual(baseline.splitlines()[0], BROKEN_PINNED.splitlines()[0])
        self.assertNotIn('apt-get', baseline)

    def test_pinned_broken_rejects_changed_digest(self):
        with self.assertRaisesRegex(ValueError, 'base image tag'):
            prepare_candidate(BROKEN_PINNED, CANDIDATE.replace(DIGEST, '8' * 64))

    def test_unpinned_broken_still_compares_tags(self):
        unpinned = BROKEN_PINNED.replace('@sha256:' + DIGEST, '')
        prepare_candidate(unpinned, CANDIDATE)
        with self.assertRaisesRegex(ValueError, 'base image tag'):
            prepare_candidate(unpinned, CANDIDATE.replace('python:3.13-slim', 'python:3.12-slim'))


if __name__ == '__&#8203;main__':
    unittest.main()
