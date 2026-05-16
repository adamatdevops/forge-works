# forge-skills-mcp

Dual-agent skill loader for forge-works. Both **Claude Code** and **Codex CLI** register this as an MCP server and load skills from `.skills/<vendor>/<slug>/SKILL.md` identically.

Phase 1 of `roadmap/ACTION_PLAN_SKILL_LOADERS.md`. Tracked as **AB-022** in `roadmap/AUTOMATIONS_BACKLOG.md`.

---

## Why this exists

Upstream `claude-skills-mcp` v1.0.0 was broken when forge-works needed a working dual-agent loader (silent backend no-start; remote mode unimplemented; surfaced 2026-05-15). We needed:

- Identical skill content delivered to both agents
- Server-side doctrine enforcement (SHA-pinning per `AGENT_SKILLS.md` §2D, categorical rejection of `git-write` / `workflow-write` per §2E)
- An audit trail of every skill invocation

So we built our own minimal stdio MCP server.

---

## Install

From the repo root:

```bash
cd tools/forge-skills-mcp
uv sync
```

This populates `.venv/` inside the package (gitignored). Both agents launch the server by invoking `.venv/bin/python` **directly** — no `uv run` wrapper at MCP-spawn time, which means no `~/.cache/uv/` writes (a sandbox blocker on Codex; see _Codex sandbox constraint_ below).

Smoke test:

```bash
.venv/bin/python -m forge_skills_mcp --skills-root ../../.skills --verbose
# (Ctrl-C to exit — the server is waiting for stdio MCP traffic.)
```

---

## Register with both agents

Both agents must register the **direct `.venv/bin/python`** form. `uv run` was the original pattern but fails under Codex's sandboxed `codex exec` because uv writes to its global cache outside the workspace.

### Codex CLI

Append to `~/.codex/config.toml`:

```toml
[mcp_servers.forge-skills]
command = '/Users/<you>/git/repos/forge-works/tools/forge-skills-mcp/.venv/bin/python'
args = ['-m', 'forge_skills_mcp', '--skills-root', '/Users/<you>/git/repos/forge-works/.skills']
env = { PYTHONDONTWRITEBYTECODE = "1" }
```

`--skills-root` is passed explicitly because the spawned process inherits Codex's CWD (not this package's directory), so the default cwd-walker can't locate `.skills/`.

### Claude Code

```bash
claude mcp remove forge-skills 2>/dev/null
claude mcp add forge-skills -- /Users/<you>/git/repos/forge-works/tools/forge-skills-mcp/.venv/bin/python -m forge_skills_mcp --skills-root /Users/<you>/git/repos/forge-works/.skills
```

