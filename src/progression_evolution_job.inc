/* Frozen display results are never authority. SELECT prepares both branches;
 * a fresh A starts a new bounded proof of the exact live Save5 state. The
 * singleton Save5 scratch remains immutable until commit/cancel, then is
 * released before animation can request a writer. No additional Save copy. */
enum { EVOLUTION_JOB_IDLE, EVOLUTION_JOB_WARM, EVOLUTION_JOB_PREFLIGHT,
       EVOLUTION_JOB_CANDIDATE, EVOLUTION_JOB_ADMISSION, EVOLUTION_JOB_FINISH,
       EVOLUTION_JOB_SLICES_PER_UPDATE=3 };
static struct {
    Save4U32 save_token;
    CreatureU32 admission_token;
    unsigned phase,warm,confirm,index,context,sanctuary,manual_choice,chapter,target;
    unsigned reasons[2];
    int room,x,y;
    unsigned char selected_party,commands[3],a_latched;
} evolution_job;

static int evolution_participant_matches(void){
    CreatureInstance*c=progression_selected();CreatureRoster*r=&adventure_save.roster;
    return c&&r->selected_party==evolution_job.selected_party&&
      r->selected_party<CREATURE_PARTY_CAPACITY&&
      r->party[r->selected_party]==progression_evolution_slot&&
      c->instance_id==progression_evolution_instance&&c->form_id==progression_evolution_source_form&&
      c->equipped[0]==evolution_job.commands[0]&&c->equipped[1]==evolution_job.commands[1]&&
      c->selected_command==evolution_job.commands[2];
}
static int evolution_request_matches(void){
    const CreatureEvolution*edge=creatures_evolution_at(progression_evolution_source_form,progression_evolution_choice);
    return progression_evolution_count==creatures_evolution_count(progression_evolution_source_form)&&
      progression_evolution_choice<progression_evolution_count&&edge&&edge->to==progression_evolution_target&&
      (!evolution_job.confirm||(progression_evolution_choice==evolution_job.index&&
        progression_evolution_target==evolution_job.target));
}
static void evolution_release(void){
    /* A revoked Save token may already belong to a different operation. Never
     * cancel that operation's singleton cursor or scratch with our stale ID. */
    if(evolution_job.save_token&&save5_preflight_status(evolution_job.save_token)!=SAVE5_FAILED){
        if(evolution_job.admission_token)creatures_admission_job_cancel();
        save5_preflight_cancel();
    }
    evolution_job.save_token=0;evolution_job.admission_token=0;
    evolution_job.phase=EVOLUTION_JOB_IDLE;evolution_job.confirm=0;
}
void progression_evolution_cancel(void){
    evolution_release();evolution_job.a_latched=0;
    progression_evolution_target=progression_evolution_choice=progression_evolution_count=0;
    progression_evolution_source_form=0;progression_evolution_instance=0;
    progression_evolution_reason=CREATURE_EVOLVE_INVALID;
}
int progression_evolution_busy(void){return evolution_job.phase!=EVOLUTION_JOB_IDLE;}
static void evolution_choice_refresh(void){
    const CreatureEvolution*e=creatures_evolution_at(progression_evolution_source_form,progression_evolution_choice);
    progression_evolution_target=e?e->to:0;
    progression_evolution_reason=evolution_job.reasons[progression_evolution_choice<2?progression_evolution_choice:0];
}
static void evolution_denied(unsigned reason){
    evolution_release();progression_evolution_reason=reason;progression_revision++;
    if(progression_evolution_count<2){toast(reason_id(reason,progression_evolution_source_form));game_state=PAUSE;}
}
static void evolution_source_changed(void){
    evolution_release();toast(TX_E_SOURCE_CHANGED);game_state=PAUSE;progression_revision++;
}
static int evolution_environment_matches(void){
    return evolution_participant_matches()&&evolution_request_matches()&&room==evolution_job.room&&px==evolution_job.x&&py==evolution_job.y&&
      chapter_flags==evolution_job.chapter&&
      progression_evolution_context()==evolution_job.context&&
      (unsigned)progression_is_sanctuary()==evolution_job.sanctuary;
}
static void evolution_prepare(unsigned confirm){
    evolution_release();
    evolution_job.confirm=confirm;evolution_job.index=confirm?progression_evolution_choice:0;
    evolution_job.target=progression_evolution_target;
    evolution_job.context=progression_evolution_context();evolution_job.sanctuary=(unsigned)progression_is_sanctuary();
    evolution_job.room=room;evolution_job.x=px;evolution_job.y=py;evolution_job.chapter=chapter_flags;
    evolution_job.save_token=save5_preflight_begin(&adventure_save);
    if(!evolution_job.save_token){evolution_denied(CREATURE_EVOLVE_INVALID);return;}
    /* Two cheap input/draw frames populate both native framebuffer pages.
     * The snapshot is already owned, so inputs during warmup cannot change it. */
    evolution_job.warm=2;evolution_job.phase=EVOLUTION_JOB_WARM;progression_revision++;
}
static unsigned evolution_admission_reason(CreatureU32 token){
    enum CreatureAdmissionStatus status=creatures_admission_job_result(token,0);
    if(creatures_admission_allowed(status))return CREATURE_EVOLVE_READY;
    return status==CREATURE_ADMISSION_COVERAGE_LOSS?CREATURE_EVOLVE_COLLECTION_RESERVED:CREATURE_EVOLVE_INVALID;
}
static void evolution_candidate_done(unsigned reason){
    evolution_job.reasons[evolution_job.index]=reason;
    if(evolution_job.confirm){
        progression_evolution_reason=reason;
        if(reason!=CREATURE_EVOLVE_READY){evolution_denied(reason);return;}
        evolution_job.phase=EVOLUTION_JOB_FINISH;return;
    }
    if(evolution_job.admission_token){creatures_admission_job_cancel();evolution_job.admission_token=0;}
    ++evolution_job.index;
    evolution_job.phase=evolution_job.index<progression_evolution_count?EVOLUTION_JOB_CANDIDATE:EVOLUTION_JOB_FINISH;
}
static void evolution_prepare_step(void){
    const Save5State*s;const CreatureEvolution*edge;unsigned status;
    if(!evolution_environment_matches()){evolution_source_changed();return;}
    if(save5_preflight_status(evolution_job.save_token)==SAVE5_FAILED){evolution_denied(CREATURE_EVOLVE_INVALID);return;}
    switch(evolution_job.phase){
    case EVOLUTION_JOB_WARM:
        if(!--evolution_job.warm)evolution_job.phase=EVOLUTION_JOB_PREFLIGHT;
        return;
    case EVOLUTION_JOB_PREFLIGHT:
        /* Four roster records at most; no whole-roster validator in UI. */
        status=save5_preflight_step(evolution_job.save_token,640);
        if(status==SAVE5_DONE)evolution_job.phase=EVOLUTION_JOB_CANDIDATE;
        else if(status!=SAVE5_BUSY)evolution_denied(CREATURE_EVOLVE_INVALID);
        return;
    case EVOLUTION_JOB_CANDIDATE:
        s=save5_preflight_snapshot(evolution_job.save_token);
        edge=creatures_evolution_at(progression_evolution_source_form,evolution_job.index);
        if(!s||!edge){evolution_denied(CREATURE_EVOLVE_INVALID);return;}
        status=creatures_can_evolve_to(&s->roster.instances[progression_evolution_slot],edge->to,
          evolution_job.context,(int)evolution_job.sanctuary);
        if(status!=CREATURE_EVOLVE_READY){evolution_candidate_done(status);return;}
        evolution_job.admission_token=creatures_admission_job_begin(&s->roster,edge->to,progression_evolution_slot);
        if(!evolution_job.admission_token){evolution_denied(CREATURE_EVOLVE_INVALID);return;}
        evolution_job.phase=EVOLUTION_JOB_ADMISSION;return;
    case EVOLUTION_JOB_ADMISSION:
        {
            int result=creatures_admission_job_step(evolution_job.admission_token,4);
            if(result==CREATURE_ADMISSION_JOB_COMPLETE)evolution_candidate_done(evolution_admission_reason(evolution_job.admission_token));
            else if(result!=CREATURE_ADMISSION_JOB_PENDING)evolution_denied(CREATURE_EVOLVE_INVALID);
        }
        return;
    case EVOLUTION_JOB_FINISH:
        /* Exact all-state comparison immediately precedes the once-only core
         * commit, which independently compares all4140 roster bytes. No yield,
         * callback or scratch release is allowed between those operations. */
        if(!save5_preflight_matches(evolution_job.save_token,&adventure_save)){evolution_source_changed();return;}
        if(evolution_job.confirm){
            evolution_before=progression_evolution_source_form;
            status=creatures_admission_job_commit_evolution(evolution_job.admission_token,&adventure_save.roster,
              evolution_job.context,(int)evolution_job.sanctuary,1);
            evolution_job.admission_token=0;
            if(status!=CREATURE_EVOLVE_READY){evolution_denied(status);return;}
            evolution_release();progression_refresh();evolution_tick=0;game_state=EVOLVE_ANIM;sfx(2);
        }else{
            if(!evolution_job.manual_choice){
                progression_evolution_choice=0;
                if(evolution_job.reasons[0]!=CREATURE_EVOLVE_READY&&progression_evolution_count==2&&
                   evolution_job.reasons[1]==CREATURE_EVOLVE_READY)progression_evolution_choice=1;
            }
            evolution_choice_refresh();evolution_release();progression_revision++;
            if(progression_evolution_count<2&&progression_evolution_reason!=CREATURE_EVOLVE_READY)
                evolution_denied(progression_evolution_reason);
        }
        return;
    default:return;
    }
}
