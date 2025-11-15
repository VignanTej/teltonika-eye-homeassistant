#!/bin/bash

# Teltonika EYE Scanner Installation Script
# This script sets up the Python environment and installs dependencies

set -e

echo "🔧 Setting up Teltonika EYE Scanner..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
    pip install -r requirements.txt
else
    echo "📦 Creating virtual environment..."
    
    # Try to create virtual environment
    if python3 -m venv venv 2>/dev/null; then
        echo "✅ Virtual environment created successfully"
        
        # Activate virtual environment
        source venv/bin/activate
        echo "✅ Virtual environment activated"
        
        # Upgrade pip
        pip install --upgrade pip
        
        # Install dependencies
        echo "📥 Installing dependencies..."
        pip install -r requirements.txt
        
        echo "✅ Dependencies installed successfully"
        echo ""
        echo "🎉 Installation complete!"
        echo ""
        echo "To use the scanner:"
        echo "  1. Activate the virtual environment: source venv/bin/activate"
        echo "  2. Run the scanner: python teltonika_eye_scanner.py"
        echo "  3. Or test the parser: python test_parser_standalone.py"
        echo ""
        echo "For help: python teltonika_eye_scanner.py --help"
        
    else
        echo "❌ Failed to create virtual environment."
        echo "You may need to install python3-venv:"
        echo "  sudo apt install python3-venv  # On Ubuntu/Debian"
        echo "  sudo yum install python3-venv  # On CentOS/RHEL"
        echo ""
        echo "Or install dependencies system-wide (not recommended):"
        echo "  pip3 install --user -r requirements.txt"
        exit 1
    fi
fi

echo ""
echo "📋 System Requirements Check:"

# Check for Bluetooth
if command -v bluetoothctl &> /dev/null; then
    echo "✅ Bluetooth tools found"
else
    echo "⚠️  Bluetooth tools not found. You may need to install bluez:"
    echo "   sudo apt install bluez  # On Ubuntu/Debian"
fi

# Check permissions (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if groups $USER | grep -q bluetooth; then
        echo "✅ User is in bluetooth group"
    else
        echo "⚠️  User not in bluetooth group. You may need to add yourself:"
        echo "   sudo usermod -a -G bluetooth $USER"
        echo "   Then log out and log back in."
    fi
fi

echo ""
echo "🚀 Ready to scan for Teltonika EYE sensors!"