"""Check exported native objects, emphasis and paragraph geometry in actual OOXML."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from compose import Composer
from deck import node_run
from typography import TextMetrics

NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}

class NativeEditorialTests(unittest.TestCase):
    def test_export_keeps_column_widths_alignment_focus_and_measured_leading(self):
        with tempfile.TemporaryDirectory() as tmp, TextMetrics() as metrics:
            root=Path(tmp)
            plan={'style':'editorial-yellow','language':'en-US',
                  'fonts':{'headingFont':'Arial','bodyFont':'Arial','latinFont':'Arial'},
                  'claims':{k:{'text':v} for k,v in {'t':'Measured comparison','h0':'Metric','h1':'Value',
                   'a':'A longer description','n':'620','b':'510'}.items()}}
            c=Composer(plan,root,metrics)
            c.render({'layout':'freeform','title':'$t','design_reason':'Table widths and a separate factual headline',
              'rows':[['$h0','$h1'],['$a','$n']],'table':{'column_widths':[3,1]},
              'frames':[{'kind':'text','claim':'$t','x':.7,'y':1,'w':10,'h':.7,'size':30},
                        {'kind':'table','x':.7,'y':2.5,'w':10,'h':3}]},1)
            c.render({'layout':'chart','title':'$t','chart':{'series':[{'name':'Range','points':[
               {'label':'A','value':'$n'},{'label':'B','value':'$b'}]}],
               'focus_points':[0],'focus_reason':'The larger value is the comparison focus.'}},2)
            (root/'deck.json').write_text(json.dumps({'slides':c.slides}))
            node_run('build_deck.mjs',root/'deck.json',root/'test.pptx')
            with ZipFile(root/'test.pptx') as z:
                page=ET.fromstring(z.read('ppt/slides/slide1.xml'))
                cols=[int(e.get('w')) for e in page.findall('.//a:tblGrid/a:gridCol',NS)]
                self.assertEqual(cols,[6858000,2286000])
                data=page.findall('.//a:tbl/a:tr',NS)[1].findall('a:tc',NS)
                self.assertEqual(data[1].find('.//a:pPr',NS).get('algn'),'r')
                fills=[e.get('val') for e in page.findall('.//a:tcPr/a:solidFill/a:srgbClr',NS)]
                self.assertEqual(set(fills),{'FFFFFF'})
                self.assertTrue(page.findall('.//a:lnSpc/a:spcPts',NS))
                chart=ET.fromstring(z.read('ppt/charts/chart1.xml'))
                colors=[e.get('val') for e in chart.findall('.//c:dPt/c:spPr/a:solidFill/a:srgbClr',NS)]
                self.assertEqual(colors,['C69300','252621'])

    def test_invalid_custom_geometry_and_emphasis_cannot_silently_export(self):
        with tempfile.TemporaryDirectory() as tmp,TextMetrics() as metrics:
            c=Composer({'style':'editorial-yellow','fonts':{'bodyFont':'Arial'},'claims':{}},Path(tmp),metrics)
            with self.assertRaisesRegex(ValueError,'outside'):
                c.freeform({'design_reason':'A note','frames':[{'kind':'text','x':12,'y':1,'w':3,'h':1}]},1)
            c.plan['claims']={'a':{'text':'Value'}}
            with self.assertRaisesRegex(ValueError,'outside'):
                c.table({'rows':[['$a'],['$a']],'table':{'emphasis_cells':[[9,0]],'emphasis_reason':'A result'}})

if __name__=='__main__':unittest.main()
