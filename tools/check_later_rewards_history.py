#!/usr/bin/env python3
"""Reproduce revision10 policy only from its hash-pinned pre-reward source."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / 'tests/fixtures/v5-revision10-policy-oracle'
MANIFEST_SHA = 'acf511870c171b0428e0189dcd334d3f46099b6f9088ee8ea5925e0efb6e010a'


def verify_oracle():
    raw = (ORACLE / 'manifest.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == MANIFEST_SHA, 'Revision10 manifest changed'
    for name, sha in json.loads(raw)['files'].items():
        assert hashlib.sha256((ORACLE / name).read_bytes()).hexdigest() == sha, name


def extract(src, name):
    match = re.search(r'^(?:static (?:inline )?)?(?:int|unsigned|void|Save4U32) ' + name + r'\([^;]+?\)\s*\{', src, re.M)
    start, end, depth = match.start(), match.end(), 1
    while depth:
        depth += (src[end] == '{') - (src[end] == '}')
        end += 1
    text = src[start:end]
    return text if text.startswith('static') else 'static ' + text


CREATURE_BODY = r'''
static int history10_form_allowed(unsigned id) { return id>=1 && id<=128; }
static unsigned history10_family(unsigned id) { return history10_form_allowed(id)?history10_forms[id-1].family:0; }
static unsigned history10_legacy(unsigned id) { unsigned f=history10_family(id);return f>=1&&f<=4?f-1:255; }
static int history10_instance_validate(const CreatureInstance*c) {
 const History10Form*p;unsigned i,n;
 if(!c)return 0;
 if(!c->form_id)return zero_bytes((const Save4U8*)c,24);
 if(!history10_form_allowed(c->form_id))return 0;
 p=&history10_forms[c->form_id-1];
 if(!(c->flags&1u)||(c->flags&~7u)||c->level<1||c->level>50||c->bond>100||c->xp>470596u||
    !c->instance_id||c->instance_id==0xffffffffu||c->nickname_id||
    ((c->flags&2u)&&history10_legacy(c->form_id)>=4)||c->polarity!=p->polarity||
    c->level<p->min_level||c->bond<p->min_bond||(c->trial_flags&~p->trial_mask)||
    (c->trial_flags&p->required_trial)!=p->required_trial||c->selected_command>1||
    !c->equipped[c->selected_command]||(c->equipped[0]&&c->equipped[0]==c->equipped[1]))return 0;
 n=c->level-1;if(c->xp<4u*n*n*n)return 0;++n;if(c->level<50&&c->xp>=4u*n*n*n)return 0;
 if(p->family>=41&&p->family<=44&&c->trial_flags&&(c->level<34||c->bond<60))return 0;
 for(i=0;i<sizeof history10_dependencies/sizeof history10_dependencies[0];++i){
  const Save4U16*d=history10_dependencies[i];
  if(p->family==d[0]&&(c->trial_flags&d[1])&&(c->trial_flags&d[2])!=d[2])return 0;
 }
 for(i=0;i<2;++i)if(c->equipped[i]){
  unsigned j;
  for(j=0;j<p->learn_count;++j){const Save4U8*l=history10_learn[p->learn_offset+j];
   if(l[1]==c->equipped[i]&&l[0]<=c->level)break;}
  if(j==p->learn_count)return 0;
 }
 return 1;
}
static int history10_roster_validate(const CreatureRoster*r) {
 unsigned i,j,stories=0,members=0,legends=0;
 if(!r||!r->next_instance_id)return 0;
 for(i=0;i<4;++i){unsigned slot=r->party[i];const CreatureInstance*c;
  if(slot==255)continue;
  if(slot>=160)return 0;
  c=&r->instances[slot];if(!history10_form_allowed(c->form_id))return 0;
  for(j=0;j<i;++j)if(slot==r->party[j])return 0;
  ++members;legends+=history10_forms[c->form_id-1].legendary;
 }
 if(legends>1||(!members?r->selected_party!=255:r->selected_party>=4||r->party[r->selected_party]==255))return 0;
 for(i=0;i<16;++i)if(r->obtained[i]&~r->seen[i])return 0;
 for(i=0;i<160;++i){const CreatureInstance*c=&r->instances[i];unsigned legacy;
  if(!history10_instance_validate(c)||r->expedition_bond[i]>10)return 0;
  if(!c->form_id){if(r->expedition_bond[i])return 0;continue;}
  if(c->instance_id>=r->next_instance_id||!(r->obtained[(c->form_id-1)>>3]&(1u<<((c->form_id-1)&7))))return 0;
  for(j=0;j<i;++j)if(c->instance_id==r->instances[j].instance_id)return 0;
  if(c->flags&2u){legacy=history10_legacy(c->form_id);
   if(legacy>=4||(stories&(1u<<legacy))||!(r->rewards[0]&(1u<<legacy)))return 0;
   stories|=1u<<legacy;
  }
 }
 return stories==(r->rewards[0]&15u);
}
'''


def creature_data():
    # Probe the accepted implementation, never the current catalog.
    import check_economy_history as prior
    original_oracle, original_probe = prior.ORACLE, prior.PROBE
    try:
        prior.ORACLE = ORACLE
        prior.PROBE = original_probe.replace('creatures_trial_allowed_mask(id,9)', 'creatures_trial_allowed_mask(id,10)')
        return prior.creature_snapshot()
    finally:
        prior.ORACLE, prior.PROBE = original_oracle, original_probe


def outputs():
    src = (ORACLE / 'src/save5.c').read_text()
    names = ('entry_requirements north_requirements save5_campaign_validate quest_objective_mask '
             'quest_objective_validate quest_reward_validate quest_fields_validate save5_quests_validate '
             'magma_quest_campaign_validate quest_campaign_validate retained_creature_bits retained_creatures '
             'quest_creatures_validate southern_instance_evidence southern_roster_evidence southern_sources_validate '
             'magma_form_row magma_instance_evidence magma_sources_validate magma_roster_sources_validate').split()
    pieces = [extract(src, name) for name in names]
    for region in ('underwater', 'return', 'horizons', 'covenants'):
        text = (ORACLE / ('src/save5_' + region + '_policy.inc')).read_text()
        names += re.findall(r'^static (?:int|unsigned|void) (\w+)\(', text, re.M)
        names += re.findall(r'^static const Save4U8 (\w+)\[', text, re.M)
        pieces.append(text)
    arrays = ['quest_masks', 'magma_bases']
    declarations = [re.search(r'^static const Save4U8 ' + name + r'\[[^;]+;', src, re.M)[0] for name in arrays]
    text = '\n'.join(declarations + pieces)
    # All cross-calls and internal tables are independent of current policy.
    for name in sorted(set(names + arrays), key=len, reverse=True):
        text = re.sub(r'\b' + name + r'\b', 'history10_' + name, text)
    text = re.sub(r'creatures_form\((\d+)\)', r'history10_form_allowed(\1)', text)
    text = re.sub(r'creatures_family_revision\(c->form_id,[78]\)', 'history10_family(c->form_id)', text)
    text = text.replace('save4_unlock_mask(chapter)', '(chapter>=3?15u:chapter?7u:3u)')
    # Function prototypes keep original dependency/order distinctions intact.
    prototypes = re.findall(r'^static (?:int|unsigned|void|Save4U32) \w+\([^;{]+\)', text, re.M)
    text = '\n'.join(p + ';' for p in prototypes) + '\n' + text
    economy = extract((ORACLE / 'src/economy_types.h').read_text(), 'economy_state_validate')
    economy = economy.replace('static inline', 'static').replace('economy_state_validate', 'history10_economy_validate')
    economy = economy.replace('for(i=0;i<9;++i)if(e->reserved[i])return 0;', 'if(e->later_claims||!zero_bytes(e->reserved,8))return 0;')
    text += '\n' + economy + '\n'
    header = '/* Immutable revision10 acceptance, reproduced from the pinned G7 source closure.\n * Source: tests/fixtures/v5-revision10-policy-oracle/manifest.json. */\n'
    equipment = (ORACLE / 'src/save5_revision9_equipment.inc').read_text().replace('save5_policy9_', 'save5_policy10_').replace('accepted E', 'accepted G7')
    # Verify this retained identity table against the actual revision10 source.
    eq_src = (ORACLE / 'src/equipment_data.c').read_text()
    ids = list(map(int, re.search(r'equipment_authored_ids\[EQUIPMENT_AUTHORED_COUNT\] = \{([^}]+)', eq_src)[1].split(',')))
    quests = list(map(int, re.search(r'equipment_source_quest\[48\] = \{([^}]+)', src)[1].split(',')))
    actual = [tuple(map(int, row.split(','))) for row in re.findall(r'\{([^{}]+)\}', equipment.split('save5_policy10_items[48]={')[1])]
    for i, item in enumerate(ids):
        row = re.search(r'\[' + str(item) + r'\] = \{' + str(item) + r', (\d+), \d+, (\d+),', eq_src)
        assert actual[i] == (item, int(row[1]), int(row[2]), 0 if not i else 1 if quests[i]<0 else 2, quests[i])
    data = creature_data()
    creatures = header + 'typedef struct History10Form { Save4U16 trial_mask,required_trial,learn_offset; Save4U8 family,polarity,min_level,min_bond,learn_count,legendary; } History10Form;\n'
    creatures += 'static const Save4U8 history10_learn[][2]={\n'
    learns, rows = [], []
    for f in data['forms']:
        rows.append((f['trial_mask'],f['required_trial'],len(learns),f['family'],f['polarity'],f['min_level'],f['min_bond'],len(f['learn']),f['rarity']))
        learns += f['learn']
    creatures += ''.join(' {%d,%d},\n' % tuple(l) for l in learns) + '};\n'
    creatures += 'static const History10Form history10_forms[128]={\n' + ''.join(' {' + ','.join(map(str,row)) + '},\n' for row in rows) + '};\n'
    creatures += 'static const Save4U16 history10_dependencies[][3]={\n' + ''.join(' {%d,%d,%d},\n' % (d['family'],d['mask'],d['prerequisite']) for d in data['trial_dependencies']) + '};\n' + CREATURE_BODY
    return {'src/save5_revision10_creatures.inc': creatures,
            'src/save5_revision10_policy.inc': header + text,
            'src/save5_revision10_equipment.inc': equipment}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    verify_oracle()
    for name, content in outputs().items():
        target = ROOT / name
        if args.write:
            target.write_text(content)
        else:
            assert target.read_text() == content, 'Frozen revision10 changed: ' + name
    print('Pinned G7 closure and immutable revision10 policy verified')


if __name__ == '__main__':
    main()
