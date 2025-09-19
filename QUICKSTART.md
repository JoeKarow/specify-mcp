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
# Test the server directly (it will start and wait for stdio input)
python -m speckit_mcp.server

# The server should start and display the FastMCP banner
# Press Ctrl+C to stop the test
```

## Quick Start Examples

### Example 1: Create a New Feature Specification

```json
// In your MCP client, invoke the specify tool:
{
  "tool": "specify",
  "arguments": {
    "description": "Add user authentication with OAuth2 support",
    "repository_path": "/path/to/your/project"
  }
}
```

**What this does:**
1. Creates branch: `001-user-authentication`
2. Generates: `specs/001-user-authentication/spec.md`
3. Returns session ID for tracking

**Expected Output:**
```json
{
  "success": true,
  "branch_name": "001-user-authentication",
  "spec_path": "/path/to/project/specs/001-user-authentication/spec.md",
  "session_id": "unique-session-id"
}
```

### Example 2: Generate Implementation Plan

```json
// Continue with the plan tool:
{
  "tool": "plan",
  "arguments": {
    "spec_path": "/path/to/project/specs/001-user-authentication/spec.md",
    "repository_path": "/path/to/your/project"
  }
}
```

**What this generates:**
- `plan.md` (implementation strategy)
- `research.md` (technical decisions)
- `data-model.md` (entity definitions)
- `contracts/` (API specifications)

**Expected Output:**
```json
{
  "success": true,
  "plan_path": "/path/to/project/specs/001-user-authentication/plan.md",
  "files_generated": [
    "plan.md",
    "research.md",
    "data-model.md",
    "contracts/mcp-tools.json",
    "contracts/mcp-resources.json"
  ]
}
```

### Example 3: Generate Task Breakdown

```json
// Create executable tasks:
{
  "tool": "tasks",
  "arguments": {
    "plan_path": "/path/to/project/specs/001-user-authentication/plan.md",
    "repository_path": "/path/to/your/project",
    "group_parallel": true
  }
}
```

**What this creates:**
- `tasks.yaml` (structured task list)
- Identifies parallel execution groups
- Orders tasks by dependencies

**Expected Output:**
```json
{
  "success": true,
  "tasks_path": "/path/to/project/specs/001-user-authentication/tasks.yaml",
  "task_count": 25,
  "parallel_groups": 3
}
```

## Project Configuration

### Initialize a New Project

```json
{
  "tool": "initialize_project",
  "arguments": {
    "repository_path": "/path/to/your/project",
    "project_name": "my-awesome-project"
  }
}
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

## Available MCP Tools

The server provides these MCP tools:

1. **specify** - Create feature specifications from descriptions
2. **plan** - Generate implementation plans from specifications
3. **tasks** - Create task breakdowns from plans
4. **initialize_project** - Set up project configuration
5. **get_context** - Retrieve project context and configuration

## Available MCP Resources

The server provides these MCP resources:

1. **templates/** - Access to all specification templates
2. **documentation/** - Complete API and usage documentation
3. **configuration/** - Project configuration schemas
4. **workflows/** - Available workflow definitions

## Common Workflows

### Complete Feature Development Cycle

1. **Describe Your Feature**
   ```json
   {
     "tool": "specify",
     "arguments": {
       "description": "Your feature description here",
       "repository_path": "/your/project"
     }
   }
   ```

2. **Review and Refine Specification**
   - Edit `specs/[branch]/spec.md` if needed
   - Ensure requirements are clear

3. **Generate Implementation Plan**
   ```json
   {
     "tool": "plan",
     "arguments": {
       "spec_path": "path-from-specify-result",
       "repository_path": "/your/project"
     }
   }
   ```

4. **Create Tasks**
   ```json
   {
     "tool": "tasks",
     "arguments": {
       "plan_path": "path-from-plan-result",
       "repository_path": "/your/project"
     }
   }
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

# 2. Configure git (required for git operations)
git config user.name "Test User"
git config user.email "test@example.com"

# 3. Create an initial commit
echo "# Test Project" > README.md
git add README.md
git commit -m "Initial commit"

# 4. Through your MCP client, run:
# - Initialize project (optional)
# - Create a simple feature spec
# - Generate plan
# - Create tasks

# 5. Verify generated files:
ls -la specs/*/
cat .specify-mcp/constitution.yaml

# 6. Check git branches:
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
├── README.md
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
python -m speckit_mcp.server
# Should show FastMCP banner and wait for input

# Check if package is installed
pip show speckit-mcp
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

### MCP Client Connection Issues

1. **Check MCP Client Configuration**: Ensure the server path and arguments are correct in your MCP client config
2. **Verify Server Executable**: Test running `python -m speckit_mcp.server` directly
3. **Check Logs**: Look for error messages in your MCP client logs
4. **Test with Simple MCP Client**: Try connecting with a basic MCP client to isolate issues

## Next Steps

1. **Customize Your Workflow**: Edit `.specify-mcp/constitution.yaml`
2. **Create Custom Templates**: Override defaults with project-specific templates
3. **Integrate with CI/CD**: Use generated tasks in your pipeline
4. **Enable Team Collaboration**: Share configuration across team

## Support

- **Documentation**: Full docs available via MCP resources
- **API Reference**: Access via `get_context` tool
- **Issue Tracking**: Report issues through your organization's tracker
- **Logs**: Check `~/.specify-mcp/logs/` for detailed debugging