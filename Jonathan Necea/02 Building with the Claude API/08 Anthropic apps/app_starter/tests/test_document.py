import os
import shutil
import pytest
from tools.document import binary_document_to_markdown, document_path_to_markdown


class TestBinaryDocumentToMarkdown:
    # Define fixture paths
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    def test_fixture_files_exist(self):
        """Verify test fixtures exist."""
        assert os.path.exists(self.DOCX_FIXTURE), (
            f"DOCX fixture not found at {self.DOCX_FIXTURE}"
        )
        assert os.path.exists(self.PDF_FIXTURE), (
            f"PDF fixture not found at {self.PDF_FIXTURE}"
        )

    def test_binary_document_to_markdown_with_docx(self):
        """Test converting a DOCX document to markdown."""
        # Read binary content from the fixture
        with open(self.DOCX_FIXTURE, "rb") as f:
            docx_data = f.read()

        # Call function
        result = binary_document_to_markdown(docx_data, "docx")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result

    def test_binary_document_to_markdown_with_pdf(self):
        """Test converting a PDF document to markdown."""
        # Read binary content from the fixture
        with open(self.PDF_FIXTURE, "rb") as f:
            pdf_data = f.read()

        # Call function
        result = binary_document_to_markdown(pdf_data, "pdf")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result


class TestDocumentPathToMarkdown:
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    # --- Happy path: the core contract ---

    def test_path_to_markdown_with_docx(self):
        """Converts a DOCX file referenced by path to markdown."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result or "-" in result or "*" in result

    def test_path_to_markdown_with_pdf(self):
        """Converts a PDF file referenced by path to markdown."""
        result = document_path_to_markdown(self.PDF_FIXTURE)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result or "-" in result or "*" in result

    def test_matches_binary_conversion(self):
        """Path-based conversion matches reading the bytes and converting directly.

        Proves the path tool is a thin wrapper that does not diverge from
        ``binary_document_to_markdown``.
        """
        with open(self.PDF_FIXTURE, "rb") as f:
            expected = binary_document_to_markdown(f.read(), "pdf")

        assert document_path_to_markdown(self.PDF_FIXTURE) == expected

    # --- File-type inference from the path ---

    def test_uppercase_extension(self, tmp_path):
        """Extension matching is case-insensitive (REPORT.PDF still parses)."""
        dest = tmp_path / "REPORT.PDF"
        shutil.copy(self.PDF_FIXTURE, dest)

        result = document_path_to_markdown(str(dest))

        assert isinstance(result, str)
        assert len(result) > 0

    # --- Path handling ---

    def test_path_with_spaces(self, tmp_path):
        """A filename containing spaces is handled correctly."""
        dest = tmp_path / "my meeting notes.docx"
        shutil.copy(self.DOCX_FIXTURE, dest)

        result = document_path_to_markdown(str(dest))

        assert isinstance(result, str)
        assert len(result) > 0

    # --- Error handling (the new filesystem surface area) ---

    def test_nonexistent_path_raises(self):
        """A missing file surfaces a clear FileNotFoundError, not a parser crash."""
        missing = os.path.join(self.FIXTURES_DIR, "does_not_exist.pdf")

        with pytest.raises(FileNotFoundError):
            document_path_to_markdown(missing)

    def test_directory_path_raises(self):
        """Passing a directory rather than a file raises IsADirectoryError."""
        with pytest.raises(IsADirectoryError):
            document_path_to_markdown(self.FIXTURES_DIR)
