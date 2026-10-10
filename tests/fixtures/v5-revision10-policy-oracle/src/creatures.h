#ifndef ADVENTURE_LEGENDS_CREATURES_H
#define ADVENTURE_LEGENDS_CREATURES_H
/* Freestanding C99. Only explicit byte encoding in save5 may persist these
 * records. All definitions and lookups live in ROM; no malloc. Bounded admission jobs own one explicitly documented private cursor. */
typedef unsigned char CreatureU8;
typedef unsigned short CreatureU16;
typedef unsigned int CreatureU32;
typedef CreatureU8 FormId;
typedef CreatureU16 CreatureCapabilityId;

enum {
    CREATURE_FORM_CAPACITY = 128, CREATURE_FAMILY_CAPACITY = 60,
    CREATURE_ENABLED_COUNT = 128,
    CREATURE_LEARNSET_COUNT = 209, CREATURE_EVOLUTION_COUNT = 68,
    CREATURE_ABILITY_COUNT = 128, CREATURE_LEGACY_COUNT = 4,
    CREATURE_ROSTER_CAPACITY = 160, CREATURE_PARTY_CAPACITY = 4,
    CREATURE_EMPTY_SLOT = 255, CREATURE_MAX_LEVEL = 50,
    CREATURE_MAX_BOND = 100, CREATURE_EXPEDITION_BOND_CAP = 10,
    CREATURE_XP_CAP = 470596,
    CREATURE_OCCUPIED = 1, CREATURE_STORY_LOCKED = 2, CREATURE_FAVORITE = 4,
    CREATURE_FLAGS_MASK = 7,
    CREATURE_GROVE_CLEAR = 1, CREATURE_SKY_CLEAR = 2, CREATURE_CORE_CLEAR = 4,
    /* Evolution-context namespace, NOT CampaignSave.chapter_flags. Bit 3 in
     * CampaignSave means ENDING_SEEN and must never be passed through here.
     * Supply (chapter_flags & CREATURE_EVOLUTION_CHAPTER_MASK) |
     *         (quest2_claimed ? CREATURE_REED_RESTORED : 0).
     * Northern context is separately derived: NORTH_HARBOR_READY requires both
     * quests 11 and 13 claimed; COUNTERWORKS_STABLE requires quest 21 claimed.
     * Legacy migration/story APIs still accept original campaign flags. */
    CREATURE_EVOLUTION_CHAPTER_MASK = 7, CREATURE_REED_RESTORED = 8,
    CREATURE_NORTH_HARBOR_READY = 16, CREATURE_COUNTERWORKS_STABLE = 32,
    CREATURE_SOUTH_READY = 64, CREATURE_SUNWELL_OPEN = 128,
    CREATURE_MAGMA_READY = 256, CREATURE_CALDERA_OPEN = 512,
    CREATURE_UNDERWATER_READY = 1024, CREATURE_PALINODE_OPEN = 2048,
    CREATURE_RETURN_READY = 4096, CREATURE_RETURN_COMPLETE = 8192,
    CREATURE_HORIZONS_READY = 16384, CREATURE_EVOLUTION_CONTEXT_MASK = 32767,
    CREATURE_CONTENT_REVISION = 10, CREATURE_ROUTE_REQUIREMENTS_MAX = 8,
    CREATURE_UNDERWATER_FIRST_FORM = 49, CREATURE_UNDERWATER_LAST_FORM = 72,
    CREATURE_UNDERWATER_FIRST_FAMILY = 17, CREATURE_UNDERWATER_FAMILY_COUNT = 8,
    /* Explicit target choice uses evolution_at(base, choice); no first-edge fallback. */
    CREATURE_BRANCH_CHOICE_FIRST = 0, CREATURE_BRANCH_CHOICE_SECOND = 1,
    CREATURE_UNDERWATER_TRIAL_FIRST = 1, CREATURE_UNDERWATER_TRIAL_SECOND = 2,
    CREATURE_TRIAL_HEARTH = 1, CREATURE_TRIAL_CANOPY = 2,
    CREATURE_TRIAL_WIND_LOOM = 4, CREATURE_TRIAL_AMBER_ARCH = 8,
    CREATURE_TRIAL_PAIRED_POOLS = 16,
    CREATURE_TRIAL_TENSION_ROOF = 32, CREATURE_TRIAL_DRY_LEDGER = 64,
    CREATURE_TRIAL_FRAGILE_CARGO = 128, CREATURE_TRIAL_BALANCED_REACH = 256,
    CREATURE_TRIAL_COMPASS_ROUND = 512, CREATURE_TRIAL_MASK = 1023,
    CREATURE_EVENT_CAPACITY = 512, CREATURE_FIELD_EVENT_BASE = 384,
    CREATURE_NICKNAME_MAX = 0 /* Named presets are not authored yet. */
};
/* Wuxing phases and polarity are independent axes. Wind is an ability. */
enum CreaturePhase {
    CREATURE_WOOD = 0, CREATURE_FIRE, CREATURE_EARTH,
    CREATURE_METAL, CREATURE_WATER, CREATURE_PHASE_COUNT
};
enum CreaturePolarity { CREATURE_YIN = 0, CREATURE_YANG = 1 };
enum FieldCapability {
    FIELD_BREAK_CRACK = 1u << 0, FIELD_BURN_THORNS = 1u << 1,
    FIELD_DRAW_ORE = 1u << 2, FIELD_DRIVE_SAIL = 1u << 3,
    FIELD_EARTH_SOCKET = 1u << 4, FIELD_EXPOSE_FIRE = 1u << 5,
    FIELD_EXPOSE_STONE = 1u << 6, FIELD_EXPOSE_WIND = 1u << 7,
    FIELD_FILL_BASIN = 1u << 8, FIELD_FIRE_SOCKET = 1u << 9,
    FIELD_GROW_BRIDGE = 1u << 10, FIELD_GROW_ROOTS = 1u << 11,
    FIELD_IGNITE = 1u << 12, FIELD_LINK_POOLS = 1u << 13,
    FIELD_PRESS_WEIGHT = 1u << 14, FIELD_REVEAL_CURRENT = 1u << 15,
    FIELD_TUNE_LATCH = 1u << 16, FIELD_TURN_VANE = 1u << 17,
    FIELD_UNCAP_WELL = 1u << 18, FIELD_WIND_SOCKET = 1u << 19,
    FIELD_WOOD_SOCKET = 1u << 20,
    FIELD_REEL_LOAD = 1u << 21, FIELD_STORE_HEAT = 1u << 22,
    FIELD_FLOAT_LOAD = 1u << 23, FIELD_ALIGN_RAIL = 1u << 24,
    FIELD_REFRACT_BEAM = 1u << 25,
    FIELD_ECHO_OUTLINE = 1u << 26, FIELD_SHIFT_BALLAST = 1u << 27,
    FIELD_INSCRIBE_TRACE = 1u << 28, FIELD_UNFOLD_SCREEN = 1u << 29
};
#define FIELD_HOMURA (FIELD_IGNITE | FIELD_BURN_THORNS | FIELD_FIRE_SOCKET | FIELD_EXPOSE_FIRE)
#define FIELD_MIDORI (FIELD_GROW_BRIDGE | FIELD_GROW_ROOTS | FIELD_WOOD_SOCKET)
#define FIELD_FUURI (FIELD_TURN_VANE | FIELD_DRIVE_SAIL | FIELD_WIND_SOCKET | FIELD_EXPOSE_WIND)
#define FIELD_KOHAKU (FIELD_BREAK_CRACK | FIELD_PRESS_WEIGHT | FIELD_UNCAP_WELL | FIELD_EARTH_SOCKET | FIELD_EXPOSE_STONE)
#define FIELD_DEWSPINDLE (FIELD_FILL_BASIN | FIELD_REVEAL_CURRENT)
#define FIELD_TIDEWHEEL (FIELD_DEWSPINDLE | FIELD_LINK_POOLS)
#define FIELD_CHIMECLASP (FIELD_TUNE_LATCH | FIELD_DRAW_ORE)

