import re 
import os 
import pandas as pd
from docx import Document
from pypdf import PdfReader
from dateparser.search import search_dates

# Word Parser 
def extract_student_info_from_docx(filepath):
    doc = Document(filepath)
    full_text = "\n".join([para.text for para in doc.paragraphs])
    
    name_match = re.search(r'Student Name:\s*(.+?)\s*DOB:', full_text)
    dob_match = re.search(r'DOB:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})', full_text)
    id_match = re.search(r'Student ID:\s*(\d+)', full_text)

    student_name = name_match.group(1).strip() if name_match else None
    dob = dob_match.group(1).strip() if dob_match else None
    student_id = id_match.group(1).strip() if id_match else None

    return {
        'Source File': os.path.basename(filepath),
        'Student Name': student_name,
        'DOB': dob,
        'Student ID': student_id
    }
# PDF parser 
def extract_student_info_from_pdf(filepath):
    reader = PdfReader(filepath)
    page = reader.pages[0]
    text = page.extract_text()

    full_name = None
    dob = None

    # Check 1: "On MM/DD/YYYY, FIRST LAST,"
    match1 = re.search(r'On\s+\d{1,2}/\d{1,2}/\d{2,4},\s+([A-Z]+\s+[A-Z]+),', text)
    if match1:
        full_name = match1.group(1)

    # Check 2: "Student Name: Juan Andres Marchan    D.O.B.: 07/14/2008"
    match2 = re.search(r'Student Name:\s*(.*?)\s+D\.O\.B\.:?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})', text)
    if match2:
        full_name = match2.group(1).strip()
        dob = match2.group(2).strip()

    # Check 3: "...ANTHONY CAMPOS, date of birth, 11/16/2012..."
    match3 = re.search(r'([A-Z]+ [A-Z]+),\s*date of birth,?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})', text, re.IGNORECASE)
    if match3:
        full_name = match3.group(1).title()  # Convert from all caps to title case
        dob = match3.group(2)

    # Final check: this looks for any "DOB" mention + search_dates
    if not dob:
        results = search_dates(text)
        if results:
            for original, parsed in results:
                if "date of birth" in text.lower().split(original.lower())[0][-40:].lower():
                    dob = parsed.strftime("%m/%d/%Y")
                    break

    return {
        'Source File': os.path.basename(filepath),
        'Student Name': full_name,
        'DOB': dob,
        'Student ID': None  # Still optional
    }
# Loop through folder 
def extract_all_student_info(folder_path):
    student_records = []
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        if filename.lower().endswith('.docx'):
            print(f"Processing Word: {filename}")
            info = extract_student_info_from_docx(filepath)
        elif filename.lower().endswith('.pdf'):
            print(f"Processing PDF: {filename}")
            info = extract_student_info_from_pdf(filepath)
        else:
            print(f"Skipping unsupported file: {filename}")
            continue
        
        student_records.append(info)

    return student_records

# Change this folder to match where the word/pdf files are on your computer.
folder = "C:/Users/alopez24/OneDrive - North East Independent School District/Desktop/DISC 2024-2025"
all_students = extract_all_student_info(folder)
df = pd.DataFrame(all_students)

##################### Save to Excel####################################

# Change output path to where you would like to save the file
output_path = "C:/Users/alopez24/OneDrive - North East Independent School District/Desktop/DISC_Exported_Students.xlsx"
df.to_excel(output_path, index=False)

print(f"\n Export complete! File saved to:\n{output_path}")