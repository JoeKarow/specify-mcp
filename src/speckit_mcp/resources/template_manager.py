"""
Template management for the SpecKit MCP server.

This module handles loading embedded templates from package resources,
parsing YAML front matter, and performing variable substitution.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from importlib import resources

from .models import Template, TemplateType


class TemplateError(Exception):
    """Exception raised when template operations fail."""
    pass


class TemplateManager:
    """
    Manages templates for specifications, plans, and tasks.

    This class handles loading embedded templates, parsing front matter,
    performing variable substitution, and caching for performance.
    """

    def __init__(self):
        """Initialize the template manager."""
        self._template_cache: Dict[str, Template] = {}
        self._embedded_templates = self._load_embedded_templates()

    def _load_embedded_templates(self) -> Dict[str, str]:
        """
        Load embedded templates from package resources.

        Returns:
            Dictionary mapping template names to content
        """
        templates = {}

        # Define embedded templates
        embedded_content = {
            'spec': self._get_spec_template(),
            'plan': self._get_plan_template(),
            'tasks': self._get_tasks_template(),
            'constitution': self._get_constitution_template(),
            'research': self._get_research_template()
        }

        for name, content in embedded_content.items():
            templates[name] = content

        return templates

    def _get_spec_template(self) -> str:
        """Get the default specification template."""
        return """---
template: spec
version: 1.0.0
variables:
  - feature_id
  - feature_name
  - description
  - repository_path
---

# Feature Specification: {{feature_name}}

**Feature ID**: {{feature_id}}
**Repository**: {{repository_path}}
**Date**: {{date}}

## Overview

{{description}}

## Motivation

*Why is this feature needed? What problem does it solve?*

## Requirements

### Functional Requirements

1. **[FR-001]** Primary functionality requirement
2. **[FR-002]** Secondary functionality requirement
3. **[FR-003]** Tertiary functionality requirement

### Non-Functional Requirements

1. **[NFR-001]** Performance requirement
2. **[NFR-002]** Security requirement
3. **[NFR-003]** Usability requirement

## Design

### Architecture

*High-level design and component interaction*

### Data Model

*Key entities and relationships*

### API Design

*Interfaces and contracts*

## Implementation Plan

### Phase 1: Foundation
- Set up project structure
- Create core models
- Write initial tests

### Phase 2: Core Features
- Implement main functionality
- Add integration tests
- Handle error cases

### Phase 3: Polish
- Optimize performance
- Add documentation
- Final testing

## Testing Strategy

### Unit Tests
- Test individual components
- Mock external dependencies
- Verify edge cases

### Integration Tests
- Test component interactions
- Verify workflows
- Test error handling

### Acceptance Tests
- Verify requirements are met
- Test user scenarios
- Validate performance

## Success Criteria

- [ ] All functional requirements implemented
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Performance metrics met
- [ ] Security review passed

## Notes

*Additional considerations and references*
"""

    def _get_plan_template(self) -> str:
        """Get the default plan template."""
        return """---
template: plan
version: 1.0.0
variables:
  - feature_id
  - feature_name
  - spec_path
---

# Implementation Plan: {{feature_name}}

**Feature ID**: {{feature_id}}
**Specification**: {{spec_path}}
**Generated**: {{date}}

## Architecture

### System Context

```
[External System] <--> [Our Component] <--> [Database]
```

### Component Design

#### Core Components
1. **Component A**: Handles X functionality
2. **Component B**: Manages Y operations
3. **Component C**: Provides Z interface

#### Data Flow
1. Input validation
2. Business logic processing
3. Data persistence
4. Response generation

## Tech Stack

### Languages & Frameworks
- Python 3.11+
- FastMCP for MCP protocol
- Pydantic for validation

### Dependencies
- PyYAML: Configuration parsing
- pytest: Testing framework
- asyncio: Async operations

### Development Tools
- mise: Toolchain management
- uv: Package management
- git: Version control

## Development Phases

### Phase 1: Foundation (Days 1-2)
- Project setup
- Core models
- Basic tests

### Phase 2: Implementation (Days 3-5)
- Main features
- Integration
- Error handling

### Phase 3: Testing & Polish (Days 6-7)
- Complete test coverage
- Documentation
- Performance optimization

## Risk Assessment

### Technical Risks
1. **Risk**: Complex integration
   **Mitigation**: Incremental implementation with tests

2. **Risk**: Performance issues
   **Mitigation**: Profile early, optimize critical paths

### Schedule Risks
1. **Risk**: Scope creep
   **Mitigation**: Strict adherence to spec

## Deliverables

1. Source code with tests
2. Documentation
3. Configuration templates
4. Deployment guide

## Success Metrics

