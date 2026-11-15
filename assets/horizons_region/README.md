# Portable Shared Horizons authoring inputs

`source_plan.json` is the input for the Horizons region and creature generators.
The formerly referenced `docs/horizons-design/shared_horizons_plan.json` was
absent from the source checkout and its available Git history. Generating the
complete asset set therefore stopped before Horizons.

The replacement records the data that its consumers actually require:

- All eight area sizes, safe routes, spawn positions and reset points come
  directly from the shipped `geometry.json`.
- All sixteen form briefs are copied verbatim from the shipped creature
  `manifest.json`.
- The four trial family/from/to mappings come from the existing revision 8
  catalog trial bindings and matching evolution rows.
- The four revision 8 equipment definitions and reward-source IDs come from
  the existing equipment catalog, preserving its stat order and values.

The source JSON records hashes of those input artifacts before reconstruction,
the missing path, and the original plan hash retained by the creature manifest.
It does not claim to reproduce the unavailable complete design document.
No geometry, creature statistics, abilities or progression rules were invented.

Generated geometry and creature manifests remain outputs. Future generation
reads the checked-in source plan directly and never reconstructs it from its
own outputs. Catalog tests compare its forms against the independent live
catalog, and its area fields against shipped geometry. The art tests continue
to check the native pixel tensors and deterministic generation.
