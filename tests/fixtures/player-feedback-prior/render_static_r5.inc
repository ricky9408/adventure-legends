/* Pinned R5 reference: full world followed by opaque WIN overwrite. */
COLD void reference_render_static(void){int display_state=game_display_state();
#ifndef GAME_HOST_TEST
 unsigned profile_started;
#endif
 screen=(u16*)(page?0x0600A000:0x06000000);if(game_state==TITLE||game_state==NEW_GAME_CONFIRM){copy_bg(BACK_TITLE);if(game_state==NEW_GAME_CONFIRM){box(8,50,224,76);centered(TX_NEW_CONFIRM,57,GOLD);centered(TX_NEW_WARNING,80,CREAM);centered(TX_NEW_CHOICE,104,TEAL);}else{wordmark();centered(TX_SUBTITLE,60,CREAM);centered(TX_TAGLINE,78,CREAM);centered(TX_FB_TITLE_KEYS,96,TEAL);box(43,112,154,36);centered(has_save?TX_CONTINUE:TX_START,114,title_option?CREAM:GOLD);if(has_save)centered(TX_NEW,130,title_option?GOLD:CREAM);else centered(TX_BUILD,132,CREAM);}return;}
#ifndef GAME_HOST_TEST
 profile_started=cycle_now();
#endif
 world_mask_active=0;{int left,top,bottom;if(modal_coverage(&left,&top,&bottom)){world_mask_left=left*2;world_mask_right=240-left*2;world_mask_top=top;world_mask_bottom=bottom;world_mask_active=1;}}
 draw_world();world_mask_active=0;
#ifndef GAME_HOST_TEST
 render_world_cycles=cycle_now()-profile_started;profile_started=cycle_now();
#endif
 if(display_state==PAUSE){int n;for(n=0;n<112;n++)modal_world_row[page][n]=screen[153*120+4+n];}draw_play_toast();draw_play_hint();if(display_state==DIALOG){box(5,99,230,56);text(dialog_speakers[dpage],13,103,GOLD);text(dialog_lines[dpage*2],13,120,CREAM);text(dialog_lines[dpage*2+1],13,136,CREAM);text(TX_NEXT,207,102,GOLD);}
 if(!game_shop_draw()&&display_state==PAUSE)draw_journal_panel();
 if(quickparty_open)quickparty_draw();

 if(display_state==EVOLVE_CONFIRM)progression_draw_confirm();
 if(display_state==EVOLVE_ANIM)progression_draw_evolution();
 if(game_state==DEAD){box(22,60,196,57);centered(TX_DEAD,69,GOLD);centered(TX_RETRY,94,CREAM);}
 if(game_state==WIN){copy_bg(BACK_TITLE);box(17,40,206,103);centered(TX_COMPLETE,49,GOLD);centered(TX_THANKS,75,CREAM);centered(TX_C_POSTGAME,122,CREAM);centered(TX_C_FINAL_SMALL,149,GOLD);}
 game_shop_draw_reward();game_draw_save_badge();draw_save_failure_notice();
#ifndef GAME_HOST_TEST
 render_card_cycles=cycle_now()-profile_started;
#endif
}
