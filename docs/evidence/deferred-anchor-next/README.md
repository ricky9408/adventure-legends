# Deferred-anchor host setup reliability

The earlier released Magma source audit retained one host-address setup failure.
A disposable diagnostic reproduced a Python heap overlapping the synthetic palette
address. This next-branch harness records exact errno/range and overlapping generic
mapping tags, cleans only its own partial mappings and never overwrites a live range.

The launcher permits at most two fresh-process retries only for EEXIST plus a proved
heap overlap before any game assertion. All attempts and failure diagnostics remain
in distinct build directories. Permission failures, unknown mapping failures, malformed
evidence and game assertions are terminal. No ASLR or security setting is changed.

Fifteen launcher model tests and strict/UBSan tests of the exact C mapping function
verify retry refusal, ownership preservation, partial cleanup and clean success.
The complete real-engine synthetic probe also passes 27 checks in strict and UBSan
builds against an isolated copy of all 893 exact delivered Magma runtime inputs.
These runs establish the harness change only. They are not Underwater runtime,
controller-acquisition, display timing or physical-hardware acceptance.

The original released audit and all fixture/source pins remain unchanged. Parent
integration must repeat the engine cases on the complete Underwater candidate.
