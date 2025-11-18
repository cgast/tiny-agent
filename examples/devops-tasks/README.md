# DevOps Tasks Example

This example demonstrates using the agent for common DevOps and infrastructure tasks.

## What It Does

The agent can:
- Audit Docker configurations
- Check CI/CD setups
- Monitor disk usage
- Validate environment configs
- Review dependencies
- Check repository status

## Tools Included

- `find_dockerfiles` - Find Dockerfiles
- `find_compose_files` - Find docker-compose files
- `read_file` - Read file contents
- `find_ci_configs` - Find CI/CD configs
- `check_disk_usage` - Check disk space
- `get_directory_size` - Get directory size
- `find_large_files` - Find large files
- `check_env_file` - Check .env configuration
- `list_dependencies` - Find dependency files
- `check_git_status` - Check git status

## Usage

### Run DevOps Audit

```bash
# Copy commands
cp examples/devops-tasks/commands.json commands.json
docker build -t cli-agent:latest .

# Run audit on your project
./run-agent.sh "Audit this project for DevOps best practices" /path/to/project
```

## Example Tasks

### Docker Audit
```bash
./run-agent.sh "Find all Dockerfiles and check if they follow best practices"
./run-agent.sh "Do we have docker-compose.yml? Show me its contents"
./run-agent.sh "Check if Dockerfiles use specific base image versions"
```

### CI/CD Review
```bash
./run-agent.sh "What CI/CD system is this project using?"
./run-agent.sh "Show me the GitHub Actions workflows"
./run-agent.sh "Is there a deployment pipeline configured?"
```

### Resource Monitoring
```bash
./run-agent.sh "What's our current disk usage?"
./run-agent.sh "Find files larger than 100MB"
./run-agent.sh "Which directories are taking up the most space?"
```

### Configuration Audit
```bash
./run-agent.sh "Check if .env file exists and show its structure (hide values)"
./run-agent.sh "List all dependency files in the project"
./run-agent.sh "Are there any uncommitted changes?"
```

### Comprehensive Audit
```bash
./run-agent.sh "Perform a complete DevOps audit:
1. List all Docker configurations
2. Identify CI/CD setup
3. Check disk usage
4. Find large files
5. Review environment config
6. Check for uncommitted changes"
```

## Sample Output

```
🎯 Goal: Perform a DevOps audit on this project

--- Iteration 1 ---
🔧 Executing: find_dockerfiles({'path': '.'})
📋 Result: ./Dockerfile

--- Iteration 2 ---
🔧 Executing: find_compose_files({'path': '.'})
📋 Result: ./docker-compose.yml

--- Iteration 3 ---
🔧 Executing: find_ci_configs({'path': '.'})
📋 Result: ./.github

--- Iteration 4 ---
🔧 Executing: check_disk_usage({})
📋 Result:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   45G   55G  45% /

--- Iteration 5 ---
🔧 Executing: check_env_file({'path': '.'})
📋 Result:
OPENAI_API_KEY=****
ANTHROPIC_API_KEY=****

✅ Final result:
DevOps Audit Report:

**Docker Configuration:**
✅ Dockerfile found
✅ docker-compose.yml found
✅ Both use best practices (non-root user, specific versions)

**CI/CD Setup:**
✅ GitHub Actions configured (.github/ directory)
- Workflows: test.yml, deploy.yml

**Disk Usage:**
✅ System: 45% used (55G available)
⚠️ /workspace: 2.3G used

**Large Files:**
- None found over 100MB

**Environment Configuration:**
✅ .env file exists
✅ Contains: OPENAI_API_KEY, ANTHROPIC_API_KEY
⚠️ Ensure .env is in .gitignore

**Dependencies:**
✅ Python: requirements.txt not found (using pip install in Dockerfile)
- Direct dependencies: openai, anthropic

**Git Status:**
✅ Clean working directory
✅ On branch: main
✅ No uncommitted changes

**Recommendations:**
1. ✅ Good Docker security practices
2. ✅ CI/CD properly configured
3. ⚠️ Consider adding requirements.txt for reproducibility
4. ✅ Secrets properly managed via .env
5. ✅ Repository clean and ready for deployment
```

## Advanced Use Cases

### Security Audit

```bash
./run-agent.sh "Check for security issues:
- Are secrets exposed in any files?
- Is .env in .gitignore?
- Do Dockerfiles run as root?
- Are base images pinned to specific versions?"
```

### Dependency Analysis

```bash
./run-agent.sh "List all project dependencies and check for:
- Package.json if Node.js
- Requirements.txt if Python
- Go.mod if Go
- And show their contents"
```

### Pre-Deployment Check

```bash
./run-agent.sh "Pre-deployment checklist:
1. All tests passing?
2. No uncommitted changes?
3. Docker builds successfully?
4. Environment variables configured?
5. CI/CD pipeline green?"
```

## Customization

### Add Kubernetes Support

```json
{
  "name": "find_k8s_configs",
  "description": "Find Kubernetes manifests",
  "command": "find {path} -name '*.yaml' -o -name '*.yml' | xargs grep -l 'apiVersion'",
  "parameters": {...}
}
```

### Add Security Scanning

```json
{
  "name": "check_secrets",
  "description": "Scan for exposed secrets",
  "command": "grep -r 'password\\|secret\\|api_key\\|token' {path} --exclude-dir=.git",
  "parameters": {...}
}
```

### Add Health Checks

```json
{
  "name": "check_service_health",
  "description": "Check if service is responding",
  "command": "curl -f {url}/health || echo 'Service unavailable'",
  "parameters": {...}
}
```

## Best Practices Checked

### Dockerfile
- [ ] Uses specific base image version
- [ ] Runs as non-root user
- [ ] Multi-stage build for smaller images
- [ ] No secrets in build args
- [ ] Health check defined

### docker-compose.yml
- [ ] Version specified
- [ ] Resource limits set
- [ ] Environment variables from .env
- [ ] Volumes properly mounted
- [ ] Networks configured

### CI/CD
- [ ] Automated testing
- [ ] Automated builds
- [ ] Deployment pipeline
- [ ] Security scanning
- [ ] Code quality checks

### Configuration
- [ ] .env for secrets
- [ ] .env in .gitignore
- [ ] All required env vars documented
- [ ] Config validation on startup

## Tips

1. **Start with discovery**: Find all relevant files first
2. **Read before judging**: Look at actual content before suggesting changes
3. **Security first**: Always check for exposed secrets
4. **Document findings**: Agent can create an audit report
5. **Be specific**: Ask about specific best practices you care about

## Related Examples

- See `examples/log-analysis/` for monitoring application logs
- See `examples/analyze-codebase/` for code quality checks
