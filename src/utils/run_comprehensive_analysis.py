#!/usr/bin/env python3
"""
Comprehensive Tool Analysis with All Documents

This script runs a complete analysis including all documents (original + new)
and generates updated reports for all tools.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.tool_analyzer import TXTToolSearcher

def main():
    """Run comprehensive analysis with all documents."""
    print("🔍 Starting Comprehensive Tool Analysis with All Documents")
    print("=" * 70)
    
    # Define tools to analyze (expanded list)
    tools = [
        'ServiceNow', 'Databricks', 'Redhat', 'AWS S3', 'AWS Lambda',
        'AWS', 'Amazon', 'S3', 'Lambda', 'EC2', 'RDS', 'CloudFormation',
        'RedHat', 'Red Hat', 'OpenShift', 'Ansible',
        'Azure', 'Microsoft', 'Power BI', 'SharePoint',
        'Oracle', 'SQL Server', 'PostgreSQL', 'MySQL',
        'SAS', 'Tableau', 'QuickSight', 'Cognos',
        'Jenkins', 'GitHub', 'GitLab', 'Terraform',
        'Docker', 'Kubernetes', 'VMware', 'Citrix'
    ]
    
    print(f"📋 Analyzing {len(tools)} tools across all documents...")
    print(f"📄 Total documents: 75 (including new contracts)")
    
    try:
        # Initialize the tool searcher
        searcher = TXTToolSearcher(txt_dir="data/documents_txt")
        
        # Search for all tools
        print("🔍 Searching all documents for tool mentions...")
        results = searcher.search_all_documents(tools)
        
        # Filter out tools with no results
        active_tools = {tool: matches for tool, matches in results.items() if matches}
        
        print(f"\n📊 Found {len(active_tools)} tools with usage:")
        
        # Generate summary
        total_mentions = 0
        total_contracts = set()
        
        for tool, matches in active_tools.items():
            mentions = len(matches)
            contracts = set(match['document'] for match in matches)
            total_mentions += mentions
            total_contracts.update(contracts)
            
            print(f"- {tool}: {mentions} mentions across {len(contracts)} contracts")
        
        print(f"\n📈 Summary:")
        print(f"- Total tools found: {len(active_tools)}")
        print(f"- Total mentions: {total_mentions}")
        print(f"- Total unique contracts: {len(total_contracts)}")
        
        # Generate detailed report for top tools
        print(f"\n📄 Generating detailed reports for top tools...")
        
        # Sort tools by mentions
        sorted_tools = sorted(active_tools.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Generate reports for top 10 tools
        top_tools = [tool for tool, _ in sorted_tools[:10]]
        
        # Import and run the separate report generator
        sys.path.insert(0, str(Path(__file__).parent))
        from separate_tool_reports import SeparateToolReportGenerator
        
        generator = SeparateToolReportGenerator()
        report_results = generator.generate_all_tool_reports(top_tools)
        
        print(f"\n" + "=" * 70)
        print("✅ COMPREHENSIVE ANALYSIS COMPLETE")
        print("=" * 70)
        
        for tool, data in report_results.items():
            print(f"📄 {tool}: {data['filename']}")
            print(f"   - {data['contracts']} contracts, {data['mentions']} mentions")
        
        # Generate summary report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"COMPREHENSIVE_SUMMARY_{timestamp}.txt"
        
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(f"# COMPREHENSIVE TOOL ANALYSIS SUMMARY\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Documents: 75\n")
            f.write(f"Total Tools Analyzed: {len(tools)}\n")
            f.write(f"Tools Found: {len(active_tools)}\n")
            f.write(f"Total Mentions: {total_mentions}\n")
            f.write(f"Total Unique Contracts: {len(total_contracts)}\n\n")
            
            f.write(f"## TOP TOOLS BY USAGE\n")
            for i, (tool, matches) in enumerate(sorted_tools[:15], 1):
                mentions = len(matches)
                contracts = set(match['document'] for match in matches)
                f.write(f"{i:2d}. {tool}: {mentions} mentions ({len(contracts)} contracts)\n")
            
            f.write(f"\n## ALL CONTRACTS WITH TOOL USAGE\n")
            for contract in sorted(total_contracts):
                f.write(f"- {contract}\n")
        
        print(f"📊 Summary Report: {summary_filename}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 