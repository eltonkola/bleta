#!/usr/bin/env python3
"""
Bleta - Setup Script
Helps users set up the Albanian news archive project locally.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        print("❌ Error: Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required Python packages."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    print("\n🧪 Testing imports...")
    modules = [
        "feedparser",
        "requests", 
        "google.generativeai",
        "bs4",
        "lxml"
    ]
    
    failed_imports = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All imports successful")
    return True

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("\n🔑 Creating .env file...")
    env_content = """# Bleta - Albanian News Archive
# Add your Google Gemini API key here
GOOGLE_API_KEY=your_api_key_here

# Get your API key from: https://makersuite.google.com/app/apikey
"""
    
    try:
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
        print("📝 Please edit .env and add your Google API key")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    directories = [
        "data",
        "data/archive", 
        "public",
        "webapp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {directory}/")

def main():
    """Main setup function."""
    print("🐝 Welcome to Bleta - Albanian News Archive Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n💡 Try running: pip install --upgrade pip")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("\n💡 Try reinstalling dependencies or check your Python environment")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your Google Gemini API key")
    print("2. Run: python scripts/update_feed.py")
    print("3. Open webapp/index.html in your browser")
    print("\n🌐 For GitHub deployment:")
    print("1. Push to GitHub")
    print("2. Add GOOGLE_API_KEY secret in repository settings")
    print("3. Enable GitHub Pages")
    print("4. Run the workflow manually")

if __name__ == "__main__":
    main()
