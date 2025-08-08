#!/usr/bin/env python3
"""
Enhanced Tool Search Script (TXT Version)
Searches TXT documents directly for tool mentions with comprehensive analysis.
"""

import os
import json
import re
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime
import pandas as pd
from pathlib import Path

# Enhanced tool name variations and aliases
TOOL_ALIASES = {
    'AWS': [
        'AWS', 'Amazon Web Services', 'Amazon AWS', 'AWS Cloud', 'AWS Services',
        'EC2', 'S3', 'Lambda', 'RDS', 'CloudFormation', 'CloudWatch',
        'AWS Select', 'AWS GovCloud', 'Amazon EC2', 'Amazon S3',
        'AWS S3', 'S3 bucket', 'S3 storage', 'AWS Lambda', 'AWS RDS',
        'Amazon Web Services', 'AWS platform', 'AWS infrastructure'
    ],
    'Redhat': [
        'Redhat', 'Red Hat', 'Red Hat Enterprise Linux', 'RHEL', 'Red Hat Linux',
        'Red Hat Select', 'Red Hat OpenShift', 'OpenShift', 'Red Hat Ansible',
        'Ansible', 'Red Hat Satellite', 'Satellite', 'Red Hat platform'
    ],
    'ServiceNow': [
        'ServiceNow', 'SNOW', 'Service Now', 'Service-Now', 'Service_Now',
        'ServiceNow platform', 'ServiceNow system', 'ServiceNow tool',
        'ServiceNow ticketing', 'ServiceNow help desk', 'ServiceNow platform'
    ],
    'Databricks': [
        'Databricks', 'DataBricks', 'Data Bricks', 'Databricks platform',
        'Databricks workspace', 'Databricks cluster', 'Databricks notebook',
        'Databricks SQL', 'Databricks ML', 'Databricks Delta', 'Databricks platform'
    ]
}

