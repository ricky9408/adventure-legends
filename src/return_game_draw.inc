static void ra(unsigned s,int x,int y){if(x-camera_x>=-8&&x-camera_x<248&&y-camera_y>=-8&&y-camera_y<168)return_actor(s,x,y);}
static void rf(unsigned f,int x,int y){if(x-camera_x>=-8&&x-camera_x<248&&y-camera_y>=-8&&y-camera_y<168)region_form_actor(f,x,y);}
static void rl(int x,int y,int xx,int yy,int c){line(x-camera_x,y-camera_y,xx-camera_x,yy-camera_y,c);}
static void rr(int x,int y,int w,int h,int c){rect(x-camera_x,y-camera_y,w,h,(unsigned char)c);}
static void outline(int x,int y,int w,int h,int c){rl(x,y,x+w,y,c);rl(x+w,y,x+w,y+h,c);rl(x+w,y+h,x,y+h,c);rl(x,y+h,x,y,c);}
static void ring(int x,int y,int c){rl(x-12,y-3,x-3,y-12,c);rl(x-3,y-12,x+3,y-12,c);rl(x+3,y-12,x+12,y-3,c);rl(x+12,y-3,x+12,y+3,c);rl(x+12,y+3,x+3,y+12,c);rl(x+3,y+12,x-3,y+12,c);rl(x-3,y+12,x-12,y+3,c);rl(x-12,y+3,x-12,y-3,c);}
static void arrow(int x,int y,int c){rl(x,y+25,x,y+17,c);rl(x,y+17,x-3,y+21,c);rl(x,y+17,x+3,y+21,c);}
COLD void return_game_draw_actors(void){unsigned i;int x,y;if(!return_game_is_room((unsigned)room))return;reset_point(&x,&y);ra(RETURN_SPR_RESET,x,y);
 for(i=0;i<13;i++)if(trials[i].area==room)ra(RETURN_SPR_TRIAL,trials[i].lectern[0],trials[i].lectern[1]);
 if(return_game_trial.index<13){const TrialDef*d=&trials[return_game_trial.index];ra(RETURN_SPR_HANDLE,d->manual[0],d->manual[1]);return;}
 if(room==54){ra((adventure_save.quests.anchors[5]&1)?RETURN_SPR_REST_LIT:RETURN_SPR_REST,72,256);ra(ambient_clock&32?RETURN_SPR_GARDENER_WORK:RETURN_SPR_GARDENER,208,240);ra(RETURN_SPR_GUIDE,288,64);ra(RETURN_SPR_NOTICE,240,240);ra(RETURN_SPR_ROOT,240,72);ra(RETURN_SPR_HEARTH,272,240);}
 else if(room==55){ra((adventure_save.quests.anchors[5]&2)?RETURN_SPR_REST_LIT:RETURN_SPR_REST,40,116);ra(RETURN_SPR_BELLMAKER,40,56);ra(RETURN_SPR_HANDLE,64,112);ra(RETURN_SPR_HANDLE,176,112);if(!done(47)||repeat_active||!(repeat_used&1))rf(101,208,80);}
 else if(room==56){ra(RETURN_SPR_RECEIVER,240,96);ra(RETURN_SPR_RECEIVER,240,208);ra(RETURN_SPR_HANDLE,288,256);ra(RETURN_SPR_NOTICE,432,256);ra(ambient_clock&32?RETURN_SPR_PORTER_WORK:RETURN_SPR_PORTER,272,56);}
 else if(room==57){ra(RETURN_SPR_LATCH,320,208);ra(RETURN_SPR_SAIL,400,240);ra(RETURN_SPR_HANDLE,352,272);ra(RETURN_SPR_HANDLE,304,272);ra(RETURN_SPR_HEARTH,304,240);ra(RETURN_SPR_NOTICE,432,272);ra(ambient_clock&32?RETURN_SPR_PORTER_WORK:RETURN_SPR_PORTER,done(48)?384:280,112);ra(RETURN_SPR_WEAVER,288,192);}
 else if(room==58){ra(RETURN_SPR_HANDLE,80,80);ra(RETURN_SPR_HANDLE,160,80);ra(RETURN_SPR_HANDLE,128,144);ra(RETURN_SPR_GUIDE,done(49)?176:128,112);ra(RETURN_SPR_NOTICE,240,240);if(!done(49)||repeat_active||!(repeat_used&2))rf(103,400,240);if(done(49))ra(RETURN_SPR_HANDLE,368,272);}
 else if(room==59){ra(RETURN_SPR_SKIFF,64,56);ra(RETURN_SPR_HANDLE,120,104);ra(RETURN_SPR_GUIDE,192,56);}
 else if(room==60){ra(RETURN_SPR_NOTICE,120,104);ra(RETURN_SPR_GUIDE,40,80);}
 else if(room==61){ra(RETURN_SPR_LATCH,64,56);ra(RETURN_SPR_SKIFF,176,56);}
}
static void draw_trial(void){ReturnTrialProof*t=&return_game_trial;const TrialDef*d=&trials[t->index];unsigned i;int x,y;for(i=0;i<d->count;i++){x=d->target[i][0];y=d->target[i][1];ring(x,y,t->casts&(1u<<i)?PAL_PINE3:PAL_GOLD3);arrow(x,y,PAL_WATER2);rr(x-2,y-2,5,5,(i==2&&(t->index==1||t->index==6||t->index==8))?PAL_ROSE3:PAL_GOLD4);}
 x=d->manual[0];y=d->manual[1];outline(x-12,y-8,24,16,t->setting?PAL_PINE3:PAL_GOLD1);rl(x-7,y+3,x+(t->setting?7:-7),y-5,PAL_GOLD4);x=d->walk[0];y=d->walk[1];outline(x-10,y-6,20,12,t->walk?PAL_PINE3:PAL_WATER2);
 /* Diagrams follow each existing workspace, never cover it with a panel. */
 if(t->index==0){rl(64,94,96,144,PAL_FIRE2);rl(128,126,96,144,PAL_FIRE2);rr(59,76,4,6,PAL_ROSE3);}
 else if(t->index==1){rl(336,86,336,126,PAL_PINE3);rl(416,118,416,148,PAL_PINE3);outline(364,102,24,20,PAL_ROSE3);}
 else if(t->index==2){rl(80,66,176,66,PAL_WATER2);outline(120,56,16,12,t->setting?PAL_PINE3:PAL_GOLD3);}
 else if(t->index==3){rl(64,68,64,94,PAL_STONE2);rl(176,68,176,94,PAL_STONE2);rl(80,92,160,92,PAL_GOLD3);}
 else if(t->index==4){rl(80,80,48,80,PAL_WATER2);rl(48,80,48,208,PAL_WATER2);rl(48,208,80,208,PAL_WATER2);}
 else if(t->index==5){for(i=0;i<3;i++)rr(60+(int)i*56,56,8,3,i<t->stage?PAL_PINE3:PAL_GOLD2);}
 else if(t->index==6){outline(108,44,24,24,PAL_ROSE3);rl(64,42,176,42,PAL_GOLD2);}
 else if(t->index==7){rl(320,48,416,48,PAL_GOLD2);rl(416,48,416,66,PAL_GOLD2);outline(360,88,16,12,t->stage>1?PAL_PINE3:PAL_STONE2);}
 else if(t->index==8){outline(196,180,24,24,t->setting?PAL_PINE3:PAL_ROSE3);rl(80,224,176,256,PAL_FIRE2);}
 else if(t->index==9){outline(306,66,28,28,PAL_PINE3);outline(402,98,28,28,PAL_PINE3);rl(336,88,400,120,PAL_PINE3);}
 else if(t->index==10){rl(80,208,176,208,PAL_WATER2);rl(88,206,96,208,PAL_WATER2);rl(168,210,176,208,PAL_WATER2);}
 else if(t->index==11){outline(352,152,24,24,PAL_ROSE3);rl(336,96,416,160,PAL_GOLD2);}
 else if(t->index==12){rl(64,72,192,72,PAL_WATER2);outline(176,88,32,16,t->setting?PAL_PINE3:PAL_GOLD2);}
}
COLD void return_game_draw_overlay(void){unsigned i;int x,y;if(!return_game_is_room((unsigned)room))return;{short dr[2][4];unsigned n=dynamic_rects((unsigned)room,setting,dr);for(i=0;i<n;i++){rr(dr[i][0],dr[i][1],dr[i][2],dr[i][3],PAL_WOOD2);outline(dr[i][0],dr[i][1],dr[i][2],dr[i][3],PAL_GOLD3);}}if(return_game_trial.index<13){draw_trial();return;}
 for(i=0;i<8;i++)if(return_game_field_target(i,&x,&y,0)){ring(x,y,(room==60&&i<phase_step)||(setting[3]&(1u<<i))?PAL_PINE3:PAL_GOLD3);if((room==57&&i==0)||(room==61&&i==0)||repeat_active)arrow(x,y,PAL_WATER2);}
 if(room==54&&setting[0]){rl(224,76,224,104,PAL_PINE3);rl(256,76,256,104,PAL_PINE3);}if(room==54&&setting[1])rr(268,230,8,6,PAL_FIRE2);
 if(room==55){for(i=0;i<2;i++){x=i?176:64;y=112;unsigned v=repeat_active?(repeat_setting>>i)&1:setting[i];rl(x-9,y-4,x+(v?9:-9),y-4+(v?0:12),v?PAL_PINE3:PAL_GOLD1);}if(setting[0]&&setting[1])rl(80,112,160,112,PAL_PINE3);}
 if(room==56){rl(240,110,264,128,setting[1]&1?PAL_WATER4:PAL_WATER2);rl(264,176,240,194,setting[1]&2?PAL_WATER4:PAL_WATER2);outline(276,246,24,16,setting[0]?PAL_PINE3:PAL_GOLD2);}
 if(room==57){outline(340,258,24,24,setting[0]?PAL_PINE3:PAL_GOLD2);rl(292,260,316,260,setting[1]?PAL_PINE3:PAL_GOLD2);if(done(52))rl(280,168,336,168,PAL_ROSE4);}
 if(room==58){for(i=0;i<2;i++){x=80+(int)i*80;outline(x-20,52,40,16,setting[i]?PAL_WATER2:PAL_GOLD2);if(setting[i]){rl(x-20,54,x+20,66,PAL_ROSE3);rl(x-20,66,x+20,54,PAL_ROSE3);}}if(setting[2])rl(112,152,144,152,PAL_WATER3);}
 if(setting[3]){if(room==56){rr(354,130,16,8,PAL_WOOD3);rl(354,134,384,134,PAL_GOLD3);}if(room==58){rl(56,212,96,212,PAL_WATER3);rl(304,64,336,64,PAL_PINE3);}if(room==54)rl(304,232,336,232,PAL_FIRE2);}
 if(room==60){for(i=0;i<4;i++){static const short pts[5][2]={{56,48},{96,40},{144,40},{184,48},{120,104}};rl(pts[i][0],pts[i][1]+14,pts[i+1][0],pts[i+1][1]+14,PAL_GOLD1);}if(phase_step<5){static const short pts[5][2]={{56,48},{96,40},{144,40},{184,48},{120,104}};outline(pts[phase_step][0]-15,pts[phase_step][1]-15,30,30,PAL_WATER2);}}
 if(repeat_active){x=room==55?208:400;y=room==55?112:272;outline(x-10,y-6,20,12,repeat_stage==2?PAL_PINE3:PAL_WATER2);}
}
/* Old-room changes are bitmap overlays, consuming zero resident/streamed OBJ
 * slots in already crowded towns. Explicit boards have their own facing cones. */
