"""
Main RAG-based Capability Matrix Analysis Script

This script replaces the embedding-based similarity approach with a RAG pipeline
that provides better contextual understanding using LLM evaluation.
"""

import os
import json
import argparse
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font
from openpyxl.utils.dataframe import dataframe_to_rows
import re

from rag_pipeline import RAGCapabilityAnalyzer, CapabilityMatch, EvidenceItem
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define paths and settings
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_EXCEL_PATH = os.path.join(SCRIPT_DIR, "RELI_Capabilities Matrix Template.xlsx")
EXCEL_PATH = Config.EXCEL_PATH  # Input Excel file
OUTPUT_JSON = Config.OUTPUT_JSON  # Results as JSON
CHECKPOINT_FILE = Config.CHECKPOINT_FILE  # Progress checkpoint
OUTPUT_EXCEL = Config.OUTPUT_EXCEL  # Final Excel output

# Runtime mode: "test" processes only first 10 requirements, "prod" processes all
MODE = Config.DEFAULT_MODE  # Change to "prod" for full processing

def load_requirements():
    """Load requirements from the Excel file, checking for bold text formatting."""
    try:
        # Read Excel with formatting information
        df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
        
        # Check if required columns exist
        if "Requirements" not in df.columns:
            logger.error("Column 'Requirements' not found in Excel file!")
            return None
        
        # If Rating column doesn't exist, add it with empty values
        if "Rating" not in df.columns:
            logger.info("'Rating' column not found in Excel file. Adding empty ratings.")
            df["Rating"] = ""
        
        # Check which cells are bold in the Requirements column
        workbook = openpyxl.load_workbook(EXCEL_PATH)
        sheet = workbook.active
        
        # Find the column index for "Requirements"
        requirements_col_idx = None
        for col_idx, cell in enumerate(sheet[1], 1):  # 1-based indexing for openpyxl
            if cell.value == "Requirements":
                requirements_col_idx = col_idx
                break
        
        if requirements_col_idx is None:
            logger.error("Could not find 'Requirements' column in Excel file!")
            return df  # Return without bold filtering
        
        # Add a column to mark if text is bold
        df['is_bold'] = False
        
        # Check each row and mark if the text is bold
        for i, row in df.iterrows():
            # Excel row index is 1-based and includes header, so add 2
            excel_row_idx = i + 2
            
            # Get the cell in the Requirements column
            cell = sheet.cell(row=excel_row_idx, column=requirements_col_idx)
            
            # Check if the cell has any bold formatting
            is_bold = False
            if cell.font and cell.font.bold:
                is_bold = True
            
            # Mark in the DataFrame
            df.at[i, 'is_bold'] = is_bold
        
        # Print summary of bold vs. non-bold rows
        bold_count = df['is_bold'].sum()
        logger.info(f"Found {bold_count} rows with bold text in Requirements column")
        logger.info(f"Will process {len(df) - bold_count} non-bold rows")
        
        return df
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        return None

