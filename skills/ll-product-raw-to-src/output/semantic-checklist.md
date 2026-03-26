# Output Semantic Checklist

Answer each item with `yes`, `no`, or a short finding.

- Does the SRC candidate stay on the same business topic as the raw input?
- Does the candidate avoid introducing EPIC, FEAT, TASK, or implementation breakdown as if they were already decided?
- Are problem statement, target users, trigger scenarios, business drivers, and key constraints traceable to the source?
- Does the candidate include a high-fidelity source layer instead of only a bridge summary?
- Does `semantic_inventory` freeze the key actors, surfaces, entry points, runtime objects, states, and constraints present in the raw input?
- Does `source_provenance_map` show where the major SRC fields came from, including any operator-facing entry surfaces?
- Are normalization decisions explicit enough to explain what was standardized, deduplicated, or merged?
- Does `omission_and_compression_report` explicitly call out any omitted or compressed content and its downstream risk?
- Are contradictions, ambiguities, or unresolved points captured explicitly instead of being silently flattened?
- If the input was an ADR, does the candidate stay thin and bridge-oriented instead of pretending to be downstream product design?
- If the ADR expresses one dominant runtime or inheritance anchor, is that anchor frozen as `semantic_lock` instead of being left as generic bridge prose?
- If the raw input expresses a skill entry, CLI control surface, initialization flow, resume flow, or monitoring surface, are they preserved in `operator_surface_inventory`?
- Are non-goals or boundary notes explicit enough to prevent scope drift downstream?
- Does the proposed action match the actual findings instead of over-claiming `freeze_ready`?
- If the recommended action is not `blocked`, does the package include a valid handoff proposal for external-gate materialization?