typedef struct CreatureInstance {
    CreatureU8 form_id, flags, level, bond;
    CreatureU32 xp, instance_id;
    CreatureU16 nickname_id, trial_flags;
    CreatureU8 equipped[2], polarity, selected_command;
    CreatureU32 cosmetic_seed;
} CreatureInstance;

typedef struct CreatureRoster {
    CreatureInstance instances[CREATURE_ROSTER_CAPACITY];
    CreatureU8 party[CREATURE_PARTY_CAPACITY];
    CreatureU8 selected_party; /* party position, not roster index */
    CreatureU32 next_instance_id; /* never zero; UINT_MAX means exhausted */
    CreatureU8 seen[16], obtained[16], rewards[16];
    CreatureU8 expedition_bond[CREATURE_ROSTER_CAPACITY];
    CreatureU8 expedition_events[64];
    CreatureU8 lifetime_field_aid[16];
} CreatureRoster;

typedef struct CreatureLearn { CreatureU8 level, ability_id; } CreatureLearn;
/* Exactly 32 bytes, no pointers, no implicit catalog/encounter fallback. */
typedef struct CreatureForm {
    CreatureU8 id, family, phase, polarity, tier, rarity;
    CreatureU8 stats[5], signature_ability;
    CreatureU32 field_caps;
    CreatureU16 name_id, learnset_offset;
    CreatureU8 learnset_count, evolution_count;
    CreatureU16 evolution_offset;
    CreatureU32 sprite_offset;
    CreatureU16 portrait_id, flags;
} CreatureForm;
typedef struct CreatureEvolution {
    CreatureU8 from, to, min_level, min_bond;
    /* chapter_flags stores evolution context bits, including REED_RESTORED;
     * the field name/layout is retained for source compatibility. */
    CreatureU16 trial_flag, chapter_flags;
} CreatureEvolution;
typedef struct CreatureAbility {
    CreatureU8 id, phase;
    CreatureU16 cooldown_updates;
    CreatureU32 field_caps;
} CreatureAbility;
extern const CreatureForm creature_forms[CREATURE_ENABLED_COUNT];
extern const CreatureLearn creature_learnsets[CREATURE_LEARNSET_COUNT];
extern const CreatureEvolution creature_evolutions[CREATURE_EVOLUTION_COUNT];
extern const CreatureAbility creature_abilities[CREATURE_ABILITY_COUNT];
extern const FormId creature_legacy_forms[CREATURE_LEGACY_COUNT];
/* ROM sparse lookup indexes store row+1; zero is absent. Identities remain
 * the explicit row keys. Mismatched/out-of-range maps fail closed. */
