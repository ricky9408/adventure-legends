/* Synthetic host bridge: current-r6 visit transaction, never a native save. */
#include "underwater_quests.h"
#include "progression.h"
int landing_mark_nacreway(void){return underwater_visit(&adventure_save,46);}
int landing_validate_revision(unsigned r){return save5_validate_revision(&adventure_save,r);}
