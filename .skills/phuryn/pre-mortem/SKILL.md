---
name: pre-mortem
vendor: phuryn
slug: phuryn/pre-mortem
source-url: https://github.com/phuryn/pm-skills/tree/main/pm-execution/skills/pre-mortem
source-canonical: https://github.com/phuryn/pm-skills/tree/a372bee16dc2275e26078ca70a2eb7614ea316f7/pm-execution/skills/pre-mortem
source-sha: a372bee16dc2275e26078ca70a2eb7614ea316f7
audited: 2026-05-20
goal: 4
tier: 2
tool-scope: repo-write
target-agents: [claude-code, codex]
context-cost-tokens: 842
owner: adamatdevops
---

<!-- Source: https://github.com/phuryn/pm-skills/tree/a372bee16dc2275e26078ca70a2eb7614ea316f7/pm-execution/skills/pre-mortem/SKILL.md · SHA: a372bee16dc2275e26078ca70a2eb7614ea316f7 · Audited: 2026-05-20 · **26th vendored skill + NEW VENDOR (phuryn — Paweł Huryn, PM Skills Marketplace author) + FIRST adoption from phuryn vendor (NO cluster yet — solo phuryn adoption) + 7-vendor framework milestone (was 6 vendors; phuryn adds 7th) + TWELFTH Tier 1→2 correction at adoption review per new §4.4.3 step 2 audit (N=18 staleness datapoints with 12 corrections + 3 deferrals + 3 confirm-Tier-1) + SECOND new-vendor adoption since AB-038 codification + AB-038 doctrine FULLY VALIDATED across both failure mode (mattpocock: brand-based rationale → DEFERRED) + success mode (phuryn: content-grounded rationale → ADOPTED) — strongest empirical evidence for the AB-038 doctrine's predictive power.** **Vendor provenance audit (NEW VENDOR — first phuryn adoption):** upstream `phuryn/pm-skills` is a multi-skill plugin marketplace (created 2026-03-01, MIT-licensed, 11,442 stars, last updated 2026-05-20 — very active community-trusted repo) containing 100+ skills across 8 plugins (pm-data-analytics, pm-execution, pm-go-to-market, pm-market-research, pm-marketing-growth, pm-product-discovery, pm-product-strategy, pm-toolkit). Author: Paweł Huryn (Product Compass author). **AB-037-class consideration:** the upstream repo is a MULTI-SKILL PLUGIN AGGREGATOR, BUT the eval-list candidate name `pre-mortem` correctly maps to a SINGLE specific skill (`pm-execution/skills/pre-mortem`) — NOT the plugin-level aggregator name. The eval-list correctly scoped the candidate to a specific skill at the correct granularity, so AB-037 candidate-MISMATCH does NOT apply here (distinct from mattpocock where eval-list said "mattpocock/skills" which IS the plugin aggregator). **AB-038-class consideration:** the eval-list rationale "Pre-mortem analysis — direct fit for Decision Record 'Removal' reasoning + sprint pre-flight risk surfacing" is CONTENT-GROUNDED (cites specific use cases — Decision Record Removal reasoning + sprint pre-flight risk) — passes the AB-038 rationale-vs-content pre-check cleanly. Distinct from mattpocock failure mode of brand-only rationale ("TypeScript expertise (Matt Pocock = canonical TS author)" — brand reputation, not content-citing). **AB-038 doctrine FULLY VALIDATED:** mattpocock (brand-based) → DEFERRED + AB-038 filed; phuryn (content-grounded) → ADOPTED cleanly. The doctrine correctly discriminates between the two failure modes. **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **YES — explicit file-write directive at SKILL.md L79** "Save the Output: Save as a markdown document: `PreMortem-[product-name]-[date].md`" → file CREATE per §J R3-A-3 → Tier 2. SAME pattern as §T security-threat-model which CREATES `<repo-or-dir-name>-threat-model.md` as the Phase 8 output. (ii) NO `allowed-tools` frontmatter (host's default tool envelope); (iii) NO `commands/` directory in the vendored single-file bundle; (iv) **Optional web search reference** at SKILL.md L19 "If relevant, use web search to research competitive landscape or market conditions" — this is HOST-MEDIATED WebSearch (NOT skill-declared egress; consistent with §A doc-coauthoring's optional MCP integrations + §AQ mcp-builder's modelcontextprotocol.io WebFetch pattern); (v) NO `Task` tool / cross-agent surface. **Final Tier 2 verdict for §AX pre-mortem**: `repo-write` only (no shell-execute since SKILL.md doesn't direct Bash usage; file CREATE for the PreMortem-*.md output document is the load-bearing Tier-2 surface). Matches §T security-threat-model pattern (Tier 2 repo-write, single-artifact CREATE deliverable). **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 2:** §AX is overwhelmingly Phase B in most invocations — Step 7 "Save the Output" requires file-CREATE via Write tool. Phase A applies only if user explicitly requests inline pre-mortem analysis (transcript only) without saving the artifact (rare; the skill's primary value is the saved artifact for future reference). Most invocations fire neutral 3-option confirmation prompt from step 1. **Single-artifact write surface (NEW analysis matching §T precedent):** like §T, §AX produces a SINGLE markdown file as its primary deliverable. The 6-state path-type preflight matrix from §A (`REJECT_DIR_TARGET` / `OVERWRITE_REGULAR` / `OVERWRITE_SYMLINK` / `OVERWRITE_UNTRACKED_WARN` / `CREATE_NEW` / `CREATE_REQUIRES_PARENT`) applies because the user may specify a custom filename via `[product-name]-[date].md` naming pattern. Agent MUST preflight the target path before writing — if `OVERWRITE_REGULAR` or `OVERWRITE_UNTRACKED_WARN`, surface to user for confirmation; if `CREATE_NEW`, proceed under the Phase-B gate. **Methodology framework — Tiger / Paper Tiger / Elephant classification (DIRECT PROJECT FIT):** the 3-class risk taxonomy maps to forge-works' Decision Record "Removal procedure" reasoning + AB-NNN backlog risk-surfacing. **Tigers** (real risks, evidence-based) ↔ Decision Record blocking risks; **Paper Tigers** (overblown concerns) ↔ Decision Record carve-outs that look risky but aren't; **Elephants** (unspoken risks) ↔ AB-NNN backlog entries surfacing un-discussed concerns. Direct meta-applicability to the framework: the AB-036 + AB-037 + AB-038 candidate-resolution events are ELEPHANTS that pre-mortem methodology would have surfaced earlier (un-discussed concerns about candidate-vs-content mismatches). **Bundle:** SKILL.md 926t full-file (842t body / 3714b post-frontmatter-strip per §2D; body sha256 `c74a5aabc36bef24...`) + LICENSE byte-identical to phuryn/pm-skills repo-root LICENSE (MIT, 1068 bytes, 221t). **Worst-case archive 1147 tokens** — SMALLEST Tier-2 bundle in framework after §AS webapp-testing's 2539t (now SECOND-smallest Tier-2; §AX is the smallest); well under §3B 5K-preferred cap. No companion files, no scripts, no bundled subagents, no commands/. The §2E "Bundled-script same-model self-invocation" clause and the §2E same-model bounded-subagent carve-out are both **non-applicable** (no scripts, no subagents). **Sister-skill cross-references:** ZERO direct cross-references to other adopted skills. **NO cluster yet (solo phuryn adoption):** §AX is the first phuryn adoption; the framework's vendor list now grows from 6 to 7 vendors (ToB / hamelsmu / Anthropic / obra / CodeRabbit / OpenAI + **phuryn NEW**). Per §4.4.5 cluster-co-adoption note, cluster requires 2+ skills at SHARED SHA from the same vendor; §AX is solo so no cluster yet. **Future phuryn adoption candidates from same upstream repo** (for §4.4.5 quarterly consideration): phuryn/pm-skills contains 100+ skills across 8 plugins; pm-execution alone has 14 other skills (brainstorm-okrs, create-prd, dummy-dataset, job-stories, outcome-roadmap, prioritization-frameworks, release-notes, retro, sprint-plan, stakeholder-map, summarize-meeting, test-scenarios, user-stories, wwas); other plugins (pm-product-strategy, pm-go-to-market, etc.) likely have additional relevant skills. **Direct project fit for forge-works:** pre-mortem methodology applies to: (1) **Decision Record "Removal procedure" reasoning** — when authoring removal procedures for adopted skills, the Tiger/Paper Tiger/Elephant taxonomy systematizes risk identification beyond the current free-form approach; (2) **Sprint pre-flight risk surfacing** — before starting a sprint (e.g., Engine Phase 6 Decision Engine), running pre-mortem on the planned features identifies launch-blocking risks early; (3) **AB-NNN backlog entry authoring** — when filing new AB-NNN candidate-resolution events or backlog items, pre-mortem methodology helps surface unspoken concerns (Elephants); (4) **Flink 1.20→2.0 upgrade pre-flight** — pairs with §AW variant-analysis (post-CVE search) by providing the PRE-upgrade risk identification (§AX) → POST-upgrade variant search (§AW) chain. **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 2:** §AX is Phase B from step 6-7 (output structure + save). Step 1-5 (gather PRD, think step-by-step, categorize risks, classify by urgency, create action plans) are inline transcript content (Phase A). The Phase A → Phase B transition happens at Step 6 "Structure Output" when the agent prepares the markdown for save. Neutral 3-option confirmation prompt MUST fire before Step 7 `Save the Output` Write tool call. **NO transitive `load skill X` refs, NO bundled subagents, NO `claude -p` CLI subprocess paths, NO model-client invocations, NO companion files** — single-file SKILL.md with LICENSE only. **AB-038 doctrine refinement codified through §AX adoption:** the AB-038 rationale-vs-content pre-check now has 2 datapoints (mattpocock FAIL + phuryn PASS) — strong evidence the doctrine correctly discriminates between brand-based and content-grounded rationales. Future new-vendor adoptions MUST apply the AB-038 pre-check; the 2-datapoint validation suggests the doctrine catches what it should (false positives unlikely given the clean discrimination). -->