extern const CreatureU8 creature_form_index[CREATURE_FORM_CAPACITY + 1];
extern const CreatureU8 creature_ability_index[256];
extern const CreatureU8 creature_incoming_evolution_index[CREATURE_FORM_CAPACITY + 1];

/* Enabled core data is not proof of a native acquisition/art/ability route.
 * All128 authored rows are enabled. Their controller acquisition remains a
 * separate acceptance gate. Southern rows are
 * development data until separate art, handlers and native acquisition pass. */
int creatures_form_id_valid(unsigned form_id);
const CreatureForm *creatures_form(unsigned form_id);
/* Checked ROM indexes allow sparse/unordered form/family/ability IDs.
 * Only explicit enabled rows resolve. Ability12 is Stilltide; command121 remains Cymbalop. */
const CreatureAbility *creatures_ability(unsigned ability_id);
/* Frozen legacy family trial mask, or zero for Southern/no trial/unknown.
 * Never derive a trial from family_id or an enabled table index. */
unsigned creatures_family_trial(unsigned form_id);
/* Exact immutable historical snapshots for revisions1..9; revision10 uses current policy. Zero mask
 * means no permitted trial, not permission to award one. */
/* Historical lookups never resolve live catalog rows. Unknown family returns0;
 * unknown/non-story legacy mapping returns255. No migration mutates evidence. */
unsigned creatures_family_revision(unsigned form_id, unsigned revision);
unsigned creatures_legacy_spirit_revision(unsigned form_id, unsigned revision);
int creatures_form_allowed_revision(unsigned form_id, unsigned content_revision);
int creatures_command_learned_revision(unsigned form_id, unsigned level,
                                       unsigned ability_id, unsigned content_revision);
/* Current masks are per-form:31/34 cannot retain key2 before32/35. */
unsigned creatures_trial_allowed_mask(unsigned form_id, unsigned content_revision);
int creatures_instance_validate_revision(const CreatureInstance *instance,
                                          unsigned content_revision);
