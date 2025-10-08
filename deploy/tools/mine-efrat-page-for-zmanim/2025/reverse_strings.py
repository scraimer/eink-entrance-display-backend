import json
from pathlib import Path

def reverse_strings_in_json(file_path: Path, output_filepath: Path):
    data = json.loads(file_path.read_text(encoding='utf-8'))

    def reverse_if_no_colon(value):
        if isinstance(value, str) and ':' not in value:
            return value[::-1]
        return value

    def process_item(item):
        if isinstance(item, dict):
            return {key: process_item(value) for key, value in item.items()}
        elif isinstance(item, list):
            return [process_item(element) for element in item]
        else:
            return reverse_if_no_colon(item)

    reversed_data = process_item(data)

    output_filepath.write_text(json.dumps(reversed_data, ensure_ascii=False, indent=4), encoding='utf-8')

if __name__ == "__main__":
    json_file_path = "extracted_tables.json"
    output_file_path = "extracted_tables.reversed.json"
    reverse_strings_in_json(Path(json_file_path), Path(output_file_path))