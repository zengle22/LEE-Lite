# LEE Lite Governance Pack

Every generated workflow skill must be a standard skill shell plus a governance pack.

## Layer Model

1. Compatibility layer
   - `SKILL.md`
   - `agents/openai.yaml`
2. Contract layer
   - `ll.contract.yaml`
   - `input/contract.yaml`
   - `output/contract.yaml`
3. Validation layer
   - structural checks in `scripts/`
   - semantic checklists in `input/semantic-checklist.md` and `output/semantic-checklist.md`
4. Governance layer
   - `agents/executor.md`
   - `agents/supervisor.md`
   - `evidence/`
   - freeze gate rules in `ll.contract.yaml`

## Required Tree

```text
skill-name/
  SKILL.md
  ll.contract.yaml
  ll.lifecycle.yaml
  input/
    contract.yaml
    schema.json
    semantic-checklist.md
  output/
    contract.yaml
    schema.json
    template.md
    semantic-checklist.md
  evidence/
    execution-evidence.schema.json
    supervision-evidence.schema.json
    report.template.md
  agents/
    executor.md
    supervisor.md
    openai.yaml
  resources/
    glossary.md
    examples/
      input.example.md
      output.example.md
    checklists/
      authoring-checklist.md
      review-checklist.md
  scripts/
    validate_input.sh
    validate_output.sh
    collect_evidence.sh
    freeze_guard.sh
```

## File Responsibilities

- `SKILL.md`: shell-facing entry. Keep it concise and operational.
- `ll.contract.yaml`: workflow governance contract. Define roles, validations, evidence, lifecycle link, revision limit, and freeze gate.
- `ll.lifecycle.yaml`: lightweight status protocol for drafted, validated, reviewed, revised, accepted, frozen, or rejected states.
- `input/contract.yaml`: what the workflow accepts.
- `output/contract.yaml`: what the workflow may emit.
- `schema.json`: structural shape checks.
- `semantic-checklist.md`: explicit review criteria, not vague "review this" prose.
- `evidence/`: machine-checkable evidence shapes and a report skeleton.
- `agents/executor.md`: execution role, generation rules, and evidence obligations.
- `agents/supervisor.md`: review role, semantic boundary checks, and pass or reject rules.

## Frontmatter Rule

Keep LL governance out of frontmatter. The base skill shell should stay minimal enough to work in standard skill environments. If the target runtime supports extra fields such as `context` or `agent`, treat them as optional runtime extensions, not as the core LL contract.

## Default Validation Split

- Structural validation
  - file presence
  - schema shape
  - naming
  - trace refs
  - freeze status
- Semantic validation
  - fidelity to upstream source
  - no unauthorized scope expansion
  - no layer mixing
  - required constraints preserved
  - no parallel truth introduced

## Freeze Rule

Freezing requires all of the following:

- input structural pass
- input semantic pass
- output structural pass
- output semantic pass
- execution evidence present
- supervision evidence present
