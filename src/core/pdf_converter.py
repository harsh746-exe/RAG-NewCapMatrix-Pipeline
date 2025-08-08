#!/usr/bin/env python3
"""
PDF to TXT Converter for RAG Pipeline
Converts all PDF documents to TXT files for more reliable text processing.
"""

import os
import re
import PyPDF2
import fitz  # PyMuPDF for better text extraction
from typing import List, Dict, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToTXTConverter:
    """Converts PDF files to TXT files with improved text extraction."""
    
    def __init__(self, pdf_dir: str = "documents", txt_dir: str = "documents_txt"):
        self.pdf_dir = Path(pdf_dir)
        self.txt_dir = Path(txt_dir)
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
    
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files in the documents directory."""
        pdf_files = []
        if self.pdf_dir.exists():
            for pdf_file in self.pdf_dir.glob("*.pdf"):
                pdf_files.append(pdf_file)
        return sorted(pdf_files)
    
    def convert_all_pdfs(self) -> Dict[str, Any]:
        """Convert all PDF files to TXT files."""
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.pdf_dir}")
            return {'success': False, 'error': 'No PDF files found'}
        
        logger.info(f"Found {len(pdf_files)} PDF files to convert")
        
        results = {
            'total_files': len(pdf_files),
            'successful_conversions': 0,
            'failed_conversions': 0,
            'conversions': []
        }
        
        for pdf_file in pdf_files:
            logger.info(f"Converting: {pdf_file.name}")
            result = self.convert_pdf_to_txt(pdf_file)
            results['conversions'].append(result)
            
            if result['success']:
                results['successful_conversions'] += 1
            else:
                results['failed_conversions'] += 1
        
        # Save conversion log
        self.save_conversion_log(results)
        
        logger.info(f"Conversion complete: {results['successful_conversions']} successful, {results['failed_conversions']} failed")
        return results
    
    def save_conversion_log(self, results: Dict[str, Any]):
        """Save conversion results to a log file."""
        log_path = self.txt_dir / "conversion_log.json"
        
        import json
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Conversion log saved to {log_path}")
    
    def verify_conversion(self) -> Dict[str, Any]:
        """Verify that all PDFs have corresponding TXT files."""
        pdf_files = self.get_pdf_files()
        txt_files = list(self.txt_dir.glob("*.txt"))
        
        missing_txt = []
        for pdf_file in pdf_files:
            txt_file = self.txt_dir / f"{pdf_file.stem}.txt"
            if not txt_file.exists():
                missing_txt.append(pdf_file.name)
        
        verification = {
            'total_pdfs': len(pdf_files),
            'total_txts': len(txt_files),
            'missing_txts': missing_txt,
            'all_converted': len(missing_txt) == 0
        }
        
        logger.info(f"Verification: {verification['total_pdfs']} PDFs, {verification['total_txts']} TXTs")
        if missing_txt:
            logger.warning(f"Missing TXT files: {missing_txt}")
        else:
            logger.info("All PDFs have corresponding TXT files")
        
        return verification

def main():
    """Main conversion function."""
    print("🔄 PDF to TXT Converter")
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