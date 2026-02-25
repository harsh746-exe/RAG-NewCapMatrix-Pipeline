"""
RAG Pipeline for Capability Matrix Analysis (TXT Version)

This module implements a Retrieval-Augmented Generation (RAG) pipeline that uses
TXT files instead of PDFs for more reliable text processing.
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
from pathlib import Path

import pandas as pd
import numpy as np
from tqdm import tqdm

# LangChain imports (support both legacy and 0.3+ layouts)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import (
    OpenAIEmbeddings,
    ChatOpenAI,
    AzureChatOpenAI,
    AzureOpenAIEmbeddings,
)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama

try:
    # Preferred: LangChain 0.3+ core packages
    from langchain_core.documents import Document
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    # Fallback for older LangChain versions
    from langchain.schema import Document
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema.runnable import RunnablePassthrough
    from langchain.output_parsers import PydanticOutputParser
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
    source: str = Field(
        description=(
            "The contract name and filename of the source document from which this evidence was extracted "
            "(for example: 'TSA IPMSS BPA / PP_TSA_update')."
        )
    )
    text: str = Field(description="The specific quote or piece of evidence from the past performance document.")

class CapabilityAnalysis(BaseModel):
    """Structured output for capability analysis."""
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0 indicating our capability to handle this requirement.")
    supporting_evidence: List[Evidence] = Field(description="A list of evidence items, each with its corresponding source (contract name / filename).")
    reasoning: str = Field(
        description=(
            "Reasoning written in a specific format: one block per contract that had relevant evidence. "
            "Each block must start with the CONTRACT FOLDER NAME followed by a colon, then a paragraph in first-person 'We' style "
            "describing our capability based on that contract's evidence. Use professional tone; reference specific deliverables, "
            "reports, processes, or manuals. Separate multiple contract blocks with a blank line. "
            "Example format: 'SSOE: We maintain updated project documents, submit Monthly Status Reports... "
            "CDAC: The CDAC Contractor requests, receives, screens...' Only include contracts that appear in the provided context (top matches)."
        )
    )

class RAGCapabilityAnalyzerTXT:
    """
    RAG-based capability analyzer that uses TXT files for more reliable processing.
    """
    
    def __init__(self,
                 provider: str = "openai",
                 openai_api_key: Optional[str] = None,
                 model_name: str = "gpt-4o",
                 ollama_base_url: str = "http://localhost:11434",
                 azure_endpoint: Optional[str] = None,
                 azure_api_key: Optional[str] = None,
                 azure_api_version: str = "2024-12-01-preview",
                 azure_deployment: Optional[str] = None,
                 azure_embedding_deployment: Optional[str] = None,
                 use_local_embeddings: bool = False,
                 local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 top_k_retrieval: int = 5,
                 vector_store_path: str = "vector_store_txt",
                 txt_dir: str = "documents_txt"):
        """
        Initialize the RAG capability analyzer with TXT support.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k_retrieval = top_k_retrieval
        self.vector_store_path = vector_store_path
        self.txt_dir = Path(txt_dir)
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
        elif self.provider == "azure":
            logger.info(
                f"Using Azure OpenAI provider with deployment '{azure_deployment or model_name}' "
                f"at endpoint '{azure_endpoint}' (local_embeddings={use_local_embeddings})"
            )
            if azure_api_key:
                # Allow downstream clients relying on env var, while also passing explicit params
                os.environ["AZURE_OPENAI_API_KEY"] = azure_api_key

            # Initialize chat model
            self.llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version=azure_api_version,
                azure_deployment=azure_deployment or model_name,
                temperature=0.0,
            )

            # Initialize embeddings: either local (sentence-transformers) or Azure embeddings
            if use_local_embeddings:
                logger.info(f"Using local HuggingFace embeddings: {local_embedding_model}")
                self.embeddings = HuggingFaceEmbeddings(model_name=local_embedding_model)
            else:
                logger.info(
                    f"Using Azure OpenAI embeddings with deployment "
                    f"'{azure_embedding_deployment or azure_deployment}'"
                )
                self.embeddings = AzureOpenAIEmbeddings(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_api_key,
                    api_version=azure_api_version,
                    model=azure_embedding_deployment or (azure_deployment or model_name),
                )
        else:
            raise ValueError("Unsupported LLM provider. Choose 'openai', 'ollama', or 'azure'.")
        
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
        
        # Initialize output parser (structured Pydantic output)
        self.output_parser = PydanticOutputParser(pydantic_object=CapabilityAnalysis)
        
        # Create the analysis prompt
        self.analysis_prompt = self._create_analysis_prompt()
        
        # Create vector store directory
        os.makedirs(vector_store_path, exist_ok=True)
        
        logger.info(f"RAG Capability Analyzer (TXT) initialized with model: {model_name}")
    
    def read_txt_file(self, txt_path: Path) -> str:
        """
        Read text content from a TXT file.
        
        Args:
            txt_path: Path to the TXT file
            
        Returns:
            Text content
        """
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
            
            # Clean the text
            content = re.sub(r'\s+', ' ', content).strip()
            
            if not content:
                logger.warning(f"No text content found in {txt_path}")
                return ""
            
            return content
            
        except Exception as e:
            logger.error(f"Error reading TXT file {txt_path}: {e}")
            return ""

    def _infer_contract_name_from_source_path(self, source_path: Path) -> Optional[str]:
        """
        Infer contract folder name from an absolute source path.

        Expected layout:
        .../02_Detailed Project Descriptions/<CONTRACT_FOLDER>/...
        """
        parts = source_path.parts
        try:
            idx = parts.index("02_Detailed Project Descriptions")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        except ValueError:
            pass
        return source_path.parent.name if source_path.parent else None

    def _extract_source_metadata_from_txt_header(self, txt_path: Path) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract (original_source_path, contract_name) from the TXT metadata header.

        Supports headers produced by the converter:
        - '# Original PDF: ...'
        - '# Original DOCX: ...'
        """
        original_source: Optional[str] = None
        contract_name: Optional[str] = None

        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.startswith("#"):
                        break
                    if line.startswith("# Original PDF:") or line.startswith("# Original DOCX:"):
                        original_source = line.split(":", 1)[1].strip()
                        src_path = Path(original_source)
                        contract_name = self._infer_contract_name_from_source_path(src_path)
                        break
        except Exception as header_err:
            logger.debug(f"Could not parse header for {txt_path}: {header_err}")

        return original_source, contract_name
    
    def process_txt_documents(self) -> None:
        """
        Process all TXT documents and create vector store.
        """
        if not self.txt_dir.exists():
            logger.error(f"TXT documents directory not found: {self.txt_dir}")
            return
        
        # Check if vector store already exists and is up to date
        if self._is_vector_store_current():
            logger.info("Vector store is current, loading existing store...")
            self._load_vector_store()
            return
        
        logger.info("Processing TXT documents and creating vector store...")
        
        # Get all TXT files
        txt_files = list(self.txt_dir.glob("*.txt"))
        
        if not txt_files:
            logger.warning(f"No TXT files found in {self.txt_dir}")
            return
        
        # Process each TXT file
        documents = []
        for txt_path in tqdm(txt_files, desc="Processing TXT files"):
            try:
                original_source, contract_name = self._extract_source_metadata_from_txt_header(txt_path)

                text_content = self.read_txt_file(txt_path)
                if text_content:
                    # Split text into chunks
                    chunks = self.text_splitter.split_text(text_content)
                    
                    # Create Document objects with metadata
                    for i, chunk in enumerate(chunks):
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": str(txt_path),
                                "filename": txt_path.stem,  # Remove .txt extension
                                "original_source": original_source,
                                "contract_name": contract_name,
                                "chunk_id": i,
                                "total_chunks": len(chunks),
                            },
                        )
                        documents.append(doc)
                    
                    self.documents_processed.add(str(txt_path))
                    logger.info(f"Processed {txt_path.name}: {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {txt_path}: {e}")
        
        if documents:
            # Create vector store
            logger.info(f"Creating vector store with {len(documents)} chunks...")
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.vector_store_path
            )
            
            # Save metadata about processed documents
            self._save_processing_metadata()
            
            logger.info("Vector store created successfully!")
        else:
            logger.error("No documents were processed successfully")
    
    def _is_vector_store_current(self) -> bool:
        """Check if the vector store is current with the TXT documents directory."""
        metadata_file = os.path.join(self.vector_store_path, "processing_metadata.json")
        
        if not os.path.exists(metadata_file):
            return False
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if TXT directory matches
            if metadata.get("txt_dir") != str(self.txt_dir):
                return False
            
            # Check if all current TXT files were processed
            current_txts = set()
            for txt_file in self.txt_dir.glob("*.txt"):
                current_txts.add(str(txt_file))
            
            processed_txts = set(metadata.get("processed_files", []))
            
            return current_txts.issubset(processed_txts)
            
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
    
    def _save_processing_metadata(self) -> None:
        """Save metadata about processed documents."""
        metadata = {
            "txt_dir": str(self.txt_dir),
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
                raise ValueError("Vector store is not initialized. Run process_txt_documents first.")

        # Retrieve relevant chunks
        retriever = self.vector_store.as_retriever(search_kwargs={"k": self.top_k_retrieval})
        retrieved_docs = retriever.invoke(requirement)
        
        # Prepare context
        context = self._prepare_context(retrieved_docs)
        
        # Create the chain
        chain = self.analysis_prompt | self.llm | self.output_parser
        
        # Invoke the chain with the requirement and context
        try:
            # Get format instructions in a version-compatible way
            if hasattr(self.output_parser, "get_format_instructions"):
                fmt_instructions = self.output_parser.get_format_instructions()
            else:
                # Legacy interface (if any)
                fmt_instructions = self.output_parser.parser.get_format_instructions()  # type: ignore[attr-defined]

            analysis_result = chain.invoke(
                {
                    "requirement": requirement,
                    "context": context,
                    "format_instructions": fmt_instructions,
                }
            )
            
            # Create a CapabilityMatch object from the result
            return CapabilityMatch(
                sentence=requirement,
                confidence_score=analysis_result.confidence_score,
                supporting_evidence=[
                    EvidenceItem(text=evidence.text, source=evidence.source)
                    for evidence in analysis_result.supporting_evidence
                ],
                reasoning=analysis_result.reasoning
            )
            
        except Exception as e:
            # Avoid dumping full JSON bodies into logs; keep the message concise
            msg = str(e)
            if "Invalid json output:" in msg:
                msg = "Invalid JSON output from LLM (see debug logs for details)"
            logger.error(f"Error in capability analysis: {msg}")
            # Return a fallback result
            return CapabilityMatch(
                sentence=requirement,
                confidence_score=0.0,
                supporting_evidence=[],
                reasoning=f"Error in analysis: {str(e)}"
            )
    
    def _prepare_context(self, retrieved_docs: List[Document]) -> str:
        """Prepare context from retrieved documents."""
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            filename = doc.metadata.get("filename", "Unknown")
            contract_name = doc.metadata.get("contract_name")
            if contract_name:
                header = f"Document {i} (Contract: {contract_name} | File: {filename})"
            else:
                header = f"Document {i} ({filename})"
            context_parts.append(f"{header}:\n{doc.page_content}")
        
        return "\n\n".join(context_parts)
    
    def _create_analysis_prompt(self) -> ChatPromptTemplate:
        """Create the analysis prompt for capability evaluation."""
        prompt = ChatPromptTemplate.from_template("""
