/* Explicit absent-Return bridge for isolated pre-Return combat harnesses.
 * These tests never enter Return rooms or cast Return commands. Current engine
 * and Return native suites link the real modules, never this bridge. */
#include "return_powers.h"
int return_powers_busy(void) { return 0; }
