"""
MCP tool for retrieving phase-specific documentation.

This module implements the get_context tool that filters and retrieves
relevant documentation based on development phase and workflow.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastmcp.exceptions import McpError

from speckit_mcp.config.manager import ConfigurationManager
from speckit_mcp.resources.models import (
    ContextDocument,
    DevelopmentPhase,
    DocumentType,
    DocumentVisibility
)
from speckit_mcp.utils.file_ops import safe_read, list_files


def _get_embedded_documents() -> List[ContextDocument]:
    """
    Get embedded documentation resources.

    Returns:
        List of embedded ContextDocument objects
    """
    documents = []

    # Constitution document - always visible
    documents.append(ContextDocument(
        document_id="constitution-guide",
        document_type=DocumentType.CONSTITUTION,
        title="Project Constitution Guide",
        phase=DevelopmentPhase.DESIGN,
        workflow="all",
        content="""# Project Constitution Guide

The constitution.yaml file defines the core principles and configuration for your project.

## Key Sections

### Project Information
- **name**: Your project's display name
- **description**: Brief project description
- **version**: Semantic version number

### Principles
Constitutional principles guide all development decisions:
1. **MCP Protocol Compliance**: All features through MCP tools
2. **File System Preservation**: Git-integrated workflow
3. **Test-First Development**: TDD methodology
4. **Structured Data**: YAML for machine parsing
5. **Simplicity**: YAGNI principle
6. **Cross-Platform**: Pure Python implementation

### Workflows
Configure specify, plan, and tasks workflows with custom steps and settings.

### Settings
- **auto_commit**: Automatically commit generated files
- **verbose_logging**: Enable detailed logging
- **max_parallel_tasks**: Maximum concurrent task execution
""",
        visibility=DocumentVisibility.ALWAYS,
        priority=1,
        tags=["configuration", "setup", "principles"]
    ))

    # Quickstart guide - research phase
    documents.append(ContextDocument(
        document_id="quickstart",
        document_type=DocumentType.QUICKSTART,
        title="SpecKit MCP Quickstart",
        phase=DevelopmentPhase.RESEARCH,
        workflow="all",
        content="""# SpecKit MCP Quickstart

## Getting Started

1. **Initialize your project**:
   ```
   initialize_project(repository_path, project_name)
   ```

2. **Create a feature specification**:
   ```
   specify(description, repository_path)
   ```

3. **Generate an implementation plan**:
   ```
   plan(spec_path, repository_path)
   ```

4. **Create task breakdown**:
   ```
   tasks(plan_path, repository_path)
   ```

## Workflow Overview

1. **Research Phase**: Understand requirements
2. **Design Phase**: Create specifications
3. **Implement Phase**: Build features with TDD
4. **Validate Phase**: Test and verify

## Best Practices

- Write clear feature descriptions
- Follow TDD methodology
- Keep specifications updated
- Use parallel task execution
- Commit changes regularly
""",
        visibility=DocumentVisibility.PHASE_SPECIFIC,
        priority=1,
        tags=["quickstart", "workflow", "guide"]
    ))

    # API reference - implement phase
    documents.append(ContextDocument(
        document_id="api-reference",
        document_type=DocumentType.API,
        title="MCP Tools API Reference",
        phase=DevelopmentPhase.IMPLEMENT,
        workflow="all",
        content="""# MCP Tools API Reference

## Available Tools

### specify(description: str, repository_path: str)
Create feature specification and branch.

**Returns**:
- branch_name: Created feature branch
- spec_path: Path to specification file
- feature_id: Unique feature identifier

### plan(spec_path: str, repository_path: str)
Generate implementation plan from specification.

**Returns**:
- plan_path: Path to plan file
- phases: Implementation phases
- estimated_complexity: Complexity estimate

### tasks(plan_path: str, repository_path: str)
Create task breakdown from plan.

**Returns**:
- tasks_path: Path to tasks file
- task_count: Number of tasks
- parallel_groups: Parallel execution groups

