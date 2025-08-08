import fitz
import json
import re
import sys
import os
import argparse
from typing import Dict, List, Tuple
import openpyxl
from openpyxl.styles import Font
import spacy

def normalize_font(font_name): 
    """Normalize font names to determine if they are bold."""
    return "bold" in font_name.lower()

def extract_bold_and_all_text(pdf_path):
    """Extract both bold headings and all text from PDF"""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF file not found: '{pdf_path}'")
        
    try:
        pdf_document = fitz.open(pdf_path)
        bold_lines = []
        all_text = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_instances = page.get_text("dict")["blocks"]

            temp_heading = ""
            for block in text_instances:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        bold_char_count = 0
                        total_char_count = 0
                        
                        for span in line["spans"]:
                            total_char_count += len(span["text"])
                            if normalize_font(span["font"]):
                                bold_char_count += len(span["text"])
                            line_text += span["text"]
                        
                        if line_text.strip():
                            # Check if 60% of the characters are bold
                            if total_char_count > 0 and (bold_char_count / total_char_count) >= 0.6:
                                if temp_heading:
                                    temp_heading += " " + line_text.strip()
                                else:
                                    temp_heading = line_text.strip()
                            else:
                                if temp_heading:
                                    bold_lines.append((len(all_text), temp_heading))
                                    all_text.append(f"%%heading%%{temp_heading}")
                                    temp_heading = ""
                                all_text.append(line_text.strip())
        
        pdf_document.close()

        if temp_heading:
            bold_lines.append((len(all_text), temp_heading))
            all_text.append(f"%%heading%%{temp_heading}")

        return bold_lines, all_text
    except Exception as e:
        raise Exception(f"Error opening PDF file: {e}")

def text_list_to_dict(text_list):
    """Convert a list of text with headings marked to a dictionary structure"""
    text_dict = {}
    current_heading = None
    heading_counter = {}
    
    for line in text_list:
        if line.startswith(r"%%heading%%"):
            parsed_heading = line[11:].strip()
            
            if parsed_heading in text_dict:
                heading_counter[parsed_heading] = heading_counter.get(parsed_heading, 1) + 1
                current_heading = f"{parsed_heading}_{heading_counter[parsed_heading]}"
            else:
                current_heading = parsed_heading
                heading_counter[parsed_heading] = 1
                
            text_dict[current_heading] = ""
        elif current_heading is not None:
            text_dict[current_heading] += line + "\n"
    
    for heading in text_dict:
        text_dict[heading] = text_dict[heading].strip()
    
    return text_dict

def clean_text(text):
    """Clean and normalize text"""
    text = text.replace("'", "'")  # Replace curly apostrophe with straight apostrophe
    text = re.sub(r'(?<!-)\n(?!-)', ' ', text)
    text = text.replace('\n', '')
    text = text.replace("\u2022", "•")
    text = text.replace(r"\netc.\n", "et cetera.")
    return text.strip()

def extract_requirements_improved(text_dict: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Extract requirements from text sections using improved logic.
    This captures ALL meaningful content under each heading, not just contractor-specific actions.
    """
    requirements_dict = {}
    nlp = spacy.load("en_core_web_lg")
    
    for heading, content in text_dict.items():
        if not content.strip():
            continue
            
        # Clean the content
        content = clean_text(content)
        
        # Process with spaCy to get sentences
        doc = nlp(content)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        requirements = []
        
        # Look for bullet points first
        if "•" in content:
            bullet_items = [item.strip() for item in content.split("•") if item.strip()]
            for item in bullet_items:
                if len(item) > 10:  # Filter out very short items
                    requirements.append(item)
        
        # If no bullet points, look for numbered lists
        elif re.search(r'\d+\.\s+', content):
            numbered_items = re.split(r'\d+\.\s+', content)
            for item in numbered_items[1:]:  # Skip first empty split
                item = item.strip()
                if len(item) > 10:
                    # Take only the first sentence if it's very long
                    if len(item) > 200:
                        first_sentence = item.split('.')[0] + '.' if '.' in item else item[:200] + '...'
                        requirements.append(first_sentence)
                    else:
                        requirements.append(item)
        
        # If no structured lists, break into meaningful sentences
        else:
            for sentence in sentences:
                # Filter out very short sentences and common headers
                if (len(sentence) > 20 and 
                    not sentence.lower().startswith(('the following', 'as follows', 'including but not limited')) and
                    not re.match(r'^\d+\.\d+', sentence)):  # Skip section numbers
                    
                    # Limit sentence length for readability
                    if len(sentence) > 300:
                        sentence = sentence[:297] + "..."
                    
                    requirements.append(sentence)
        
        # If still no requirements found, use the entire content as one requirement
        if not requirements and content:
            if len(content) > 300:
                content = content[:297] + "..."
            requirements.append(content)
        
        requirements_dict[heading] = requirements
    
    return requirements_dict

def save_to_excel_improved(requirements_dict: Dict[str, List[str]], output_path: str):
    """Save requirements to Excel with improved formatting"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requirements Matrix"
    
    # Set headers
    bold_font = Font(bold=True)
    ws['A1'] = 'Requirements'
    ws['B1'] = 'Rating'
    ws['C1'] = 'Past Performance'
    
    for col in ['A1', 'B1', 'C1']:
        ws[col].font = bold_font
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 80
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 60
    
    row_idx = 2
    
    for section, requirements in requirements_dict.items():
        # Add section header in bold
        ws.cell(row=row_idx, column=1, value=section).font = bold_font
        row_idx += 1
        
        # Add each requirement
        for requirement in requirements:
            ws.cell(row=row_idx, column=1, value=requirement)
            ws.cell(row=row_idx, column=2, value="")  # Empty rating column
            ws.cell(row=row_idx, column=3, value="")  # Empty past performance column
            row_idx += 1
    
    # Add END marker
    ws.cell(row=row_idx, column=1, value="END.").font = bold_font
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)

