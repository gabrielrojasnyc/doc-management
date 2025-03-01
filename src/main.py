import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from pydantic import BaseModel
import uuid

from src.core.document_classifier import DocumentClassifier
from src.core.document_processor import DocumentProcessor
from src.integrations.platform_connector import PlatformConnector

app = FastAPI(
    title="BU DocCloud Document Classification Service",
    description="An LLM-based document classification service for BU DocCloud Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
document_classifier = DocumentClassifier()
platform_connector = PlatformConnector()

class ClassificationResult(BaseModel):
    document_id: str
    document_name: str
    document_type: str
    confidence_score: float
    metadata: dict


@app.get("/")
async def root():
    return {"message": "BU DocCloud Document Classification Service"}


@app.post("/classify", response_model=List[ClassificationResult])
async def classify_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    platform: Optional[str] = Form(None),
    callback_url: Optional[str] = Form(None),
):
    """
    Classify multiple documents and return their categories.
    Optionally push results to a document management platform.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    for file in files:
        document_id = str(uuid.uuid4())
        
        # Process document
        document_content = await document_processor.process(file)
        
        # Classify document
        classification = document_classifier.classify(document_content)
        
        result = ClassificationResult(
            document_id=document_id,
            document_name=file.filename,
            document_type=classification["document_type"],
            confidence_score=classification["confidence_score"],
            metadata=classification["metadata"]
        )
        
        results.append(result)
        
        # If platform is specified, push to platform in background
        if platform and callback_url:
            background_tasks.add_task(
                platform_connector.push_classification,
                platform=platform,
                document_id=document_id,
                file=file,
                classification_result=result,
                callback_url=callback_url
            )
    
    return results


@app.get("/supported-platforms")
async def get_supported_platforms():
    """Return a list of supported document management platforms"""
    return {
        "platforms": platform_connector.get_supported_platforms()
    }


@app.get("/document-types")
async def get_document_types():
    """Return a list of supported document types for classification"""
    return {
        "document_types": [
            "I-9",
            "W-4",
            "W-2",
            "1099",
            "Driver License",
            "Passport",
            "Social Security Card",
            "Birth Certificate",
            "Marriage Certificate",
            "Divorce Decree",
            "Legal Contract",
            "NDA",
            "Employment Contract",
            "Medical Record",
            "Insurance Card",
            "Pay Stub",
            "Bank Statement",
            "Utility Bill",
            "Rental Agreement",
            "Mortgage Document",
            "Other"
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)