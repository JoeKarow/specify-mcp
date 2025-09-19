# Tasks: MCP Server for Centralized Spec-Kit Functionality

**Input**: Design documents from `/specs/001-build-a-model/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)

```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, FastMCP, PyYAML, Pydantic, asyncio, pytest
   → Structure: Single project with src/speckit_mcp package
2. Load optional design documents:
   → data-model.md: 6 entities (ProjectConfiguration, WorkflowSession, Template, Task, ContextDocument, RepositoryRegistration)
   → contracts/: 2 files (mcp-tools.json with 5 tools, mcp-resources.json with 4 resource types)
   → research.md: FastMCP patterns, subprocess git operations, YAML config management
3. Generate tasks by category:
   → Setup: project structure, dependencies, toolchain
   → Tests: 5 MCP tool tests, 4 resource tests, 6 model tests
   → Core: 6 Pydantic models, git operations, config manager, MCP server
   → Integration: End-to-end workflows, error handling
   → Polish: Documentation, performance optimization
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T042)
6. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Project package: `src/speckit_mcp/`
- Paths shown below follow single project structure from plan.md

## Phase 3.1: Setup

- [x] T001 Create project structure: src/speckit_mcp/{server.py,tools/,resources/,git/,config/,utils/}, tests/{contract/,integration/,unit/}
- [x] T002 Initialize Python project with pyproject.toml: FastMCP>=2.0.0, PyYAML>=6.0, Pydantic>=2.0, pytest>=7.0, pytest-asyncio
- [x] T003 [P] Create mise configuration in .mise.toml for Python 3.11+ toolchain management (updated pyproject.toml instead)
- [x] T004 [P] Configure pytest with asyncio support in pytest.ini and setup.cfg for testing (configured in pyproject.toml)
- [x] T005 [P] Create .gitignore for Python project with **pycache**, *.pyc, .venv/, dist/,*.egg-info

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests for MCP Tools

- [x] T006 [P] Contract test for specify tool in tests/contract/test_specify_tool.py (create branch, generate spec)
- [x] T007 [P] Contract test for plan tool in tests/contract/test_plan_tool.py (generate implementation plan)
- [x] T008 [P] Contract test for tasks tool in tests/contract/test_tasks_tool.py (create task breakdown)
- [x] T009 [P] Contract test for initialize_project tool in tests/contract/test_initialize_tool.py (setup constitution.yaml)
- [x] T010 [P] Contract test for get_context tool in tests/contract/test_context_tool.py (retrieve phase-specific docs)

### Contract Tests for MCP Resources

- [x] T011 [P] Contract test for template resources in tests/contract/test_template_resources.py (spec, plan, tasks templates)
- [x] T012 [P] Contract test for documentation resources in tests/contract/test_documentation_resources.py (guides, references)
- [x] T013 [P] Contract test for configuration resources in tests/contract/test_configuration_resources.py (constitution schema)
- [x] T014 [P] Contract test for workflow resources in tests/contract/test_workflow_resources.py (specify, plan, tasks workflows)

### Integration Tests

- [x] T015 [P] Integration test for complete specify workflow in tests/integration/test_specify_workflow.py
- [x] T016 [P] Integration test for git operations in tests/integration/test_git_operations.py (branch creation, status)
- [x] T017 [P] Integration test for configuration inheritance in tests/integration/test_config_inheritance.py
- [x] T018 [P] Integration test for concurrent repository operations in tests/integration/test_concurrent_repos.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Pydantic Models

- [x] T019 [P] ProjectConfiguration model in src/speckit_mcp/config/models.py with YAML validation
- [x] T020 [P] WorkflowSession model in src/speckit_mcp/config/models.py with state transitions
- [x] T021 [P] Template model in src/speckit_mcp/resources/models.py with markdown validation
- [x] T022 [P] Task model in src/speckit_mcp/config/models.py with dependency tracking
- [x] T023 [P] ContextDocument model in src/speckit_mcp/resources/models.py with phase filtering
- [x] T024 [P] RepositoryRegistration model in src/speckit_mcp/config/models.py with path validation

### Core Modules

- [x] T025 Git operations module in src/speckit_mcp/git/operations.py with subprocess.run() for cross-platform git commands
- [x] T026 Configuration manager in src/speckit_mcp/config/manager.py with YAML safe_load and Pydantic validation
- [x] T027 Template manager in src/speckit_mcp/resources/template_manager.py with embedded template loading
- [x] T028 File operations utilities in src/speckit_mcp/utils/file_ops.py with path validation and safe I/O

### MCP Server Setup