- Code coverage > 80%
- All tests passing
- Performance benchmarks met
- Zero critical bugs
"""

    def _get_tasks_template(self) -> str:
        """Get the default tasks template."""
        return """---
template: tasks
version: 1.0.0
variables:
  - feature_id
  - feature_name
  - plan_path
---

# Tasks: {{feature_name}}

**Feature ID**: {{feature_id}}
**Plan**: {{plan_path}}
**Generated**: {{date}}

## Execution Summary

Total Tasks: {{task_count}}
Parallel Groups: {{parallel_groups}}
Estimated Duration: {{estimated_duration}}

## Task Breakdown

### Setup Phase

- [ ] T001: Initialize project structure
- [ ] T002: Configure dependencies
- [ ] T003: Set up development environment

### Test Phase (TDD)

- [ ] T004: Write unit tests for core models
- [ ] T005: Write integration tests for workflows
- [ ] T006: Write contract tests for APIs

### Implementation Phase

- [ ] T007: Implement core models
- [ ] T008: Implement business logic
- [ ] T009: Implement API endpoints
- [ ] T010: Add error handling

### Integration Phase

- [ ] T011: Connect components
- [ ] T012: Verify workflows
- [ ] T013: Test error scenarios

### Polish Phase

- [ ] T014: Optimize performance
- [ ] T015: Complete documentation
- [ ] T016: Final testing

## Dependencies

```
Setup (T001-T003) → Tests (T004-T006) → Implementation (T007-T010) → Integration (T011-T013) → Polish (T014-T016)
```

## Parallel Execution

Tasks that can run in parallel:
- T004, T005, T006 (different test files)
- T007, T008 (independent modules)
- T014, T015 (different concerns)

## Validation Checklist

- [ ] All tests written before implementation
- [ ] Each task has clear deliverables
- [ ] Dependencies properly mapped
- [ ] Parallel tasks identified
- [ ] Time estimates reasonable
"""

    def _get_constitution_template(self) -> str:
        """Get the default constitution template."""
        return """---
template: constitution
version: 1.0.0
variables:
  - project_name
  - description
---

# {{project_name}} Constitution

## Project Information

**Name**: {{project_name}}
**Description**: {{description}}
**Version**: 1.0.0

## Constitutional Principles

### 1. MCP Protocol Compliance
All functionality must be exposed through MCP tools and resources.
**Priority**: 1

### 2. File System Preservation
Maintain git-integrated workflow without external dependencies.
**Priority**: 2

### 3. Test-First Development
Write failing tests before implementation (TDD).
**Priority**: 3

### 4. Structured Data
Use YAML over markdown for machine-parsable data.
**Priority**: 4

### 5. Simplicity (YAGNI)
Build MVP without premature features.
**Priority**: 5

### 6. Cross-Platform Support
No shell dependencies, pure Python implementation.
**Priority**: 6

## Workflow Configuration

### Specify Workflow
- Create feature branch
- Generate specification
- Commit changes

### Plan Workflow
- Load specification
- Analyze requirements
- Generate plan

### Tasks Workflow
- Load plan
- Generate tasks
- Apply rules

## Settings

- Auto-commit: enabled
- Verbose logging: disabled
- Max parallel tasks: 5
"""

    def _get_research_template(self) -> str:
        """Get the default research template."""
        return """---
template: research
version: 1.0.0
variables:
  - feature_name
  - research_topic
---

# Research: {{feature_name}}

**Topic**: {{research_topic}}
**Date**: {{date}}

## Summary

*Brief overview of research findings*

## Key Findings

### Finding 1
- Description
- Impact
- Recommendations

### Finding 2
- Description
- Impact
- Recommendations

## Technical Details

### Option A
**Pros**:
- Advantage 1
- Advantage 2

**Cons**:
- Disadvantage 1
- Disadvantage 2

### Option B
**Pros**:
- Advantage 1
- Advantage 2

**Cons**:
- Disadvantage 1
- Disadvantage 2

## Recommendations

1. Primary recommendation
2. Secondary recommendation
3. Alternative approach

## References

- [Reference 1](url)
- [Reference 2](url)
- [Reference 3](url)

## Next Steps

