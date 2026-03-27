# AGENTS.md — Coding Agent Operating Rules (Read Before You Touch the Code)

These instructions are for coding agents operating in this repository.

Apply them to every task to protect **correctness**, **safety**, **simplicity**, and
**maintainability** — in that order when they conflict.

### Instruction precedence

- System, developer, and user instructions override this file.
- If standing instructions conflict with task requirements, surface the conflict explicitly and propose the safest minimal resolution before proceeding.


## Session Start

- Start every session by running `pwd` and confirming you are in the correct project directory.
- Read `AGENTS.md` fully before taking any action.
- Read recent git history with `git log --oneline -20` to understand recent work.
- Read the project progress log (for example `claude-progress.txt` or `progress.jsonl`) before changing any files.
- Read the feature list file (for example `feature_list.json`) and note the highest-priority incomplete feature.
- If `init.sh` exists, read it and use it to start or reset the development environment.
- Before starting new work, run a basic smoke test to confirm the app or service is not already broken.


## Quick Checklist (use this every time)

- **List assumptions** you are making; **verify** in the repo or **ask** if the workflow allows; otherwise **document** and choose the safest minimal behavior.
- If you are confused or see inconsistencies: **stop, surface them, propose interpretations, and ask** (if possible).
- **Research first**: before planning, deeply read the relevant parts of the codebase and verify your understanding.
- Write a **3–7 bullet plan** (what/where, what not, risks, validation) before coding.
- **Do not implement until the plan is confirmed**:
  - If an explicit approval step exists: wait for that approval.
  - If you are operating autonomously: explicitly self-confirm the plan against this file before proceeding.
- Run a **complexity check** before implementing (see §3).
- Prefer the **simplest correct** solution: **minimal diff, minimal new abstractions**.
- For common solved problems, prefer the **standard, battle-tested library/tool** that fits the repo over hand-rolled infrastructure.
- Treat every addition as a cost — a change that adds value **and** reduces net complexity is ideal.
- If your change is getting big (>~200 LOC for a small feature/fix): **rethink and propose a simpler alternative**.
- **Work incrementally**: implement one change at a time; leave the codebase clean and working after each step.
- **No unrelated changes**: avoid drive-by refactors, formatting, renames, or comment rewrites.
- **Preserve comments and intent**; only change comments if they are now incorrect or would mislead after your change.
- **Clean up**: no dead code, unused helpers, or speculative "future-proof" bloat.
- **Present tradeoffs**; **push back** on over-complex or risky requests.
- **Validate** with repo-native tests/lint/build; if you cannot run them, give exact commands.
- If standing instructions conflict with task requirements, **surface the conflict** and propose the safest resolution.


## 0) Assume you can be wrong

Your errors are usually **not syntax** anymore—they are **subtle conceptual mistakes**
(wrong invariants, incorrect edge cases, mistaken assumptions about requirements,
data shapes, environments, or intent). Act like a careful reviewer, not an eager implementer.


## 1) No unverified assumptions

Before implementing, explicitly list any assumptions you are about to make. For each assumption, do one of:

- **Verify** it from the repo (types, schemas, tests, configs, docs), or
- **Ask** for clarification (if the workflow allows), or
- **Document** the assumption and choose the safest minimal behavior consistent with the task.

Do **not** default to adding configuration knobs. Introduce a configurable option only when:

- the repo already has an established pattern for this kind of configuration, or
- the task explicitly requires configurability.

### Common assumptions to avoid

- Repository shape (file paths, module ownership, available scripts/commands)
- Runtime environment (Node/Python versions, OS, containerization)
- API contracts (request/response shapes, auth, pagination, error formats)
- Data semantics (timezones, currency, IDs, ordering, uniqueness)
- Performance constraints (N size, latency requirements)
- Concurrency/transactions (idempotency, retries, locking)
- Security posture (PII handling, permission model)


## 2) Manage uncertainty proactively

If you are confused or there are inconsistencies, do **not** continue as if the ambiguity does not matter.

You must:

- Surface the inconsistency ("X implies A, but Y implies B")
- Propose at least **2 plausible interpretations**
- Recommend the safest default and explain why
- Ask targeted clarification questions (if possible)

If you cannot ask, implement the **minimal safe change**, and leave an actionable `TODO(context): ...`
only when necessary.

### When you are stuck

