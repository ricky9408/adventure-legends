#!/usr/bin/env python3
"""Read-only native cache observation around a controller-selected R91 cast."""
import argparse,json
from pathlib import Path
from player_feedback_native import Run,ROOT
class Probe(Run):
    def cache(self):
        return {'hardware_frame':self.e.frame,'frame':self.g('frame'),'completed_frame':self.g('render_profile_frame'),'serial':self.g('render_profile_serial'),'page':self.g('page'),'mode':self.g('game_state'),'return_power_kind':self.g('return_power_kind'),'fields':[[self.e.read(self.sym['cache_fields']+4*(45*p+i)) for i in range(45)] for p in range(2)]}
    def tap(self,k,hold=2,release=3):
        s=self.save_state() if k=='R' else None
        if s is not None:
            c=s.roster.instances[s.roster.party[s.roster.selected_party]];command=c.equipped[c.selected_command]
        else:command=0
        if command!=91:return super().tap(k,hold,release)
        before=self.cache();super().tap(k,hold,release)
        self.wait(lambda:self.g('render_profile_serial')!=before['serial'],8)
        after=self.cache();reference=before['fields'][before['page']^1]
        changes=[[{'index':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(reference,row)) if a!=b] for row in after['fields']]
        report={'rom_sha256':self.hashes['rom_sha256'],'symbols_sha256':self.hashes['symbols_sha256'],'command':91,'before':before,'after':after,'changed_indices_against_previous_presented_page':changes,'game_ram_writes':len(self.writes)}
        (self.out/'return91-cache-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--earned-shop-save',type=Path,required=True);p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True);a=p.parse_args();r=Probe(a);r.section('power_cooldowns',r.power_cooldowns);r.finish()
if __name__=='__main__':main()
