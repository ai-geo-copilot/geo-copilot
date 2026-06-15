# AGENTS.md

## Scope

These instructions apply to the entire `E:\vibe coding\geo项目` repository.

## Operating Rules

- Focus only on the current task.
- Inspect first, then act.
- Execute the exact requirement with maximum autonomy inside scope.
- Prioritize correctness, robustness, maintainability, and minimal necessary change.
- Do not hallucinate facts, files, APIs, results, or completion status.
- Preserve verified work as no-op unless direct evidence proves it wrong.
- Avoid side work, unnecessary refactors, premature abstraction, extra features, and scope drift.
- Report only verified findings, changes, blockers, and uncertainties.
- Apply `karpathy-guidelines` by default for coding, review, debugging, and refactor tasks unless explicitly overridden.

## Mandatory Development Status Source

`docs/DEVELOPMENT_STATUS.md` is the repository's single source of truth for current development status.

`docs/README.md` is the single entry point for project design documents. Project design Markdown files must live under `docs/`; do not duplicate them at the repository root.

Before starting any coding, review, debugging, refactor, architecture, database, API, frontend, or documentation task:

1. Read `docs/DEVELOPMENT_STATUS.md`.
2. Use it to identify current phase, verified work, active priorities, blockers, and next steps.
3. Do not rely on chat history alone when it conflicts with this file.

After completing any task that changes code, contracts, database schema, architecture, verification status, blockers, or implementation priorities:

1. Update `docs/DEVELOPMENT_STATUS.md` in the same turn.
2. Record only verified facts and exact commands/results.
3. Update current status, completed work, verification results, blockers, and next steps as applicable.
4. Do not mark work complete unless it was actually implemented and verified.

If a task cannot update `docs/DEVELOPMENT_STATUS.md`, report that as a blocker or residual risk in the final response.

## Current Architecture Priority

The next full module priority is Page Evidence + Rule Engine under `apps/api/app/page_evidence`.

Do not prioritize DeepSeek integration, full frontend report UI, or RAG hybrid retrieval before Page Evidence v1 is complete unless the user explicitly changes the priority.
