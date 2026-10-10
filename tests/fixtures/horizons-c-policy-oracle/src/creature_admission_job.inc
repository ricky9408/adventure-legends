/* Frame-bounded admission against one exclusively owned immutable snapshot.
 * Save5 owns that snapshot and must keep it unchanged until commit/cancel.
 * This module independently validates every roster record; a caller cannot
 * pass a trusted-valid flag. The private singleton and generation token avoid
 * forged/stale cursor completion, while exact comparison rejects live changes.
 * No heap, full-save copy, roster copy, history-derived individual, or IWRAM. */
typedef struct CreatureAdmissionJobState {
    const CreatureRoster *snapshot;
    CreatureU32 token;
    CreatureU8 counts[60], masks[60];
    CreatureAdmission detail;
    CreatureU16 cursor, stories;
    CreatureU8 target, slot, phase, status;
} CreatureAdmissionJobState;
static CreatureAdmissionJobState admission_job;
static CreatureU32 admission_job_serial;
typedef char CreatureAdmissionJobBound[(sizeof(CreatureAdmissionJobState) <= 192) ? 1 : -1];

unsigned creatures_admission_job_bytes(void) {
    return (unsigned)sizeof(admission_job) + (unsigned)sizeof(admission_job_serial);
}
void creatures_admission_job_cancel(void) {
    clear_bytes(&admission_job, sizeof(admission_job));
}
CreatureU32 creatures_admission_job_begin(const CreatureRoster *snapshot,
    unsigned target, unsigned slot) {
    creatures_admission_job_cancel();
    if (!snapshot || !creatures_form(target) ||
        (slot != CREATURE_EMPTY_SLOT && slot >= CREATURE_ROSTER_CAPACITY) ||
        admission_job_serial == U32_MAX_VALUE) return 0;
    ++admission_job_serial;
    admission_job.snapshot = snapshot; admission_job.token = admission_job_serial;
    admission_job.target = (CreatureU8)target; admission_job.slot = (CreatureU8)slot;
    admission_job.status = CREATURE_ADMISSION_INVALID;
    return admission_job.token;
}
static int admission_job_fail(void) {
    admission_job.phase = 2;
    admission_job.status = CREATURE_ADMISSION_INVALID;
    clear_bytes(&admission_job.detail, sizeof(admission_job.detail));
    return 1;
}
static int admission_job_header_valid(void) {
    const CreatureRoster *r = admission_job.snapshot;
    unsigned i, bit;
    if (!r->next_instance_id || !party_validate(r, 0, 0) ||
        !creatures_terminal_family(admission_job.target)) return 0;
    if (admission_job.slot != CREATURE_EMPTY_SLOT &&
        (!r->instances[admission_job.slot].form_id ||
         !creatures_evolution_to(r->instances[admission_job.slot].form_id, admission_job.target))) return 0;
    for (i = 0; i < sizeof(r->seen); ++i) {
        unsigned bits = r->seen[i];
        if (r->obtained[i] & (CreatureU8)~bits) return 0;
        for (bit = 0; bits; bits >>= 1, ++bit)
            if ((bits & 1u) && !creatures_form(i * 8u + bit + 1u)) return 0;
    }
    return 1;
}
static int admission_job_record_valid(unsigned slot) {
    const CreatureRoster *r = admission_job.snapshot;
    const CreatureInstance *c = &r->instances[slot];
    unsigned j, legacy;
    if (!c->form_id) return instance_is_zero(c) && !r->expedition_bond[slot];
    if (!creatures_instance_validate(c) || r->expedition_bond[slot] > 10 ||
        c->instance_id >= r->next_instance_id || !bit_get(r->obtained, c->form_id - 1u)) return 0;
    for (j = 0; j < slot; ++j)
        if (c->instance_id == r->instances[j].instance_id) return 0;
    if (c->flags & CREATURE_STORY_LOCKED) {
        legacy = creatures_legacy_spirit(c->form_id);
        if (legacy >= 4 || (admission_job.stories & (1u << legacy)) || !bit_get(r->rewards, legacy)) return 0;
        admission_job.stories |= (CreatureU16)(1u << legacy);
    }
    return slot == admission_job.slot ||
        coverage_add(&admission_job.detail.before, admission_job.counts, admission_job.masks, c->form_id);
}
static int admission_job_finish(void) {
    CreatureAdmission *result = &admission_job.detail;
    unsigned family, saved_count, saved_mask;
    if (admission_job.stories != (admission_job.snapshot->rewards[0] & 15u)) return admission_job_fail();
    coverage_finish(&result->before); result->after = result->before;
    if (admission_job.slot != CREATURE_EMPTY_SLOT) {
        family = creatures_terminal_family(admission_job.target);
        if (!family) return admission_job_fail();
        saved_count = admission_job.counts[family - 1u]; saved_mask = admission_job.masks[family - 1u];
        if (!coverage_add(&result->before, admission_job.counts, admission_job.masks,
                          admission_job.snapshot->instances[admission_job.slot].form_id)) return admission_job_fail();
        coverage_finish(&result->before);
        admission_job.counts[family - 1u] = (CreatureU8)saved_count;
        admission_job.masks[family - 1u] = (CreatureU8)saved_mask;
    } else if (result->before.occupied == CREATURE_ROSTER_CAPACITY) {
        admission_job.status = CREATURE_ADMISSION_FULL; admission_job.phase = 2; return 1;
    }
    if (!coverage_add(&result->after, admission_job.counts, admission_job.masks,
                      admission_job.target)) return admission_job_fail();
    coverage_finish(&result->after);
    if (result->after.admission_safe) admission_job.status = CREATURE_ADMISSION_READY;
    else if (!result->before.admission_safe && result->after.excess <= result->before.excess &&
             result->after.viable >= result->before.viable)
        admission_job.status = CREATURE_ADMISSION_GRANDFATHERED_READY;
    else admission_job.status = admission_job.slot == CREATURE_EMPTY_SLOT ?
        CREATURE_ADMISSION_RESERVED : CREATURE_ADMISSION_COVERAGE_LOSS;
    admission_job.phase = 2; return 1;
}
int creatures_admission_job_step(CreatureU32 token, unsigned records) {
    if (!token || token != admission_job.token || !admission_job.snapshot) return -1;
    if (!records || records > CREATURE_ADMISSION_JOB_RECORDS_MAX) return -1;
    if (admission_job.phase == 2) return 1;
    if (!admission_job.phase) {
        if (!admission_job_header_valid()) return admission_job_fail();
        admission_job.phase = 1;
    }
    while (records-- && admission_job.cursor < CREATURE_ROSTER_CAPACITY) {
        if (!admission_job_record_valid(admission_job.cursor)) return admission_job_fail();
        ++admission_job.cursor;
    }
    return admission_job.cursor == CREATURE_ROSTER_CAPACITY ? admission_job_finish() : 0;
}
enum CreatureAdmissionStatus creatures_admission_job_result(CreatureU32 token,
    CreatureAdmission *detail) {
    if (detail) clear_bytes(detail, sizeof(*detail));
    if (!token || token != admission_job.token || admission_job.phase != 2) return CREATURE_ADMISSION_INVALID;
    if (detail) {
        unsigned i;
        CreatureU8 *out = (CreatureU8 *)(void *)detail;
        const CreatureU8 *in = (const CreatureU8 *)(const void *)&admission_job.detail;
        for (i = 0; i < sizeof(*detail); ++i) out[i] = in[i];
    }
    return (enum CreatureAdmissionStatus)admission_job.status;
}
static int admission_job_matches(const CreatureRoster *live) {
    unsigned i;
    if (!live || !admission_job.snapshot || live == admission_job.snapshot) return 0;
#if defined(__GNUC__) || defined(__clang__)
    {
        const CreatureAliasU32 *a = (const CreatureAliasU32 *)(const void *)live;
        const CreatureAliasU32 *b = (const CreatureAliasU32 *)(const void *)admission_job.snapshot;
        for (i = 0; i < sizeof(*live) / sizeof(*a); ++i) if (a[i] != b[i]) return 0;
    }
#else
    {
        const CreatureU8 *a = (const CreatureU8 *)(const void *)live;
        const CreatureU8 *b = (const CreatureU8 *)(const void *)admission_job.snapshot;
        for (i = 0; i < sizeof(*live); ++i) if (a[i] != b[i]) return 0;
    }
#endif
    return 1;
}
enum CreatureAdmissionStatus creatures_admission_job_commit_grant(CreatureU32 token,
    CreatureRoster *live, unsigned level, unsigned bond, unsigned flags,
    unsigned reward, unsigned *out_slot) {
    enum CreatureAdmissionStatus status = creatures_admission_job_result(token, 0);
    unsigned target = admission_job.target, slot, legacy;
    int matching = token && token == admission_job.token && admission_job.phase == 2 &&
        admission_job.slot == CREATURE_EMPTY_SLOT && admission_job_matches(live);
    if (out_slot) *out_slot = CREATURE_EMPTY_SLOT;
    /* An attempt consumes the token, including stale/denied attempts. */
    if (token == admission_job.token) creatures_admission_job_cancel();
    if (!matching || status == CREATURE_ADMISSION_INVALID || level < 1 || level > 50 || bond > 100 ||
        (flags & ~(CREATURE_STORY_LOCKED | CREATURE_FAVORITE)) || reward > 128) return CREATURE_ADMISSION_INVALID;
    legacy = creatures_legacy_spirit(target);
    if (flags & CREATURE_STORY_LOCKED) {
        if (legacy >= 4 || reward != legacy + 1u) return CREATURE_ADMISSION_INVALID;
    } else if (reward && reward <= 4) return CREATURE_ADMISSION_INVALID;
    /* Match the synchronous API's receipt/identity precedence. */
    if (reward && bit_get(live->rewards, reward - 1u)) return CREATURE_ADMISSION_ALREADY_CLAIMED;
    if (live->next_instance_id == U32_MAX_VALUE) return CREATURE_ADMISSION_ID_EXHAUSTED;
    if (!creatures_admission_allowed(status)) return status;
    slot = grant_validated(live, target, level, bond, flags, reward);
    if (slot == CREATURE_EMPTY_SLOT) return CREATURE_ADMISSION_INVALID;
    if (out_slot) *out_slot = slot;
    return status;
}
unsigned creatures_admission_job_commit_evolution(CreatureU32 token,
    CreatureRoster *live, unsigned context, int sanctuary, int confirmed) {
    enum CreatureAdmissionStatus admission = creatures_admission_job_result(token, 0);
    unsigned slot = admission_job.slot, target = admission_job.target, status;
    CreatureInstance candidate;
    const CreatureForm *form;
    int matching = token && token == admission_job.token && admission_job.phase == 2 &&
        slot < CREATURE_ROSTER_CAPACITY && admission_job_matches(live);
    if (token == admission_job.token) creatures_admission_job_cancel();
    if (!matching || admission == CREATURE_ADMISSION_INVALID) return CREATURE_EVOLVE_INVALID;
    status = creatures_can_evolve_to(&live->instances[slot], target, context, sanctuary);
    if (status != CREATURE_EVOLVE_READY) return status;
    if (!confirmed) return CREATURE_EVOLVE_DEFERRED;
    if (!creatures_admission_allowed(admission)) return admission == CREATURE_ADMISSION_COVERAGE_LOSS ?
        CREATURE_EVOLVE_COLLECTION_RESERVED : CREATURE_EVOLVE_INVALID;
    form = creatures_form(target); if (!form) return CREATURE_EVOLVE_INVALID;
    candidate = live->instances[slot]; candidate.form_id = form->id; candidate.polarity = form->polarity;
    if (!creatures_instance_validate(&candidate)) return CREATURE_EVOLVE_INVALID;
    live->instances[slot] = candidate;
    bit_set(live->seen, target - 1u); bit_set(live->obtained, target - 1u);
    return CREATURE_EVOLVE_READY;
}
