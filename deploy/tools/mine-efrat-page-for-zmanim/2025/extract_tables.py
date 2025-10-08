import pdfplumber
import json

# Filepath to the PDF
pdf_path = "1759210892.3722.pdf"

# Output JSON file
output_json_path = "extracted_tables.json"

# Extract tables from the PDF
def extract_tables_to_json(pdf_path, output_json_path):
    tables_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            # Extract tables from the page
            tables = page.extract_tables()
            for table_index, table in enumerate(tables):
                # Convert table to a list of dictionaries (optional)
                table_data = {
                    "page": page_number,
                    "table_index": table_index,
                    "data": table
                }
                tables_data.append(table_data)

    # Save the extracted tables to a JSON file
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(tables_data, json_file, indent=4, ensure_ascii=False)

    print(f"Tables extracted and saved to {output_json_path}")

# Run the function
extract_tables_to_json(pdf_path, output_json_path)