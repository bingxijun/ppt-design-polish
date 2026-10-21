"""Evidence workflow invariants using explicit unit-level render stand-ins."""
import csv
from pathlib import Path
import tempfile
import unittest
from deck import init,adopt,write,read,state,state_path,snapshot,digest,review,finalize
from test_inspect_pptx import fixture,shape
from studio import begin,register,select,critique,resolve,status,export_evidence,evidence_ok,STORE
from blind_review import prepare,summarize,FIELDS

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.w=self.root/'final';self.setup_work(self.w,'final')
        begin(self.w,{'audience':'Exhibition committee','viewing':'Readable PDF','visual_goal':'An editorial proposal with a readable programme',
                      'proofs':[{'id':'body','job':'Read the exhibition premise'}],'max_revision_rounds':2})
        self.setup_build(self.w,'final')
        self.a=self.root/'a';self.b=self.root/'b';self.setup_work(self.a,'a');self.setup_work(self.b,'b')

    def setup_work(self,w,label):
        init(w,1,'native');write(w/'contract.json',{'required_text':{'1':['Grounded content']}})
        self.setup_build(w,label)

    def setup_build(self,w,label):
        source=self.root/(w.name+'-source.pptx');fixture(source,[shape('Grounded content')]);adopt(w,source)
        img=w/'.ppt-beautify/page-1.png';img.write_bytes(('UNIT RENDER STAND-IN '+label).encode())
        s=state(w);s['render']={'artifact_sha256':s['build']['sha256'],'inputs':snapshot(w),'renderer':'unit-fixture','pages':{str(img.relative_to(w)):digest(img)}};write(state_path(w),s)
        review(w,[{'slide':i,'verdict':'pass','summary':'Unit fixture only','issues':[]} for i in (1,'deck')])

    def register_pair(self):
        register(self.w,'body','a',self.a,1);register(self.w,'body','b',self.b,1)

    def choice(self):return {'group':'body','selected':'b','reason':'The paragraph has a clearer reading path',
      'observations':[{'candidate':'a','strength':'Aligned','weakness':'Too many labels'},
                      {'candidate':'b','strength':'Direct reading','weakness':'Requires shorter copy'}]}

    def test_single_candidate_and_missing_observations_are_rejected(self):
        register(self.w,'body','a',self.a,1)
        with self.assertRaisesRegex(ValueError,'two'):select(self.w,self.choice())
        register(self.w,'body','b',self.b,1);c=self.choice();c['observations'].pop()
        with self.assertRaisesRegex(ValueError,'every'):select(self.w,c)

    def test_changed_raw_source_cannot_be_a_fair_candidate(self):
        (self.a/'inputs/extra.txt').write_text('More convenient material')
        with self.assertRaisesRegex(ValueError,'inputs'):register(self.w,'body','a',self.a,1)

    def test_frozen_candidate_tampering_invalidates_selection(self):
        self.register_pair();select(self.w,self.choice())
        p=self.w/STORE/'candidates/body/b/page-01.png';p.write_bytes(b'changed')
        self.assertFalse(status(self.w)['ready'])
        with self.assertRaisesRegex(ValueError,'stale'):select(self.w,self.choice())

    def test_same_content_is_required_between_composition_variants(self):
        register(self.w,'body','a',self.a,1)
        write(self.b/'contract.json',{'required_text':{'1':['Grounded']}});self.setup_build(self.b,'b')
        with self.assertRaisesRegex(ValueError,'same page content'):register(self.w,'body','b',self.b,1)

    def test_clean_current_inspection_and_selection_allow_delivery(self):
        self.register_pair();select(self.w,self.choice())
        self.assertFalse(finalize(self.w)['complete'])
        critique(self.w,{'summary':'Read the entire actual page; no visible defects in this unit fixture','issues':[]})
        self.assertTrue(status(self.w)['ready']);self.assertTrue(finalize(self.w)['complete'])

    def test_fix_requires_new_export_and_changed_page_pixels(self):
        self.register_pair();select(self.w,self.choice())
        issue={'id':'body-gap','slide':1,'severity':'major','bbox':[.1,.2,.3,.2],
               'observation':'Paragraph collides with caption','action':'Increase the paragraph-caption gap'}
        critique(self.w,{'summary':'One observed issue','issues':[issue]})
        fix=[{'id':'body-gap','change':'Moved caption','verification':'No collision remains'}]
        with self.assertRaisesRegex(ValueError,'changed export'):resolve(self.w,fix)
        with self.assertRaisesRegex(ValueError,'must be fixed'):resolve(self.w,[{**fix[0],'outcome':'accepted'}])
        # Change a real PPTX part without changing the required text.
        from zipfile import ZipFile
        pptx=self.w/'.ppt-beautify/draft.pptx'
        with ZipFile(pptx,'a') as z:z.writestr('customXml/revision.xml','<revision/>')
        source=self.root/'revised.pptx';source.write_bytes(pptx.read_bytes());adopt(self.w,source)
        s=state(self.w);img=self.w/'.ppt-beautify/page-1.png';img.write_bytes(b'UNIT changed page pixels')
        s['render']={'artifact_sha256':s['build']['sha256'],'inputs':snapshot(self.w),'renderer':'unit-fixture',
                     'pages':{str(img.relative_to(self.w)):digest(img)}};write(state_path(self.w),s)
        resolve(self.w,fix);self.assertTrue(status(self.w)['ready'])
        img.write_bytes(b'Another unreviewed image');self.assertFalse(status(self.w)['ready'])

    def test_brief_change_invalidates_proofs_and_geometry_location_is_required(self):
        self.register_pair();select(self.w,self.choice())
        brief=read(self.w/'design-study.json');brief['viewing']='Projected keynote';write(self.w/'design-study.json',brief)
        self.assertFalse(status(self.w)['ready'])
        self.setup_build(self.w,'after brief change')
        with self.assertRaisesRegex(ValueError,'bbox'):critique(self.w,{'summary':'Found issue','issues':[
          {'id':'missing-box','slide':1,'severity':'major','observation':'Dense','action':'Reorganize'}]})

    def test_revision_budget_stops_unbounded_loop(self):
        for _ in range(2):critique(self.w,{'summary':'Unit fixture clean inspection','issues':[]})
        with self.assertRaisesRegex(ValueError,'budget'):critique(self.w,{'summary':'Again','issues':[]})

    def test_export_packet_is_portable_without_changing_workspace_state(self):
        self.register_pair();select(self.w,self.choice())
        critique(self.w,{'summary':'Current unit fixture is clean','issues':[]})
        before=(self.w/STORE/'index.json').read_bytes()
        output=self.root/'portable';export_evidence(self.w,output)
        index=read(output/'index.json');report=read(output/'report.json')
        self.assertTrue(evidence_ok(output,report['final']))
        self.assertTrue(evidence_ok(output,index['candidates']['body']['a']))
        self.assertEqual(before,(self.w/STORE/'index.json').read_bytes())
        self.assertTrue(status(self.w)['ready'])

    def test_clean_later_critique_does_not_erase_unresolved_issue(self):
        self.register_pair();select(self.w,self.choice())
        critique(self.w,{'summary':'Visible problem','issues':[{'id':'open-issue','slide':1,'severity':'major',
                  'bbox':[0,.1,.3,.3],'observation':'Text collides','action':'Move the text'}]})
        critique(self.w,{'summary':'Later clean inspection cannot close earlier work by omission','issues':[]})
        self.assertFalse(status(self.w)['ready'])
        self.assertTrue(any('open-issue' in p for p in status(self.w)['problems']))

    def test_selected_reference_can_use_one_actual_proof(self):
        c=read(self.w/'design-study.json');c['proofs'][0].update(mode='reference',reason='User selected this exact template')
        write(self.w/'design-study.json',c);self.setup_build(self.w,'adopted')
        register(self.w,'body','a',self.a,1)
        select(self.w,{'group':'body','selected':'a','reason':'Matches the selected reference on actual content',
             'observations':[{'candidate':'a','strength':'Reference identity retained','weakness':'Fixed brand typography limits long headlines'}]})
        critique(self.w,{'summary':'Actual approved-reference proof inspected','issues':[]})
        self.assertTrue(status(self.w)['ready'])

