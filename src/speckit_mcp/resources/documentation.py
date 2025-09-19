"""
MCP resource implementation for serving documentation.

This module provides MCP resources for serving guides, references, and examples
with phase-specific filtering and metadata support.
"""

from typing import Dict, Any, Optional, List
from fastmcp.resources import Resource
from fastmcp.exceptions import McpError

from speckit_mcp.resources.models import (
    ContextDocument,
    DocumentType,
    DevelopmentPhase,
    DocumentVisibility
)


class DocumentationResources:
    """
    Manages MCP resources for documentation.

    Provides access to embedded documentation via MCP resource URIs,
    supporting categorization and phase-specific filtering.
    """

    def __init__(self):
        """Initialize documentation resources."""
        self.documents = self._load_embedded_documentation()

    def _load_embedded_documentation(self) -> Dict[str, ContextDocument]:
        """
        Load embedded documentation content.

        Returns:
            Dictionary mapping document IDs to ContextDocument instances
        """
        documents = {}

        # Constitution document
        documents['constitution'] = ContextDocument(
            document_id='constitution',
            document_type=DocumentType.CONSTITUTION,
            title='SpecKit Constitution',
            phase=DevelopmentPhase.DESIGN,
            workflow='all',
            content=self._get_constitution_content(),
            summary='Core principles and guidelines for the SpecKit system',
            visibility=DocumentVisibility.ALWAYS,
            priority=1,
            tags=['constitution', 'principles', 'guidelines']
        )

        # Quickstart guide
        documents['quickstart'] = ContextDocument(
            document_id='quickstart',
            document_type=DocumentType.QUICKSTART,
            title='SpecKit Quick Start Guide',
            phase=DevelopmentPhase.RESEARCH,
            workflow='all',
            content=self._get_quickstart_content(),
            summary='Get started with SpecKit in minutes',
            visibility=DocumentVisibility.ALWAYS,
            priority=1,
            tags=['quickstart', 'tutorial', 'getting-started']
        )

        # API reference
        documents['api-reference'] = ContextDocument(
            document_id='api-reference',
            document_type=DocumentType.API,
            title='SpecKit API Reference',
            phase=DevelopmentPhase.IMPLEMENT,
            workflow='all',
            content=self._get_api_reference_content(),
            summary='Complete API reference for SpecKit MCP tools',
            visibility=DocumentVisibility.PHASE_SPECIFIC,
            priority=2,
            tags=['api', 'reference', 'tools']
        )

        # Workflow guides
        documents['specify-guide'] = ContextDocument(
            document_id='specify-guide',
            document_type=DocumentType.GUIDE,
            title='Specification Workflow Guide',
            phase=DevelopmentPhase.RESEARCH,
            workflow='specify',
            content=self._get_specify_guide_content(),
            summary='How to create effective feature specifications',
            visibility=DocumentVisibility.PHASE_SPECIFIC,
            priority=2,
            tags=['guide', 'specify', 'workflow']
        )

        documents['plan-guide'] = ContextDocument(
            document_id='plan-guide',
            document_type=DocumentType.GUIDE,
            title='Planning Workflow Guide',
            phase=DevelopmentPhase.DESIGN,
            workflow='plan',
            content=self._get_plan_guide_content(),
            summary='How to generate implementation plans from specifications',
            visibility=DocumentVisibility.PHASE_SPECIFIC,
            priority=2,
            tags=['guide', 'plan', 'workflow']
        )

        documents['tasks-guide'] = ContextDocument(
            document_id='tasks-guide',
            document_type=DocumentType.GUIDE,
            title='Task Breakdown Guide',
            phase=DevelopmentPhase.IMPLEMENT,
            workflow='tasks',
            content=self._get_tasks_guide_content(),
            summary='How to create and manage task breakdowns',
            visibility=DocumentVisibility.PHASE_SPECIFIC,
            priority=2,
            tags=['guide', 'tasks', 'workflow']
        )

        return documents

    def _get_constitution_content(self) -> str:
        """Get constitution document content."""
        return """# SpecKit Constitution

## Core Principles

### 1. MCP Protocol Compliance
All functionality must be exposed through MCP tools and resources. Direct file system access
should be minimized and encapsulated within the MCP server.

### 2. File System Preservation
Maintain git-integrated workflow without requiring external state management. All artifacts
should be stored as files within the repository.

### 3. Test-First Development
Embrace Test-Driven Development (TDD) by writing failing tests before implementation. This
ensures robust, well-tested code and clear requirements.

### 4. Structured Data
Use YAML for configuration and machine-parsable data instead of unstructured markdown. This
enables better tooling and automation.

### 5. Simplicity (YAGNI)
Build the Minimum Viable Product (MVP) first. Avoid premature optimization and feature creep.
Add complexity only when proven necessary.

### 6. Cross-Platform Support
Ensure pure Python implementation without shell script dependencies. This maximizes portability
and reduces system requirements.

## Development Guidelines

### Git Integration
- Every feature starts with a branch
- Specifications are committed to the repository
- Plans and tasks are tracked in files
- Use conventional commit messages

### Testing Strategy
- Write contract tests for MCP protocol compliance
- Write integration tests for workflows
- Write unit tests for business logic
- Maintain minimum 80% code coverage

### Documentation Standards
- Document all MCP tools with clear descriptions
- Include examples in documentation
- Keep README files up to date
- Use docstrings for all public functions

## Workflow Rules

### Feature Development
1. Create specification using `specify` tool
2. Generate plan using `plan` tool
3. Break down into tasks using `tasks` tool
4. Implement following TDD principles
5. Validate with tests

### Code Review
- All code must pass tests
- Follow Python PEP 8 style guide
- Ensure proper error handling
- Document complex logic

### Release Process
- Semantic versioning (SemVer)
- Changelog maintenance
- Tagged releases
- Documentation updates"""

    def _get_quickstart_content(self) -> str:
        """Get quickstart guide content."""
        return """# SpecKit Quick Start Guide

## Installation

```bash
# Install using pip
pip install speckit-mcp

# Or install from source
git clone https://github.com/yourusername/speckit-mcp
cd speckit-mcp
pip install -e .
```

## Basic Usage

### Initialize a Project

```python
# Using the MCP client
await client.call_tool('initialize_project', {
    'repository_path': '/path/to/repo',
    'project_name': 'My Project'
})
```

### Create a Specification

```python
# Create a feature specification
result = await client.call_tool('specify', {
    'description': 'Add user authentication feature',
    'repository_path': '/path/to/repo'
})
```

### Generate a Plan

```python
# Generate implementation plan from spec
result = await client.call_tool('plan', {
    'spec_path': 'specs/001-user-auth.md',
    'repository_path': '/path/to/repo'
})
```

### Create Task Breakdown

```python
# Generate tasks from plan
result = await client.call_tool('tasks', {
    'plan_path': 'plans/001-user-auth-plan.md',
    'repository_path': '/path/to/repo'
})
```

## MCP Client Setup

### With Claude Desktop

Add to your Claude configuration:

```json
{
  "mcpServers": {
    "speckit": {
      "command": "python",
      "args": ["-m", "speckit_mcp.server"],
      "env": {}
    }
  }
}
```

### With Python Client

```python
from mcp import Client
import asyncio

async def main():
    async with Client("stdio://python -m speckit_mcp.server") as client:
        # Use tools
        await client.call_tool('specify', {...})

asyncio.run(main())
```

## Next Steps

1. Read the [Constitution](mcp://speckit/docs/references/constitution) for principles
2. Review workflow guides for detailed instructions
3. Check API reference for all available tools
4. Explore example projects"""

    def _get_api_reference_content(self) -> str:
        """Get API reference content."""
        return """# SpecKit API Reference

## MCP Tools

### specify
Create feature specification from description.

**Parameters:**
- `description` (str): Feature description
- `repository_path` (str): Path to git repository

**Returns:**
- `success` (bool): Operation success status
- `feature_id` (str): Generated feature ID
- `branch_name` (str): Created git branch
- `spec_path` (str): Path to specification file

### plan
Generate implementation plan from specification.

**Parameters:**
- `spec_path` (str): Path to specification file
- `repository_path` (str): Path to git repository
- `tech_stack` (list[str], optional): Technology stack

**Returns:**
- `success` (bool): Operation success status
- `plan_path` (str): Path to plan file
- `phases` (list): Implementation phases

### tasks
Create task breakdown from plan.

**Parameters:**
- `plan_path` (str): Path to plan file
- `repository_path` (str): Path to git repository
- `parallel_groups` (int, optional): Number of parallel groups

**Returns:**
- `success` (bool): Operation success status
- `tasks_path` (str): Path to tasks file
- `task_count` (int): Total number of tasks
- `groups` (list): Task groups

### initialize_project
Initialize a new SpecKit project.

**Parameters:**
- `repository_path` (str): Path to git repository
- `project_name` (str): Project name
- `description` (str, optional): Project description

**Returns:**
- `success` (bool): Operation success status
- `config_path` (str): Path to constitution file

### get_context
Get phase-specific documentation.

**Parameters:**
- `phase` (str): Development phase
- `workflow` (str, optional): Workflow type

**Returns:**
- `documents` (list): Relevant documentation

## MCP Resources

### Templates
- `mcp://speckit/templates/spec`: Specification template
- `mcp://speckit/templates/plan`: Plan template
- `mcp://speckit/templates/tasks`: Tasks template
- `mcp://speckit/templates/constitution`: Constitution template
- `mcp://speckit/templates/research`: Research template

### Documentation
- `mcp://speckit/docs/guides/{name}`: Workflow guides
- `mcp://speckit/docs/references/{name}`: Reference documentation
- `mcp://speckit/docs/examples/{name}`: Example projects

### Configuration
- `mcp://speckit/config/schema`: Configuration schema
- `mcp://speckit/config/defaults`: Default configuration

### Workflows
- `mcp://speckit/workflows/specify`: Specify workflow
- `mcp://speckit/workflows/plan`: Plan workflow
- `mcp://speckit/workflows/tasks`: Tasks workflow"""

    def _get_specify_guide_content(self) -> str:
        """Get specification workflow guide content."""
        return """# Specification Workflow Guide

## Overview

The specification workflow creates detailed feature specifications from high-level descriptions.

## Process

### 1. Prepare Description
Write a clear, concise description of the feature you want to build. Include:
- Problem being solved
- Target users
- Key functionality
- Success criteria

### 2. Run Specify Tool
```python
await client.call_tool('specify', {
    'description': 'Your feature description',
    'repository_path': '/path/to/repo'
})
```

### 3. Review Generated Spec
The tool will:
- Create a feature branch
- Generate specification from template
- Commit to repository

### 4. Refine Specification
Edit the generated specification to:
- Add detailed requirements
- Clarify design decisions
- Include acceptance criteria
- Document risks

## Best Practices

### Writing Descriptions
- Be specific about the problem
- Include user stories
- Mention constraints
- List success metrics

### Specification Structure
- Keep sections organized
- Use clear requirement IDs
- Include diagrams when helpful
- Document assumptions

### Collaboration
- Share specs for review
- Get stakeholder approval
- Track changes in git
- Update as needed"""

    def _get_plan_guide_content(self) -> str:
        """Get planning workflow guide content."""
        return """# Planning Workflow Guide

## Overview

The planning workflow generates implementation plans from specifications.

## Process

### 1. Review Specification
Ensure the specification is complete with:
- Clear requirements
- Design decisions
- Success criteria
- Test strategy

### 2. Run Plan Tool
```python
await client.call_tool('plan', {
    'spec_path': 'specs/001-feature.md',
    'repository_path': '/path/to/repo',
    'tech_stack': ['python', 'fastapi', 'postgresql']
})
```

### 3. Review Generated Plan
The tool will create:
- Architecture design
- Component breakdown
- Development phases
- Risk assessment

### 4. Customize Plan
Adjust the plan to:
- Add specific technologies
- Define milestones
- Allocate resources
- Set timelines

## Best Practices

### Architecture Design
- Start with high-level overview
- Define component boundaries
- Document data flow
- Identify integration points

### Phase Planning
- Break into manageable phases
- Define clear deliverables
- Identify dependencies
- Include testing phases

### Risk Management
- Identify technical risks
- Plan mitigation strategies
- Build in contingencies
- Monitor progress"""

    def _get_tasks_guide_content(self) -> str:
        """Get tasks workflow guide content."""
        return """# Task Breakdown Guide

## Overview

The tasks workflow creates detailed task breakdowns from implementation plans.

## Process

### 1. Review Plan
Ensure the plan includes:
- Clear phases
- Component design
- Technical approach
- Testing strategy

### 2. Run Tasks Tool
```python
await client.call_tool('tasks', {
    'plan_path': 'plans/001-feature-plan.md',
    'repository_path': '/path/to/repo',
    'parallel_groups': 3
})
```

### 3. Review Task Breakdown
The tool generates:
- Numbered tasks
- Dependencies
- Parallel groups
- Time estimates

### 4. Execute Tasks
Follow the breakdown to:
- Complete tasks in order
- Run parallel tasks simultaneously
- Track progress
- Update status

## Best Practices

### Task Definition
- Make tasks atomic
- Define clear deliverables
- Include acceptance criteria
- Estimate realistically

### Dependency Management
- Map dependencies clearly
- Avoid circular dependencies
- Identify blockers early
- Plan critical path

### Progress Tracking
- Update task status
- Document blockers
- Communicate progress
- Adjust as needed"""

    async def get_documentation_resource(
        self,
        category: str,
        name: Optional[str] = None,
        phase: Optional[str] = None
    ) -> Resource:
        """
        Serve documentation as an MCP resource.

        Args:
            category: Documentation category (guides, references, examples)
            name: Specific document name
            phase: Filter by development phase

        Returns:
            MCP Resource with documentation content

        Raises:
            McpError: If document not found or invalid category
        """
        # Map category to document lookup
        if category == 'references' and name == 'constitution':
            doc = self.documents.get('constitution')
        elif category == 'references' and name == 'api':
            doc = self.documents.get('api-reference')
        elif category == 'guides' and name == 'quickstart':
            doc = self.documents.get('quickstart')
        elif category == 'guides' and name == 'specify':
            doc = self.documents.get('specify-guide')
        elif category == 'guides' and name == 'plan':
            doc = self.documents.get('plan-guide')
        elif category == 'guides' and name == 'tasks':
            doc = self.documents.get('tasks-guide')
        else:
            doc = None

        if not doc:
            raise McpError(f"Documentation not found: {category}/{name}")

        # Apply phase filtering if requested
        if phase:
            try:
                phase_enum = DevelopmentPhase(phase.lower())
                if not doc.is_visible_for_phase(phase_enum):
                    raise McpError(f"Document not available for phase: {phase}")
            except ValueError:
                raise McpError(f"Invalid phase: {phase}")

        # Create resource
        uri = f"mcp://speckit/docs/{category}/{name}"

        return Resource(
            uri=uri,
            name=doc.title,
            mimeType="text/markdown",
            text=doc.content,
            metadata={
                "document_id": doc.document_id,
                "document_type": doc.document_type.value,
                "phase": doc.phase.value,
                "workflow": doc.workflow,
                "visibility": doc.visibility.value,
                "priority": doc.priority,
                "tags": doc.tags,
                "summary": doc.summary
            }
        )

    async def list_documentation(self, category: Optional[str] = None) -> List[Resource]:
        """
        List available documentation resources.

        Args:
            category: Optional category filter

        Returns:
            List of available documentation resources
        """
        resources = []

        for doc_id, doc in self.documents.items():
            # Determine category
            if doc.document_type == DocumentType.GUIDE:
                doc_category = 'guides'
            elif doc.document_type in [DocumentType.CONSTITUTION, DocumentType.API]:
                doc_category = 'references'
            else:
                doc_category = 'examples'

            # Apply category filter
            if category and doc_category != category:
                continue

            # Determine name from document ID
            name = doc_id.replace('-guide', '').replace('-reference', '')

            uri = f"mcp://speckit/docs/{doc_category}/{name}"

            resources.append(Resource(
                uri=uri,
                name=doc.title,
                mimeType="text/markdown",
                description=doc.summary,
                metadata={
                    "document_type": doc.document_type.value,
                    "phase": doc.phase.value,
                    "workflow": doc.workflow,
                    "tags": doc.tags
                }
            ))

        return resources


