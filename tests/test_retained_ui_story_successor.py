from pathlib import Path
import copy,os,re,sys,tempfile,unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent if HERE.name=='tests' else HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/'tests')]
import retained_ui_successor as base
import retained_ui_story_successor as story
CONTRACT=HERE/'combined-story-contract.json' if HERE.name!='tests' else ROOT/'docs/journey-guidance/retained-ui-story-contract.json'
PARENT=ROOT/'docs/journey-guidance/retained-ui-contract.json'

class StoryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=base.load_contract(PARENT);cls.contract=story.load_contract(CONTRACT)
        cls.state=story.load_state(ROOT,cls.parent,cls.contract)
    def rejects(self,mutator):
        state=copy.deepcopy(self.state);mutator(state)
        with self.assertRaises(base.Rejected):story.verify_state(state,self.parent,self.contract)
    def pixel(self,state,key):
        for path,text in state['files'].items():
            for statement,name,_ in base.RASTER.findall(text):
                if name==key:
                    new=re.sub(r'\{(\d+),(\d+),(\d+)\}',lambda m:'{%d,%s,%s}'%(int(m[1])+1,m[2],m[3]),statement,count=1)
                    state['files'][path]=text.replace(statement,new,1);return
        self.fail('missing raster '+key)
    def test_exact_combined_positive_and_parent_stays_pinned(self):
        view=story.verify_state(self.state,self.parent,self.contract)
        self.assertEqual(view.proof['total_changed_existing_texts'],8)
        self.assertEqual(view.proof['total_changed_existing_raster_statements'],16)
        self.assertEqual(view.proof['appended_texts'],105)
        self.assertEqual(view.metadata('assets/ui_texts.json')['C_ELDER_ACT1_0_0'],self.contract['changed_texts']['C_ELDER_ACT1_0_0']['g4'])
        self.assertEqual(base.digest(PARENT.read_bytes()),base.CONTRACT_SHA256)
    def test_defaults_are_raw_and_g4_only_still_rejects(self):
        self.assertIsNone(story.read_view(ROOT).proof)
        self.assertEqual(story.read_view(ROOT).metadata('assets/ui_texts.json')['C_ELDER_ACT1_0_0'],self.contract['changed_texts']['C_ELDER_ACT1_0_0']['g5'])
        with self.assertRaises(base.Rejected):base.verify_state(self.state,self.parent)
    def test_wrong_story_values_each(self):
        for key in story.ALLOWED:
            self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__(key,'Other'))
    def test_stale_generated_metadata_each(self):
        for key in story.ALLOWED:
            self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__(key,self.contract['changed_texts'][key]['g4']))
    def test_missing_story_metadata(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].pop('C_ELDER_ACT1_0_1'))
    def test_unrelated_old_metadata(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__('E_YIN','陽'))
    def test_extra_old_metadata(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__('UNAPPROVED','Other'))
    def test_wrong_parent_six_key_value(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__('THANKS','Other'))
    def test_changed_added_journey_label(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts_journey_guidance.json'].__setitem__('JG_BEGIN','Other'))
    def test_extra_authoring_override(self):
        self.rejects(lambda s:s['metadata']['assets/journey_guidance_ui.json'].__setitem__('E_YIN','Other'))
    def test_elder_authoring_wrong_value(self):
        self.rejects(lambda s:s['story_authoring']['dialogue']['ELDER_ACT1']['pages'][0].__setitem__(0,'Other'))
    def test_unrelated_npc_authoring(self):
        self.rejects(lambda s:s['story_authoring']['dialogue']['ACT1_OPEN']['pages'][0].__setitem__(0,'Other'))
    def test_elder_topology_change(self):
        self.rejects(lambda s:s['story_authoring']['dialogue']['ELDER_ACT1']['pages'].append(['Extra','Extra']))
    def test_each_story_raster_shift(self):
        for key in self.contract['changed_rasters']:self.rejects(lambda s:self.pixel(s,key))
    def test_old_raster_shift(self):self.rejects(lambda s:self.pixel(s,'txt_E_YIN_0'))
    def test_parent_replacement_raster_shift(self):self.rejects(lambda s:self.pixel(s,'txt_THANKS_0'))
    def test_journey_raster_shift(self):self.rejects(lambda s:self.pixel(s,'txt_JG_BEGIN_0'))
    def test_missing_or_duplicate_story_raster(self):
        row=next(iter(self.contract['changed_rasters'].values()))
        def edit(s,duplicate):
            path=row['path'];matches=[x[0]for x in base.RASTER.findall(s['files'][path])if x[2]==row['key']]
            s['files'][path]=s['files'][path].replace(matches[0],matches[0]*2 if duplicate else'',1)
        for duplicate in (False,True):self.rejects(lambda s:edit(s,duplicate))
    def test_story_table_width_or_pointer_change(self):
        row=next(iter(self.contract['changed_table_rows'].values()))
        self.rejects(lambda s:s['files'].__setitem__(row['path'],s['files'][row['path']].replace(row['after_statement'],row['before_statement'],1)))
    def test_enum_shift(self):self.rejects(lambda s:s['files'].__setitem__('src/ui.h',s['files']['src/ui.h'].replace('enum {','enum { TX_EXTRA,',1)))
    def test_include_drift(self):self.rejects(lambda s:s['files'].__setitem__('src/ui.c',s['files']['src/ui.c']+'\n'))
    def test_historical_hash_drift(self):self.rejects(lambda s:s['historical'].__setitem__(next(iter(s['historical'])),'0'*64))
    def test_modified_story_contract(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'contract.json';p.write_bytes(CONTRACT.read_bytes()+b' ')
            with self.assertRaises(base.Rejected):story.load_contract(p)
    def test_modified_parent_contract(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'contract.json';p.write_bytes(PARENT.read_bytes()+b' ')
            with self.assertRaises(base.Rejected):story.read_view(ROOT,successor=True,contract_path=CONTRACT,parent_contract_path=p)
    def test_flags_explicit_and_conflicts_rejected(self):
        a=['test'];self.assertFalse(story.consume_story_flag(a));self.assertEqual(a,['test'])
        a=['test',story.FLAG];self.assertTrue(story.consume_story_flag(a));self.assertEqual(a,['test'])
        for a in [['test',story.FLAG,story.FLAG],['test',story.FLAG,'--journey-ui-successor']]:
            with self.assertRaises(base.Rejected):story.consume_story_flag(a)
    def test_normalization_is_pure(self):
        before=copy.deepcopy(self.state);view=story.verify_state(self.state,self.parent,self.contract)
        self.assertEqual(self.state,before);values=view.metadata('assets/ui_texts.json');values['E_YIN']='Other'
        self.assertEqual(view.metadata('assets/ui_texts.json')['E_YIN'],'陰')

if __name__=='__main__':unittest.main(verbosity=2)
