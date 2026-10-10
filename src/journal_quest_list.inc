/* Visible quest lists retain the original per-region selection references. */
extern unsigned region_game_journal_selection;
static const int region_entries[11]={TX_RG_Q0,TX_RG_Q1,TX_RG_Q2,TX_RG_Q3,TX_RG_Q4,TX_RG_Q5,TX_RG_Q6,TX_RG_Q7,TX_RG_Q8,TX_RG_Q9,TX_RG_Q10};
extern unsigned north_game_journal_selection;
static const int north_entries[11]={TX_NT_Q11,TX_NT_Q12,TX_NT_Q13,TX_NT_Q14,TX_NT_Q15,TX_NT_Q16,TX_NT_Q17,TX_NT_Q18,TX_NT_Q19,TX_NT_Q20,TX_NT_Q21};
extern unsigned south_game_journal_selection;
static const int south_entries[18]={TX_ST_Q22,TX_ST_Q23,TX_ST_Q24,TX_ST_Q25,TX_ST_Q26,TX_ST_Q27,TX_ST_Q28,TX_ST_Q29,TX_ST_TRIAL0,TX_ST_TRIAL1,TX_ST_TRIAL2,TX_ST_TRIAL3,TX_ST_TRIAL4,TX_ST_TRIAL5,TX_ST_TRIAL6,TX_ST_TRIAL7,TX_ST_TRIAL8,TX_ST_TRIAL9};
extern unsigned magma_game_journal_selection;
static const int magma_entries[24]={TX_MG_Q30,TX_MG_Q31,TX_MG_Q32,TX_MG_Q33,TX_MG_Q34,TX_MG_Q35,TX_MG_Q36,TX_MG_Q37,TX_MG_DISCOVERY_TITLE,TX_MG_TRIAL0,TX_MG_TRIAL1,TX_MG_TRIAL2,TX_MG_TRIAL3,TX_MG_TRIAL4,TX_MG_TRIAL5,TX_MG_TRIAL6,TX_MG_TRIAL7,TX_MG_TRIAL8,TX_MG_TRIAL9,TX_MG_TRIAL10,TX_MG_TRIAL11,TX_MG_TRIAL12,TX_MG_TRIAL13,TX_MG_TRIAL14};
extern unsigned underwater_game_journal_selection;
static const int underwater_entries[24]={TX_UW_Q38,TX_UW_Q39,TX_UW_Q40,TX_UW_Q41,TX_UW_Q42,TX_UW_Q43,TX_UW_Q44,TX_UW_Q45,TX_UW_TRIAL0,TX_UW_TRIAL1,TX_UW_TRIAL2,TX_UW_TRIAL3,TX_UW_TRIAL4,TX_UW_TRIAL5,TX_UW_TRIAL6,TX_UW_TRIAL7,TX_UW_TRIAL8,TX_UW_TRIAL9,TX_UW_TRIAL10,TX_UW_TRIAL11,TX_UW_TRIAL12,TX_UW_TRIAL13,TX_UW_TRIAL14,TX_UW_TRIAL15};
extern unsigned return_game_journal_selection;
static const int return_entries[21]={TX_RT_Q46,TX_RT_Q47,TX_RT_Q48,TX_RT_Q49,TX_RT_Q50,TX_RT_Q51,TX_RT_Q52,TX_RT_Q53,TX_RT_TRIAL0,TX_RT_TRIAL1,TX_RT_TRIAL2,TX_RT_TRIAL3,TX_RT_TRIAL4,TX_RT_TRIAL5,TX_RT_TRIAL6,TX_RT_TRIAL7,TX_RT_TRIAL8,TX_RT_TRIAL9,TX_RT_TRIAL10,TX_RT_TRIAL11,TX_RT_TRIAL12};
extern unsigned horizons_game_journal_selection;
static const int horizons_entries[10]={TX_HZ_Q54,TX_HZ_Q55,TX_HZ_Q56,TX_HZ_Q57,TX_HZ_Q58,TX_HZ_Q59,TX_HZ_T41,TX_HZ_T42,TX_HZ_T43,TX_HZ_T44};
extern unsigned covenants_game_journal_selection;
static const int covenants_entries[12]={TX_CV_Q60,TX_CV_Q61,TX_CV_Q62,TX_CV_Q63,TX_CV_ROOM70,TX_CV_ROOM71,TX_CV_ROOM72,TX_CV_ROOM73,TX_CV_ROOM74,TX_CV_ROOM75,TX_CV_ROOM76,TX_CV_ROOM77};
static const struct QuestList {const int*names;unsigned*selection;unsigned count;int title;} quest_lists[8]={
{region_entries,&region_game_journal_selection,11,TX_RG_JOURNAL},
{north_entries,&north_game_journal_selection,11,TX_NT_JOURNAL},
{south_entries,&south_game_journal_selection,18,TX_ST_JOURNAL},
{magma_entries,&magma_game_journal_selection,24,TX_MG_JOURNAL},
{underwater_entries,&underwater_game_journal_selection,24,TX_UW_JOURNAL},
{return_entries,&return_game_journal_selection,21,TX_RT_JOURNAL},
{horizons_entries,&horizons_game_journal_selection,10,TX_HZ_JOURNAL},
{covenants_entries,&covenants_game_journal_selection,12,TX_CV_JOURNAL},
};