# Create singleton instance
_documentation_resources = DocumentationResources()


async def serve_documentation(uri: str) -> Resource:
    """
    Serve a documentation resource based on URI.

    Expected URI format: mcp://speckit/docs/{category}/{name}

    Args:
        uri: Resource URI

    Returns:
        MCP Resource containing documentation

    Raises:
        McpError: If URI is invalid or document not found
    """
    if not uri.startswith("mcp://speckit/docs/"):
        raise McpError(f"Invalid documentation URI: {uri}")

    parts = uri.replace("mcp://speckit/docs/", "").split("/")

    if len(parts) == 0:
        # List all documentation
        docs = await _documentation_resources.list_documentation()
        return Resource(
            uri="mcp://speckit/docs",
            name="Available Documentation",
            mimeType="application/json",
            metadata={
                "documents": [
                    {
                        "uri": d.uri,
                        "name": d.name,
                        "description": d.description
                    } for d in docs
                ]
            }
        )
    elif len(parts) == 1:
        # List documentation in category
        category = parts[0]
        docs = await _documentation_resources.list_documentation(category)
        return Resource(
            uri=f"mcp://speckit/docs/{category}",
            name=f"{category.title()} Documentation",
            mimeType="application/json",
            metadata={
                "documents": [
                    {
                        "uri": d.uri,
                        "name": d.name,
                        "description": d.description
                    } for d in docs
                ]
            }
        )
    else:
        # Get specific document
        category = parts[0]
        name = parts[1]
        return await _documentation_resources.get_documentation_resource(category, name)


async def list_documentation_resources() -> List[Resource]:
    """
    List all available documentation resources.

    Returns:
        List of available documentation resources
    """
    return await _documentation_resources.list_documentation()