from pathlib import Path
import copy,json,re,tempfile,unittest
import retained_ui_successor as adapter
import os,sys
import retained_ui_story_successor as story
_STORY=story.consume_story_flag(sys.argv)

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
CONTRACT=ROOT/'docs/journey-guidance/retained-ui-contract.json'

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=adapter.load_contract(CONTRACT)
        cls.state=adapter.load_state(ROOT,cls.contract)
        if _STORY:
            contract=story.load_contract(Path(os.environ.get('JOURNEY_STORY_UI_SUCCESSOR_CONTRACT',
                ROOT/'docs/journey-guidance/retained-ui-story-contract.json')))
            cls.state=story.normalize_to_g4(story.load_state(ROOT,cls.contract,contract),contract)
    def rejects(self,mutator):
        state=copy.deepcopy(self.state);mutator(state)
        with self.assertRaises(adapter.Rejected):adapter.verify_state(state,self.contract)
    def raster_edit(self,state,name,transform):
        for path,text in state['files'].items():
            for statement,found,key in adapter.RASTER.findall(text):
                if found==name:
                    state['files'][path]=text.replace(statement,transform(statement),1);return
        self.fail('test raster missing: '+name)
    def shift_pixel(self,statement):
        return re.sub(r'\{(\d+),(\d+),(\d+)\}',
            lambda m:'{%d,%s,%s}'%(int(m[1])+1,m[2],m[3]),statement,count=1)
    def test_exact_positive_and_default_is_raw(self):
        proof=adapter.verify_state(self.state,self.contract)
        self.assertEqual(proof.proof['unchanged_existing_raster_statements'],4154)
        raw=adapter.read_view(ROOT)
        self.assertIsNone(raw.proof)
        self.assertNotEqual(raw.header,proof.header)
        self.assertIn('TX_JG_BEGIN',raw.header)
        self.assertNotIn('TX_JG_BEGIN',proof.header)
        self.assertEqual(raw.metadata('assets/ui_texts.json')['C_FINAL_SMALL'],
                         'EMBERBOND / THE JOURNEY CONTINUES')
        self.assertEqual(proof.metadata('assets/ui_texts.json')['C_FINAL_SMALL'],
                         'EMBERBOND / THE END')
    def test_unrelated_old_text(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__('E_YIN','陽'))
    def test_allowed_key_wrong_value(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__('THANKS','Other'))
    def test_other_old_metadata_file(self):
        def change(s):
            p='assets/ui_texts_return.json';s['metadata'][p][next(iter(s['metadata'][p]))]='Other'
        self.rejects(change)
    def test_extra_old_key(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].__setitem__('UNAPPROVED','Extra'))
    def test_missing_old_key(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts.json'].pop('E_YIN'))
    def test_wrong_new_label(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts_journey_guidance.json'].__setitem__('JG_BEGIN','Other'))
    def test_extra_new_label(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts_journey_guidance.json'].__setitem__('JG_OPENING_EXTRA','Extra'))
    def test_missing_new_label(self):
        self.rejects(lambda s:s['metadata']['assets/ui_texts_journey_guidance.json'].pop('JG_BEGIN'))
    def test_unapproved_authoring_override(self):
        self.rejects(lambda s:s['metadata']['assets/journey_guidance_ui.json'].__setitem__('E_YIN','陽'))
    def test_old_enum_shift(self):
        self.rejects(lambda s:s['files'].__setitem__('src/ui.h',s['files']['src/ui.h'].replace('enum {','enum { TX_UNAPPROVED,',1)))
    def test_missing_appended_enum(self):
        self.rejects(lambda s:s['files'].__setitem__('src/ui.h',s['files']['src/ui.h'].replace(' TX_JG_BEGIN,\n','',1)))
    def test_old_raster_change(self):
        self.rejects(lambda s:self.raster_edit(s,'txt_E_YIN_0',self.shift_pixel))
    def test_allowed_raster_wrong_value(self):
        name=next(iter(self.contract['changed_rasters']))
        self.rejects(lambda s:self.raster_edit(s,name,self.shift_pixel))
    def test_added_raster_wrong_value(self):
        self.rejects(lambda s:self.raster_edit(s,'txt_JG_BEGIN_0',self.shift_pixel))
    def test_missing_added_raster(self):
        self.rejects(lambda s:self.raster_edit(s,'txt_JG_BEGIN_0',lambda x:''))
    def test_duplicate_raster(self):
        self.rejects(lambda s:self.raster_edit(s,'txt_E_YIN_0',lambda x:x+'\n'+x))
    def test_pointer_table_or_include_change(self):
        self.rejects(lambda s:s['files'].__setitem__('src/ui.c',s['files']['src/ui.c']+'\n/* unrelated output change */\n'))
    def test_old_width_table_change_with_intact_rasters(self):
        def change(s):
            pattern=r'\{(\d+),(\d+),0,\{txt_'
            for p,text in s['files'].items():
                if re.search(pattern,text):
                    s['files'][p]=re.sub(pattern,lambda m:'{%d,%s,0,{txt_'%(int(m[1])+1,m[2]),text,count=1)
                    return
            self.fail('no width-table test target')
        self.rejects(change)
    def test_historical_hash_change(self):
        self.rejects(lambda s:s['historical'].__setitem__(next(iter(s['historical'])),'0'*64))
    def test_modified_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'contract.json';path.write_bytes(CONTRACT.read_bytes()+b' ')
            with self.assertRaisesRegex(adapter.Rejected,'unreviewed successor contract'):
                adapter.load_contract(path)
    def test_duplicate_json_is_rejected(self):
        with self.assertRaisesRegex(adapter.Rejected,'duplicate JSON'):
            adapter.strict_json('{"JG_BEGIN":"a","JG_BEGIN":"b"}')
    def test_opt_in_is_explicit_and_single(self):
        a=['test'];self.assertFalse(adapter.consume_successor_flag(a));self.assertEqual(a,['test'])
        a=['test','--journey-ui-successor'];self.assertTrue(adapter.consume_successor_flag(a));self.assertEqual(a,['test'])
        with self.assertRaises(adapter.Rejected):adapter.consume_successor_flag(['test','--journey-ui-successor','--journey-ui-successor'])
    def test_view_cannot_mutate_input_metadata(self):
        view=adapter.verify_state(self.state,self.contract);a=view.metadata('assets/ui_texts.json');a['E_YIN']='changed'
        self.assertEqual(view.metadata('assets/ui_texts.json')['E_YIN'],'陰')

if __name__=='__main__':unittest.main(verbosity=2)