const char *creatures_name(unsigned form_id);
const char *creatures_ability_name(unsigned ability_id);
unsigned creatures_legacy_spirit(unsigned form_id); /* 255 if unavailable */
CreatureU32 creatures_capabilities(unsigned form_id);
int creatures_has_capability(unsigned form_id, CreatureU32 needed);
/* Stable keys 1..30 map explicitly to reviewed bits 0..29. All other keys
 * are disabled until authored. No query shifts by an unchecked key. */
int creatures_supports_capability(unsigned form_id, unsigned capability_id);
int creatures_party_supports_capability(const CreatureRoster *roster, unsigned capability_id);
int creatures_party_set_requirements(CreatureRoster *roster, const CreatureU8 party[4],
                                      const CreatureCapabilityId *required, unsigned required_count);
unsigned creatures_phase_multiplier_q8(unsigned attacker, unsigned defender); /* 0 invalid */
unsigned creatures_generated_phase(unsigned phase); /* 255 invalid */
int creatures_catalog_validate(void);

CreatureU32 creatures_xp_threshold(unsigned level); /* UINT_MAX invalid */
unsigned creatures_level_for_xp(CreatureU32 xp); /* saturates at 50 */
int creatures_command_learned(unsigned form_id, unsigned level, unsigned ability_id);
int creatures_instance_validate(const CreatureInstance *instance);
int creatures_roster_validate(const CreatureRoster *roster);
int creatures_roster_validate_revision(const CreatureRoster *roster, unsigned revision);
int creatures_party_validate(const CreatureRoster *roster);
void creatures_roster_init(CreatureRoster *roster);
unsigned creatures_roster_count(const CreatureRoster *roster);
CreatureU32 creatures_party_capabilities(const CreatureRoster *roster);
int creatures_party_set(CreatureRoster *roster, const CreatureU8 party[4], CreatureU32 required_caps);
/* Legacy/staging primitive. NOT an unguarded gameplay acquisition permission.
 * Forward gameplay callers must use creatures_grant_admitted or check the
 * prospective query in the same atomic transaction before this inner operation.
 * Adds an enabled form; callers author acquisition gates. Returns slot or 255.
 * reward_id 1..4 is reserved for matching story families; 5..128 is a
 * general one-time transaction; 0 means repeatable. At capacity
 * nothing changes, including the reward ledger. Story grants use the API below.
 * Regional recruits are ordinary owned instances (flags 0), never STORY_LOCKED.
 * Full parties are never replaced; a new companion remains in storage.
 * Quest 2 authors grant(13, 10, 20, 0, 5); quest 3 authors reward 6/form 16.
 * This API does not mark quests complete or verify the external recruit gate. */
enum {
    CREATURE_TERMINAL_OPPORTUNITIES = 72,
    CREATURE_EXTRA_COPY_BUDGET = 88
};
/* Immutable final topology metadata includes disabled forms only for capacity
 * reservation; it never enables their acquisition, commands or evolution. */
typedef struct CreatureTerminalPolicy { CreatureU8 family, terminal_mask; } CreatureTerminalPolicy;
extern const CreatureTerminalPolicy creature_terminal_policy[129];
unsigned creatures_terminal_family(unsigned form_id); /* 0 invalid */
unsigned creatures_terminal_mask(unsigned form_id);   /* 1/2/3; 0 invalid */
typedef struct CreatureCoverage {
    CreatureU16 occupied, viable, excess, free_slots, missing_opportunities;
    CreatureU16 admission_safe;
} CreatureCoverage;
typedef struct CreatureAdmission {
    CreatureCoverage before, after;
} CreatureAdmission;
enum CreatureAdmissionStatus {
    CREATURE_ADMISSION_READY = 0,
    CREATURE_ADMISSION_GRANDFATHERED_READY,
    CREATURE_ADMISSION_INVALID,
    CREATURE_ADMISSION_FULL,
    CREATURE_ADMISSION_RESERVED,
    CREATURE_ADMISSION_COVERAGE_LOSS,
    CREATURE_ADMISSION_ALREADY_CLAIMED,
    CREATURE_ADMISSION_ID_EXHAUSTED
};
/* Read-only, bounded160-record scans. Invalid output is zeroed. Optional detail
 * exposes candidate coverage without copying a roster; no history bits count as
 * individuals. These are gameplay guards, NEVER save-validity requirements.
 * A legal over-budget save remains loadable/saveable; new actions can only be
 * nonworsening and cannot promise recovery of all future terminal outcomes. */
