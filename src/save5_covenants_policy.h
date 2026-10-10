#ifndef EMBERBOND_SAVE5_COVENANTS_POLICY_H
#define EMBERBOND_SAVE5_COVENANTS_POLICY_H
/* Current9 only. Wire5 retains all offsets and reserved bytes. */
typedef struct CovenantsEvidence { Save4U8 count[8]; } CovenantsEvidence;
static int covenants_objective_validate(const Save5Quests*,unsigned);
static int covenants_quest_campaign_validate(const CampaignSave*,const Save5Quests*);
static int covenants_campaign_validate(const CampaignSave*,const Save5Quests*);
static void covenants_instance_evidence(CovenantsEvidence*,const CreatureInstance*);
static int covenants_sources_validate(const Save5Quests*,const Save4U8*,const CovenantsEvidence*);
static int covenants_roster_sources_validate(const Save5Quests*,const CreatureRoster*);
#endif
