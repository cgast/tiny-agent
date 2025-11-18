#!/usr/bin/env bash
# Quick setup script for CLI Agent

echo "🚀 Setting up CLI Agent..."
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API key!"
    echo ""
fi

# Create example workspace
if [ ! -d workspace ]; then
    echo "📁 Creating example workspace..."
    mkdir -p workspace
    
    # Create some example files
    cat > workspace/example.py << 'EOF'
# Example Python file
def hello():
    print("Hello from the agent!")
    # TODO: Add more features

if __name__ == "__main__":
    hello()
EOF
    
    cat > workspace/README.md << 'EOF'
# Example Workspace

This is a test workspace for the CLI agent.

Files:
- example.py - A simple Python script
- data.txt - Some data
EOF
    
    echo "Sample data for testing" > workspace/data.txt
    echo "More sample data" > workspace/data2.txt
    
    echo "✅ Created workspace/ with example files"
    echo ""
fi

# Make run script executable
chmod +x run-agent.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API key"
echo "  2. Run: ./run-agent.sh 'List all files in workspace'"
echo ""
echo "Example tasks:"
echo "  ./run-agent.sh 'Find all Python files'"
echo "  ./run-agent.sh 'Count lines of code'"
echo "  ./run-agent.sh 'Search for TODO comments'"
echo "  ./run-agent.sh 'What files are larger than 1KB?'"