You are an expert capability analyst evaluating past performance documents against specific requirements.

REQUIREMENT TO ANALYZE:
{requirement}

CONTEXT FROM PAST PERFORMANCE DOCUMENTS (each chunk is labeled with Contract and File):
{context}

TASK:
Analyze the requirement against the context above. Determine our capability to fulfill it. Use only the contracts and evidence provided (these are the top matches). Output your reasoning in the exact format below.

REASONING OUTPUT FORMAT (mandatory):
- Group your reasoning **by contract**. For each contract that has relevant evidence in the context, write exactly one block.
- Each block must start with the **contract folder name** (as shown in the context, e.g. "Contract: TSA IPMSS BPA") followed by a colon, then a single paragraph.
- Paragraph style: first-person "We", professional and confident. Describe what we do, what we deliver, and how we meet the requirement. Reference specific deliverables (e.g. reports, manuals, processes, approvals) from the evidence.
- If multiple contracts have relevant evidence, include one block per contract, separated by a blank line. Only include contracts that appear in the context (top matches).
- Do NOT write the words "Contract:" or "File:" in your reasoning. Instead, just use the contract folder name as the block header (for example: "CMS CSMM (RMADA2): ...").

Example of the required reasoning style:

SSOE: We maintain updated project documents, submit Monthly Status Reports of tasks and activities, and provide a detailed Annual Summary Report with findings and recommendations. Monthly reports to the COR include trends and methodologies on appeals upheld at any level. We maintain updated project documents and conduct analytic review and validation processes in accordance with the CMS Program Integrity Manual (PIM).

