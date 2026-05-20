---
name: sharp-edges
vendor: trailofbits
slug: trailofbits/sharp-edges
source-url: https://github.com/trailofbits/skills/tree/main/plugins/sharp-edges/skills/sharp-edges
source-canonical: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/sharp-edges/skills/sharp-edges
source-sha: a56045e9ae00b3506cacefea0f672aab0a1a6e3c
audited: 2026-05-20
goal: 3
tier: 1
tool-scope: read-only
target-agents: [claude-code, codex]
context-cost-tokens: 2476
owner: adamatdevops
---

<!-- Source: https://github.com/trailofbits/skills/tree/a56045e9ae00b3506cacefea0f672aab0a1a6e3c/plugins/sharp-edges/skills/sharp-edges/SKILL.md · SHA: a56045e9ae00b3506cacefea0f672aab0a1a6e3c · Audited: 2026-05-20 · **28th vendored skill + 10th ToB-vendor adoption + EXTENDS ToB cluster from 9 to 10 skills (LARGEST cluster — 10/28 = 35.7% concentration; still below 50% gate) + 14TH consecutive Tier 1 estimate-confirm at adoption review per new §4.4.3 step 2 audit (N=20 staleness datapoints with 12 corrections + 3 deferrals + 5 confirm-Tier-1) + NEW worst-case-archive maximum (34,233 tokens — exceeds §AO codeql's 27,298 by ~25%) + BUNDLED SUB-AGENT with EXACT-subset tool grants (§2E condition (b) carve-out applies cleanly; READ-ONLY parent + READ-ONLY child = simplest carve-out case yet).** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **NO file-write directives** — grep'd SKILL.md; all `.md` mentions are companion-file references (`See [config-patterns.md](references/config-patterns.md)`), NOT file CREATE; (ii) **YES `allowed-tools: Read Grep Glob` declared** — explicitly READ-ONLY with pattern matching → Tier 1; (iii) NO `commands/` directory; (iv) NO network egress; (v) **YES `Task`/cross-agent surface — bundled sub-agent at `agents/sharp-edges-analyzer.md`** with `tools: Read, Grep, Glob` (EXACT subset of parent skill's `allowed-tools: Read Grep Glob`). Per §AGENT_SKILLS.md §2E same-model bounded-subagent carve-out condition (b) vendored-named: same model family ✓; no external API ✓; child grant set ⊆ parent grant set (EXACT match ✓); bounded by audited source ✓. **All 4 carve-out conditions hold → §AZ Tier 1 (not Tier 3)** — the bundled sub-agent qualifies for the simplest case of the carve-out (read-only parent + read-only child); no intra-skill Tier-3 escalation gate required (distinct from §AP semgrep which has Bash + Task escalation gate). **Final Tier 1 verdict for §AZ sharp-edges**: `read-only` — pure security-design-analysis methodology emitting inline-transcript content. **14TH adoption to maintain Tier 1 estimate** (after §J/§AG/§AH/§AJ/§AK/§AL/§AM/§AU/§AV/§AY + the inline-output normative elevation; 5 confirm-Tier-1 datapoints now). **NEW WORST-CASE ARCHIVE MAXIMUM (34,233 tokens):** SKILL.md 2565t + 16 references/*.md companion files (28,934t total: auth-patterns 1682 + case-studies 2009 + config-patterns 2254 + crypto-apis 1275 + lang-c 1530 + lang-csharp 1803 + lang-go 1815 + lang-java 1695 + lang-javascript 1871 + lang-kotlin 1688 + lang-php 1784 + lang-python 1832 + lang-ruby 1742 + lang-rust 1800 + lang-swift 1641 + language-specific 3513) + agents/sharp-edges-analyzer.md 1734t + LICENSE byte-identical to other ToB skills. **Exceeds §3B 5K-preferred cap by ~6.8x** — flagged per §3B archive-load metering. Acknowledged: the 11 language-specific reference files (lang-*.md) are load-on-demand (agent reads them WHEN reviewing code in the matching language); the 5 cross-cutting references (auth-patterns, case-studies, config-patterns, crypto-apis, language-specific) are also load-on-demand per the SKILL.md L259-262 "See" references. The CORE methodology in SKILL.md alone is 2565t — manageable. **ToB cluster (10-skill EXTENSION — LARGEST in framework, NEW SIZE CLASS):** §F + §G + §H + §J + §AN + §AO + §AP + §AW + §AY + §AZ at shared SHA `a56045e9...`. **6-of-7 vendor clusters now span 7 distinct cluster sizes** (10 NEW / 5 / 4 / 4 / 2 / 2 / 1) — ToB extends to a NEW size class (10-skill, double-digit). The size-class progression 1 → 2 → 4 → 5 → 7 → 8 → 9 → 10 now spans 8 distinct values, densely covering the framework's working range. **§F + §G + §H + §J + §AN + §AO + §AP + §AW + §AY gate entries BACKPATCHED** per §4.5.3 sister-reference status maintenance rule (9 gate entries — largest backpatch operation yet). **AB-038 inverse-validation #4:** §AZ eval-list rationale was content-grounded ("Language/framework footguns. Complements modern-python with cross-language coverage (Java/TS)" — cites specific cross-language need) — passed rationale-vs-content check cleanly. FOURTH content-grounded PASS event. AB-038 doctrine empirical validation now spans **6 datapoints** (4 PASS content-grounded + 2 FAIL assumption-based) — strong evidence for §4.4.5 quarterly codification. **Bundled sub-agent `agents/sharp-edges-analyzer.md`** — same-model bounded-subagent carve-out per §2E condition (b) vendored-named. THIRD framework adoption with bundled sub-agent (after §D anthropics/skill-creator's 3 sub-agents + §AP semgrep's semgrep-scanner). Distinct from §AP: §AP's bundled sub-agent has Bash tool (shell-execute, intra-skill Tier-3 escalation gate required); §AZ's bundled sub-agent has READ-ONLY tools (Read/Grep/Glob — EXACT subset of parent skill's grants). The simplest sub-agent carve-out case in framework. **§AZ → §H differential-review canonical chain:** §AZ identifies sharp-edge API/configuration designs; findings feed into §H differential-review for PR-level security review. **§AZ pairs with §G audit-context-building** (§G provides deep code understanding before §AZ runs the four-phase workflow on the surface). Canonical security-design-review chain: `§G context → §AZ sharp-edges → §H diff-review (or §T threat-model)`. **Direct project fit for forge-works:** (1) Flink Java sharp-edge review — lang-java.md companion file covers Java-specific footguns (Serializable, ThreadLocal, etc.); (2) Frontend TS strict-mode patterns — lang-javascript.md covers JS/TS footguns; (3) Crypto API review — crypto-apis.md companion catalogs OpenSSL/GMP/etc. case-study patterns; (4) Configuration schema review — config-patterns.md catalogs dangerous-default patterns (relevant for forge-works' CUE schemas + Pydantic models). **Sister-skill cross-references:** ZERO direct cross-references to other adopted skills in SKILL.md body. The bundled sub-agent itself references the references/*.md files at runtime ("reads language-specific references on demand" per SKILL.md L27). **No transitive `load skill X` refs, NO `claude -p` CLI subprocess paths, NO model-client invocations** across the 18-file bundle. The §2E "Bundled-script same-model self-invocation" clause is NON-APPLICABLE (no scripts, no model-client invocations in sub-agent). **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 1:** §AZ is read-only methodology — NO Phase-A/Phase-B gate; per AGENTS.md §3.2 advisory-only, agent emits sharp-edges-analysis findings + four-phase workflow (Surface Identification → Edge Case Probing → Threat Modeling → Validate Findings) as inline transcript content. -->


