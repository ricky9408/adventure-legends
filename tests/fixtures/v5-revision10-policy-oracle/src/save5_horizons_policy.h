#ifndef EMBERBOND_SAVE5_HORIZONS_POLICY_H
#define EMBERBOND_SAVE5_HORIZONS_POLICY_H
/* Content8 only. No wire extension or serialized attempt proof. */
typedef struct HorizonsEvidence { Save4U8 count[12], trained, invalid; } HorizonsEvidence;
static int horizons_quest_campaign_validate(const Save5Quests *);
static int horizons_campaign_validate(const CampaignSave *,const Save5Quests *);
static void horizons_instance_evidence(HorizonsEvidence *,const CreatureInstance *);
static int horizons_sources_validate(const Save5Quests *,const Save4U8 *,const HorizonsEvidence *);
static int horizons_roster_sources_validate(const Save5Quests *,const CreatureRoster *);
static int horizons_objective_validate(const Save5Quests *,unsigned);
#endif
