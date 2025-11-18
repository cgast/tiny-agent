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

# Set up Python virtual environment
if [ ! -d .venv ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "✅ Dependencies installed"
    echo ""
else
    echo "⚠️  Virtual environment not found, skipping dependency installation"
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

# Make agent script executable
chmod +x agent.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API key"
echo "  2. Run: ./agent.sh 'List all files in workspace'"
echo ""
echo "Example tasks:"
echo "  ./agent.sh 'Find all Python files'"
echo "  ./agent.sh 'Count lines of code'"
echo "  ./agent.sh --mode sandbox 'Search for TODO comments'"
echo "  ./agent.sh -m sandbox -w ./myproject 'Analyze this code'"