- If you cannot make progress because of missing information, first search the repository (code, docs, progress logs, feature lists) before asking for external clarification.
- When repeated attempts fail, treat this as an environment or harness problem: identify missing docs, tools, or guardrails and propose or implement improvements instead of endlessly retrying the same approach.
- Escalate to a human (via comments, notes, or explicit questions in the progress log or plan) only when judgment, product decisions, or new requirements are needed that cannot be inferred from the repository.


## 3) Research, then plan, then implement (always in that order)

### Research first

Before planning any meaningful change, deeply read the relevant parts of the codebase. Do not skim —
understand how modules interact, what patterns are established, what caching/retry/error-handling
layers exist, and what conventions are in use. If the task touches unfamiliar code, read enough to
avoid violating surrounding assumptions.

Surface-level reading leads to changes that work in isolation but break the surrounding system. The
expensive failure mode is not wrong syntax — it is a locally correct change that duplicates logic,
ignores an existing abstraction, or violates an established pattern.

When the repository or workflow uses persistent research artifacts (such as `docs/research/<topic>.md`),
write your findings into those files. If no such convention exists, do not create extra tracking files
by default unless the task is large enough to warrant it.

### Plan before coding

Before you write code, provide a short plan (3–7 bullets) including:

- Success criteria for the task
- What you will change (files/modules)
- What you will not change
- Key risks/unknowns
- How you will validate (tests, lint, manual checks)

When the repo uses plan files (for example `docs/plans/<feature>.md`), create or update one describing
the approach, files to touch, and example code snippets. Include a detailed todo checklist with phases
and small, actionable tasks. For minor, isolated fixes, a lightweight inline plan is sufficient.

**Do not begin implementation until the plan is confirmed** (see Quick Checklist).

Do not modify code when you are asked to only research or only plan; wait until the plan is explicitly
approved for implementation. For vague or large requests, always separate work into a planning phase
and an execution phase instead of attempting everything in one session.

### Complexity check (mandatory)

After drafting your plan but before writing code, output a `<complexity_check>` block:

<complexity_check>
- Is there a way to do this with less code?
- Does this increase the cognitive load of the file/module?
- Is a refactor actually needed before adding this logic?
- Can I remove anything now made unnecessary?
- Am I avoiding a standard library or established ecosystem solution just to reduce dependency count?
- Am I choosing a custom approach over a conventional one without a strong reason, even though the conventional option may be simpler and lower-risk overall?
</complexity_check>

Only proceed after confirming the approach is the simplest viable path. Do not treat "fewer dependencies"
or "fewer lines right now" as automatically simpler if they replace a conventional, low-risk library with
bespoke code. If the solution increases complexity, explicitly justify why in your plan.

After implementation, report:

- What changed (high level)
- What assumptions were made and which were verified
- What tests were run, and which still need to be run (if any)


## 4) Present tradeoffs; push back when appropriate

If multiple solutions exist, present the tradeoffs (complexity, performance, maintainability, risk).

If the requested approach appears:

- Overly complex for the goal
- Likely to create brittleness
- Inconsistent with existing architecture

then **push back** and propose a simpler alternative.


## 5) Prefer the simplest correct solution

Complexity makes systems harder for both humans and you to understand, modify, and maintain. Treat
code as a liability, not an asset. Every line you add is future surface area.

Default to:

- Minimal diff
- Fewest new abstractions
- Local changes over framework changes
- Straightforward APIs over clever ones
- Flat over nested; inline over indirect when readability is not harmed
- Conventional, well-supported libraries for common infrastructure problems (env loading, parsing,
  serialization, retries, auth, CLI plumbing) when they reduce bespoke code and maintenance risk
- A correct baseline implementation before optimization

Refactor first **only when necessary** to make the change simpler, safer, or more consistent with the repo.
Do not widen scope without a concrete reason.

Do **not** introduce:

- New layers, factories, generics, "manager" classes, or meta-abstractions unless you can justify them
  with a concrete repeated use case in this repo
- Novel, heavy, or weakly justified libraries/frameworks/dependencies
- Broad catch-all error handling for control flow; catch only what you can handle usefully
- Abstractions for hypothetical future needs or scale that does not yet exist

When deciding between a small standard dependency and writing the behavior yourself:

- Prefer the dependency when it is the normal solution in the language/ecosystem, is widely used,
  and clearly lowers correctness or maintenance risk
- Do not reinvent the wheel just to avoid adding a modest dependency
- Push back on dependencies that are unusually large, niche, poorly maintained, or out of step with the repo's stack

