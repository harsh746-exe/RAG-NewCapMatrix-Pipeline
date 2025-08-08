# RAG NewCap Matrix Script - Clean Project Structure

## 🏗️ Directory Structure

```
RAG_NewCapMatrixScript-main/
├── main.py                           # Main entry point
├── cleanup.py                        # Cleanup script for outputs
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
├── PROJECT_STRUCTURE.md              # This file
├── LICENSE                           # License file
├── .gitignore                        # Git ignore rules
├── .venv/                            # Virtual environment
│
├── src/                              # Source code
│   ├── __init__.py
│   ├── run_rag_analysis.py          # Main RAG analysis script
│   ├── RELI_Capabilities Matrix Template.xlsx  # Excel template
│   │
│   ├── core/                         # Core functionality
│   │   ├── __init__.py
│   │   ├── rag_pipeline.py          # Main RAG pipeline
│   │   ├── extract_sow_text.py      # PDF text extraction
│   │   ├── tool_analyzer.py         # Tool analysis functionality
│   │   └── pdf_converter.py         # PDF conversion utilities
│   │
│   ├── config/                       # Configuration
│   │   ├── __init__.py
│   │   └── settings.py              # Configuration settings
│   │
│   └── utils/                        # Utility scripts
│       ├── __init__.py
│       ├── detailed_contract_analysis.py
│       ├── fix_encoding.py
│       ├── fix_sentence_extraction.py
│       ├── generate_comprehensive_matrix.py
│       ├── generate_template_excel_matrix.py
│       ├── run_comprehensive_analysis.py
│       ├── sentence_extractor_v3.py
│       └── separate_tool_reports.py
│
├── data/                             # Data directory
│   ├── raw/                          # Raw input files (PDFs, DOCX)
│   ├── processed/                    # Processed intermediate files
│   ├── outputs/                      # Generated outputs
│   └── vector_store/                 # Vector embeddings storage
│
├── templates/                        # Template files
│   └── RELI_Capabilities Matrix Template.xlsx
│
├── tests/                            # Test files (empty)
├── docs/                             # Documentation (empty)
└── logs/                             # Log files (empty)
```

## 🚀 Usage

### 1. Extract Requirements from PDF
```bash
.venv/bin/python src/core/extract_sow_text.py "data/raw/your_document.pdf"
```

### 2. Run RAG Analysis (Test Mode - 10 requirements)
```bash
.venv/bin/python main.py --mode test
```

### 3. Run RAG Analysis (Production Mode - All requirements)
```bash
.venv/bin/python main.py --mode prod
```

### 4. Clean Up Between Runs
```bash
# Clean only outputs (default)
.venv/bin/python cleanup.py

# Clean everything
.venv/bin/python cleanup.py --all

# Dry run to see what would be cleaned
.venv/bin/python cleanup.py --dry-run --all
```

## 📊 Output Files

The pipeline generates three main outputs in `data/outputs/`:

1. **Excel Results**: `*_rag_requirement_analysis_results.xlsx`
   - Detailed analysis with confidence scores
   - Capability matches and evidence
   - Formatted for stakeholder review

2. **JSON Data**: `*_rag_requirement_matches.json`
   - Raw analysis data
   - Programmatic access to results
   - Includes all metadata

3. **Executive Report**: `EXECUTIVE_CAPABILITY_REPORT_*.txt`
   - High-level strategic insights
   - Summary statistics
   - Key findings and recommendations

## 🔧 Configuration

- **Settings**: `src/config/settings.py`
- **API Keys**: Set `OPENAI_API_KEY` environment variable
- **Paths**: All paths are automatically configured relative to project root

## 📝 Key Features

✅ **Clean Structure**: Organized by functionality
✅ **Proper Imports**: All imports work correctly
✅ **Path Management**: Automatic path resolution
✅ **Virtual Environment**: Isolated dependencies
✅ **Template Support**: Excel template integration
✅ **Multiple Modes**: Test and production modes
✅ **Comprehensive Output**: Excel, JSON, and text reports

## 🛠️ Development

- All Python files are properly structured as packages
- Configuration is centralized in `src/config/settings.py`
- Core functionality is separated from utilities
- Easy to extend and maintain

## ✅ Status

The project structure has been completely cleaned and reorganized. All components are working correctly and the RAG pipeline is fully functional.