int creatures_collection_coverage(const CreatureRoster *roster, CreatureCoverage *out);
enum CreatureAdmissionStatus creatures_admission_query_grant(
    const CreatureRoster *roster, unsigned form_id, CreatureAdmission *detail);
enum CreatureAdmissionStatus creatures_admission_query_evolution(
    const CreatureRoster *roster, unsigned roster_slot, unsigned target_form,
    CreatureAdmission *detail);
/* Additional source/quest authorization belongs to the caller. receipt retries
 * return ALREADY_CLAIMED before admission. out_slot is255 except on a new grant.
 * Both READY statuses are successful; every other result leaves all bytes intact. */
enum CreatureAdmissionStatus creatures_grant_admitted(
    CreatureRoster *roster, unsigned form_id, unsigned level, unsigned bond,
    unsigned flags, unsigned reward_id, unsigned *out_slot);
int creatures_admission_allowed(enum CreatureAdmissionStatus status);

/* Single frame-bounded operation; snapshot is exclusively owned and immutable
 * through completion. Begin supersedes the previous job and returns a fresh
 * token (0 invalid). No caller-supplied validation flags. Step performs actual
 * full roster validation and coverage, at most four records per call including
 * each record's bounded prior-ID checks. It returns -1 invalid token/budget,
 * 0 pending, 1 complete. Result is INVALID until complete. Commit requires a
 * distinct live roster byte-identical to the snapshot and consumes the token
 * once. Caller separately validates its typed quest/source/attempt/context and
 * all non-roster state, and cancels on load, death, scene change or decline.
 * No additional full-save or roster copy, and synchronous APIs stay unchanged. */
enum { CREATURE_ADMISSION_JOB_ERROR = -1, CREATURE_ADMISSION_JOB_PENDING = 0,
       CREATURE_ADMISSION_JOB_COMPLETE = 1, CREATURE_ADMISSION_JOB_RECORDS_MAX = 4 };
unsigned creatures_admission_job_bytes(void);
CreatureU32 creatures_admission_job_begin(const CreatureRoster *snapshot,
    unsigned target_form, unsigned replaced_slot); /*255 means grant*/
int creatures_admission_job_step(CreatureU32 token, unsigned records);
enum CreatureAdmissionStatus creatures_admission_job_result(CreatureU32 token,
    CreatureAdmission *detail);
void creatures_admission_job_cancel(void);
enum CreatureAdmissionStatus creatures_admission_job_commit_grant(CreatureU32 token,
    CreatureRoster *live, unsigned level, unsigned bond, unsigned flags,
    unsigned reward_id, unsigned *out_slot);
unsigned creatures_admission_job_commit_evolution(CreatureU32 token,
    CreatureRoster *live, unsigned context, int sanctuary, int confirmed);


/* Original four-family story reward as one bounded, atomic operation. Uses
 * the admission cursor/snapshot contract above and its ordinary step/cancel.
 * Step validates every record; a story token cannot commit a normal grant or
 * evolution, nor can a normal token commit story rewards. Commit returns1 on
 * a valid once-only application (also when already satisfied),0 on refusal.
 * The caller proves boss/story context and exact non-roster state separately. */
CreatureU32 creatures_story_job_begin(const CreatureRoster *snapshot,unsigned chapter_flags);
int creatures_story_job_commit(CreatureU32 token,CreatureRoster *live);
void creatures_story_job_cancel(CreatureU32 token);

unsigned creatures_grant(CreatureRoster *roster, unsigned form_id, unsigned level,
                         unsigned bond, unsigned flags, unsigned reward_id);
unsigned creatures_grant_story(CreatureRoster *roster, unsigned legacy_spirit,
                               unsigned chapter_flags); /* slot or 255 */
int creatures_migrate_legacy(CreatureRoster *roster, unsigned chapter_flags,
                             unsigned legacy_spirit);
/* Explicit chapter catch-up compensation; never decreases existing XP/bond. */
int creatures_apply_story_floors(CreatureRoster *roster, unsigned chapter_flags);
int creatures_add_xp(CreatureInstance *instance, CreatureU32 amount);
int creatures_equip(CreatureInstance *instance, unsigned command_slot, unsigned ability_id);
int creatures_select_command(CreatureInstance *instance, unsigned command_slot);

