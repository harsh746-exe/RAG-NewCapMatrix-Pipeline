#!/usr/bin/env python3
"""
Template Excel Matrix Generator

This script generates a professional Excel matrix using the existing
RELI Capabilities Matrix Template and populates it with tool usage data.
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo
except ImportError:
    print("❌ openpyxl not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo

class TemplateExcelMatrixGenerator:
    """Generate professional Excel matrix using RELI template."""
    
    def __init__(self, template_path: str = "RELI_Capabilities Matrix Template.xlsx"):
        self.template_path = Path(template_path)
        self.workbook = None
        self.worksheet = None
        
    def load_template(self):
        """Load the existing RELI template."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
        
        print(f"📄 Loading template: {self.template_path}")
        self.workbook = openpyxl.load_workbook(self.template_path)
        
        # Get the first worksheet or create one if needed
        if len(self.workbook.sheetnames) > 0:
            self.worksheet = self.workbook.active
            print(f"📊 Using worksheet: {self.worksheet.title}")
        else:
            self.worksheet = self.workbook.create_sheet("Tool Usage Matrix")
            print("📊 Created new worksheet: Tool Usage Matrix")
        
    def find_data_start_row(self) -> int:
        """Find where to start adding data in the template."""
        
        # Look for common header patterns in the template
        for row in range(1, 20):  # Check first 20 rows
            for col in range(1, 10):  # Check first 10 columns
                cell_value = self.worksheet.cell(row=row, column=col).value
                if cell_value and isinstance(cell_value, str):
                    if any(keyword in cell_value.lower() for keyword in ['tool', 'contract', 'capability', 'technology']):
                        print(f"📍 Found potential header at row {row}: {cell_value}")
                        return row + 1
        
        # If no headers found, start at row 5 (typical for templates)
        print("📍 No headers found, starting at row 5")
        return 5
        
    def add_matrix_data(self, matrix_data: List[Dict], start_row: int):
        """Add matrix data to the template."""
        
        print(f"📊 Adding {len(matrix_data)} tool-contract combinations starting at row {start_row}")
        
        # Define the columns we want to include
        columns = [
            ('Tool', 'Tool'),
            ('Contract', 'Contract'),
            ('Contract Type', 'Contract_Type'),
            ('Mentions', 'Mentions'),
            ('Primary Business Purpose', 'Primary_Business_Purpose'),
            ('Primary Technical Type', 'Primary_Technical_Type'),
            ('Key Business Value', 'Key_Business_Value'),
            ('Usage Intensity', 'Usage_Intensity'),
            ('Business Summary', 'Business_Summary'),
            ('Usage Context', 'Usage_Context'),
            ('Context Quality', 'Context_Quality'),
            ('Business Purposes', 'Business_Purposes'),
            ('Technical Implementations', 'Technical_Implementations'),
            ('Specific Features', 'Specific_Features'),
            ('Business Values', 'Business_Value')
        ]
        
        # Add headers if starting fresh
        if start_row == 5:  # If we're starting fresh
            for col, (header_name, _) in enumerate(columns, 1):
                cell = self.worksheet.cell(row=start_row-1, column=col, value=header_name)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
        
        # Add data rows
        for i, row_data in enumerate(matrix_data):
            current_row = start_row + i
            
            for col, (_, data_key) in enumerate(columns, 1):
                value = row_data.get(data_key, '')
                cell = self.worksheet.cell(row=current_row, column=col, value=value)
                
                # Apply alternating row colors for readability
                if i % 2 == 1:
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        
        print(f"✅ Added data to rows {start_row} through {start_row + len(matrix_data) - 1}")
        return start_row + len(matrix_data)
        
    def add_summary_sheet(self, matrix_data: List[Dict]):
        """Add a summary sheet with tool statistics."""
        
        # Check if summary sheet already exists
        if "Tool Summary" in self.workbook.sheetnames:
            summary_sheet = self.workbook["Tool Summary"]
        else:
            summary_sheet = self.workbook.create_sheet("Tool Summary")
        
        # Clear existing content
        summary_sheet.delete_rows(1, summary_sheet.max_row)
        
        # Title
        summary_sheet['A1'] = "TOOL USAGE SUMMARY"
        summary_sheet['A1'].font = Font(name="Calibri", size=16, bold=True, color="366092")
        summary_sheet.merge_cells('A1:D1')
        summary_sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Headers
        headers = ["Tool", "Total Contracts", "Total Mentions", "Primary Use Cases"]
        for col, header in enumerate(headers, 1):
            cell = summary_sheet.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Calculate tool summaries
        tool_summaries = {}
        for row in matrix_data:
            tool = row['Tool']
            if tool not in tool_summaries:
                tool_summaries[tool] = {
                    'contracts': set(),
                    'mentions': 0,
                    'purposes': set()
                }
            tool_summaries[tool]['contracts'].add(row['Contract'])
            tool_summaries[tool]['mentions'] += int(row.get('Mentions', 0))
            purposes = row.get('Business_Purposes', '').split('; ')
            tool_summaries[tool]['purposes'].update(purposes)
        
        # Add tool summary data
        row = 4
        for tool, summary in tool_summaries.items():
            summary_sheet.cell(row=row, column=1, value=tool)
            summary_sheet.cell(row=row, column=2, value=len(summary['contracts']))
            summary_sheet.cell(row=row, column=3, value=summary['mentions'])
            summary_sheet.cell(row=row, column=4, value='; '.join(sorted(summary['purposes'])))
            
            # Apply alternating row colors
            if (row - 4) % 2 == 1:
                for col in range(1, 5):
                    summary_sheet.cell(row=row, column=col).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            
            row += 1
        
        # Auto-adjust column widths
        for col in range(1, 5):
            summary_sheet.column_dimensions[get_column_letter(col)].width = 20
        
        print("✅ Added Tool Summary sheet")
        
    def add_contract_summary_sheet(self, matrix_data: List[Dict]):
        """Add a summary sheet with contract statistics."""
        
        # Check if contract summary sheet already exists
        if "Contract Summary" in self.workbook.sheetnames:
            contract_sheet = self.workbook["Contract Summary"]
        else:
            contract_sheet = self.workbook.create_sheet("Contract Summary")
        
        # Clear existing content
        contract_sheet.delete_rows(1, contract_sheet.max_row)
        
        # Title
        contract_sheet['A1'] = "CONTRACT TOOL USAGE SUMMARY"
        contract_sheet['A1'].font = Font(name="Calibri", size=16, bold=True, color="366092")
        contract_sheet.merge_cells('A1:D1')
        contract_sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Headers
        headers = ["Contract", "Contract Type", "Tools Used", "Total Mentions"]
        for col, header in enumerate(headers, 1):
            cell = contract_sheet.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Calculate contract summaries
        contract_summaries = {}
        for row in matrix_data:
            contract = row['Contract']
            if contract not in contract_summaries:
                contract_summaries[contract] = {
                    'type': row.get('Contract_Type', ''),
                    'tools': set(),
                    'mentions': 0
                }
            contract_summaries[contract]['tools'].add(row['Tool'])
            contract_summaries[contract]['mentions'] += int(row.get('Mentions', 0))
        
        # Add contract summary data
        row = 4
        for contract, summary in contract_summaries.items():
            contract_sheet.cell(row=row, column=1, value=contract)
            contract_sheet.cell(row=row, column=2, value=summary['type'])
            contract_sheet.cell(row=row, column=3, value=', '.join(sorted(summary['tools'])))
            contract_sheet.cell(row=row, column=4, value=summary['mentions'])
            
            # Apply alternating row colors
            if (row - 4) % 2 == 1:
                for col in range(1, 5):
                    contract_sheet.cell(row=row, column=col).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            
            row += 1
        
        # Auto-adjust column widths
        for col in range(1, 5):
            contract_sheet.column_dimensions[get_column_letter(col)].width = 25
        
        print("✅ Added Contract Summary sheet")
        
    def format_worksheet(self):
        """Apply final formatting to the worksheet."""
        
        # Auto-adjust column widths for better readability
        column_widths = {
            'A': 15,  # Tool
            'B': 35,  # Contract
            'C': 20,  # Contract Type
            'D': 10,  # Mentions
            'E': 25,  # Primary Business Purpose
            'F': 20,  # Primary Technical Type
            'G': 20,  # Key Business Value
            'H': 15,  # Usage Intensity
            'I': 50,  # Business Summary
            'J': 60,  # Usage Context
            'K': 15,  # Context Quality
            'L': 40,  # Business Purposes
            'M': 40,  # Technical Implementations
            'N': 40,  # Specific Features
            'O': 40   # Business Values
        }
        
        for col, width in column_widths.items():
            if col in self.worksheet.column_dimensions:
                self.worksheet.column_dimensions[col].width = width
        
        # Set row heights for better readability
        for row in range(1, self.worksheet.max_row + 1):
            self.worksheet.row_dimensions[row].height = 20
        
        print("✅ Applied formatting to worksheet")
        
    def save_template_excel(self, filename: str):
        """Save the populated template Excel file."""
        self.workbook.save(filename)
        print(f"✅ Template Excel matrix saved: {filename}")

