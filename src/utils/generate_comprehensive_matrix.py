#!/usr/bin/env python3
"""
Comprehensive Matrix Generator

This script generates a comprehensive matrix with all documents (including new ones)
showing detailed tool usage data in Excel and CSV formats.
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.tool_analyzer import TXTToolSearcher

class ComprehensiveMatrixGenerator:
    """Generate comprehensive matrix with all tool usage data."""
    
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
        elif "NIH" in contract_name:
            return "NIH Services"
        elif "ACTS" in contract_name:
            return "Administrative Services"
        elif "ASETT" in contract_name:
            return "Administrative Simplification"
        elif "RADV" in contract_name:
            return "Risk Adjustment"
        elif "HEDAS" in contract_name:
            return "Health Equity"
        else:
            return "Other Government Services"
    
    def generate_comprehensive_matrix(self, tools: List[str]) -> List[Dict]:
        """Generate comprehensive matrix data."""
        
        print("📊 Generating comprehensive matrix data...")
        
        # Get raw results
        raw_results = self.searcher.search_all_documents(tools)
        
        # Create matrix data
        matrix_data = []
        
        for tool, matches in raw_results.items():
            if matches:
                contract_analysis = self.analyze_tool_usage(tool, matches)
                
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
                        "Usage_Context": contract_data['detailed_contexts'][0]['context'] if contract_data['detailed_contexts'] else "",
                        "Primary_Business_Purpose": contract_data['business_purposes'][0]['purpose'] if contract_data['business_purposes'] else "",
                        "Primary_Technical_Type": contract_data['technical_implementations'][0]['type'] if contract_data['technical_implementations'] else "",
                        "Key_Business_Value": contract_data['business_value'][0]['value_type'] if contract_data['business_value'] else "",
                        "Usage_Intensity": "High" if contract_data['mentions'] > 20 else "Medium" if contract_data['mentions'] > 5 else "Low",
                        "Feature_Count": len(set(contract_data['specific_features'])),
                        "Value_Count": len(set([v['value_type'] for v in contract_data['business_value']])),
                        "Context_Count": len(contract_data['detailed_contexts'])
                    }
                    matrix_data.append(row)
        
        return matrix_data
    
    def save_matrix_files(self, matrix_data: List[Dict]) -> Dict[str, str]:
        """Save matrix data in multiple formats."""
        
        print("💾 Saving matrix files...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_filename = f"COMPREHENSIVE_MATRIX_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_filename = f"COMPREHENSIVE_MATRIX_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if matrix_data:
                writer = csv.DictWriter(f, fieldnames=matrix_data[0].keys())
                writer.writeheader()
                writer.writerows(matrix_data)
        
        # Save as Excel (if pandas is available)
        try:
            import pandas as pd
            excel_filename = f"COMPREHENSIVE_MATRIX_{timestamp}.xlsx"
            df = pd.DataFrame(matrix_data)
            df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f"✅ Excel file created: {excel_filename}")
        except ImportError:
            excel_filename = None
            print("⚠️  Excel file not created (pandas not available)")
        
        return {
            "json_filename": json_filename,
            "csv_filename": csv_filename,
            "excel_filename": excel_filename,
            "matrix_data": matrix_data
        }

def main():
    """Generate comprehensive matrix with all documents."""
    print("🔍 Starting Comprehensive Matrix Generation")
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
        # Initialize the matrix generator
        generator = ComprehensiveMatrixGenerator()
        
        # Generate matrix data
        matrix_data = generator.generate_comprehensive_matrix(tools)
        
        # Save matrix files
        results = generator.save_matrix_files(matrix_data)
        
        print(f"\n" + "=" * 70)
        print("✅ COMPREHENSIVE MATRIX COMPLETE")
        print("=" * 70)
        
        print(f"📊 Matrix Summary:")
        print(f"- Total Contract-Tool Combinations: {len(matrix_data)}")
        print(f"- Total Tools Found: {len(set(row['Tool'] for row in matrix_data))}")
        print(f"- Total Contracts: {len(set(row['Contract'] for row in matrix_data))}")
        
        # Group by tool
        tool_summary = {}
        for row in matrix_data:
            tool = row['Tool']
            if tool not in tool_summary:
                tool_summary[tool] = {'contracts': 0, 'mentions': 0}
            tool_summary[tool]['contracts'] += 1
            tool_summary[tool]['mentions'] += row['Mentions']
        
        print(f"\n📈 Tool Usage Summary:")
        for tool, summary in sorted(tool_summary.items(), key=lambda x: x[1]['mentions'], reverse=True):
            print(f"- {tool}: {summary['contracts']} contracts, {summary['mentions']} total mentions")
        
        print(f"\n📄 Generated Files:")
        print(f"- JSON Matrix: {results['json_filename']}")
        print(f"- CSV Matrix: {results['csv_filename']}")
        if results['excel_filename']:
            print(f"- Excel Matrix: {results['excel_filename']}")
        
        # Generate summary statistics
        total_mentions = sum(row['Mentions'] for row in matrix_data)
        avg_mentions = total_mentions / len(matrix_data) if matrix_data else 0
        
        print(f"\n📊 Matrix Statistics:")
        print(f"- Average mentions per contract-tool combination: {avg_mentions:.1f}")
        print(f"- High intensity usage: {len([row for row in matrix_data if row['Usage_Intensity'] == 'High'])} combinations")
        print(f"- Medium intensity usage: {len([row for row in matrix_data if row['Usage_Intensity'] == 'Medium'])} combinations")
        print(f"- Low intensity usage: {len([row for row in matrix_data if row['Usage_Intensity'] == 'Low'])} combinations")
        
    except Exception as e:
        print(f"❌ Matrix generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 