def process_selected_text_improved(start_index, end_index, bold_lines, all_text):
    """Process selected text with improved extraction"""
    if start_index < 0 or end_index >= len(bold_lines) or start_index > end_index:
        raise ValueError("Invalid start or end indices")

    start_text_index = bold_lines[start_index][0]
    end_text_index = bold_lines[end_index][0]

    selected_text = all_text[start_text_index:end_text_index + 1]
    text_dict = text_list_to_dict(selected_text)
    
    return text_dict

def save_to_json_improved(data, output_path="outgoing/document_extracted_requirements.json"):
    """Save data to JSON and Excel with improved extraction"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Extract requirements using improved logic
    requirements_dict = extract_requirements_improved(data)
    
    # Save to Excel
    excel_path = os.path.join(os.path.dirname(output_path), "requirements_matrix.xlsx")
    save_to_excel_improved(requirements_dict, excel_path)
    
    return output_path, excel_path

class ImprovedExtractSOWText:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def main(self):
        try:
            print(f"Processing PDF: {self.pdf_path}")
            bold_lines, all_text = extract_bold_and_all_text(self.pdf_path)
            
            if not bold_lines:
                print("Warning: No bold lines detected in the document.")
                return
            
            self._run_cli(bold_lines, all_text)
                
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            sys.exit(1)

    def _run_cli(self, bold_lines, all_text):
        """Command line interface with automatic range detection"""
        print("\nDetected sections:")
        for idx, (text_index, line) in enumerate(bold_lines, start=1):
            print(f"{idx}: {line}")
        
        # Auto-detect likely range (skip first and last sections if they look like headers/footers)
        if len(bold_lines) >= 3:
            # Skip first section if it looks like a title
            start_idx = 0
            if any(word in bold_lines[0][1].lower() for word in ['questions', 'areas', 'input', 'rfi', 'title']):
                start_idx = 1
            
            # Find END marker or use second-to-last section
            end_idx = len(bold_lines) - 1
            for idx, (_, line) in enumerate(bold_lines):
                if line.strip().lower() in ['end.', 'end']:
                    end_idx = idx - 1 if idx > 0 else idx
                    break
            
            print(f"\nAuto-detected range: {start_idx + 1} to {end_idx + 1}")
            
            while True:
                try:
                    user_input = input(f"\nPress Enter to use auto-detected range ({start_idx + 1}-{end_idx + 1}), or enter custom range (start end): ").strip()
                    
                    if not user_input:
                        # Use auto-detected range
                        start_index = start_idx
                        end_index = end_idx
                    else:
                        # Parse custom range
                        parts = user_input.split()
                        if len(parts) != 2:
                            raise ValueError("Please enter two numbers (start end) or press Enter for auto-range")
                        start_index = int(parts[0]) - 1
                        end_index = int(parts[1]) - 1
                    
                    # Process the text
                    text_dict = process_selected_text_improved(start_index, end_index, bold_lines, all_text)
                    
                    # Save the processed text
                    json_path, excel_path = save_to_json_improved(text_dict)
                    
                    print(f"\nFiles saved successfully:")
                    print(f"- JSON: {json_path}")
                    print(f"- Excel: {excel_path}")
                    break
                    
                except ValueError as e:
                    print(f"Error: {e}")
                except KeyboardInterrupt:
                    sys.exit(0)
        else:
            # Fallback to manual input for simple cases
            while True:
                try:
                    start_index = int(input("\nEnter start index: ")) - 1
                    end_index = int(input("Enter end index: ")) - 1
                    
                    text_dict = process_selected_text_improved(start_index, end_index, bold_lines, all_text)
                    json_path, excel_path = save_to_json_improved(text_dict)
                    
                    print(f"\nFiles saved successfully:")
                    print(f"- JSON: {json_path}")
                    print(f"- Excel: {excel_path}")
                    break
                    
                except ValueError as e:
                    print(f"Error: {e}")
                except KeyboardInterrupt:
                    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract SOW text from PDF files (Improved Version)')
    parser.add_argument('pdf_path', nargs='?', help='Path to the PDF file')
    
    args = parser.parse_args()
    
    if args.pdf_path:
        pdf_path = args.pdf_path
    else:
        print("Usage: python extract_sow_text_improved.py <path_to_pdf>")
        sys.exit(1)
        
    extractor = ImprovedExtractSOWText(pdf_path)
    extractor.main()

    print("\nOutput files:")
    print(f"- JSON: outgoing/document_extracted_requirements.json")
    print(f"- Excel: requirements_matrix.xlsx")