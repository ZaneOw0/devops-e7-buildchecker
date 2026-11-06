import json, tempfile, unittest
from pathlib import Path
from lab import fixture,scan,patch,commit

class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/'sample';fixture(self.p)

    def test_independent_known_edges(self):
        r=scan(self.p)
        self.assertEqual(r['actual']['main.o'],['config.h','main.c'])
        self.assertEqual({(f['type'],f['dependency']) for f in r['findings']},{('MISSING','config.h'),('REDUNDANT','unused.h')})

    def test_unchanged_reuses_both_targets(self):
        r=scan(self.p,scan(self.p));self.assertEqual(r['reused'],['main.o','helper.o']);self.assertEqual(r['refreshed'],[])

    def test_include_added_invalidates_cache(self):
        old=scan(self.p)
        (self.p/'main.c').write_text('#include "extra.h"\n'+(self.p/'main.c').read_text());commit(self.p,'new include')
        r=scan(self.p,old)
        self.assertIn(['MISSING','main.o','extra.h'],r['added']);self.assertEqual(len(r['refreshed']),2)

    def test_patch_preserves_redundant_dependency(self):
        r=scan(self.p);diff,plan=patch(self.p,r)
        self.assertIn('+main.o: main.c unused.h config.h',diff)
        self.assertNotIn('-\tgcc',diff)
        self.assertNotIn('config.h',(self.p/'Makefile').read_text())

    def test_old_report_rejected(self):
        r=scan(self.p);r['commit']='0'*40
        with self.assertRaisesRegex(ValueError,'STALE_REPORT'):patch(self.p,r)

    def test_unsafe_dependency_rejected(self):
        r=scan(self.p);r['findings']=[{'type':'MISSING','target':'main.o','dependency':'../outside.h'}]
        with self.assertRaisesRegex(ValueError,'UNSAFE_PATH'):patch(self.p,r)

    def test_unsupported_configuration_rejected(self):
        (self.p/'Makefile').write_text((self.p/'Makefile').read_text().replace('-O0','-include unknown.h'))
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_FLAGS'):scan(self.p)
class StudentE8A241880617(unittest.TestCase):
    def test_unused_header_content_change_forces_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            old=scan(p)
            (p/'unused.h').write_text('#define UNUSED_NOTE "edited"\n')
            commit(p,'student: edit declared-but-unused header')
            result=scan(p,old)
            self.assertEqual(result['actual'],old['actual'])
            self.assertEqual(result['findings'],old['findings'])
            self.assertEqual(result['reused'],[])
            self.assertEqual(set(result['refreshed']),{'main.o','helper.o'})
class StudentE9A241880617(unittest.TestCase):
    def test_helper_include_adds_target_specific_md(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            old=scan(p)
            (p/'helper.c').write_text('#include "extra.h"\n'+(p/'helper.c').read_text())
            commit(p,'student: helper includes extra')
            result=scan(p,old)
            self.assertEqual(set(result['refreshed']),{'main.o','helper.o'})
            self.assertEqual(result['actual']['helper.o'],['extra.h','helper.c'])
            self.assertIn(['MISSING','helper.o','extra.h'],result['added'])
            self.assertEqual(result['actual']['main.o'],old['actual']['main.o'])
class StudentE10A241880617(unittest.TestCase):
    def test_remove_redundant_declaration_clears_rd(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sample'
            fixture(p)
            old=scan(p)
            f=p/'Makefile'
            f.write_text(f.read_text().replace('main.c unused.h','main.c'))
            commit(p,'student: drop redundant declaration')
            result=scan(p,old)
            self.assertEqual(result['reused'],['main.o','helper.o'])
            self.assertEqual(result['refreshed'],[])
            self.assertEqual(result['declared']['main.o'],['main.c'])
            self.assertIn({'type':'MISSING','target':'main.o','dependency':'config.h'},result['findings'])
            self.assertNotIn({'type':'REDUNDANT','target':'main.o','dependency':'unused.h'},result['findings'])


class StudentE8Tests(unittest.TestCase):
    def test_transitive_header_invalidates_history(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)/'sample'
            fixture(project)
            previous=scan(project)
            (project/'config.h').write_text('#include "extra.h"\n#define VALUE 1\n')
            commit(project,'student: add transitive include')
            result=scan(project,previous)
            self.assertEqual(result['actual']['main.o'],['config.h','extra.h','main.c'])
            self.assertEqual(set(result['refreshed']),{'main.o','helper.o'})
            self.assertEqual(result['reused'],[])
            self.assertEqual(
                {(f['type'],f['target'],f['dependency']) for f in result['findings']},
                {('MISSING','main.o','config.h'),('MISSING','main.o','extra.h'),
                 ('REDUNDANT','main.o','unused.h')})
            self.assertEqual(result['actual'],scan(project)['actual'])


class StudentE9Tests(unittest.TestCase):
    def test_removed_include_resolves_missing_edge(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)/'sample'
            fixture(project)
            source=project/'main.c'
            original=source.read_text()
            source.write_text('#include "extra.h"\n'+original)
            commit(project,'student: add include')
            previous=scan(project)
            source.write_text(original)
            commit(project,'student: remove include')
            result=scan(project,previous)
            self.assertEqual(result['actual']['main.o'],['config.h','main.c'])
            self.assertEqual(result['resolved'],[['MISSING','main.o','extra.h']])
            self.assertEqual(set(result['refreshed']),{'main.o','helper.o'})
            self.assertEqual(result['findings'],scan(project)['findings'])


class StudentE10Tests(unittest.TestCase):
    def test_nested_include_incremental_equals_full(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)/'sample'
            fixture(project)
            previous=scan(project)
            (project/'config.h').write_text('#include "extra.h"\n#define VALUE 1\n')
            (project/'extra.h').write_text('#include "leaf.h"\n')
            (project/'leaf.h').write_text('#define LEAF 7\n')
            commit(project,'student: nested include')
            incremental=scan(project,previous)
            full=scan(project)
            self.assertEqual(incremental['actual']['main.o'],
                             ['config.h','extra.h','leaf.h','main.c'])
            self.assertEqual(
                {(f['type'],f['target'],f['dependency']) for f in incremental['findings']},
                {('MISSING','main.o','config.h'),('MISSING','main.o','extra.h'),
                 ('MISSING','main.o','leaf.h'),('REDUNDANT','main.o','unused.h')})
            for key in ['actual','declared','findings']:
                self.assertEqual(incremental[key],full[key])

if __name__=='__main__':unittest.main()
