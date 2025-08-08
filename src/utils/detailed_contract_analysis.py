#!/usr/bin/env python3
"""
Detailed Contract-Specific Tool Analysis

This script provides granular analysis of tool usage for every contract instance,
showing exactly WHERE, HOW, and WHY each tool is used in each specific contract.
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.tool_analyzer import TXTToolSearcher

class DetailedContractAnalyzer:
    """Detailed contract-specific tool usage analysis."""
    
    def __init__(self, txt_dir: str = "data/documents_txt"):
        self.txt_dir = Path(txt_dir)
        self.searcher = TXTToolSearcher(txt_dir=str(txt_dir))
        
    def analyze_contract_usage(self, tool_name: str, matches: List[Dict]) -> Dict[str, Any]:
        """Analyze tool usage for each specific contract."""
        
        # Group matches by contract
        contract_usage = {}
        
        for match in matches:
            document = match['document']
            context = match.get('context', '')
            
            if document not in contract_usage:
                contract_usage[document] = {
                    "contract_name": document,
                    "mentions": 0,
                    "usage_contexts": [],
                    "business_purposes": [],
                    "technical_implementations": [],
                    "specific_features": [],
                    "business_value": []
                }
            
            contract_usage[document]["mentions"] += 1
            
            # Extract detailed usage context
            usage_context = self._extract_usage_context(context, document)
            if usage_context:
                contract_usage[document]["usage_contexts"].append(usage_context)
            
            # Extract business purpose
            business_purpose = self._extract_business_purpose(context, document)
            if business_purpose:
                contract_usage[document]["business_purposes"].append(business_purpose)
            
            # Extract technical implementation
            tech_impl = self._extract_technical_details(context, document)
            if tech_impl:
                contract_usage[document]["technical_implementations"].append(tech_impl)
            
            # Extract specific features
            features = self._extract_specific_features(context, document)
            if features:
                contract_usage[document]["specific_features"].extend(features)
            
            # Extract business value
            value = self._extract_business_value(context, document)
            if value:
                contract_usage[document]["business_value"].append(value)
        
        return contract_usage
    
    def _extract_usage_context(self, context: str, document: str) -> Dict[str, str]:
        """Extract specific usage context from the text."""
        
        # Clean and extract meaningful context
        context_clean = context.strip()
        if len(context_clean) < 50:
            return None
        
        # Extract the most relevant part (around the tool mention)
        return {
            "context": context_clean[:300] + "..." if len(context_clean) > 300 else context_clean,
            "document": document
        }
    
    def _extract_business_purpose(self, context: str, document: str) -> Dict[str, str]:
        """Extract the specific business purpose from context."""
        
        context_lower = context.lower()
        
        # Business purpose patterns with specific examples
        business_patterns = {
            "User Management & Authentication": ["user", "authentication", "login", "access", "identity"],
            "Data Processing & Analytics": ["data", "analytics", "processing", "analysis", "reporting"],
            "Service Management & Ticketing": ["service", "ticket", "support", "helpdesk", "incident"],
            "Security & Compliance": ["security", "compliance", "audit", "encryption", "protection"],
            "Integration & Workflow": ["integration", "workflow", "process", "automation", "api"],
            "Monitoring & Performance": ["monitoring", "performance", "tracking", "metrics", "dashboard"],
            "Storage & Backup": ["storage", "backup", "archive", "file", "bucket"],
            "Deployment & Infrastructure": ["deployment", "infrastructure", "cloud", "serverless", "scaling"]
        }
        
        for purpose, keywords in business_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return {
                    "purpose": purpose,
                    "context": context[:200] + "..." if len(context) > 200 else context,
                    "document": document
                }
        
        return None
    
    def _extract_technical_details(self, context: str, document: str) -> Dict[str, str]:
        """Extract technical implementation details."""
        
        context_lower = context.lower()
        
        # Technical implementation patterns
        tech_patterns = {
            "Serverless Architecture": ["lambda", "serverless", "function", "event-driven"],
            "Microservices": ["microservice", "container", "docker", "kubernetes"],
            "Cloud Infrastructure": ["aws", "cloud", "infrastructure", "scalable"],
            "API Integration": ["api", "rest", "endpoint", "integration"],
            "Database Management": ["database", "rds", "query", "sql", "oracle"],
            "Security Implementation": ["iam", "encryption", "authentication", "authorization"],
            "Monitoring & Logging": ["logging", "monitoring", "tracking", "analytics"],
            "DevOps & CI/CD": ["devops", "ci/cd", "jenkins", "github", "terraform"]
        }
        
        for tech_type, keywords in tech_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return {
                    "type": tech_type,
                    "details": context[:250] + "..." if len(context) > 250 else context,
                    "document": document
                }
        
        return None
    
    def _extract_specific_features(self, context: str, document: str) -> List[str]:
        """Extract specific features or capabilities mentioned."""
        
        context_lower = context.lower()
        features = []
        
        # Feature patterns
        feature_patterns = {
            "Ticketing System": ["ticket", "incident", "request", "workflow"],
            "Dashboard & Reporting": ["dashboard", "report", "metrics", "analytics"],
            "User Authentication": ["authentication", "login", "identity", "access"],
            "Data Storage": ["storage", "bucket", "file", "backup"],
            "API Management": ["api", "endpoint", "integration", "rest"],
            "Security Controls": ["security", "encryption", "iam", "compliance"],
            "Monitoring Tools": ["monitoring", "logging", "tracking", "alerting"],
            "Automation": ["automation", "workflow", "process", "scheduled"]
        }
        
        for feature, keywords in feature_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                features.append(feature)
        
        return features
    
    def _extract_business_value(self, context: str, document: str) -> Dict[str, str]:
        """Extract business value and outcomes."""
        
        context_lower = context.lower()
        
        # Business value patterns
        value_patterns = {
            "Cost Savings": ["savings", "cost", "efficiency", "optimization", "reduction"],
            "Performance Improvement": ["performance", "speed", "efficiency", "optimization"],
            "Security Enhancement": ["security", "protection", "compliance", "safeguard"],
            "Scalability": ["scalable", "scaling", "growth", "expansion"],
            "User Experience": ["user experience", "interface", "usability", "accessibility"],
            "Compliance": ["compliance", "audit", "regulatory", "governance"],
            "Automation": ["automation", "efficiency", "productivity", "streamline"],
            "Integration": ["integration", "connectivity", "workflow", "seamless"]
        }
        
        for value_type, keywords in value_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return {
                    "value_type": value_type,
                    "context": context[:200] + "..." if len(context) > 200 else context,
                    "document": document
                }
        
        return None
    
    def generate_detailed_report(self, tools: List[str]) -> str:
        """Generate detailed contract-specific report."""
        
        print("🔍 Running Detailed Contract-Specific Analysis...")
        
        # Get raw results
        raw_results = self.searcher.search_all_documents(tools)
        
        # Analyze each tool
        detailed_analysis = {}
        
        for tool, matches in raw_results.items():
            if matches:
                detailed_analysis[tool] = self.analyze_contract_usage(tool, matches)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# DETAILED CONTRACT-SPECIFIC TOOL USAGE ANALYSIS
Generated: {timestamp}

## Executive Summary
This report provides granular analysis of tool usage for every contract instance,
showing exactly WHERE, HOW, and WHY each tool is used in each specific contract.

## Analysis Methodology
- **Contract-Specific Analysis**: Detailed breakdown for each contract where tools are used
- **Business Context Extraction**: Specific business purposes and value for each usage
- **Technical Implementation Details**: How tools are technically implemented in each contract
- **Feature Mapping**: Specific features and capabilities used in each contract

"""
        
        for tool, contract_analysis in detailed_analysis.items():
            report += f"""
## {tool.upper()}
**Total Contracts**: {len(contract_analysis)}
**Total Mentions**: {sum(contract['mentions'] for contract in contract_analysis.values())}

"""
            
            # Sort contracts by number of mentions
            sorted_contracts = sorted(contract_analysis.items(), 
                                    key=lambda x: x[1]['mentions'], reverse=True)
            
            for contract_name, contract_data in sorted_contracts:
                report += f"""
### Contract: {contract_name}
**Mentions**: {contract_data['mentions']}

#### WHERE is it used in this contract?
**Usage Contexts:**
"""
                
                for context in contract_data['usage_contexts'][:3]:  # Show top 3
                    report += f"- {context['context']}\n"
                
                report += f"""
#### HOW is it used in this contract?
**Technical Implementations:**
"""
                
                for tech in contract_data['technical_implementations'][:3]:  # Show top 3
                    report += f"- **{tech['type']}**: {tech['details']}\n"
                
                report += f"""
**Specific Features Used:**
"""
                
                unique_features = list(set(contract_data['specific_features']))
                for feature in unique_features[:5]:  # Show top 5 features
                    report += f"- {feature}\n"
                
                report += f"""
#### WHY is it used in this contract?
**Business Purposes:**
"""
                
                for purpose in contract_data['business_purposes'][:3]:  # Show top 3
                    report += f"- **{purpose['purpose']}**: {purpose['context']}\n"
                
                report += f"""
**Business Value Delivered:**
"""
                
                for value in contract_data['business_value'][:3]:  # Show top 3
                    report += f"- **{value['value_type']}**: {value['context']}\n"
                
                report += f"""
---
"""
        
        # Add cross-contract analysis
        report += f"""
## Cross-Contract Analysis

### Tool Usage by Contract Type:
"""
        
        for tool, contract_analysis in detailed_analysis.items():
            report += f"""
**{tool}**:
"""
            
            # Group by contract type
            contract_types = {}
            for contract_name, contract_data in contract_analysis.items():
                contract_type = self._get_contract_type(contract_name)
                if contract_type not in contract_types:
                    contract_types[contract_type] = []
                contract_types[contract_type].append({
                    "name": contract_name,
                    "mentions": contract_data['mentions']
                })
            
            for contract_type, contracts in contract_types.items():
                total_mentions = sum(c['mentions'] for c in contracts)
                report += f"- **{contract_type}**: {total_mentions} mentions across {len(contracts)} contracts\n"
        
        report += f"""
### Key Insights by Contract:

"""
        
        for tool, contract_analysis in detailed_analysis.items():
            report += f"""
**{tool} - Contract-Specific Insights:**
"""
            
            # Find most intensive usage
            most_intensive = max(contract_analysis.items(), key=lambda x: x[1]['mentions'])
            report += f"- **Most Intensive Usage**: {most_intensive[0]} ({most_intensive[1]['mentions']} mentions)\n"
            
            # Find most diverse usage
            most_diverse = max(contract_analysis.items(), 
                             key=lambda x: len(set(x[1]['specific_features'])))
            report += f"- **Most Feature-Rich Usage**: {most_diverse[0]} ({len(set(most_diverse[1]['specific_features']))} features)\n"
            
            # Find highest business value
            highest_value = max(contract_analysis.items(), 
                              key=lambda x: len(x[1]['business_value']))
            report += f"- **Highest Business Value**: {highest_value[0]} ({len(highest_value[1]['business_value'])} value types)\n"
        
        return report
    
    def _get_contract_type(self, contract_name: str) -> str:
        """Categorize contract by type."""
        
        if "MIDAS" in contract_name:
            return "Data Management & Analytics"
        elif "NPPES" in contract_name:
            return "Provider Enrollment"
        elif "DEX" in contract_name:
            return "Data Exchange"
        elif "MED" in contract_name:
            return "Medical Data"
        elif "EAOS" in contract_name:
            return "Enterprise Architecture"
        elif "CPI" in contract_name:
            return "Consumer Price Index"
        elif "CMS" in contract_name:
            return "CMS Operations"
        elif "CDC" in contract_name:
            return "CDC Health Data"
        elif "TSA" in contract_name:
            return "Transportation Security"
        else:
            return "Other Government Services"
    
    def generate_detailed_matrix(self, tools: List[str]) -> str:
        """Generate detailed Excel-compatible matrix."""
        
        print("📊 Generating Detailed Contract Matrix...")
        
        # Get raw results
        raw_results = self.searcher.search_all_documents(tools)
        
        # Create matrix data
        matrix_data = []
        
        for tool, matches in raw_results.items():
            if matches:
                contract_analysis = self.analyze_contract_usage(tool, matches)
                
                for contract_name, contract_data in contract_analysis.items():
                    # Create detailed row for each contract-tool combination
                    row = {
                        "Tool": tool,
                        "Contract": contract_name,
                        "Contract_Type": self._get_contract_type(contract_name),
                        "Mentions": contract_data['mentions'],
                        "Business_Purposes": "; ".join(list(set([p['purpose'] for p in contract_data['business_purposes']]))),
                        "Technical_Implementations": "; ".join(list(set([t['type'] for t in contract_data['technical_implementations']]))),
                        "Specific_Features": "; ".join(list(set(contract_data['specific_features']))),
                        "Business_Value": "; ".join(list(set([v['value_type'] for v in contract_data['business_value']]))),
                        "Usage_Context": contract_data['usage_contexts'][0]['context'] if contract_data['usage_contexts'] else "",
                        "Primary_Business_Purpose": contract_data['business_purposes'][0]['purpose'] if contract_data['business_purposes'] else "",
                        "Primary_Technical_Type": contract_data['technical_implementations'][0]['type'] if contract_data['technical_implementations'] else "",
                        "Key_Business_Value": contract_data['business_value'][0]['value_type'] if contract_data['business_value'] else ""
                    }
                    matrix_data.append(row)
        
        return matrix_data
    
    def save_detailed_analysis(self, tools: List[str]) -> Dict[str, str]:
        """Save detailed analysis results."""
        
        print("💾 Saving detailed analysis results...")
        
        # Generate detailed report
        report = self.generate_detailed_report(tools)
        
        # Generate matrix data
        matrix_data = self.generate_detailed_matrix(tools)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"DETAILED_CONTRACT_ANALYSIS_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save matrix data as JSON
        json_filename = f"DETAILED_CONTRACT_MATRIX_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, indent=2, ensure_ascii=False)
        
        # Save matrix data as CSV
        csv_filename = f"DETAILED_CONTRACT_MATRIX_{timestamp}.csv"
        import csv
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if matrix_data:
                writer = csv.DictWriter(f, fieldnames=matrix_data[0].keys())
                writer.writeheader()
                writer.writerows(matrix_data)
        
        return {
            "report_filename": report_filename,
            "json_filename": json_filename,
            "csv_filename": csv_filename,
            "report_content": report,
            "matrix_data": matrix_data
        }

