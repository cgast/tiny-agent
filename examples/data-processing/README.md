# Data Processing Example

This example demonstrates using the agent to process and analyze CSV and JSON data files.

## What It Does

The agent can:
- Find and read CSV/JSON files
- Count rows and extract columns
- Query JSON with jq
- Sort and filter data
- Fetch data from APIs
- Generate summaries

## Tools Included

- `find_csv_files` - Find all CSV files
- `find_json_files` - Find all JSON files
- `csv_head` - Show first N rows
- `csv_count_rows` - Count total rows
- `csv_extract_column` - Extract column
- `json_read` - Read and format JSON
- `json_query` - Query with jq
- `json_keys` - List JSON keys
- `http_get_json` - Fetch from API
- `sort_csv_column` - Sort by column

## Usage

### Setup Test Data

```bash
# Create sample CSV file
mkdir -p workspace/data

cat > workspace/data/sales.csv << 'EOF'
date,product,quantity,price
2024-01-15,Widget A,100,19.99
2024-01-15,Widget B,50,29.99
2024-01-16,Widget A,75,19.99
2024-01-16,Widget C,200,9.99
2024-01-17,Widget B,125,29.99
EOF

# Create sample JSON file
cat > workspace/data/users.json << 'EOF'
{
  "users": [
    {"id": 1, "name": "Alice", "age": 30, "city": "NYC"},
    {"id": 2, "name": "Bob", "age": 25, "city": "SF"},
    {"id": 3, "name": "Carol", "age": 35, "city": "NYC"}
  ],
  "total": 3
}
EOF
```

### Run Analysis

```bash
# Copy commands
cp examples/data-processing/commands.json commands.json
docker build -t cli-agent:latest .

# Process data
./run-agent.sh "Analyze the sales data and summarize total quantity by product"
```

## Example Tasks

### CSV Analysis
```bash
./run-agent.sh "How many rows are in the sales.csv file?"
./run-agent.sh "Show me the first 5 rows of sales.csv"
./run-agent.sh "Extract the product column from sales.csv"
./run-agent.sh "What products were sold?"
```

### JSON Analysis
```bash
./run-agent.sh "Read the users.json file and show me all users"
./run-agent.sh "How many users are from NYC?"
./run-agent.sh "List all the keys in users.json"
./run-agent.sh "Show me just the names of all users"
```

### Data Aggregation
```bash
./run-agent.sh "Calculate total revenue from sales.csv"
./run-agent.sh "Which product had the highest quantity sold?"
./run-agent.sh "Group sales by date and show totals"
```

### API Integration
```bash
./run-agent.sh "Fetch user data from https://api.example.com/users and count how many there are"
./run-agent.sh "Get the latest data from the API and compare with local users.json"
```

## Sample Output

```
🎯 Goal: Analyze the sales data and summarize by product

--- Iteration 1 ---
🔧 Executing: find_csv_files({'path': '/workspace/data'})
📋 Result: /workspace/data/sales.csv

--- Iteration 2 ---
🔧 Executing: csv_head({'file': '/workspace/data/sales.csv', 'lines': '6'})
📋 Result:
date,product,quantity,price
2024-01-15,Widget A,100,19.99
2024-01-15,Widget B,50,29.99
2024-01-16,Widget A,75,19.99
2024-01-16,Widget C,200,9.99
2024-01-17,Widget B,125,29.99

--- Iteration 3 ---
🔧 Executing: csv_extract_column({'file': '/workspace/data/sales.csv', 'column': '2'})
📋 Result:
product
Widget A
Widget B
Widget A
Widget C
Widget B

✅ Final result:
Sales Data Summary:

**Products Sold:**
- Widget A: 175 units (100 + 75)
- Widget B: 175 units (50 + 125)
- Widget C: 200 units

**Total Units Sold:** 550

**Date Range:** 2024-01-15 to 2024-01-17

**Top Seller:** Widget C (200 units)

**Revenue Estimate:**
- Widget A: $3,498.25 (175 × $19.99)
- Widget B: $5,248.25 (175 × $29.99)
- Widget C: $1,998.00 (200 × $9.99)
- **Total Revenue:** $10,744.50
```

## Advanced Use Cases

### Data Transformation

```bash
# Convert CSV to specific format
./run-agent.sh "Extract unique products from sales.csv and create a list"
```

### Data Validation

```bash
# Check data quality
./run-agent.sh "Check if all required columns exist in the CSV"
./run-agent.sh "Validate the JSON file structure"
```

### Cross-File Analysis

```bash
# Compare multiple files
./run-agent.sh "Compare sales.csv with inventory.json and identify discrepancies"
```

## Customization

### Add Advanced CSV Processing

```json
{
  "name": "csv_unique_values",
  "description": "Get unique values in column",
  "command": "cut -d',' -f{column} {file} | sort -u",
  "parameters": {...}
}
```

### Add Statistical Analysis

```json
{
  "name": "csv_sum_column",
  "description": "Sum values in numeric column",
  "command": "awk -F',' '{sum+=$column} END {print sum}' {file}",
  "parameters": {...}
}
```

### Add Data Export

```json
{
  "name": "json_to_csv",
  "description": "Convert JSON to CSV",
  "command": "cat {file} | jq -r '.[] | [.field1, .field2] | @csv'",
  "parameters": {...}
}
```

## Tips

1. **Inspect first**: Always look at the first few rows before processing
2. **Check structure**: For JSON, list keys first to understand structure
3. **Use jq for JSON**: Learn basic jq syntax for powerful queries
4. **Column numbers**: CSV columns are 1-indexed (first column is 1)
5. **Combine tools**: Use multiple queries to build complete analysis

## Common jq Queries

```bash
# Get array length
'.users | length'

# Filter by condition
'.users[] | select(.age > 30)'

# Get specific field from all items
'.users[].name'

# Group and count
'group_by(.city) | map({city: .[0].city, count: length})'
```

## Related Examples

- See `examples/log-analysis/` for text-based log processing
- See `examples/analyze-codebase/` for structured code analysis
