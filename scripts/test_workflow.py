#!/usr/bin/env python3
"""Behavioral tests for preservation and stale evidence; no aesthetic scoring."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from deck import init, adopt, snapshot, state, state_path, digest, write, review, finalize, verify_contract
from patch_template import patch
from reference_library import extract
from test_inspect_pptx import fixture, shape


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.w = self.base/'work'
        init(self.w, 2, 'native')
        self.source = self.base/'source.pptx'
        fixture(self.source, [shape('Keep this'), shape('中文')])
        with ZipFile(self.source, 'a') as z:
            z.writestr('customXml/opaque.bin', b'preserve unknown payload\x00\xff')
        write(self.w/'deck.json', {'source': 'test fixture'})
        adopt(self.w, self.source)

    def register_fixture_render(self):
        # Unit-level stand-ins for image files; actual rendering is tested separately.
        current = state(self.w)
        pages = {}
        for n in [1, 2]:
            path = self.w/f'.ppt-beautify/page-{n}.png'
            path.write_bytes(f'render-fixture-{n}'.encode())
            pages[str(path.relative_to(self.w))] = digest(path)
        current['render'] = {'artifact_sha256': current['build']['sha256'], 'inputs': snapshot(self.w),
                             'renderer': 'unit-fixture', 'pages': pages}
        write(state_path(self.w), current)

    def pass_reviews(self, scopes=(1, 2, 'deck')):
        review(self.w, [{'slide': n, 'verdict': 'pass', 'summary': 'Fixture assertion only', 'issues': []} for n in scopes])

    def test_init_preserves_existing_workspace(self):
        before = (self.w/'task.json').read_bytes()
        with self.assertRaises(ValueError): init(self.w, 10, 'image')
        self.assertEqual(before, (self.w/'task.json').read_bytes())

    def test_no_reviews_no_delivery(self):
        self.assertFalse(finalize(self.w)['complete'])
        self.assertFalse((self.w/'output').exists())

    def test_review_requires_current_final_render(self):
        with self.assertRaises(ValueError): self.pass_reviews()

    def test_review_major_issue_cannot_be_marked_pass(self):
        self.register_fixture_render()
        with self.assertRaises(ValueError):
            review(self.w, [{'slide': 1, 'verdict': 'pass', 'summary': 'Invalid', 'issues': [
                {'slide': 1, 'severity': 'major', 'description': 'Clipped', 'suggested_fix': 'Resize'}]}])

    def test_missing_page_or_deck_review_blocks_delivery(self):
        self.register_fixture_render();self.pass_reviews(scopes=(1, 'deck'))
        self.assertFalse(finalize(self.w)['complete'])

    def test_successful_gate_copies_exact_artifact(self):
        self.register_fixture_render();self.pass_reviews()
        result = finalize(self.w)
        self.assertTrue(result['complete'])
        self.assertEqual(digest(result['output']), digest(self.source))

    def test_requested_pdf_requires_matching_pdf_render(self):
        payload = json.loads((self.w/'task.json').read_text())
        payload['outputs'] = ['pptx', 'pdf']
        write(self.w/'task.json', payload)
        adopt(self.w, self.source)
        self.register_fixture_render();self.pass_reviews()
        result = finalize(self.w)
        self.assertFalse(result['complete'])
        self.assertFalse(result['checks']['requested_formats'])

    def test_source_change_invalidates_review(self):
        self.register_fixture_render();self.pass_reviews()
        write(self.w/'deck.json', {'source': 'changed'})
        result = finalize(self.w)
        self.assertFalse(result['complete'])
        self.assertFalse(result['checks']['build_current'])

    def test_render_change_invalidates_review(self):
        self.register_fixture_render();self.pass_reviews()
        (self.w/'.ppt-beautify/page-1.png').write_bytes(b'new render')
        self.assertFalse(finalize(self.w)['checks']['renders_current'])

    def test_artifact_change_invalidates_review(self):
        self.register_fixture_render();self.pass_reviews()
        with ZipFile(self.w/'.ppt-beautify/draft.pptx', 'a') as z:
            z.writestr('customXml/new.xml', '<new/>')
        self.assertFalse(finalize(self.w)['checks']['build_current'])

    def test_text_and_native_object_contract_blocks_loss(self):
        write(self.w/'contract.json', {'required_text': {'1': ['Missing fact']},
                                      'min_objects': {'2': {'native_charts': 1}}})
        result = verify_contract(self.w, self.source)
        self.assertFalse(result['ok'])
        self.assertEqual(len(result['errors']), 2)

    def test_source_preservation_detects_loss(self):
        changed = self.base/'changed.pptx'
        patch(self.source, [{'slide': 1, 'old': 'Keep this', 'new': 'Lost fact'}], changed)
        preserved = self.w/'inputs/source.pptx'
        preserved.write_bytes(self.source.read_bytes())
        write(self.w/'contract.json', {'preserve_from': 'inputs/source.pptx'})
        self.assertFalse(verify_contract(self.w, changed)['ok'])

    def test_patch_keeps_unmodified_payloads_and_source(self):
        result = self.base/'patched.pptx'
        before = digest(self.source)
        patch(self.source, [{'slide': 2, 'old': '中文', 'new': '新内容'}], result)
        with ZipFile(self.source) as old, ZipFile(result) as new:
            for name in old.namelist():
                if name != 'ppt/slides/slide2.xml': self.assertEqual(old.read(name), new.read(name))
            self.assertIn('新内容', new.read('ppt/slides/slide2.xml').decode())
        self.assertEqual(before, digest(self.source))

    def test_ambiguous_patch_does_not_write_output(self):
        source = self.base/'duplicate.pptx'
        fixture(source, [shape('duplicate') + shape('duplicate')])
        output = self.base/'bad.pptx'
        with self.assertRaises(ValueError): patch(source, [{'slide':1, 'old':'duplicate', 'new':'new'}], output)
        self.assertFalse(output.exists())

    def test_reference_extraction_preserves_media(self):
        with ZipFile(self.source, 'a') as z: z.writestr('ppt/media/image1.png', b'original media')
        output = self.base/'reference'
        extract(self.source, output)
        self.assertEqual((output/'assets/image1.png').read_bytes(), b'original media')
        self.assertEqual(json.loads((output/'reference.json').read_text())['source_sha256'], digest(self.source))


if __name__ == '__main__': unittest.main()
