---
name: webapp-testing
vendor: anthropics
slug: anthropics/webapp-testing
source-url: https://github.com/anthropics/skills/tree/main/skills/webapp-testing
source-canonical: https://github.com/anthropics/skills/tree/b9e19e6f44773509fbdd7001d77ff41a49a486c1/skills/webapp-testing
source-sha: b9e19e6f44773509fbdd7001d77ff41a49a486c1
audited: 2026-05-20
goal: 2
tier: 2
tool-scope: shell-execute+repo-write
target-agents: [claude-code, codex]
context-cost-tokens: 832
owner: adamatdevops
---

<!-- Source: https://github.com/anthropics/skills/tree/b9e19e6f44773509fbdd7001d77ff41a49a486c1/skills/webapp-testing/SKILL.md · SHA: b9e19e6f44773509fbdd7001d77ff41a49a486c1 · Audited: 2026-05-20 · **21st vendored skill + 4th Anthropic-first-party adoption (after §D skill-creator + §A doc-coauthoring + §AQ mcp-builder) + FIRST Anthropic cluster (§AQ + §AS at shared SHA `b9e19e6f...`) + FIFTH cluster overall in framework (after hamelsmu 5-skill / ToB 7-skill / obra 2-skill / CodeRabbit 2-skill) + TENTH Tier 1→2 correction at adoption review per new §4.4.3 step 2 audit (N=13 Tier-staleness datapoints now: 10 corrections + 3 deferrals from 6 vendors) + FIRST framework adoption with Playwright browser-automation surface that was DEFERRED at AB-034 (build-review-interface).** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **YES — file-write directives in SKILL.md L9-10 ("write native Python Playwright scripts")**: agent CREATES Playwright test scripts (e.g., `your_automation.py`) per L41/L46 invocation examples — file CREATE per §J R3-A-3 → Tier 2. (ii) NO `allowed-tools` frontmatter (host's default tool envelope — same pattern as §AM/§AQ); (iii) NO `commands/` directory; (iv) NO network egress in SKILL.md body — Playwright launches LOCAL chromium in headless mode (L57 "headless=True") to test LOCAL webapp at user-specified URLs (typically `localhost:<port>`); no external network calls declared; (v) NO `Task` tool / cross-agent surface declared. **Final Tier 2 verdict for §AS webapp-testing**: `shell-execute+repo-write` — runs `python scripts/with_server.py` via Bash + creates Playwright test scripts via Write tool. Matches §AQ mcp-builder + §D skill-creator tool-scope pattern. **Bundled-script audit (per §4.4.3 step 1 R2-2 hardening):** `scripts/with_server.py` (3693 bytes / 813t) — `import subprocess` + `subprocess.Popen(..., shell=True, ...)` at L68-71 (process-spawn with `shell=True` — security-relevant because user-controlled `--server` arg becomes shell input; the script's safety relies on user authorization at agent-invocation time, not on shell-quoting). ✅ NO `claude`/`anthropic`/`messages.create`/SDK tokens — pure server-lifecycle management script. Per §2E "Bundled-script same-model self-invocation" clause: NON-APPLICABLE (no model-client invocation). **SKILL.md DIRECTS agent to run `python scripts/with_server.py`** at L25 + L41 + L46 + L85 — this is in-scope agent-execution; the script runs as a host-managed subprocess via Bash tool (same execution boundary as the agent, NOT cross-agent per §2E predicate). The shell-execute surface is acknowledged in the tool-scope declaration. **`examples/*.py` audit (3 files, 845t total):** `console_logging.py` 254t — Playwright pattern for capturing browser console messages; `element_discovery.py` 361t — Playwright pattern for finding selectors; `static_html_automation.py` 230t — Playwright pattern for static HTML. All three are reference examples the agent reads + adapts when writing user-specific Playwright scripts; NO subprocess / NO model-client tokens / NO shell=True. These are pure Playwright-API pattern documentation (analogous to §AM's `condition-based-waiting-example.ts` reference example). **Playwright browser-automation surface (NEW for framework):** §AS is the FIRST framework adoption with explicit Playwright (`playwright.sync_api`) usage. AB-034 (build-review-interface) was DEFERRED partly over Playwright browser-automation surface (per AB-034 trigger (c)); **§AS adopts the surface in a different application context** — §AS uses Playwright for TESTING existing webapps (local headless chromium → assertion-based test scripts the user runs), while AB-034 would have used Playwright for VERIFYING agent-built HTML annotation interfaces (Playwright as a verification step in a file-CREATE-heavy workflow). **§AS does NOT trigger AB-034 rescore** because the application contexts differ: §AS is testing-tool methodology (Playwright as the primary tool); AB-034 is file-CREATE methodology with Playwright as one verification step. **AB-034 status remains DEFERRED-CONFIRMED** post-§AS adoption (re-confirmed at 2026-Q3 quarterly per the §4.4.5 attestation rules). The Playwright surface is now established in the framework as Tier 2 shell-execute + repo-write (agent runs `python` scripts; agent writes `.py` Playwright test files); this is consistent with §AS's positioning as a TOOLKIT skill (Playwright is the tool, tests are the artifact). **`shell=True` security observation (NEW framework pattern surfaced):** §AS's `with_server.py` uses `subprocess.Popen(..., shell=True, ...)` to support compound commands like `cd subdir && npm run dev`. This is a security-relevant pattern — `shell=True` with user-supplied `--server` arg means the user's command becomes shell input (any quoting failure could allow command injection). The script's safety relies on: (a) user authorization at agent-invocation time (the agent reports the command being invoked, per Tier 2 Phase-A/Phase-B gate), (b) the script not parsing untrusted external input. Per §4.4.3 step 1 R2-2 hardening, this is acknowledged in the §AS Notes for provenance; future shell=True bundled scripts MUST be flagged similarly. The script's safety is ADEQUATE for §AS's use case (user explicitly authorizes the `--server` command at Phase-B gate) but the pattern is worth tracking for §4.4.5 quarterly review. **Anthropic cluster (FIRST):** §AQ + §AS share repo `anthropics/skills` + SHA `b9e19e6f...` — FIRST Anthropic cluster in framework. Per §4.4.5 cluster-co-adoption note, quarterly source-SHA review for the 2-skill Anthropic cluster MAY use one shared upstream check (but each Decision Record independently attested). §D + §A remain at DIFFERENT SHAs (`f458cee31...` + `6a5bb069...`) and are NOT part of the Anthropic cluster — they're solo Anthropic adoptions at distinct SHAs. **Cluster co-adoption pattern empirical validation EXTENDED:** with 5 clusters now (hamelsmu 5 / ToB 7 / obra 2 / CodeRabbit 2 / Anthropic 2), the §4.4.5 cluster-co-adoption pattern is validated across 5 vendor profiles + 5 cluster sizes + 4 Tier-mix shapes (hamelsmu all-Tier-1 / ToB mixed / obra Tier-1+Tier-1 / CodeRabbit all-Tier-3 / Anthropic Tier-2+Tier-2). Re-confirm STRONG case for 2026-Q3 normative elevation of the cluster-co-adoption rule. **§AQ gate entry BACKPATCHED in this commit** per §4.5.3 sister-reference status maintenance rule (codified at §AK): §AQ was previously solo on the cluster slot; now has §AS as cluster sibling at shared SHA. **Direct project fit for forge-works:** forge-works frontend is Next.js + vitest (per `src/frontend/`); §AS Playwright methodology directly applies to e2e testing the frontend. Pairs with `vitest run --coverage` workflow (existing CI). Phase 2 frontend coverage debt mentioned in eval-list line 90 is the canonical use case. **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 2:** §AS is Phase B from invocation start in most cases — Phase 1 begins with `python scripts/with_server.py --help` (Phase B Bash) per L25 + L41. Phase A applies only if user pre-supplies a fully-running localhost server AND agent only writes Playwright assertions against an in-session URL (rare). Most invocations fire neutral 3-option confirmation prompt from step 1. **Bundle:** SKILL.md 832t body + 4 companion files (3 examples 845t + 1 script 813t) + LICENSE.txt byte-identical to §AQ's (both at SHA `b9e19e6f...`). **Worst-case archive: 2539 tokens** — SMALLEST Tier-2 bundle in framework; well under §3B 5K-preferred cap (the 3 example .py files are referenced via L93-94 "examples/ - Examples showing common patterns"; agent loads them when Playwright pattern needed). **Body sha256:** `830bd54146bc08d4...`. NO transitive `load skill X` refs, NO bundled subagents, NO `claude -p` CLI subprocess paths, NO model-client invocations across the 4 companion files. **Sister-skill cross-references:** ZERO direct cross-references to other adopted skills (the only cross-reference is implicit cluster sibling with §AQ at shared SHA). **AB-038 doctrinal observation (filed inline; NOT a deferred-adoption entry):** §AS establishes the Playwright surface as Tier-2-shell-execute in the framework; future skills using Playwright in different application contexts (e.g., AB-034 build-review-interface if rescored) MUST follow the §AS pattern for browser-automation tier classification (NOT a new framework lift; Playwright is just another bundled-CLI surface under Tier 2 shell-execute when used for local testing). -->