static void old_notice(int x,int y,int color){ring(x,y,PAL_GOLD2);rr(x-7,y-8,15,12,PAL_WOOD1);rr(x-5,y-6,11,8,PAL_GOLD4);rr(x-1,y+4,3,5,PAL_WOOD2);rl(x-3,y-3,x+3,y-3,color);}
COLD void return_game_draw_old_overlay(void){if(!done(40))return;if(room==46){old_notice(200,272,PAL_WATER2);return;}if(room==0){old_notice(152,112,PAL_WATER2);if(done(46)){rl(148,107,156,104,PAL_PINE3);rl(148,104,156,107,PAL_WATER2);}if(done(51)){rl(147,100,151,97,PAL_GOLD3);rl(153,97,159,100,PAL_GOLD3);}return;}if(!done(46))return;
 if(room==16){old_notice(368,152,PAL_GOLD1);old_notice(112,144,PAL_WATER2);rl(394,152,384,152,PAL_GOLD2);rl(384,152,388,148,PAL_GOLD2);rl(400,144,410,144,PAL_GOLD2);rl(410,144,406,140,PAL_GOLD2);if(done(47)){rr(400,136,16,3,PAL_GOLD3);rr(402,129,4,7,PAL_STONE3);}if(done(50)){rr(134,120,18,24,PAL_GOLD4);rl(137,124,148,140,PAL_WATER2);rl(137,138,148,128,PAL_PINE3);}}
 else if(room==17){if(done(50)){rl(244,274,280,274,PAL_WATER2);rl(270,270,280,274,PAL_WATER2);}}
 else if(room==22){old_notice(192,192,PAL_WATER2);old_notice(352,176,PAL_FIRE2);if(done(48)){rr(286,132,30,3,PAL_GOLD3);rr(298,124,4,8,PAL_WOOD3);}if(done(52)){rr(340,180,32,3,PAL_ROSE3);rr(341,183,2,9,PAL_WOOD1);rr(370,183,2,9,PAL_WOOD1);}}
 else if(room==30){old_notice(448,192,PAL_GOLD1);if(done(49)){rl(350,182,418,182,PAL_ROSE3);rl(354,179,414,185,PAL_GOLD3);}if(done(53)){for(unsigned j=0;j<4;j++)rr(440+(int)(j&1)*8,166+(int)(j>>1)*8,6,6,PAL_GOLD4);}}
 else if(room==18||room==20)old_notice(208,112,PAL_GOLD1);
 else if(room==38&&done(52))old_notice(208,272,PAL_FIRE2);
}
COLD void return_game_draw_journal(void){static const int states[4]={TX_RT_UNSEEN,TX_RT_ACTIVE,TX_RT_READY,TX_RT_CLAIMED};unsigned sel=return_game_journal_selection%21,q,b,x=82;CreatureInstance*c=progression_selected();box(8,31,224,122);centered(TX_RT_JOURNAL,34,PAL_GOLD3);if(sel<8){q=46+sel;text(qnames[sel],14,54,PAL_GOLD4);text(states[state(q)],178,54,PAL_TEAL2);text(qclues[sel][0],14,76,PAL_GOLD4);text(qclues[sel][1],14,94,PAL_GOLD4);for(b=1;b<=8;b<<=1)if(return_quest_mask(q)&b){rect(x,116,8,8,adventure_save.quests.objectives[q]&b?PAL_GOLD3:PAL_STONE1);x+=13;}}else{sel-=8;text(trial_names[sel],14,54,PAL_GOLD4);text(trial_clues[sel][0],14,76,PAL_GOLD4);text(trial_clues[sel][1],14,94,PAL_GOLD4);text(room_names[trials[sel].area-54],14,116,PAL_TEAL2);q=c&&creatures_has_trial_qualified(c,trials[sel].family,trials[sel].key);text(q?TX_RT_CLAIMED:TX_RT_ACTIVE,178,54,PAL_TEAL2);}centered(TX_RT_KEYS,138,PAL_TEAL2);}
int return_game_menu_input(int k){if(journal_tab!=10)return 0;if(k&UP){return_game_journal_selection=(return_game_journal_selection+20)%21;changed();return 1;}if(k&DOWN){return_game_journal_selection=(return_game_journal_selection+1)%21;changed();return 1;}return 0;}
