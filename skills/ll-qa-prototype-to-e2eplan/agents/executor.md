# Executor Agent: ll-qa-prototype-to-e2eplan
## Role
Generate e2e-journey-plan.md from frozen prototype or FEAT
## Instructions
1. Determine mode (prototype-driven or API-derived)
2. Extract journeys from prototype/FEAT
3. Apply journey identification rules
4. Validate minimum journey count (>=1 main + >=1 exception)
5. Generate e2e-journey-plan.md

---

# Supervisor Agent: ll-qa-prototype-to-e2eplan
## Validation Checklist
1. Mode correctly determined
2. All journey identification rules applied
3. At least 1 main journey (P0)
4. At least 1 exception journey
5. Each journey has entry_point and >= 2 user_steps
6. API-derived mode has derivation_mode annotation
