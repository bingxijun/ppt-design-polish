"""Check analytical meaning, native output and offline visual defaults."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from visuals import normalise, resolve_chart, default_design, icon_name, prepare, ROOT
from visual_layouts import validate_diagram
from typography import TextMetrics
from compose import compose
from deck import init, build, verify_contract


def plan_with(values,labels=None):
    labels=labels or list('ABCDEFGH')[:len(values)]
    return {'design':{'palette':{'ink':'222222','accent':'A06920'}},'claims':
            {**{'n'+str(i):{'text':str(v)} for i,v in enumerate(values)},
             **{'l'+str(i):{'text':s} for i,s in enumerate(labels)}}}


def chart_slide(values,intent,labels=None):
    p=plan_with(values,labels)
    return p,{'chart':{'type':'auto','intent':intent,'series':[{'name':'sample','points':
        [{'label':'$l'+str(i),'value':'$n'+str(i)} for i in range(len(values))]}]}}


class VisualTests(unittest.TestCase):
    def test_pie_is_native_and_still_requires_a_reconciled_whole(self):
        p,s=chart_slide([50,30,20],'share');s['chart'].update(whole='All time',total='100',form='pie')
        self.assertEqual(resolve_chart(s,p)['form'],'pie')
        s['chart']['total']='90'
        with self.assertRaisesRegex(ValueError,'sum'):resolve_chart(s,p)

    def test_semantic_build_recompiles_changed_plan_and_applies_default_treatment(self):
        import shutil
        example=ROOT/'examples/visual-defaults'
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp)
            for name in ('plan.json','source.json'):shutil.copyfile(example/name,w/name)
            shutil.copytree(example/'inputs',w/'inputs');shutil.copytree(example/'assets',w/'assets')
            p=json.loads((w/'plan.json').read_text());p.pop('visual_defaults')
            # No design flag, fonts, recipe names or coordinates are needed.
            (w/'plan.json').write_text(json.dumps(p));init(w,9,'hybrid');build(w)
            brief=json.loads((w/'visual-brief.json').read_text())
            self.assertEqual(brief['profile'],'product-launch')
            self.assertEqual(len(brief['pages']),9)
            deck=json.loads((w/'deck.json').read_text())
            self.assertNotEqual(deck['slides'][0]['background'],deck['slides'][1]['background'])
            self.assertTrue(any(e['type']=='image' and 'f7f7f4' in e['path'] for e in deck['slides'][1]['elements']))
            # A real plan edit must change the exported chart without manual compose.
            p['slides'][3]['chart']['form']='pie';(w/'plan.json').write_text(json.dumps(p))
            result=build(w)
            with ZipFile(w/result['artifact']) as z:
                self.assertTrue(any(b'<c:pieChart>' in z.read(n) for n in z.namelist() if n.startswith('ppt/charts/') and n.endswith('.xml')))
            self.assertTrue(verify_contract(w,w/result['artifact'])['ok'])
            p['visual_defaults']={'profile':'classic'};(w/'plan.json').write_text(json.dumps(p));prepare(w)
            self.assertFalse((w/'visual-brief.json').exists())

    def test_display_wrapping_keeps_chinese_word_boundaries(self):
        with TextMetrics() as m:
            r=m.wrap('一半使用时长发生在家庭书桌','Songti SC',34,3.72)
            self.assertNotIn('发',[line[-1:] for line in r['lines'][:-1]])
            self.assertEqual(''.join(r['lines']),'一半使用时长发生在家庭书桌')

    def test_ranking_sort_preserves_labels_values_and_focus_identity(self):
        p,s=chart_slide([12,40,25],'ranking');s['chart']['focus_points']=[0]
        decision=resolve_chart(s,p);points=s['chart']['series'][0]['points']
        self.assertEqual([p['claims'][x['label'][1:]]['text'] for x in points],['B','C','A'])
        self.assertEqual(s['chart']['focus_points'],[2]);self.assertEqual(decision['form'],'bar')

    def test_trend_keeps_chronology_instead_of_sorting_by_magnitude(self):
        p,s=chart_slide([12,4,25],'trend',['Jan','Feb','Mar'])
        before=copy.deepcopy(s['chart']['series']);resolve_chart(s,p)
        self.assertEqual(s['chart']['series'],before);self.assertEqual(s['chart']['type'],'line')

    def test_share_requires_a_named_whole_and_reconciled_total(self):
        p,s=chart_slide([50,30,20],'share')
        with self.assertRaisesRegex(ValueError,'whole'):resolve_chart(s,p)
        s['chart']['whole']='All observed time';s['chart']['total']='110'
        with self.assertRaisesRegex(ValueError,'sum'):resolve_chart(s,p)
        s['chart']['total']='100';self.assertEqual(resolve_chart(s,p)['form'],'doughnut')
        p,s=chart_slide([20,20,20,20,10,10],'share');s['chart'].update(whole='All time',total='100')
        self.assertEqual(resolve_chart(s,p)['form'],'bar')

    def test_waterfall_rejects_an_unreconciled_story(self):
        p,s=chart_slide([100,-12,-8,5,85],'contribution');s['chart']['steps']=['total','delta','delta','delta','total']
        self.assertEqual(resolve_chart(s,p)['form'],'waterfall')
        p['claims']['n4']['text']='80'
        with self.assertRaisesRegex(ValueError,'reconcile'):resolve_chart(s,p)

    def test_paired_comparison_rejects_mismatched_tasks(self):
        p,s=chart_slide([3,4],'paired');s['chart']['series'].append(copy.deepcopy(s['chart']['series'][0]))
        s['chart']['series'][1]['points'].reverse()
        with self.assertRaisesRegex(ValueError,'categories'):resolve_chart(s,p)

    def test_negative_bars_keep_negative_observations_in_scale(self):
        p,s=chart_slide([-5,20],'ranking');resolve_chart(s,p)
        self.assertLessEqual(s['chart']['min'],-5)

    def test_scales_and_center_readouts_cannot_misrepresent_observations(self):
        p,s=chart_slide([20,40],'ranking');s['chart']['min']=30
        with self.assertRaisesRegex(ValueError,'clips'):resolve_chart(s,p)
        p,s=chart_slide([50,30,20],'share');s['chart'].update(whole='All time',total='100',center='60%')
        with self.assertRaisesRegex(ValueError,'Center readout'):resolve_chart(s,p)

    def test_dark_default_gets_readable_ink_and_explicit_low_contrast_stops(self):
        d=default_design({'background':'151A18'},'en-US',['Arial'])
        self.assertEqual(d['palette']['ink'],'F4F5F2')
        with self.assertRaisesRegex(ValueError,'contrast'):default_design({'background':'FFFFFF','ink':'EEEEEE'},'en-US',['Arial'])

    def test_font_defaults_use_available_families_and_respect_language(self):
        d=default_design({'tone':'editorial'},'zh-CN',['Noto Sans CJK SC','Noto Serif CJK SC','Liberation Sans'])
        self.assertEqual(d['typography']['headingFont'],'Noto Serif CJK SC')
        self.assertEqual(d['typography']['bodyFont'],'Noto Sans CJK SC')
        self.assertIsNone(d['font_warning'])
        self.assertIsNotNone(default_design({},'zh-CN',['Liberation Sans'])['font_warning'])

    def test_icons_follow_meaning_and_allow_deliberate_omission(self):
        p={'claims':{'a':{'text':'环境感知'},'b':{'text':'未分类叙述'}}}
        self.assertEqual(icon_name({'title':'$a'},p),'radio')
        self.assertIsNone(icon_name({'title':'$b'},p))
        self.assertIsNone(icon_name({'title':'$a','icon':False},p))
        with self.assertRaises(ValueError):icon_name({'icon':'made-up'},p)
        self.assertIsNone(icon_name({'title':'Flight preview'},p))

    def test_japanese_korean_and_traditional_chinese_fonts_follow_locale(self):
        for locale,font in [('ja-JP','Noto Sans CJK JP'),('ko-KR','Noto Sans CJK KR'),('zh-TW','Noto Sans CJK TC')]:
            d=default_design({},locale,['Arial','Noto Sans CJK SC',font])
            self.assertEqual(d['typography']['bodyFont'],font)

    def test_real_product_request_cannot_generate_a_lookalike(self):
        from visuals import image_request
        p={'design':{'palette':{'background':'FFFFFF','ink':'222222','accent':'A06920'}}}
        with self.assertRaisesRegex(ValueError,'Real product'):
            image_request({'illustration':{'asset':'hero','subject':'Named real product','purpose':'Identity','identity':'real','mode':'generate'}},p,{})

    def test_tree_rejects_cycles_and_missing_parent(self):
        for nodes in ([{'id':'r','title':'root'},{'id':'a','title':'A','parent':'b'},{'id':'b','title':'B','parent':'a'}],
                      [{'id':'r','title':'root'},{'id':'a','title':'A','parent':'missing'}]):
            with self.assertRaises(ValueError):validate_diagram({'form':'hierarchy','nodes':nodes})
        nodes=[{'id':'r','title':'root'},{'id':'a','title':'A','parent':'r'}]
        self.assertEqual(len(validate_diagram({'form':'hierarchy','nodes':nodes})[1]),2)

    def test_last_line_balancing_keeps_text_and_number_unit(self):
        with TextMetrics() as m:
            a=m.wrap('Measured output remains at 620 km under the stated operating conditions.', 'Arial',20,3.2,balance_last_line=True)
            self.assertIn('620 km','\n'.join(a['lines']))
            self.assertEqual(' '.join(' '.join(a['lines']).split()),'Measured output remains at 620 km under the stated operating conditions.')

    def test_offline_icons_and_native_chart_export(self):
        # Rebuild from the high-level public plan, with no source coordinates or font names.
        import shutil
        example=ROOT/'examples/visual-defaults'
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp)
            for name in ('plan.json','source.json'):shutil.copyfile(example/name,w/name)
            shutil.copytree(example/'inputs',w/'inputs');shutil.copytree(example/'assets',w/'assets')
            result=prepare(w);self.assertGreaterEqual(result['icons'],4)
            self.assertEqual(result['image_requests'],2)
            p=json.loads((w/'plan.json').read_text())
            self.assertNotIn('design',p)
            self.assertTrue(all('frames' not in s for s in p['slides']))
            count=compose(w)['slides'];init(w,count,'hybrid');artifact=w/build(w)['artifact']
            self.assertTrue(verify_contract(w,artifact)['ok'])
            with ZipFile(artifact) as z:
                charts=[n for n in z.namelist() if n.startswith('ppt/charts/chart') and n.endswith('.xml')]
                self.assertEqual(len(charts),3)
                self.assertTrue(any(b'doughnutChart' in z.read(n) for n in charts))
                ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
                for page in (6,7):
                    xml=ET.fromstring(z.read(f'ppt/slides/slide{page}.xml'))
                    self.assertGreater(len(xml.findall('.//p:sp',ns)),10)
                    self.assertEqual(len(xml.findall('.//p:pic',ns)),0)
            self.assertTrue((w/'assets/icons/radio-202623.png').read_bytes().startswith(b'\x89PNG'))


if __name__=='__main__':unittest.main()
