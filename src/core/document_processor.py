import io
import os
from typing import Dict, Any, List, Optional
from fastapi import UploadFile
import pytesseract
from PIL import Image
import pypdf

class DocumentProcessor:
    """
    Handles document processing, extraction, and preparation for classification.
    Supports various document types including PDFs, images, and text files.
    """
    
    async def process(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process a document file and extract its content.
        
        Args:
            file: The uploaded file to process
            
        Returns:
            Dict containing document content and metadata
        """
        content = await file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        document_content = {
            "filename": file.filename,
            "mime_type": file.content_type,
            "file_extension": file_extension,
            "text_content": "",
            "pages": [],
            "metadata": {},
        }
        
        # Process based on file type
        if file_extension == ".pdf":
            document_content = self._process_pdf(content, document_content)
        elif file_extension in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            document_content = self._process_image(content, document_content)
        elif file_extension in [".txt", ".csv", ".md", ".html"]:
            document_content = self._process_text(content, document_content)
        elif file_extension in [".doc", ".docx"]:
            # For simplicity, we'll just extract text here
            # In a production system, you'd use libraries like python-docx
            document_content["text_content"] = "Document content extraction not implemented for this type"
            document_content["pages"] = ["Document content extraction not implemented for this type"]
        else:
            document_content["text_content"] = "Unsupported file type"
            document_content["pages"] = ["Unsupported file type"]
        
        # Reset file position for potential future use
        await file.seek(0)
        
        return document_content
    
    def _process_pdf(self, content: bytes, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process PDF file and extract text and metadata"""
        pdf_file = io.BytesIO(content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        # Extract text from each page
        pages = []
        full_text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            pages.append(page_text)
            full_text += page_text + "\n\n"
        
        # Extract metadata
        metadata = {}
        for key, value in pdf_reader.metadata.items():
            if key and value:
                metadata[key] = value
        
        document_content["text_content"] = full_text
        document_content["pages"] = pages
        document_content["metadata"] = metadata
        
        return document_content
    
    def _process_image(self, content: bytes, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process image file and extract text using OCR"""
        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image)
        
        document_content["text_content"] = text
        document_content["pages"] = [text]
        
        # Extract basic image metadata
        document_content["metadata"] = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode
        }
        
        return document_content
    
    def _process_text(self, content: bytes, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """Process text-based file and extract content"""
        text = content.decode("utf-8", errors="replace")
        
        document_content["text_content"] = text
        document_content["pages"] = [text]
        
        return document_content