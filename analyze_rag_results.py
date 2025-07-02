"""
Analysis utility for RAG-based capability matrix results.

This script provides various analysis functions for the results generated
by the RAG pipeline, including confidence score analysis, source document
analysis, and requirement categorization.
"""

import json
import os
import argparse
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns

def load_rag_results(json_file_path: str) -> List[Dict[str, Any]]:
    """
    Load RAG results from JSON file.
    
    Args:
        json_file_path: Path to the RAG results JSON file
        
    Returns:
        List of requirement analysis results
    """
    if not os.path.exists(json_file_path):
        print(f"Error: File {json_file_path} not found")
        return []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            results = json.load(file)
        print(f"Loaded {len(results)} requirement analyses from {json_file_path}")
        return results
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_file_path}")
        return []
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return []

def analyze_confidence_scores(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze confidence scores across all requirements.
    
    Args:
        results: List of requirement analysis results
        
    Returns:
        Dictionary with confidence score statistics
    """
    confidence_scores = []
    
    for result in results:
        if "capability_match" in result and "confidence_score" in result["capability_match"]:
            confidence_scores.append(result["capability_match"]["confidence_score"])
    
    if not confidence_scores:
        return {"error": "No confidence scores found"}
    
    stats = {
        "count": len(confidence_scores),
        "mean": np.mean(confidence_scores),
        "median": np.median(confidence_scores),
        "std": np.std(confidence_scores),
        "min": np.min(confidence_scores),
        "max": np.max(confidence_scores),
        "quartiles": np.percentile(confidence_scores, [25, 50, 75]).tolist()
    }
    
    # Categorize confidence levels
    high_confidence = sum(1 for score in confidence_scores if score >= 0.8)
    medium_confidence = sum(1 for score in confidence_scores if 0.5 <= score < 0.8)
    low_confidence = sum(1 for score in confidence_scores if score < 0.5)
    
    stats["confidence_categories"] = {
        "high": high_confidence,
        "medium": medium_confidence,
        "low": low_confidence
    }
    
    return stats

def analyze_source_documents(results: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
    """
    Analyze which source documents are most frequently referenced.
    
    Args:
        results: List of requirement analysis results
        top_n: Number of top documents to display
        
    Returns:
        Dictionary with source document analysis
    """
    doc_counts = Counter()
    doc_confidence_scores = defaultdict(list)
    
    for result in results:
        if "capability_match" in result:
            capability_match = result["capability_match"]
            confidence_score = capability_match.get("confidence_score", 0)
            
            for doc in capability_match.get("source_documents", []):
                doc_counts[doc] += 1
                doc_confidence_scores[doc].append(confidence_score)
    
    # Calculate average confidence scores for each document
    doc_avg_scores = {}
    for doc, scores in doc_confidence_scores.items():
        doc_avg_scores[doc] = np.mean(scores)
    
    # Get top documents by frequency
    top_docs = doc_counts.most_common(top_n)
    
    analysis = {
        "total_unique_documents": len(doc_counts),
        "top_documents": [
            {
                "document": doc,
                "frequency": count,
                "avg_confidence": doc_avg_scores.get(doc, 0)
            }
            for doc, count in top_docs
        ]
    }
    
    return analysis

def analyze_evidence_quality(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the quality and quantity of supporting evidence.
    
    Args:
        results: List of requirement analysis results
        
    Returns:
        Dictionary with evidence quality analysis
    """
    evidence_counts = []
    evidence_lengths = []
    
    for result in results:
        if "capability_match" in result:
            evidence = result["capability_match"].get("supporting_evidence", [])
            evidence_counts.append(len(evidence))
            
            for ev in evidence:
                evidence_lengths.append(len(ev.split()))
    
    if not evidence_counts:
        return {"error": "No evidence found"}
    
    analysis = {
        "total_requirements": len(results),
        "requirements_with_evidence": sum(1 for count in evidence_counts if count > 0),
        "evidence_stats": {
            "mean_count": np.mean(evidence_counts),
            "median_count": np.median(evidence_counts),
            "max_count": np.max(evidence_counts),
            "min_count": np.min(evidence_counts)
        }
    }
    
    if evidence_lengths:
        analysis["evidence_length_stats"] = {
            "mean_length": np.mean(evidence_lengths),
            "median_length": np.median(evidence_lengths),
            "max_length": np.max(evidence_lengths),
            "min_length": np.min(evidence_lengths)
        }
    
    return analysis

def generate_summary_report(results: List[Dict[str, Any]], output_file: str = None) -> str:
    """
    Generate a comprehensive summary report.
    
    Args:
        results: List of requirement analysis results
        output_file: Optional file to save the report
        
    Returns:
        Formatted report string
    """
    if not results:
        return "No results to analyze."
    
    report_parts = []
    report_parts.append("=" * 80)
    report_parts.append("RAG CAPABILITY ANALYSIS SUMMARY REPORT")
    report_parts.append("=" * 80)
    report_parts.append("")
    
    # Basic statistics
    report_parts.append(f"Total Requirements Analyzed: {len(results)}")
    report_parts.append("")
    
    # Confidence score analysis
    confidence_stats = analyze_confidence_scores(results)
    if "error" not in confidence_stats:
        report_parts.append("CONFIDENCE SCORE ANALYSIS:")
        report_parts.append("-" * 30)
        report_parts.append(f"Mean Confidence: {confidence_stats['mean']:.3f}")
        report_parts.append(f"Median Confidence: {confidence_stats['median']:.3f}")
        report_parts.append(f"Standard Deviation: {confidence_stats['std']:.3f}")
        report_parts.append(f"Range: {confidence_stats['min']:.3f} - {confidence_stats['max']:.3f}")
        report_parts.append("")
        
        categories = confidence_stats["confidence_categories"]
        report_parts.append("Confidence Categories:")
        report_parts.append(f"  High (≥0.8): {categories['high']} requirements")
        report_parts.append(f"  Medium (0.5-0.8): {categories['medium']} requirements")
        report_parts.append(f"  Low (<0.5): {categories['low']} requirements")
        report_parts.append("")
    
    # Source document analysis
    doc_analysis = analyze_source_documents(results)
    report_parts.append("TOP SOURCE DOCUMENTS:")
    report_parts.append("-" * 30)
    report_parts.append(f"Total Unique Documents: {doc_analysis['total_unique_documents']}")
    report_parts.append("")
    
    for i, doc_info in enumerate(doc_analysis["top_documents"][:5], 1):
        report_parts.append(f"{i}. {doc_info['document']}")
        report_parts.append(f"   Frequency: {doc_info['frequency']} references")
        report_parts.append(f"   Avg Confidence: {doc_info['avg_confidence']:.3f}")
        report_parts.append("")
    
    # Evidence quality analysis
    evidence_analysis = analyze_evidence_quality(results)
    if "error" not in evidence_analysis:
        report_parts.append("EVIDENCE QUALITY ANALYSIS:")
        report_parts.append("-" * 30)
        report_parts.append(f"Requirements with Evidence: {evidence_analysis['requirements_with_evidence']}/{evidence_analysis['total_requirements']}")
        
        evidence_stats = evidence_analysis["evidence_stats"]
        report_parts.append(f"Average Evidence Count: {evidence_stats['mean_count']:.2f}")
        report_parts.append(f"Median Evidence Count: {evidence_stats['median_count']:.2f}")
        report_parts.append("")
    
    report = "\n".join(report_parts)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to {output_file}")
    
    return report

def create_visualizations(results: List[Dict[str, Any]], output_dir: str = "analysis_plots"):
    """
    Create visualizations of the analysis results.
    
    Args:
        results: List of requirement analysis results
        output_dir: Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract confidence scores
    confidence_scores = []
    for result in results:
        if "capability_match" in result and "confidence_score" in result["capability_match"]:
            confidence_scores.append(result["capability_match"]["confidence_score"])
    
    if not confidence_scores:
        print("No confidence scores found for visualization")
        return
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # 1. Confidence Score Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(confidence_scores, bins=20, alpha=0.7, edgecolor='black')
    plt.xlabel('Confidence Score')
    plt.ylabel('Frequency')
    plt.title('Distribution of Confidence Scores')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'confidence_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Confidence Score Box Plot
    plt.figure(figsize=(8, 6))
    plt.boxplot(confidence_scores)
    plt.ylabel('Confidence Score')
    plt.title('Confidence Score Distribution (Box Plot)')
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(output_dir, 'confidence_boxplot.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Source Document Frequency
    doc_analysis = analyze_source_documents(results, top_n=10)
    if doc_analysis["top_documents"]:
        docs = [doc["document"][:30] + "..." if len(doc["document"]) > 30 else doc["document"] 
                for doc in doc_analysis["top_documents"][:10]]
        frequencies = [doc["frequency"] for doc in doc_analysis["top_documents"][:10]]
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(range(len(docs)), frequencies)
        plt.yticks(range(len(docs)), docs)
        plt.xlabel('Frequency')
        plt.title('Top 10 Most Referenced Source Documents')
        plt.gca().invert_yaxis()
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                    str(frequencies[i]), va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'source_document_frequency.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    print(f"Visualizations saved to {output_dir}/")

def main():
    """Main function to run the analysis."""
    parser = argparse.ArgumentParser(description='Analyze RAG-based capability matrix results')
    parser.add_argument('--file', default='rag_requirement_matches.json', 
                        help='Path to the RAG results JSON file')
    parser.add_argument('--output', type=str,
                        help='Output file for the summary report')
    parser.add_argument('--plots', action='store_true',
                        help='Generate visualization plots')
    parser.add_argument('--plots-dir', default='analysis_plots',
                        help='Directory to save plots')
    
    args = parser.parse_args()
    
    # Load results
    results = load_rag_results(args.file)
    
    if not results:
        print("No results to analyze. Exiting.")
        return
    
    # Generate and display summary report
    report = generate_summary_report(results, args.output)
    print(report)
    
    # Generate visualizations if requested
    if args.plots:
        create_visualizations(results, args.plots_dir)

if __name__ == "__main__":
    main() 