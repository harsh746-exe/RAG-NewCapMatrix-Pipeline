"""
RAG Pipeline for Capability Matrix Analysis

This module implements a Retrieval-Augmented Generation (RAG) pipeline to replace
the current embedding-based similarity approach. It provides better contextual
understanding by using LLM evaluation of retrieved chunks from past contracts.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pickle
import time
from collections import defaultdict

import pandas as pd
import numpy as np
from tqdm import tqdm

# LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EvidenceItem:
    """Represents a single piece of evidence with its source."""
    text: str
    source: str

@dataclass
class CapabilityMatch:
    """Represents a capability match with confidence and evidence."""
    sentence: str
    confidence_score: float
    supporting_evidence: List[EvidenceItem]
    reasoning: str

class Evidence(BaseModel):
    """A structured representation of a single piece of evidence."""
    source: str = Field(description="The filename of the source document from which this evidence was extracted.")
    text: str = Field(description="The specific quote or piece of evidence from the past performance document.")

class CapabilityAnalysis(BaseModel):
    """Structured output for capability analysis."""
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0 indicating our capability to handle this requirement.")
    supporting_evidence: List[Evidence] = Field(description="A list of evidence items, each with its corresponding source document.")
    reasoning: str = Field(description="Detailed reasoning for the confidence score based on a gap analysis of the requirement versus the evidence.")

class RAGCapabilityAnalyzer:
    """
    RAG-based capability analyzer that replaces the embedding similarity approach.
    """
    
    def __init__(self,
                 provider: str = "openai",
                 openai_api_key: Optional[str] = None,
                 model_name: str = "gpt-4o",
                 ollama_base_url: str = "http://localhost:11434",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 top_k_retrieval: int = 5,
                 vector_store_path: str = "vector_store"):
        """
        Initialize the RAG capability analyzer.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k_retrieval = top_k_retrieval
        self.vector_store_path = vector_store_path
        self.provider = provider
        
        # Initialize LLM and Embeddings based on the provider
        if self.provider == "ollama":
            logger.info(f"Using Ollama provider with model '{model_name}' at {ollama_base_url}")
            self.llm = ChatOllama(model=model_name, base_url=ollama_base_url, temperature=0.0)
            self.embeddings = OllamaEmbeddings(model=model_name, base_url=ollama_base_url)
        elif self.provider == "openai":
            logger.info(f"Using OpenAI provider with model '{model_name}'")
            if openai_api_key:
                os.environ["OPENAI_API_KEY"] = openai_api_key
            self.llm = ChatOpenAI(model_name=model_name, temperature=0.0)
            self.embeddings = OpenAIEmbeddings()
        else:
            raise ValueError("Unsupported LLM provider. Choose 'openai' or 'ollama'.")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize vector store
        self.vector_store = None
        self.documents_processed = set()
        
        # Initialize output parser
        base_parser = PydanticOutputParser(pydantic_object=CapabilityAnalysis)
        self.output_parser = OutputFixingParser.from_llm(parser=base_parser, llm=self.llm)
        
        # Create the analysis prompt
        self.analysis_prompt = self._create_analysis_prompt()
        
        # Create vector store directory
        os.makedirs(vector_store_path, exist_ok=True)
        
        logger.info(f"RAG Capability Analyzer initialized with model: {model_name}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            import PyPDF2
            
            text_content = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ""
                    text_content += page_text + " "
            
            # Clean the text
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            if not text_content:
                logger.warning(f"No text content extracted from {pdf_path}")
                return ""
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def process_documents(self, documents_dir: str) -> None:
        """
        Process all PDF documents in the directory and create vector store.
        
        Args:
            documents_dir: Directory containing PDF documents
        """
        if not os.path.exists(documents_dir):
            logger.error(f"Documents directory not found: {documents_dir}")
            return
        
        # Check if vector store already exists and is up to date
        if self._is_vector_store_current(documents_dir):
            logger.info("Vector store is current, loading existing store...")
            self._load_vector_store()
            return
        
        logger.info("Processing documents and creating vector store...")
        
        # Get all PDF files
        pdf_files = []
        for root, _, files in os.walk(documents_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {documents_dir}")
            return
        
        # Process each PDF file
        documents = []
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                text_content = self.extract_text_from_pdf(pdf_path)
                if text_content:
                    # Split text into chunks
                    chunks = self.text_splitter.split_text(text_content)
                    
                    # Create Document objects with metadata
                    for i, chunk in enumerate(chunks):
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": pdf_path,
                                "filename": os.path.basename(pdf_path),
                                "chunk_id": i,
                                "total_chunks": len(chunks)
                            }
                        )
                        documents.append(doc)
                    
                    self.documents_processed.add(pdf_path)
                    logger.info(f"Processed {pdf_path}: {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
        
        if documents:
            # Create vector store
            logger.info(f"Creating vector store with {len(documents)} chunks...")
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.vector_store_path
            )
            
            # Save metadata about processed documents
            self._save_processing_metadata(documents_dir)
            
            logger.info("Vector store created successfully!")
        else:
            logger.error("No documents were processed successfully")
    
    def _is_vector_store_current(self, documents_dir: str) -> bool:
        """Check if the vector store is current with the documents directory."""
        metadata_file = os.path.join(self.vector_store_path, "processing_metadata.json")
        
        if not os.path.exists(metadata_file):
            return False
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if documents directory matches
            if metadata.get("documents_dir") != documents_dir:
                return False
            
            # Check if all current PDFs were processed
            current_pdfs = set()
            for root, _, files in os.walk(documents_dir):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        current_pdfs.add(os.path.join(root, file))
            
            processed_pdfs = set(metadata.get("processed_files", []))
            
            return current_pdfs.issubset(processed_pdfs)
            
        except Exception as e:
            logger.error(f"Error checking vector store currency: {e}")
            return False
    
    def _load_vector_store(self) -> None:
        """Load existing vector store."""
        try:
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
            logger.info("Vector store loaded successfully")
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
    
    def _save_processing_metadata(self, documents_dir: str) -> None:
        """Save metadata about processed documents."""
        metadata = {
            "documents_dir": documents_dir,
            "processed_files": list(self.documents_processed),
            "timestamp": time.time(),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        
        metadata_file = os.path.join(self.vector_store_path, "processing_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def analyze_capability(self, requirement: str) -> CapabilityMatch:
        """
        Analyzes a single requirement against the vectorized past performance documents.
        """
        if self.vector_store is None:
            self._load_vector_store()
            if self.vector_store is None:
                raise ValueError("Vector store is not initialized. Run process_documents first.")

        # Retrieve relevant chunks
        retriever = self.vector_store.as_retriever(search_kwargs={"k": self.top_k_retrieval})
        retrieved_docs = retriever.invoke(requirement)
        
        # Prepare context
        context = self._prepare_context(retrieved_docs)
        
        # Create the chain
        chain = self.analysis_prompt | self.llm | self.output_parser
        
        # Invoke the chain with the requirement and context
        try:
            analysis_result = chain.invoke({
                "requirement": requirement,
                "context": context,
                "format_instructions": self.output_parser.parser.get_format_instructions()
            })
            
            # Create a CapabilityMatch object from the result
            return CapabilityMatch(
                sentence=requirement,
                confidence_score=analysis_result.confidence_score,
                supporting_evidence=[EvidenceItem(text=ev.text, source=ev.source) for ev in analysis_result.supporting_evidence],
                reasoning=analysis_result.reasoning
            )
        except Exception as e:
            logger.error(f"Error during LLM analysis for requirement: '{requirement[:50]}...': {e}")
            return CapabilityMatch(
                sentence=requirement,
                confidence_score=0.0,
                supporting_evidence=[],
                reasoning="Analysis failed due to a model output error. This may be a temporary issue."
            )
            
    def _prepare_context(self, retrieved_docs: List[Document]) -> str:
        """Prepare context from retrieved documents for LLM analysis."""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            context_parts.append(f"Document {i} ({doc.metadata.get('filename', 'Unknown')}):")
            context_parts.append(doc.page_content)
            context_parts.append("")  # Empty line for separation
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self) -> ChatPromptTemplate:
        """Creates the prompt template for capability analysis."""
        prompt_template = """
You are a skilled technical proposal analyst working for a federal contracting firm. Your task is to assess our organization's capability to fulfill a requirement, using retrieved evidence from our past performance documents.

Please follow this structured approach:

1. **Understand the Requirement**: Identify its key technical and operational goals.
2. **Context Matching**: Review the retrieved content to determine if our past work aligns functionally or thematically. Allow for professional judgment and analogous reasoning. Don't require exact keyword matches if a clearly relevant capability is shown.
3. **Gap Assessment**:
   - **Fully Met**: Strong evidence for all major components of the requirement.
   - **Partially Met**: Relevant experience shown, but some components are missing or not clearly demonstrated.
   - **Not Met**: No substantial evidence found.
4. **Confidence Score**: 
   - 1.0 = Direct match across all major areas.
   - 0.7–0.9 = Strong but slightly indirect or incomplete.
   - 0.4–0.6 = Partial relevance, key pieces missing.
   - 0.0–0.3 = Little or no matching evidence.

5. **Reasoning**: Justify the rating. Explain what the match covers, and what it doesn't. Allow for inferred similarity where appropriate.
6. **Evidence List**: Provide at least 2–3 supporting quotes with source filenames. Focus on functional or domain overlap even if the task names differ.

---

**Requirement:**
{requirement}

**Retrieved Context from Past Performance:**
{context}

{format_instructions}
"""
        return ChatPromptTemplate.from_template(prompt_template)
    
    def batch_analyze_capabilities(self, requirements: List[str]) -> List[CapabilityMatch]:
        """
        Analyzes a batch of requirements, returning a list of capability matches.
        """
        # ... (Implementation for batching if needed, for now we process one-by-one)
        
        results = []
        for req in tqdm(requirements, desc="Analyzing Requirements"):
            results.append(self.analyze_capability(req))
        return results

    def format_past_performance(self, capability_match: CapabilityMatch) -> str:
        """Formats the past performance details for the Excel output."""
        output_parts = [
            f"Confidence: {capability_match.confidence_score:.2f}",
            f"Reasoning: {capability_match.reasoning}",
            "\nSupporting Evidence:"
        ]
        
        if capability_match.supporting_evidence:
            for evidence in capability_match.supporting_evidence:
                output_parts.append(f"- {evidence.text} (from: {evidence.source})")
        else:
            output_parts.append("- No specific evidence found.")
            
        return "\n".join(output_parts)

    def generate_summary_report(self, analysis_results: List[Dict[str, Any]]) -> str:
        """
        Generates a comprehensive executive capability report using multi-stage LLM generation.
        This creates a detailed one-page document for stakeholders with specific contract
        alignments, thorough gap analysis, and strategic recommendations.
        """
        logger.info("Generating comprehensive executive capability report using multi-stage generation...")

        # Filter out non-scored items (e.g., headers)
        scored_results = [r for r in analysis_results if r.get('confidence_score') is not None]

        if not scored_results:
            return "No scored requirements found to generate a report."

        # Sort by confidence score
        scored_results.sort(key=lambda x: x['confidence_score'], reverse=True)

        # Calculate comprehensive statistics
        total_requirements = len(scored_results)
        average_score = sum(r['confidence_score'] for r in scored_results) / total_requirements
        high_confidence = len([r for r in scored_results if r['confidence_score'] >= 0.8])
        strong_confidence = len([r for r in scored_results if 0.6 <= r['confidence_score'] < 0.8])
        moderate_confidence = len([r for r in scored_results if 0.4 <= r['confidence_score'] < 0.6])
        low_confidence = len([r for r in scored_results if r['confidence_score'] < 0.4])

        # Analyze source documents for contract alignment
        contract_analysis = self._analyze_contract_alignments(scored_results)
        
        # Categorize requirements by domain/type
        domain_analysis = self._categorize_requirements(scored_results)
        
        # Get detailed strength and weakness analysis
        strengths_analysis = self._analyze_strengths(scored_results)
        weaknesses_analysis = self._analyze_weaknesses(scored_results)

        # Create comprehensive context for the LLM
        results_summary = f"""
        **COMPREHENSIVE CAPABILITY ANALYSIS SUMMARY**
        
        **Overall Performance Metrics:**
        • Total Requirements Analyzed: {total_requirements}
        • Average Confidence Score: {average_score:.2f}/1.0
        • High Confidence (≥0.8): {high_confidence} requirements ({high_confidence/total_requirements*100:.1f}%)
        • Strong Confidence (0.6-0.8): {strong_confidence} requirements ({strong_confidence/total_requirements*100:.1f}%)
        • Moderate Confidence (0.4-0.6): {moderate_confidence} requirements ({moderate_confidence/total_requirements*100:.1f}%)
        • Low Confidence (<0.4): {low_confidence} requirements ({low_confidence/total_requirements*100:.1f}%)

        **Key Performance Indicators:**
        • Strong alignment (≥0.7): {high_confidence + strong_confidence} requirements ({(high_confidence + strong_confidence)/total_requirements*100:.1f}%)
        • Areas needing attention (<0.7): {moderate_confidence + low_confidence} requirements ({(moderate_confidence + low_confidence)/total_requirements*100:.1f}%)
        • Critical gaps (<0.4): {low_confidence} requirements ({low_confidence/total_requirements*100:.1f}%)

        **Contract Alignment Analysis:**
        {contract_analysis}

        **Domain-Specific Performance:**
        {domain_analysis}

        **Detailed Strength Analysis:**
        {strengths_analysis}

        **Comprehensive Gap Analysis:**
        {weaknesses_analysis}

        **Top 5 Strongest Capabilities (with specific evidence):**
        {self._format_top_capabilities(scored_results[:5])}

        **Top 5 Critical Gaps (with specific details):**
        {self._format_top_gaps(scored_results[-5:])}

        **Strategic Insights:**
        • Primary strength areas: {', '.join([theme for theme, items in self._get_strength_themes(scored_results).items() if len(items) >= 3])}
        • Main gap categories: {', '.join([cat for cat, gaps in self._get_gap_categories(scored_results).items() if len(gaps) >= 2])}
        • Most relevant contracts: {', '.join([contract['contract'] for contract in self._get_top_contracts(scored_results)[:3]])}
        """

        # Generate report sections using multi-stage approach
        sections = self._generate_report_sections(results_summary, contract_analysis)
        
        # Combine sections into final report
        final_report = self._combine_report_sections(sections)
        
        return final_report

    def _generate_report_sections(self, results_summary: str, contract_analysis: str) -> Dict[str, str]:
        """Generate report sections using focused prompts for each part."""
        sections = {}
        
        try:
            # 1. Executive Summary
            prompt_exec_summary = """
You are a senior proposal analyst. Based on the performance summary below, generate a high-level Executive Summary paragraph (150–200 words). Cover:

- Overall alignment with the new contract opportunity.
- Confidence score breakdown (e.g., 75% green).
- Tone: confident, transparent, and professional.
- Mention that a detailed breakdown follows.

Performance Summary:
{results_summary}
"""
            sections['Executive Summary'] = self._call_llm(prompt_exec_summary.format(results_summary=results_summary))
            
            # 2. Best-Aligned Past Contract(s)
            prompt_best_alignment = """
Identify the past contracts that contributed the strongest matches to this analysis based on frequency and content relevance.

For the top 1–2 contracts, generate a detailed paragraph (150–250 words) describing:

- What each contract covered
- Why it aligns closely with the new opportunity
- Technical tools, domains, and success metrics

Use the following document references and capability evidence:

{top_documents_summary}
"""
            sections['Alignment with Key Past Contracts'] = self._call_llm(prompt_best_alignment.format(top_documents_summary=contract_analysis))
            
            # 3. Demonstrated Strengths
            prompt_strengths = """
Generate a section titled 'Demonstrated Strengths' based on the summary below.

- Identify 3–5 key areas where the company has demonstrated strong technical or domain capabilities.
- For each area, mention what kind of work was done, for which past contract, and why it's relevant.
- Aim for clarity and specificity. Keep the language simple and confident.

Analysis Summary:
{results_summary}
"""
            sections['Demonstrated Strengths'] = self._call_llm(prompt_strengths.format(results_summary=results_summary))
            
            # 4. Identified Gaps and Weaknesses
            prompt_gaps = """
Based on the following analysis summary, generate a detailed section called 'Identified Gaps and Weaknesses'.

- Focus on all requirements with confidence scores < 0.7
- Group gaps by theme (missing tools, unclear domain match, insufficient evidence)
- Mention which capabilities are partially or not matched
- Provide specific examples of what's missing and why it matters

Tone: professional, honest, and constructive

Analysis Summary:
{results_summary}
"""
            sections['Identified Gaps and Weaknesses'] = self._call_llm(prompt_gaps.format(results_summary=results_summary))
            
            # 5. Final Recommendation
            prompt_recommendation = """
Write a recommendation section (100–150 words) summarizing whether we should pursue the opportunity and why.

Include:
- High-level justification (balance of strengths vs. gaps)
- Suggested next steps (e.g., SME involvement, partnership, capability narrative enhancement)

Use this summary as context:
{results_summary}
"""
            sections['Final Recommendation'] = self._call_llm(prompt_recommendation.format(results_summary=results_summary))
            
        except Exception as e:
            logger.error(f"Error generating report sections: {e}")
            # Fallback to single prompt if multi-stage fails
            sections = self._generate_fallback_report(results_summary)
        
        return sections

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with a specific prompt and return the response."""
        try:
            prompt_template = ChatPromptTemplate.from_template(prompt)
            chain = prompt_template | self.llm
            
            response = chain.invoke({})
            return response.content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return f"Error generating section: {str(e)}"

    def _combine_report_sections(self, sections: Dict[str, str]) -> str:
        """Combine the generated sections into a final report."""
        report_parts = []
        report_parts.append("# Capability Summary Report\n")
        
        for section_name, content in sections.items():
            report_parts.append(f"## {section_name}")
            report_parts.append(content)
            report_parts.append("")  # Empty line between sections
        
        return "\n".join(report_parts)

    def _generate_fallback_report(self, results_summary: str) -> Dict[str, str]:
        """Fallback method using the original single-prompt approach."""
        logger.warning("Using fallback single-prompt report generation")
        
        prompt_template = """
        You are a senior-level proposal strategist at a federal contracting firm. Your job is to write a comprehensive, easy-to-read **capability summary report** based on analysis results generated by an AI system comparing our company's past performance with a new contract opportunity.

        This report will be the **first and primary document reviewed by stakeholders** to make a decision on whether to pursue this opportunity.

        Your task: Write a detailed, clear, and structured report that:

        ---

        ### ✅ REPORT STRUCTURE (Include all sections, in order):

        1. **Executive Summary**
           - Clearly state whether our company has a **strong, moderate, or limited** alignment with the new opportunity overall.
           - Quantify our performance (e.g., "We achieved high-confidence matches on 75% of requirements").
           - Summarize the intent of the opportunity and our positioning.

        2. **Alignment with New Opportunity**
           - Describe the **key themes or goals** of the new requirement (based on your understanding).
           - Compare those themes with the work we have done in the past.
           - Call out 1–2 **specific past contracts** that are most similar (e.g., "Our work on NPPES aligns well with XYZ in this opportunity").
           - Summarize what made those contracts successful and relevant (technical scope, agencies served, tools used, delivery experience).

        3. **Demonstrated Strengths**
           - Break down 3–5 areas where we have shown **strong technical or domain capability**.
           - Use evidence from the past performance summaries.
           - Mention which contracts contributed the most (e.g., "MSSPSS was referenced 55 times").
           - Highlight scale, outcomes, and tools wherever relevant (e.g., "Managed HIPAA-compliant data warehouse for 10,000+ users").

        4. **Identified Gaps or Shortcomings**
           - Analyze all **medium- and low-confidence matches** (scores below 0.7).
           - Group gaps by theme (e.g., "Emerging tech," "Lack of specific framework use," "Limited federal experience in X domain").
           - Include **why** these were weak (e.g., incomplete tooling evidence, capability not documented clearly, lacking partner experience).
           - Be honest but constructive — the goal is to highlight risk areas for mitigation.

        5. **Recommendations**
           - State whether we should pursue the opportunity, and **why**.
           - Recommend specific next steps (e.g., "Involve SME for gap fill", "Team with partner who has X capability", "Prepare capability narrative for section Y").
           - Suggest narrative positioning for proposal if we decide to move forward (e.g., "Leverage NPPES and MSSPSS as cornerstone examples").

        ---

        ### ✅ WRITING STYLE GUIDELINES:
        - Use clear, simple language (aim for Flesch Reading Ease 60+).
        - Avoid jargon and dense paragraphs.
        - Write in a calm, confident, and professional tone.
        - Don't repeat input verbatim — synthesize and narrate.
        - Make this readable by someone without technical expertise.
        - Be transparent, balanced, and informative.

        ---

        **Input Summary:**
        Below is a summary of the AI-generated capability analysis.

        {results_summary}
        """
        
        try:
            response = self._call_llm(prompt_template.format(results_summary=results_summary))
            return {
                'Executive Summary': response,
                'Alignment with Key Past Contracts': 'Fallback: See main report above',
                'Demonstrated Strengths': 'Fallback: See main report above', 
                'Identified Gaps and Weaknesses': 'Fallback: See main report above',
                'Final Recommendation': 'Fallback: See main report above'
            }
        except Exception as e:
            logger.error(f"Fallback report generation failed: {e}")
            return {
                'Executive Summary': 'Error: Could not generate report sections',
                'Alignment with Key Past Contracts': 'Error: Could not generate report sections',
                'Demonstrated Strengths': 'Error: Could not generate report sections',
                'Identified Gaps and Weaknesses': 'Error: Could not generate report sections', 
                'Final Recommendation': 'Error: Could not generate report sections'
            }

    def _analyze_contract_alignments(self, scored_results: List[Dict[str, Any]]) -> str:
        """Analyze which past contracts are most relevant to current requirements with detailed metrics."""
        contract_scores = defaultdict(list)
        contract_evidence = defaultdict(list)
        contract_requirements = defaultdict(list)
        
        for result in scored_results:
            confidence = result.get('confidence_score', 0)
            requirement = result.get('requirement', '')
            evidence_list = result.get('supporting_evidence', [])
            
            for evidence in evidence_list:
                source = evidence.get('source', 'Unknown')
                # Extract contract name from filename
                contract_name = self._extract_contract_name(source)
                contract_scores[contract_name].append(confidence)
                contract_evidence[contract_name].append({
                    'requirement': requirement[:100] + '...',
                    'evidence': evidence.get('text', '')[:200] + '...',
                    'confidence': confidence
                })
                contract_requirements[contract_name].append(requirement)
        
        # Calculate detailed statistics for each contract
        contract_analysis = []
        for contract, scores in contract_scores.items():
            avg_score = sum(scores) / len(scores)
            evidence_count = len(contract_evidence[contract])
            high_confidence_count = sum(1 for score in scores if score >= 0.7)
            total_requirements = len(set(contract_requirements[contract]))
            
            contract_analysis.append({
                'contract': contract,
                'avg_score': avg_score,
                'evidence_count': evidence_count,
                'high_confidence_count': high_confidence_count,
                'total_requirements': total_requirements,
                'top_evidence': contract_evidence[contract][:3],  # Top 3 pieces of evidence
                'requirements': list(set(contract_requirements[contract]))
            })
        
        contract_analysis.sort(key=lambda x: x['avg_score'], reverse=True)
        
        # Format the analysis with detailed contract information
        analysis_text = "**Contract Alignment Analysis:**\n"
        for i, contract in enumerate(contract_analysis[:5]):  # Top 5 contracts
            analysis_text += f"{i+1}. {contract['contract']}\n"
            analysis_text += f"   • Referenced {contract['evidence_count']} times\n"
            analysis_text += f"   • Average Score: {contract['avg_score']:.2f}\n"
            analysis_text += f"   • High-Confidence Matches: {contract['high_confidence_count']}\n"
            analysis_text += f"   • Requirements Covered: {contract['total_requirements']}\n"
            if contract['top_evidence']:
                analysis_text += f"   • Key Experience: {contract['top_evidence'][0]['evidence']}\n"
            analysis_text += "\n"
        
        return analysis_text

    def _categorize_requirements(self, scored_results: List[Dict[str, Any]]) -> str:
        """Categorize requirements by domain and analyze performance in each category."""
        categories = {
            'Cybersecurity': ['security', 'cyber', 'fisma', 'nist', 'risk', 'compliance', 'audit'],
            'Data Management': ['data', 'analytics', 'reporting', 'dashboard', 'database'],
            'Identity Management': ['identity', 'piv', 'icam', 'authentication', 'authorization'],
            'System Architecture': ['architecture', 'design', 'integration', 'framework'],
            'Incident Response': ['incident', 'response', 'threat', 'hunting', 'remediation'],
            'Governance': ['governance', 'policy', 'compliance', 'oversight', 'management']
        }
        
        category_results = defaultdict(list)
        
        for result in scored_results:
            requirement = result.get('requirement', '').lower()
            confidence = result.get('confidence_score', 0)
            
            # Find the best matching category
            best_category = 'Other'
            max_matches = 0
            
            for category, keywords in categories.items():
                matches = sum(1 for keyword in keywords if keyword in requirement)
                if matches > max_matches:
                    max_matches = matches
                    best_category = category
            
            category_results[best_category].append(confidence)
        
        # Calculate statistics for each category with simple language
        analysis_text = "**Performance by Area:**\n"
        for category, scores in category_results.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                count = len(scores)
                analysis_text += f"• {category}: {count} requirements, average score {avg_score:.2f}\n"
        
        return analysis_text

    def _analyze_strengths(self, scored_results: List[Dict[str, Any]]) -> str:
        """Analyze our strongest capabilities with detailed evidence and contract references."""
        high_confidence = [r for r in scored_results if r.get('confidence_score', 0) >= 0.7]
        
        if not high_confidence:
            return "No high-confidence capabilities identified."
        
        # Group by common themes with detailed analysis
        strength_themes = defaultdict(list)
        
        for result in high_confidence:
            requirement = result.get('requirement', '')
            confidence = result.get('confidence_score', 0)
            evidence = result.get('supporting_evidence', [])
            
            # Identify themes based on keywords
            themes = []
            if any(word in requirement.lower() for word in ['risk', 'compliance', 'audit', 'fisma', 'nist']):
                themes.append('Risk & Compliance Management')
            if any(word in requirement.lower() for word in ['data', 'analytics', 'reporting', 'dashboard', 'database', 'warehouse']):
                themes.append('Data Management & Analytics')
            if any(word in requirement.lower() for word in ['security', 'cyber', 'threat', 'incident']):
                themes.append('Cybersecurity & Incident Response')
            if any(word in requirement.lower() for word in ['identity', 'authentication', 'piv', 'icam']):
                themes.append('Identity & Access Management')
            if any(word in requirement.lower() for word in ['architecture', 'design', 'integration', 'framework']):
                themes.append('System Architecture & Integration')
            if any(word in requirement.lower() for word in ['governance', 'policy', 'oversight', 'management']):
                themes.append('Governance & Policy')
            
            for theme in themes:
                strength_themes[theme].append({
                    'requirement': requirement,
                    'confidence': confidence,
                    'evidence': evidence,
                    'contracts': [ev.get('source', 'Unknown') for ev in evidence]
                })
        
        analysis_text = "**Demonstrated Strengths by Domain:**\n"
        for theme, items in strength_themes.items():
            avg_confidence = sum(item['confidence'] for item in items) / len(items)
            unique_contracts = set()
            for item in items:
                unique_contracts.update(item['contracts'])
            
            analysis_text += f"• {theme}: {len(items)} requirements, average score {avg_confidence:.2f}\n"
            analysis_text += f"  - Contracts involved: {len(unique_contracts)}\n"
            if items:
                top_item = max(items, key=lambda x: x['confidence'])
                analysis_text += f"  - Top example: {top_item['requirement'][:80]}...\n"
                if top_item['evidence']:
                    analysis_text += f"  - Evidence: {top_item['evidence'][0].get('text', '')[:100]}...\n"
        
        return analysis_text

    def _analyze_weaknesses(self, scored_results: List[Dict[str, Any]]) -> str:
        """Analyze gaps and weaknesses with detailed categorization and reasoning."""
        low_confidence = [r for r in scored_results if r.get('confidence_score', 0) < 0.7]
        
        if not low_confidence:
            return "No significant gaps identified."
        
        # Categorize gaps by type and severity
        gap_categories = {
            'Emerging Technologies': [],
            'Specific Frameworks': [],
            'Federal Domain Experience': [],
            'Technical Capabilities': [],
            'Scale & Complexity': [],
            'Tools & Platforms': []
        }
        
        for result in low_confidence:
            requirement = result.get('requirement', '').lower()
            confidence = result.get('confidence_score', 0)
            reasoning = result.get('reasoning', '')
            
            # Categorize based on content
            if any(word in requirement for word in ['ai', 'machine learning', 'automation', 'advanced']):
                gap_categories['Emerging Technologies'].append(result)
            elif any(word in requirement for word in ['framework', 'standard', 'protocol']):
                gap_categories['Specific Frameworks'].append(result)
            elif any(word in requirement for word in ['federal', 'agency', 'government']):
                gap_categories['Federal Domain Experience'].append(result)
            elif any(word in requirement for word in ['technical', 'engineering', 'development']):
                gap_categories['Technical Capabilities'].append(result)
            elif any(word in requirement for word in ['scale', 'large', 'enterprise', 'complex']):
                gap_categories['Scale & Complexity'].append(result)
            elif any(word in requirement for word in ['tool', 'platform', 'software', 'system']):
                gap_categories['Tools & Platforms'].append(result)
            else:
                gap_categories['Technical Capabilities'].append(result)
        
        analysis_text = "**Identified Gaps by Category:**\n"
        for category, gaps in gap_categories.items():
            if gaps:
                avg_score = sum(g.get('confidence_score', 0) for g in gaps) / len(gaps)
                analysis_text += f"• {category}: {len(gaps)} requirements, average score {avg_score:.2f}\n"
                if gaps:
                    top_gap = min(gaps, key=lambda x: x.get('confidence_score', 0))
                    analysis_text += f"  - Example: {top_gap.get('requirement', '')[:80]}...\n"
                    analysis_text += f"  - Issue: {top_gap.get('reasoning', '')[:100]}...\n"
        
        return analysis_text

    def _format_top_capabilities(self, top_results: List[Dict[str, Any]]) -> str:
        """Format the top capabilities with simple bullet points."""
        formatted = "**Top 5 Strongest Capabilities:**\n"
        for i, result in enumerate(top_results, 1):
            formatted += f"{i}. {result.get('requirement', '')[:100]}...\n"
            formatted += f"   • Score: {result.get('confidence_score', 0):.2f}\n"
            if result.get('supporting_evidence'):
                formatted += f"   • Evidence: {result.get('supporting_evidence', [{}])[0].get('text', '')[:80]}...\n"
            formatted += "\n"
        return formatted

    def _format_top_gaps(self, gap_results: List[Dict[str, Any]]) -> str:
        """Format the top gaps with simple bullet points."""
        formatted = "**Top 5 Critical Gaps:**\n"
        for i, result in enumerate(gap_results, 1):
            formatted += f"{i}. {result.get('requirement', '')[:100]}...\n"
            formatted += f"   • Score: {result.get('confidence_score', 0):.2f}\n"
            formatted += f"   • Issue: {result.get('reasoning', '')[:100]}...\n\n"
        return formatted

    def _extract_contract_name(self, filename: str) -> str:
        """Extract a readable contract name from filename."""
        # Remove file extension and common prefixes
        name = filename.replace('.pdf', '').replace('PP_Consolidated_', '').replace('_', ' ')
        
        # Clean up common patterns
        name = name.replace('CMS ', 'CMS ').replace('CDC ', 'CDC ').replace('TSA ', 'TSA ')
        
        return name.strip()

    def _get_strength_themes(self, scored_results: List[Dict[str, Any]]) -> Dict[str, List]:
        """Get strength themes for strategic insights."""
        high_confidence = [r for r in scored_results if r.get('confidence_score', 0) >= 0.7]
        strength_themes = defaultdict(list)
        
        for result in high_confidence:
            requirement = result.get('requirement', '').lower()
            
            # Identify themes based on keywords
            themes = []
            if any(word in requirement for word in ['risk', 'compliance', 'audit', 'fisma', 'nist']):
                themes.append('Risk & Compliance')
            if any(word in requirement for word in ['data', 'analytics', 'reporting', 'dashboard']):
                themes.append('Data & Analytics')
            if any(word in requirement for word in ['security', 'cyber', 'threat', 'incident']):
                themes.append('Cybersecurity')
            if any(word in requirement for word in ['identity', 'authentication', 'piv', 'icam']):
                themes.append('Identity Management')
            if any(word in requirement for word in ['architecture', 'design', 'integration']):
                themes.append('System Architecture')
            if any(word in requirement for word in ['governance', 'policy', 'oversight']):
                themes.append('Governance')
            
            for theme in themes:
                strength_themes[theme].append(result)
        
        return strength_themes

    def _get_gap_categories(self, scored_results: List[Dict[str, Any]]) -> Dict[str, List]:
        """Get gap categories for strategic insights."""
        low_confidence = [r for r in scored_results if r.get('confidence_score', 0) < 0.7]
        gap_categories = defaultdict(list)
        
        for result in low_confidence:
            requirement = result.get('requirement', '').lower()
            
            # Categorize based on content
            if any(word in requirement for word in ['ai', 'machine learning', 'automation']):
                gap_categories['Emerging Tech'].append(result)
            elif any(word in requirement for word in ['framework', 'standard', 'protocol']):
                gap_categories['Specific Frameworks'].append(result)
            elif any(word in requirement for word in ['federal', 'agency', 'government']):
                gap_categories['Federal Experience'].append(result)
            elif any(word in requirement for word in ['technical', 'engineering']):
                gap_categories['Technical Capabilities'].append(result)
            elif any(word in requirement for word in ['scale', 'large', 'enterprise']):
                gap_categories['Scale & Complexity'].append(result)
            else:
                gap_categories['Other'].append(result)
        
        return gap_categories

    def _get_top_contracts(self, scored_results: List[Dict[str, Any]]) -> List[Dict]:
        """Get top contracts for strategic insights."""
        contract_scores = defaultdict(list)
        
        for result in scored_results:
            confidence = result.get('confidence_score', 0)
            evidence_list = result.get('supporting_evidence', [])
            
            for evidence in evidence_list:
                source = evidence.get('source', 'Unknown')
                contract_name = self._extract_contract_name(source)
                contract_scores[contract_name].append(confidence)
        
        contract_analysis = []
        for contract, scores in contract_scores.items():
            avg_score = sum(scores) / len(scores)
            contract_analysis.append({
                'contract': contract,
                'avg_score': avg_score,
                'evidence_count': len(scores)
            })
        
        contract_analysis.sort(key=lambda x: x['avg_score'], reverse=True)
        return contract_analysis[:3]  # Top 3 contracts

if __name__ == '__main__':
    # Example usage for testing
    # This part will only run if you execute this script directly
    pass 