### initialize_project(repository_path: str, project_name: str?)
Initialize project configuration.

**Returns**:
- constitution_path: Configuration file path
- project_id: Unique project identifier

### get_context(phase: str, workflow: str?)
Retrieve phase-specific documentation.

**Returns**:
- documents: List of relevant documents
- total_count: Total documents found
""",
        visibility=DocumentVisibility.PHASE_SPECIFIC,
        priority=2,
        tags=["api", "reference", "tools"]
    ))

    # TDD guide - validate phase
    documents.append(ContextDocument(
        document_id="tdd-guide",
        document_type=DocumentType.GUIDE,
        title="Test-Driven Development Guide",
        phase=DevelopmentPhase.VALIDATE,
        workflow="all",
        content="""# Test-Driven Development Guide

## TDD Cycle

1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code quality

## Testing Strategy

### Unit Tests
- Test individual components
- Mock external dependencies
- Cover edge cases

### Integration Tests
- Test component interactions
- Verify workflows
- Test error handling

### Contract Tests
- Validate MCP tool interfaces
- Test JSON-RPC compliance
- Verify response schemas

## Best Practices

- Write tests first
- One assertion per test
- Use descriptive test names
- Keep tests independent
- Mock external services
- Test error conditions

## Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical paths
- All MCP tools fully tested
""",
        visibility=DocumentVisibility.PHASE_SPECIFIC,
        priority=1,
        tags=["testing", "tdd", "validation"]
    ))

    # Design patterns - design phase
    documents.append(ContextDocument(
        document_id="design-patterns",
        document_type=DocumentType.GUIDE,
        title="Design Patterns and Architecture",
        phase=DevelopmentPhase.DESIGN,
        workflow="all",
        content="""# Design Patterns and Architecture

## Architectural Principles

### Separation of Concerns
- MCP tools handle user interaction
- Core modules handle business logic
- Utils provide cross-cutting concerns

### Dependency Injection
- Use configuration managers
- Inject dependencies via constructors
- Avoid global state

### Error Handling
- Use McpError for tool failures
- Provide meaningful error messages
- Include error codes and data

## Common Patterns

### Factory Pattern
- Template creation
- Configuration loading
- Task generation

### Strategy Pattern
- Workflow execution
- Phase-specific behavior
- Template selection

### Repository Pattern
- Git operations abstraction
- File operations wrapper
- Configuration management

## Code Organization

