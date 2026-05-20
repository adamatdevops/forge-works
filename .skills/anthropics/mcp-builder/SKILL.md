---
name: mcp-builder
vendor: anthropics
slug: anthropics/mcp-builder
source-url: https://github.com/anthropics/skills/tree/main/skills/mcp-builder
source-canonical: https://github.com/anthropics/skills/tree/b9e19e6f44773509fbdd7001d77ff41a49a486c1/skills/mcp-builder
source-sha: b9e19e6f44773509fbdd7001d77ff41a49a486c1
audited: 2026-05-20
goal: 1
tier: 2
tool-scope: shell-execute+repo-write
target-agents: [claude-code, codex]
context-cost-tokens: 1847
owner: adamatdevops
---

<!-- Source: https://github.com/anthropics/skills/tree/b9e19e6f44773509fbdd7001d77ff41a49a486c1/skills/mcp-builder/SKILL.md · SHA: b9e19e6f44773509fbdd7001d77ff41a49a486c1 · Audited: 2026-05-20 · **19th vendored skill + 3rd Anthropic-first-party adoption (after §D skill-creator + §A doc-coauthoring) + EIGHTH Tier 1→2 correction at adoption review (corrected from eval-list's Tier 1 estimate per new §4.4.3 step 2 audit — N=11 Tier-staleness datapoints now: 8 corrections + 3 deferrals from 6 independent vendors) + FIRST framework adoption with a vendored Python script that DIRECTLY invokes the `anthropic` SDK (`messages.create` calls) — distinct from §D anthropics/skill-creator's `claude --print` CLI subprocess pattern.** **Tier-staleness audit (per new §4.4.3 step 2 checklist):** (i) **YES — file-write directives in SKILL.md Phase 2**: Phase 2.1 "Set Up Project Structure" + Phase 2.2 "Implement Core Infrastructure" + Phase 2.3 "Implement Tools" direct the agent to CREATE MCP server source files (Python: FastMCP-based modules + `__init__.py` + tool definitions; TypeScript: MCP SDK-based modules + tsconfig.json + tool definitions); Phase 2.1 includes `mkdir` + project-structure scaffolding per `reference/node_mcp_server.md` + `reference/python_mcp_server.md` workflow guides. **File CREATE → Tier 2 per §J R3-A-3.** (ii) NO `allowed-tools` frontmatter in upstream SKILL.md (Anthropic's MCP-building skill uses host agent's default tool grants; the host applies its standard Read/Edit/Write/Bash envelope) — same pattern as §AM `obra/systematic-debugging` (no upstream `allowed-tools` declaration); (iii) NO `commands/` directory; (iv) **Documentation-fetch network egress**: SKILL.md L43 + L203 instruct agent to `fetch specific pages with .md suffix` from `https://modelcontextprotocol.io` (specifically `/specification/draft.md` + `/sitemap.xml`) — this is read-only public-docs network access via the host's WebFetch tool, NOT skill-declared egress; agent uses host's WebFetch which is standard tooling (consistent with how §A uses host's Slack/Drive MCPs); (v) NO `Task` tool / cross-agent surface declared. **Final Tier 2 verdict for §AQ mcp-builder**: `shell-execute+repo-write` — file CREATE (MCP server source files) + Bash (build, test, `npm install` / `uv pip install`) is the primary deliverable. Matches §D anthropics/skill-creator's tool-scope. **Bundled-script same-model self-invocation clause analysis (per §4.4.3 step 1 R2-2 hardening + §AGENT_SKILLS.md §2E):** `scripts/evaluation.py` (12579 bytes / 2865t) imports `from anthropic import Anthropic` + calls `client.messages.create` with configurable model (default `claude-3-7-sonnet-20250219`) — **HAS model-client invocation tokens per R2-2**. However, **SKILL.md does NOT direct the agent to execute `evaluation.py`** (grep'd SKILL.md for "evaluation.py" / "scripts/" / "python scripts/" — ZERO matches; the only reference is Phase 4 "Create Evaluations" which directs the agent to AUTHOR a `<evaluation>` XML file per `reference/evaluation.md`, NOT to run the harness). Phase 4 output is an XML file the USER subsequently runs through `evaluation.py` (the harness invokes the MCP server being tested using its own Anthropic API client). **§2E "Bundled-script same-model self-invocation" clause is therefore NON-APPLICABLE at agent-run time** — the clause applies only when the agent EXECUTES the script; here the script is a USER UTILITY (analogous to §AM's `find-polluter.sh`, §AP's `merge_sarif.py`, §AN's `sarif_helpers.py`). **R2-2 audit documented for provenance:** `evaluation.py` runs as a SEPARATE Python subprocess with its own Anthropic API client + own ANTHROPIC_API_KEY usage; per the §2E cross-agent normative predicate (lines ~406-426 in AGENT_SKILLS.md), if the agent WERE to execute the script all 3 predicate conditions would fail (execution boundary external, child grants not provably subset, grant inheritance opaque) → would be cross-agent Tier 3 → would require intra-skill Tier-3 escalation gate (§D pattern). Currently NOT directed by SKILL.md → NO Tier-3 escalation required at adoption. **`scripts/connections.py` R2-2 audit:** ✅ NO `subprocess`/`os.system`/`os.exec`/`shell=True`/`claude`/`anthropic`/`messages.create`/SDK tokens — pure Python helper for MCP connection (stdio + HTTP transports); user-runnable library imported by `evaluation.py`. **Doctrinal observation (NEW framework pattern surfaced):** §AQ is the FIRST framework adoption where a vendored Python script directly imports the `anthropic` SDK (not subprocess'd via `claude --print`). The §D anthropics/skill-creator precedent used `claude --print` CLI patterns (subprocess wrapper); §AQ uses the direct SDK pattern. This SHARPENS the §2E clause: "Bundled-script same-model self-invocation" applies to BOTH (a) `claude --` subprocess invocations AND (b) direct `anthropic` SDK imports — both are model-client invocation surfaces. The clause's NON-APPLICABILITY in §AQ's case is because the AGENT doesn't execute the script (USER does), NOT because the script lacks model-client invocations. **Bundle:** SKILL.md 1847t body + 4 reference/*.md (4938 + 1593 + 6581 + 5524 = 18636t) + 4 scripts files (1051 + 2865 + 326 + 18 = 4260t) + LICENSE.txt byte-identical (Anthropic Apache 2.0 from anthropics/skills repo). **Worst-case archive 24,818 tokens** — SECOND-largest bundle in framework after §AO codeql's 27,298; 8 companion files load-on-demand per §3B (the 4 reference guides are referenced via explicit "Load [...]" directives at Phase 1.2-1.3 + Phase 4 — agent loads them WHEN entering the corresponding phase, not at SKILL.md ingest). **Cross-cluster Anthropic vendor (NOT a cluster):** §D + §A + §AQ all share vendor `anthropics` + repo `anthropics/skills` BUT pinned at 3 DIFFERENT SHAs (§D `f458cee31...` 2026-05-09 pre-restructure; §A `6a5bb069...` 2026-05-17 post-restructure; §AQ `b9e19e6f...` 2026-04-20 latest at-path for mcp-builder). Per §4.4.5 cluster-co-adoption note: "two or more adopted skills share canonical upstream repo + SHA" — requires SHARED SHA, not just shared repo. The 3 Anthropic skills are at 3 different SHAs → **NO Anthropic cluster** in the cluster-co-adoption-optimization sense; each skill has independent quarterly source-SHA review. **Sub-cluster within MCP authoring tooling:** §AQ is FIRST-PARTY authority on MCP server CREATION; pairs naturally with the forge-skills MCP loader in this project (`tools/forge-skills-mcp/`) which is itself a vendored MCP server we author. Direct meta-applicability: §AQ doctrine validates / improves the forge-skills-mcp loader's tool-design + evaluation harness. **Phase-A/Phase-B handling per §4.5.2 step 4 Tier 2:** §AQ is **overwhelmingly Phase B in practice** — Phase 2.1 starts with `mkdir` + project scaffold creation (Phase B operations). Phase A applies only if the user pre-supplies a fully-scaffolded MCP server project AND agent only needs to add a single tool (rare). Most invocations fire neutral 3-option confirmation prompt from step 1. **Sister-skill cross-references:** SKILL.md has ZERO direct cross-references to other adopted skills; the only adjacency is meta-applicability to forge-skills-mcp loader (this project's own MCP authoring). **Body sha256:** `6eaabfcf59c08178...`. -->


