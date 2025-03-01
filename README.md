# BU DocCloud Document Classification Service

An LLM-powered document classification service for BU DocCloud Platform, capable of integrating with various document management systems.

## Overview

This service analyzes and classifies documents using state-of-the-art LLMs. It can process various document types (PDF, images, text files, etc.) and classify them into categories like:

- I-9 forms
- W-4 forms
- ID documents (Driver License, Passport)
- Personal documents (Birth Certificate, Marriage Certificate)
- Legal documents (Contracts, NDAs)
- Financial documents (Bank Statements, Pay Stubs)
- And more

## Features

- **Intelligent Document Classification**: Uses advanced LLMs to accurately classify documents
- **Platform Integration**: Seamless integration with BU DocCloud and other document management platforms
- **Bulk Upload Support**: Process multiple documents efficiently
- **OCR Capabilities**: Extract text from images and scanned documents
- **Metadata Extraction**: Pull relevant information from documents (dates, names, IDs)
- **Confidence Scoring**: Provides classification confidence levels
- **REST API**: Simple API for integrating with any client application

## Prerequisites

- Python 3.9+
- OpenAI API key
- BU DocCloud API credentials (for platform integration)

## Installation

1. Clone the repository:
   ```
   git clone bitbucket
   cd document-classification
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

1. Start the server:
   ```
   uvicorn src.main:app --reload
   ```

2. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

3. Test the classification endpoint:
   ```
   curl -X POST "http://localhost:8000/classify" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@/path/to/document.pdf" \
     -F "platform=BU_doccloud" \
     -F "callback_url=https://your-callback-url.com"
   ```

## API Endpoints

- `GET /`: Health check and service information
- `POST /classify`: Classify one or more documents
- `GET /supported-platforms`: List available document management platforms
- `GET /document-types`: List supported document classification types

## Integration with Document Management Platforms

The service supports these platforms out of the box:
- BU DocCloud (native support)
- Microsoft SharePoint
- Box
- Dropbox
- Google Drive
- Microsoft OneDrive

To add a new platform integration, create a new connector in `src/integrations/platforms/`.

## Development

### Testing

```
pytest
```

### Code Formatting

```
black src/
isort src/
flake8 src/
```

## License

MIT

## Support

For issues or questions, contact the BU DocCloud support team.