- [ ] Validate approach
- [ ] Create proof of concept
- [ ] Document decision
"""

    def parse_front_matter(self, content: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Parse YAML front matter from template content.

        Args:
            content: Template content with optional front matter

        Returns:
            Tuple of (front_matter_dict, content_without_front_matter)
        """
        if not content.startswith('---'):
            return None, content

        # Split on the front matter delimiters
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None, content

        front_matter_text = parts[1].strip()
        content_body = parts[2].strip()

        if not front_matter_text:
            return None, content_body

        try:
            front_matter = yaml.safe_load(front_matter_text)
            return front_matter, content_body
        except yaml.YAMLError:
            return None, content

    def get_template(
        self,
        template_type: TemplateType,
        custom_path: Optional[str] = None
    ) -> Template:
        """
        Get a template by type.

        Args:
            template_type: Type of template to retrieve
            custom_path: Optional path to custom template file

        Returns:
            Template object

        Raises:
            TemplateError: If template cannot be loaded
        """
        # Check cache first
        cache_key = f"{template_type.value}:{custom_path or 'embedded'}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Load template content
        if custom_path:
            content = self._load_custom_template(custom_path)
            is_embedded = False
            source_path = custom_path
        else:
            content = self._embedded_templates.get(template_type.value)
            if not content:
                raise TemplateError(f"No embedded template for type: {template_type}")
            is_embedded = True
            source_path = None

        # Parse front matter
        front_matter, body = self.parse_front_matter(content)

        # Extract variables from content
        variables = self._extract_variables(body)

        # Extract sections from content
        sections = self._extract_sections(body)

        # Create Template object
        template = Template(
            name=template_type.value,
            template_type=template_type,
            version=front_matter.get('version', '1.0.0') if front_matter else '1.0.0',
            content=content,
            variables=variables,
            sections=sections,
            description=front_matter.get('description') if front_matter else None,
            is_embedded=is_embedded,
            source_path=source_path
        )

        # Cache the template
        self._template_cache[cache_key] = template

        return template

    def _load_custom_template(self, file_path: str) -> str:
        """
        Load a custom template from file.

        Args:
            file_path: Path to template file

        Returns:
            Template content

        Raises:
            TemplateError: If file cannot be read
        """
        path = Path(file_path)

        if not path.exists():
            raise TemplateError(f"Template file not found: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise TemplateError(f"Could not read template file: {e}")

    def _extract_variables(self, content: str) -> List[str]:
        """
        Extract template variables from content.

        Args:
            content: Template content

        Returns:
            List of variable names found in content
        """
        # Find {{variable}} patterns
        pattern = r'\{\{(\w+)\}\}'
        variables = re.findall(pattern, content)

        # Remove duplicates while preserving order
        seen = set()
        unique_vars = []
        for var in variables:
            if var not in seen and var != 'date':  # Skip built-in variables
                seen.add(var)
                unique_vars.append(var)

        return unique_vars

    def _extract_sections(self, content: str) -> List[str]:
        """
        Extract markdown sections from content.

        Args:
            content: Template content

        Returns:
            List of section headings
        """
        # Find markdown headers
        pattern = r'^#+\s+(.+)$'
        sections = re.findall(pattern, content, re.MULTILINE)
        return sections

    def substitute_variables(
        self,
        template: Template,
        variables: Dict[str, str]
    ) -> str:
        """
        Substitute variables in template content.

        Args:
            template: Template object
            variables: Dictionary of variable substitutions

        Returns:
            Content with variables substituted

        Raises:
            TemplateError: If required variables are missing
        """
        # Add built-in variables
        from datetime import datetime
        all_vars = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            **variables
        }

        # Check for missing required variables
        missing = set(template.variables) - set(all_vars.keys())
        if missing:
            raise TemplateError(f"Missing required variables: {missing}")

        # Perform substitution
        content = template.content

        # Remove front matter if present
        _, body = self.parse_front_matter(content)
        if body != content:
            content = body

        for var_name, var_value in all_vars.items():
            pattern = f'{{{{{var_name}}}}}'
            content = content.replace(pattern, str(var_value))

        return content

    def list_templates(self, include_custom: bool = False) -> List[Dict[str, Any]]:
        """
        List available templates.

        Args:
            include_custom: Whether to include custom templates

        Returns:
            List of template information dictionaries
        """
        templates = []

        # Add embedded templates
        for name in self._embedded_templates.keys():
            templates.append({
                'name': name,
                'type': name,
                'embedded': True,
                'description': f"Embedded {name} template"
            })

        # TODO: Add custom templates if include_custom is True

        return templates

    def validate_template(self, template_path: str) -> bool:
        """
        Validate a template file.

        Args:
            template_path: Path to template file

        Returns:
            True if template is valid

        Raises:
            TemplateError: If template is invalid
        """
        try:
            content = self._load_custom_template(template_path)
            front_matter, body = self.parse_front_matter(content)

            # Check for required elements
            if not body:
                raise TemplateError("Template body is empty")

            # Check variables are properly formatted
            variables = self._extract_variables(body)

            # Try to create a Template object
            Template(
                name="validation_test",
                template_type=TemplateType.SPEC,
                content=content,
                variables=variables,
                is_embedded=False,
                source_path=template_path
            )

            return True

        except Exception as e:
            raise TemplateError(f"Invalid template: {e}")

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()