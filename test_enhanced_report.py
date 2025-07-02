#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced executive report generation.
This script creates a sample analysis and generates the comprehensive report.
"""

import json
import os
from datetime import datetime
from rag_pipeline import RAGCapabilityAnalyzer

def create_sample_analysis_data():
    """Create sample analysis data for testing the enhanced report."""
    sample_results = [
        {
            "requirement": "Implement NIST Risk Management Framework (SP 800-37, 800-30, 800-39) for enterprise risk assessment and mitigation.",
            "rating": "",
            "confidence_score": 0.85,
            "supporting_evidence": [
                {
                    "text": "We provide comprehensive risk analysis and guidance, secure baseline configuration guidance, and security tool training and support. As part of our work, we perform cybersecurity and privacy research, and prepare presentations and reports for policy and documentation updates to support the NCHS Risk Management Program.",
                    "source": "PP_Consolidated_CDC NCHS RMF.pdf"
                },
                {
                    "text": "Our team delivers information security services, guidance, and training to CDC information security stakeholders in the areas of cybersecurity risk and compliance management, Security Assessment and Authorization (SA&A) audit analysis and support.",
                    "source": "PP_Consolidated_CDC NCHS RMF.pdf"
                }
            ],
            "reasoning": "Strong alignment with NIST RMF requirements. Our experience includes risk analysis, compliance management, and SA&A processes that directly map to the NIST framework components.",
            "past_performance_text": "Confidence: 0.85\nStrong alignment with NIST RMF requirements..."
        },
        {
            "requirement": "Design and implement Zero Trust architecture with continuous monitoring and adaptive access controls.",
            "rating": "",
            "confidence_score": 0.75,
            "supporting_evidence": [
                {
                    "text": "We review system architecture designs, planned security controls, and proposed interconnection security agreements to ensure appropriate configurations and controls are established for secure data management.",
                    "source": "PP_Consolidated_CDC NCHS RMF.pdf"
                },
                {
                    "text": "Utilized 2 factor authentication during identification, authentication, and authorization for remote access.",
                    "source": "TSA VAD.pdf"
                }
            ],
            "reasoning": "Good experience with secure architecture design and multi-factor authentication. While Zero Trust terminology is not explicitly mentioned, our security architecture and access control experience provides a strong foundation.",
            "past_performance_text": "Confidence: 0.75\nGood experience with secure architecture design..."
        },
        {
            "requirement": "Develop and maintain comprehensive incident response playbooks with automated threat hunting capabilities.",
            "rating": "",
            "confidence_score": 0.60,
            "supporting_evidence": [
                {
                    "text": "Incident management is facilitated through JIRA, with tickets logged, services restored, resolutions documented, and tickets closed.",
                    "source": "CMS_MRAC_Consolidated.pdf"
                }
            ],
            "reasoning": "Basic incident management processes are in place, but lacks specific playbook development and automated threat hunting experience. Moderate capability with room for enhancement.",
            "past_performance_text": "Confidence: 0.60\nBasic incident management processes are in place..."
        },
        {
            "requirement": "Implement advanced data analytics and machine learning for predictive security analytics.",
            "rating": "",
            "confidence_score": 0.45,
            "supporting_evidence": [
                {
                    "text": "We translate complex quantitative analytic findings into automated, user-friendly reports, dashboards, and visualizations, enabling stakeholders to access and interpret data easily.",
                    "source": "PP_Consolidated_CDC Data Management DHP.pdf"
                }
            ],
            "reasoning": "Some experience with data analytics and reporting, but limited evidence of machine learning or predictive analytics specifically for security applications.",
            "past_performance_text": "Confidence: 0.45\nSome experience with data analytics and reporting..."
        },
        {
            "requirement": "Establish comprehensive cloud security controls and compliance monitoring for multi-cloud environments.",
            "rating": "",
            "confidence_score": 0.30,
            "supporting_evidence": [
                {
                    "text": "Project Name: Risk Management Framework (RMF) and Cloud Security Operations Support Consulting Services",
                    "source": "PP_Consolidated_CDC NCHS RMF.pdf"
                }
            ],
            "reasoning": "Limited specific experience with cloud security controls and multi-cloud environments. While RMF experience exists, cloud-specific security implementation is not clearly demonstrated.",
            "past_performance_text": "Confidence: 0.30\nLimited specific experience with cloud security controls..."
        },
        {
            "requirement": "Deploy and manage advanced threat intelligence platforms with automated response capabilities.",
            "rating": "",
            "confidence_score": 0.20,
            "supporting_evidence": [
                {
                    "text": "Event management involves logging and forwarding logs to our security information and event management tool.",
                    "source": "CMS_MRAC_Consolidated.pdf"
                }
            ],
            "reasoning": "Very limited experience with threat intelligence platforms and automated response. Basic SIEM logging experience exists but does not demonstrate advanced threat intelligence capabilities.",
            "past_performance_text": "Confidence: 0.20\nVery limited experience with threat intelligence platforms..."
        }
    ]
    return sample_results

def test_enhanced_report():
    """Test the enhanced report generation with sample data."""
    print("🧪 Testing Enhanced Executive Report Generation")
    print("="*60)
    
    # Create sample data
    sample_results = create_sample_analysis_data()
    
    # Initialize analyzer (we won't actually use it for processing, just for report generation)
    try:
        analyzer = RAGCapabilityAnalyzer(
            provider="openai",
            model_name="gpt-3.5-turbo",
            chunk_size=1000,
            chunk_overlap=200,
            top_k_retrieval=5,
            vector_store_path="test_vector_store"
        )
        
        # Generate the enhanced report
        print("📝 Generating comprehensive executive report...")
        report_content = analyzer.generate_summary_report(sample_results)
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"DEMO_EXECUTIVE_REPORT_{timestamp}.txt"
        
        # Add header
        header = f"""
{'='*80}
DEMO: EXECUTIVE CAPABILITY ANALYSIS REPORT
Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
Analysis Mode: DEMO
Total Requirements Analyzed: {len(sample_results)}
Note: This is a demonstration using sample data
{'='*80}

"""
        
        full_report = header + report_content
        
        # Save the report
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(full_report)
        
        print(f"✅ Demo report saved to: {report_filename}")
        print("\n📋 Report Preview (first 500 characters):")
        print("-" * 60)
        print(full_report[:500] + "...")
        print("-" * 60)
        print(f"\n📄 Full report available in: {report_filename}")
        
    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        print("Note: This demo requires OpenAI API key to be set in environment variables.")

if __name__ == "__main__":
    test_enhanced_report() 