# MCP Server Development Guide

## Overview

Create MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. The quality of an MCP server is measured by how well it enables LLMs to accomplish real-world tasks.

---

# Process

## 🚀 High-Level Workflow

Creating a high-quality MCP server involves four main phases:

### Phase 1: Deep Research and Planning

#### 1.1 Understand Modern MCP Design

**API Coverage vs. Workflow Tools:**
Balance comprehensive API endpoint coverage with specialized workflow tools. Workflow tools can be more convenient for specific tasks, while comprehensive coverage gives agents flexibility to compose operations. Performance varies by client—some clients benefit from code execution that combines basic tools, while others work better with higher-level workflows. When uncertain, prioritize comprehensive API coverage.

**Tool Naming and Discoverability:**
Clear, descriptive tool names help agents find the right tools quickly. Use consistent prefixes (e.g., `github_create_issue`, `github_list_repos`) and action-oriented naming.

**Context Management:**
Agents benefit from concise tool descriptions and the ability to filter/paginate results. Design tools that return focused, relevant data. Some clients support code execution which can help agents filter and process data efficiently.

**Actionable Error Messages:**
Error messages should guide agents toward solutions with specific suggestions and next steps.

#### 1.2 Study MCP Protocol Documentation

**Navigate the MCP specification:**

Start with the sitemap to find relevant pages: `https://modelcontextprotocol.io/sitemap.xml`