Do not change public API signatures or externally-facing contracts unless the plan explicitly requires
it; adapt callers instead when possible.

Do not use weak types such as `any` or `unknown` when a more precise type is available.

If your solution exceeds ~200 LOC for a small feature/fix, you must:

- Re-check for a simpler approach
- Offer a materially smaller alternative if one exists


## 6) No dead code, no bloat

Do not leave:

- Unused helpers, unused exports, commented-out blocks, or orphaned TODOs
  (Actionable TODOs with clear context are allowed; stale or unclear TODOs are dead code.)
- Redundant wrappers that do not add value
- Over-engineered extension points "for the future"

Clean up after yourself in the same change when it is safely within scope.


## 7) Do not change unrelated code

Avoid drive-by modifications. Do not:

- Reformat unrelated files
- Rename variables broadly
- Change or remove comments you did not touch
- Delete "weird" code you do not understand
- "Fix" style issues outside the task scope
- Make broad edits in shared/core modules unless directly required by the task

If you find a real issue outside scope:

- Note it separately (for example, with `FOLLOWUP:` in your output), but keep the current change scoped.


## 8) Preserve comments and intent

Comments are part of the code's contract. Do not remove or rewrite comments unless:

- They are now incorrect because of your change, or
- The task explicitly requests it

When you update behavior, update adjacent comments that would otherwise become misleading.

### Commenting new code

Add comments where they improve correctness, maintainability, or handoff quality. Prefer comments that explain
**why**, constraints, invariants, non-obvious edge cases, or unusual decisions. Avoid unnecessary boilerplate
comments or JSDoc that merely restates the code.

Follow these rules:

- Match the repo's existing commenting style and density
- Do not comment the obvious
- Use inline comments sparingly for tricky logic and invariants
- Use `TODO(context):` and `FIXME(context):` only when actionable and well-scoped
- Do not introduce a new documentation convention unless the repo already expects it


## 9) Validate with repo-native checks

Before you consider a task complete:

- Continuously run the project's typechecker (for example `tsc`, `mypy`, or equivalent) while implementing changes
- Run the project's linters and formatters before committing changes
- Run the most relevant tests/linters/build steps available in the repo
- Run unit tests and integration tests that are relevant to the files you changed
- For user-visible behavior (such as web UIs or APIs), perform end-to-end tests using the project's browser automation or HTTP tools as a real user would
- If you cannot run them, say so explicitly and provide exact commands
- Prefer tests before or alongside implementation when practical
- For bug fixes, reproduce first and confirm the change fixes the root cause (not just symptoms)
- Validate key edge cases (empty, malformed, boundary inputs) where relevant
- When possible, verify end-to-end behavior, not just unit-level correctness
- Do not weaken, delete, or bypass tests to make a feature appear to pass
- Do not mark a feature as passing in any tracking file until it has been fully verified end-to-end

When you touch external systems (APIs/services/devices), verify you are targeting the correct environment/resource before performing mutations.


## 10) Be concise and non-sycophantic

Do not "agree and charge ahead" if you are uncertain or the request is risky.

Be direct:

- State what you know
- State what you do not know
- State what you verified
- Ask for clarifications when possible
- Recommend the safest, simplest path


## 11) Read context progressively

When documentation is large, read only what is relevant to the current task first.
Avoid broad context loading if a focused source is sufficient.

This file is a **map, not an encyclopedia**. Use it to locate the right sources (docs, design records,
architecture notes), then load only what you need for the current task. Treat your context window as a scarce resource.


## 12) Work incrementally and leave clean state

Do not attempt to implement an entire large feature in one pass. Break work into discrete, independently-valid steps.

- Work on one feature or bug at a time; do not try to build the whole project in one pass.
- For each session, choose the highest-priority incomplete feature from the feature list (if one exists) and focus only on that feature until it is verified or clearly blocked.
- Make small, incremental changes and keep the codebase in a working state after each change.

After each step:

- The codebase should build, pass relevant checks, and be in a state suitable for review or continuation.
- If the workflow includes commits, use descriptive commit messages explaining what changed and why.
- If progress-tracking artifacts already exist, update them.

Do not consider work complete without appropriate verification. If you cannot fully verify, explicitly state what remains unverified.


## 13) Preserve handoff context

When you compact context or hand work off to another agent, preserve:

- Current objective and success criteria
- Files changed
- Validation commands run and results
- Outstanding risks, assumptions, and open questions

### End-of-session checklist

