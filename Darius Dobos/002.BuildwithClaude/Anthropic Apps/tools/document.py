from markitdown import MarkItDown, StreamInfo
from io import BytesIO
from pathlib import Path
from pydantic import Field


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    path: str = Field(description="Absolute or relative path to a PDF or DOCX file"),
) -> str:
    """Convert a PDF or DOCX file to markdown-formatted text.

    Reads the file at the given path and converts its contents to markdown.
    Supports .pdf and .docx file formats.

    When to use:
    - When you have a local file path to a document you want to extract text from
    - When you need to read and process the contents of a PDF or DOCX file

    When not to use:
    - For file formats other than PDF and DOCX
    - When you already have the binary content of the file (use binary_document_to_markdown instead)

    Examples:
    >>> document_path_to_markdown("/path/to/report.pdf")
    "# Report Title\\n\\nContent..."
    >>> document_path_to_markdown("/path/to/document.docx")
    "# Document Title\\n\\nContent..."
    """
    file_path = Path(path)
    file_type = file_path.suffix.lstrip(".")
    with open(file_path, "rb") as f:
        binary_data = f.read()
    return binary_document_to_markdown(binary_data, file_type)
