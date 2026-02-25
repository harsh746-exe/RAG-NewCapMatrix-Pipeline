#!/usr/bin/env python3
"""
PDF/DOCX to TXT Converter for RAG Pipeline
Converts all PDF and DOCX documents to TXT files for more reliable text processing.
"""

import os
import re
import sys
import PyPDF2
import fitz  # PyMuPDF for better text extraction
from typing import List, Dict, Any
from pathlib import Path
import logging

# Ensure src/ is on sys.path when running as a script
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_ROOT = SCRIPT_DIR.parent  # points to src/
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from docx import Document as DocxDocument
from config.settings import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToTXTConverter:
    """Converts PDF (and DOCX) files to TXT files with improved text extraction."""
    
    def __init__(self, pdf_dir: str = None, txt_dir: str = None):
        """
        pdf_dir: directory containing source PDFs/DOCX (defaults to Config.PP_SOURCE_DIR,
                 typically '02_Detailed Project Descriptions')
        txt_dir: directory where converted TXT files will be written
        """
        self.pdf_dir = Path(pdf_dir) if pdf_dir is not None else Path(Config.PP_SOURCE_DIR)
        self.txt_dir = Path(txt_dir) if txt_dir is not None else Path("documents_txt")
        self.conversion_log = []
        
        # Create txt directory if it doesn't exist
        self.txt_dir.mkdir(exist_ok=True)
    
    def extract_text_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF (fitz) for better results."""
        try:
            doc = fitz.open(pdf_path)
            text_content = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text_content += page_text + "\n"
            
            doc.close()
            
            # Clean the text
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            return text_content
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed for {pdf_path}: {e}")
            return ""
    
    def extract_text_with_pypdf2(self, pdf_path: Path) -> str:
        """Fallback text extraction using PyPDF2."""
        try:
            text_content = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ""
                    text_content += page_text + " "
            
            # Clean the text
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            return text_content
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {pdf_path}: {e}")
            return ""
    
    def convert_pdf_to_txt(self, pdf_path: Path) -> Dict[str, Any]:
        """Convert a single PDF file to TXT."""
        txt_path = self.txt_dir / f"{pdf_path.stem}.txt"
        
        # Try PyMuPDF first (better extraction)
        text_content = self.extract_text_with_pymupdf(pdf_path)
        
        # Fallback to PyPDF2 if PyMuPDF fails
        if not text_content:
            logger.warning(f"PyMuPDF failed for {pdf_path}, trying PyPDF2...")
            text_content = self.extract_text_with_pypdf2(pdf_path)
        
        if not text_content:
            logger.error(f"Failed to extract text from {pdf_path}")
            return {
                'pdf_path': str(pdf_path),
                'txt_path': str(txt_path),
                'success': False,
                'error': 'No text content extracted',
                'text_length': 0
            }
        
        # Write text to file
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Add metadata header
            metadata_header = f"""# Converted from: {pdf_path.name}
# Original PDF: {pdf_path}
# Conversion Date: {Path().cwd()}
# Text Length: {len(text_content)} characters

"""
            
            # Rewrite with metadata
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(metadata_header + text_content)
            
            logger.info(f"Successfully converted {pdf_path.name} -> {txt_path.name} ({len(text_content)} chars)")
            
            return {
                'pdf_path': str(pdf_path),
                'txt_path': str(txt_path),
                'success': True,
                'text_length': len(text_content),
                'extraction_method': 'PyMuPDF' if text_content else 'PyPDF2'
            }
            
        except Exception as e:
            logger.error(f"Failed to write TXT file {txt_path}: {e}")
            return {
                'pdf_path': str(pdf_path),
                'txt_path': str(txt_path),
                'success': False,
                'error': str(e),
                'text_length': 0
            }

    def convert_docx_to_txt(self, docx_path: Path) -> Dict[str, Any]:
        """Convert a single DOCX file to TXT."""
        txt_path = self.txt_dir / f"{docx_path.stem}.txt"

        try:
            doc = DocxDocument(docx_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text_content = "\n".join(paragraphs)

            # Clean the text
            text_content = re.sub(r"\s+", " ", text_content).strip()

            if not text_content:
                logger.error(f"No text extracted from DOCX {docx_path}")
                return {
                    "docx_path": str(docx_path),
                    "txt_path": str(txt_path),
                    "success": False,
                    "error": "No text content extracted",
                    "text_length": 0,
                }

            # Write text to file with metadata header
            metadata_header = f"""# Converted from: {docx_path.name}
# Original DOCX: {docx_path}
# Conversion Date: {Path().cwd()}
# Text Length: {len(text_content)} characters