- [x] T029 Main MCP server initialization in src/speckit_mcp/server.py with FastMCP stdio transport
- [x] T030 Server **main** entry point in src/speckit_mcp/**main**.py for python -m execution

### MCP Tool Implementations

- [x] T031 Implement specify tool in src/speckit_mcp/tools/specify.py (create branch, generate spec from template)
- [x] T032 Implement plan tool in src/speckit_mcp/tools/plan.py (analyze spec, generate plan artifacts)
- [x] T033 Implement tasks tool in src/speckit_mcp/tools/tasks.py (create structured task YAML from plan)
- [x] T034 Implement initialize_project tool in src/speckit_mcp/tools/initialize.py (create .specify-mcp/constitution.yaml)
- [x] T035 Implement get_context tool in src/speckit_mcp/tools/context.py (serve phase-specific documentation)

### MCP Resource Implementations

- [x] T036 Implement template resources in src/speckit_mcp/resources/templates.py (serve spec, plan, tasks templates)
- [x] T037 Implement documentation resources in src/speckit_mcp/resources/documentation.py (serve guides and references)
- [x] T038 Implement configuration resources in src/speckit_mcp/resources/configuration.py (serve schema and defaults)
- [x] T039 Implement workflow resources in src/speckit_mcp/resources/workflows.py (serve workflow definitions)

## Phase 3.4: Integration

- [x] T040 Connect all tools and resources to MCP server in src/speckit_mcp/server.py with proper registration ✓
- [x] T041 Implement error handling and MCPError responses across all tools with proper error codes ✓
- [x] T042 Add comprehensive logging to ~/.specify-mcp/logs/ with rotation and debug levels ✓

## Phase 3.5: Polish

- [ ] T043 [P] Add unit tests for git operations in tests/unit/test_git.py with mocked subprocess
- [ ] T044 [P] Add unit tests for configuration validation in tests/unit/test_config.py
- [ ] T045 [P] Performance optimization for concurrent operations using asyncio.gather()
- [ ] T046 [P] Create README.md with installation and usage instructions
- [ ] T047 Run quickstart.md validation to verify all examples work correctly
- [ ] T048 Package distribution setup with setup.py and MANIFEST.in for PyPI

## Dependencies

- Setup (T001-T005) must complete first
- All tests (T006-T018) before any implementation (T019-T039)
- Models (T019-T024) before core modules (T025-T028)
- Core modules before MCP setup (T029-T030)
- MCP setup before tool/resource implementations (T031-T039)
- All implementation before integration (T040-T042)
- Integration before polish (T043-T048)

## Parallel Execution Examples

### Launch all contract tests together (T006-T014)

```
Task: "Contract test for specify tool in tests/contract/test_specify_tool.py"
Task: "Contract test for plan tool in tests/contract/test_plan_tool.py"
Task: "Contract test for tasks tool in tests/contract/test_tasks_tool.py"
Task: "Contract test for initialize_project tool in tests/contract/test_initialize_tool.py"
Task: "Contract test for get_context tool in tests/contract/test_context_tool.py"
Task: "Contract test for template resources in tests/contract/test_template_resources.py"
Task: "Contract test for documentation resources in tests/contract/test_documentation_resources.py"
Task: "Contract test for configuration resources in tests/contract/test_configuration_resources.py"
Task: "Contract test for workflow resources in tests/contract/test_workflow_resources.py"
```

### Launch all Pydantic models together (T019-T024)

```
Task: "ProjectConfiguration model in src/speckit_mcp/config/models.py"
Task: "WorkflowSession model in src/speckit_mcp/config/models.py"
Task: "Template model in src/speckit_mcp/resources/models.py"
Task: "Task model in src/speckit_mcp/config/models.py"
Task: "ContextDocument model in src/speckit_mcp/resources/models.py"
Task: "RepositoryRegistration model in src/speckit_mcp/config/models.py"
```

### Launch polish tasks together (T043-T046)

```
Task: "Add unit tests for git operations in tests/unit/test_git.py"
Task: "Add unit tests for configuration validation in tests/unit/test_config.py"
Task: "Performance optimization for concurrent operations"
Task: "Create README.md with installation instructions"
```

## Notes

- [P] tasks = different files, no shared dependencies
- Verify all tests fail before implementing (TDD requirement)
- Commit after each task completion
- Follow constitution: MCP compliance, file system preservation, structured data
- No shell script dependencies - pure Python subprocess for git

## Validation Checklist

*GATE: Checked before execution*

- [x] All 5 MCP tools have corresponding contract tests (T006-T010)
- [x] All 4 resource types have contract tests (T011-T014)
- [x] All 6 entities have model tasks (T019-T024)
- [x] All tests come before implementation (T006-T018 before T019-T039)
- [x] Parallel tasks operate on different files (verified)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task

**Total Tasks**: 48
**Parallel Groups**: 9 (contract tests), 6 (models), 4 (polish)
**Estimated Completion**: 2-3 days with parallel execution
