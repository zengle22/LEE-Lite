# Authoring Patterns

Use this reference when the workflow boundary is clear and the scaffold already exists.

## Concrete Example

For `src-to-epic`:

- input artifact: `src`
- output artifact: `epic`
- authority rule: only accept frozen SRC input
- executor concern: draft EPIC without implementation detail leakage
- supervisor concern: reject scope drift, missing non-goals, and unstated rollout assumptions

## Authoring Sequence

1. Write `input/contract.yaml`.
   - accepted artifact type
   - allowed state
   - mandatory fields
   - mandatory refs
   - forbidden inputs
2. Write `output/contract.yaml`.
   - output artifact type
   - required sections
   - required source refs
   - forbidden details
   - downstream expectations
3. Write semantic checklists.
   - input checklist asks whether the source is authoritative enough
   - output checklist asks whether the result stays in layer
4. Write evidence schemas.
   - executor records inputs, outputs, commands, structural results, key decisions, and uncertainties
   - supervisor records reviewed materials, findings, decision, and reason
5. Write role prompts.
   - executor cannot self-approve
   - supervisor cannot silently rewrite output

## Contract Design Rules

- Prefer small, explicit fields over prose blobs.
- Mention forbidden changes directly.
- Encode source refs and freeze rules in the contract, not in body text alone.
- Keep schema versioning explicit so downstream tooling can upgrade safely.

## Checklist Design Rules

- Each checklist item should be answerable with yes, no, or a short finding.
- Keep structural checks out of semantic checklists.
- Phrase semantic checks in terms of artifact responsibility, scope, and fidelity.

## Runtime Guidance

- Use shell scripts for wrapper entry points when the execution shell expects them.
- Move complex or cross-platform logic into Python only when needed.
- Leave placeholders where project-specific `lee` commands differ, but keep the file names and roles stable.