class BlindReviewTests(unittest.TestCase):
    def test_pending_is_not_counted_as_human_approval_and_votes_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp);(w/'a.png').write_bytes(b'unit image a');(w/'b.png').write_bytes(b'unit image b')
            pairs=[{'case':'body','task':'Committee reading a PDF: compare the programme explanation.',
                    'a':str(w/'a.png'),'b':str(w/'b.png'),'a_label':'baseline','b_label':'candidate'}]
            prepare(pairs,w/'pack',w/'key.json',seed=10)
            r=summarize(w/'pack',w/'pack/ratings.csv',w/'key.json')
            self.assertEqual(r['status'],'pending');self.assertEqual(r['decisions'],0)
            with (w/'votes.csv').open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerow(dict(zip(FIELDS,
                    ['body','reader-1','left','left','tie','right','unjudgeable','The caption is easier to find on the left.'])))
            r=summarize(w/'pack',w/'votes.csv',w/'key.json')
            expected=read(w/'key.json')['answers']['body']['left'];self.assertEqual(r['counts']['preference'][expected],1)
            self.assertEqual(r['reviewers'],1)
            (w/'pack/body-left.png').write_bytes(b'altered')
            with self.assertRaisesRegex(ValueError,'changed'):summarize(w/'pack',w/'votes.csv',w/'key.json')

    def test_answer_key_cannot_leak_into_reader_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Path(tmp)
            with self.assertRaisesRegex(ValueError,'outside'):prepare([],w/'pack',w/'pack/key.json')

if __name__=='__main__':unittest.main()
