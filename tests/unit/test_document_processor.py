import io
import os
import pytest
from fastapi import UploadFile
from unittest.mock import MagicMock, patch

from src.core.document_processor import DocumentProcessor

class TestDocumentProcessor:
    """Tests for DocumentProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Return a DocumentProcessor instance"""
        return DocumentProcessor()
    
    @pytest.mark.asyncio
    async def test_process_text_file(self, processor):
        """Test processing a text file"""
        # Create a mock text file
        content = "This is a sample text file.\nWith multiple lines.\nTesting document processing."
        file = MagicMock(spec=UploadFile)
        file.filename = "sample.txt"
        file.content_type = "text/plain"
        file.read = MagicMock(return_value=content.encode("utf-8"))
        file.seek = MagicMock()
        
        # Process the file
        result = await processor.process(file)
        
        # Verify the result
        assert result["filename"] == "sample.txt"
        assert result["mime_type"] == "text/plain"
        assert result["file_extension"] == ".txt"
        assert result["text_content"] == content
        assert result["pages"] == [content]
        assert isinstance(result["metadata"], dict)
        
        # Verify file.seek was called
        file.seek.assert_called_once_with(0)
    
    @pytest.mark.asyncio
    async def test_process_unsupported_file(self, processor):
        """Test processing an unsupported file type"""
        # Create a mock unsupported file
        file = MagicMock(spec=UploadFile)
        file.filename = "sample.xyz"
        file.content_type = "application/octet-stream"
        file.read = MagicMock(return_value=b"Some binary content")
        file.seek = MagicMock()
        
        # Process the file
        result = await processor.process(file)
        
        # Verify the result
        assert result["filename"] == "sample.xyz"
        assert result["file_extension"] == ".xyz"
        assert result["text_content"] == "Unsupported file type"
        assert result["pages"] == ["Unsupported file type"]
        
        # Verify file.seek was called
        file.seek.assert_called_once_with(0)
    
    @pytest.mark.asyncio
    @patch("src.core.document_processor.pypdf.PdfReader")
    async def test_process_pdf_file(self, mock_pdf_reader, processor):
        """Test processing a PDF file"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.5\nSome PDF content"
        file = MagicMock(spec=UploadFile)
        file.filename = "sample.pdf"
        file.content_type = "application/pdf"
        file.read = MagicMock(return_value=pdf_content)
        file.seek = MagicMock()
        
        # Configure mock PDF reader
        mock_pdf_reader.return_value.pages = [
            MagicMock(extract_text=MagicMock(return_value="Page 1 content")),
            MagicMock(extract_text=MagicMock(return_value="Page 2 content"))
        ]
        mock_pdf_reader.return_value.metadata = {
            "/Title": "Sample PDF",
            "/Author": "Test User"
        }
        
        # Process the file
        result = await processor.process(file)
        
        # Verify the result
        assert result["filename"] == "sample.pdf"
        assert result["file_extension"] == ".pdf"
        assert "Page 1 content" in result["text_content"]
        assert "Page 2 content" in result["text_content"]
        assert len(result["pages"]) == 2
        assert result["pages"][0] == "Page 1 content"
        assert result["pages"][1] == "Page 2 content"
        assert result["metadata"] == {
            "/Title": "Sample PDF",
            "/Author": "Test User"
        }
        
        # Verify file.seek was called
        file.seek.assert_called_once_with(0)
    
    @pytest.mark.asyncio
    @patch("src.core.document_processor.Image.open")
    @patch("src.core.document_processor.pytesseract.image_to_string")
    async def test_process_image_file(self, mock_image_to_string, mock_image_open, processor):
        """Test processing an image file"""
        # Create a mock image file
        image_content = b"Some image binary content"
        file = MagicMock(spec=UploadFile)
        file.filename = "sample.jpg"
        file.content_type = "image/jpeg"
        file.read = MagicMock(return_value=image_content)
        file.seek = MagicMock()
        
        # Configure mocks
        mock_image = MagicMock()
        mock_image.width = 800
        mock_image.height = 600
        mock_image.format = "JPEG"
        mock_image.mode = "RGB"
        mock_image_open.return_value = mock_image
        
        mock_image_to_string.return_value = "Text extracted from image via OCR"
        
        # Process the file
        result = await processor.process(file)
        
        # Verify the result
        assert result["filename"] == "sample.jpg"
        assert result["file_extension"] == ".jpg"
        assert result["text_content"] == "Text extracted from image via OCR"
        assert result["pages"] == ["Text extracted from image via OCR"]
        assert result["metadata"] == {
            "width": 800,
            "height": 600,
            "format": "JPEG",
            "mode": "RGB"
        }
        
        # Verify file.seek was called
        file.seek.assert_called_once_with(0)