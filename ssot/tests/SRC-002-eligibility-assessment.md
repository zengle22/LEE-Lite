# SRC-002 Eligibility Assessment for ADR-047 Dual-Chain Test Spec Generation

## Assessment Metadata

| Field | Value |
|-------|-------|
| src_id | SRC-002 |
| src_title | ADR-019 raw-to-src: From Thin Bridge to High-Fidelity SRC Normalizer |
| src_status | frozen |
| src_frozen_at | 2026-03-26T03:13:16Z |
| assessment_date | 2026-04-11 |
| assessed_by | automated eligibility check |
| eligibility_result | **NOT ELIGIBLE** |

## Investigation Findings

### File Inventory for SRC-002

| Artifact Type | Count | Files Found |
|---------------|-------|-------------|
| SRC | 1 | `ssot/src/SRC-002__adr-019-raw-to-src-从-thin-bridge-升级为-high-fidelity-src-normalizer.md` |
| EPIC | 0 | None |
| FEAT | 0 | None |
| IMPL | 0 | None |
| API | 0 | None |
| TECH | 0 | None |
| TESTSET | 0 | None |

### Search Methods Used

- Glob search for `**/*SRC-002*` in `ssot/` directory: only the SRC document matched
- Glob search for `**/*FEAT*SRC-002*`: zero results
- Glob search for `**/*EPIC*SRC-002*`: zero results

## Why SRC-002 Is NOT Eligible

### 1. No Downstream FEAT Chain Exists

The ADR-047 dual-chain test spec generation workflow requires **FEAT-level artifacts** as the anchor for both the API test chain and the E2E test chain. Specifically:

- **API chain anchor**: `ssot/tests/api/FEAT-{src}-{NNN}/` requires a corresponding FEAT document in `ssot/feat/`
- **E2E chain anchor**: `ssot/tests/e2e/PROTOTYPE-FEAT-{src}-{NNN}/` derives journeys from the FEAT's Goal/Scope/Constraints/Acceptance Checks

SRC-002 has **zero FEAT files**. There is nothing to anchor test plans, coverage manifests, or journey specs against.

### 2. No EPIC Breakdown Exists

The standard demand-chain pipeline is:

```
SRC (governance source) --> EPIC (capability grouping) --> FEAT (testable unit) --> TEST specs
```

SRC-002 has no EPIC decomposition. The jump from SRC directly to test specs would bypass the entire EPIC-level scoping layer, which means there is no structured breakdown of what capabilities should be tested, how they group, or what acceptance criteria apply at each level.

### 3. SRC-002 Is a Governance Document, Not a Feature Specification

Reading the SRC-002 content reveals it is a **governance bridge document** that:

- Defines governance boundaries for ADR-019 (raw-to-src normalization)
- Establishes inheritance constraints for downstream chains
- Records operator surface inventories and standardized decisions
- Explicitly marks **implementation details as out of scope**:
  - "Out of scope: 下游 EPIC/FEAT/TASK 分解与实现细节" (Downstream EPIC/FEAT/TASK decomposition and implementation details)
  - "In scope: 为后续主链对象提供统一约束来源与交接依据，而不是在本层展开 API 或实现设计" (Provide unified constraint source for downstream chain objects, rather than expanding API or implementation design at this layer)

This confirms that SRC-002 was **never intended** to contain feature-level specifications. It is a policy/constraint document that downstream EPICs and FEATs must inherit from, not a feature that can be directly tested.

### 4. No Testable Capabilities at SRC Level

The ADR-047 workflow extracts testable capabilities from FEAT documents:
- API objects and their CRUD operations
- User journeys and state transitions
- Acceptance checks with verifiable criteria
- Constraints with observable enforcement

SRC-002 contains governance decisions (source_projection, bridge_projection, operator_surface_preservation) and inheritance requirements, but **no API endpoints, no user interactions, no state machines, and no concrete acceptance criteria** that can be expressed as test cases.

## Prerequisites Before SRC-002 Can Enter Dual-Chain Testing

To make SRC-002 eligible for ADR-047 dual-chain test spec generation, the following steps must be completed **in order**:

### Step 1: Run `ll-product-src-to-epic`

Decompose SRC-002 into one or more EPIC documents. The EPIC should capture:
- Capability groupings derived from SRC-002's governance boundaries
- Operator surface implementations (Execution Loop Job Runner, `ll loop run-execution`, runner observability)
- Governance enforcement mechanisms (validation, evidence, gate-ready outputs)
- Inheritance contract enforcement for downstream chains

Expected output: `ssot/epics/EPIC-SRC-002-*.md`

### Step 2: Run `ll-product-epic-to-feat`

Decompose each EPIC into testable FEAT documents. Each FEAT must contain:
- **Goal**: What the feature achieves
- **Scope**: Concrete user-facing capabilities (with capability IDs like `CAP-XXX-001`)
- **Constraints**: Enforceable rules with observable outcomes
- **Acceptance Checks**: Verifiable criteria (e.g., "Submission completion", "Downstream flow inheritance")
- **Inherited governance**: Explicit references to SRC-002 constraints that must be inherited

Expected output: `ssot/feat/FEAT-SRC-002-*.md`

### Step 3: Freeze FEAT Documents

Each FEAT must reach `status: frozen` before test specs can be generated. The freeze indicates the feature contract is stable and ready for test derivation.

### Step 4: Run ADR-047 Dual-Chain Test Spec Generation

Only after Steps 1-3 are complete can the dual-chain test specs be generated:

```
For each frozen FEAT-SRC-002-NNN:
  API chain:
    ssot/tests/api/FEAT-SRC-002-NNN/api-test-plan.md
    ssot/tests/api/FEAT-SRC-002-NNN/api-coverage-manifest.yaml
    ssot/tests/api/FEAT-SRC-002-NNN/api-test-specs/

  E2E chain:
    ssot/tests/e2e/PROTOTYPE-FEAT-SRC-002-NNN/e2e-journey-plan.md
    ssot/tests/e2e/PROTOTYPE-FEAT-SRC-002-NNN/e2e-coverage-manifest.yaml
    ssot/tests/e2e/PROTOTYPE-FEAT-SRC-002-NNN/e2e-journey-specs/
```

## Recommendation

**Block SRC-002 from dual-chain testing until the demand chain (EPIC/FEAT decomposition) is completed.** The SRC document is a well-formed governance artifact, but the absence of downstream EPICs and FEATs makes it impossible to generate meaningful test specs. Attempting to generate test specs at this stage would produce artifacts with no anchor, no capabilities to test, and no acceptance criteria to verify.

Priority action: Run `ll-product-src-to-epic` on SRC-002 to begin the demand-chain decomposition.
