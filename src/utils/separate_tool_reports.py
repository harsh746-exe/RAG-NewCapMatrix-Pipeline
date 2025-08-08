#!/usr/bin/env python3
"""
Separate Tool Reports Generator

This script generates individual detailed reports for each tool,
providing focused analysis that is clear and easy to understand.
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

class SeparateToolReportGenerator:
    """Generate separate detailed reports for each tool."""
    
    def __init__(self, txt_dir: str = "data/documents_txt"):
        self.txt_dir = Path(txt_dir)
        self.searcher = TXTToolSearcher(txt_dir=str(txt_dir))
        
    def analyze_tool_usage(self, tool_name: str, matches: List[Dict]) -> Dict[str, Any]:
        """Analyze detailed usage for a specific tool."""
        
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
                    "business_value": [],
                    "detailed_contexts": []
                }
            
            contract_usage[document]["mentions"] += 1
            
            # Store detailed context
            if context.strip():
                contract_usage[document]["detailed_contexts"].append({
                    "context": context.strip(),
                    "length": len(context.strip())
                })
            
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
    
    def _extract_business_purpose(self, context: str, document: str) -> Dict[str, str]:
        """Extract the specific business purpose from context."""
        
        context_lower = context.lower()
        
        # Business purpose patterns
        business_patterns = {
            "User Management & Authentication": ["user", "authentication", "login", "access", "identity", "enrollment"],
            "Data Processing & Analytics": ["data", "analytics", "processing", "analysis", "reporting", "warehouse"],
            "Service Management & Ticketing": ["service", "ticket", "support", "helpdesk", "incident", "request"],
            "Security & Compliance": ["security", "compliance", "audit", "encryption", "protection", "ato"],
            "Integration & Workflow": ["integration", "workflow", "process", "automation", "api", "orchestration"],
            "Monitoring & Performance": ["monitoring", "performance", "tracking", "metrics", "dashboard", "logging"],
            "Storage & Backup": ["storage", "backup", "archive", "file", "bucket", "lake"],
            "Deployment & Infrastructure": ["deployment", "infrastructure", "cloud", "serverless", "scaling", "migration"]
        }
        
        for purpose, keywords in business_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return {
                    "purpose": purpose,
                    "context": context[:300] + "..." if len(context) > 300 else context,
                    "document": document
                }
        
        return None
    
    def _extract_technical_details(self, context: str, document: str) -> Dict[str, str]:
        """Extract technical implementation details."""
        
        context_lower = context.lower()
        
        # Technical implementation patterns
        tech_patterns = {
            "Serverless Architecture": ["lambda", "serverless", "function", "event-driven", "faas"],
            "Microservices": ["microservice", "container", "docker", "kubernetes", "pod"],
            "Cloud Infrastructure": ["aws", "cloud", "infrastructure", "scalable", "ec2", "s3"],
            "API Integration": ["api", "rest", "endpoint", "integration", "gateway"],
            "Database Management": ["database", "rds", "query", "sql", "oracle", "postgresql"],
            "Security Implementation": ["iam", "encryption", "authentication", "authorization", "vpc"],
            "Monitoring & Logging": ["logging", "monitoring", "tracking", "analytics", "cloudwatch"],
            "DevOps & CI/CD": ["devops", "ci/cd", "jenkins", "github", "terraform", "ansible"]
        }
        
        for tech_type, keywords in tech_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return {
                    "type": tech_type,
                    "details": context[:400] + "..." if len(context) > 400 else context,
                    "document": document
                }
        
        return None
    
    def _extract_specific_features(self, context: str, document: str) -> List[str]:
        """Extract specific features or capabilities mentioned."""
        
        context_lower = context.lower()
        features = []
        
        # Feature patterns
        feature_patterns = {
            "Ticketing System": ["ticket", "incident", "request", "workflow", "service desk"],
            "Dashboard & Reporting": ["dashboard", "report", "metrics", "analytics", "visualization"],
            "User Authentication": ["authentication", "login", "identity", "access", "sso"],
            "Data Storage": ["storage", "bucket", "file", "backup", "lake", "warehouse"],
            "API Management": ["api", "endpoint", "integration", "rest", "graphql"],
            "Security Controls": ["security", "encryption", "iam", "compliance", "firewall"],
            "Monitoring Tools": ["monitoring", "logging", "tracking", "alerting", "observability"],
            "Automation": ["automation", "workflow", "process", "scheduled", "orchestration"],
            "Data Processing": ["processing", "etl", "transformation", "pipeline", "streaming"],
            "Machine Learning": ["ml", "machine learning", "ai", "model", "prediction"]
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
            "Cost Savings": ["savings", "cost", "efficiency", "optimization", "reduction", "budget"],
            "Performance Improvement": ["performance", "speed", "efficiency", "optimization", "faster"],
            "Security Enhancement": ["security", "protection", "compliance", "safeguard", "secure"],
            "Scalability": ["scalable", "scaling", "growth", "expansion", "elastic"],
            "User Experience": ["user experience", "interface", "usability", "accessibility", "ux"],
            "Compliance": ["compliance", "audit", "regulatory", "governance", "certification"],
            "Automation": ["automation", "efficiency", "productivity", "streamline", "manual"],
            "Integration": ["integration", "connectivity", "workflow", "seamless", "unified"]
        }
        
        for value_type, keywords in value_patterns.items():
            if any(keyword in context_lower for keyword in keywords):
                return {
                    "value_type": value_type,
                    "context": context[:300] + "..." if len(context) > 300 else context,
                    "document": document
                }
        
        return None
    
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
    
    def generate_tool_report(self, tool_name: str, contract_analysis: Dict[str, Any]) -> str:
        """Generate detailed report for a specific tool."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate summary statistics
        total_contracts = len(contract_analysis)
        total_mentions = sum(contract['mentions'] for contract in contract_analysis.values())
        
        # Sort contracts by mentions
        sorted_contracts = sorted(contract_analysis.items(), 
                                key=lambda x: x[1]['mentions'], reverse=True)
        
        # Analyze business purposes
        business_purposes = {}
        for contract_data in contract_analysis.values():
            for purpose in contract_data['business_purposes']:
                purpose_name = purpose['purpose']
                if purpose_name not in business_purposes:
                    business_purposes[purpose_name] = 0
                business_purposes[purpose_name] += 1
        
        # Analyze technical implementations
        tech_implementations = {}
        for contract_data in contract_analysis.values():
            for tech in contract_data['technical_implementations']:
                tech_type = tech['type']
                if tech_type not in tech_implementations:
                    tech_implementations[tech_type] = 0
                tech_implementations[tech_type] += 1
        
        # Analyze business value
        business_values = {}
        for contract_data in contract_analysis.values():
            for value in contract_data['business_value']:
                value_type = value['value_type']
                if value_type not in business_values:
                    business_values[value_type] = 0
                business_values[value_type] += 1
        
        # Generate report
        report = f"""
# {tool_name.upper()} - DETAILED USAGE ANALYSIS REPORT
Generated: {timestamp}

## EXECUTIVE SUMMARY
- **Total Contracts Using {tool_name}**: {total_contracts}
- **Total Mentions**: {total_mentions}
- **Average Mentions per Contract**: {total_mentions/total_contracts:.1f}

## BUSINESS IMPACT ANALYSIS

### Primary Business Purposes
"""
        
        # Sort business purposes by frequency
        sorted_purposes = sorted(business_purposes.items(), key=lambda x: x[1], reverse=True)
        for purpose, count in sorted_purposes:
            percentage = (count / total_contracts) * 100
            report += f"- **{purpose}**: {count} contracts ({percentage:.1f}%)\n"
        
        report += f"""
### Technical Implementation Patterns
"""
        
        # Sort technical implementations by frequency
        sorted_tech = sorted(tech_implementations.items(), key=lambda x: x[1], reverse=True)
        for tech_type, count in sorted_tech:
            percentage = (count / total_contracts) * 100
            report += f"- **{tech_type}**: {count} contracts ({percentage:.1f}%)\n"
        
        report += f"""
### Business Value Delivered
"""
        
        # Sort business values by frequency
        sorted_values = sorted(business_values.items(), key=lambda x: x[1], reverse=True)
        for value_type, count in sorted_values:
            percentage = (count / total_contracts) * 100
            report += f"- **{value_type}**: {count} contracts ({percentage:.1f}%)\n"
        
        report += f"""
## CONTRACT-BY-CONTRACT DETAILED ANALYSIS

### Top Contracts by Usage Intensity
"""
        
        # Show top 10 contracts
        for i, (contract_name, contract_data) in enumerate(sorted_contracts[:10], 1):
            report += f"""
#### {i}. {contract_name}
**Contract Type**: {self._get_contract_type(contract_name)}
**Mentions**: {contract_data['mentions']}
**Usage Intensity**: {'🔴 High' if contract_data['mentions'] > 20 else '🟡 Medium' if contract_data['mentions'] > 5 else '🟢 Low'}

##### WHERE is {tool_name} used in this contract?
"""
            
            # Show detailed contexts (top 3)
            detailed_contexts = sorted(contract_data['detailed_contexts'], 
                                     key=lambda x: x['length'], reverse=True)
            for j, context_data in enumerate(detailed_contexts[:3], 1):
                report += f"**Context {j}**: {context_data['context']}\n\n"
            
            report += f"##### HOW is {tool_name} used in this contract?\n"
            
            # Show technical implementations
            unique_tech_types = list(set([tech['type'] for tech in contract_data['technical_implementations']]))
            for tech_type in unique_tech_types[:3]:
                tech_details = [tech for tech in contract_data['technical_implementations'] if tech['type'] == tech_type]
                if tech_details:
                    report += f"- **{tech_type}**: {tech_details[0]['details']}\n"
            
            # Show specific features
            unique_features = list(set(contract_data['specific_features']))
            if unique_features:
                report += f"\n**Specific Features Used**: {', '.join(unique_features[:5])}\n"
            
            report += f"\n##### WHY is {tool_name} used in this contract?\n"
            
            # Show business purposes
            unique_purposes = list(set([purpose['purpose'] for purpose in contract_data['business_purposes']]))
            for purpose in unique_purposes[:3]:
                report += f"- **{purpose}**: Primary business purpose\n"
            
            # Show business value
            unique_values = list(set([value['value_type'] for value in contract_data['business_value']]))
            for value_type in unique_values[:3]:
                report += f"- **{value_type}**: Key business value delivered\n"
            
            report += f"\n---\n"
        
        # Show remaining contracts in summary
        if len(sorted_contracts) > 10:
            report += f"""
### Remaining Contracts (Summary)
"""
            for contract_name, contract_data in sorted_contracts[10:]:
                report += f"- **{contract_name}**: {contract_data['mentions']} mentions ({self._get_contract_type(contract_name)})\n"
        
        report += f"""
## CONTRACT TYPE ANALYSIS

### Usage by Contract Category
"""
        
        # Group by contract type
        contract_types = {}
        for contract_name, contract_data in contract_analysis.items():
            contract_type = self._get_contract_type(contract_name)
            if contract_type not in contract_types:
                contract_types[contract_type] = {'contracts': 0, 'mentions': 0}
            contract_types[contract_type]['contracts'] += 1
            contract_types[contract_type]['mentions'] += contract_data['mentions']
        
        for contract_type, data in sorted(contract_types.items(), key=lambda x: x[1]['mentions'], reverse=True):
            report += f"- **{contract_type}**: {data['mentions']} mentions across {data['contracts']} contracts\n"
        
        report += f"""
## KEY INSIGHTS & RECOMMENDATIONS

### Most Intensive Usage
- **Contract**: {sorted_contracts[0][0]} ({sorted_contracts[0][1]['mentions']} mentions)
- **Primary Purpose**: {sorted_contracts[0][1]['business_purposes'][0]['purpose'] if sorted_contracts[0][1]['business_purposes'] else 'Not specified'}

### Most Feature-Rich Implementation
"""
        
        # Find contract with most features
        most_features_contract = max(contract_analysis.items(), 
                                   key=lambda x: len(set(x[1]['specific_features'])))
        report += f"- **Contract**: {most_features_contract[0]} ({len(set(most_features_contract[1]['specific_features']))} features)\n"
        
        report += f"""
### Highest Business Value
"""
        
        # Find contract with most business value types
        most_value_contract = max(contract_analysis.items(), 
                                key=lambda x: len(set([v['value_type'] for v in x[1]['business_value']])))
        report += f"- **Contract**: {most_value_contract[0]} ({len(set([v['value_type'] for v in most_value_contract[1]['business_value']]))} value types)\n"
        
        report += f"""
## TECHNICAL ARCHITECTURE PATTERNS

### Common Integration Patterns
"""
        
        # Analyze integration patterns
        api_integrations = sum(1 for contract_data in contract_analysis.values() 
                             for tech in contract_data['technical_implementations'] 
                             if tech['type'] == 'API Integration')
        cloud_infrastructure = sum(1 for contract_data in contract_analysis.values() 
                                 for tech in contract_data['technical_implementations'] 
                                 if tech['type'] == 'Cloud Infrastructure')
        
        report += f"- **API Integration**: {api_integrations} contracts\n"
        report += f"- **Cloud Infrastructure**: {cloud_infrastructure} contracts\n"
        
        report += f"""
## BUSINESS VALUE MATRIX

### Value Delivery by Contract Type
"""
        
        for contract_type, data in contract_types.items():
            report += f"- **{contract_type}**: {data['mentions']} total mentions, {data['contracts']} contracts\n"
        
        report += f"""
---
*Report generated automatically from contract analysis data*
"""
        
        return report
    
    def generate_all_tool_reports(self, tools: List[str]) -> Dict[str, str]:
        """Generate separate reports for all tools."""
        
        print("🔍 Generating separate detailed reports for each tool...")
        
        # Get raw results
        raw_results = self.searcher.search_all_documents(tools)
        
        # Generate reports for each tool
        report_files = {}
        
        for tool, matches in raw_results.items():
            if matches:
                print(f"📄 Generating report for {tool}...")
                
                # Analyze tool usage
                contract_analysis = self.analyze_tool_usage(tool, matches)
                
                # Generate report
                report_content = self.generate_tool_report(tool, contract_analysis)
                
                # Save report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"{tool.upper()}_DETAILED_REPORT_{timestamp}.txt"
                
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                report_files[tool] = {
                    "filename": report_filename,
                    "content": report_content,
                    "contracts": len(contract_analysis),
                    "mentions": sum(contract['mentions'] for contract in contract_analysis.values())
                }
                
                print(f"✅ {tool}: {len(contract_analysis)} contracts, {sum(contract['mentions'] for contract in contract_analysis.values())} mentions")
        
        return report_files

def main():
    """Generate separate detailed reports for each tool."""
    print("🔍 Starting Separate Tool Report Generation")
    print("=" * 60)
    
    # Define tools to analyze
    tools = ['ServiceNow', 'Databricks', 'Redhat', 'AWS S3', 'AWS Lambda']
    
    print(f"📋 Generating reports for: {', '.join(tools)}")
    print("📄 Creating individual detailed reports for each tool...")
    
    try:
        generator = SeparateToolReportGenerator()
        results = generator.generate_all_tool_reports(tools)
        
        print("\n" + "=" * 60)
        print("✅ SEPARATE TOOL REPORTS COMPLETE")
        print("=" * 60)
        
        for tool, data in results.items():
            print(f"📄 {tool}: {data['filename']}")
            print(f"   - {data['contracts']} contracts, {data['mentions']} mentions")
        
        print(f"\n📊 Summary:")
        total_contracts = sum(data['contracts'] for data in results.values())
        total_mentions = sum(data['mentions'] for data in results.values())
        print(f"- Total unique contracts: {total_contracts}")
        print(f"- Total tool mentions: {total_mentions}")
        print(f"- Reports generated: {len(results)}")
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 