Then fetch specific pages with `.md` suffix for markdown format (e.g., `https://modelcontextprotocol.io/specification/draft.md`).

Key pages to review:
- Specification overview and architecture
- Transport mechanisms (streamable HTTP, stdio)
- Tool, resource, and prompt definitions

#### 1.3 Study Framework Documentation

**Recommended stack:**
- **Language**: TypeScript (high-quality SDK support and good compatibility in many execution environments e.g. MCPB. Plus AI models are good at generating TypeScript code, benefiting from its broad usage, static typing and good linting tools)
- **Transport**: Streamable HTTP for remote servers, using stateless JSON (simpler to scale and maintain, as opposed to stateful sessions and streaming responses). stdio for local servers.

**Load framework documentation:**

- **MCP Best Practices**: [📋 View Best Practices](./reference/mcp_best_practices.md) - Core guidelines

**For TypeScript (recommended):**
- **TypeScript SDK**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- [⚡ TypeScript Guide](./reference/node_mcp_server.md) - TypeScript patterns and examples

**For Python:**
- **Python SDK**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
- [🐍 Python Guide](./reference/python_mcp_server.md) - Python patterns and examples

#### 1.4 Plan Your Implementation

**Understand the API:**
Review the service's API documentation to identify key endpoints, authentication requirements, and data models. Use web search and WebFetch as needed.

**Tool Selection:**
Prioritize comprehensive API coverage. List endpoints to implement, starting with the most common operations.

---

### Phase 2: Implementation

#### 2.1 Set Up Project Structure

See language-specific guides for project setup:
- [⚡ TypeScript Guide](./reference/node_mcp_server.md) - Project structure, package.json, tsconfig.json
- [🐍 Python Guide](./reference/python_mcp_server.md) - Module organization, dependencies

#### 2.2 Implement Core Infrastructure

Create shared utilities:
- API client with authentication
- Error handling helpers
- Response formatting (JSON/Markdown)
- Pagination support

#### 2.3 Implement Tools

For each tool:

**Input Schema:**
- Use Zod (TypeScript) or Pydantic (Python)
- Include constraints and clear descriptions
- Add examples in field descriptions

**Output Schema:**
- Define `outputSchema` where possible for structured data
- Use `structuredContent` in tool responses (TypeScript SDK feature)
- Helps clients understand and process tool outputs

