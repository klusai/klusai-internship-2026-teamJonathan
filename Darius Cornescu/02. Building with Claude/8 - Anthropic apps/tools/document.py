import os
from markitdown import MarkItDown, StreamInfo
from io import BytesIO
from pydantic import Field

SUPPORTED_EXTENSIONS = {"pdf", "docx"}


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    file_path: str = Field(description="Path to a PDF or DOCX file to convert"),
) -> str:
    """Read a PDF or DOCX file from disk and convert its contents to markdown.

    Opens the file at the given path, reads its binary contents, and converts
    them into markdown-formatted text. The file type is inferred from the path's
    extension.

    When to use:
    - When you have a PDF or DOCX file on the local filesystem and need its
      contents as markdown text.

    When not to use:
    - For file types other than PDF or DOCX (raises ValueError).
    - When you already have the document bytes in memory; use
      `binary_document_to_markdown` instead.

    Examples:
    >>> document_path_to_markdown("report.pdf")
    '# Report\\n\\n...'
    >>> document_path_to_markdown("notes.docx")
    '# Notes\\n\\n...'
    """
    extension = os.path.splitext(file_path)[1].lstrip(".").lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{extension}'. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    with open(file_path, "rb") as file_obj:
        binary_data = file_obj.read()

    return binary_document_to_markdown(binary_data, extension)