def main():
    """Generate template Excel matrix using RELI template."""
    print("📊 Starting RELI Template Excel Matrix Generation")
    print("=" * 60)
    
    # Find the most recent fixed matrix
    matrix_files = list(Path('.').glob('*FIXED*.csv'))
    if not matrix_files:
        print("❌ No fixed matrix files found!")
        return
    
    # Use the most recent one
    latest_matrix = max(matrix_files, key=lambda x: x.stat().st_mtime)
    print(f"📄 Processing: {latest_matrix}")
    
    try:
        # Read the matrix data
        with open(latest_matrix, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            matrix_data = list(reader)
        
        print(f"📊 Loaded {len(matrix_data)} tool-contract combinations")
        
        # Initialize the generator with RELI template
        generator = TemplateExcelMatrixGenerator("RELI_Capabilities Matrix Template.xlsx")
        
        # Load the template
        generator.load_template()
        
        # Find where to start adding data
        data_start_row = generator.find_data_start_row()
        
        # Add matrix data
        generator.add_matrix_data(matrix_data, data_start_row)
        
        # Add summary sheets
        generator.add_summary_sheet(matrix_data)
        generator.add_contract_summary_sheet(matrix_data)
        
        # Apply final formatting
        generator.format_worksheet()
        
        # Save the populated template Excel file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"RELI_TEMPLATE_MATRIX_{timestamp}.xlsx"
        generator.save_template_excel(excel_filename)
        
        print(f"\n" + "=" * 60)
        print("✅ RELI TEMPLATE EXCEL MATRIX GENERATION COMPLETE")
        print("=" * 60)
        
        # Show summary
        print(f"\n📊 Matrix Summary:")
        print(f"- Total Tool-Contract Combinations: {len(matrix_data)}")
        print(f"- Total Contracts: {len(set(row['Contract'] for row in matrix_data))}")
        print(f"- Total Tools: {len(set(row['Tool'] for row in matrix_data))}")
        
        print(f"\n📄 Output Files:")
        print(f"- RELI Template Excel: {excel_filename}")
        print(f"- Based on: RELI_Capabilities Matrix Template.xlsx")
        print(f"- Contains: Main Matrix, Tool Summary, Contract Summary")
        
        print(f"\n🎨 Template Features:")
        print(f"- Uses existing RELI corporate template")
        print(f"- Preserves original template styling")
        print(f"- Adds comprehensive tool usage data")
        print(f"- Includes summary sheets for insights")
        print(f"- Professional presentation ready")
        
    except Exception as e:
        print(f"❌ RELI template Excel generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 