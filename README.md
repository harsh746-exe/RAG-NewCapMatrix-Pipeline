# RAG Capability Matrix Analysis System

A sophisticated RAG (Retrieval-Augmented Generation) based system for analyzing contract requirements against past performance documents using Large Language Models (OpenAI or Ollama). This system extracts text from PDFs, creates embeddings, stores them in a vector store, and uses LLMs to generate structured capability analysis with confidence scores, evidence, and reasoning.

## 🚀 Features

- **PDF Text Extraction**: Automated extraction of text from PDF documents
- **Vector Embeddings**: Creates and stores embeddings using ChromaDB vector store
- **LLM Integration**: Supports both OpenAI and Ollama models
- **Structured Analysis**: Generates detailed capability analysis with confidence scores
- **Executive Reports**: Produces comprehensive, stakeholder-friendly reports
- **Multi-format Output**: Generates JSON, Excel, and markdown reports
- **Batch Processing**: Handles multiple requirements from Excel files
- **Evidence-based Reasoning**: Provides specific contract references and evidence

## 📋 Requirements

- Python 3.8+
- OpenAI API key (for OpenAI models) or Ollama (for local models)
- Required Python packages (see requirements.txt)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/egnyani/RAG-CapMatrix.git
   cd RAG-CapMatrix
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration**:
   - Copy `config.py` and update with your API keys
   - For OpenAI: Set your OpenAI API key
   - For Ollama: Ensure Ollama is running locally

## 📁 Project Structure

```
RAG-CapMatrix/
├── main_rag.py                 # Main execution script
├── rag_pipeline.py            # Core RAG pipeline implementation
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── documents/                 # Input PDF documents
├── outgoing/                  # Generated reports and outputs
├── vector_store/              # ChromaDB vector store
└── test_*.py                  # Test scripts
```

## 🚀 Usage

### Basic Usage

1. **Prepare your documents**:
   - Place PDF documents in the `documents/` folder
   - Prepare an Excel file with requirements (see template)

2. **Run the analysis**:
   ```bash
   python main_rag.py
   ```

3. **View results**:
   - Check `outgoing/` folder for generated reports
   - Review JSON and Excel outputs
   - Read the executive capability report

### Advanced Usage

#### Custom Configuration
Edit `config.py` to customize:
- Model selection (OpenAI vs Ollama)
- Temperature and other LLM parameters
- File paths and output formats

#### Test Individual Components
```bash
# Test report generation
python test_comprehensive_report.py

# Test enhanced pipeline
python test_enhanced_report.py

# Test simple report
python test_simple_report.py
```

## 📊 Output Formats

### 1. JSON Analysis (`rag_requirement_matches.json`)
Structured data with:
- Requirement analysis
- Confidence scores
- Evidence and reasoning
- Contract alignments

### 2. Excel Report (`rag_requirement_analysis_results.xlsx`)
Spreadsheet format with:
- Detailed requirement breakdowns
- Capability scores
- Evidence summaries
- Recommendations

### 3. Executive Report (`EXECUTIVE_CAPABILITY_REPORT_*.txt`)
Comprehensive narrative report including:
- Executive summary
- Best-aligned contracts
- Key strengths
- Identified gaps
- Strategic recommendations

## 🔧 Configuration

### Model Selection
```python
# In config.py
USE_OPENAI = True  # Set to False for Ollama
OPENAI_API_KEY = "your-api-key-here"
OLLAMA_BASE_URL = "http://localhost:11434"
```

### LLM Parameters
```python
TEMPERATURE = 0.1
MAX_TOKENS = 4000
MODEL_NAME = "gpt-4"  # or "llama2" for Ollama
```

## 📈 Report Features

### Executive Summary
- High-level capability assessment
- Overall confidence scores
- Key contract alignments

### Best-Aligned Contracts
- Top matching contracts with scores
- Specific requirement alignments
- Evidence from past performance

### Strengths Analysis
- Categorized by capability areas
- Specific contract references
- Confidence levels

### Gap Analysis
- Identified capability gaps
- Risk assessment
- Mitigation strategies

### Recommendations
- Strategic next steps
- Resource allocation
- Timeline considerations

## 🧪 Testing

The system includes comprehensive test scripts:

- `test_comprehensive_report.py`: Tests full report generation
- `test_enhanced_report.py`: Tests enhanced pipeline features
- `test_simple_report.py`: Tests basic functionality

Run tests to verify system functionality:
```bash
python test_comprehensive_report.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Run `python install_dependencies.py` to fix missing packages
2. **API Errors**: Verify your OpenAI API key or Ollama connection
3. **Memory Issues**: Reduce batch size or use smaller models

### Debug Mode
Enable debug logging in `config.py`:
```python
DEBUG_MODE = True
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with LangChain for LLM orchestration
- Uses ChromaDB for vector storage
- Integrates with OpenAI and Ollama APIs

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review test scripts for examples

---

**Note**: This system is designed for federal contracting and capability analysis. Ensure compliance with relevant regulations and data handling requirements. 