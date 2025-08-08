# RAG-Based Capability Matrix Analysis System

This project implements a **Retrieval-Augmented Generation (RAG)** pipeline to replace the previous embedding-based similarity approach for capability matrix analysis. The new system provides better contextual understanding by using LLM evaluation of retrieved chunks from past contracts.

## 🚀 Key Improvements

### Old System (Embedding-Based)
- Used sentence-transformers for similarity matching
- Simple cosine similarity between sentence embeddings
- Limited contextual understanding
- Basic similarity scores without reasoning

### New System (RAG-Based)
- **LLM-powered analysis** with contextual understanding
- **Structured output** with confidence scores and reasoning
- **Supporting evidence** from past contracts
- **Source document tracking** for transparency
- **Better text chunking** optimized for LLM consumption
- **Vector store caching** for improved performance

## 📁 Project Structure

```
├── main_rag.py              # Main RAG pipeline script
├── rag_pipeline.py          # Core RAG implementation
├── config.py                # Configuration settings
├── analyze_rag_results.py   # Analysis and visualization utilities
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
├── env_example.txt          # Example environment file
├── documents/               # Past performance PDFs
├── outgoing/                # Input Excel files
├── vector_store/            # Vector database storage
└── README_RAG.md           # This documentation
```

## 🛠️ Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp env_example.txt .env

# Edit the .env file and add your OpenAI API key
nano .env
```

Your `.env` file should contain:

```env
# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Override default model
# MODEL_NAME=gpt-4

# Optional: Override default temperature
# TEMPERATURE=0.1
```

### 3. Prepare Your Data

1. **Past Performance Documents**: Place your PDF contracts in the `documents/` directory
2. **Requirements Excel**: Create an Excel file with a "Requirements" column in the `outgoing/` directory named `requirements_matrix.xlsx`

## 🚀 Usage

### Basic Usage

```bash
# Run in test mode (first 10 requirements)
python main_rag.py --mode test

# Run in production mode (all requirements)
python main_rag.py --mode prod
```

### Automated Setup

```bash
# Run the setup script (creates .env file and validates configuration)
python setup.py
```

### Configuration

Edit `config.py` to customize:
- Chunk size and overlap for text processing
- LLM model selection
- Vector store settings
- Processing parameters

### Analysis and Visualization

```bash
# Generate summary report
python analyze_rag_results.py --file rag_requirement_matches.json

# Generate report with visualizations
python analyze_rag_results.py --file rag_requirement_matches.json --plots

# Save report to file
python analyze_rag_results.py --file rag_requirement_matches.json --output report.txt
```

### Enhanced Executive Report Generation

The system now generates a comprehensive **Executive Capability Report** that serves as the primary stakeholder document:

```bash
# Run the main analysis (generates executive report automatically)
python main_rag.py --mode prod

# Test the enhanced report generation with sample data
python test_enhanced_report.py
```

**Executive Report Features:**
- **One-page comprehensive analysis** for senior stakeholders
- **Contract alignment analysis** showing most relevant past performance
- **Domain-specific performance breakdown** (Cybersecurity, Data Management, etc.)
- **Detailed strength analysis** with specific evidence and contract references
- **Comprehensive gap analysis** with risk assessment and mitigation strategies
- **Strategic recommendations** with clear go/no-go guidance
- **Actionable next steps** with timeline and resource requirements

**Report Structure:**
1. **Executive Summary** - High-level positioning and key metrics
2. **Competitive Strengths & Contract Alignments** - Detailed capability analysis
3. **Critical Gaps & Risk Assessment** - Comprehensive gap analysis
4. **Strategic Recommendations** - Clear decision guidance
5. **Next Steps & Timeline** - Actionable implementation plan

The executive report is automatically generated with a timestamped filename (e.g., `EXECUTIVE_CAPABILITY_REPORT_20241201_143022.txt`) and serves as the primary document for stakeholder decision-making.

## 📊 Output Format

### Executive Report (Primary Document)
The system generates a comprehensive **one-page executive report** that serves as the primary stakeholder document:

- **Executive Summary**: High-level assessment with key performance metrics
- **Competitive Strengths & Contract Alignments**: Detailed analysis of strongest capabilities with specific past contract references
- **Critical Gaps & Risk Assessment**: Comprehensive analysis of areas requiring attention
- **Strategic Recommendations**: Clear go/no-go recommendation with actionable next steps
- **Next Steps & Timeline**: Immediate actions and resource requirements

**Report Features:**
- Professional executive-level language
- Specific contract alignments and evidence
- Quantified risk assessments
- Actionable recommendations
- Strategic positioning analysis
- Timestamped and professionally formatted

### Excel Output
The system generates an Excel file with:
- **Requirements**: Original requirement text
- **Rating**: Any existing ratings
- **Past Performance**: Detailed analysis including:
  - Confidence score (0.0-1.0)
  - Detailed reasoning
  - Supporting evidence from past contracts
  - Source document references

### JSON Output
Structured data with:
```json
{
  "requirement": "Requirement text",
  "rating": "Existing rating",
  "capability_match": {
    "confidence_score": 0.85,
    "supporting_evidence": ["Evidence 1", "Evidence 2"],
    "source_documents": ["Document1.pdf", "Document2.pdf"],
    "reasoning": "Detailed analysis reasoning..."
  },
  "past_performance": "Formatted output for Excel"
}
```

## 🔧 RAG Pipeline Architecture

### 1. Document Processing
- **Text Extraction**: Extracts text from PDF documents
- **Chunking**: Splits text into LLM-friendly chunks with overlap
- **Vectorization**: Creates embeddings for each chunk
- **Storage**: Stores in Chroma vector database

### 2. Requirement Analysis
- **Retrieval**: Finds most relevant chunks for each requirement
- **Context Preparation**: Prepares retrieved chunks for LLM analysis
- **LLM Evaluation**: Uses GPT to analyze capability with context
- **Structured Output**: Returns confidence score, evidence, and reasoning

### 3. Caching and Performance
- **Vector Store Caching**: Reuses processed documents
- **Checkpoint System**: Resumes interrupted processing
- **Batch Processing**: Efficient handling of multiple requirements

## 📈 Analysis Features

### Confidence Score Analysis
- Distribution analysis
- Categorization (High/Medium/Low confidence)
- Statistical summaries

### Source Document Analysis
- Most frequently referenced documents
- Average confidence scores per document
- Document relevance tracking

### Evidence Quality Analysis
- Evidence count and length statistics
- Quality metrics
- Coverage analysis

## 🔄 Migration from Old System

### File Changes
- `main.py` → `main_rag.py` (new RAG implementation)
- `analyze_document_matches.py` → `analyze_rag_results.py` (enhanced analysis)
- New: `rag_pipeline.py` (core RAG functionality)
- New: `config.py` (centralized configuration)
- New: `.env` file (API key management)

### Data Compatibility
- Same input Excel format
- Same PDF document structure
- Enhanced output with additional analysis fields

### Performance Improvements
- Better contextual understanding
- More detailed reasoning
- Structured evidence presentation
- Source document transparency

## 🎯 Example Output

### Excel Format
```
Confidence Score: 0.85

