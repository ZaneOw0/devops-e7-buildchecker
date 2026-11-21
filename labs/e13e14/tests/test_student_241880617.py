"""Regression for the E13 defect 241880617 found in scan_runtime_logs.py.

Parser source assigns a token pointer from a function call or from an array
element. The 2851-byte version reported those assignments as hard-coded
credentials, so scanning an evidence directory that carries source or build
logs produced false hits and the "no secrets" conclusion became unexplainable.

Fixtures below are assembled with templates so this file itself never contains
a literal assignment the repository secret scanner would flag.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCANNER = ROOT / 'labs' / 'e13e14' / 'scan_runtime_logs.py'
FAKE_KEY = 'sk-' + 'demo' + '1234567890' + 'abcdefghijk'


def scan(path):
    proc = subprocess.run([sys.executable, str(SCANNER), str(path)],
                          cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def hits(output):
    for line in output.splitlines():
        if line.startswith('runtime log scan:'):
            return int(line.split('hits=')[1].split()[0])
    raise AssertionError('scanner summary line missing: ' + output)


class StudentE13Scanner241880617(unittest.TestCase):
    """C code is not a secret; a real key still is."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding='utf-8')
        return path

    def test_parser_assignments_are_not_reported(self):
        self.write('parse.log', '\n'.join([
            'tok' + 'en = %s(parser, tokens, 4)' % 'jsmn_alloc_tok' + 'en',
            'nod' + 'e = &tok' + 'ens[parser->toknext - 1]',
            'api_sec' + 'ret = %s[42]' % 'keys_table',
            '',
        ]))
        code, output = scan(self.root)
        self.assertEqual(code, 0, output)
        self.assertEqual(hits(output), 0, output)

    def test_real_key_is_still_reported(self):
        self.write('leak.log', 'api_key = "%s"\n' % FAKE_KEY)
        code, output = scan(self.root)
        self.assertEqual(code, 1, output)
        self.assertGreaterEqual(hits(output), 1, output)
        self.assertNotIn(FAKE_KEY, output, 'scanner must mask the value')

    def test_clean_copy_passes(self):
        self.write('clean.log', 'api_key = "your-key-here"\nbuild finished\n')
        code, output = scan(self.root)
        self.assertEqual(code, 0, output)
        self.assertEqual(hits(output), 0, output)

    def test_placeholder_assignment_is_still_excluded(self):
        self.write('template.log', 'secret = ${SECRET_FROM_ENV}\n')
        code, output = scan(self.root)
        self.assertEqual(code, 0, output)
        self.assertEqual(hits(output), 0, output)


if __name__ == '__main__':
    unittest.main()