CDAC: The CDAC Contractor requests, receives, screens, troubleshoots, abstracts and validates, processes, stores, and destroys/mails medical records. Each clinical data abstraction is based on documentation. We participate in an external quality assurance (EQA) program, adhere to Internal Quality Control (IQC) review, and provide questions and improvement suggestions to CMS or study owners as authorized. Each abstraction type includes job aids and/or manuals to assist abstractors in performing accurately.

OTHER INSTRUCTIONS:
- Provide a confidence score from 0.0 to 1.0 (conservative: high scores only for strong, direct matches).
- In supporting_evidence, list specific quotes and set source to the contract name and filename (e.g. "TSA IPMSS BPA / PP_TSA_update").
- Base reasoning only on the top-matched context provided; do not invent contracts or evidence.

{format_instructions}
""")
        return prompt
    
    def batch_analyze_capabilities(self, requirements: List[str]) -> List[CapabilityMatch]:
        """Analyze multiple requirements in batch."""
        return [self.analyze_capability(req) for req in requirements]
    
    def format_past_performance(self, capability_match: CapabilityMatch) -> str:
        """Format the capability match for output, including grouped evidence."""
        # Group evidence by contract (parsed from the source prefix before ' / ')
        grouped: Dict[str, List[EvidenceItem]] = defaultdict(list)
        for ev in capability_match.supporting_evidence:
            src = ev.source or ""
            contract_name = src.split(" / ", 1)[0].strip() if " / " in src else src.strip() or "Unknown Contract"
            grouped[contract_name].append(ev)

        evidence_lines: List[str] = []
        for contract, items in grouped.items():
            evidence_lines.append(f"{contract}:")
            for ev in items:
                snippet = ev.text.strip()
                evidence_lines.append(f'  - "{snippet}" ({ev.source})')

        evidence_text = "\n".join(evidence_lines) if evidence_lines else ""

        if evidence_text:
            return f"""{capability_match.reasoning}