"""
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(metadata_header + text_content)

            logger.info(f"Successfully converted {docx_path.name} -> {txt_path.name} ({len(text_content)} chars)")

            return {
                "docx_path": str(docx_path),
                "txt_path": str(txt_path),
                "success": True,
                "text_length": len(text_content),
                "extraction_method": "python-docx",
            }

        except Exception as e:
            logger.error(f"Failed to convert DOCX file {docx_path}: {e}")
            return {
                "docx_path": str(docx_path),
                "txt_path": str(txt_path),
                "success": False,
                "error": str(e),
                "text_length": 0,
            }
    
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files in the documents directory (recursively)."""
        pdf_files: List[Path] = []
        if self.pdf_dir.exists():
            for pdf_file in self.pdf_dir.rglob("*.pdf"):
                pdf_files.append(pdf_file)
        return sorted(pdf_files)

    def get_docx_files(self) -> List[Path]:
        """Get all DOCX files in the documents directory (recursively)."""
        docx_files: List[Path] = []
        if self.pdf_dir.exists():
            for docx_file in self.pdf_dir.rglob("*.docx"):
                docx_files.append(docx_file)
        return sorted(docx_files)
    
    def convert_all_pdfs(self) -> Dict[str, Any]:
        """Convert all PDF and DOCX files to TXT files."""
        pdf_files = self.get_pdf_files()
        docx_files = self.get_docx_files()

        if not pdf_files and not docx_files:
            logger.warning(f"No PDF or DOCX files found in {self.pdf_dir}")
            return {"success": False, "error": "No PDF or DOCX files found"}

        logger.info(f"Found {len(pdf_files)} PDF files and {len(docx_files)} DOCX files to convert")

        results = {
            "total_files": len(pdf_files) + len(docx_files),
            "successful_conversions": 0,
            "failed_conversions": 0,
            "conversions": [],
        }

        for pdf_file in pdf_files:
            logger.info(f"Converting PDF: {pdf_file.name}")
            result = self.convert_pdf_to_txt(pdf_file)
            results["conversions"].append(result)

            if result["success"]:
                results["successful_conversions"] += 1
            else:
                results["failed_conversions"] += 1

        for docx_file in docx_files:
            logger.info(f"Converting DOCX: {docx_file.name}")
            result = self.convert_docx_to_txt(docx_file)
            results["conversions"].append(result)

            if result["success"]:
                results["successful_conversions"] += 1
            else:
                results["failed_conversions"] += 1

        # Save conversion log
        self.save_conversion_log(results)

        logger.info(
            f"Conversion complete: {results['successful_conversions']} successful, {results['failed_conversions']} failed"
        )
        return results
    
    def save_conversion_log(self, results: Dict[str, Any]):
        """Save conversion results to a log file."""
        log_path = self.txt_dir / "conversion_log.json"
        
        import json
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Conversion log saved to {log_path}")
    
    def verify_conversion(self) -> Dict[str, Any]:
        """Verify that all PDFs and DOCX files have corresponding TXT files."""
        pdf_files = self.get_pdf_files()
        docx_files = self.get_docx_files()
        txt_files = list(self.txt_dir.glob("*.txt"))

        missing_txt = []
        for pdf_file in pdf_files:
            txt_file = self.txt_dir / f"{pdf_file.stem}.txt"
            if not txt_file.exists():
                missing_txt.append(pdf_file.name)

        for docx_file in docx_files:
            txt_file = self.txt_dir / f"{docx_file.stem}.txt"
            if not txt_file.exists():
                missing_txt.append(docx_file.name)

        total_sources = len(pdf_files) + len(docx_files)
        verification = {
            "total_sources": total_sources,
            "total_txts": len(txt_files),
            "missing_txts": missing_txt,
            "all_converted": len(missing_txt) == 0,
        }

        logger.info(
            f"Verification: {verification['total_sources']} source files, {verification['total_txts']} TXTs"
        )
        if missing_txt:
            logger.warning(f"Missing TXT files: {missing_txt}")
        else:
            logger.info("All PDFs and DOCX files have corresponding TXT files")

        return verification

def main():
    """Main conversion function."""
    print("🔄 PDF/DOCX to TXT Converter")
    print("=" * 40)
    
    converter = PDFToTXTConverter()
    
    # Convert all PDFs
    print("📄 Converting PDF files to TXT...")
    results = converter.convert_all_pdfs()
    
    # Verify conversion
    print("✅ Verifying conversion...")
    verification = converter.verify_conversion()
    
    # Print summary
    print("\n📋 CONVERSION SUMMARY:")
    print("=" * 30)
    print(f"Total PDFs: {results['total_files']}")
    print(f"Successful: {results['successful_conversions']}")
    print(f"Failed: {results['failed_conversions']}")
    print(f"All converted: {verification['all_converted']}")
    
    if verification['missing_txts']:
        print(f"Missing TXT files: {verification['missing_txts']}")
    
    print(f"\n📁 TXT files saved to: {converter.txt_dir}")
    print(f"📋 Conversion log: {converter.txt_dir}/conversion_log.json")

if __name__ == "__main__":
    main() 