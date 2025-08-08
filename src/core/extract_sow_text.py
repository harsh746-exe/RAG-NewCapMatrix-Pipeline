import fitz
import json
import re
import sys
import os
import argparse
from typing import Dict
import openpyxl
from openpyxl.styles import Font
import tkinter as tk
from tkinter import messagebox
import spacy
import shutil

def normalize_font(font_name): 
    """Normalize font names to determine if they are bold."""
    return "bold" in font_name.lower()

def extract_bold_and_all_text(pdf_path):
    # Check if file exists before opening
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF file not found: '{pdf_path}'")
        
    # Open the PDF file
    try:
        pdf_document = fitz.open(pdf_path)
        bold_lines = []
        all_text = []

        # Iterate through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_instances = page.get_text("dict")["blocks"]

            # Iterate through text blocks
            temp_heading = ""  # Temporary variable to store multiline headings
            for block in text_instances:
                if "lines" in block:  # Check if the block contains lines of text
                    for line in block["lines"]:
                        line_text = ""
                        bold_char_count = 0
                        total_char_count = 0  # Total characters in the line
                        for span in line["spans"]:
                            total_char_count += len(span["text"])  # Count total characters in the line

                            # Check if the text is bold
                            if normalize_font(span["font"]):
                                bold_char_count += len(span["text"])  # Count bold characters

                            line_text += span["text"]  # Concatenate text from spans
                        
                        # Process the text if it contains content
                        if line_text.strip():
                            # Check if 80% of the characters are bold
                            if total_char_count > 0 and (bold_char_count / total_char_count) >= 0.6:
                                if temp_heading:
                                    temp_heading += " " + line_text.strip()  # Combine multiline heading
                                else:
                                    temp_heading = line_text.strip()
                            else:
                                # Add the temporary heading if it exists and reset
                                if temp_heading:
                                    bold_lines.append((len(all_text), temp_heading))
                                    all_text.append(f"%%heading%%{temp_heading}")
                                    temp_heading = ""  # Reset temporary heading

                                # Add non-bold line to all_text as normal text
                                all_text.append(line_text.strip())
        
        # Close the document
        pdf_document.close()

        # Capture any remaining temp_heading as a final bold heading
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
            
            # Check if heading already exists
            if parsed_heading in text_dict:
                # Increment the counter for this heading
                heading_counter[parsed_heading] = heading_counter.get(parsed_heading, 1) + 1
                # Append counter to make the heading unique
                current_heading = f"{parsed_heading}_{heading_counter[parsed_heading]}"
            else:
                # First occurrence of the heading
                current_heading = parsed_heading
                heading_counter[parsed_heading] = 1
                
            # Initialize the heading content
            text_dict[current_heading] = ""
        elif current_heading is not None:
            # Append content to the current heading
            text_dict[current_heading] += line + "\n"
    
    # Clean up the content by removing trailing newlines
    for heading in text_dict:
        text_dict[heading] = text_dict[heading].strip()
    
    return text_dict

def clean_newlines(text):
    # Step 1: Normalize all apostrophes to standard single quote (')
    text = text.replace('’', "'")  # Replace curly apostrophe (’) with straight apostrophe (')
    
    # Step 2: Replace newlines with spaces unless surrounded by hyphens
    text = re.sub(r'(?<!-)\n(?!-)', ' ', text)  # Replace newlines with spaces if no hyphen around them

    # Step 3: Remove any remaining newlines (these are surrounded by hyphens)
    text = text.replace('\n', '')  # Remove any remaining newlines

    # Step 4: Replace any \u2022 with bullet point marker
    text = text.replace("\u2022", "•")

    text = text.replace(r"\netc.\n", "et cetera.")

    return text

def process_selected_text(start_index, end_index, bold_lines, all_text):
    """Process the selected text range and return the structured content"""
    # Validate indices
    if start_index < 0 or end_index >= len(bold_lines) or start_index > end_index:
        raise ValueError("Invalid start or end indices")

    # Identify the range in the all_text list based on bold indices
    start_text_index = bold_lines[start_index][0]
    end_text_index = bold_lines[end_index][0]

    # Extract the selected text
    selected_text = all_text[start_text_index:end_text_index + 1]
    
    # Convert to dictionary structure
    text_dict = text_list_to_dict(selected_text)
    
    # Clean the text in each section
    for heading, content in text_dict.items():
        text_dict[heading] = clean_newlines(content)
    
    return text_dict