def main():
    """Run detailed contract-specific analysis."""
    print("🔍 Starting Detailed Contract-Specific Tool Analysis")
    print("=" * 70)
    
    # Define tools to analyze
    tools = ['ServiceNow', 'Databricks', 'Redhat', 'AWS S3', 'AWS Lambda']
    
    print(f"📋 Analyzing tools: {', '.join(tools)}")
    print("🔍 Extracting WHERE, HOW, and WHY for every contract instance...")
    
    try:
        analyzer = DetailedContractAnalyzer()
        results = analyzer.save_detailed_analysis(tools)
        
        print("\n" + "=" * 70)
        print("✅ DETAILED ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"📄 Detailed Report: {results['report_filename']}")
        print(f"📊 JSON Matrix: {results['json_filename']}")
        print(f"📈 CSV Matrix: {results['csv_filename']}")
        
        # Print summary
        print(f"\n📊 Matrix Summary:")
        print(f"- Total Contract-Tool Combinations: {len(results['matrix_data'])}")
        
        # Group by tool
        tool_summary = {}
        for row in results['matrix_data']:
            tool = row['Tool']
            if tool not in tool_summary:
                tool_summary[tool] = {'contracts': 0, 'mentions': 0}
            tool_summary[tool]['contracts'] += 1
            tool_summary[tool]['mentions'] += row['Mentions']
        
        for tool, summary in tool_summary.items():
            print(f"- {tool}: {summary['contracts']} contracts, {summary['mentions']} total mentions")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 