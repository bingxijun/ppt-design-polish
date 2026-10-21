import unittest
from editorial import design_tokens, flow_items, table_geometry, audit
from typography import TextMetrics


class EditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.metrics=TextMetrics()
    @classmethod
    def tearDownClass(cls):cls.metrics.close()

    def test_auto_does_not_guess_style_from_industry(self):
        with self.assertRaisesRegex(ValueError,'Auto design'):
            design_tokens({'kind':'product-launch'}, {})
        design={'basis':'Supplied brand guide','palette':{'background':'FFFFFF','paper':'FFFFFF',
                'ink':'202020','muted':'666666','rule':'DDDDDD','accent':'C05020'},
                'typography':{'headingFont':'Arial','bodyFont':'Arial','latinFont':'Arial'}}
        a=design_tokens({'kind':'product-launch','design':design},{})
        b=design_tokens({'kind':'business','design':design},{})
        self.assertEqual(a,b)

    def test_font_measurement_distinguishes_wide_and_narrow_latin(self):
        self.assertGreater(self.metrics.width('WWWW','Arial',20),self.metrics.width('iiii','Arial',20)*2)

    def test_wrap_keeps_number_and_unit_together(self):
        result=self.metrics.wrap('Nominal range 620 km for this version','Arial',18,2.3)
        self.assertIn('620 km','\n'.join(result['lines']))
        self.assertTrue(all(w<=2.3*72*1.04 for w in result['widths']))

    def test_measured_flow_is_not_equal_height_distribution(self):
        content={'short':'One sentence.','long':'A much longer explanation with the qualifying conditions kept beside the result. '*3}
        items=[{'body':'short'},{'body':'long'}]
        blocks=flow_items(items,lambda k:content[k],self.metrics,'Arial',5,6)
        self.assertGreater(blocks[1]['parts'][0]['h'],blocks[0]['parts'][0]['h'])
        self.assertLess(blocks[1]['y'],1)

    def test_emphasis_requires_reason(self):
        with self.assertRaisesRegex(ValueError,'reason'):
            flow_items([{'body':'a','priority':'primary'}],lambda _: 'Fact',self.metrics,'Arial',5,4)

    def test_table_widths_follow_content_and_numeric_alignment(self):
        rows=[['Measurement and operating conditions','A','B'],['Nominal range under stated conditions','510','620']]
        widths,heights,aligns=table_geometry(rows,{},self.metrics,'Arial',17,12,4)
        self.assertGreater(widths[0],widths[1])
        self.assertEqual(aligns,['left','right','right'])
        self.assertAlmostEqual(sum(widths),12)

    def test_explicit_equal_alternatives_are_supported(self):
        rows=[['A','B'],['First alternative','Second alternative']]
        widths,_,_=table_geometry(rows,{'column_widths':[1,1]},self.metrics,'Arial',17,12,4)
        self.assertEqual(widths,[6,6])

    def test_table_overflow_is_reported_without_shrinking(self):
        rows=[['Label','Value']]+[['A long explanation '*20,'620']]*8
        with self.assertRaisesRegex(ValueError,'exceeds'):
            table_geometry(rows,{},self.metrics,'Arial',18,8,2)

    def test_audit_reports_patterns_not_authorship(self):
        plan={'claims':{},'slides':[]}
        for i in range(4):
            plan['claims'][str(i)]={'text':'Generic phrase, generic outcome'}
            plan['slides'].append({'title':'$'+str(i),'kicker':'SECTION'})
        result=audit(plan,{'slides':[]},[{'layout':'text','slide':i+1} for i in range(4)])
        self.assertTrue(result['findings'])
        self.assertNotIn('score',result)
        self.assertNotIn('ai_probability',result)


if __name__=='__main__':unittest.main()
