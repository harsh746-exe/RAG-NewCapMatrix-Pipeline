#!/usr/bin/env python3
"""
Cleanup script for RAG NewCap Matrix Script

This script cleans up output directories and temporary files to prepare for a fresh run.
"""

import os
import shutil
import argparse
import sys
from pathlib import Path

def clean_directory(directory_path, description="directory"):
    """Clean a directory by removing all contents but keeping the directory itself."""
    if os.path.exists(directory_path):
        try:
            # Remove all contents
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            print(f"✅ Cleaned {description}: {directory_path}")
            return True
        except Exception as e:
            print(f"❌ Error cleaning {description} {directory_path}: {e}")
            return False
    else:
        print(f"ℹ️  {description.capitalize()} doesn't exist: {directory_path}")
        return True

def remove_file_pattern(directory_path, pattern, description="files"):
    """Remove files matching a pattern in a directory."""
    if not os.path.exists(directory_path):
        return True
    
    try:
        count = 0
        for file in Path(directory_path).glob(pattern):
            if file.is_file():
                file.unlink()
                count += 1
        
        if count > 0:
            print(f"✅ Removed {count} {description} from {directory_path}")
        else:
            print(f"ℹ️  No {description} found in {directory_path}")
        return True
    except Exception as e:
        print(f"❌ Error removing {description} from {directory_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Clean up RAG pipeline outputs and temporary files")
    parser.add_argument("--all", action="store_true", help="Clean all outputs and temporary files")
    parser.add_argument("--outputs", action="store_true", help="Clean only output files")
    parser.add_argument("--vector-store", action="store_true", help="Clean vector store (will require re-indexing)")
    parser.add_argument("--processed", action="store_true", help="Clean processed/temporary files")
    parser.add_argument("--logs", action="store_true", help="Clean log files")
    parser.add_argument("--cache", action="store_true", help="Clean Python cache files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without actually doing it")
    
    args = parser.parse_args()
    
    # If no specific options are given, default to cleaning outputs
    if not any([args.all, args.outputs, args.vector_store, args.processed, args.logs, args.cache]):
        args.outputs = True
    
    print("🧹 RAG Pipeline Cleanup Script")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be actually deleted")
        print()
    
    # Define paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(project_root, "data")
    outputs_dir = os.path.join(data_dir, "outputs")
    processed_dir = os.path.join(data_dir, "processed")
    vector_store_dir = os.path.join(data_dir, "vector_store")
    logs_dir = os.path.join(project_root, "logs")
    
    success = True
    
    if args.dry_run:
        print("Would clean the following:")
        if args.all or args.outputs:
            print(f"  - Output files in: {outputs_dir}")
        if args.all or args.processed:
            print(f"  - Processed files in: {processed_dir}")
        if args.all or args.vector_store:
            print(f"  - Vector store in: {vector_store_dir}")
        if args.all or args.logs:
            print(f"  - Log files in: {logs_dir}")
        if args.all or args.cache:
            print(f"  - Python cache files (__pycache__, *.pyc)")
        return
    
    # Clean outputs
    if args.all or args.outputs:
        print("\n📊 Cleaning output files...")
        success &= clean_directory(outputs_dir, "outputs directory")
        
        # Also clean any output files that might be in the root
        success &= remove_file_pattern(project_root, "*.xlsx", "Excel files")
        success &= remove_file_pattern(project_root, "*.json", "JSON files")
        success &= remove_file_pattern(project_root, "*REPORT*.txt", "report files")
    
    # Clean processed files
    if args.all or args.processed:
        print("\n🔄 Cleaning processed/temporary files...")
        success &= clean_directory(processed_dir, "processed directory")
    
    # Clean vector store
    if args.all or args.vector_store:
        print("\n🗂️  Cleaning vector store...")
        print("⚠️  Warning: This will require re-indexing all documents on next run!")
        success &= clean_directory(vector_store_dir, "vector store directory")
    
    # Clean logs
    if args.all or args.logs:
        print("\n📝 Cleaning log files...")
        success &= clean_directory(logs_dir, "logs directory")
        success &= remove_file_pattern(project_root, "*.log", "log files")
    
    # Clean Python cache
    if args.all or args.cache:
        print("\n🐍 Cleaning Python cache files...")
        
        # Remove __pycache__ directories
        for root, dirs, files in os.walk(project_root):
            if "__pycache__" in dirs:
                cache_dir = os.path.join(root, "__pycache__")
                try:
                    shutil.rmtree(cache_dir)
                    print(f"✅ Removed cache directory: {cache_dir}")
                except Exception as e:
                    print(f"❌ Error removing cache directory {cache_dir}: {e}")
                    success = False
        
        # Remove .pyc files
        success &= remove_file_pattern(project_root, "**/*.pyc", ".pyc files")
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Cleanup completed successfully!")
        print("\n💡 Next steps:")
        print("   - Run your RAG analysis with: python main.py --mode test")
        print("   - Or extract new requirements with: python src/core/extract_sow_text.py <pdf_file>")
    else:
        print("⚠️  Cleanup completed with some errors. Check the messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()