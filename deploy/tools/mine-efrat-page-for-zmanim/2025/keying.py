import json
from pathlib import Path

def convert_to_keyed_json(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    with input_path.open('r', encoding='utf-8') as file:
        data = json.load(file)

    # Use the first row as keys
    keys = data[0]
    keyed_data = []

    for row in data[1:]:
        keyed_row = {keys[i]: row[i] if i < len(row) else None for i in range(len(keys))}
        keyed_data.append(keyed_row)

    with output_path.open('w', encoding='utf-8') as file:
        json.dump(keyed_data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_json_file = "extracted_tables.reversed.json"
    output_json_file = "extracted_tables.keyed.json"
    convert_to_keyed_json(input_json_file, output_json_file)