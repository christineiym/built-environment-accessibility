import os
import json
import pandas as pd
import openai
import csv

# -------------------
# CONFIG
# -------------------
INPUT_CSV = "ocr_results.csv"     # from OCR script
OUTPUT_CSV = "places_activities.csv"
MODEL_NAME = "gpt-4o-mini"        # or another GPT model

# Set your API key as an environment variable before running:
# export OPENAI_API_KEY="your_api_key"
# openai.api_key = os.getenv("OPENAI_API_KEY")

# -------------------
# GPT Helper
# -------------------
def extract_places_activities(text, filename):
    """
    Sends text to GPT and extracts structured data.
    Returns list of dicts: {filename, place_label, activity}
    """
    prompt = f"""
You are an information extraction assistant.

Task:
- Read the following newspaper article text.
- Identify **places/addresses** mentioned and the **activities** occurring there.
- If multiple activities happen at one place, list them separately.
- Normalize places so that the same place has exactly the same label across mentions.
- Return the results strictly as a JSON array of objects with keys:
  - "place_label": the standardized place/address
  - "activity": the activity occurring at that place

Article text:
\"\"\"{text}\"\"\"
"""

    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_output = response.choices[0].message.content.strip()

    try:
        cleaned_output = response_to_JSON(raw_output)
        data = json.loads(cleaned_output)
    except Exception as e:
        print(f"⚠️ Error parsing GPT output for {filename}: {e}")
        print("Raw output:", raw_output)
        return []

    base_name = os.path.splitext(filename)[0]
    return [{"filename": base_name, "place_label": d["place_label"], "activity": d["activity"]}
            for d in data if "place_label" in d and "activity" in d]

# -------------------
# Main
# -------------------
def main():
    df = pd.read_csv(INPUT_CSV)

    all_results = []
    place_dict = {}   # maps place_label -> place_id
    place_counter = 1

    for _, row in df.iterrows():
        filename = row["filename"]
        text = row["extracted_text"]

        if not isinstance(text, str) or not text.strip():
            continue

        print(f"🔍 Processing {filename}...")
        extracted = extract_places_activities(text, filename)

        for item in extracted:
            place = item["place_label"].strip()

            if place not in place_dict:
                place_id = f"place_{place_counter}"
                place_dict[place] = place_id
                place_counter += 1
            else:
                place_id = place_dict[place]

            item["place_id"] = place_id
            all_results.append(item)

        with open(OUTPUT_CSV, "w", newline='') as output_file:
            if len(all_results) > 0:
                dict_writer = csv.DictWriter(output_file, all_results[0].keys())
                dict_writer.writeheader()
                dict_writer.writerows(all_results)
                print(f"✅ Results saved to {OUTPUT_CSV}")
            else:
                print("⚠️ No results extracted.")

    # # Save results to CSV
    # if all_results:
    #     out_df = pd.DataFrame(all_results, columns=["filename", "place_id", "place_label", "activity"])
    #     out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    #     print(f"✅ Results saved to {OUTPUT_CSV}")
    # else:
    #     print("⚠️ No results extracted.")


def response_to_JSON(response):
    """Extract JSON as string from full response."""
    raw_response = str(response)
    
    potential_json = ""
    if not ((raw_response[0] == "[") and (raw_response[len(raw_response) - 1] == "]")):
        if ("[" in raw_response) and ("]" in raw_response):
            _, trim_beginning = raw_response.split("[", maxsplit=1)
            trim_end, _ = trim_beginning.rsplit("]", maxsplit=1)
            potential_json = trim_end
        potential_json = "[" + potential_json.strip() + "]"
    else:
        potential_json = raw_response
    
    json_dict = json.loads(potential_json)  # ensure valid JSON
    json_string = json.dumps(json_dict)
    cleaned_response = json_string
    return cleaned_response


if __name__ == "__main__":
    main()