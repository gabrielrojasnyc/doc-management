import os
from typing import Dict, Any, List
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

class DocumentClassifier:
    """
    Uses LLMs to classify documents into different categories.
    """
    
    def __init__(self):
        """Initialize the document classifier with LLM"""
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY", "")
        debug_mode = os.getenv("DEBUG", "")
        
        # Enable mock mode if debug is enabled or using a demo key
        self.mock_mode = debug_mode.lower() in ["true", "1"] or api_key.startswith("sk-demo")
        
        if self.mock_mode:
            print("WARNING: Using mock LLM in debug mode. Classification will return sample responses.")
            self.llm = None
        else:
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
                
            self.llm = ChatOpenAI(
                api_key=api_key,
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                temperature=0
            )
        
        # Define the output schema for structured responses
        self.response_schemas = [
            ResponseSchema(
                name="document_type",
                description="The classified document type"
            ),
            ResponseSchema(
                name="confidence_score",
                description="Confidence score for the classification (0.0 to 1.0)"
            ),
            ResponseSchema(
                name="metadata",
                description="Additional metadata extracted from the document"
            ),
            ResponseSchema(
                name="reasoning",
                description="Reasoning behind the classification decision"
            )
        ]
        
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        self.format_instructions = self.output_parser.get_format_instructions()
        
        # Classification prompt template
        self.classification_prompt = ChatPromptTemplate.from_template(
            """You are an expert document classifier for ADP DocCloud Platform.
            
Your task is to analyze document content and classify it into one of the following categories:
- I-9 (Employment Eligibility Verification)
- W-4 (Employee's Withholding Certificate)
- W-2 (Wage and Tax Statement)
- 1099 (Independent Contractor Income)
- Driver License
- Passport
- Social Security Card
- Birth Certificate
- Marriage Certificate
- Divorce Decree
- Legal Contract
- NDA (Non-Disclosure Agreement)
- Employment Contract
- Medical Record
- Insurance Card
- Pay Stub
- Bank Statement
- Utility Bill
- Rental Agreement
- Mortgage Document
- Other (if none of the above)

Below is the text content extracted from a document. Analyze it carefully and determine which category it belongs to.

DOCUMENT CONTENT:
{document_content}

{format_instructions}

Be sure to include any relevant extracted information in the metadata (such as dates, names, ID numbers, etc.)"""
        )
    
    def classify(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document based on its content
        
        Args:
            document_data: Dictionary containing document content and metadata
            
        Returns:
            Dictionary with classification results
        """
        # If in mock mode, return sample response
        if hasattr(self, 'mock_mode') and self.mock_mode:
            # Create a mock response based on filename or extension
            filename = document_data.get("filename", "").lower()
            file_ext = document_data.get("file_extension", "").lower()
            
            # Determine document type based on filename
            doc_type = "Other"
            confidence = 0.95
            metadata = {}
            
            if "w4" in filename or "w-4" in filename:
                doc_type = "W-4"
                metadata = {"form_year": "2023", "employee_name": "Sample Employee"}
            elif "w2" in filename or "w-2" in filename:
                doc_type = "W-2"
                metadata = {"tax_year": "2023", "employer_id": "12-3456789"}
            elif "i9" in filename or "i-9" in filename:
                doc_type = "I-9"
                metadata = {"form_version": "10/21/2019"}
            elif "passport" in filename:
                doc_type = "Passport"
                metadata = {"issue_date": "2020-01-01", "expiry_date": "2030-01-01"}
            elif "license" in filename or "dl" in filename:
                doc_type = "Driver License"
                metadata = {"state": "California", "issue_date": "2021-05-15"}
            elif "contract" in filename:
                doc_type = "Legal Contract"
                metadata = {"parties": ["Company A", "Company B"], "date": "2023-09-01"}
            elif "bank" in filename or "statement" in filename:
                doc_type = "Bank Statement"
                metadata = {"bank_name": "Sample Bank", "account_type": "Checking"}
            elif "pay" in filename or "stub" in filename:
                doc_type = "Pay Stub"
                metadata = {"pay_period": "Jan 1-15, 2023"}
            elif file_ext in [".jpg", ".jpeg", ".png"]:
                doc_type = "ID Document"
                confidence = 0.75  # Lower confidence for images
            
            # Add original document file information to metadata
            metadata["filename"] = document_data.get("filename", "")
            metadata["file_extension"] = document_data.get("file_extension", "")
            metadata["mime_type"] = document_data.get("mime_type", "")
            
            return {
                "document_type": doc_type,
                "confidence_score": confidence,
                "metadata": metadata,
                "reasoning": "This is a mock classification in debug mode."
            }
        
        # Extract text content from the document
        text_content = document_data["text_content"]
        
        # If document is too large, truncate it
        max_token_length = 15000  # Approximate token limit
        if len(text_content) > max_token_length:
            text_content = text_content[:max_token_length] + "..."
        
        # Create the prompt with document content
        prompt = self.classification_prompt.format(
            document_content=text_content,
            format_instructions=self.format_instructions
        )
        
        # Get classification from LLM
        llm_response = self.llm.invoke(prompt)
        parsed_response = self.output_parser.parse(llm_response.content)
        
        # Convert confidence_score to float if it's not already
        if isinstance(parsed_response["confidence_score"], str):
            try:
                parsed_response["confidence_score"] = float(parsed_response["confidence_score"])
            except ValueError:
                parsed_response["confidence_score"] = 0.0
        
        # Ensure metadata is a dictionary
        if not isinstance(parsed_response["metadata"], dict):
            try:
                if isinstance(parsed_response["metadata"], str):
                    parsed_response["metadata"] = json.loads(parsed_response["metadata"])
                else:
                    parsed_response["metadata"] = {}
            except:
                parsed_response["metadata"] = {}
        
        # Add original document file information to metadata
        parsed_response["metadata"]["filename"] = document_data.get("filename", "")
        parsed_response["metadata"]["file_extension"] = document_data.get("file_extension", "")
        parsed_response["metadata"]["mime_type"] = document_data.get("mime_type", "")
        
        return parsed_response