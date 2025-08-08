#!/usr/bin/env python3
"""
Fix Encoding Issues in Documents

This script fixes encoding issues in the new documents by converting them
to proper UTF-8 format.
"""

import os
import sys
from pathlib import Path

def fix_encoding(file_path):
    """Fix encoding issues in a file."""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                # Write back with UTF-8 encoding
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Fixed {file_path} using {encoding}")
                return True
                
            except UnicodeDecodeError:
                continue
        
        print(f"❌ Could not fix {file_path}")
        return False
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix encoding for all documents."""
    print("🔧 Fixing encoding issues in documents...")
    
    documents_dir = Path("data/documents_txt")
    
    if not documents_dir.exists():
        print("❌ Documents directory not found")
        return
    
    fixed_count = 0
    total_count = 0
    
    for file_path in documents_dir.glob("*.txt"):
        total_count += 1
        if fix_encoding(file_path):
            fixed_count += 1
    
    print(f"\n📊 Encoding Fix Summary:")
    print(f"- Total files: {total_count}")
    print(f"- Fixed: {fixed_count}")
    print(f"- Failed: {total_count - fixed_count}")

if __name__ == "__main__":
    main() 