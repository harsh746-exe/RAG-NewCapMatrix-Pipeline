#!/bin/bash

# RAG Analysis Workflow Script
# This script automates common workflows for the RAG pipeline

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_error "Virtual environment not found. Please run: python -m venv .venv"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  clean           Clean output files (default: outputs only)"
    echo "  clean-all       Clean all files (outputs, cache, vector store)"
    echo "  extract <pdf>   Extract requirements from PDF"
    echo "  test            Run RAG analysis in test mode (10 requirements)"
    echo "  prod            Run RAG analysis in production mode (all requirements)"
    echo "  full-clean      Clean everything and run fresh analysis"
    echo ""
    echo "Examples:"
    echo "  $0 clean"
    echo "  $0 extract \"data/raw/document.pdf\""
    echo "  $0 test"
    echo "  $0 prod"
    echo "  $0 full-clean"
}

# Main script logic
case "${1:-help}" in
    "clean")
        print_status "Cleaning output files..."
        .venv/bin/python cleanup.py --outputs
        print_success "Output files cleaned!"
        ;;
    
    "clean-all")
        print_status "Cleaning all files (outputs, cache, vector store)..."
        .venv/bin/python cleanup.py --all
        print_success "All files cleaned!"
        ;;
    
    "extract")
        if [ -z "$2" ]; then
            print_error "Please provide a PDF file path"
            echo "Usage: $0 extract \"path/to/document.pdf\""
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            print_error "File not found: $2"
            exit 1
        fi
        
        print_status "Extracting requirements from: $2"
        .venv/bin/python src/core/extract_sow_text.py "$2"
        print_success "Requirements extracted successfully!"
        ;;
    
    "test")
        print_status "Running RAG analysis in test mode..."
        .venv/bin/python main.py --mode test
        print_success "Test analysis completed!"
        ;;
    
    "prod")
        print_status "Running RAG analysis in production mode..."
        .venv/bin/python main.py --mode prod
        print_success "Production analysis completed!"
        ;;
    
    "full-clean")
        print_status "Performing full clean and fresh analysis..."
        
        print_status "Step 1: Cleaning all files..."
        .venv/bin/python cleanup.py --all
        
        print_status "Step 2: Checking for requirements file..."
        if [ ! -f "data/outputs/requirements_matrix.xlsx" ]; then
            print_warning "No requirements matrix found. Please extract requirements first:"
            echo "  $0 extract \"path/to/your/document.pdf\""
            exit 1
        fi
        
        print_status "Step 3: Running fresh analysis..."
        .venv/bin/python main.py --mode test
        
        print_success "Full clean and analysis completed!"
        ;;
    
    "help"|"-h"|"--help"|*)
        show_usage
        ;;
esac