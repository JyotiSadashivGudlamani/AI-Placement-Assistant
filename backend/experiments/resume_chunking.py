
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Step 1: Read PDF
BASE_DIR = Path(__file__).resolve().parent
pdf_path = BASE_DIR / "sample_resume.pdf"

reader = PdfReader(str(pdf_path))

resume_text = ""

for page in reader.pages:
    text = page.extract_text()
    if text:
        resume_text += text + "\n"

# Step 2: Create text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# Step 3: Split resume text
chunks = text_splitter.split_text(resume_text)

# Step 4: Display chunks
print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks, start=1):
    print(f"\n--- CHUNK {i} ---")
    print(chunk)
