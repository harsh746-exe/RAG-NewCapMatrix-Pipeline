#!/usr/bin/env python3
"""
Main entry point for the RAG NewCap Matrix Script
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from run_rag_analysis import main

if __name__ == "__main__":
    main() 