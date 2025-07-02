#!/usr/bin/env python3
"""
Quick fix script to resolve import issues with LangChain packages.
"""

import subprocess
import sys

def fix_langchain_imports():
    """Fix LangChain import issues by installing the correct packages."""
    print("🔧 Fixing LangChain import issues...")
    
    # Uninstall potentially conflicting packages
    packages_to_remove = [
        "langchain-openai",
        "langchain-community", 
        "langchain-text-splitters"
    ]
    
    for package in packages_to_remove:
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package], 
                         capture_output=True, check=False)
            print(f"✅ Removed {package}")
        except:
            pass
    
    # Install the correct versions
    packages_to_install = [
        "langchain-openai>=0.1.0",
        "langchain-community>=0.0.20", 
        "langchain-text-splitters>=0.0.1"
    ]
    
    for package in packages_to_install:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         capture_output=True, check=True)
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def test_import():
    """Test if the import now works."""
    print("\n🧪 Testing import...")
    try:
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        print("✅ langchain_openai import successful!")
        return True
    except ImportError as e:
        print(f"❌ Import still failing: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LangChain Import Fix Script")
    print("="*40)
    
    if fix_langchain_imports():
        if test_import():
            print("\n🎉 Import issues resolved!")
            print("You can now run: python main_rag.py --mode test")
        else:
            print("\n❌ Import still failing. Try running: python install_dependencies.py")
    else:
        print("\n❌ Failed to fix imports. Try running: python install_dependencies.py") 