```
src/speckit_mcp/
├── tools/       # MCP tool implementations
├── core/        # Business logic
├── config/      # Configuration management
├── resources/   # Templates and documents
└── utils/       # Shared utilities
```
""",
        visibility=DocumentVisibility.PHASE_SPECIFIC,
        priority=2,
        tags=["design", "architecture", "patterns"]
    ))

    return documents


def _load_project_documents(repository_path: str) -> List[ContextDocument]:
    """
    Load project-specific documentation from .specify-mcp/docs.

    Args:
        repository_path: Path to repository

    Returns:
        List of ContextDocument objects from project
    """
    documents = []
    docs_dir = Path(repository_path) / '.specify-mcp' / 'docs'

    if not docs_dir.exists():
        return documents

    # Find markdown files in docs directory
    try:
        doc_files = list_files(docs_dir, pattern="*.md")

        for doc_file in doc_files:
            # Read document content
            content = safe_read(doc_file)

            # Extract metadata from filename or content
            filename = doc_file.stem
            title = filename.replace('-', ' ').replace('_', ' ').title()

            # Try to determine phase from content or filename
            phase = DevelopmentPhase.DESIGN  # Default
            if 'research' in filename.lower():
                phase = DevelopmentPhase.RESEARCH
            elif 'implement' in filename.lower():
                phase = DevelopmentPhase.IMPLEMENT
            elif 'test' in filename.lower() or 'validate' in filename.lower():
                phase = DevelopmentPhase.VALIDATE

            # Create document object
            doc = ContextDocument(
                document_id=f"project-{filename}",
                document_type=DocumentType.GUIDE,
                title=title,
                phase=phase,
                workflow="all",
                content=content,
                visibility=DocumentVisibility.ALWAYS,
                priority=5,  # Lower priority than embedded
                tags=["project", "custom"]
            )

            documents.append(doc)

    except Exception as e:
        # Log warning but don't fail
        print(f"Warning: Could not load project documents: {e}")

    return documents


def _filter_documents_by_phase(
    documents: List[ContextDocument],
    phase: DevelopmentPhase
) -> List[ContextDocument]:
    """
    Filter documents by development phase.

    Args:
        documents: List of all documents
        phase: Current development phase

    Returns:
        Filtered list of documents
    """
    filtered = []

    for doc in documents:
        if doc.is_visible_for_phase(phase):
            filtered.append(doc)

    # Sort by priority (lower number = higher priority)
    filtered.sort(key=lambda d: d.priority)

    return filtered


def _filter_documents_by_workflow(
    documents: List[ContextDocument],
    workflow: str
) -> List[ContextDocument]:
    """
    Filter documents by workflow type.

    Args:
        documents: List of documents
        workflow: Workflow type to filter by

    Returns:
        Filtered list of documents
    """
    return [doc for doc in documents if doc.matches_workflow(workflow)]


async def get_context(
    phase: str,
    workflow: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve phase-specific documentation.

    This MCP tool filters and retrieves relevant documentation based on
    the current development phase and optionally the workflow type.

    Args:
        phase: Development phase (research/design/implement/validate)
        workflow: Optional workflow type (specify/plan/tasks) to filter by

    Returns:
        Dictionary containing:
            - success: Whether the operation succeeded
            - documents: List of document objects with title, content, and metadata
            - total_count: Total number of documents found
            - phase: The requested phase
            - message: Status message

    Raises:
        McpError: If invalid phase specified or retrieval fails
    """
    try:
        # Validate phase
        valid_phases = ['research', 'design', 'implement', 'validate']
        if phase.lower() not in valid_phases:
            raise McpError(
                code=-32602,  # Invalid params
                message=f"Invalid phase: {phase}. Must be one of: {', '.join(valid_phases)}"
            )

        # Convert phase string to enum
        phase_map = {
            'research': DevelopmentPhase.RESEARCH,
            'design': DevelopmentPhase.DESIGN,
            'implement': DevelopmentPhase.IMPLEMENT,
            'validate': DevelopmentPhase.VALIDATE
        }
        phase_enum = phase_map[phase.lower()]

        # Validate workflow if provided
        if workflow:
            valid_workflows = ['specify', 'plan', 'tasks', 'all']
            if workflow.lower() not in valid_workflows:
                raise McpError(
                    code=-32602,
                    message=f"Invalid workflow: {workflow}. Must be one of: {', '.join(valid_workflows)}"
                )

        # Get all available documents
        all_documents = _get_embedded_documents()

        # Try to load project-specific documents if we have a repository context
        # (In a real implementation, we might get this from server state)
        # For now, we'll just use embedded documents

        # Filter by phase
        phase_documents = _filter_documents_by_phase(all_documents, phase_enum)

        # Filter by workflow if specified
        if workflow:
            phase_documents = _filter_documents_by_workflow(
                phase_documents,
                workflow.lower()
            )

        # Convert documents to response format
        document_list = []
        for doc in phase_documents:
            document_list.append({
                'id': doc.document_id,
                'title': doc.title,
                'type': doc.document_type.value,
                'content': doc.content,
                'summary': doc.summary,
                'tags': doc.tags,
                'priority': doc.priority,
                'visibility': doc.visibility.value
            })

        return {
            'success': True,
            'documents': document_list,
            'total_count': len(document_list),
            'phase': phase,
            'workflow': workflow or 'all',
            'message': f"Retrieved {len(document_list)} documents for {phase} phase"
        }

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        # Wrap other exceptions in McpError
        raise McpError(
            code=-32603,  # Internal error
            message=f"Context retrieval failed: {str(e)}",
            data={"error_type": type(e).__name__}
        )