# Sharp Edges Analysis

Evaluates whether APIs, configurations, and interfaces are resistant to developer misuse. Identifies designs where the "easy path" leads to insecurity.

## When to Use

- Reviewing API or library design decisions
- Auditing configuration schemas for dangerous options
- Evaluating cryptographic API ergonomics
- Assessing authentication/authorization interfaces
- Reviewing any code that exposes security-relevant choices to developers

## When NOT to Use

- Implementation bugs (use standard code review)
- Business logic flaws (use domain-specific analysis)
- Performance optimization (different concern)

## Agent

The `sharp-edges-analyzer` agent runs the full sharp edges analysis workflow autonomously. Use it when you want a dedicated analysis of APIs, configurations, or interfaces for misuse resistance and footgun potential. The agent follows the four-phase workflow (Surface Identification, Edge Case Probing, Threat Modeling, Validate Findings) and reads language-specific references on demand.

## Core Principle

**The pit of success**: Secure usage should be the path of least resistance. If developers must understand cryptography, read documentation carefully, or remember special rules to avoid vulnerabilities, the API has failed.

## Rationalizations to Reject

| Rationalization | Why It's Wrong | Required Action |
|-----------------|----------------|-----------------|
| "It's documented" | Developers don't read docs under deadline pressure | Make the secure choice the default or only option |
| "Advanced users need flexibility" | Flexibility creates footguns; most "advanced" usage is copy-paste | Provide safe high-level APIs; hide primitives |
| "It's the developer's responsibility" | Blame-shifting; you designed the footgun | Remove the footgun or make it impossible to misuse |
| "Nobody would actually do that" | Developers do everything imaginable under pressure | Assume maximum developer confusion |
| "It's just a configuration option" | Config is code; wrong configs ship to production | Validate configs; reject dangerous combinations |
| "We need backwards compatibility" | Insecure defaults can't be grandfather-claused | Deprecate loudly; force migration |