# Pre-Mortem: Risk Analysis for Product Launch

## Purpose

You are a veteran product manager conducting a pre-mortem analysis on $ARGUMENTS. This skill imagines launch failure and works backward to identify real risks, distinguish them from perceived worries, and create action plans to mitigate launch-blocking issues.

## Context

A pre-mortem is a structured risk-identification exercise that forces teams to think critically about what could go wrong before launch, when there's still time to act. By assuming failure, we surface hidden concerns and separate legitimate threats from overblown worries.

## Instructions

1. **Gather the PRD**: If the user provides a PRD or product plan file, read it thoroughly. Understand the product, target market, key assumptions, and timeline. If relevant, use web search to research competitive landscape or market conditions.

2. **Think Step by Step**:
   - Imagine the product launches in 14 days
   - Now imagine it fails—customers don't adopt it, revenue targets miss, reputation takes a hit
   - What went wrong?
   - What did we miss or not execute well?
   - What were we overconfident about?

3. **Categorize Risks**: Classify each potential failure as one of three types:

   **Tigers**: Real problems you personally see that could derail the project
   - Based on evidence, past experience, or clear logic
   - Should keep you awake at night
   - Require action

   **Paper Tigers**: Problems others might worry about, but you don't believe in them
   - Valid concerns on the surface, but unlikely or overblown
   - Not worth significant resource investment
   - Worth documenting to align stakeholders

   **Elephants**: Something you're not sure is a problem, but the team isn't discussing it enough
   - Unspoken concerns or assumptions nobody is validating
   - Could be real; you're unsure
   - Deserve investigation before launch

