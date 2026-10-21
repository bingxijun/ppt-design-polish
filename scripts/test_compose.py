"""Test source accountability, real pagination and reusable layout behaviour."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from compose import prepare, validate, paginate, choose_layout, compose, write
from deck import snapshot, init


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.w = Path(self.tmp.name)/'work'
        src = Path(self.tmp.name)/'notice.md'
        src.write_text('# Launch\n\nRange is 620 km.\n\nOrders open in May.\n', encoding='utf-8')
        self.source = prepare(src, self.w)
        self.plan = {'source_sha256': self.source['sha256'], 'kind': 'product-launch',
                     'claims': {
                         'range': {'text': '620', 'evidence': [{'unit': 'p002', 'quote': 'Range is 620 km.'}]},
                         'title': {'text': 'Range', 'evidence': [{'unit': 'p002', 'quote': 'Range is 620 km.'}]},
                         'orders': {'text': 'Orders open in May.', 'evidence': [{'unit': 'p003', 'quote': 'Orders open in May.'}]}},
                     'slides': [{'role': 'content', 'title': '$title', 'metric': '$range', 'body': '$orders'}]}

    def test_exact_evidence_and_all_source_units_accounted(self):
        result = validate(self.plan, self.source, self.w)
        self.assertEqual(result['covered_units'], ['p002', 'p003'])

    def test_unsupported_number_rejected(self):
        self.plan['claims']['range']['text'] = '820'
        with self.assertRaisesRegex(ValueError, 'number'): validate(self.plan, self.source, self.w)

    def test_fabricated_quote_rejected(self):
        self.plan['claims']['range']['evidence'][0]['quote'] = 'Range is 820 km.'
        with self.assertRaisesRegex(ValueError, 'exact quote'): validate(self.plan, self.source, self.w)

    def test_unused_claim_cannot_hide_omission(self):
        del self.plan['slides'][0]['body']
        self.plan['unpresented_claims'] = {'orders': 'User excludes availability'}
        with self.assertRaisesRegex(ValueError, 'Unaccounted'): validate(self.plan, self.source, self.w)
        self.plan['omitted'] = [{'unit': 'p003', 'reason': 'Explicit user request excludes availability'}]
        self.assertEqual(len(validate(self.plan, self.source, self.w)['omitted']), 1)

    def test_source_edit_invalidates_plan(self):
        (self.w/'inputs/announcement.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'changed'): validate(self.plan, self.source, self.w)

    def test_duplicate_omission_rejected(self):
        del self.plan['slides'][0]['body']
        self.plan['unpresented_claims'] = {'orders': 'User excludes availability'}
        self.plan['omitted'] = [{'unit': 'p003', 'reason': 'duplicate'}]*2
        with self.assertRaises(ValueError): validate(self.plan, self.source, self.w)

    def test_content_selects_layout(self):
        self.assertEqual(choose_layout({'chart': {}}), 'text')
        self.assertEqual(choose_layout({'chart': {'series': []}}), 'chart')
        self.assertEqual(choose_layout({'events': [1]}), 'timeline')
        self.assertEqual(choose_layout({'image': 'product', 'metrics': [1]}), 'overview')

    def test_overfull_items_split_without_loss(self):
        slides = [{'title': '$title', 'image': 'asset', 'items': ['$orders']*7}]
        pages = paginate(slides, self.plan)
        self.assertEqual(len(pages), 3)
        self.assertEqual([i for p in pages for i in p['items']], ['$orders']*7)
        fixed = {**self.plan, 'slide_count': 1}
        with self.assertRaisesRegex(ValueError, 'Content needs'): paginate(slides, fixed)

    def test_composes_native_objects_and_defaults(self):
        write(self.w/'plan.json', self.plan)
        result = compose(self.w)
        self.assertEqual(result['style'], 'teal-launch')
        deck = json.loads((self.w/'deck.json').read_text())
        self.assertTrue(all(e['type'] in ('text', 'shape') for e in deck['slides'][0]['elements']))
        self.assertIn('620', [e.get('text') for e in deck['slides'][0]['elements']])
        self.plan['kind'] = 'business'; write(self.w/'plan.json', self.plan)
        self.assertEqual(compose(self.w)['style'], 'editorial-yellow')

    def test_plan_edit_invalidates_delivery_snapshot(self):
        write(self.w/'plan.json', self.plan)
        before = snapshot(self.w)
        self.plan['style'] = 'editorial-yellow'; write(self.w/'plan.json', self.plan)
        self.assertNotEqual(before, snapshot(self.w))

    def test_initialization_keeps_composed_content_contract(self):
        write(self.w/'plan.json', self.plan)
        compose(self.w)
        contract = (self.w/'contract.json').read_bytes()
        init(self.w, 1, 'hybrid')
        self.assertEqual((self.w/'contract.json').read_bytes(), contract)


if __name__ == '__main__': unittest.main()
