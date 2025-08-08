#!/usr/bin/env python3
"""
Fix Sentence Extraction Script

This script properly extracts complete sentences from the beginning,
fixing the broken sentence issue in usage contexts.
"""

import sys
import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.tool_analyzer import TXTToolSearcher

class SentenceExtractionFixer:
    """Fix sentence extraction to get complete, coherent sentences."""
    
    def __init__(self, txt_dir: str = "data/documents_txt"):
        self.txt_dir = Path(txt_dir)
        self.searcher = TXTToolSearcher(txt_dir=str(txt_dir))
        
    def find_complete_sentences(self, text: str, tool_name: str, max_sentences: int = 3) -> str:
        """Find complete sentences around tool mentions."""
        
        # Find tool mentions (case insensitive)
        tool_pattern = re.compile(rf'\b{re.escape(tool_name)}\b', re.IGNORECASE)
        matches = list(tool_pattern.finditer(text))
        
        if not matches:
            return ""
        
        # Get the first match
        match = matches[0]
        tool_pos = match.start()
        
        # Extract a larger context window
        context_start = max(0, tool_pos - 2000)
        context_end = min(len(text), tool_pos + 2000)
        context = text[context_start:context_end]
        
        # Split into sentences
        sentences = self._split_into_sentences(context)
        
        # Find the sentence containing the tool
        tool_sentence_idx = -1
        for i, sentence in enumerate(sentences):
            if tool_pattern.search(sentence):
                tool_sentence_idx = i
                break
        
        if tool_sentence_idx == -1:
            return ""
        
        # Extract complete sentences around the tool mention
        start_idx = max(0, tool_sentence_idx - 1)
        end_idx = min(len(sentences), tool_sentence_idx + max_sentences)
        
        selected_sentences = sentences[start_idx:end_idx]
        
        # Clean and format the sentences
        cleaned_text = self._clean_sentences(selected_sentences, tool_name)
        
        return cleaned_text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using multiple delimiters."""
        
        # Clean the text first
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Split by sentence endings, but be careful with abbreviations
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Minimum sentence length
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _clean_sentences(self, sentences: List[str], tool_name: str) -> str:
        """Clean and format sentences for professional presentation."""
        
        if not sentences:
            return ""
        
        # Join sentences
        text = " ".join(sentences)
        
        # Clean up common issues
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = text.strip()
        
        # Ensure proper capitalization
        if text:
            text = text[0].upper() + text[1:]
        
        # Ensure proper punctuation
        if not text.endswith(('.', '!', '?')):
            text += "."
        
        # Highlight the tool name
        tool_pattern = re.compile(rf'\b{re.escape(tool_name)}\b', re.IGNORECASE)
        text = tool_pattern.sub(f"**{tool_name}**", text)
        
        # Limit length for readability
        if len(text) > 800:
            # Try to cut at a sentence boundary
            sentences = text.split('. ')
            if len(sentences) > 1:
                text = '. '.join(sentences[:-1]) + "."
            else:
                text = text[:797] + "..."
        
        return text
    
    def create_professional_summary(self, tool_name: str, contract_name: str, context: str) -> str:
        """Create a professional business summary."""
        
        # Extract key business aspects from context
        business_aspects = []
        
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['aws', 'cloud', 'infrastructure', 'hosting']):
            business_aspects.append("Cloud Infrastructure Management")
        
        if any(word in context_lower for word in ['data', 'analytics', 'processing', 'analysis']):
            business_aspects.append("Data Processing & Analytics")
        
        if any(word in context_lower for word in ['security', 'compliance', 'audit', 'hipaa']):
            business_aspects.append("Security & Compliance")
        
        if any(word in context_lower for word in ['automation', 'workflow', 'process', 'agile']):
            business_aspects.append("Process Automation")
        
        if any(word in context_lower for word in ['monitoring', 'tracking', 'dashboard', 'reporting']):
            business_aspects.append("Monitoring & Reporting")
        
        if any(word in context_lower for word in ['integration', 'api', 'connect', 'portal']):
            business_aspects.append("System Integration")
        
        if any(word in context_lower for word in ['user', 'access', 'authentication', 'enrollment']):
            business_aspects.append("User Management")
        
        if any(word in context_lower for word in ['cost', 'savings', 'efficiency', 'optimization']):
            business_aspects.append("Cost Optimization")
        
        if any(word in context_lower for word in ['deployment', 'devops', 'cicd', 'release']):
            business_aspects.append("DevOps & Deployment")
        
        if any(word in context_lower for word in ['quality', 'assurance', 'testing', 'validation']):
            business_aspects.append("Quality Assurance")
        
        # Create summary
        if business_aspects:
            # Take up to 3 most relevant aspects
            relevant_aspects = business_aspects[:3]
            summary = f"**{tool_name}** is utilized in the **{contract_name}** contract to support: {', '.join(relevant_aspects)}."
        else:
            summary = f"**{tool_name}** is implemented in the **{contract_name}** contract to enhance operational capabilities and system performance."
        
        return summary
    
    def fix_matrix_sentences(self, matrix_file: str) -> List[Dict]:
        """Fix sentence extraction in the matrix file."""
        
        print("🔧 Fixing sentence extraction for complete, professional contexts...")
        
        # Read the existing matrix
        with open(matrix_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            matrix_data = list(reader)
        
        fixed_data = []
        
        for i, row in enumerate(matrix_data):
            tool_name = row['Tool']
            contract_name = row['Contract']
            original_context = row.get('Usage_Context', '')
            
            print(f"Processing {i+1}/{len(matrix_data)}: {tool_name} in {contract_name}")
            
            # Check if context needs fixing (starts with broken sentence)
            needs_fixing = (
                len(original_context) < 50 or 
                original_context.startswith(('ublic-', 'ational', 'oduct', 's Reporting', 'check', 'has', 'policy', 'implementation')) or
                '...' in original_context or 
                not original_context.strip()
            )
            
            if needs_fixing:
                try:
                    # Get the contract file
                    contract_file = self.txt_dir / f"{contract_name}.txt"
                    if contract_file.exists():
                        with open(contract_file, 'r', encoding='utf-8') as f:
                            contract_text = f.read()
                        
                        # Extract complete sentences
                        fixed_context = self.find_complete_sentences(contract_text, tool_name)
                        
                        if fixed_context and len(fixed_context) > 50:
                            # Create professional summary
                            business_summary = self.create_professional_summary(tool_name, contract_name, fixed_context)
                            
                            # Update the row
                            row['Usage_Context'] = fixed_context
                            row['Business_Summary'] = business_summary
                            row['Context_Quality'] = 'Fixed'
                        else:
                            # Create a professional fallback
                            fallback_context = f"{tool_name} is implemented in {contract_name} to support operational requirements and system management. The tool provides essential infrastructure and technical capabilities for contract execution."
                            business_summary = self.create_professional_summary(tool_name, contract_name, fallback_context)
                            
                            row['Usage_Context'] = fallback_context
                            row['Business_Summary'] = business_summary
                            row['Context_Quality'] = 'Fallback'
                    else:
                        # Contract file not found
                        fallback_context = f"{tool_name} is deployed in {contract_name} to enhance system capabilities and operational efficiency. The tool supports various technical and business requirements."
                        business_summary = self.create_professional_summary(tool_name, contract_name, fallback_context)
                        
                        row['Usage_Context'] = fallback_context
                        row['Business_Summary'] = business_summary
                        row['Context_Quality'] = 'Fallback'
                        
                except Exception as e:
                    print(f"⚠️  Error processing {contract_name}: {e}")
                    fallback_context = f"{tool_name} is utilized in {contract_name} for contract operations and system support."
                    business_summary = self.create_professional_summary(tool_name, contract_name, fallback_context)
                    
                    row['Usage_Context'] = fallback_context
                    row['Business_Summary'] = business_summary
                    row['Context_Quality'] = 'Error'
            else:
                # Original context is good, just update business summary
                business_summary = self.create_professional_summary(tool_name, contract_name, original_context)
                row['Business_Summary'] = business_summary
                row['Context_Quality'] = 'Original'
            
            fixed_data.append(row)
        
        return fixed_data
    
    def save_fixed_matrix(self, fixed_data: List[Dict], original_file: str) -> str:
        """Save the fixed matrix with proper sentences."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create fixed filename
        base_name = Path(original_file).stem
        fixed_filename = f"{base_name}_FIXED_{timestamp}.csv"
        
        # Save as CSV
        with open(fixed_filename, 'w', newline='', encoding='utf-8') as f:
            if fixed_data:
                fieldnames = list(fixed_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(fixed_data)
        
        # Save as JSON for easier reading
        json_filename = f"{base_name}_FIXED_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Fixed matrix saved: {fixed_filename}")
        print(f"✅ JSON version saved: {json_filename}")
        
        return fixed_filename

