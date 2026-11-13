
from pathlib import Path
from pypdf import PdfReader

# Get the current script directory
BASE_DIR = Path(__file__).resolve().parent

# PDF file path
pdf_path = BASE_DIR / "sample_resume.pdf"

# Check whether PDF exists
if not pdf_path.exists():
    print("PDF file not found!")
    print("Expected location:", pdf_path)
    raise SystemExit

# Read PDF
reader = PdfReader(str(pdf_path))

resume_text = ""

for page_number, page in enumerate(reader.pages, start=1):
    text = page.extract_text()

    if text:
        resume_text += text + "\n"

print("PDF extraction successful!")
print("\nExtracted Resume Text:")
print(resume_text)

print("\nTotal Pages:", len(reader.pages))
print("Total Characters:", len(resume_text))
