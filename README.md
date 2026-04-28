# LEE Lite — Skill-First Governed Development

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue)](https://www.typescriptlang.org/)
[![Playwright](https://img.shields.io/badge/E2E-Playwright-green)](https://playwright.dev/)
[![Coverage](https://img.shields.io/badge/Coverage-%E2%89%A580%25-brightgreen)](pytest.ini)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A governed, skill-first development framework that turns AI-assisted coding into traceable, reviewable, and auditable engineering workflows.**

LEE Lite bridges the gap between ad-hoc AI code generation and production-grade software engineering. It introduces a **governed mainline** where every change — from raw requirements to shipped implementation — flows through structured skills, formal gates, and durable single-source-of-truth (SSOT) objects.

---

## Table of Contents

- [Why LEE Lite?](#why-lee-lite)
- [Core Concepts](#core-concepts)
- [Architecture Overview](#architecture-overview)
- [Directory Layout](#directory-layout)
- [Getting Started](#getting-started)
- [CLI Usage](#cli-usage)
- [Skill Catalog](#skill-catalog)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)

---

## Why LEE Lite?

| Problem | How LEE Lite Solves It |
|---------|------------------------|
| AI-generated code lacks traceability | Every output is an **artifact** with lineage, evidence, and supervision records |
| Prompt drift across sessions | **Skills** encode reusable workflows as governed contracts, not one-off prompts |
| No formal handoff between PM and Engineering | **SSOT objects** (SRC → EPIC → FEAT → TECH → IMPL) form a verifiable derivation chain |
| Unreviewed AI changes reach production | **Gate runtime** enforces human or automated approval at every stage |
| Experience is lost between projects | **Experience Patches** capture fixes and adaptations as reusable, schema-validated records |

---

## Core Concepts

### 1. Skill-First Architecture

A **Skill** is a self-contained, contract-governed workflow unit. Each skill declares:

- `SKILL.md` — purpose, boundary, and execution protocol
- `ll.contract.yaml` — input/output schema and semantic checklist
- `agents/` — supervisor and executor agent definitions
- `scripts/` — validated runtime implementation
- `resources/` — templates, checklists, and reference material

Skills are **composable** and **versioned**. They are the primary unit of reuse, not prompt fragments.

### 2. SSOT Derivation Chain

Formal objects flow through a governed pipeline with explicit handoffs:

```
Raw Input        →  SRC (Source Document)        →  EPIC
                                                          ↓
Test Plan  ←  FEAT (Feature Spec)  ←  TECH (Tech Design)  ←  IMPL (Implementation)
     ↓
E2E / API Test Execution  →  Gate Review  →  Release
```

Every transition is **materialized** (written to disk), **validated** (schema + semantic checks), and **admitted** (gate review) before entering the canonical mainline.

### 3. Gate Runtime

The **Gate** is a decision layer that sits between workflow stages. It supports:

- **Human Gate** — manual review and approval
- **Auto-Pass** — mechanical validation with escalation triggers
- **Supervised Execution** — AI-assisted with mandatory evidence capture

Gates are expressed as file-based runtimes, making them inspectable, reproducible, and CI-friendly.

### 4. Experience Patch Layer

When AI output deviates from expectations, the **Patch Capture** skill records the correction as a structured *Experience Patch*. Patches are:

- Schema-validated (`PatchExperience` dataclass)
- Conflict-detected (overlap analysis before registration)
- Traceable (session ID, source context, test impact)
- Reusable (injected into future skill executions as context)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer (ll.py)                     │
│  artifact · registry · audit · gate · loop · job · skill    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────┐
│         Skills Layer        │         SSOT Layer          │
│  ┌─────────────────────┐    │    ┌───────────────────┐    │
│  │ Product Skills      │    │    │ adr/              │    │
│  │   raw-to-src        │    │    │ src/              │    │
│  │   src-to-epic       │    │    │ epic/             │    │
│  │   epic-to-feat      │    │    │ feat/             │    │
│  │                     │    │    │ tech/             │    │
│  │ Development Skills  │    │    │ impl/             │    │
│  │   feat-to-proto     │    │    │ gate/             │    │
│  │   feat-to-tech      │    │    │ mapping/          │    │
│  │   tech-to-impl      │    │    │ schemas/          │    │
│  │                     │    │    └───────────────────┘    │
│  │ QA Skills           │    │                             │
│  │   impl-spec-test    │    │                             │
│  │   test-exec-web-e2e │    │                             │
│  │   gate-evaluate     │    │                             │
│  └─────────────────────┘    │                             │
│                             │                             │
│  ┌─────────────────────┐    │    ┌───────────────────┐    │
│  │ Governance Skills   │    │    │ Experience        │    │
│  │   patch-capture     │    │    │   patches/        │    │
│  │   frz-manage        │    │    │   registry/       │    │
│  │   meta-skill-creator│    │    │   release/        │    │
│  └─────────────────────┘    │    └───────────────────┘    │
└─────────────────────────────┴─────────────────────────────┘
```

---

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `ssot/` | **Single Source of Truth** — canonical ADRs, formal objects, schemas, and governance rules |
| `skills/` | **Reusable Skills** — 30+ governed workflow definitions, each with contracts, agents, and runtime scripts |
| `cli/` | **Command-Line Interface** — shared validators, helpers, and the `ll` entrypoint |
| `tests/` | **Test Suite** — unit, integration, and golden tests (pytest + Playwright) |
| `artifacts/` | **Reviewable Outputs** — execution evidence, reports, and lineage snapshots |
| `docs/` | **Documentation** — architecture notes, playbooks, and implementation plans |
| `examples/` | **Learning Material** — sample workflows and demo projects |
| `.local/` | **Developer Workspace** — ignored; for local experiments only |

> **Design principle:** The project tree stores only reusable, reviewable, versionable, and traceable content. Runtime state lives outside the tree.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for E2E testing)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/LEE-Lite-skill-first.git
cd LEE-Lite-skill-first

# Install Python dependencies
pip install -r requirements.txt  # or use your preferred environment manager

# Install Node dependencies (for E2E testing)
npm install

# Install Playwright browsers
npx playwright install chromium
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env to configure runtime directories:
# LL_RUNTIME_HOME=/tmp/ll
# LL_CACHE_HOME=~/.cache/ll
# LL_SESSION_HOME=~/.ll
```

---

## CLI Usage

The `ll` CLI is the unified entrypoint for all governed operations:

```bash
# Run a skill
python -m cli.ll skill impl-spec-test \
  --request <request.json> \
  --response-out <response.json> \
  --evidence-out <evidence.json>

# Gate operations
python -m cli.ll gate decide \
  --request <handoff.json> \
  --response-out <result.json>

# Audit workspace
python -m cli.ll audit scan-workspace \
  --request <config.json> \
  --response-out <report.json>

# Validate artifacts
python -m cli.ll validate request --request <payload.json> --response-out <result.json>
```

Available command groups: `artifact`, `registry`, `audit`, `gate`, `loop`, `job`, `rollout`, `skill`, `validate`, `evidence`.

---

## Skill Catalog

### Product Pipeline
| Skill | Description |
|-------|-------------|
| `ll-product-raw-to-src` | Normalize raw requirements into governed SRC documents |
| `ll-product-src-to-epic` | Derive EPICs from SRC with scope boundaries |
| `ll-product-epic-to-feat` | Decompose EPICs into implementable FEAT specs |

### Development Pipeline
| Skill | Description |
|-------|-------------|
| `ll-dev-feat-to-proto` | Generate UI prototypes from FEAT specs |
| `ll-dev-feat-to-tech` | Produce technical designs (TECH) from FEAT |
| `ll-dev-tech-to-impl` | Derive implementation candidates from TECH |
| `ll-dev-feat-to-ui` | Direct UI derivation with surface-map contracts |
| `ll-dev-proto-to-ui` | Prototype-to-UI refinement |

### QA Pipeline
| Skill | Description |
|-------|-------------|
| `ll-qa-impl-spec-test` | Pre-implementation specification stress testing |
| `ll-qa-test-run` | Governed test execution with evidence capture |
| `ll-qa-api-from-feat` | API test plan generation from FEAT |
| `ll-qa-e2e-from-proto` | E2E test derivation from UI prototypes |
| `ll-qa-gate-evaluate` | Gate readiness evaluation |

### Governance & Meta
| Skill | Description |
|-------|-------------|
| `ll-patch-capture` | Capture and register experience patches |
| `ll-frz-manage` | Freeze management and release orchestration |
| `ll-meta-skill-creator` | Create new skills from templates |
| `ll-project-init` | Initialize a repository with the LEE Lite skeleton |

---

## Testing

### Python Tests

```bash
# Run unit and CLI tests with coverage
pytest

# Coverage report (terminal)
pytest --cov=cli.lib --cov-report=term-missing

# Coverage report (HTML)
pytest --cov=cli.lib --cov-report=html
```

Minimum coverage threshold: **80%**.

### E2E Tests

```bash
# Run Playwright E2E tests
npx playwright test

# Run with UI mode for debugging
npx playwright test --ui
```

### Test Structure

```
tests/
├── unit/           # Unit tests for utilities and validators
├── cli/            # CLI command tests
├── integration/    # Integration tests for skill runtimes
├── qa/             # QA schema and contract tests
├── fixtures/       # Shared test data
└── golden/         # Snapshot/golden file tests
```

---

## Security

LEE Lite follows a security-first design. All phases undergo structured threat modeling with ASVS Level 1 verification.

Key security controls:

- **Input Validation** — Regex, enum, and schema validation on all CLI payloads
- **Path Containment** — Document paths are resolved and verified relative to workspace root
- **Schema Enforcement** — All generated YAML validated against dataclass schemas before registration
- **Audit Trail** — Every patch carries a session ID and returns evidence references
- **Auto-Pass Safeguards** — Requires ALL conditions (schema valid + no conflicts + non-semantic + high confidence); escalates on first patch, semantic classification, or disputes

See [SECURITY.md](SECURITY.md) for the full threat verification summary.

---

## Contributing

We welcome contributions that align with the governed workflow philosophy.

1. **Open an issue** to discuss your idea or bug report
2. **Fork and branch** — follow conventional commit format (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`)
3. **Write tests first** — TDD is mandatory for new features
4. **Run the full suite** — `pytest` must pass with ≥80% coverage
5. **Code review** — All changes require review via the code-reviewer agent checklist
6. **Security review** — Use the security-reviewer agent for auth, input, or file-system changes

Please read [docs/repository-layout.md](docs/repository-layout.md) for project structure conventions and [CLAUDE.md](CLAUDE.md) for patch context injection rules.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

> *Project tree = SSOT + Skill + CLI + Artifacts + Docs. Runtime lives outside the tree. Only outcomes enter the tree.*