## Sharp Edge Categories

### 1. Algorithm/Mode Selection Footguns

APIs that let developers choose algorithms invite choosing wrong ones.

**The JWT Pattern** (canonical example):
- Header specifies algorithm: attacker can set `"alg": "none"` to bypass signatures
- Algorithm confusion: RSA public key used as HMAC secret when switching RS256→HS256
- Root cause: Letting untrusted input control security-critical decisions

**Detection patterns:**
- Function parameters like `algorithm`, `mode`, `cipher`, `hash_type`
- Enums/strings selecting cryptographic primitives
- Configuration options for security mechanisms

**Example - PHP password_hash allowing weak algorithms:**
```php
// DANGEROUS: allows crc32, md5, sha1
password_hash($password, PASSWORD_DEFAULT); // Good - no choice
hash($algorithm, $password); // BAD: accepts "crc32"
```

### 2. Dangerous Defaults

Defaults that are insecure, or zero/empty values that disable security.

**The OTP Lifetime Pattern:**
```python
# What happens when lifetime=0?
def verify_otp(code, lifetime=300):  # 300 seconds default
    if lifetime == 0:
        return True  # OOPS: 0 means "accept all"?
        # Or does it mean "expired immediately"?
```

**Detection patterns:**
- Timeouts/lifetimes that accept 0 (infinite? immediate expiry?)
- Empty strings that bypass checks
- Null values that skip validation
- Boolean defaults that disable security features
- Negative values with undefined semantics

**Questions to ask:**
- What happens with `timeout=0`? `max_attempts=0`? `key=""`?
- Is the default the most secure option?
- Can any default value disable security entirely?

### 3. Primitive vs. Semantic APIs

APIs that expose raw bytes instead of meaningful types invite type confusion.

**The Libsodium vs. Halite Pattern:**

```php
// Libsodium (primitives): bytes are bytes
sodium_crypto_box($message, $nonce, $keypair);
// Easy to: swap nonce/keypair, reuse nonces, use wrong key type

// Halite (semantic): types enforce correct usage
Crypto::seal($message, new EncryptionPublicKey($key));
// Wrong key type = type error, not silent failure
```

**Detection patterns:**
- Functions taking `bytes`, `string`, `[]byte` for distinct security concepts
- Parameters that could be swapped without type errors
- Same type used for keys, nonces, ciphertexts, signatures

**The comparison footgun:**
```go
// Timing-safe comparison looks identical to unsafe
if hmac == expected { }           // BAD: timing attack
if hmac.Equal(mac, expected) { }  // Good: constant-time
// Same types, different security properties
```

### 4. Configuration Cliffs

One wrong setting creates catastrophic failure, with no warning.

**Detection patterns:**
- Boolean flags that disable security entirely
- String configs that aren't validated
- Combinations of settings that interact dangerously
- Environment variables that override security settings
- Constructor parameters with sensible defaults but no validation (callers can override with insecure values)

**Examples:**
```yaml
# One typo = disaster
verify_ssl: fasle  # Typo silently accepted as truthy?

# Magic values
session_timeout: -1  # Does this mean "never expire"?

# Dangerous combinations accepted silently
auth_required: true
bypass_auth_for_health_checks: true
health_check_path: "/"  # Oops
```

```php
// Sensible default doesn't protect against bad callers
public function __construct(
    public string $hashAlgo = 'sha256',  // Good default...
    public int $otpLifetime = 120,       // ...but accepts md5, 0, etc.
) {}
```

