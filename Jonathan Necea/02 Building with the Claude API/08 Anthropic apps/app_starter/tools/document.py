import os
from io import BytesIO

from markitdown import MarkItDown, StreamInfo
from pydantic import Field


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    file_path: str = Field(
        description="Filesystem path to a PDF or DOCX file to convert. May be "
        "absolute or relative to the server's working directory."
    ),
) -> str:
    """Read a PDF or DOCX file from disk and convert its contents to markdown.

    Opens the file at ``file_path``, reads its raw bytes, infers the document
    type from the file extension, and returns the contents as markdown-formatted
    text.

    When to use:
    - When you have a path to a ``.pdf`` or ``.docx`` file on the local
      filesystem and need its contents as markdown text.

    When not to use:
    - For formats other than PDF or DOCX.
    - When you already hold the raw bytes in memory (use
      ``binary_document_to_markdown`` instead).
    - When the document is remote (download it first, then call this tool).

    Examples:
    >>> document_path_to_markdown("docs/report.pdf")
    '# Quarterly Report\\n\\n...'
    >>> document_path_to_markdown("/abs/path/notes.docx")
    '# Meeting Notes\\n\\n- item one\\n- item two'
    """
    with open(file_path, "rb") as f:
        binary_data = f.read()
    file_type = os.path.splitext(file_path)[1].lstrip(".").lower()
    return binary_document_to_markdown(binary_data, file_type)
