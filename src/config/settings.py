"""
Configuration settings for the RAG-based Capability Matrix Analysis system.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file (best-effort; may be blocked in some environments)
try:
    load_dotenv()
except PermissionError:
    # Some sandboxed environments block reading dotfiles; rely on process env instead.
    pass


class Config:
    """Configuration class for the RAG pipeline."""

    # File paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DOCUMENTS_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
    TMP_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
    OUTGOING_DIR = os.path.join(PROJECT_ROOT, "data", "outputs")

    # Vector store root: use writable location if project is on read-only volume (e.g. /Volumes/T9)
    # Set VECTOR_STORE_ROOT in .env to override (e.g. /tmp/rag_vector_store)
    _vector_store_root = os.getenv("VECTOR_STORE_ROOT")
    if _vector_store_root:
        _vector_store_root = os.path.expanduser(_vector_store_root)
    else:
        _vector_store_root = os.path.join(PROJECT_ROOT, "data")
    VECTOR_STORE_PATH = os.path.join(_vector_store_root, "vector_store")

    # --- Past performance source (new structured folder) ---
    # This is the authoritative source directory for the RAG pipeline.
    PP_SOURCE_DIR = os.path.join(PROJECT_ROOT, "02_Detailed Project Descriptions")

    # Structured TXT output produced from PP_SOURCE_DIR (keeps headings/sections).
    # The RAG pipeline indexes these files (not the old flat documents_txt).
    STRUCTURED_TXT_DIR = os.path.join(PROJECT_ROOT, "data", "processed", "pp_structured_txt")

    # Dual-index vector stores (document-level + chunk-level)
    VECTOR_STORE_DOCS_PATH = os.path.join(_vector_store_root, "vector_store_docs")
    VECTOR_STORE_CHUNKS_PATH = os.path.join(_vector_store_root, "vector_store_chunks")

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
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
    TEMPERATURE = 0.1
    MAX_TOKENS = 2000

    # Processing Settings
    DEFAULT_MODE = "test"  # "test" or "prod"
    TEST_LIMIT = 10  # Number of requirements to process in test mode

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    # --- LLM Provider Configuration ---
    # Azure OpenAI is required. Set LLM_PROVIDER=azure in .env
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure")

    # --- Azure OpenAI Configuration ---
    # Get these from your Azure OpenAI resource in Azure Portal
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g., "https://your-resource.openai.azure.com"
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")  # Your deployment name
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")  # API version
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: Optional[str] = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")  # Embedding deployment name (can be same as model)

    # --- Local embeddings (optional, for vector store when using Azure/OpenAI/Gemini/Graph for LLM only) ---
    # Set USE_LOCAL_EMBEDDINGS=true to use a local sentence-transformers model instead of Azure/OpenAI embeddings.
    # Default: false (use Azure embeddings when LLM_PROVIDER=azure).
    USE_LOCAL_EMBEDDINGS: bool = os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() in ("true", "1", "yes")
    LOCAL_EMBEDDING_MODEL_NAME: str = os.getenv("LOCAL_EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")  # sentence-transformers model

    # --- Microsoft Graph Copilot Configuration ---
    # Used only if LLM_PROVIDER is "graph_copilot"
    GRAPH_TENANT_ID: Optional[str] = os.getenv("GRAPH_TENANT_ID")
    GRAPH_CLIENT_ID: Optional[str] = os.getenv("GRAPH_CLIENT_ID")
    GRAPH_CLIENT_SECRET: Optional[str] = os.getenv("GRAPH_CLIENT_SECRET")
    GRAPH_USE_DEFAULT_CREDENTIAL: bool = os.getenv("GRAPH_USE_DEFAULT_CREDENTIAL", "false").lower() == "true"

    # --- SharePoint Sync Configuration (Graph API) ---
    # Optional: set SHAREPOINT_SYNC=true to auto-sync before ingest
    SHAREPOINT_SYNC: bool = os.getenv("SHAREPOINT_SYNC", "false").lower() in ("true", "1", "yes")
    SHAREPOINT_SITE_HOST: Optional[str] = os.getenv("SHAREPOINT_SITE_HOST")
    SHAREPOINT_SITE_PATH: Optional[str] = os.getenv("SHAREPOINT_SITE_PATH")
    SHAREPOINT_FOLDER_PATH: Optional[str] = os.getenv("SHAREPOINT_FOLDER_PATH")
    SHAREPOINT_DRIVE_NAME: Optional[str] = os.getenv("SHAREPOINT_DRIVE_NAME")
    SHAREPOINT_ALLOWED_EXTS: str = os.getenv("SHAREPOINT_ALLOWED_EXTS", ".pdf,.docx")

    # --- Google Gemini Configuration ---
    # Used only if LLM_PROVIDER is "gemini"
    GEMINI_API_KEY: Optional[str] = os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")  # Options: gemini-2.0-flash, gemini-pro, etc.

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

        # Check if API key is set based on provider
        if cls.LLM_PROVIDER == "azure":
            if not cls.AZURE_OPENAI_API_KEY:
                errors.append("AZURE_OPENAI_API_KEY not found in .env file or environment")
            if not cls.AZURE_OPENAI_ENDPOINT:
                errors.append("AZURE_OPENAI_ENDPOINT not found in .env file or environment")
            if not cls.AZURE_OPENAI_DEPLOYMENT_NAME:
                errors.append("AZURE_OPENAI_DEPLOYMENT_NAME not found in .env file or environment")

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
        print(f"  PP Source Directory: {cls.PP_SOURCE_DIR}")
        print(f"  Vector Store Path: {cls.VECTOR_STORE_PATH}")
        print(f"  Input Excel: {cls.EXCEL_PATH}")
        print(f"  Output Excel: {cls.OUTPUT_EXCEL}")
        print(f"  Model: {cls.MODEL_NAME}")
        print(f"  Chunk Size: {cls.CHUNK_SIZE}")
        print(f"  Chunk Overlap: {cls.CHUNK_OVERLAP}")
        print(f"  Top-K Retrieval: {cls.TOP_K_RETRIEVAL}")
        print(f"  Default Mode: {cls.DEFAULT_MODE}")
        print(f"  LLM Provider: {cls.LLM_PROVIDER}")
        if cls.LLM_PROVIDER == "azure":
            print(f"  Azure OpenAI: {'Configured' if cls.AZURE_OPENAI_API_KEY else 'Not Set'}")
        print()


# Create required directories
os.makedirs(Config.DOCUMENTS_DIR, exist_ok=True)
os.makedirs(Config.OUTGOING_DIR, exist_ok=True)
os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)
os.makedirs(Config.STRUCTURED_TXT_DIR, exist_ok=True)
os.makedirs(Config.VECTOR_STORE_DOCS_PATH, exist_ok=True)
os.makedirs(Config.VECTOR_STORE_CHUNKS_PATH, exist_ok=True)