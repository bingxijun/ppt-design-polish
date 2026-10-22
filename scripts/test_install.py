import tempfile
from pathlib import Path
import unittest
from install import install, NAME


class InstallTests(unittest.TestCase):
    def test_copy_is_self_contained_and_collision_preserves_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp)/'skills'
            target, backup = install('codex', skills_dir)
            self.assertIsNone(backup)
            for relative in ('SKILL.md', 'scripts/deck.py', 'references/workflow.md',
                             'LICENSE', 'licenses/PPTAgent.txt', 'licenses/Lucide.txt', 'assets/icons/radio.svg', 'package.json'):
                self.assertTrue((target/relative).is_file(), relative)
            (target/'local-note.txt').write_text('keep me')
            with self.assertRaises(ValueError):
                install('codex', skills_dir)
            self.assertEqual((target/'local-note.txt').read_text(), 'keep me')

    def test_update_retains_full_previous_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp)/'skills'
            target, _ = install('claude', skills_dir)
            (target/'local-note.txt').write_text('old installation')
            updated, backup = install('claude', skills_dir, update=True)
            self.assertEqual(updated, target)
            self.assertNotIn(skills_dir, backup.parents)
            self.assertEqual((backup/'local-note.txt').read_text(), 'old installation')
            self.assertFalse((updated/'local-note.txt').exists())

    def test_update_refuses_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp)/'skills'
            target = skills_dir/NAME
            target.mkdir(parents=True)
            (target/'SKILL.md').write_text('Unrelated content')
            with self.assertRaises(ValueError):
                install('codex', skills_dir, update=True)
            self.assertEqual((target/'SKILL.md').read_text(), 'Unrelated content')


if __name__ == '__main__':
    unittest.main()
