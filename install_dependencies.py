#!/usr/bin/env python3
"""
Installation script for RAG Capability Matrix Analysis System.
This script helps set up the environment and install all required dependencies.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install all required dependencies."""
    print("🚀 Installing RAG Capability Matrix Analysis Dependencies")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Upgrade pip
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install core dependencies
    dependencies = [
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "scikit-learn>=1.0.0",
        "nltk>=3.6.0",
        "sentence-transformers>=2.2.0",
        "spacy>=3.4.0",
        "tqdm>=4.62.0",
        "PyPDF2>=2.0.0",
        "PyMuPDF>=1.19.0",
        "openpyxl>=3.0.0",
        "python-dotenv>=1.0.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.11.0",
        "pydantic>=2.0.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"{sys.executable} -m pip install '{dep}'", f"Installing {dep.split('>=')[0]}"):
            return False
    
    # Install LangChain dependencies (these are more complex)
    langchain_deps = [
        "langchain>=0.1.0",
        "langchain-openai>=0.1.0",
        "langchain-community>=0.0.20",
        "langchain-text-splitters>=0.0.1",
        "chromadb>=0.4.0",
        "tiktoken>=0.5.0",
        "openai>=1.0.0"
    ]
    
    print("\n📦 Installing LangChain and AI dependencies...")
    for dep in langchain_deps:
        if not run_command(f"{sys.executable} -m pip install '{dep}'", f"Installing {dep.split('>=')[0]}"):
            return False
    
    # Optional: Install Ollama support
    print("\n🤖 Installing optional Ollama support...")
    run_command(f"{sys.executable} -m pip install 'ollama>=0.1.0'", "Installing Ollama support")
    
    return True

def create_env_file():
    """Create a .env file template if it doesn't exist."""
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ .env file already exists")
        return True
    
    print("📝 Creating .env file template...")
    env_content = """# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Override default model
# MODEL_NAME=gpt-4

# Optional: Override default temperature
# TEMPERATURE=0.1

# LLM Provider Configuration
# Choose your LLM provider: "openai" or "ollama"
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_MODEL_NAME=gpt-3.5-turbo

# Ollama Configuration (if using local LLM)
OLLAMA_MODEL_NAME=llama3
OLLAMA_BASE_URL=http://localhost:11434
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        print("   Please edit the .env file and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_imports():
    """Test if all imports work correctly."""
    print("\n🧪 Testing imports...")
    
    test_imports = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("langchain_openai", "langchain_openai"),
        ("langchain_community", "langchain_community"),
        ("langchain_text_splitters", "langchain_text_splitters"),
        ("chromadb", "chromadb"),
        ("openai", "openai"),
        ("pydantic", "pydantic")
    ]
    
    failed_imports = []
    
    for module_name, import_name in test_imports:
        try:
            __import__(import_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n❌ Failed imports: {', '.join(failed_imports)}")
        return False
    
    print("✅ All imports successful!")
    return True

def main():
    """Main installation function."""
    print("🚀 RAG Capability Matrix Analysis - Installation Script")
    print("="*60)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed. Please check the errors above.")
        return False
    
    # Create .env file
    create_env_file()
    
    # Test imports
    if not test_imports():
        print("\n❌ Some imports failed. Please check the errors above.")
        return False
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Edit the .env file and add your OpenAI API key")
    print("2. Add your PDF documents to the 'documents/' directory")
    print("3. Create your requirements Excel file in the 'outgoing/' directory")
    print("4. Run: python main_rag.py --mode test")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 