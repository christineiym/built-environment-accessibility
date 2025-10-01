import os
import pandas as pd
from pdf2image import convert_from_path
import pytesseract


def ocr_pdfs_to_csv(input_folder, output_csv):
    results = []

    # Loop through all PDF files in the folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            print(f"Processing: {pdf_path}")

            # Convert PDF to images (one per page)
            try:
                pages = convert_from_path(pdf_path)
            except Exception as e:
                print(f"Error converting {filename}: {e}")
                continue

            text_content = []
            for page_num, page in enumerate(pages, start=1):
                # Run OCR on each page
                text = pytesseract.image_to_string(page)
                text_content.append(text)

            # Join all page texts for this PDF
            full_text = "\n".join(text_content)
            results.append({"filename": filename, "extracted_text": full_text})

        with open("pdfs.csv", APPEND_MODE, newline='') as output_file:
            if len(result) > 0:
                dict_writer = csv.DictWriter(output_file, result[0].keys())
                dict_writer.writeheader()
                dict_writer.writerows(results)
    # Save results to CSV
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"OCR results saved to {output_csv}")


if __name__ == "__main__":
    input_folder = "./column"
    output_csv = "ocr_results.csv"
    ocr_pdfs_to_csv(input_folder, output_csv)
