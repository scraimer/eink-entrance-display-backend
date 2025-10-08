import json
from convertdate import hebrew

# Load the JSON data from the file
with open('extracted_tables.keyed.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Define the mapping of Hebrew field names to English field names
field_mapping = {
    "סוף הצום": "fast_end",
    # "תחילת הצום 2": "Start of Fast 2",
    "תחילת הצום": "fast_start",
    "צאת השבת/החג": "tzet_shabbat",
    "הדלקת נרות": "candle_lighting",
    # "החמה\nשקיעת": "Sunset",
    # "מג\"א\nפלג המנחה": "MGA Plag Hamincha",
    # "גר\"א\nפלג המנחה": "GRA Plag Hamincha",
    # "מנחה גדולה": "Mincha Gedola",
    # "גר״א\nס״ז ק״ש": "GRA Latest Shema",
    # "מג״א\nס״ז ק״ש": "MGA Latest Shema",
    # "הנץ החמה": "Sunrise",
    # "עלות השחר": "Dawn",
    "תאריך": "hebrew_date",
    "הפרשה": "name"
}

def hebrew_number_to_int(hebrew_num:str) -> int:
    hebrew_numerals = {
        'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5,
        'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9, 'י': 10,
        'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60,
        'ע': 70, 'פ': 80, 'צ': 90, 'ק': 100, 'ר': 200,
        'ש': 300, 'ת': 400
    }
    total = 0
    for char in hebrew_num:
        if char in hebrew_numerals:
            total += hebrew_numerals[char]
    return total

# Function to convert Hebrew date to Gregorian date
def hebrew_date_to_gregorian(hebrew_date):
    try:
        parts = hebrew_date.split()
        day = hebrew_number_to_int(parts[0].replace('׳', '').replace('״', ''))  # Remove Hebrew punctuation
        fix_month_spelling = {
            'חשון': 'חשוון',
            'סיון': 'סיוון',
        }
        month_part = parts[1]
        month_part = fix_month_spelling.get(month_part, month_part)
        month = hebrew.MONTHS_HEB.index(month_part) + 1  # Convert Hebrew month name to number
        year = 5786  # Hebrew year corresponding to 2025-2026
        gregorian_date = hebrew.to_gregorian(year, month, day)
        return f"{gregorian_date[0]}-{gregorian_date[1]:02d}-{gregorian_date[2]:02d}"
    except Exception as ex:
        print(f"Failed to convert Hebrew date: {hebrew_date}, exception: {ex}")
        return hebrew_date  # Return original if conversion fails

# Process the data to replace field names and convert dates
updated_data = []
for record in data:
    updated_record = {}
    for hebrew_field, value in record.items():
        if hebrew_field not in field_mapping:
            continue  # Skip fields not in the mapping
        if not value:
            continue  # Skip empty values
        english_field = field_mapping.get(hebrew_field, hebrew_field)  # Default to original if no mapping exists
        if english_field == "hebrew_date" and value:
            updated_record["gregorian_date"] = hebrew_date_to_gregorian(value)
        else:
            updated_record[english_field] = value
    updated_data.append(updated_record)

# Save the updated data back to a new JSON file
with open('extracted_tables_translated.json', 'w', encoding='utf-8') as file:
    json.dump(updated_data, file, ensure_ascii=False, indent=4)

print("Field names have been translated and dates converted. Saved to 'extracted_tables_translated.json'.")