4. **Classify Tigers by Urgency**:

   **Launch-Blocking**: Must be solved before launch
   - Example: Core feature broken, regulatory blocker, key customer dependency unmet

   **Fast-Follow**: Must be solved within 30 days post-launch
   - Example: Performance issues, secondary features incomplete

   **Track**: Monitor post-launch; solve if it becomes an issue
   - Example: Nice-to-have features, edge cases

5. **Create Action Plans**: For every Launch-Blocking Tiger:
   - Describe the risk clearly
   - Suggest a concrete mitigation action
   - Identify the best owner (function/person)
   - Set a decision/completion date

6. **Structure Output**: Present the analysis as:

   ```
   ## Pre-Mortem Analysis: [Product Name]

   ### Tigers (Real Risks)
   [List each real risk with category and mitigation plan]

   ### Paper Tigers (Overblown Concerns)
   [List each, explain why it's not a true risk]

   ### Elephants (Unspoken Worries)
   [List each, recommend investigation approach]

   ### Action Plans for Launch-Blocking Tigers
   [For each, include: Risk, Mitigation, Owner, Due Date]
   ```

7. **Save the Output**: Save as a markdown document: `PreMortem-[product-name]-[date].md`

## Notes

- Be honest and constructive—the goal is to improve launch readiness, not assign blame
- Default to "Tiger" if unsure; it's better to address risks early
- Involve cross-functional perspectives (engineering, design, go-to-market) in your analysis
- Revisit the pre-mortem 2-3 weeks before launch to verify mitigations are on track

---

### Further Reading

- [How Meta and Instagram Use Pre-Mortems to Avoid Post-Mortems](https://www.productcompass.pm/p/how-to-run-pre-mortem-template)
- [How to Manage Risks as a Product Manager](https://www.productcompass.pm/p/how-to-manage-risks-as-a-product-manager)