**Tool Description:**
- Concise summary of functionality
- Parameter descriptions
- Return type schema

**Implementation:**
- Async/await for I/O operations
- Proper error handling with actionable messages
- Support pagination where applicable
- Return both text content and structured data when using modern SDKs

**Annotations:**
- `readOnlyHint`: true/false
- `destructiveHint`: true/false
- `idempotentHint`: true/false
- `openWorldHint`: true/false

---

### Phase 3: Review and Test

#### 3.1 Code Quality

Review for:
- No duplicated code (DRY principle)
- Consistent error handling
- Full type coverage
- Clear tool descriptions

#### 3.2 Build and Test

**TypeScript:**
- Run `npm run build` to verify compilation
- Test with MCP Inspector: `npx @modelcontextprotocol/inspector`

**Python:**
- Verify syntax: `python -m py_compile your_server.py`
- Test with MCP Inspector

See language-specific guides for detailed testing approaches and quality checklists.

---

### Phase 4: Create Evaluations

After implementing your MCP server, create comprehensive evaluations to test its effectiveness.

**Load [✅ Evaluation Guide](./reference/evaluation.md) for complete evaluation guidelines.**

#### 4.1 Understand Evaluation Purpose

Use evaluations to test whether LLMs can effectively use your MCP server to answer realistic, complex questions.

#### 4.2 Create 10 Evaluation Questions

To create effective evaluations, follow the process outlined in the evaluation guide:

1. **Tool Inspection**: List available tools and understand their capabilities
2. **Content Exploration**: Use READ-ONLY operations to explore available data
3. **Question Generation**: Create 10 complex, realistic questions
4. **Answer Verification**: Solve each question yourself to verify answers

#### 4.3 Evaluation Requirements

Ensure each question is:
- **Independent**: Not dependent on other questions
- **Read-only**: Only non-destructive operations required
- **Complex**: Requiring multiple tool calls and deep exploration
- **Realistic**: Based on real use cases humans would care about
- **Verifiable**: Single, clear answer that can be verified by string comparison
- **Stable**: Answer won't change over time

#### 4.4 Output Format

Create an XML file with this structure:

```xml
<evaluation>
  <qa_pair>
    <question>Find discussions about AI model launches with animal codenames. One model needed a specific safety designation that uses the format ASL-X. What number X was being determined for the model named after a spotted wild cat?</question>
    <answer>3</answer>
  </qa_pair>
<!-- More qa_pairs... -->
</evaluation>
```

---

# Reference Files

## 📚 Documentation Library

Load these resources as needed during development:

### Core MCP Documentation (Load First)
- **MCP Protocol**: Start with sitemap at `https://modelcontextprotocol.io/sitemap.xml`, then fetch specific pages with `.md` suffix
- [📋 MCP Best Practices](./reference/mcp_best_practices.md) - Universal MCP guidelines including:
  - Server and tool naming conventions
  - Response format guidelines (JSON vs Markdown)
  - Pagination best practices
  - Transport selection (streamable HTTP vs stdio)
  - Security and error handling standards

### SDK Documentation (Load During Phase 1/2)
- **Python SDK**: Fetch from `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
- **TypeScript SDK**: Fetch from `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`

### Language-Specific Implementation Guides (Load During Phase 2)
- [🐍 Python Implementation Guide](./reference/python_mcp_server.md) - Complete Python/FastMCP guide with:
  - Server initialization patterns
  - Pydantic model examples
  - Tool registration with `@mcp.tool`
  - Complete working examples
  - Quality checklist

- [⚡ TypeScript Implementation Guide](./reference/node_mcp_server.md) - Complete TypeScript guide with:
  - Project structure
  - Zod schema patterns
  - Tool registration with `server.registerTool`
  - Complete working examples
  - Quality checklist

### Evaluation Guide (Load During Phase 4)
- [✅ Evaluation Guide](./reference/evaluation.md) - Complete evaluation creation guide with:
  - Question creation guidelines
  - Answer verification strategies
  - XML format specifications
  - Example questions and answers
  - Running an evaluation with the provided scripts
