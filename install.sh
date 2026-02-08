#!/bin/bash
# AutoNation Appraisal System - Installation Script

set -e  # Exit on error

echo "=============================================================================="
echo "  AutoNation Intelligent Appraisal System - Installation"
echo "=============================================================================="
echo ""

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found: Python $PYTHON_VERSION"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "   ✅ Python version is compatible (3.10+)"
else
    echo "   ❌ Python 3.10 or higher is required"
    exit 1
fi

echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists, removing..."
    rm -rf venv
fi

python3 -m venv venv
echo "   ✅ Virtual environment created"

echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Activated"

echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --quiet --upgrade pip
echo "   ✅ pip upgraded"

echo ""

# Install dependencies
echo "📥 Installing dependencies..."
echo "   This may take a few minutes..."
echo ""

# Install in stages to handle potential issues
echo "   [1/4] Installing core packages..."
pip install --quiet requests

echo "   [2/4] Installing Google Cloud packages..."
pip install --quiet google-cloud-aiplatform google-cloud-bigquery google-cloud-storage

echo "   [3/4] Installing ADK..."
pip install --quiet google-genai

echo "   [4/4] Installing UI and data packages..."
pip install --quiet streamlit pandas plotly python-dotenv Pillow

echo ""
echo "   ✅ All dependencies installed"

echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✅ .env file created - please edit with your settings"
    else
        echo "   ❌ .env.example not found"
    fi
else
    echo "✅ .env file exists"
fi

echo ""

# Run tests
echo "🧪 Running system tests..."
python3 test_system.py

echo ""
echo "=============================================================================="
echo "  ✅ Installation Complete!"
echo "=============================================================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure Authentication:"
echo "   gcloud auth application-default login"
echo "   gcloud config set project uppdemos"
echo ""
echo "2. Edit .env file if needed:"
echo "   nano .env"
echo ""
echo "3. Run the Streamlit demo:"
echo "   streamlit run ui/streamlit_app.py"
echo ""
echo "4. Or test individual agents:"
echo "   adk run agents/market_intelligence.py"
echo ""
echo "=============================================================================="
echo ""
