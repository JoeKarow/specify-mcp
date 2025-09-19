# Quickstart Guide: Speckit MCP Server

## Prerequisites

- Python 3.11 or higher
- Git installed and available in PATH
- An MCP-compatible client (Claude Desktop, VS Code with MCP extension, etc.)
- mise (for Python version management)
- uv (for package management)

## Installation

### 1. Install the MCP Server

```bash
# Clone the repository
git clone https://github.com/your-org/speckit-mcp.git
cd speckit-mcp

# Set up Python environment with mise
mise install

# Install dependencies with uv
uv pip install -e .
```

### 2. Configure Your MCP Client

Add to your MCP client configuration (e.g., `~/.config/claude/mcp.json` for Claude Desktop):

```json
{
  "mcpServers": {
    "speckit": {
      "command": "python",
      "args": ["-m", "speckit_mcp.server"],
      "transport": "stdio"
    }
  }
}
```

### 3. Verify Installation

```bash
# Test the server directly
python -m speckit_mcp.server --version

# Or through your MCP client
# The server should appear in available MCP servers list
```

## Quick Start Examples

### Example 1: Create a New Feature Specification

```python
# In your MCP client, invoke the specify tool:
await mcp.tools.specify({
  "description": "Add user authentication with OAuth2 support",
  "repository_path": "/path/to/your/project"
})

# This will:
# 1. Create branch: 001-user-authentication
# 2. Generate: specs/001-user-authentication/spec.md
# 3. Return session ID for tracking
```

**Expected Output:**
- New git branch created and checked out
- Specification file generated with feature requirements
- Ready for planning phase

### Example 2: Generate Implementation Plan

```python
# Continue with the plan tool:
await mcp.tools.plan({
  "spec_path": "/path/to/project/specs/001-user-authentication/spec.md",
  "repository_path": "/path/to/your/project"
})

# This will generate:
# - plan.md (implementation strategy)
# - research.md (technical decisions)
# - data-model.md (entity definitions)
# - contracts/ (API specifications)
```

**Expected Output:**
- Complete implementation plan with phases
- Research document with resolved technical choices
- Data model and API contracts ready for implementation

### Example 3: Generate Task Breakdown

```python
# Create executable tasks:
await mcp.tools.tasks({
  "plan_path": "/path/to/project/specs/001-user-authentication/plan.md",
  "repository_path": "/path/to/your/project",
  "group_parallel": true
})

# This creates:
# - tasks.yaml (structured task list)
# - Identifies parallel execution groups
# - Orders tasks by dependencies
```

**Expected Output:**
- Structured task file with 20-30 tasks
- Tasks marked for parallel execution where possible
- Ready for implementation phase

## Project Configuration

### Initialize a New Project

```python
await mcp.tools.initialize_project({
  "repository_path": "/path/to/your/project",
  "project_name": "my-awesome-project"
})
```

This creates `.specify-mcp/constitution.yaml`:

```yaml
version: "1.0.0"
project_name: "my-awesome-project"
workflows:
  - specify
  - plan
  - tasks
settings:
  auto_generate_config: true
  preserve_existing: true
```

### Customize Templates

Override default templates in your constitution.yaml:

```yaml
templates:
  spec: "custom-templates/my-spec.md"
  plan: "custom-templates/my-plan.md"
```

## Common Workflows

### Complete Feature Development Cycle

1. **Describe Your Feature**
   ```python
   result = await mcp.tools.specify({
     "description": "Your feature description here",
     "repository_path": "/your/project"
   })
   ```

2. **Review and Refine Specification**
   - Edit `specs/[branch]/spec.md` if needed
   - Ensure requirements are clear

3. **Generate Implementation Plan**
   ```python
   result = await mcp.tools.plan({
     "spec_path": result.spec_path,
     "repository_path": "/your/project"
   })
   ```

4. **Create Tasks**
   ```python
   result = await mcp.tools.tasks({
     "plan_path": result.plan_path,
     "repository_path": "/your/project"
   })
   ```

5. **Execute Tasks**
   - Follow tasks in order
   - Run parallel tasks concurrently
   - Mark tasks complete as you progress

## Verification Steps

### Test the Complete Workflow

```bash
# 1. Create a test repository
mkdir test-project && cd test-project
git init

# 2. Through your MCP client, run:
# - Initialize project
# - Create a simple feature spec
# - Generate plan
# - Create tasks

# 3. Verify generated files:
ls -la specs/*/
cat .specify-mcp/constitution.yaml

# 4. Check git branches:
git branch -a
```

### Expected File Structure

After running all workflows:

```
test-project/
├── .git/
├── .specify-mcp/
│   ├── constitution.yaml
│   └── tasks/
│       └── 001-feature.yaml
└── specs/
    └── 001-feature/
        ├── spec.md
        ├── plan.md
        ├── research.md
        ├── data-model.md
        ├── quickstart.md
        ├── contracts/
        │   ├── mcp-tools.json
        │   └── mcp-resources.json
        └── tasks.yaml
```

## Troubleshooting

### Server Not Starting

```bash
# Check Python version
python --version  # Should be 3.11+

# Verify installation
python -m speckit_mcp.server --help

# Check MCP client logs
tail -f ~/.specify-mcp/logs/server.log
```

### Git Operations Failing

```bash
# Ensure git is configured
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify repository
cd /your/project && git status
```

### Configuration Not Loading

```bash
# Check configuration exists
cat .specify-mcp/constitution.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.specify-mcp/constitution.yaml'))"
```

## Next Steps

1. **Customize Your Workflow**: Edit `.specify-mcp/constitution.yaml`
2. **Create Custom Templates**: Override defaults with project-specific templates
3. **Integrate with CI/CD**: Use generated tasks in your pipeline
4. **Enable Team Collaboration**: Share configuration across team

## Support

- **Documentation**: Full docs at `/resources/documentation/guide`
- **API Reference**: Available at `/resources/documentation/api`
- **Issue Tracking**: Report issues through your organization's tracker
- **Logs**: Check `~/.specify-mcp/logs/` for detailed debugging