
# Implementation Plan: MCP Server for Centralized Spec-Kit Functionality

**Branch**: `001-build-a-model` | **Date**: 2025-09-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-build-a-model/spec.md`

## Execution Flow (/plan command scope)

```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:

- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Build a Model Context Protocol (MCP) server that eliminates manual spec-kit installation across repositories while maintaining git-integrated workflows. Implement using Python 3.11+ with FastMCP framework for stdio protocol, structured YAML for configuration and task tracking, embedded templates served via MCP resources, and subprocess calls for git operations.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastMCP (MCP protocol), PyYAML (config parsing), Pydantic (data validation), asyncio (concurrency)
**Storage**: File system only - `.specify-mcp/` directory for configs, structured YAML files for tasks
**Testing**: pytest with asyncio support for integration tests
**Target Platform**: Cross-platform (Windows, macOS, Linux) - stdio MCP server
**Project Type**: single - Python package with embedded resources
**Performance Goals**: Handle concurrent workflow executions across multiple repositories
**Constraints**: No external databases, no shell script dependencies, coexist with existing spec-kit installations
**Scale/Scope**: Support unlimited repositories with single-tenant operation per MCP server instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **MCP Protocol Compliance**: All functionality exposed through MCP tools/resources, stdio protocol with JSON-RPC 2.0 ✓
- [x] **File System Preservation**: Maintains git-integrated workflow, generates files in specs/[branch]/ structure ✓
- [x] **Test-First Development**: TDD mandatory with integration tests for MCP tools and file generation ✓
- [x] **Structured Data Over Markdown**: Uses structured YAML for tasks and config instead of markdown parsing ✓
- [x] **Simplicity and YAGNI**: Single-tenant MVP without premature team features ✓
- [x] **Cross-Platform Compatibility**: Python subprocess for git ops, no shell dependencies ✓

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each MCP tool contract → contract test task [P]
- Each entity → Pydantic model creation task [P]
- Each MCP resource → resource implementation task [P]
- Integration tests for complete workflows
- Implementation tasks to make tests pass

**Task Categories**:

1. **Setup Tasks** (1-5):
   - Project structure creation
   - Dependencies setup (pyproject.toml, mise.toml)
   - Configuration scaffolding

2. **Contract Test Tasks** (6-15) [P]:
   - Test for each MCP tool (specify, plan, tasks, initialize, context)
   - Test for each MCP resource (templates, documentation, configuration)
   - All tests must fail initially (TDD)

3. **Model Implementation Tasks** (16-20) [P]:
   - ProjectConfiguration Pydantic model
   - WorkflowSession model
   - Template model
   - Task model
   - ContextDocument model

4. **Core Implementation Tasks** (21-30):
   - Git operations module
   - Configuration manager
   - MCP server setup
   - Tool implementations (ordered by dependency)
   - Resource implementations

5. **Integration Tasks** (31-35):
   - End-to-end workflow tests
   - Cross-repository operations
   - Error handling verification

**Ordering Strategy**:

- TDD order: Tests before implementation
- Dependency order: Models → Git operations → Config → Tools → Resources
- Mark [P] for parallel execution (independent files)
- Group related tasks for context switching efficiency

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.yaml (structured format)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