See [config-patterns.md](references/config-patterns.md#unvalidated-constructor-parameters) for detailed patterns.

### 5. Silent Failures

Errors that don't surface, or success that masks failure.

**Detection patterns:**
- Functions returning booleans instead of throwing on security failures
- Empty catch blocks around security operations
- Default values substituted on parse errors
- Verification functions that "succeed" on malformed input

**Examples:**
```python
# Silent bypass
def verify_signature(sig, data, key):
    if not key:
        return True  # No key = skip verification?!

# Return value ignored
signature.verify(data, sig)  # Throws on failure
crypto.verify(data, sig)     # Returns False on failure
# Developer forgets to check return value
```

### 6. Stringly-Typed Security

Security-critical values as plain strings enable injection and confusion.

**Detection patterns:**
- SQL/commands built from string concatenation
- Permissions as comma-separated strings
- Roles/scopes as arbitrary strings instead of enums
- URLs constructed by joining strings

**The permission accumulation footgun:**
```python
permissions = "read,write"
permissions += ",admin"  # Too easy to escalate

# vs. type-safe
permissions = {Permission.READ, Permission.WRITE}
permissions.add(Permission.ADMIN)  # At least it's explicit
```

## Analysis Workflow

### Phase 1: Surface Identification

1. **Map security-relevant APIs**: authentication, authorization, cryptography, session management, input validation
2. **Identify developer choice points**: Where can developers select algorithms, configure timeouts, choose modes?
3. **Find configuration schemas**: Environment variables, config files, constructor parameters

### Phase 2: Edge Case Probing

For each choice point, ask:
- **Zero/empty/null**: What happens with `0`, `""`, `null`, `[]`?
- **Negative values**: What does `-1` mean? Infinite? Error?
- **Type confusion**: Can different security concepts be swapped?
- **Default values**: Is the default secure? Is it documented?
- **Error paths**: What happens on invalid input? Silent acceptance?

### Phase 3: Threat Modeling

Consider three adversaries:

1. **The Scoundrel**: Actively malicious developer or attacker controlling config
   - Can they disable security via configuration?
   - Can they downgrade algorithms?
   - Can they inject malicious values?

2. **The Lazy Developer**: Copy-pastes examples, skips documentation
   - Will the first example they find be secure?
   - Is the path of least resistance secure?
   - Do error messages guide toward secure usage?

3. **The Confused Developer**: Misunderstands the API
   - Can they swap parameters without type errors?
   - Can they use the wrong key/algorithm/mode by accident?
   - Are failure modes obvious or silent?

### Phase 4: Validate Findings

For each identified sharp edge:

1. **Reproduce the misuse**: Write minimal code demonstrating the footgun
2. **Verify exploitability**: Does the misuse create a real vulnerability?
3. **Check documentation**: Is the danger documented? (Documentation doesn't excuse bad design, but affects severity)
4. **Test mitigations**: Can the API be used safely with reasonable effort?

If a finding seems questionable, return to Phase 2 and probe more edge cases.

## Severity Classification

| Severity | Criteria | Examples |
|----------|----------|----------|
| Critical | Default or obvious usage is insecure | `verify: false` default; empty password allowed |
| High | Easy misconfiguration breaks security | Algorithm parameter accepts "none" |
| Medium | Unusual but possible misconfiguration | Negative timeout has unexpected meaning |
| Low | Requires deliberate misuse | Obscure parameter combination |

## References

**By category:**

- **Cryptographic APIs**: See [references/crypto-apis.md](references/crypto-apis.md)
- **Configuration Patterns**: See [references/config-patterns.md](references/config-patterns.md)
- **Authentication/Session**: See [references/auth-patterns.md](references/auth-patterns.md)
- **Real-World Case Studies**: See [references/case-studies.md](references/case-studies.md) (OpenSSL, GMP, etc.)

**By language** (general footguns, not crypto-specific):

| Language | Guide |
|----------|-------|
| C/C++ | [references/lang-c.md](references/lang-c.md) |
| Go | [references/lang-go.md](references/lang-go.md) |
| Rust | [references/lang-rust.md](references/lang-rust.md) |
| Swift | [references/lang-swift.md](references/lang-swift.md) |
| Java | [references/lang-java.md](references/lang-java.md) |
| Kotlin | [references/lang-kotlin.md](references/lang-kotlin.md) |
| C# | [references/lang-csharp.md](references/lang-csharp.md) |
| PHP | [references/lang-php.md](references/lang-php.md) |
| JavaScript/TypeScript | [references/lang-javascript.md](references/lang-javascript.md) |
| Python | [references/lang-python.md](references/lang-python.md) |
| Ruby | [references/lang-ruby.md](references/lang-ruby.md) |

See also [references/language-specific.md](references/language-specific.md) for a combined quick reference.

## Quality Checklist

Before concluding analysis:

- [ ] Probed all zero/empty/null edge cases
- [ ] Verified defaults are secure
- [ ] Checked for algorithm/mode selection footguns
- [ ] Tested type confusion between security concepts
- [ ] Considered all three adversary types
- [ ] Verified error paths don't bypass security
- [ ] Checked configuration validation
- [ ] Constructor params validated (not just defaulted) - see [config-patterns.md](references/config-patterns.md#unvalidated-constructor-parameters)
