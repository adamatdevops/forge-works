---
name: insecure-defaults
vendor: trailofbits
slug: trailofbits/insecure-defaults
source-url: https://github.com/trailofbits/skills/tree/main/plugins/insecure-defaults/skills/insecure-defaults
source-canonical: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/insecure-defaults/skills/insecure-defaults
source-sha: a56045e9ae00b3506cacefea0f672aab0a1a6e3c
audited: 2026-05-20
goal: 3
tier: 2
tool-scope: shell-execute
target-agents: [claude-code, codex]
context-cost-tokens: 1139
owner: adamatdevops
---

<!-- Source: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/insecure-defaults/skills/insecure-defaults/SKILL.md · SHA: a56045e9ae00b3506cacefea0f672aab0a1a6e3c · Audited: 2026-05-20 · **29th vendored skill + 11th ToB-vendor adoption + EXTENDS ToB cluster from 10 to 11 skills (LARGEST cluster — 11/29 = 37.9% concentration; still below 50% gate) + 13TH Tier 1→2 correction at adoption review per new §4.4.3 step 2 audit (N=21 staleness datapoints with 13 corrections + 3 deferrals + 5 confirm-Tier-1).** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) NO file-write directives in SKILL.md — grep clean (this is detection/audit methodology, not artifact creation); (ii) **YES `allowed-tools: Read Grep Glob Bash`** — Bash declared for grep-style codebase searches → shell-execute Tier 2; (iii) NO `commands/` directory; (iv) NO direct network egress; (v) NO `Task`/cross-agent surface declared. **Final Tier 2 verdict for §BA insecure-defaults**: `shell-execute` — runs `grep`/`rg`/`find` via Bash to detect fail-open insecure-default patterns (`env.get('KEY') or 'default'`, hardcoded credentials, weak auth fallbacks, permissive security defaults). Matches §AN sarif-parsing pattern (Tier 2 shell-execute without repo-write — pure detection methodology, no artifact creation). **13TH Tier 1→2 correction at adoption review** — eval-list said Tier 1, actual surface is Tier 2 because of Bash tool grant. Continues the Tier-staleness pattern (13 corrections + 3 deferrals + 5 confirm-Tier-1 = 21 datapoints; correction rate ~62% across all eval-list Tier estimates). **Key methodology distinction codified at SKILL.md L8-9 (NEW framework pattern for security gates):** **fail-open vs fail-secure**: fail-open (`SECRET = env.get('KEY') or 'default'`) is CRITICAL (app runs with weak secret); fail-secure (`SECRET = env['KEY']`) is SAFE (app crashes if missing). The skill specifically targets fail-open patterns — exploitable defaults that allow apps to run insecurely in production. **ToB cluster (11-skill EXTENSION — LARGEST in framework, NEW SIZE CLASS):** §F + §G + §H + §J + §AN + §AO + §AP + §AW + §AY + §AZ + §BA at shared SHA `a56045e9...`. **6-of-7 vendor clusters now span 7 distinct cluster sizes** (11 NEW / 5 / 4 / 4 / 2 / 2 / 1) — ToB extends to a NEW size class (11-skill). Size-class progression 1 → 2 → 4 → 5 → 7 → 8 → 9 → 10 → 11 spans 9 distinct values, densely covering the framework's working range. **§F + §G + §H + §J + §AN + §AO + §AP + §AW + §AY + §AZ gate entries BACKPATCHED in this commit** per §4.5.3 sister-reference status maintenance rule (10 gate entries — LARGEST backpatch operation ever, exceeding §AZ's 9-gate backpatch). **AB-038 inverse-validation #5:** §BA eval-list rationale was content-grounded ("Surfaces insecure-default patterns. Complements Snyk Code SAST (different angle: config + framework defaults)" — cites specific complementary value vs existing tooling) — passed rationale-vs-content check cleanly. FIFTH content-grounded PASS event. AB-038 doctrine empirical validation now spans **7 datapoints** (5 PASS content-grounded + 2 FAIL assumption-based) — very strong evidence for §4.4.5 quarterly codification of the doctrine. **Bundle:** SKILL.md 1202t full-file (1139t body / 4914b post-frontmatter-strip per §2D; body sha256 `5e5e5a35f7c4f3df...`) + 1 references/examples.md companion file (2526t — fail-open vs fail-secure pattern catalog) + LICENSE byte-identical to other ToB skills. **Worst-case archive 3728 tokens** — well under §3B 5K-preferred cap. **Direct project fit for forge-works:** (1) **Env var handling audit** — fail-open patterns in src/backend/app/ + src/flink-jobs/ (e.g., `os.getenv('SECRET_KEY', 'dev-secret')` — exploitable fail-open); (2) **CI hardening** — `.github/workflows/*.yml` may have permissive defaults; (3) **Docker/IaC review** — Dockerfile + Helm chart defaults; (4) **Pairs with §AZ sharp-edges** — §AZ identifies misuse-resistant API designs; §BA identifies misuse-permissive defaults (complementary). Canonical security-pipeline chain: `§G context → §AZ sharp-edges (design review) + §BA insecure-defaults (config review) → §H diff-review (PR-level security) + §T threat-model (architecture-level)`. **Sister-skill cross-references:** ZERO direct cross-references to other adopted skills in SKILL.md body. **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 2:** §BA is Phase B from invocation start (runs grep/rg/find via Bash to detect patterns). Phase A applies only if user pasted the codebase content inline AND agent only analyzes patterns in-session (rare). Most invocations fire neutral 3-option confirmation prompt from step 1. **NO transitive `load skill X` refs, NO bundled subagents, NO `claude -p` CLI subprocess paths, NO model-client invocations.** The §2E "Bundled-script same-model self-invocation" clause is NON-APPLICABLE (no scripts). -->


