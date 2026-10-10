/* Four compact intents, not a Save5State snapshot. Job engine owns the existing
 * scratch buffer; calls from active PLAY only enqueue facts already proved. */
static COLD int queue(unsigned op,unsigned area,unsigned quest,unsigned bit,unsigned source,unsigned slot,unsigned family,unsigned key,unsigned id){WorldIntent e;unsigned i;if(event_handle)return 0;e.instance_id=id;e.op=(unsigned char)op;e.area=(unsigned char)area;e.quest=(unsigned char)quest;e.bit=(unsigned char)bit;e.source=(unsigned char)source;e.slot=(unsigned char)slot;e.family=(unsigned char)family;e.key=(unsigned char)key;
 for(i=event_index;i<event_count;i++){WorldIntent*p=&events[i];if(p->op==op&&p->area==area&&p->quest==quest&&p->bit==bit&&p->source==source&&p->slot==slot&&p->family==family&&p->key==key&&p->instance_id==id)return 1;if(op==UW_REQUEST_QUEST_PROGRESS&&p->op==UW_REQUEST_QUEST_OFFER&&p->quest==quest){*p=e;return 1;}}
 if(event_count>=4)return 0;
 if(!event_count)event_generation=room_generation;
 events[event_count++]=e;changed();return 1;
}
int underwater_game_event_pending(void){return event_count!=0;}
static COLD void event_present(const WorldIntent*e,int r){unsigned aid;int good=r==UNDERWATER_CHANGED||r==UNDERWATER_NOW_READY||r==UNDERWATER_REWARDED;if(e->op==UW_REQUEST_VISIT){if(good||r==UNDERWATER_UNCHANGED)transition_ready=1;else transition_area=0;return;}
 if(e->op==UW_REQUEST_TRIAL_STATUS){if(r==UNDERWATER_REWARDED||r==UNDERWATER_CHANGED||r==UNDERWATER_NOW_READY)start_trial_proof(e);else toast(r==UNDERWATER_UNCHANGED?TX_UW_TRIAL_ALREADY:TX_UW_TRIAL_PICK);return;}
 if(e->op==UW_REQUEST_ANCHOR){if(good||r==UNDERWATER_UNCHANGED){checkpoint_spawn=2;adventure_save.campaign.spawn=2;game_health_fill();dirty=1;toast(TX_UW_RESTED);}return;}
 if(!good){if(r!=UNDERWATER_UNCHANGED)toast(r==UNDERWATER_FULL?TX_UW_FULL:r==UNDERWATER_SPACE_RESERVED?TX_UW_RESERVED:r==UNDERWATER_ID_EXHAUSTED?TX_UW_ID_LIMIT:TX_UW_NOT_YET);return;}
 dirty=1;
 if(e->op==UW_REQUEST_QUEST_CLAIM){creatures_credit_event(&adventure_save.roster,280+e->quest-38,160,CREATURE_CREDIT_PERSONAL_QUEST);progression_refresh();toast(e->quest==40?TX_UW_END:TX_UW_RECEIVED);}
 else if(e->op==UW_REQUEST_FIELD_RECRUIT){aid=underwater_source_aid(e->source);if(aid<128)creatures_credit_event(&adventure_save.roster,384+aid,120,CREATURE_CREDIT_FIELD_AID);progression_refresh();toast(TX_UW_RECRUITED);}
 else if(e->op==UW_REQUEST_REPEAT_RECRUIT){repeat_used|=(unsigned char)(1u<<(e->source-1));progression_refresh();toast(TX_UW_RECRUITED);}
 else if(e->op==UW_REQUEST_TRIAL_COMPLETE){aid=underwater_trial_aid(e->family,e->key);if(aid<128)creatures_credit_event(&adventure_save.roster,384+aid,160,CREATURE_CREDIT_FIELD_AID);progression_refresh();clear_trial();invalidate_actions();toast(TX_UW_TRIAL_DONE);}
 changed();
}
COLD unsigned underwater_game_prepare_event(void){unsigned status;int r;WorldIntent e;UnderwaterRequest req={0};if(!event_count)return SAVE5_DONE;if(event_generation!=room_generation){underwater_game_cancel_event();return SAVE5_FAILED;}e=events[event_index];if(!event_handle){req.operation=e.op;req.room=e.area;req.quest=e.quest;req.bit=e.bit;req.source=e.source;req.slot=e.slot;req.family=e.family;req.key=e.key;req.instance_id=e.instance_id;event_handle=underwater_job_begin(&adventure_save,&req,event_generation);if(!event_handle){underwater_game_cancel_event();return SAVE5_FAILED;}return SAVE5_BUSY;}
 status=underwater_job_step(event_handle,1024,event_generation);if(status==SAVE5_BUSY)return status;r=underwater_job_result(event_handle);underwater_job_cancel();event_handle=0;if(status==SAVE5_FAILED){underwater_game_cancel_event();toast(TX_UW_NOT_YET);return status;}event_index++;event_present(&e,r);if(event_index>=event_count){event_count=event_index=0;if(transition_ready==2)transition_ready=1;persist();return SAVE5_DONE;}if(event_generation!=room_generation){underwater_game_cancel_event();return SAVE5_FAILED;}return SAVE5_BUSY;
}
