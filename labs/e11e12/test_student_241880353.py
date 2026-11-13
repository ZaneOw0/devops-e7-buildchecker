"""Personal adapter and contract tests for 241880353 (A-track E11-E12)."""
import tempfile
import unittest
from pathlib import Path

import lab
import pipeline


class StudentE11A241880353(unittest.TestCase):
    def test_helper_new_local_header_adds_missing_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / 'sample'
            lab.fixture(project)
            baseline = lab.scan(project)
            (project / 'output_format.h').write_text(
                '#ifndef E12_OUTPUT_FORMAT_H\n'
                '#define E12_OUTPUT_FORMAT_H\n'
                '#define OUTPUT_FORMAT "%d\\n"\n'
                '#endif\n'
            )
            (project / 'helper.c').write_text(
                '#include <stdio.h>\n'
                '#include "output_format.h"\n'
                'int helper(void){return 0;}\n'
            )
            lab.commit(project, 'student: helper includes output_format.h')
            incremental = lab.scan(project, baseline)
            full = lab.scan(project)
            self.assertIn('output_format.h', incremental['actual']['helper.o'])
            self.assertEqual(incremental['declared']['helper.o'], ['helper.c'])
            self.assertIn(
                {'type': 'MISSING', 'target': 'helper.o', 'dependency': 'output_format.h'},
                incremental['findings'],
            )
            self.assertIn(['MISSING', 'helper.o', 'output_format.h'], incremental['added'])
            self.assertEqual(incremental['reused'], [])
            self.assertEqual(
                {(item['type'], item['target'], item['dependency']) for item in incremental['findings']},
                {(item['type'], item['target'], item['dependency']) for item in full['findings']},
            )
            self.assertEqual(
                pipeline.normalized(incremental['findings']),
                pipeline.normalized(full['findings']),
            )

    def test_incremental_envelope_rejected_when_commit_differs(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / 'sample'
            lab.fixture(project)
            report = lab.scan(project)
            target = report['commit']
            envelope = {
                'schema_version': 'e11e12-1',
                'job_id': 'job-student-241880353',
                'trace_id': 'trace-student-241880353',
                'kind': 'incremental-check',
                'commit': target,
                'status': 'SUCCEEDED',
                'data': report,
                'artifacts': [],
            }
            pipeline.check_envelope(envelope, target, 'incremental-check')
            with self.assertRaises(pipeline.Failure) as ctx:
                pipeline.check_envelope(envelope, '0' * 40, 'incremental-check')
            self.assertEqual(ctx.exception.code, 'STALE_REPORT')


if __name__ == '__main__':
    unittest.main()
