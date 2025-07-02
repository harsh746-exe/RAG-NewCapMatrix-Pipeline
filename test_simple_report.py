#!/usr/bin/env python3
"""
Test script to verify RAG pipeline is working and generate a simple report.
"""

import os
import sys
from datetime import datetime

def test_rag_pipeline():
    """Test if the RAG pipeline is working correctly."""
    print("🧪 Testing RAG Pipeline and Simple Report Generation")
    print("="*60)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from rag_pipeline import RAGCapabilityAnalyzer
        print("✅ RAG pipeline imports successful")
        
        # Test analyzer initialization
        print("🔧 Testing analyzer initialization...")
        analyzer = RAGCapabilityAnalyzer(
            provider="openai",
            model_name="gpt-3.5-turbo",
            chunk_size=1000,
            chunk_overlap=200,
            top_k_retrieval=5,
            vector_store_path="test_vector_store"
        )
        print("✅ Analyzer initialized successfully")
        
        # Test with sample data
        print("📝 Testing report generation...")
        sample_results = [
            {
                "requirement": "Implement NIST Risk Management Framework for enterprise risk assessment.",
                "confidence_score": 0.85,
                "supporting_evidence": [
                    {
                        "text": "We provide comprehensive risk analysis and guidance, secure baseline configuration guidance, and security tool training and support.",
                        "source": "PP_Consolidated_CDC NCHS RMF.pdf"
                    }
                ],
                "reasoning": "Strong alignment with NIST RMF requirements. Our experience includes risk analysis and compliance management."
            },
            {
                "requirement": "Design and implement Zero Trust architecture with continuous monitoring.",
                "confidence_score": 0.75,
                "supporting_evidence": [
                    {
                        "text": "We review system architecture designs and planned security controls to ensure appropriate configurations.",
                        "source": "PP_Consolidated_CDC NCHS RMF.pdf"
                    }
                ],
                "reasoning": "Good experience with secure architecture design. While Zero Trust terminology is not explicit, our security architecture experience provides a strong foundation."
            },
            {
                "requirement": "Deploy advanced threat intelligence platforms with automated response.",
                "confidence_score": 0.20,
                "supporting_evidence": [
                    {
                        "text": "Event management involves logging and forwarding logs to our security information and event management tool.",
                        "source": "CMS_MRAC_Consolidated.pdf"
                    }
                ],
                "reasoning": "Very limited experience with threat intelligence platforms. Basic SIEM logging experience exists but does not demonstrate advanced capabilities."
            }
        ]
        
        # Generate simple report
        report_content = analyzer.generate_summary_report(sample_results)
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"SIMPLE_TEST_REPORT_{timestamp}.txt"
        
        # Add header
        header = f"""
{'='*80}
SIMPLE EXECUTIVE CAPABILITY REPORT - TEST
Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
Analysis Mode: TEST
Total Requirements Analyzed: {len(sample_results)}
Note: This is a test using sample data
{'='*80}

"""
        
        full_report = header + report_content
        
        # Save the report
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(full_report)
        
        print(f"✅ Simple test report saved to: {report_filename}")
        print("\n📋 Report Preview (first 800 characters):")
        print("-" * 60)
        print(full_report[:800] + "...")
        print("-" * 60)
        print(f"\n📄 Full report available in: {report_filename}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please run: pip install PyPDF2 chromadb")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_rag_pipeline()
    if success:
        print("\n🎉 RAG pipeline test successful!")
        print("You can now run: python main_rag.py --mode test")
    else:
        print("\n❌ RAG pipeline test failed. Please check the errors above.")
    sys.exit(0 if success else 1) 