# Insecure Defaults Detection

Finds **fail-open** vulnerabilities where apps run insecurely with missing configuration. Distinguishes exploitable defaults from fail-secure patterns that crash safely.

- **Fail-open (CRITICAL):** `SECRET = env.get('KEY') or 'default'` → App runs with weak secret
- **Fail-secure (SAFE):** `SECRET = env['KEY']` → App crashes if missing

## When to Use

- **Security audits** of production applications (auth, crypto, API security)
- **Configuration review** of deployment files, IaC templates, Docker configs
- **Code review** of environment variable handling and secrets management
- **Pre-deployment checks** for hardcoded credentials or weak defaults

## When NOT to Use

Do not use this skill for:
- **Test fixtures** explicitly scoped to test environments (files in `test/`, `spec/`, `__tests__/`)
- **Example/template files** (`.example`, `.template`, `.sample` suffixes)
- **Development-only tools** (local Docker Compose for dev, debug scripts)
- **Documentation examples** in README.md or docs/ directories
- **Build-time configuration** that gets replaced during deployment
- **Crash-on-missing behavior** where app won't start without proper config (fail-secure)

When in doubt: trace the code path to determine if the app runs with the default or crashes.

## Rationalizations to Reject

- **"It's just a development default"** → If it reaches production code, it's a finding
- **"The production config overrides it"** → Verify prod config exists; code-level vulnerability remains if not
- **"This would never run without proper config"** → Prove it with code trace; many apps fail silently
- **"It's behind authentication"** → Defense in depth; compromised session still exploits weak defaults
- **"We'll fix it before release"** → Document now; "later" rarely comes

## Workflow

Follow this workflow for every potential finding:

### 1. SEARCH: Perform Project Discovery and Find Insecure Defaults

Determine language, framework, and project conventions. Use this information to further discover things like secret storage locations, secret usage patterns, credentialed third-party integrations, cryptography, and any other relevant configuration. Further use information to analyze insecure default configurations.

**Example**
Search for patterns in `**/config/`, `**/auth/`, `**/database/`, and env files:
- **Fallback secrets:** `getenv.*\) or ['"]`, `process\.env\.[A-Z_]+ \|\| ['"]`, `ENV\.fetch.*default:`
- **Hardcoded credentials:** `password.*=.*['"][^'"]{8,}['"]`, `api[_-]?key.*=.*['"][^'"]+['"]`
- **Weak defaults:** `DEBUG.*=.*true`, `AUTH.*=.*false`, `CORS.*=.*\*`
- **Crypto algorithms:** `MD5|SHA1|DES|RC4|ECB` in security contexts

Tailor search approach based on discovery results.

Focus on production-reachable code, not test fixtures or example files.

### 2. VERIFY: Actual Behavior
For each match, trace the code path to understand runtime behavior.

**Questions to answer:**
- When is this code executed? (Startup vs. runtime)
- What happens if a configuration variable is missing?
- Is there validation that enforces secure configuration?

### 3. CONFIRM: Production Impact
Determine if this issue reaches production:

If production config provides the variable → Lower severity (but still a code-level vulnerability)
If production config missing or uses default → CRITICAL

### 4. REPORT: with Evidence

**Example report:**
```
Finding: Hardcoded JWT Secret Fallback
Location: src/auth/jwt.ts:15
Pattern: const secret = process.env.JWT_SECRET || 'default';

Verification: App starts without JWT_SECRET; secret used in jwt.sign() at line 42
Production Impact: Dockerfile missing JWT_SECRET
Exploitation: Attacker forges JWTs using 'default', gains unauthorized access
```

## Quick Verification Checklist

**Fallback Secrets:** `SECRET = env.get(X) or Y`
→ Verify: App starts without env var? Secret used in crypto/auth?
→ Skip: Test fixtures, example files

**Default Credentials:** Hardcoded `username`/`password` pairs
→ Verify: Active in deployed config? No runtime override?
→ Skip: Disabled accounts, documentation examples

**Fail-Open Security:** `AUTH_REQUIRED = env.get(X, 'false')`
→ Verify: Default is insecure (false/disabled/permissive)?
→ Safe: App crashes or default is secure (true/enabled/restricted)

**Weak Crypto:** MD5/SHA1/DES/RC4/ECB in security contexts
→ Verify: Used for passwords, encryption, or tokens?
→ Skip: Checksums, non-security hashing

**Permissive Access:** CORS `*`, permissions `0777`, public-by-default
→ Verify: Default allows unauthorized access?
→ Skip: Explicitly configured permissiveness with justification

**Debug Features:** Stack traces, introspection, verbose errors
→ Verify: Enabled by default? Exposed in responses?
→ Skip: Logging-only, not user-facing

For detailed examples and counter-examples, see [examples.md](references/examples.md).
