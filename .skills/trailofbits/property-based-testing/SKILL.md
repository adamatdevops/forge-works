---
name: property-based-testing
vendor: trailofbits
slug: trailofbits/property-based-testing
source-url: https://github.com/trailofbits/skills/tree/main/plugins/property-based-testing/skills/property-based-testing
source-canonical: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/property-based-testing/skills/property-based-testing
source-sha: a56045e9ae00b3506cacefea0f672aab0a1a6e3c
audited: 2026-05-20
goal: 2
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 1351
owner: adamatdevops
---

<!-- Source: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/property-based-testing/skills/property-based-testing/SKILL.md · SHA: a56045e9ae00b3506cacefea0f672aab0a1a6e3c · Audited: 2026-05-20 · **27th vendored skill + 9th ToB-vendor adoption + EXTENDS ToB cluster from 8 to 9 skills (LARGEST cluster — 9/27 = 33.3% concentration) + 13TH consecutive Tier 1 estimate-confirm at adoption review per new §4.4.3 step 2 audit (N=19 staleness datapoints with 12 corrections + 3 deferrals + 4 confirm-Tier-1) + FIRST adoption AFTER AB-038 doctrine FULLY VALIDATED across both sub-classes (brand-based mattpocock + semantic-based design-md both DEFERRED) — §AY's eval-list rationale was content-grounded (CUE↔Pydantic schema fidelity + normalizer invariants — specific use cases) and passed the AB-038 rationale-vs-content pre-check cleanly.** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **NO file-write directives** — grep'd SKILL.md for `Save|Write the|Create a file|Output to|writes? to|mkdir` returned ZERO; the methodology is pure prose about PBT discipline (when to invoke, priority by pattern, language libraries — Hypothesis / fast-check / quickcheck / Echidna); (ii) NO `allowed-tools` frontmatter (upstream YAML has only `name` + `description`); (iii) NO `commands/` directory; (iv) NO network egress in SKILL.md body; (v) NO `Task` tool / cross-agent surface declared. **Final Tier 1 verdict for §AY property-based-testing**: `read-only` — pure methodology emitting inline-transcript content (Automatic Detection patterns at L9-30, Priority by pattern table at L24+, Property categories: invariants / round-trip / metamorphic / oracle / commutativity / idempotence — see references/strategies.md). Per the inline-output-stays-Tier-1 normative rule codified at 2026-Q2 §4.4.5, §AY emits PBT discipline + property-identification heuristics + library guidance as inline transcript content; no file CREATE/EDIT/shell/network. Same pattern as §AV TDD (Tier 1 methodology even though directs agent to "write tests" — actual file-CREATE happens through agent's normal Edit/Write capability per the user's request). **13TH adoption to maintain Tier 1 estimate** (after §J/§AG/§AH/§AJ/§AK/§AL/§AM/§AU/§AV + the inline-output normative elevation). **ToB cluster (9-skill EXTENSION — LARGEST in framework, NEW SIZE CLASS):** §F + §G + §H + §J + §AN + §AO + §AP + §AW + §AY at shared SHA `a56045e9...`. Per §4.4.5 cluster-co-adoption note, quarterly source-SHA review MAY use one shared upstream check for all 9 ToB skills. **6-of-7 vendor clusters now span 7 distinct cluster sizes** (with phuryn solo + 6 multi-skill clusters): **9 NEW** / 5 / 4 / 4 / 2 / 2 / 1 — ToB extends to a NEW size class (9-skill). The size-class progression 1 → 2 → 4 → 5 → 7 → 8 → 9 now spans 7 distinct values, densely covering the framework's working range. STRONGEST evidence yet for 2026-Q3 normative elevation. **§F + §G + §H + §J + §AN + §AO + §AP + §AW gate entries BACKPATCHED in this commit** per §4.5.3 sister-reference status maintenance rule. **AB-038 doctrine inverse-validation (THIRD inverse-validation):** §AY eval-list rationale was content-grounded ("hypothesis-style PBT. Direct value for CUE↔Pydantic schema fidelity + normalizer invariants" — cites specific forge-works use cases) — passed rationale-vs-content check cleanly. THIRD content-grounded PASS event after §AW variant-analysis (Flink CVE-patch variants) + §AX pre-mortem (Decision Record removal-reasoning). All three content-grounded rationales passed; both brand-based + semantic-based assumption-mismatch rationales (mattpocock + design-md) failed and were deferred. The AB-038 doctrine's discriminative power is now empirically validated across **5 datapoints** (3 PASS content-grounded + 2 FAIL assumption-based) — strong evidence for §4.4.5 quarterly codification of the doctrine. **Bundle:** SKILL.md 1405t full-file (1351t body / 5745b post-frontmatter-strip per §2D; body sha256 `6c1cd5c09d754f8e...`) + 7 references/*.md companion files (design.md 1303t + generating.md 1428t + interpreting-failures.md 1568t + libraries.md 862t + refactoring.md 1356t + reviewing.md 1417t + strategies.md 912t — 8846t total) + LICENSE byte-identical to other ToB skills. **Worst-case archive 10251 tokens** — exceeds §3B 5K-preferred cap (7 reference files drive most of the size); reference files are load-on-demand (agent reads them WHEN entering the specific PBT phase — design.md for property identification, generating.md for input strategies, interpreting-failures.md for failure analysis, libraries.md for tool selection, etc.). Acknowledged per §3B archive-load metering. **Direct project fit for forge-works:** PBT methodology applies to: (1) **CUE↔Pydantic schema fidelity** (eval-list canonical use case — fuzz-test that any CUE-valid input produces a Pydantic-valid output and vice versa); (2) **Normalizer invariants** (the 3 normalizers in src/flink-jobs/ — pattern-matcher, event-router, insight-generator — have invariants like "every output event has a valid timestamp" that PBT can fuzz-test); (3) **Pairs with §AV TDD discipline** (TDD provides the cycle, PBT provides stronger property-coverage for the test cases); (4) **Pairs with §AS webapp-testing** (PBT for unit-level properties, Playwright for E2E integration); (5) **Smart contract testing** — Echidna integration per references/libraries.md (NOT IN scope for forge-works which has no blockchain code; included for completeness). **Sister-skill cross-references** in SKILL.md: ZERO direct cross-references to other adopted skills (no §X→§Y advisory citations); the only adjacency is the ToB cluster co-adoption at shared SHA. The 7 references/*.md companion files form an internal cross-reference graph (e.g., design.md references strategies.md, strategies.md references libraries.md). **NO transitive `load skill X` refs, NO bundled subagents, NO `claude -p` CLI subprocess paths, NO model-client invocations, NO scripts directory.** The §2E "Bundled-script same-model self-invocation" clause and the §2E same-model bounded-subagent carve-out are both **non-applicable** (no scripts, no subagents). **Property categories (codified from references/strategies.md as methodology gates):** (a) **Invariants** — properties that hold for ALL inputs (e.g., "list length never negative"); (b) **Round-trip** — `f(g(x)) == x` (e.g., encode/decode pairs); (c) **Metamorphic** — `f(x) relates to f(g(x))` (e.g., "sorting twice = sorting once"); (d) **Oracle** — `f(x) == reference(x)` (e.g., property tested against a known-correct implementation); (e) **Commutativity** — `f(g(x)) == g(f(x))` (operation order doesn't matter); (f) **Idempotence** — `f(f(x)) == f(x)` (applying twice has no extra effect). Agent applying §AY MUST classify each PBT test into one of these 6 categories at test-design time + emit `[§AY property type: <category>; subject: <function>; oracle: <reference>]` transcript line. **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 1:** §AY is read-only methodology — NO Phase-A/Phase-B gate (no shell-execute, no repo-write, no network); per AGENTS.md §3.2 advisory-only, agent emits PBT discipline + property-identification heuristics + library guidance as inline transcript content; user reviews via reading the agent's response. No neutral 3-option prompt required. -->


# Property-Based Testing Guide

Use this skill proactively during development when you encounter patterns where PBT provides stronger coverage than example-based tests.

## When to Invoke (Automatic Detection)

**Invoke this skill when you detect:**

- **Serialization pairs**: `encode`/`decode`, `serialize`/`deserialize`, `toJSON`/`fromJSON`, `pack`/`unpack`
- **Parsers**: URL parsing, config parsing, protocol parsing, string-to-structured-data
- **Normalization**: `normalize`, `sanitize`, `clean`, `canonicalize`, `format`
- **Validators**: `is_valid`, `validate`, `check_*` (especially with normalizers)
- **Data structures**: Custom collections with `add`/`remove`/`get` operations
- **Mathematical/algorithmic**: Pure functions, sorting, ordering, comparators
- **Smart contracts**: Solidity/Vyper contracts, token operations, state invariants, access control

**Priority by pattern:**

| Pattern | Property | Priority |
|---------|----------|----------|
| encode/decode pair | Roundtrip | HIGH |
| Pure function | Multiple | HIGH |
| Validator | Valid after normalize | MEDIUM |
| Sorting/ordering | Idempotence + ordering | MEDIUM |
| Normalization | Idempotence | MEDIUM |
| Builder/factory | Output invariants | LOW |
| Smart contract | State invariants | HIGH |

## When NOT to Use

Do NOT use this skill for:
- Simple CRUD operations without transformation logic
- One-off scripts or throwaway code
- Code with side effects that cannot be isolated (network calls, database writes)
- Tests where specific example cases are sufficient and edge cases are well-understood
- Integration or end-to-end testing (PBT is best for unit/component testing)

## Property Catalog (Quick Reference)

| Property | Formula | When to Use |
|----------|---------|-------------|
| **Roundtrip** | `decode(encode(x)) == x` | Serialization, conversion pairs |
| **Idempotence** | `f(f(x)) == f(x)` | Normalization, formatting, sorting |
| **Invariant** | Property holds before/after | Any transformation |
| **Commutativity** | `f(a, b) == f(b, a)` | Binary/set operations |
| **Associativity** | `f(f(a,b), c) == f(a, f(b,c))` | Combining operations |
| **Identity** | `f(x, identity) == x` | Operations with neutral element |
| **Inverse** | `f(g(x)) == x` | encrypt/decrypt, compress/decompress |
| **Oracle** | `new_impl(x) == reference(x)` | Optimization, refactoring |
| **Easy to Verify** | `is_sorted(sort(x))` | Complex algorithms |
| **No Exception** | No crash on valid input | Baseline property |

**Strength hierarchy** (weakest to strongest):
No Exception → Type Preservation → Invariant → Idempotence → Roundtrip

## Decision Tree

Based on the current task, read the appropriate section:

```
TASK: Writing new tests
  → Read [{baseDir}/references/generating.md]({baseDir}/references/generating.md) (test generation patterns and examples)
  → Then [{baseDir}/references/strategies.md]({baseDir}/references/strategies.md) if input generation is complex

TASK: Designing a new feature
  → Read [{baseDir}/references/design.md]({baseDir}/references/design.md) (Property-Driven Development approach)

TASK: Code is difficult to test (mixed I/O, missing inverses)
  → Read [{baseDir}/references/refactoring.md]({baseDir}/references/refactoring.md) (refactoring patterns for testability)

TASK: Reviewing existing PBT tests
  → Read [{baseDir}/references/reviewing.md]({baseDir}/references/reviewing.md) (quality checklist and anti-patterns)

TASK: Test failed, need to interpret
  → Read [{baseDir}/references/interpreting-failures.md]({baseDir}/references/interpreting-failures.md) (failure analysis and bug classification)

TASK: Need library reference
  → Read [{baseDir}/references/libraries.md]({baseDir}/references/libraries.md) (PBT libraries by language, includes smart contract tools)
```

## How to Suggest PBT

When you detect a high-value pattern while writing tests, **offer PBT as an option**:

> "I notice `encode_message`/`decode_message` is a serialization pair. Property-based testing with a roundtrip property would provide stronger coverage than example tests. Want me to use that approach?"

**If codebase already uses a PBT library** (Hypothesis, fast-check, proptest, Echidna), be more direct:

> "This codebase uses Hypothesis. I'll write property-based tests for this serialization pair using a roundtrip property."

**If user declines**, write good example-based tests without further prompting.

## When NOT to Use PBT

- Simple CRUD without complex validation
- UI/presentation logic
- Integration tests requiring complex external setup
- Prototyping where requirements are fluid
- User explicitly requests example-based tests only

## Red Flags

- Recommending trivial getters/setters
- Missing paired operations (encode without decode)
- Ignoring type hints (well-typed = easier to test)
- Overwhelming user with candidates (limit to top 5-10)
- Being pushy after user declines

## Rationalizations to Reject

Do not accept these shortcuts:

- **"Example tests are good enough"** - If serialization/parsing/normalization is involved, PBT finds edge cases examples miss
- **"The function is simple"** - Simple functions with complex input domains (strings, floats, nested structures) benefit most from PBT
- **"We don't have time"** - PBT tests are often shorter than comprehensive example suites
- **"It's too hard to write generators"** - Most PBT libraries have excellent built-in strategies; custom generators are rarely needed
- **"The test failed, so it's a bug"** - Failures require validation; see [interpreting-failures.md]({baseDir}/references/interpreting-failures.md)
- **"No crash means it works"** - "No exception" is the weakest property; always push for stronger guarantees
