import os
import pytest
from tools.document import (
    binary_document_to_markdown,
    document_path_to_markdown,
    compute_text_stats,
    document_stats,
)


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

    def test_document_path_to_markdown_with_docx(self):
        """Test converting a DOCX document by path to markdown."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result or "-" in result or "*" in result

    def test_document_path_to_markdown_with_pdf(self):
        """Test converting a PDF document by path to markdown."""
        result = document_path_to_markdown(self.PDF_FIXTURE)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result or "-" in result or "*" in result

    def test_document_path_to_markdown_unsupported_extension(self):
        """Unsupported extensions should raise ValueError."""
        with pytest.raises(ValueError):
            document_path_to_markdown("some_file.txt")

    def test_document_path_to_markdown_missing_file(self):
        """A nonexistent path should raise FileNotFoundError."""
        missing = os.path.join(self.FIXTURES_DIR, "does_not_exist.pdf")
        with pytest.raises(FileNotFoundError):
            document_path_to_markdown(missing)

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


class TestComputeTextStats:
    def test_empty_string_has_zero_counts(self):
        """An empty string yields zero words, chars, and lines."""
        assert compute_text_stats("") == {
            "word_count": 0,
            "char_count": 0,
            "line_count": 0,
        }

    def test_whitespace_only_has_zero_words(self):
        """Whitespace-only text has no words; chars count the whitespace."""
        stats = compute_text_stats("   \n  \t ")
        assert stats["word_count"] == 0
        assert stats["char_count"] == len("   \n  \t ")

    def test_counts_words_chars_and_lines(self):
        """Counts are computed from whitespace tokens, length, and lines."""
        text = "hello world\nsecond line here"
        assert compute_text_stats(text) == {
            "word_count": 5,
            "char_count": len(text),
            "line_count": 2,
        }


class TestDocumentStats:
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    def test_document_stats_with_docx(self):
        """A DOCX path returns all three integer counts, each positive."""
        stats = document_stats(self.DOCX_FIXTURE)

        assert set(stats.keys()) == {"word_count", "char_count", "line_count"}
        assert all(isinstance(v, int) for v in stats.values())
        assert stats["word_count"] > 0
        assert stats["char_count"] > 0
        assert stats["line_count"] > 0

    def test_document_stats_with_pdf(self):
        """A PDF path returns all three integer counts, each positive."""
        stats = document_stats(self.PDF_FIXTURE)

        assert set(stats.keys()) == {"word_count", "char_count", "line_count"}
        assert all(isinstance(v, int) for v in stats.values())
        assert stats["word_count"] > 0
        assert stats["char_count"] > 0
        assert stats["line_count"] > 0

    def test_document_stats_are_internally_consistent(self):
        """Char count is at least word count, and there is at least one line."""
        stats = document_stats(self.DOCX_FIXTURE)
        assert stats["char_count"] >= stats["word_count"]
        assert stats["line_count"] >= 1

    def test_document_stats_unsupported_extension(self):
        """Unsupported extensions raise ValueError (inherited guard)."""
        with pytest.raises(ValueError):
            document_stats("some_file.txt")

    def test_document_stats_missing_file(self):
        """A nonexistent path raises FileNotFoundError (inherited guard)."""
        missing = os.path.join(self.FIXTURES_DIR, "does_not_exist.pdf")
        with pytest.raises(FileNotFoundError):
            document_stats(missing)