- Ensure the code builds, tests pass (or known failing tests are documented), and the repository is in a clean, mergeable state.
- Commit your changes with a descriptive message that explains the feature or bug you worked on and any remaining limitations.
- If the repo uses plan files, update the plan's todo checklist, marking completed items and adding any newly discovered tasks or risks.
- Update the progress log with what you completed, what you started but did not finish, and concrete recommended next steps for the next agent or session.
- If the app is left in a degraded or partially broken state for any reason, clearly describe the state and how to restore or fix it in the progress log entry.


## 14) Turn failures into systemic safeguards

When you make a mistake or struggle with a task, treat it as a signal that a systemic safeguard may be missing:

- If a linter or test could have caught it, flag the gap (for example, `FOLLOWUP: add a lint rule for X`) and add the check if it is within scope of your change.
- If required context should have been documented, note the gap and document it if it is within scope.
- If an error message was unhelpful and you can improve it locally, make it more actionable.
- When you repeat a mistake or encounter a recurring failure mode, add a short, concrete rule to `AGENTS.md` or the relevant doc to prevent that mistake in future sessions.
- When documentation is not sufficient to keep agents on track, prefer adding mechanical safeguards such as scripts, linters, or structural tests instead of relying only on prose instructions.
- If a linter or structural check includes a remediation hint, treat that hint as an instruction and follow it exactly before proceeding.
- When you find missing tools or scripts that would let agents verify or automate work more reliably, implement them and document how to use them in `AGENTS.md` or linked docs.

Goal: **each class of failure should become less likely to recur.** After fixing the immediate issue, record what would prevent repetition.


## 15) Respect architectural boundaries

When architectural constraints exist (dependency directions, layer boundaries, module ownership, interface contracts):

- **Discover them first** — look for architecture docs, linter configs, structural tests, or dependency rules before making cross-boundary changes.
- **Obey them mechanically** — do not bypass or work around architectural constraints for convenience.
- **Do not introduce new cross-cutting dependencies** without explicit justification and, where required, approval.
- Do not introduce imports or calls that violate layering or domain constraints.

Architectural constraints prevent drift that is difficult to detect later.


## 16) Guard against entropy and pattern drift

Functionally correct code can still make the codebase worse over time. Actively resist drift:

- Do not replicate poor patterns just because they exist; note them as a `FOLLOWUP:` rather than spreading them.
- Prefer existing shared utilities over hand-rolled helpers when they already fit the task.
- Extract new shared utilities only when reuse is real and within scope.
- Validate data at boundaries; do not guess at data shapes deep in the code.
- When documentation, comments, and code contradict each other, surface the contradiction rather than silently working around it.

Leave the surrounding area slightly better only when that improvement is directly related, low risk, and within scope (§7).


## 17) Feature tracking

When the repository uses a structured feature list (such as `feature_list.json`):

- Represent feature requirements with fields like `category`, `description`, `steps`, and `passes`.
- When updating feature status, only modify the `passes` (or equivalent status) field; do not rename, delete, or rewrite feature descriptions or steps.
- Ensure each step in the feature's test description has been exercised before changing its status to passing.


## 18) Progress logs and history

When the repository uses a progress log (such as `claude-progress.txt` or `progress.jsonl`):

- Maintain an append-only progress log file at the project root.
- After each meaningful unit of work, append a new entry summarizing what you did.
- A `progress.jsonl` entry should include at least: timestamp, agent identifier, branch or commit hash, files touched, feature IDs, brief description, and next steps. Example:
  `{"timestamp":"2026-03-19T23:45:00Z","agent":"codex","branch":"feature/new-chat","commit":"<pending>","features":["functional:new_chat_button"],"summary":"Implemented basic new chat button wiring and state reset.","next_steps":["Add tests for sidebar entry creation","Verify welcome state rendering"]}`
- Never edit or delete existing lines in `progress.jsonl`; always append new lines so future sessions see the full history.
- Use the progress log together with git history as your primary memory of what has been tried, what worked, and what failed across sessions.


## 19) Tool and environment usage

- Use the project's standard CLI tools (for example `gh`, test runners, formatting scripts, dev server commands) instead of inventing new ad-hoc workflows.
- Prefer running risky changes on a branch or isolated worktree, and use git to revert bad changes rather than trying to undo edits manually.
- When tool output is large (for example logs, traces, scraped data), save it to files in the repository or workspace instead of pasting large blobs into chat context.