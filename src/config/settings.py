"""
Configuration settings for the RAG-based Capability Matrix Analysis system.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the RAG pipeline."""
    
    # File paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
    TMP_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
    OUTGOING_DIR = os.path.join(PROJECT_ROOT, "data", "outputs")
    VECTOR_STORE_PATH = os.path.join(PROJECT_ROOT, "data", "vector_store")
    
    # Input/Output files
    EXCEL_PATH = os.path.join(OUTGOING_DIR, "requirements_matrix.xlsx")
    OUTPUT_JSON = os.path.join(OUTGOING_DIR, "rag_requirement_matches.json")
    CHECKPOINT_FILE = os.path.join(OUTGOING_DIR, "rag_checkpoint.json")
    OUTPUT_EXCEL = os.path.join(OUTGOING_DIR, "rag_requirement_analysis_results.xlsx")
    
    # RAG Pipeline Settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    TOP_K_RETRIEVAL = 5
    
    # LLM Settings
    MODEL_NAME = "gpt-3.5-turbo"
    TEMPERATURE = 0.1
    MAX_TOKENS = 2000
    
    # Processing Settings
    DEFAULT_MODE = "test"  # "test" or "prod"
    TEST_LIMIT = 10  # Number of requirements to process in test mode
    
    # API Settings - Now loaded from .env file
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # --- LLM Provider Configuration ---
    # Choose your LLM provider: "openai" or "ollama"
    LLM_PROVIDER = "openai"  # Change to "ollama" to use Ollama models

    # --- OpenAI Configuration ---
    # Used only if LLM_PROVIDER is "openai"
    OPENAI_MODEL_NAME = "gpt-3.5-turbo"

    # --- Ollama Configuration ---
    # Used only if LLM_PROVIDER is "ollama"
    # Make sure you have pulled the model you want to use, e.g., `ollama pull llama3`
    OLLAMA_MODEL_NAME = "llama3"
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate the configuration."""
        errors = []
        
        # Check if required directories exist
        if not os.path.exists(cls.DOCUMENTS_DIR):
            errors.append(f"Documents directory not found: {cls.DOCUMENTS_DIR}")
        
        if not os.path.exists(cls.OUTGOING_DIR):
            errors.append(f"Outgoing directory not found: {cls.OUTGOING_DIR}")
        
        # Check if OpenAI API key is set
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not found in .env file or environment")
        
        # Check if input Excel file exists (optional for testing)
        if not os.path.exists(cls.EXCEL_PATH):
            errors.append(f"Input Excel file not found: {cls.EXCEL_PATH} (create this file when ready to run analysis)")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_summary(cls):
        """Print a summary of the current configuration."""
        print("RAG Pipeline Configuration Summary:")
        print(f"  Documents Directory: {cls.DOCUMENTS_DIR}")
        print(f"  Vector Store Path: {cls.VECTOR_STORE_PATH}")
        print(f"  Input Excel: {cls.EXCEL_PATH}")
        print(f"  Output Excel: {cls.OUTPUT_EXCEL}")
        print(f"  Model: {cls.MODEL_NAME}")
        print(f"  Chunk Size: {cls.CHUNK_SIZE}")
        print(f"  Chunk Overlap: {cls.CHUNK_OVERLAP}")
        print(f"  Top-K Retrieval: {cls.TOP_K_RETRIEVAL}")
        print(f"  Default Mode: {cls.DEFAULT_MODE}")
        print(f"  OpenAI API Key: {'Set' if cls.OPENAI_API_KEY else 'Not Set'}")
        if cls.OPENAI_API_KEY:
            print(f"  API Key Source: {'Environment' if os.getenv('OPENAI_API_KEY') else '.env file'}")
        print()

# Create required directories
os.makedirs(Config.DOCUMENTS_DIR, exist_ok=True)
os.makedirs(Config.OUTGOING_DIR, exist_ok=True)
os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True) 