# Web Application Testing

To test local web applications, write native Python Playwright scripts.

**Helper Scripts Available**:
- `scripts/with_server.py` - Manages server lifecycle (supports multiple servers)

**Always run scripts with `--help` first** to see usage. DO NOT read the source until you try running the script first and find that a customized solution is abslutely necessary. These scripts can be very large and thus pollute your context window. They exist to be called directly as black-box scripts rather than ingested into your context window.

## Decision Tree: Choosing Your Approach

```
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         ├─ Success → Write Playwright script using selectors
    │         └─ Fails/Incomplete → Treat as dynamic (below)
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Run: python scripts/with_server.py --help
        │        Then use the helper + write simplified Playwright script
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for networkidle
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Example: Using with_server.py

To start a server, run `--help` first, then use the helper:

**Single server:**
```bash
python scripts/with_server.py --server "npm run dev" --port 5173 -- python your_automation.py
```

**Multiple servers (e.g., backend + frontend):**
```bash
python scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_automation.py
```

To create an automation script, include only Playwright logic (servers are managed automatically):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Always launch chromium in headless mode
    page = browser.new_page()
    page.goto('http://localhost:5173') # Server already running and ready
    page.wait_for_load_state('networkidle') # CRITICAL: Wait for JS to execute
    # ... your automation logic
    browser.close()
```

## Reconnaissance-Then-Action Pattern

1. **Inspect rendered DOM**:
   ```python
   page.screenshot(path='/tmp/inspect.png', full_page=True)
   content = page.content()
   page.locator('button').all()
   ```

2. **Identify selectors** from inspection results

3. **Execute actions** using discovered selectors

## Common Pitfall

❌ **Don't** inspect the DOM before waiting for `networkidle` on dynamic apps
✅ **Do** wait for `page.wait_for_load_state('networkidle')` before inspection

## Best Practices

- **Use bundled scripts as black boxes** - To accomplish a task, consider whether one of the scripts available in `scripts/` can help. These scripts handle common, complex workflows reliably without cluttering the context window. Use `--help` to see usage, then invoke directly. 
- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Use descriptive selectors: `text=`, `role=`, CSS selectors, or IDs
- Add appropriate waits: `page.wait_for_selector()` or `page.wait_for_timeout()`

## Reference Files

- **examples/** - Examples showing common patterns:
  - `element_discovery.py` - Discovering buttons, links, and inputs on a page
  - `static_html_automation.py` - Using file:// URLs for local HTML
  - `console_logging.py` - Capturing console logs during automation