class TXTToolSearcher:
    """Searches TXT files for tool mentions with comprehensive analysis."""
    
    def __init__(self, txt_dir: str = "documents_txt"):
        self.txt_dir = Path(txt_dir)
        self.search_results = defaultdict(list)
    
    def read_txt_file(self, txt_path: Path) -> str:
        """Read text content from a TXT file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove metadata header if present
            if content.startswith('# Converted from:'):
                lines = content.split('\n')
                # Find the first non-comment line
                for i, line in enumerate(lines):
                    if not line.startswith('#'):
                        content = '\n'.join(lines[i:])
                        break
            
            return content.strip()
            
        except Exception as e:
            print(f"Error reading TXT file {txt_path}: {e}")
            return ""
    
    def search_for_tools_in_document(self, txt_path: Path, tools: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Search for specific tools and their aliases in a single TXT document."""
        tool_matches = defaultdict(list)
        
        # Read text from TXT file
        text_content = self.read_txt_file(txt_path)
        if not text_content:
            return dict(tool_matches)
        
        # Convert to lowercase for case-insensitive search
        text_lower = text_content.lower()
        
        for tool in tools:
            if tool in TOOL_ALIASES:
                aliases = TOOL_ALIASES[tool]
                for alias in aliases:
                    if alias.lower() in text_lower:
                        # Find all occurrences
                        occurrences = []
                        start = 0
                        while True:
                            index = text_lower.find(alias.lower(), start)
                            if index == -1:
                                break
                            
                            # Extract context around the match
                            context_start = max(0, index - 300)
                            context_end = min(len(text_content), index + len(alias) + 300)
                            context = text_content[context_start:context_end]
                            
                            # Clean up context
                            context = re.sub(r'\s+', ' ', context).strip()
                            
                            # Calculate confidence based on technical context
                            technical_words = [
                                'implementation', 'deployment', 'configuration', 'integration', 
                                'development', 'administration', 'management', 'support', 'maintenance',
                                'platform', 'system', 'tool', 'service', 'infrastructure', 'architecture',
                                'database', 'cloud', 'server', 'application', 'software', 'technology',
                                'solution', 'environment', 'framework', 'api', 'interface', 'protocol'
                            ]
                            technical_context = sum(1 for word in technical_words if word.lower() in context.lower())
                            confidence = min(0.3 + (technical_context * 0.1), 1.0)
                            
                            # Check for usage indicators
                            usage_indicators = [
                                'used', 'utilized', 'implemented', 'deployed', 'configured',
                                'managed', 'administered', 'supported', 'maintained', 'developed',
                                'built', 'created', 'established', 'set up', 'installed'
                            ]
                            usage_bonus = sum(1 for word in usage_indicators if word.lower() in context.lower()) * 0.05
                            confidence = min(confidence + usage_bonus, 1.0)
                            
                            occurrences.append({
                                'alias': alias,
                                'context': context,
                                'confidence': confidence,
                                'position': index,
                                'technical_context_score': technical_context,
                                'usage_score': usage_bonus
                            })
                            
                            start = index + 1
                        
                        # Add all occurrences to tool matches
                        for occurrence in occurrences:
                            tool_matches[tool].append({
                                'document': txt_path.stem,  # Remove .txt extension
                                'document_path': str(txt_path),
                                'original_pdf': f"{txt_path.stem}.pdf",  # Reference to original PDF
                                'alias_found': occurrence['alias'],
                                'context': occurrence['context'],
                                'confidence': occurrence['confidence'],
                                'position': occurrence['position'],
                                'technical_context_score': occurrence['technical_context_score'],
                                'usage_score': occurrence['usage_score']
                            })
                        
                        break  # Found one alias, no need to check others for this tool
        
        return dict(tool_matches)
    
    def search_all_documents(self, tools: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Search all TXT documents in the directory for tool mentions."""
        all_tool_matches = defaultdict(list)
        
        if not self.txt_dir.exists():
            print(f"TXT documents directory not found: {self.txt_dir}")
            return dict(all_tool_matches)
        
        # Get all TXT files
        txt_files = list(self.txt_dir.glob("*.txt"))
        
        if not txt_files:
            print(f"No TXT files found in {self.txt_dir}")
            return dict(all_tool_matches)
        
        print(f"Searching {len(txt_files)} TXT documents for tool mentions...")
        
        # Search each TXT file
        for txt_path in txt_files:
            print(f"Searching: {txt_path.name}")
            document_matches = self.search_for_tools_in_document(txt_path, tools)
            
            # Merge results
            for tool, matches in document_matches.items():
                all_tool_matches[tool].extend(matches)
        
        return dict(all_tool_matches)
    
    def generate_detailed_report(self, tool_matches: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate a detailed text report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# COMPREHENSIVE TOOL USAGE ANALYSIS REPORT (TXT Version)
Generated: {timestamp}

## Executive Summary
This report provides a comprehensive analysis of tool usage across all TXT documents in the capability matrix.
Total documents searched: {len(set([match['document'] for matches in tool_matches.values() for match in matches]))}

## Analysis Methodology
- **Source**: TXT files converted from original PDFs for reliable text processing
- **Search Method**: Direct text search with comprehensive alias matching
- **Confidence Scoring**: Based on technical context and usage indicators
- **Context Extraction**: 600-character context windows around each match

"""
        
        for tool, matches in tool_matches.items():
            if not matches:
                report += f"\n## {tool.upper()}\n**Status: No usage found**\n"
                continue
                
            documents = list(set([match['document'] for match in matches]))
            total_mentions = len(matches)
            
            report += f"""
## {tool.upper()}
**Status: Found in {len(documents)} document(s) with {total_mentions} total mentions**

### Documents Where Used:
{chr(10).join([f"- {doc}" for doc in documents])}

### Detailed Usage Analysis:
"""
            
            # Group by document
            by_document = defaultdict(list)
            for match in matches:
                by_document[match['document']].append(match)
            
            for document, doc_matches in by_document.items():
                report += f"\n#### {document}\n"
                report += f"**Mentions: {len(doc_matches)}**\n"
                report += f"**Original PDF: {doc_matches[0]['original_pdf']}**\n\n"
                
                for i, match in enumerate(doc_matches, 1):
                    report += f"**Match {i}:**\n"
                    report += f"- **Alias Found:** {match['alias_found']}\n"
                    report += f"- **Confidence:** {match['confidence']:.2f}\n"
                    report += f"- **Technical Context Score:** {match['technical_context_score']}\n"
                    report += f"- **Usage Score:** {match['usage_score']:.2f}\n"
                    report += f"- **Context:** {match['context'][:500]}...\n\n"
        
        return report
    
    def generate_excel_matrix(self, tool_matches: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """Generate Excel capability matrix."""
        rows = []
        
        for tool, matches in tool_matches.items():
            if not matches:
                continue
                
            # Group by document
            by_document = defaultdict(list)
            for match in matches:
                by_document[match['document']].append(match)
            
            for document, doc_matches in by_document.items():
                # Create detailed row for each document-tool combination
                row = {
                    'Tool': tool,
                    'Document': document,
                    'Original_PDF': doc_matches[0]['original_pdf'],
                    'Total_Mentions': len(doc_matches),
                    'Aliases_Found': ', '.join(set([m['alias_found'] for m in doc_matches])),
                    'Avg_Confidence': sum([m['confidence'] for m in doc_matches]) / len(doc_matches),
                    'Avg_Technical_Score': sum([m['technical_context_score'] for m in doc_matches]) / len(doc_matches),
                    'Avg_Usage_Score': sum([m['usage_score'] for m in doc_matches]) / len(doc_matches),
                    'Usage_Context': '; '.join([m['context'][:150] for m in doc_matches[:3]]),
                    'Document_Path': doc_matches[0]['document_path']
                }
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def run_analysis(self, tools: List[str] = None) -> Dict[str, Any]:
        """Run the complete tool analysis."""
        if tools is None:
            tools = ['AWS', 'Redhat', 'ServiceNow', 'Databricks']
        
        print("🔍 Enhanced Tool Usage Analysis (TXT Version)")
        print("=" * 50)
        
        # Search all documents
        tool_matches = self.search_all_documents(tools)
        
        # Generate report
        print("📝 Generating detailed report...")
        report = self.generate_detailed_report(tool_matches)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"COMPREHENSIVE_TOOL_REPORT_TXT_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Generate Excel matrix
        print("📊 Generating Excel capability matrix...")
        df = self.generate_excel_matrix(tool_matches)
        
        if not df.empty:
            excel_filename = f"COMPREHENSIVE_TOOL_MATRIX_TXT_{timestamp}.xlsx"
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Tool_Usage_Matrix', index=False)
                
                # Create summary sheet
                summary_data = []
                for tool in tools:
                    matches = tool_matches.get(tool, [])
                    documents = list(set([m['document'] for m in matches]))
                    summary_data.append({
                        'Tool': tool,
                        'Documents_Found': len(documents),
                        'Total_Mentions': len(matches),
                        'Document_List': ', '.join(documents) if documents else 'None'
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            print(f"✅ Excel matrix saved: {excel_filename}")
        else:
            print("⚠️  No tool usage found to create Excel matrix")
        
        print(f"✅ Detailed report saved: {report_filename}")
        
        # Print summary
        print("\n📋 SUMMARY:")
        print("=" * 30)
        for tool in tools:
            matches = tool_matches.get(tool, [])
            documents = list(set([m['document'] for m in matches]))
            if documents:
                print(f"✅ {tool}: Found in {len(documents)} document(s) - {', '.join(documents)}")
            else:
                print(f"❌ {tool}: No usage found")
        
        return {
            'tool_matches': tool_matches,
            'report_filename': report_filename,
            'excel_filename': excel_filename if not df.empty else None
        }

def main():
    """Main analysis function."""
    searcher = TXTToolSearcher()
    searcher.run_analysis()

if __name__ == "__main__":
    main() 