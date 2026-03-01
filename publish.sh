#!/bin/bash

# Local PyPI Publishing Script for Local Agent Toolkit
# This script helps you build and publish your package to PyPI

set -e

echo "🚀 Local Agent Toolkit - PyPI Publishing Script"
echo "================================================"

if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: You're not in a virtual environment."
    echo "   It's recommended to use a virtual environment."
    echo "   Create one with: python -m venv .venv && source .venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Installing build dependencies..."
pip install --upgrade pip build twine

echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

CURRENT_VERSION=$(grep -oP "version=\"\K[^\"]+" setup.py)
echo "📋 Current version: $CURRENT_VERSION"

echo "🔨 Building the package..."
python -m build

echo "🔍 Checking the package..."
twine check dist/*

echo ""
echo "✅ Package built successfully!"
echo "📁 Distribution files created in dist/:"
ls -la dist/

echo ""
echo "🚀 Ready to publish! Choose an option:"
echo "1. Test PyPI (recommended for testing)"
echo "2. Real PyPI (production)"
echo "3. Exit without publishing"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "📤 Publishing to Test PyPI..."
        echo "ℹ️  You'll need a Test PyPI account and API token"
        echo "   Sign up at: https://test.pypi.org/"
        twine upload --repository testpypi dist/*
        echo ""
        echo "✅ Published to Test PyPI!"
        echo "🔗 View at: https://test.pypi.org/project/local-agent-toolkit/"
        echo "📋 Test installation: pip install -i https://test.pypi.org/simple/ local-agent-toolkit"
        ;;
    2)
        echo "📤 Publishing to Real PyPI..."
        echo "⚠️  This will publish to the real PyPI - make sure you're ready!"
        echo "ℹ️  You'll need a PyPI account and API token"
        echo "   Sign up at: https://pypi.org/"
        echo ""
        read -p "Are you sure you want to publish to real PyPI? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            twine upload dist/*
            echo ""
            echo "🎉 Published to PyPI!"
            echo "🔗 View at: https://pypi.org/project/local-agent-toolkit/"
            echo "📋 Install with: pip install local-agent-toolkit"
        else
            echo "❌ Publishing cancelled."
        fi
        ;;
    3)
        echo "👋 Exiting without publishing."
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎯 Next Steps:"
echo "1. Update version in setup.py and pyproject.toml for next release"
echo "2. Tag your release: git tag v0.1.1 && git push origin v0.1.1"
echo "3. Create a GitHub release for automatic publishing"
echo ""
echo "📚 Documentation:"
echo "- PyPI: https://packaging.python.org/"
echo "- Twine: https://twine.readthedocs.io/"
