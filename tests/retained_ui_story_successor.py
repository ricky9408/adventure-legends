"""Explicit story-only assertion layer over the unchanged pinned G4 adapter.

Never feed the normalized view to a generator/compiler or export it as source.
Default and the old G4 opt-in retain their original behavior.
"""
from pathlib import Path
import copy,os
import retained_ui_successor as base

CONTRACT_SHA256='b93396464c062e59e403f9abaa952f5add5a8331aa1a1daa34b951dd0712fc25'
ALLOWED=frozenset(('C_ELDER_ACT1_0_0','C_ELDER_ACT1_0_1'))
FLAG='--journey-story-ui-successor'

def load_contract(path):
    raw=Path(path).read_bytes()
    base.require(base.digest(raw)==CONTRACT_SHA256,'unreviewed story contract bytes')
    c=base.strict_json(raw)
    base.require(c['schema']==1 and c['name']=='journey-guidance-village-morning-g5','wrong story contract identity')
    base.require(c['parent_contract_sha256']==base.CONTRACT_SHA256,'wrong parent G4 contract')
    base.require(set(c['changed_texts'])==ALLOWED,'story scope is not exactly two elder keys')
    base.require(set(c['changed_rasters'])=={'txt_'+k+'_'+str(i)for k in ALLOWED for i in (0,1)},'wrong story raster scope')
    base.require(set(c['changed_table_rows'])==ALLOWED,'wrong story table scope')
    return c

def load_state(root,parent,contract):
    state=base.load_state(root,parent)
    p=contract['campaign_dialogue']['path']
    state['story_authoring']=base.strict_json((Path(root)/p).read_bytes())
    return state

def normalize_to_g4(state,contract):
    """Validate exact G5 shared UI before reconstructing a G4 assertion input."""
    base.require(len(state['files'])==contract['target_ui_corpus']['file_count'] and
                 base.corpus_digest(state['files'])==contract['target_ui_corpus']['sha256'],
                 'shared UI differs from frozen combined-story output')
    result=copy.deepcopy(state)
    metadata=result['metadata']['assets/ui_texts.json']
    for key,row in contract['changed_texts'].items():
        base.require(metadata.get(key)==row['g5'],'wrong generated story metadata: '+key)
        metadata[key]=row['g4']
    authoring=result.pop('story_authoring')
    expected=contract['campaign_dialogue']
    base.require(base.digest(base.canonical(authoring))==expected['after_canonical_sha256'],
                 'unapproved campaign dialogue authoring')
    pages=authoring['dialogue']['ELDER_ACT1']['pages']
    base.require(pages==[[contract['changed_texts'][k]['g5']for k in sorted(ALLOWED)]],
                 'elder page topology changed')
    pages[0]=[contract['changed_texts'][k]['g4']for k in sorted(ALLOWED)]
    base.require(base.digest(base.canonical(authoring))==expected['before_canonical_sha256'],
                 'campaign authoring does not reconstruct exact G4')
    for name,row in contract['changed_rasters'].items():
        path=row['path'];source=result['files'][path]
        matches=[(statement,key)for statement,found,key in base.RASTER.findall(source)if found==name]
        base.require(len(matches)==1,'missing/duplicate story raster: '+name)
        statement,key=matches[0]
        base.require(key==row['key'] and base.digest(statement.encode())==row['after_sha256'],
                     'unapproved story raster: '+name)
        result['files'][path]=source.replace(statement,row['before_statement'],1)
    for key,row in contract['changed_table_rows'].items():
        path=row['path'];source=result['files'][path]
        base.require(source.count(row['after_statement'])==1,'missing/duplicate story table row: '+key)
        result['files'][path]=source.replace(row['after_statement'],row['before_statement'],1)
    return result

def verify_state(state,parent,contract):
    view=base.verify_state(normalize_to_g4(state,contract),parent)
    view.proof={**view.proof,'story_contract':contract['name'],
        'story_contract_sha256':CONTRACT_SHA256,'additional_existing_texts':2,
        'additional_existing_raster_statements':4,'additional_width_count_table_rows':2,
        'total_changed_existing_texts':8,'total_changed_existing_raster_statements':16,
        'campaign_authoring_exact':True,'parent_g4_verifier_unchanged':True}
    return view

def read_view(root,*,successor=False,contract_path=None,parent_contract_path=None):
    if not successor:return base.read_view(root)
    base.require(contract_path is not None and parent_contract_path is not None,
                 'explicit story and parent contract paths required')
    parent=base.load_contract(parent_contract_path);contract=load_contract(contract_path)
    return verify_state(load_state(root,parent,contract),parent,contract)

def consume_story_flag(argv):
    base.require(argv.count(FLAG)<=1,'repeated story successor flag')
    base.require(not(FLAG in argv and '--journey-ui-successor' in argv),
                 'mixed G4 and story successor flags')
    if FLAG not in argv:return False
    argv.remove(FLAG);return True

def read_view_for_flags(root,argv):
    root=Path(root)
    parent=Path(os.environ.get('JOURNEY_UI_SUCCESSOR_CONTRACT',root/'docs/journey-guidance/retained-ui-contract.json'))
    if consume_story_flag(argv):
        story=Path(os.environ.get('JOURNEY_STORY_UI_SUCCESSOR_CONTRACT',root/'docs/journey-guidance/retained-ui-story-contract.json'))
        return read_view(root,successor=True,contract_path=story,parent_contract_path=parent)
    return base.read_view(root,successor=base.consume_successor_flag(argv),contract_path=parent)