def handle_nan_values(obj):
    """Convert NaN values to empty strings in a nested object structure."""
    if isinstance(obj, dict):
        return {k: handle_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [handle_nan_values(item) for item in obj]
    elif pd.isna(obj):  # Check for NaN values
        return ""
    else:
        return obj

def load_checkpoint():
    """Load the checkpoint file if it exists."""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as file:
                checkpoint = json.load(file)
                # Fix any NaN values in the checkpoint
                checkpoint = handle_nan_values(checkpoint)
                logger.info(f"Checkpoint loaded, resuming from requirement {checkpoint['last_processed_index'] + 1}")
                # Check if we need to reset checkpoint when switching modes
                if MODE == "test" and checkpoint.get("mode", MODE) == "prod":
                    logger.warning("Switching from prod to test mode with existing checkpoint.")
                    logger.warning("Consider deleting the checkpoint file if you want to start a fresh test run.")
                return checkpoint
        return {"results": [], "last_processed_index": -1, "mode": MODE}
    except Exception as e:
        logger.error(f"Error loading checkpoint: {e}")
        return {"results": [], "last_processed_index": -1, "mode": MODE}

def save_checkpoint(results, last_idx):
    """Save a checkpoint with current progress."""
    # Handle any NaN values in results
    clean_results = handle_nan_values(results)
    
    checkpoint = {
        "results": clean_results,
        "last_processed_index": last_idx,
        "timestamp": pd.Timestamp.now().isoformat(),
        "mode": MODE
    }
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as file:
        json.dump(checkpoint, file, indent=2)
    logger.info(f"Checkpoint saved after processing requirement {last_idx + 1}")

def save_results_to_excel(result_df: pd.DataFrame, template_path: str, output_path: str):
    """
    Saves the analysis results to an Excel file, using a template and applying color-coding.
    """
    try:
        # Check if template exists
        if not os.path.exists(template_path):
            logger.warning(f"Template file not found: {template_path}")
            logger.info("Saving results without template styling...")
            result_df.to_excel(output_path, index=False, engine="openpyxl")
            logger.info(f"Successfully saved results to {output_path}")
            return
            
        # Load the template workbook
        workbook = openpyxl.load_workbook(template_path)
        sheet = workbook.active  # Use the active sheet from the template

        # Define color fills
        
# Strong Green (used for "Strong Capabilities")
        green_fill = PatternFill(start_color="00B050", end_color="00B050", fill_type="solid")

        # Strong Yellow (used for "Some Capabilities")
        yellow_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")

        # Strong Red (used for "No Capabilities")
        red_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
        gray_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        bold_font = Font(bold=True)
        
        title_pattern = re.compile(r'^\s*(\d+(\.\d+)*)\s+[A-Za-z]')

        # Find the starting row to write data (e.g., after the headers)
        start_row = 1
        for row in sheet.iter_rows():
            if any(cell.value for cell in row):
                start_row = row[0].row + 1

        # Prepare a dataframe for writing, dropping the helper 'is_bold' column
        df_to_write = result_df.drop(columns=['is_bold'], errors='ignore')

        # Write data to the sheet, applying styles
        for r_idx, row in enumerate(dataframe_to_rows(df_to_write, index=False, header=True), start_row):
            is_title_row = False
            # Check if the current row is a title row (after the header)
            if r_idx > start_row:
                try:
                    original_df_idx = r_idx - start_row - 1
                    original_series = result_df.iloc[original_df_idx]
                    requirement_text = str(original_series.get('Requirements', ''))
                    
                    if original_series.get('is_bold', False) or title_pattern.match(requirement_text):
                        is_title_row = True
                except (IndexError, KeyError):
                    pass

            # Find the index of the 'Rating' column to apply specific styling
            try:
                rating_df_idx = df_to_write.columns.get_loc('Rating') + 1
            except KeyError:
                rating_df_idx = -1

            for c_idx, value in enumerate(row, 1):
                cell = sheet.cell(row=r_idx, column=c_idx, value=value)
                
                if is_title_row:
                    cell.fill = gray_fill
                    cell.font = bold_font
                elif c_idx == rating_df_idx:
                    # Apply confidence score styling only if it's not a title row
                    try:
                        confidence = float(value)
                        if confidence > 0.7:
                            cell.fill = green_fill
                        elif confidence >= 0.4:
                            cell.fill = yellow_fill
                        else:
                            cell.fill = red_fill
                    except (ValueError, TypeError):
                        pass # Not a numeric confidence score, probably the header

        # Save the workbook
        workbook.save(output_path)
        logger.info(f"Successfully saved styled results to {output_path}")

    except Exception as e:
        logger.error(f"Error saving to Excel with template: {e}")
        # Fallback to simple save if templating fails
        result_df.to_excel(output_path, index=False, engine="openpyxl")
        logger.info(f"Fallback: Saved results to {output_path} without styling")

def generate_capability_report(analyzer: RAGCapabilityAnalyzer, results: List[Dict[str, Any]], output_path: str):
    """
    Generates a comprehensive executive capability report using an LLM.
    Creates a professional one-page document for stakeholder decision-making.
    """
    logger.info("Generating comprehensive executive capability report...")
    
    # Generate timestamp for the report
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a more professional filename
    base_dir = os.path.dirname(output_path)
    if MODE == "test":
        report_filename = f"EXECUTIVE_CAPABILITY_REPORT_TEST_{timestamp}.txt"
    else:
        report_filename = f"EXECUTIVE_CAPABILITY_REPORT_{timestamp}.txt"
    
    report_path = os.path.join(base_dir, report_filename)
    
    # Generate the comprehensive report
    report_content = analyzer.generate_summary_report(results)
    
    # Add header information
    header = f"""
{'='*80}
EXECUTIVE CAPABILITY ANALYSIS REPORT
Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
Analysis Mode: {MODE.upper()}
Total Requirements Analyzed: {len([r for r in results if r.get('confidence_score') is not None])}
{'='*80}

"""
    
    full_report = header + report_content
    
    # Save the report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    logger.info(f"Executive capability report saved to {report_path}")
    
    # Also save a copy with the original filename for compatibility
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    return report_path

def main():
    """Main function to run the RAG-based capability analysis."""
    logger.info(f"Running RAG-based capability analysis in {MODE.upper()} mode")
    
    # Check if the input files exist
    if not os.path.exists(EXCEL_PATH):
        logger.error(f"ERROR: Input Excel file not found at {EXCEL_PATH}")
        logger.error(f"Please create an Excel file with a 'Requirements' column and save it as 'requirements_matrix.xlsx' in the outgoing directory")
        return
    
    # Check if documents directory has any PDFs
    pdf_count = sum(1 for f in os.listdir(Config.DOCUMENTS_DIR) if f.lower().endswith('.pdf')) if os.path.exists(Config.DOCUMENTS_DIR) else 0
    if pdf_count == 0:
        logger.warning(f"No PDF documents found in {Config.DOCUMENTS_DIR}")
        logger.warning(f"Please add PDF documents to be analyzed to this directory")
        return
    
    # Initialize RAG analyzer based on the provider from config
    logger.info("Initializing RAG Capability Analyzer...")
    try:
        if Config.LLM_PROVIDER == "openai":
            model_name = Config.OPENAI_MODEL_NAME
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.error("OPENAI_API_KEY environment variable not set for OpenAI provider!")
                return
            analyzer = RAGCapabilityAnalyzer(
                provider="openai",
                openai_api_key=openai_api_key,
                model_name=model_name,
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                top_k_retrieval=Config.TOP_K_RETRIEVAL,
                vector_store_path=Config.VECTOR_STORE_PATH
            )
        elif Config.LLM_PROVIDER == "ollama":
            model_name = Config.OLLAMA_MODEL_NAME
            analyzer = RAGCapabilityAnalyzer(
                provider="ollama",
                model_name=model_name,
                ollama_base_url=Config.OLLAMA_BASE_URL,
                chunk_size=Config.CHUNK_SIZE,
                chunk_overlap=Config.CHUNK_OVERLAP,
                top_k_retrieval=Config.TOP_K_RETRIEVAL,
                vector_store_path=Config.VECTOR_STORE_PATH
            )
        else:
            raise ValueError("Invalid LLM_PROVIDER configured. Choose 'openai' or 'ollama'.")
        
        # Process documents and create vector store
        logger.info("Processing past performance documents...")
        analyzer.process_documents(Config.DOCUMENTS_DIR)
        
    except Exception as e:
        logger.error(f"Error initializing RAG analyzer: {e}")
        return
    
    # Load requirements from Excel
    logger.info("Loading requirements from Excel...")
    requirements_df = load_requirements()
    
    if requirements_df is None:
        logger.error("Failed to load requirements. Exiting.")
        return
    
    if len(requirements_df) == 0:
        logger.error("No requirements to process. Exiting.")
        return
    
    # Initialize new columns in the requirements dataframe
    requirements_df['Past Performance'] = ""
    # Use the 'Rating' column for the score; ensure it exists.
    if 'Rating' not in requirements_df.columns:
        requirements_df['Rating'] = None

    # Create a result dataframe with all necessary columns for processing and styling
    columns_to_keep = ['Requirements', 'Rating', 'Past Performance', 'is_bold']
    result_df = requirements_df[columns_to_keep].copy()

    # Load checkpoint if exists
    checkpoint = load_checkpoint()
    results = checkpoint["results"]
    start_idx = checkpoint["last_processed_index"] + 1
    
    # Count how many bold vs non-bold rows we have
    bold_count = requirements_df['is_bold'].sum()
    non_bold_count = len(requirements_df) - bold_count
    logger.info(f"Found {bold_count} bold requirements (will have empty analysis)")
    logger.info(f"Processing {non_bold_count} non-bold requirements out of {len(requirements_df)} total")
    
    # Get the non-bold rows for processing
    non_bold_df = requirements_df[~requirements_df['is_bold']]
    
    # Limit processing if in test mode
    if MODE == "test":
        end_idx = min(10, len(non_bold_df))
        if start_idx >= end_idx:
            logger.info(f"Test mode: Already processed {start_idx} requirements, which is >= the test limit of {end_idx}.")
            logger.info("To continue, either set MODE to 'prod' or delete the checkpoint file.")
            return
        logger.info(f"Test mode: Will process requirements from index {start_idx} to {end_idx-1}")
        requirements_to_process = non_bold_df.iloc[start_idx:end_idx]
    else:  # prod mode
        requirements_to_process = non_bold_df.iloc[start_idx:]
        logger.info(f"Production mode: Will process all remaining requirements from index {start_idx} to {len(non_bold_df)-1}")
    
    # Process each non-bold requirement
    try:
        for idx, row in requirements_to_process.iterrows():
            requirement = row["Requirements"]
            # Convert NaN rating to empty string
            rating_value = row.get("Rating", "")
            rating = "" if pd.isna(rating_value) else rating_value
            
            logger.info(f"Processing requirement {idx+1}/{len(non_bold_df)}: {requirement[:50]}...")
            
            # Analyze capability using RAG
            capability_match = analyzer.analyze_capability(requirement)
            
            # Format past performance for Excel output
            past_performance = analyzer.format_past_performance(capability_match)
            
            # Store results for JSON
            results.append({
                "requirement": requirement,
                "rating": rating,
                "confidence_score": capability_match.confidence_score,
                "supporting_evidence": [{"text": ev.text, "source": ev.source} for ev in capability_match.supporting_evidence],
                "reasoning": capability_match.reasoning,
                "past_performance_text": past_performance
            })
            
            # Update dataframe for Excel output
            result_df.loc[result_df['Requirements'] == requirement, 'Past Performance'] = past_performance
            result_df.loc[result_df['Requirements'] == requirement, 'Rating'] = capability_match.confidence_score
            
            # Save checkpoint after each requirement
            save_checkpoint(results, idx)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Progress has been saved.")
    except Exception as e:
        logger.error(f"An error occurred: {e}. Progress has been saved.")
    finally:
        # Save final results to JSON
        if MODE == "test":
            # Extract directory and filename
            results_dir = os.path.dirname(OUTPUT_JSON)
            results_filename = os.path.basename(OUTPUT_JSON)
            output_file = os.path.join(results_dir, f"test_{results_filename}")
            
            # Same for Excel output
            excel_dir = os.path.dirname(OUTPUT_EXCEL)
            excel_filename = os.path.basename(OUTPUT_EXCEL)
            excel_output = os.path.join(excel_dir, f"test_{excel_filename}")
        else:
            output_file = OUTPUT_JSON
            excel_output = OUTPUT_EXCEL
        
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(results, json_file, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        # Save to Excel using the new function with template and styling
        save_results_to_excel(result_df, TEMPLATE_EXCEL_PATH, excel_output)

        # Generate the comprehensive executive capability report
        report_path = generate_capability_report(analyzer, results, os.path.join(os.path.dirname(OUTPUT_EXCEL), "capability_report.txt"))
        
        # Provide summary of outputs
        logger.info("="*60)
        logger.info("ANALYSIS COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        logger.info(f"📊 Excel Results: {excel_output}")
        logger.info(f"📋 JSON Data: {output_file}")
        logger.info(f"📄 Executive Report: {report_path}")
        logger.info("="*60)
        logger.info("💡 NEXT STEPS:")
        logger.info("1. Review the Executive Report first for strategic insights")
        logger.info("2. Use the Excel file for detailed requirement-by-requirement analysis")
        logger.info("3. Reference the JSON file for programmatic access to results")
        logger.info("="*60)

        # If process completed successfully in prod mode, remove checkpoint
        if MODE == "prod" and start_idx + len(results) >= len(non_bold_df):
            if os.path.exists(CHECKPOINT_FILE):
                os.remove(CHECKPOINT_FILE)
                logger.info("Checkpoint file removed after successful completion.")
        elif MODE == "test":
            logger.info("Test mode completed. Set MODE to 'prod' to process all requirements.")

if __name__ == "__main__":
    # Allow command line override of mode
    parser = argparse.ArgumentParser(description='RAG-based Capability Matrix Analysis Script')
    parser.add_argument('--mode', choices=['test', 'prod'], 
                      help='Run mode: test (first 10 requirements) or prod (all requirements)')
    parser.add_argument('--openai-key', type=str,
                      help='OpenAI API key (if not set in environment)')
    args = parser.parse_args()
    
    if args.mode:
        MODE = args.mode
        logger.info(f"Mode set from command line: {MODE}")
    
    if args.openai_key:
        os.environ["OPENAI_API_KEY"] = args.openai_key
        logger.info("OpenAI API key set from command line")
    
    main() 