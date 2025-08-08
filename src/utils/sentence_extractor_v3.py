#!/usr/bin/env python3
"""
Advanced Hybrid Sentence Extractor
Combines Unstructured's layout awareness with PySBD's sentence accuracy
Battle-tested workflow for sentence-perfect PDF extraction
"""

import re
import sys
import os
import argparse
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, Counter

# PDF extraction with Unstructured
try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import Title, NarrativeText, ListItem
    from unstructured.chunking.title import is_title
except ImportError:
    print("Installing unstructured...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "unstructured[all-docs]"])
    from unstructured.partition.pdf import partition_pdf
    from unstructured.documents.elements import Title, NarrativeText, ListItem
    from unstructured.chunking.title import is_title

# Sentence segmentation with PySBD
try:
    import pysbd
except ImportError:
    print("Installing pysbd...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pysbd"])
    import pysbd

# NLP for requirement detection
try:
    import spacy
    from spacy.matcher import Matcher
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Installing NLP dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy sentence-transformers"])
    import spacy
    from spacy.matcher import Matcher
    from sentence_transformers import SentenceTransformer

# Excel handling
try:
    import openpyxl
except ImportError:
    print("Installing openpyxl...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

@dataclass
class SentenceMetadata:
    """Metadata for each extracted sentence."""
    text: str
    page_number: Optional[int] = None
    category: str = "Unknown"
    block_id: Optional[str] = None
    y_position: Optional[float] = None
    is_heading: bool = False
    is_requirement: bool = False
    detector: Optional[str] = None
    confidence: float = 0.0

def merge_lines(txt: str) -> str:
    """
    Merge wrapped lines and kill soft hyphens.
    Battle-tested line merging for PDF text.
    """
    # Normalize unicode (ﬁ → fi, smart quotes → ")
    txt = unicodedata.normalize("NFKD", txt)
    
    # Remove soft hyphen character
    txt = txt.replace("\u00ad", "")
    
    # Remove bullet points and list markers
    txt = re.sub(r'^[•\-\*]\s*', '', txt)  # Remove leading bullets
    txt = re.sub(r'\s*[•\-\*]\s*', ' ', txt)  # Remove inline bullets
    
    # Remove layout hyphens at line end: "hy-\nphen"
    txt = re.sub(r'(?<=\w)-\n(?=\w)', '', txt)
    
    # Join leftover single newlines inside a paragraph
    txt = re.sub(r'(?<!\n)\n(?!\n)', ' ', txt)
    
    # Collapse multiple spaces
    txt = re.sub(r'\s{2,}', ' ', txt)
    
    return txt.strip()

def scrub_headers_footers(elements: List) -> List:
    """
    Remove headers, footers, and TOC sections that pollute heading detection.
    """
    print("Scrubbing headers, footers, and TOC sections...")
    
    # Track text frequency across pages
    text_page = [(e.text.strip(), getattr(e.metadata, 'page_number', 0)) 
                 for e in elements if hasattr(e, 'text') and e.text.strip()]
    
    # Find common elements (appear on many pages)
    text_freq = {}
    for text, page in text_page:
        if text not in text_freq:
            text_freq[text] = set()
        text_freq[text].add(page)
    
    # Calculate frequency percentage
    total_pages = max(page for _, page in text_page) if text_page else 1
    common_threshold = 0.7  # 70% of pages
    
    common_elements = {text for text, pages in text_freq.items() 
                      if len(pages) >= common_threshold * total_pages}
    
    # Header/footer patterns
    header_footer_patterns = [
        r'^(Page\s+\d+|Attachment|DSS\s+\d+\.\d+\s+BPA|Statement\s+of\s+Work|RFQ\s+\d+)',
        r'^(Confidential|Proprietary|Draft|Final)',
        r'^\d+$',  # Just page numbers
        r'^[A-Z\s]{2,}$',  # All caps short text (likely headers)
        # Footer patterns
        r'.*Please\s+refer\s+to.*',
        r'.*For\s+more\s+information.*',
        r'.*Additional\s+information.*',
        r'.*See\s+.*\s+for\s+details.*',
        r'.*Contact\s+.*\s+for\s+.*',
        r'.*Visit\s+.*\s+website.*',
        r'.*Go\s+to\s+.*\s+for\s+.*',
        r'.*Access\s+.*\s+at\s+.*',
        r'.*Available\s+at\s+.*',
        r'.*Located\s+at\s+.*',
        r'.*Found\s+at\s+.*',
        r'.*Reference\s+.*',
        r'.*Library.*',
        r'.*Safeguards.*',
        r'.*Security\s+Library.*',
        r'.*Information\s+Security.*',
        r'.*Acceptable\s+Risk.*',
        r'.*https?://.*',  # URLs
        r'.*www\..*',      # URLs
        r'.*\.gov.*',      # Government URLs
        r'.*\.com.*',      # Commercial URLs
        r'.*\.org.*',      # Organization URLs
    ]
    
    # TOC patterns
    toc_patterns = [
        r'^\d+(\.\d+)*\s+.*?\.{2,}\s*\d+\s*$',  # 1.2.3 Title ........ 5
        r'^Table\s+of\s+Contents?$',
        r'^Contents?$',
        r'^Index$',
    ]
    
    clean_elements = []
    in_toc_section = False
    
    for element in elements:
        if not hasattr(element, 'text') or not element.text:
            continue
            
        text = element.text.strip()
        if not text:
            continue
        
        # Skip common elements (headers/footers)
        if text in common_elements:
            continue
        
        # Skip obvious header/footer patterns
        if any(re.match(pattern, text, re.I) for pattern in header_footer_patterns):
            continue
        
        # Handle TOC sections
        if any(re.match(pattern, text, re.I) for pattern in toc_patterns):
            in_toc_section = True
            continue
        
        if in_toc_section:
            # Check if we're still in TOC (dot leaders or numbered entries)
            if re.match(r'^\d+(\.\d+)*\s+.*?\.{2,}\s*\d+\s*$', text):
                continue
            elif re.match(r'^\d+(\.\d+)*\s+[A-Z]', text) and not re.search(r'\.{2,}', text):
                # This looks like a real heading, exit TOC
                in_toc_section = False
            else:
                continue
        
        clean_elements.append(element)
    
    print(f"Removed {len(elements) - len(clean_elements)} header/footer/TOC elements")
    return clean_elements

def extract_with_unstructured(pdf_path: str) -> List:
    """
    Step 1: Parse PDF with Unstructured → blocks with tags.
    """
    print(f"Extracting with Unstructured: {pdf_path}")
    
    try:
        elements = partition_pdf(
            pdf_path,
            strategy="hi_res",          # keeps line order + runs OCR on scanned content
            extract_metadata=True,      # pulls page numbers etc.
        )
        print(f"Extracted {len(elements)} elements")
        return elements
    except Exception as e:
        print(f"Error with hi_res strategy, falling back to fast: {e}")
        elements = partition_pdf(
            pdf_path,
            strategy="fast",
            extract_metadata=True,
        )
        print(f"Extracted {len(elements)} elements with fast strategy")
        return elements

def propagate_obligation_context(sentence_meta: List[SentenceMetadata]) -> List[SentenceMetadata]:
    """
    Propagate obligation context from headings to subsequent bullet points.
    Handles "shall / must / should (not)" lists and other modal verb patterns.
    """
    print("Propagating obligation context...")
    
    # Comprehensive modal patterns covering all obligation types
    obligation_patterns = [
        # Positive obligations
        r'^(.*?)\s+(?:shall|must|will|is\s+required\s+to|is\s+responsible\s+for|is\s+obligated\s+to|needs?\s+to|has?\s+to|should|may|can|could):\s*$',
        # Negative obligations (prohibitions)
        r'^(.*?)\s+(?:shall\s+not|must\s+not|will\s+not|is\s+not\s+authorized\s+to|is\s+prohibited\s+from|should\s+not|may\s+not|cannot|could\s+not):\s*$',
        # Conditional obligations
        r'^(.*?)\s+(?:will\s+ensure|shall\s+ensure|must\s+ensure|is\s+responsible\s+for\s+ensuring):\s*$'
    ]
    
    current_actor = None
    current_modal = None
    current_is_negative = False
    current_full_prefix = None
    
    for i, meta in enumerate(sentence_meta):
        sentence = meta.text.strip()
        
        # Check if this is an obligation heading
        is_obligation_heading = False
        for pattern in obligation_patterns:
            match = re.match(pattern, sentence, re.IGNORECASE)
            if match:
                current_actor = match.group(1).strip()
                # Extract the modal verb
                modal_match = re.search(r'(?:shall|must|will|is\s+required\s+to|is\s+responsible\s+for|is\s+obligated\s+to|needs?\s+to|has?\s+to|should|may|can|could|shall\s+not|must\s+not|will\s+not|is\s+not\s+authorized\s+to|is\s+prohibited\s+from|should\s+not|may\s+not|cannot|could\s+not|will\s+ensure|shall\s+ensure|must\s+ensure|is\s+responsible\s+for\s+ensuring)', sentence, re.IGNORECASE)
                if modal_match:
                    current_modal = modal_match.group(0)
                    # Check if the modal contains negative words
                    current_is_negative = any(neg in current_modal.lower() for neg in ['not', 'prohibited', 'cannot'])
                    # Also check the full sentence for negative context
                    if not current_is_negative and any(neg in sentence.lower() for neg in ['shall not', 'must not', 'will not', 'should not', 'may not']):
                        current_is_negative = True
                    current_full_prefix = f"{current_actor} {current_modal}"
                    is_obligation_heading = True
                    print(f"Found obligation heading: '{sentence}' (actor: {current_actor}, modal: {current_modal}, negative: {current_is_negative})")
                    break
        
        # If this is an obligation heading, mark it as a heading and continue
        if is_obligation_heading:
            meta.is_heading = True
            continue
        
        # Check if this is a bullet point (ListItem category or starts with bullet chars)
        is_bullet = (
            meta.category == "ListItem" or
            sentence.startswith('•') or 
            sentence.startswith('-') or 
            sentence.startswith('*') or
            sentence.startswith('(') or  # Numbered bullets like (1), (2)
            re.match(r'^\d+\.', sentence) or  # Numbered bullets like 1., 2.
            re.match(r'^[a-z]\.', sentence) or  # Lettered bullets like a., b.
            (len(sentence.split()) <= 20 and current_full_prefix)  # Short sentences after obligation heading
        )
        
        # Apply obligation context to bullet points
        if is_bullet and current_full_prefix:
            # Remove bullet symbols and numbering
            clean_sentence = re.sub(r'^[•\-*]\s*', '', sentence)
            clean_sentence = re.sub(r'^\(\d+\)\s*', '', clean_sentence)
            clean_sentence = re.sub(r'^\d+\.\s*', '', clean_sentence)
            clean_sentence = re.sub(r'^[a-z]\.\s*', '', clean_sentence)
            
            # Construct full requirement with proper modal
            if current_is_negative:
                # For negative obligations, use the exact modal from the heading
                full_requirement = f"{current_actor} {current_modal} {clean_sentence}"
            else:
                # For positive obligations, use the exact modal from the heading
                full_requirement = f"{current_actor} {current_modal} {clean_sentence}"
            
            # Update the metadata
            meta.text = full_requirement
            print(f"Applied obligation context: '{full_requirement}'")
    
    return sentence_meta

def clean_and_segment_blocks(elements: List) -> Tuple[List[str], List[SentenceMetadata], List]:
    """
    Steps 2-3: Merge wrapped lines and split with PySBD.
    Returns sentences, metadata, and original elements for heading detection.
    """
    print("Cleaning blocks and segmenting sentences...")
    
    # Initialize PySBD segmenter
    segmenter = pysbd.Segmenter(language="en", clean=False)
    
    sentences = []
    sentence_meta = []
    element_mapping = []  # Map sentences back to original elements
    
    # Filter elements to only process relevant categories
    relevant_categories = {"Title", "NarrativeText", "ListItem", "Header"}
    
    for element in elements:
        if not hasattr(element, 'category') or element.category not in relevant_categories:
            continue
            
        if not hasattr(element, 'text') or not element.text:
            continue
        
        # Step 2: Merge wrapped lines
        clean_block = merge_lines(element.text)
        
        if not clean_block or len(clean_block.strip()) < 10:
            continue
        
        # Step 3: Split with PySBD
        block_sentences = segmenter.segment(clean_block)
        
        for sentence in block_sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue
            
            # Create metadata
            meta = SentenceMetadata(
                text=sentence,
                page_number=getattr(element.metadata, 'page_number', None),
                category=element.category,
                block_id=getattr(element, 'id', None),
                y_position=getattr(element.metadata, 'y', None),
                is_heading=element.category in {"Title", "Header"}
            )
            
            sentences.append(sentence)
            sentence_meta.append(meta)
            element_mapping.append(element)  # Keep reference to original element
    
    print(f"Extracted {len(sentences)} sentences from {len(elements)} elements")
    return sentences, sentence_meta, element_mapping

def detect_headings_advanced(sentence_meta: List[SentenceMetadata], element_mapping: List) -> List[SentenceMetadata]:
    """
    Advanced heading detection using multiple signals from sow_extractor_v4.py.
    """
    print("Detecting headings with robust logic...")
    
    for i, meta in enumerate(sentence_meta):
        if meta.is_heading:  # Already marked by category
            continue
            
        sentence = meta.text
        original_element = element_mapping[i] if i < len(element_mapping) else None
        
        # Method 1: Use unstructured's is_title function (most reliable)
        if original_element and is_title(original_element):
            meta.is_heading = True
            continue
        
        # Method 2: Check element category
        if hasattr(original_element, 'category') and original_element.category in ['Title', 'Header']:
            meta.is_heading = True
            continue
        
        # Method 3: Check for numbered patterns (1.2.3, etc.) - enhanced for subheadings
        if re.match(r'^\d+(\.\d+)*\s+[A-Z]', sentence):
            meta.is_heading = True
            continue
        
        # Method 3.5: Check for letter-based subheadings (Task 1a:, etc.)
        if re.match(r'^(Task|Section|Part|Chapter|Appendix)\s+\d+[a-z]?\s*:', sentence, re.I):
            meta.is_heading = True
            continue
        
        # Method 3.6: Check for standalone letter subheadings (a., b., c., etc.)
        if re.match(r'^[a-z]\.\s+[A-Z]', sentence):
            meta.is_heading = True
            continue
        
        # Method 4: Check for all-caps short headings
        if (sentence.isupper() and len(sentence.split()) <= 5 and len(sentence) < 100):
            meta.is_heading = True
            continue
        
        # Method 5: Check for common heading keywords (more restrictive)
        heading_keywords = [
            'introduction', 'background', 'purpose', 'scope', 'requirements',
            'deliverables', 'tasks', 'objectives', 'methodology', 'timeline',
            'section', 'chapter', 'part', 'appendix', 'overview', 'summary',
            'goal', 'mission', 'vision', 'strategy', 'approach', 'framework',
            'subtask', 'component', 'element', 'phase', 'stage', 'level'
        ]
        sentence_lower = sentence.lower()
        # Only mark as heading if it's a short sentence with heading keywords
        if (len(sentence.split()) <= 8 and 
            any(keyword in sentence_lower for keyword in heading_keywords)):
            meta.is_heading = True
            continue
        
        # Method 6: Check for short sentences that end with colons (likely subheadings)
        if (len(sentence.split()) <= 6 and sentence.endswith(':')):
            meta.is_heading = True
            continue
    
    heading_count = sum(1 for meta in sentence_meta if meta.is_heading)
    print(f"Detected {heading_count} headings")
    return sentence_meta

class AdvancedRequirementDetector:
    """Advanced requirement detection using multiple methods."""
    
    def __init__(self):
        self._init_nlp()
        self._build_patterns()
    
    def _init_nlp(self):
        """Initialize spaCy and sentence transformer."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded")
        except OSError:
            print("⚠️ Installing spaCy model...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model installed and loaded")
        
        try:
            self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ Sentence transformer loaded")
        except Exception as e:
            print(f"⚠️ Sentence transformer not available: {e}")
            self.sentence_model = None
    
    def _build_patterns(self):
        """Build comprehensive patterns for requirement detection."""
        self.requirement_patterns = [
            # Contractor obligations (expanded)
            r'(?:the\s+)?contractor\s+(?:shall|must|will|is\s+responsible\s+for|may\s+be\s+required\s+to|needs?\s+to|has?\s+to)',
            r'(?:the\s+)?vendor\s+(?:shall|must|will|is\s+responsible\s+for|needs?\s+to|has?\s+to)',
            r'(?:the\s+)?supplier\s+(?:shall|must|will|is\s+responsible\s+for|needs?\s+to|has?\s+to)',
            r'(?:the\s+)?offeror\s+(?:shall|must|will|is\s+responsible\s+for|needs?\s+to|has?\s+to)',
            
            # Requirement sections (expanded)
            r'requirements?\s*:',
            r'deliverables?\s*:',
            r'obligations?\s*:',
            r'tasks?\s*:',
            r'responsibilities?\s*:',
            r'objectives?\s*:',
            r'goals?\s*:',
            
            # Government requirements (expanded)
            r'(?:the\s+)?government\s+(?:shall|must|will|requires?|needs?)',
            r'cms\s+(?:shall|must|will|requires?|needs?)',
            r'federal\s+(?:shall|must|will|requires?|needs?)',
            r'agency\s+(?:shall|must|will|requires?|needs?)',
            
            # Compliance requirements (expanded)
            r'must\s+comply\s+with',
            r'in\s+accordance\s+with',
            r'as\s+required\s+by',
            r'per\s+(?:the|this|contract|agreement)',
            r'according\s+to',
            r'pursuant\s+to',
            
            # Data and security requirements
            r'data\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'security\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'privacy\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'hipaa\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'fisma\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            
            # Quality and performance requirements
            r'quality\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'performance\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'accuracy\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            
            # Reporting and documentation requirements
            r'report\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'document\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'submit\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            
            # Time and schedule requirements
            r'timeline\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'schedule\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            r'deadline\s+(?:shall|must|will|needs?\s+to|has?\s+to)',
            
            # General obligation patterns
            r'(?:shall|must|will)\s+(?:be|have|provide|deliver|ensure|maintain|support|implement)',
            r'(?:is|are)\s+(?:required|responsible|obligated|expected)\s+to',
            r'(?:needs?|has?)\s+to\s+(?:be|have|provide|deliver|ensure|maintain|support|implement)',
        ]
        
        self.imperative_verbs = [
            'provide', 'deliver', 'ensure', 'maintain', 'support', 'implement',
            'develop', 'create', 'establish', 'perform', 'conduct', 'execute',
            'manage', 'coordinate', 'facilitate', 'administer', 'operate',
            'monitor', 'report', 'document', 'train', 'assist', 'review',
            'submit', 'prepare', 'conduct', 'analyze', 'evaluate', 'assess',
            'obtain', 'access', 'process', 'handle', 'store', 'protect',
            'dispose', 'validate', 'verify', 'test', 'check', 'examine',
            'collect', 'gather', 'extract', 'transform', 'load', 'export',
            'import', 'transfer', 'share', 'distribute', 'publish', 'present',
            'demonstrate', 'show', 'prove', 'certify', 'attest', 'confirm'
        ]
        
        # Additional requirement indicators
        self.requirement_indicators = [
            'requirement', 'deliverable', 'obligation', 'responsibility',
            'duty', 'task', 'assignment', 'work', 'service', 'product',
            'output', 'result', 'outcome', 'delivery', 'submission',
            'compliance', 'conformance', 'adherence', 'following',
            'pursuant', 'according', 'per', 'as', 'when', 'if',
            'upon', 'within', 'during', 'throughout', 'via', 'using',
            'through', 'by', 'for', 'to', 'of', 'with', 'in', 'at'
        ]
    
    def detect_requirements(self, sentence_meta: List[SentenceMetadata]) -> List[SentenceMetadata]:
        """
        Detect requirements using multiple methods with confidence scoring.
        Enhanced to catch more requirements that might be missed.
        """
        print("Detecting requirements with enhanced methods...")
        
        for meta in sentence_meta:
            if meta.is_heading:  # Skip headings
                continue
                
            sentence = meta.text
            sentence_lower = sentence.lower()
            
            # Method 1: Regex patterns (highest confidence)
            for pattern in self.requirement_patterns:
                if re.search(pattern, sentence_lower, re.I):
                    meta.is_requirement = True
                    meta.detector = 'regex'
                    meta.confidence = 0.9
                    break
            
            # Method 2: Imperative verbs (expanded)
            if not meta.is_requirement:
                words = sentence_lower.split()
                if words and words[0] in self.imperative_verbs:
                    meta.is_requirement = True
                    meta.detector = 'regex'
                    meta.confidence = 0.7
            
            # Method 3: Enhanced keyword analysis
            if not meta.is_requirement:
                # Check for multiple requirement indicators
                indicator_count = sum(1 for indicator in self.requirement_indicators if indicator in sentence_lower)
                obligation_words = ['shall', 'must', 'will', 'required', 'responsible', 'obligated', 'needs', 'has to']
                obligation_count = sum(1 for word in obligation_words if word in sentence_lower)
                
                # If sentence has multiple indicators or obligation words, it's likely a requirement
                if indicator_count >= 2 or obligation_count >= 1:
                    meta.is_requirement = True
                    meta.detector = 'keyword'
                    meta.confidence = 0.6
            
            # Method 4: spaCy linguistic analysis (enhanced)
            if not meta.is_requirement and hasattr(self, 'nlp'):
                doc = self.nlp(sentence)
                if doc and len(doc) > 0:
                    # Check if sentence starts with verb and contains obligation words
                    if doc[0].pos_ == 'VERB':
                        obligation_words = ['shall', 'must', 'will', 'required', 'responsible', 'obligated']
                        if any(word in sentence_lower for word in obligation_words):
                            meta.is_requirement = True
                            meta.detector = 'spacy'
                            meta.confidence = 0.6
                    
                    # Check for modal verbs (shall, must, will) anywhere in sentence
                    modal_verbs = ['shall', 'must', 'will', 'should', 'need', 'have to']
                    if any(token.text.lower() in modal_verbs for token in doc):
                        # Additional check: sentence should be about actions/obligations
                        action_words = ['provide', 'deliver', 'ensure', 'maintain', 'support', 'implement', 'perform', 'conduct']
                        if any(word in sentence_lower for word in action_words):
                            meta.is_requirement = True
                            meta.detector = 'spacy'
                            meta.confidence = 0.5
            
            # Method 5: BERT semantic analysis (enhanced)
            if not meta.is_requirement and self.sentence_model:
                # Expanded requirement keywords
                requirement_keywords = [
                    'contractor', 'vendor', 'supplier', 'offeror', 'shall', 'must', 'will', 
                    'provide', 'deliver', 'ensure', 'maintain', 'support', 'implement',
                    'perform', 'conduct', 'execute', 'manage', 'coordinate', 'facilitate',
                    'administer', 'operate', 'monitor', 'report', 'document', 'train',
                    'assist', 'review', 'submit', 'prepare', 'analyze', 'evaluate',
                    'obtain', 'access', 'process', 'handle', 'store', 'protect',
                    'validate', 'verify', 'test', 'check', 'examine', 'collect',
                    'gather', 'extract', 'transform', 'load', 'export', 'import'
                ]
                keyword_count = sum(1 for keyword in requirement_keywords if keyword in sentence_lower)
                if keyword_count >= 2:
                    meta.is_requirement = True
                    meta.detector = 'bert'
                    meta.confidence = 0.5
            
            # Method 6: Context-based detection (new)
            if not meta.is_requirement:
                # Check if sentence is in a requirement-heavy context
                # Look for sentences that contain specific requirement-related phrases
                requirement_phrases = [
                    'the contractor', 'the vendor', 'the supplier', 'the offeror',
                    'shall provide', 'must provide', 'will provide',
                    'shall deliver', 'must deliver', 'will deliver',
                    'shall ensure', 'must ensure', 'will ensure',
                    'shall maintain', 'must maintain', 'will maintain',
                    'shall support', 'must support', 'will support',
                    'shall implement', 'must implement', 'will implement',
                    'is required to', 'is responsible for', 'is obligated to',
                    'needs to', 'has to', 'must comply', 'in accordance with',
                    'as required by', 'per the', 'according to', 'pursuant to'
                ]
                
                if any(phrase in sentence_lower for phrase in requirement_phrases):
                    meta.is_requirement = True
                    meta.detector = 'context'
                    meta.confidence = 0.8
        
        # Count results
        requirement_count = sum(1 for meta in sentence_meta if meta.is_requirement)
        print(f"Detected {requirement_count} requirements")
        
        return sentence_meta

def remove_pre_intro_content(sentence_meta: List[SentenceMetadata]) -> List[SentenceMetadata]:
    """
    Remove any content that appears before and including the Table of Contents section.
    """
    print("Removing content before and including Table of Contents...")
    
    # Find the first content section after TOC
    start_index = 0
    toc_end_index = -1
    
    # First, find where TOC ends
    for i, meta in enumerate(sentence_meta):
        if meta.is_heading:
            heading_lower = meta.text.lower()
            # Check if this is a TOC section
            if any(keyword in heading_lower for keyword in ['table of contents', 'contents', 'toc']):
                toc_end_index = i
                print(f"Found TOC section: {meta.text}")
                # Look for the next major section after TOC
                for j in range(i + 1, len(sentence_meta)):
                    next_meta = sentence_meta[j]
                    if next_meta.is_heading:
                        next_heading_lower = next_meta.text.lower()
                        # Skip if it's still part of TOC (numbered items, etc.)
                        if (re.match(r'^\d+\.', next_meta.text) or 
                            any(toc_word in next_heading_lower for toc_word in ['page', 'section', 'appendix'])):
                            continue
                        # Found the first real content section
                        start_index = j
                        print(f"Starting content from: {next_meta.text}")
                        break
                break
    
    # If no TOC found, try to find Introduction/Background as fallback
    if start_index == 0:
        for i, meta in enumerate(sentence_meta):
            if meta.is_heading:
                heading_lower = meta.text.lower()
                if any(keyword in heading_lower for keyword in ['introduction', 'background', 'purpose', 'scope']):
                    start_index = i
                    print(f"No TOC found, starting from: {meta.text}")
                    break
    
    # If still no start point found, keep everything
    if start_index == 0:
        print("No TOC or Introduction/Background section found, keeping all content")
        return sentence_meta
    
    # Remove content before and including TOC
    filtered_meta = sentence_meta[start_index:]
    removed_count = len(sentence_meta) - len(filtered_meta)
    print(f"Removed {removed_count} sentences before and including TOC")
    
    return filtered_meta

def create_dataframe(sentence_meta: List[SentenceMetadata]) -> pd.DataFrame:
    """
    Step 4: Create DataFrame with single column structure.
    """
    print("Creating DataFrame...")
    
    data = []
    current_heading = "(UNLABELED)"
    
    for meta in sentence_meta:
        if meta.is_heading:
            current_heading = meta.text
            # Add heading row
            data.append({
                'Content': current_heading,
                'is_heading': True,
                'page': meta.page_number,
                'category': meta.category,
                'block_id': meta.block_id,
                'detector': meta.detector,
                'confidence': meta.confidence
            })
        elif meta.is_requirement:
            # Add requirement row
            data.append({
                'Content': meta.text,
                'is_heading': False,
                'page': meta.page_number,
                'category': meta.category,
                'block_id': meta.block_id,
                'detector': meta.detector,
                'confidence': meta.confidence
            })
    
    df = pd.DataFrame(data)
    print(f"Created DataFrame with {len(df)} rows")
    return df

def save_results(df: pd.DataFrame, output_dir: str) -> None:
    """
    Save results with Requirements Matrix structure (Requirements | Past Performance).
    """
    print("Saving results...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save Excel with Requirements Matrix structure
    excel_path = os.path.join(output_dir, "requirements_hybrid_extractor.xlsx")
    
    # Create a new workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requirements Matrix"
    
    # Import styling
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    
    # Set headers and make them bold
    bold_font = Font(bold=True, size=12)
    ws['A1'] = 'Requirements'      # Column A Header
    ws['B1'] = 'Past Performance'  # Column B Header
    ws['A1'].font = bold_font
    ws['B1'].font = bold_font
    
    # Add borders to headers
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    ws['A1'].border = thin_border
    ws['B1'].border = thin_border
    
    # Add header background
    header_fill = PatternFill(start_color="E6E6E6", end_color="E6E6E6", fill_type="solid")
    ws['A1'].fill = header_fill
    ws['B1'].fill = header_fill
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 60  # Requirements column width
    ws.column_dimensions['B'].width = 60  # Past Performance column width
    
    # Start populating data from row 2
    row_idx = 2
    
    # Heading style (grey background, bold font)
    heading_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    heading_font = Font(bold=True, size=12)
    
    # Content style (white background, normal font)
    content_font = Font(size=11)
    
    # Iterate through each row in the DataFrame
    for _, row in df.iterrows():
        content = row['Content']
        is_heading = row['is_heading']
        
        # Add content to Requirements column
        cell = ws.cell(row=row_idx, column=1, value=content)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True, vertical='top')
        
        # Apply styling based on whether it's a heading or requirement
        if is_heading:
            cell.fill = heading_fill
            cell.font = heading_font
        else:
            cell.font = content_font
        
        # Past Performance column remains empty
        past_perf_cell = ws.cell(row=row_idx, column=2, value="")
        past_perf_cell.border = thin_border
        past_perf_cell.alignment = Alignment(wrap_text=True, vertical='top')
        
        row_idx += 1
    
    # Save the workbook
    wb.save(excel_path)
    
    # Save JSON with metadata
    json_path = os.path.join(output_dir, "requirements_hybrid_extractor.json")
    json_data = {}
    current_heading = "(UNLABELED)"
    requirements = []
    
    for _, row in df.iterrows():
        if row['is_heading']:
            if requirements:  # Save previous heading's requirements
                json_data[current_heading] = requirements
            current_heading = row['Content']
            requirements = []
        elif row['Content']:
            requirements.append(row['Content'])
    
    # Save last heading's requirements
    if requirements:
        json_data[current_heading] = requirements
    
    import json
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    # Save detailed CSV for analysis
    csv_path = os.path.join(output_dir, "requirements_hybrid_extractor_detailed.csv")
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Results saved:")
    print(f"   - Excel: {excel_path}")
    print(f"   - JSON: {json_path}")
    print(f"   - CSV: {csv_path}")

def process_pdf_hybrid(pdf_path: str, output_dir: str = "outgoing") -> pd.DataFrame:
    """
    Main processing function using the hybrid Unstructured + PySBD workflow.
    """
    print(f"Processing PDF with hybrid approach: {pdf_path}")
    
    # Step 1: Parse with Unstructured
    elements = extract_with_unstructured(pdf_path)
    
    # Step 1.5: Remove headers, footers, and TOC sections
    elements = scrub_headers_footers(elements)
    
    # Steps 2-3: Clean and segment
    sentences, sentence_meta, element_mapping = clean_and_segment_blocks(elements)
    
    # Step 4: Detect headings
    sentence_meta = detect_headings_advanced(sentence_meta, element_mapping)
    
    # Step 4.5: Propagate obligation context
    sentence_meta = propagate_obligation_context(sentence_meta)
    
    # Step 5: Detect requirements
    detector = AdvancedRequirementDetector()
    sentence_meta = detector.detect_requirements(sentence_meta)
    
    # Step 5.5: Remove content before Introduction/Background
    sentence_meta = remove_pre_intro_content(sentence_meta)
    
    # Step 6: Create DataFrame
    df = create_dataframe(sentence_meta)
    
    # Step 7: Save results
    save_results(df, output_dir)
    
    # Print summary
    requirement_count = sum(1 for meta in sentence_meta if meta.is_requirement)
    heading_count = sum(1 for meta in sentence_meta if meta.is_heading)
    
    print(f"✅ Processing complete!")
    print(f"📊 Summary:")
    print(f"   - Total sentences: {len(sentences)}")
    print(f"   - Headings: {heading_count}")
    print(f"   - Requirements: {requirement_count}")
    print(f"   - DataFrame rows: {len(df)}")
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Advanced hybrid PDF requirement extractor")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output-dir", default="outgoing", help="Output directory")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)
    
    try:
        df = process_pdf_hybrid(args.pdf_path, args.output_dir)
        print(f"Successfully processed {len(df)} rows")
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 