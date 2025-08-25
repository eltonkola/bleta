#!/usr/bin/env python3
"""
Bleta - Local Runner
Simple script to run the Albanian news archive locally.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required modules are available."""
    required_modules = [
        "feedparser",
        "requests",
        "google.generativeai",
        "bs4"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing modules: {', '.join(missing_modules)}")
        print("💡 Run: python setup.py")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has API key."""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# Bleta - Albanian News Archive
# Add your Google Gemini API key here
GOOGLE_API_KEY=your_api_key_here

# Get your API key from: https://makersuite.google.com/app/apikey
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
        print("⚠️  Please edit .env and add your Google API key")
        return False
    
    # Check if API key is set
    with open(env_file, "r") as f:
        content = f.read()
        if "your_api_key_here" in content:
            print("⚠️  Please edit .env and add your Google API key")
            return False
    
    return True

def ensure_directories():
    """Ensure required directories exist."""
    directories = ["data", "data/archive", "public", "webapp"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main function to run Bleta locally."""
    print("🐝 Bleta - Albanian News Archive")
    print("=" * 40)
    
    # Ensure we're in the right directory
    if not Path("config.py").exists():
        print("❌ Error: config.py not found")
        print("💡 Make sure you're in the Bleta project directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Ensure directories exist
    ensure_directories()
    
    # Check environment
    if not check_env_file():
        print("\n📋 Next steps:")
        print("1. Edit .env file and add your Google API key")
        print("2. Run this script again")
        sys.exit(1)
    
    # Run the news aggregator
    print("\n🚀 Running Bleta news aggregator...")
    try:
        subprocess.run([sys.executable, "scripts/update_feed.py"], check=True)
        print("✅ News aggregation completed!")
        
        print("\n📱 To view the web app:")
        print("1. Open webapp/index.html in your browser")
        print("2. Or serve it with: python -m http.server 8000")
        print("3. Then visit: http://localhost:8000/webapp/")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running news aggregator: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