/* Caller persists these fields in the shared quest/bond reservation. Departing
 * sanctuary starts a new expedition; resting alone never grants bond. */
void creatures_begin_expedition(CreatureRoster *roster);
enum CreatureCreditKind { CREATURE_CREDIT_ENCOUNTER = 0, CREATURE_CREDIT_FIELD_AID = 1,
                           CREATURE_CREDIT_PERSONAL_QUEST = 2 };
/* Events are 0..511. Field aids exclusively use 384..511, mapped to lifetime
 * first-aid bits 0..127. XP and bond go once to every valid current party member.
 * Return 1 credited, 0 already credited/no party, -1 invalid. Shared event bits
 * prevent swapping members to re-credit. Encounter/quest IDs must be <384. */
int creatures_credit_event(CreatureRoster *roster, unsigned event_id,
                           CreatureU32 xp, unsigned kind);
/* Legacy family trials 1/2/4/8 are unchanged. PAIRED_POOLS (16) belongs only
 * to Dewspindle/Tidewheel and is awarded by regional personal quest 4.
 * Zero, combined flags and trials for another family are rejected. The u16
 * save field is unchanged; new trials require explicit collision-free policy. */
int creatures_mark_trial(CreatureInstance *instance, unsigned trial_flag);
/* Qualifiers are full-width and checked before conversion; a shared wire bit
 * never grants a different family's trial. These APIs do not prove objectives. */
unsigned creatures_trial_mask_for_key(unsigned family_id, unsigned local_trial_id);
int creatures_mark_trial_qualified(CreatureInstance *instance, unsigned family_id,
                                   unsigned local_trial_id);
int creatures_has_trial_qualified(const CreatureInstance *instance, unsigned family_id,
                                  unsigned local_trial_id);

enum CreatureEvolutionStatus {
    CREATURE_EVOLVE_READY = 0, CREATURE_EVOLVE_INVALID,
    CREATURE_EVOLVE_NO_EDGE, CREATURE_EVOLVE_LEVEL,
    CREATURE_EVOLVE_BOND, CREATURE_EVOLVE_STORY,
    CREATURE_EVOLVE_TRIAL, CREATURE_EVOLVE_SANCTUARY,
    CREATURE_EVOLVE_DEFERRED, CREATURE_EVOLVE_AMBIGUOUS,
    CREATURE_EVOLVE_COLLECTION_RESERVED
};
/* Legacy lookup returns NULL for zero or multiple edges. Ordinal enumeration
 * is bounded and never substitutes an implicit first target for player choice. */
const CreatureEvolution *creatures_evolution(unsigned form_id);
unsigned creatures_evolution_count(unsigned form_id);
const CreatureEvolution *creatures_evolution_at(unsigned form_id, unsigned ordinal);
const CreatureEvolution *creatures_evolution_to(unsigned form_id, unsigned target_form);
unsigned creatures_can_evolve_to(const CreatureInstance *instance, unsigned target_form,
                                 unsigned evolution_context, int at_sanctuary);
/* Roster-aware preconfirmation query includes prospective terminal admission.
 * Instance-only queries above answer trial/context eligibility only. */
unsigned creatures_can_evolve_roster_to(const CreatureRoster *roster,
    unsigned roster_slot, unsigned target_form, unsigned evolution_context,
    int at_sanctuary);
unsigned creatures_evolve_to(CreatureRoster *roster, unsigned roster_slot, unsigned target_form,
                             unsigned evolution_context, int at_sanctuary, int confirmed);
/* READY ignores confirmation so UI can show eligibility; evolve requires it.
 * Deferring is explicit and leaves every roster byte unchanged. evolution_context
 * uses the separate masked namespace documented above, never raw campaign flags. */
unsigned creatures_can_evolve(const CreatureInstance *instance, unsigned evolution_context,
                              int at_sanctuary);
unsigned creatures_evolve(CreatureRoster *roster, unsigned roster_slot,
                          unsigned evolution_context, int at_sanctuary, int confirmed);
unsigned creatures_defer_evolution(const CreatureInstance *instance);
#endif