(The `--` separator is required so `claude mcp add` doesn't try to parse `-m` as its own flag.)

### Verify dual-agent visibility

From Claude Code, in a new session:

```text
Call mcp__forge-skills__loader_health.
```

Expected: a JSON payload with `version`, `skills_count`, `skills_root`, `last_scan_at`.

From Codex CLI (interactive TUI):

```text
Use the forge-skills MCP tool loader_health and print the version field.
```

When Codex prompts to approve the MCP call, choose **Allow** (or **Allow for this session**). Expected: `0.1.0`.

Both responses should report the same `skills_count` and the same `.skills/` root path.

---

## Codex sandbox constraint

> Documented 2026-05-16 after AB-022 fix work. Owner: adamatdevops.

**Codex CLI auto-cancels MCP tool calls in non-interactive sandboxed `codex exec` runs.** This is by Codex design: MCP tool calls are treated as consequential operations requiring interactive approval. Under `--sandbox read-only` or `--sandbox workspace-write` with `approval_policy = "never"` (i.e. `[profiles.review]`), the agent sees `error: "user cancelled MCP tool call"`. There is no public config key (`always_allow`, `auto_approve`, per-server allowlist) to override this in Codex 0.130.0.

| Mode                                                       | forge-skills available? |
| ---------------------------------------------------------- | ----------------------- |
| Claude Code (any session)                                  | ✅ Yes                  |
| Interactive `codex` TUI (any sandbox)                      | ✅ Yes (user approves)  |
| `codex exec --sandbox danger-full-access`                  | ✅ Yes                  |
| `codex exec --dangerously-bypass-approvals-and-sandbox`    | ✅ Yes                  |
| `codex exec --profile review` (sandbox=read-only, never)   | ❌ Auto-cancels         |
| `codex exec --sandbox workspace-write -c approval="never"` | ❌ Auto-cancels         |

**Implication for `[profiles.review]`:** the Claude→Codex code-review loop (`/codex-review`) reviews diffs — it does not load skills. Skill access from the review loop is not currently a workflow requirement. If a future review task needs a skill, the agent can shell-exec `.venv/bin/python -m forge_skills_mcp` directly (which Codex demonstrated as a working fallback during the AB-022 investigation), or the loop can switch to `--dangerously-bypass-approvals-and-sandbox` for that invocation only.

**Implication for dual-agent doctrine:** dual-agent skill delivery (`AGENTS.md` §4.4) holds for **development-time** sessions (interactive Claude + interactive Codex), which is the primary use case. It does not hold for Codex's non-interactive review profile, which is fine — skills are an authoring aid, not a review-time aid.

---

## Tools exposed

| Tool            | Signature                                    | Purpose                                                                                     |
| --------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `list_skills`   | `(tier_max: int \| None = None)`             | List summaries of all skills, optionally capped by Tier.                                    |
| `get_skill`     | `(slug: str)`                                | Return full SKILL.md content + frontmatter for a slug. Refuses on missing / rejected scope. |
| `find_skills`   | `(query: str, tier_max: int \| None = None)` | Substring match on name + body. No LLM ranking.                                             |
| `loader_health` | `()`                                         | Version, skills count, root path, last-scan timestamp. Smoke-test endpoint.                 |

### Refusal semantics

`get_skill` returns `{"error": "categorically-rejected", "reason": ...}` when a skill's `tool-scope` frontmatter is `git-write` or `workflow-write` (per `AGENT_SKILLS.md` §2E). `{"error": "not-found"}` when the slug doesn't exist.

---

## SKILL.md frontmatter schema

Every vendored `.skills/<vendor>/<slug>/SKILL.md` MUST have YAML frontmatter:

```yaml
---
name: <slug-name>
vendor: <vendor-org>
slug: <vendor>/<name>
source-url: https://...
source-canonical: https://github.com/<owner>/<repo>/tree/<sha>/<path>
source-sha: <40-char-hex>
audited: YYYY-MM-DD
goal: 1-5 # AGENT_SKILLS.md §1 goal number
tier: 1-3 # AGENT_SKILLS.md §4 tier
tool-scope: read-only | read-only+transform | shell-execute | repo-write | network | cross-agent | external-write
target-agents: [claude-code, codex]
context-cost-tokens: <int>
owner: <person>
---
<SKILL body markdown>
```

Skills missing required fields land in `loader_health()["skills_errors_count"]` rather than `list_skills`. Phase 2 will promote this to a hard refuse at server start.

---

## Run tests

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

---

## Phase scope

This is **Phase 1** of the strategic plan. Phase 1 is intentionally minimal — file-based stdio, no remote backend, no aggregator client. See `roadmap/ACTION_PLAN_SKILL_LOADERS.md` §2 for the full phased roadmap (Phase 2 = SHA enforcement + audit log; Phase 3 = aggregator client; Phase 4 = multi-loader composition).

Out of scope explicitly listed in §10 of the action plan. Don't add features in this directory without updating the plan first.

---

## Owner

`adamatdevops`. See `roadmap/AUTOMATIONS_BACKLOG.md` AB-022 for acceptance criteria.
