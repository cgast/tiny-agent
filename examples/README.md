# Examples

This directory contains complete, ready-to-use examples demonstrating different use cases for the CLI agent.

## Available Examples

### 1. [Analyze Codebase](./analyze-codebase/)
Analyze code repositories and generate insights.

**Use Cases:**
- Count lines of code by language
- Find TODO/FIXME comments
- List dependencies and imports
- Review project structure
- Analyze git history

**Example:**
```bash
cp examples/analyze-codebase/commands.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "Analyze this Python project and summarize it"
```

### 2. [Log Analysis](./log-analysis/)
Analyze application logs and troubleshoot issues.

**Use Cases:**
- Find and count errors/warnings
- Search for specific patterns
- Monitor log file sizes
- Identify unique IPs
- Analyze time ranges

**Example:**
```bash
cp examples/log-analysis/commands.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "How many errors are in the logs?" ./your-logs
```

### 3. [Data Processing](./data-processing/)
Process and analyze CSV and JSON data.

**Use Cases:**
- Read and query CSV files
- Extract and sort columns
- Query JSON with jq
- Fetch data from APIs
- Generate summaries

**Example:**
```bash
cp examples/data-processing/commands.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "Summarize the sales data by product" ./data
```

### 4. [DevOps Tasks](./devops-tasks/)
Perform DevOps and infrastructure tasks.

**Use Cases:**
- Audit Docker configurations
- Check CI/CD setups
- Monitor disk usage
- Review dependencies
- Validate environment configs

**Example:**
```bash
cp examples/devops-tasks/commands.json commands.json
docker build -t cli-agent:latest .
./run-agent.sh "Audit this project for DevOps best practices"
```

## Quick Start

Each example directory contains:
- `commands.json` - Tool definitions for the specific use case
- `README.md` - Detailed documentation and usage examples

### Using an Example

1. **Copy the commands:**
   ```bash
   cp examples/<example-name>/commands.json commands.json
   ```

2. **Rebuild Docker image:**
   ```bash
   docker build -t cli-agent:latest .
   ```

3. **Run the agent:**
   ```bash
   ./run-agent.sh "Your task here"
   ```

### Using Multiple Examples

You can combine tools from multiple examples:

```bash
# Merge multiple command sets
jq -s 'add' \
  examples/analyze-codebase/commands.json \
  examples/devops-tasks/commands.json \
  > commands.json
```

## Comparison Matrix

| Example | Tools | Best For | Complexity |
|---------|-------|----------|------------|
| **analyze-codebase** | 8 | Code reviews, project analysis | Medium |
| **log-analysis** | 9 | Troubleshooting, monitoring | Easy |
| **data-processing** | 10 | Data analysis, ETL tasks | Medium |
| **devops-tasks** | 10 | Infrastructure, deployments | Advanced |

## Creating Your Own Example

To create a new example:

1. **Create directory:**
   ```bash
   mkdir examples/my-example
   ```

2. **Create commands.json:**
   ```bash
   cat > examples/my-example/commands.json << 'EOF'
   [
     {
       "name": "my_tool",
       "description": "What it does",
       "command": "bash_command {arg}",
       "parameters": {...}
     }
   ]
   EOF
   ```

3. **Create README.md:**
   - Describe the use case
   - List the tools
   - Provide usage examples
   - Show sample output

4. **Test it:**
   ```bash
   cp examples/my-example/commands.json commands.json
   docker build -t cli-agent:latest .
   ./run-agent.sh "Test task"
   ```

## Example Use Cases by Industry

### Software Development
- **analyze-codebase**: Code reviews, technical debt analysis
- **devops-tasks**: CI/CD audits, deployment checks

### Data Science
- **data-processing**: Data cleaning, exploratory analysis
- **log-analysis**: Experiment log analysis

### DevOps/SRE
- **devops-tasks**: Infrastructure audits, security checks
- **log-analysis**: Incident response, debugging

### Business Analysis
- **data-processing**: Report generation, data aggregation
- **log-analysis**: Usage analytics, error tracking

## Tips for Using Examples

1. **Start Simple**: Begin with one example, learn how it works
2. **Customize**: Modify commands.json to fit your specific needs
3. **Combine**: Mix tools from multiple examples for complex tasks
4. **Document**: Keep notes on what works well for your use cases
5. **Share**: Create your own examples and contribute back

## Template vs Example

**Templates** (`/templates/`):
- Individual tool categories
- Reusable building blocks
- Mix and match as needed

**Examples** (`/examples/`):
- Complete, ready-to-use configurations
- Specific use cases
- Documentation and sample output

Use templates to build custom tool sets, use examples to get started quickly.

## Contributing Examples

Want to contribute an example? Please include:

1. **commands.json** - Working tool definitions
2. **README.md** with:
   - Clear description
   - Usage instructions
   - Example tasks
   - Sample output
   - Customization tips
3. **Test it** - Make sure it actually works!

## Support

For help with examples:
- Read the example's README.md
- Check the main project README.md
- Review `/templates/README.md` for individual tools
- Open an issue on GitHub

## License

All examples are provided under the same license as the main project.