def check_first_three_words_for_verb(potential_action):
    commonly_missed_verbs = {"conduct", "leverage", "engage", "document", "adhere", "report", "gain", "design", "implement", "draft", "validate", "abide", "coordinate", "track", "allow", "support", "institute", "inventory"}
    
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(potential_action)
    
    # Check first three tokens for VERB or AUX
    for token in doc[:3]:  # Limit to first three tokens
        if token.pos_ in {"VERB", "AUX", "ADV"} or token.text.lower() in commonly_missed_verbs:
            return True
    return False

def extract_actions(text_dict: dict) -> dict:
    # First, reformat the dictionary to have sentences
    reformatted_dict = {}
    nlp = spacy.load("en_core_web_lg")

    for key, value in text_dict.items():
        # Clean newlines and special characters from the value text
        value = clean_newlines(value)
        
        # Use SpaCy to process the text sentence by sentence
        doc = nlp(value)
        sentences = [sent.text.strip() for sent in doc.sents]
        reformatted_dict[key.strip()] = sentences

    # Regex pattern to capture the specified phrases
    pattern = r'(?i)(?:the contractor shall|contractor may be required to|the contractor will|request the contractor to|the contractor\'s responsibility to|may request the contractor to|the responsibility of the contractor to|the contractor must|contractor is responsible for|contractors shall|contractor should|contractor may need to|contractor shall|contractor\'s team shall|contractor to|contractor\'s team shall|contractor\'s responsibilities will be to|contractor expected to|contractor must)'

    actions_dict = {}

    for key, sentences in reformatted_dict.items():
        actions = []  # Use a list to maintain order
        
        for sent in sentences:
            sent_text = str(sent).strip()  # Normalize the sentence
            
            # Check if the sentence contains a list item
            if "•" in sent_text:
                potential_action_from_list = sent_text.split("•")[1].strip() if len(sent_text.split("•")) > 1 else ""
                
                # Check for the pattern match directly
                match = re.search(pattern, potential_action_from_list)
                if match:
                    split_text = re.split(pattern, potential_action_from_list)
                    if len(split_text) > 1:
                        action_text = split_text[1].strip()  # Extract the actionable part
                        if action_text and action_text not in actions:  # Avoid duplicates
                            action_text = action_text[0].upper() + action_text[1:]  # Capitalize
                            actions.append(action_text)  # Add to list
                    continue  # Skip further processing for this sentence
                
                # If no pattern match, fallback to verb-based checking
                if check_first_three_words_for_verb(potential_action_from_list):
                    capitalized_action = potential_action_from_list[0].upper() + potential_action_from_list[1:]
                    if capitalized_action not in actions:  # Avoid duplicates
                        actions.append(capitalized_action)  # Add to list

            else:
                # Check for the pattern match directly
                match = re.search(pattern, sent_text)
                if match:
                    split_text = re.split(pattern, sent_text)
                    if len(split_text) > 1:
                        action_text = split_text[1].strip()  # Extract the actionable part
                        if action_text and action_text not in actions:  # Avoid duplicates
                            action_text = action_text[0].upper() + action_text[1:]  # Capitalize
                            actions.append(action_text)  # Add to list

        actions_dict[key] = actions  # List maintains order
        
    return actions_dict

def save_to_json(data, output_path="outgoing/document_extracted_requirements.json"):
    """Save the data to a JSON file"""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Extract actions from the text
    actions_dict = extract_actions(data)
    
    # Also save to Excel
    excel_path = os.path.join(os.path.dirname(output_path), "requirements_matrix.xlsx")
    save_to_excel(actions_dict, excel_path)
    
    return output_path, excel_path