Analysis:
Based on our past performance in data management and analytics projects, 
we have strong capability to handle this requirement. Our experience 
includes similar data processing workflows and stakeholder engagement 
processes.

Supporting Evidence:
1. Successfully implemented data management system for CMS with 99.9% uptime
2. Delivered analytics dashboard serving 10,000+ users
3. Managed stakeholder communications across 15 federal agencies

Source Documents:
- PP_Consolidated_CMS_CCIIO__MIDAS.pdf
- PP_Consolidated_CMS_PCG__Data Analysis.pdf
```

## 🚨 Troubleshooting

### Common Issues

1. **Missing .env file**
   ```bash
   # Create .env file from template
   cp env_example.txt .env
   # Edit .env file and add your API key
   ```

2. **Invalid API key in .env file**
   - Ensure your API key starts with `sk-`
   - Get a valid key from: https://platform.openai.com/api-keys

3. **No PDF Documents Found**
   - Ensure PDFs are in the `documents/` directory
   - Check file permissions

4. **Excel File Not Found**
   - Create `requirements_matrix.xlsx` in `outgoing/` directory
   - Ensure it has a "Requirements" column

5. **Vector Store Issues**
   - Delete `vector_store/` directory to rebuild
   - Check disk space availability

### Performance Tips

1. **Test Mode**: Always start with `--mode test` to verify setup
2. **Chunk Size**: Adjust in `config.py` based on document complexity
3. **Model Selection**: Use `gpt-4` for better analysis (higher cost)
4. **Batch Processing**: System automatically handles rate limiting

## 📝 Configuration Options

### Environment Variables (.env file)
```env
OPENAI_API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-3.5-turbo
TEMPERATURE=0.1
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
```

### RAG Settings (`config.py`)
```python
CHUNK_SIZE = 1000          # Text chunk size
CHUNK_OVERLAP = 200        # Overlap between chunks
TOP_K_RETRIEVAL = 5        # Number of chunks to retrieve
MODEL_NAME = "gpt-3.5-turbo"  # LLM model
TEMPERATURE = 0.1          # LLM creativity level
```

### Processing Modes
- **Test Mode**: Process first 10 requirements
- **Production Mode**: Process all requirements
- **Checkpoint System**: Resume interrupted processing

## 🔮 Future Enhancements

1. **Local LLM Support**: Integration with Ollama for offline processing
2. **Multi-Modal Analysis**: Support for images and tables in PDFs
3. **Advanced Chunking**: Semantic chunking based on document structure
4. **Custom Prompts**: User-defined analysis prompts
5. **Batch Optimization**: Parallel processing for large datasets

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review configuration settings
3. Test with a small dataset first
4. Check OpenAI API usage and limits
5. Run `python test_rag_pipeline.py` for diagnostics

---

**Note**: This RAG pipeline provides significantly better contextual understanding compared to the previous embedding-based approach, making it more suitable for complex capability analysis tasks.