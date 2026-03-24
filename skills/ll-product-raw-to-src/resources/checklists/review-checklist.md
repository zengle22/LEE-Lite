# Review Checklist

- Does the skill reject already-governed SSOT input?
- Does the runner preserve the staged order from validation through freeze-readiness assessment?
- Are duplicate-title and multi-topic guards enforced before recommending downstream flow?
- Are ADR bridge outputs explicitly marked as `governance_bridge_src`?
- Are acceptance report, defect list, retry-budget report, execution evidence, and supervision evidence all emitted?
- If the action is not `blocked`, does the package include `handoff-proposal.json` and `job-proposal.json`?
- Does the skill stop at proposals and leave final gate materialization outside the skill?