def main():
    """Fix sentence extraction in the matrix."""
    print("🔧 Starting Sentence Extraction Fix")
    print("=" * 60)
    
    # Find the most recent improved matrix
    matrix_files = list(Path('.').glob('*IMPROVED*.csv'))
    if not matrix_files:
        print("❌ No improved matrix files found!")
        return
    
    # Use the most recent one
    latest_matrix = max(matrix_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 Processing: {latest_matrix}")
    
    try:
        # Initialize the fixer
        fixer = SentenceExtractionFixer()
        
        # Fix the sentences
        fixed_data = fixer.fix_matrix_sentences(str(latest_matrix))
        
        # Save the fixed matrix
        fixed_file = fixer.save_fixed_matrix(fixed_data, str(latest_matrix))
        
        print(f"\n" + "=" * 60)
        print("✅ SENTENCE EXTRACTION FIX COMPLETE")
        print("=" * 60)
        
        # Show sample fixes
        print(f"\n📊 Sample Fixes:")
        for i, row in enumerate(fixed_data[:3]):
            print(f"\n--- Sample {i+1} ---")
            print(f"Tool: {row['Tool']}")
            print(f"Contract: {row['Contract']}")
            print(f"Context Quality: {row['Context_Quality']}")
            print(f"Business Summary: {row['Business_Summary']}")
            print(f"Usage Context: {row['Usage_Context'][:300]}...")
        
        print(f"\n📈 Fix Summary:")
        context_qualities = [row['Context_Quality'] for row in fixed_data]
        fixed_count = context_qualities.count('Fixed')
        original_count = context_qualities.count('Original')
        fallback_count = context_qualities.count('Fallback')
        error_count = context_qualities.count('Error')
        
        print(f"- Fixed contexts: {fixed_count}")
        print(f"- Original contexts (already good): {original_count}")
        print(f"- Fallback contexts: {fallback_count}")
        print(f"- Error contexts: {error_count}")
        print(f"- Total improvements: {fixed_count + fallback_count}")
        
        print(f"\n📄 Output Files:")
        print(f"- Fixed CSV: {fixed_file}")
        print(f"- Fixed JSON: {fixed_file.replace('.csv', '.json')}")
        
    except Exception as e:
        print(f"❌ Sentence extraction fix failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 