def save_to_excel(actions_dict: Dict[str, list], output_path: str):
    """
    Save the extracted actions to an Excel file with Requirement and Past Performance columns.
    
    Args:
        actions_dict: Dictionary with headings as keys and lists of actions as values
        output_path: Path to save the Excel file
    """
    # Create a new workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Requirements Matrix"
    
    # Set headers and make them bold
    bold_font = Font(bold=True)
    ws['A1'] = 'Requirements'
    ws['B1'] = 'Past Performance'
    ws['A1'].font = bold_font
    ws['B1'].font = bold_font
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 60
    ws.column_dimensions['B'].width = 60
    
    # Start populating data from row 2
    row_idx = 2
    
    # Iterate through each section and its actions
    for section, actions in actions_dict.items():
        # Add section header in bold
        ws.cell(row=row_idx, column=1, value=section).font = bold_font
        row_idx += 1
        
        # Add each action as a separate row
        for action in actions:
            ws.cell(row=row_idx, column=1, value=action)
            row_idx += 1
        
    
    # Save the workbook
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)

class ExtractSOWText:
    def __init__(self, pdf_path) -> None:
        self.pdf_path = pdf_path

    def main(self):
        try:
            # Load PDF and extract bold lines and all text
            print(f"Processing PDF: {self.pdf_path}")
            bold_lines, all_text = extract_bold_and_all_text(self.pdf_path)
            
            if not bold_lines:
                print("Warning: No bold lines detected in the document.")

            
            self._run_cli(bold_lines, all_text)
                
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            sys.exit(1)

    def _run_gui(self, bold_lines, all_text):
        # Set up the GUI
        root = tk.Tk()
        root.title("Bold Line Selector")

        # Listbox to display all bold lines with their indices
        bold_listbox = tk.Listbox(root, width=80, height=20)
        for idx, (text_index, line) in enumerate(bold_lines, start=1):
            bold_listbox.insert(tk.END, f"{idx}: {line}")
        bold_listbox.pack(pady=10)

        # Input fields for start and end indices
        start_label = tk.Label(root, text="Start (Index):")
        start_label.pack()
        start_entry = tk.Entry(root, width=10)
        start_entry.pack()

        end_label = tk.Label(root, text="End (Index):")
        end_label.pack()
        end_entry = tk.Entry(root, width=10)
        end_entry.pack()

        # Submit button to process the selected range
        def process_selection():
            try:
                start_index = int(start_entry.get()) - 1
                end_index = int(end_entry.get()) - 1
                
                # Process the text
                text_dict = process_selected_text(start_index, end_index, bold_lines, all_text)
                
                # Close the window
                root.destroy()
                
                # Save the processed text
                save_to_json(text_dict)
                
            except ValueError as e:
                messagebox.showerror("Error", f"Please enter valid indices: {e}")
        
        submit_button = tk.Button(
            root, text="Submit", command=process_selection
        )
        submit_button.pack(pady=10)

        # Run the GUI loop
        root.mainloop()
        
    def _run_cli(self, bold_lines, all_text):
        """Command line interface alternative when tkinter is not available"""
        for idx, (text_index, line) in enumerate(bold_lines, start=1):
            print(f"{idx}: {line}")
        
        while True:
            try:
                start_index = int(input("\nEnter start index: ")) - 1
                end_index = int(input("Enter end index: ")) - 1
                
                # Process the text
                text_dict = process_selected_text(start_index, end_index, bold_lines, all_text)
                
                # Save the processed text to JSON and Excel
                json_path, excel_path = save_to_json(text_dict)
                
                print(f"\nFiles saved successfully:")
                print(f"- JSON: {json_path}")
                print(f"- Excel: {excel_path}")
                break
                
            except ValueError as e:
                print(f"Error: {e}")
            except KeyboardInterrupt:
                sys.exit(0)

if __name__ == "__main__":
    # Use argparse for better command line argument handling
    parser = argparse.ArgumentParser(description='Extract SOW text from PDF files')
    parser.add_argument('pdf_path', nargs='?', help='Path to the PDF file')
    parser.add_argument('--install-deps', action='store_true', help='Print instructions for installing dependencies')
    
    args = parser.parse_args()
    
    if args.install_deps:
        print("Missing packages")
        sys.exit(0)
    
    if args.pdf_path:
        pdf_path = args.pdf_path
    else:
        print("Usage: python -m extract_sow_text <path_to_pdf> or --install-deps")
        sys.exit(1)
        
    extractor = ExtractSOWText(pdf_path)
    extractor.main()

    print("\nOutput files:")
    print(f"- JSON: outgoing/document_extracted_requirements.json")
    print(f"- Excel: requirements_matrix.xlsx")
