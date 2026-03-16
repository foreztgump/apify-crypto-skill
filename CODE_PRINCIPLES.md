# Code Principles

Single source of truth for code quality standards. Referenced by CLAUDE.md, CodeRabbit, OpenSpec, and implementation subagents.

## Hard Rules (violations must be fixed)

1. **Single Responsibility**: Every function and class does one thing. If the description needs "and", split it.
2. **No Magic Values**: All literals that aren't self-evident (0, 1, True, False, "") must be named constants. Apify endpoints, timeouts, default limits — all constants.
3. **Descriptive Names**: Names reveal intent using snake_case. No abbreviations, no generic names (data, info, item, temp, result) in scopes longer than 3 lines.
4. **Error Handling at Boundaries**: All httpx calls, Apify API interactions, and JSON parsing must handle errors explicitly. Use specific exception types.
5. **Max 40 Lines per Function**: If longer, decompose. Measured excluding blank lines and comments.
6. **Max 3 Parameters**: Functions with more than 3 parameters must use a Pydantic model or dataclass.
7. **Max 3 Nesting Levels**: Use early returns, guard clauses, or extraction to reduce nesting.
8. **No Duplication**: Extract shared behavior into functions. If you see >5 similar lines in multiple locations, refactor.
9. **Type Annotations**: All public functions must have full type annotations (parameters and return types).
10. **Arrange-Act-Assert Tests**: Each test covers one behavior. Test names describe expected behavior, not implementation.
11. **No Speculative Abstractions**: Only build what the current task requires. No "just in case" interfaces, factories, or registries.

## Soft Guidelines (prefer, but use judgment)

1. **KISS**: Pick the simplest solution that works. Three similar lines is better than a premature abstraction.
2. **Deep Modules**: Simple interface, complex implementation hidden behind it. The Apify client should hide all REST API details.
3. **Composition Over Inheritance**: Combine objects, don't extend class hierarchies.
4. **Comments Explain Why**: Code should be self-documenting for the "what". Comments explain non-obvious decisions.
5. **Law of Demeter**: Talk to direct collaborators only. No chaining through objects (e.g., `run.data.defaultDatasetId` is fine as a typed model access, but avoid raw dict chaining).
6. **Strategic Programming**: Invest a little extra time to produce clean, well-structured code rather than just making it work.
7. **Async by Default**: All I/O-bound functions should be async. Use `httpx.AsyncClient` throughout.
8. **Pydantic for External Data**: All data from Apify API responses should be validated through Pydantic models before use.
