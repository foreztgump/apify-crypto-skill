# Project Guidelines

## Code Quality
Mandatory: SRP, no magic values, descriptive names, error handling on boundaries,
max 40 lines / 3 params / 3 nesting, no duplication, YAGNI, Law of Demeter, AAA tests.
Prefer: KISS (simplest solution wins), deep modules, composition over inheritance,
strategic programming. See CODE_PRINCIPLES.md for full details.

## Behavioral Rules
- Never guess versions, APIs, or config syntax from training knowledge — always research first (see Tool Workflow below).
- Apify REST API base URL is `https://api.apify.com/v2` — do NOT hardcode full URLs in skill modules, use the client abstraction.
- Actor IDs: `moving_beacon-owner1/my-actor-14` (KuCoin), `benthepythondev/crypto-intelligence` (CoinGecko) — these are URL-encoded as `moving_beacon-owner1~my-actor-14` in API paths.
- Apify sync run endpoint has a 300-second timeout — for long-running actor calls, use async run + polling instead.
- All monetary/price values from actors are floats — do NOT convert to integers.
- OHLCV timestamps from KuCoin are Unix milliseconds — convert to seconds when exposing to consumers.
- `APIFY_API_TOKEN` must come from environment variable — never accept tokens as function parameters or hardcode them.
- When stuck or confused for more than 2 attempts at the same problem, say so explicitly.
- Always request local code review (`superpowers:code-reviewer`) before committing.

## Tool Workflow
- **Research**: Context7 (`resolve-library-id` -> `query-docs`) -> Tavily (`tavily_search`, `tavily_extract`, `tavily_research`) -> OpenMemory (`openmemory query`). Never use built-in WebSearch or WebFetch.
- **Spec**: `/opsx:new` -> `/opsx:ff` -> review -> implement -> `/opsx:verify` -> `/opsx:archive`
- **Plan & Execute**: `/superpowers:brainstorm` -> `/superpowers:write-plan` -> `/superpowers:execute-plan`
- **Review**: `superpowers:code-reviewer` before every commit. `coderabbit:code-review` for PR-level review.
- **Navigate**: LSP (`goToDefinition`, `findReferences`, `documentSymbol`, `workspaceSymbol`) — prefer over grep. Requires `ENABLE_LSP_TOOL=1`.
- **Test**: `pytest` for unit/integration tests.

## OpenMemory Checkpoints
| When | Action |
|------|--------|
| Before `/opsx:new`, `/opsx:ff`, `/fix` | `openmemory query "<topic> patterns" --limit 5` |
| After `/opsx:ff`, `/opsx:continue` | Store design summary and key decisions |
| During `/opsx:apply` (every 3-4 tasks) | Store progress, surprises, deviations |
| After `/opsx:verify` | Store findings (pass/fail, issues, fixes) |
| After `/opsx:archive` | Store completion record, patterns learned |
| After code review | Store non-obvious issues that apply beyond current PR |
| After `/fix` confirmed | Store error pattern, root cause, resolution |
| On `/resume` or session start | `openmemory query "recent context apify-crypto-skill" --limit 5` |

## Workflows
- `/work-local "<description>"` — full pipeline from spec to PR
- `/resume` — pick up where you left off
- `/fix "<bug>"` — debug and fix workflow

## Documentation Updates
After every implementation, check and update: README.md, CHANGELOG.md, CLAUDE.md.

## Git
Branch: `feature/short-desc` | Commit: `type(scope): desc` | PR against `main`
