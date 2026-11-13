"""
Document loader service supporting PDF (PyMuPDF), DOCX (python-docx), and TXT formats.
Preserves page numbers, handles table extraction, and validates extensions, size, and content.
"""

from dataclasses import dataclass, field
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import docx
import pymupdf

from backend.app.core.config import settings


class DocumentLoaderError(Exception):
    """Base exception for document loading errors."""
    pass


class UnsupportedFileTypeError(DocumentLoaderError):
    """Raised when an unsupported file extension is provided."""
    pass


class EmptyDocumentError(DocumentLoaderError):
    """Raised when a file has 0 bytes or no readable text."""
    pass


class FileTooLargeError(DocumentLoaderError):
    """Raised when a file exceeds the allowed file size limit."""
    pass


class DocumentParsingError(DocumentLoaderError):
    """Raised when parsing fails due to corruption or syntax errors."""
    pass


@dataclass
class DocumentPage:
    """Represents text extracted from a specific page/section."""
    text: str
    page_number: int  # 1-indexed
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedDocument:
    """Represents a fully ingested document."""
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    content_hash: str
    total_pages: int
    total_characters: int
    pages: List[DocumentPage]
    category: str = "resume"

    @property
    def full_text(self) -> str:
        """Returns the concatenated text from all pages."""
        return "\n\n".join(page.text for page in self.pages if page.text.strip())


class DocumentLoader:
    """Service to load and extract text from PDF, DOCX, and TXT files."""

    def __init__(
        self,
        allowed_extensions: Optional[set[str]] = None,
        max_file_size_bytes: Optional[int] = None,
    ):
        self.allowed_extensions = allowed_extensions or settings.ALLOWED_EXTENSIONS
        self.max_file_size_bytes = max_file_size_bytes or settings.MAX_FILE_SIZE_BYTES

    def load_from_path(
        self,
        file_path: Union[str, Path],
        category: str = "resume",
        document_id: Optional[str] = None,
    ) -> LoadedDocument:
        """Loads and extracts text from a file path."""
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file_bytes = path.read_bytes()
        return self.load_from_bytes(
            file_bytes=file_bytes,
            filename=path.name,
            category=category,
            document_id=document_id,
        )

    def load_from_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        category: str = "resume",
        document_id: Optional[str] = None,
    ) -> LoadedDocument:
        """Loads and extracts text from raw bytes with a given filename."""
        # 1. Size validation
        file_size = len(file_bytes)
        if file_size == 0:
            raise EmptyDocumentError(f"File '{filename}' is empty (0 bytes).")

        if file_size > self.max_file_size_bytes:
            raise FileTooLargeError(
                f"File '{filename}' ({file_size} bytes) exceeds maximum limit "
                f"of {self.max_file_size_bytes} bytes."
            )

        # 2. Extension validation
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{extension}' for file '{filename}'. "
                f"Allowed types: {', '.join(sorted(self.allowed_extensions))}"
            )

        # 3. Compute deterministic hash and stable ID
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        stable_id = document_id or f"doc_{content_hash[:16]}"

        # 4. Extract pages based on file extension
        if extension == ".pdf":
            pages = self._extract_pdf(file_bytes, filename)
        elif extension == ".docx":
            pages = self._extract_docx(file_bytes, filename)
        elif extension == ".txt":
            pages = self._extract_txt(file_bytes, filename)
        else:
            raise UnsupportedFileTypeError(f"Unsupported format: {extension}")

        # 5. Validate extracted text
        total_chars = sum(len(p.text.strip()) for p in pages)
        if total_chars == 0:
            raise EmptyDocumentError(
                f"No readable text could be extracted from '{filename}'."
            )

        return LoadedDocument(
            document_id=stable_id,
            filename=filename,
            file_type=extension.lstrip("."),
            file_size_bytes=file_size,
            content_hash=content_hash,
            total_pages=len(pages),
            total_characters=total_chars,
            pages=pages,
            category=category,
        )

    def _extract_pdf(self, file_bytes: bytes, filename: str) -> List[DocumentPage]:
        """Extracts text per page from PDF bytes using PyMuPDF."""
        pages: List[DocumentPage] = []
        try:
            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                if len(doc) == 0:
                    raise EmptyDocumentError(f"PDF document '{filename}' has 0 pages.")

                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    page_text = page.get_text("text").strip()
                    pages.append(
                        DocumentPage(
                            text=page_text,
                            page_number=page_idx + 1,  # 1-indexed
                            metadata={
                                "source": filename,
                                "page_number": page_idx + 1,
                                "total_pages": len(doc),
                            },
                        )
                    )
        except EmptyDocumentError:
            raise
        except Exception as error:
            raise DocumentParsingError(
                f"Failed to parse PDF '{filename}': {str(error)}"
            ) from error

        return pages

    def _extract_docx(self, file_bytes: bytes, filename: str) -> List[DocumentPage]:
        """Extracts text and tables from DOCX bytes using python-docx."""
        try:
            doc = docx.Document(BytesIO(file_bytes))
            sections: List[str] = []

            # Paragraph extraction
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    sections.append(text)

            # Table extraction
            for table_idx, table in enumerate(doc.tables, start=1):
                table_lines: List[str] = []
                for row in table.rows:
                    # Collect cells and de-duplicate merged cells in the same row
                    deduped_cells: List[str] = []
                    for cell in row.cells:
                        clean_cell = cell.text.strip()
                        if not deduped_cells or clean_cell != deduped_cells[-1]:
                            deduped_cells.append(clean_cell)

                    row_str = " | ".join(c for c in deduped_cells if c)
                    if row_str:
                        table_lines.append(row_str)

                if table_lines:
                    sections.append(
                        f"[Table {table_idx}]\n" + "\n".join(table_lines)
                    )

            full_text = "\n\n".join(sections).strip()

            return [
                DocumentPage(
                    text=full_text,
                    page_number=1,
                    metadata={
                        "source": filename,
                        "page_number": 1,
                        "total_pages": 1,
                        "has_tables": len(doc.tables) > 0,
                    },
                )
            ]
        except Exception as error:
            raise DocumentParsingError(
                f"Failed to parse DOCX '{filename}': {str(error)}"
            ) from error

    def _extract_txt(self, file_bytes: bytes, filename: str) -> List[DocumentPage]:
        """Extracts text from TXT bytes with fallback encoding support."""
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        decoded_text: Optional[str] = None

        for enc in encodings:
            try:
                decoded_text = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if decoded_text is None:
            raise DocumentParsingError(
                f"Failed to decode text file '{filename}' with supported encodings."
            )

        clean_text = decoded_text.strip()

        return [
            DocumentPage(
                text=clean_text,
                page_number=1,
                metadata={
                    "source": filename,
                    "page_number": 1,
                    "total_pages": 1,
                },
            )
        ]
