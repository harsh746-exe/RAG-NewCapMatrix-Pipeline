#!/usr/bin/env python3
"""
Main entry point for the RAG NewCap Matrix Script.

Thin wrapper around src/run_rag_analysis.py that correctly forwards CLI
arguments like --mode to the underlying script.
"""

import os
import sys
import argparse

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import run_rag_analysis as rag_module  # noqa: E402


def main() -> None:
    """Parse top-level CLI args and delegate to run_rag_analysis.main."""
    parser = argparse.ArgumentParser(
        description="RAG-based Capability Matrix Analysis Script (wrapper)"
    )
    parser.add_argument(
        "--mode",
        choices=["test", "prod"],
        help="Run mode: test (first 10 requirements) or prod (all requirements)",
    )
    # Allow passing through any future args to the underlying script if needed
    args, _ = parser.parse_known_args()

    # Forward mode into the underlying module's global MODE, if provided
    if args.mode:
        rag_module.MODE = args.mode

    # Call the real main
    rag_module.main()


if __name__ == "__main__":
    main()