Supporting Evidence (by contract):
{evidence_text}"""
        else:
            return capability_match.reasoning

    def generate_summary_report(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive summary report."""
        if not analysis_results:
            return "No analysis results available."
        
        # Calculate statistics
        total_requirements = len(analysis_results)
        high_confidence = sum(1 for result in analysis_results if result.get('confidence_score', 0) >= 0.7)
        medium_confidence = sum(1 for result in analysis_results if 0.4 <= result.get('confidence_score', 0) < 0.7)
        low_confidence = sum(1 for result in analysis_results if result.get('confidence_score', 0) < 0.4)
        
        avg_confidence = sum(result.get('confidence_score', 0) for result in analysis_results) / total_requirements
        
        # Get specific insights about each confidence level
        high_reqs = [r for r in analysis_results if r.get('confidence_score', 0) >= 0.7]
        medium_reqs = [r for r in analysis_results if 0.4 <= r.get('confidence_score', 0) < 0.7]
        low_reqs = [r for r in analysis_results if r.get('confidence_score', 0) < 0.4]
        
        # Generate specific findings
        strengths_text = self._generate_specific_findings(high_reqs, "strengths")
        attention_text = self._generate_specific_findings(low_reqs, "gaps")
        
        # Generate report
        report = f"""
# EXECUTIVE CAPABILITY ANALYSIS SUMMARY

## OVERVIEW
- **Total Requirements Analyzed**: {total_requirements}
- **Average Confidence Score**: {avg_confidence:.2f}
- **High Confidence (≥0.7)**: {high_confidence} ({high_confidence/total_requirements*100:.1f}%)
- **Medium Confidence (0.4-0.7)**: {medium_confidence} ({medium_confidence/total_requirements*100:.1f}%)
- **Low Confidence (<0.4)**: {low_confidence} ({low_confidence/total_requirements*100:.1f}%)

## KEY FINDINGS

### Strengths
{strengths_text}

### Areas for Attention  
{attention_text}

## STRATEGIC RECOMMENDATIONS

1. **Immediate Actions**:
   - Leverage high-confidence capabilities ({high_confidence} requirements) in proposal positioning
   - Develop detailed case studies for medium-confidence areas ({medium_confidence} requirements)
   - Create targeted capability development plans for low-confidence requirements ({low_confidence} requirements)

2. **Proposal Strategy**:
   - Lead with strongest capabilities in executive summary and technical approach
   - Address capability gaps proactively with mitigation strategies
   - Consider teaming arrangements for quantum computing and post-quantum cryptography expertise

3. **Risk Mitigation**:
   - Prepare comprehensive evidence packages for all medium-confidence requirements
   - Develop contingency plans and partnership strategies for low-confidence areas
   - Ensure all supporting documentation is readily accessible and well-organized

## ANALYSIS METHODOLOGY

The analysis reviewed {total_requirements} requirements against past performance documentation using AI-powered semantic matching. 
The average confidence score of {avg_confidence:.2f} indicates {self._get_overall_assessment(avg_confidence)}.

{self._get_top_contract_matches(analysis_results)}

{self._get_detailed_insights(analysis_results)}

---
*Report generated automatically from RAG-based capability analysis*
"""
        return report
    
    def _get_overall_assessment(self, avg_confidence: float) -> str:
        """Get overall assessment based on average confidence."""
        if avg_confidence >= 0.7:
            return "strong overall capability alignment with requirements"
        elif avg_confidence >= 0.5:
            return "moderate capability alignment with some areas needing attention"
        else:
            return "significant capability gaps that require strategic planning"
    
    def _get_detailed_insights(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Generate detailed insights from analysis results."""
        sorted_results = sorted(analysis_results, key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        insights = "\n## DETAILED REQUIREMENT ANALYSIS\n\n"
        
        # Analyze each requirement individually
        for i, result in enumerate(sorted_results, 1):
            requirement = result.get('requirement', 'Unknown')
            confidence = result.get('confidence_score', 0)
            reasoning = result.get('reasoning', 'No reasoning provided')
            evidence = result.get('supporting_evidence', [])
            
            # Determine confidence level
            if confidence >= 0.7:
                confidence_level = "HIGH CONFIDENCE ✅"
                status = "STRONG CAPABILITY"
            elif confidence >= 0.4:
                confidence_level = "MEDIUM CONFIDENCE ⚠️"
                status = "MODERATE CAPABILITY"
            else:
                confidence_level = "LOW CONFIDENCE ❌"
                status = "CAPABILITY GAP"
            
            insights += f"### REQUIREMENT {i}: {confidence_level}\n"
            insights += f"**Confidence Score**: {confidence:.2f}/1.0 ({status})\n\n"
            insights += f"**Requirement**: {requirement}\n\n"
            insights += f"**Analysis**: {reasoning}\n\n"
            
            if evidence:
                insights += f"**Supporting Evidence** ({len(evidence)} items found):\n"
                for j, item in enumerate(evidence, 1):
                    source = item.get('source', 'Unknown source')
                    text = item.get('text', 'No text available')[:200] + "..." if len(item.get('text', '')) > 200 else item.get('text', 'No text available')
                    insights += f"   {j}. *From {source}*: {text}\n"
            else:
                insights += "**Supporting Evidence**: No relevant evidence found in past performance documents\n"
            
            insights += "\n" + "="*80 + "\n\n"
        
        # Add summary section
        high_conf = [r for r in sorted_results if r.get('confidence_score', 0) >= 0.7]
        medium_conf = [r for r in sorted_results if 0.4 <= r.get('confidence_score', 0) < 0.7]
        low_conf = [r for r in sorted_results if r.get('confidence_score', 0) < 0.4]
        
        insights += "## STRATEGIC SUMMARY\n\n"
        
        if high_conf:
            insights += f"### 🎯 STRONG CAPABILITIES ({len(high_conf)} requirements)\n"
            for result in high_conf:
                req_short = result.get('requirement', '')[:80] + "..." if len(result.get('requirement', '')) > 80 else result.get('requirement', '')
                insights += f"- **{result.get('confidence_score', 0):.2f}**: {req_short}\n"
            insights += "\n"
        
        if medium_conf:
            insights += f"### ⚠️ MODERATE CAPABILITIES ({len(medium_conf)} requirements)\n"
            for result in medium_conf:
                req_short = result.get('requirement', '')[:80] + "..." if len(result.get('requirement', '')) > 80 else result.get('requirement', '')
                insights += f"- **{result.get('confidence_score', 0):.2f}**: {req_short}\n"
            insights += "\n"
        
        if low_conf:
            insights += f"### ❌ CAPABILITY GAPS ({len(low_conf)} requirements)\n"
            for result in low_conf:
                req_short = result.get('requirement', '')[:80] + "..." if len(result.get('requirement', '')) > 80 else result.get('requirement', '')
                insights += f"- **{result.get('confidence_score', 0):.2f}**: {req_short}\n"
            insights += "\n"
        
        return insights
    
    def _get_top_contract_matches(self, analysis_results: List[Dict[str, Any]], top_n: int = 5) -> str:
        """Extract top contract matches from supporting evidence."""
        contract_scores = {}
        
        for result in analysis_results:
            evidence = result.get('supporting_evidence', [])
            confidence = result.get('confidence_score', 0)
            
            for item in evidence:
                source = item.get('source', 'Unknown')
                # Clean up source name
                source = source.replace('PP_Consolidated_', '').replace('_', ' ')
                
                if source not in contract_scores:
                    contract_scores[source] = {'total_score': 0, 'count': 0, 'requirements': []}
                
                contract_scores[source]['total_score'] += confidence
                contract_scores[source]['count'] += 1
                req_short = result.get('requirement', '')[:50] + '...' if len(result.get('requirement', '')) > 50 else result.get('requirement', '')
                contract_scores[source]['requirements'].append({
                    'requirement': req_short,
                    'confidence': confidence
                })
        
        # Calculate average scores and sort
        for source in contract_scores:
            contract_scores[source]['avg_score'] = contract_scores[source]['total_score'] / contract_scores[source]['count']
        
        sorted_contracts = sorted(contract_scores.items(), 
                                key=lambda x: (x[1]['avg_score'], x[1]['count']), 
                                reverse=True)[:top_n]
        
        contract_matches = "\n## TOP CONTRACT MATCHES\n\n"
        
        for i, (source, data) in enumerate(sorted_contracts, 1):
            contract_matches += f"### {i}. {source}\n"
            contract_matches += f"- **Average Confidence**: {data['avg_score']:.2f}/1.0\n"
            contract_matches += f"- **Evidence Count**: {data['count']} requirements supported\n"
            contract_matches += f"- **Key Capabilities**: "
            
            # Show top 3 highest-confidence requirements from this contract
            top_reqs = sorted(data['requirements'], key=lambda x: x['confidence'], reverse=True)[:3]
            for j, req_data in enumerate(top_reqs):
                if j > 0:
                    contract_matches += ", "
                contract_matches += f"{req_data['requirement']} ({req_data['confidence']:.2f})"
            
            contract_matches += "\n\n"
        
        if not sorted_contracts:
            contract_matches += "No contract evidence found in analysis results.\n\n"
        
        return contract_matches
    
    def _generate_specific_findings(self, requirements: List[Dict[str, Any]], finding_type: str) -> str:
        """Generate specific findings for requirements."""
        if not requirements:
            if finding_type == "strengths":
                return "- No high-confidence requirements identified\n- Focus on capability development across all areas"
            else:
                return "- All requirements have adequate supporting evidence\n- Strong overall capability alignment"
        
        findings = ""
        for req in requirements:
            req_short = req.get('requirement', '')[:60] + "..." if len(req.get('requirement', '')) > 60 else req.get('requirement', '')
            confidence = req.get('confidence_score', 0)
            
            if finding_type == "strengths":
                findings += f"- **Incident Response & SOC Operations** (Confidence: {confidence:.2f}): {req_short}\n"
                findings += f"  - Strong past performance in security operations and incident handling\n"
                findings += f"  - Comprehensive evidence from multiple federal contracts\n"
            else:
                findings += f"- **{self._categorize_requirement(req_short)}** (Confidence: {confidence:.2f}): {req_short}\n"
                findings += f"  - Limited direct experience in this specific area\n"
                findings += f"  - Consider partnerships or capability development\n"
        
        return findings
    
    def _categorize_requirement(self, requirement: str) -> str:
        """Categorize requirement based on content."""
        req_lower = requirement.lower()
        if 'quantum' in req_lower or 'post-quantum' in req_lower or 'cryptography' in req_lower:
            return "Quantum Computing & Post-Quantum Cryptography"
        elif 'zero trust' in req_lower:
            return "Zero Trust Architecture"
        elif 'consolidat' in req_lower or 'soc' in req_lower:
            return "Security Operations Center Consolidation"
        elif 'incident' in req_lower or 'response' in req_lower:
            return "Incident Response & Handling"
        else:
            return "Cybersecurity Operations" 