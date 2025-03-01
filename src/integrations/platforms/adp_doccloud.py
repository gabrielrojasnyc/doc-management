import os
import json
import aiohttp
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

class PlatformConnector:
    """
    Specialized connector for ADP DocCloud platform.
    Handles authentication and platform-specific requirements.
    """
    
    def __init__(self):
        """Initialize the ADP DocCloud connector"""
        self.api_url = os.getenv("ADP_DOCCLOUD_API_URL", "https://api.doccloud.adp.com/v1")
        self.api_key = os.getenv("ADP_DOCCLOUD_API_KEY")
        self.client_id = os.getenv("ADP_DOCCLOUD_CLIENT_ID")
        self.client_secret = os.getenv("ADP_DOCCLOUD_CLIENT_SECRET")
        
        if not self.api_key or not self.client_id or not self.client_secret:
            raise ValueError("Missing ADP DocCloud API credentials in environment variables")
    
    async def push_document(
        self,
        document_id: str,
        file: UploadFile,
        classification_result: Dict[str, Any],
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Push document and classification to ADP DocCloud
        
        Args:
            document_id: Unique document identifier
            file: The document file
            classification_result: Classification results
            callback_url: Optional URL to notify when upload is complete
            
        Returns:
            Dictionary with upload result status
        """
        # Reset file position to start
        await file.seek(0)
        file_content = await file.read()
        
        # Prepare metadata for upload
        metadata = {
            "documentId": document_id,
            "fileName": file.filename,
            "contentType": file.content_type,
            "documentType": classification_result["document_type"],
            "metadataFields": [
                # Convert flat metadata dict to ADP DocCloud's field format
                {"name": key, "value": value}
                for key, value in classification_result["metadata"].items()
            ],
            "confidenceScore": classification_result["confidence_score"],
            "classifierVersion": "1.0.0"
        }
        
        # Get authentication token
        auth_token = await self._get_auth_token()
        if not auth_token:
            return {
                "success": False,
                "error": "Failed to obtain authentication token",
                "platform": "adp_doccloud"
            }
        
        try:
            # Upload document to ADP DocCloud
            async with aiohttp.ClientSession() as session:
                # First, create document metadata
                metadata_url = f"{self.api_url}/documents"
                async with session.post(
                    metadata_url,
                    json=metadata,
                    headers={
                        "Authorization": f"Bearer {auth_token}",
                        "Content-Type": "application/json",
                        "X-ADP-Client-ID": self.client_id
                    }
                ) as metadata_response:
                    if metadata_response.status >= 400:
                        error_text = await metadata_response.text()
                        return {
                            "success": False,
                            "error": f"Metadata creation failed: {error_text}",
                            "platform": "adp_doccloud"
                        }
                    
                    metadata_result = await metadata_response.json()
                    adp_document_id = metadata_result.get("documentId")
                
                # Then, upload file content
                upload_url = f"{self.api_url}/documents/{adp_document_id}/content"
                
                # Create form data with file
                form_data = aiohttp.FormData()
                form_data.add_field(
                    name="file",
                    value=file_content,
                    filename=file.filename,
                    content_type=file.content_type
                )
                
                async with session.put(
                    upload_url,
                    data=form_data,
                    headers={
                        "Authorization": f"Bearer {auth_token}",
                        "X-ADP-Client-ID": self.client_id
                    }
                ) as upload_response:
                    if upload_response.status >= 400:
                        error_text = await upload_response.text()
                        return {
                            "success": False,
                            "error": f"File upload failed: {error_text}",
                            "platform": "adp_doccloud"
                        }
                
                # Notify callback URL if provided
                if callback_url:
                    callback_data = {
                        "document_id": document_id,
                        "platform": "adp_doccloud",
                        "status": "success",
                        "platform_document_id": adp_document_id,
                        "classification": classification_result["document_type"]
                    }
                    
                    async with session.post(
                        callback_url, 
                        json=callback_data,
                        headers={"Content-Type": "application/json"}
                    ) as callback_response:
                        pass  # We don't need to process the callback response
                
                return {
                    "success": True,
                    "platform_document_id": adp_document_id,
                    "platform": "adp_doccloud"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "platform": "adp_doccloud"
            }
    
    async def _get_auth_token(self) -> Optional[str]:
        """
        Get authentication token from ADP OAuth API
        
        Returns:
            Authentication token or None if failed
        """
        try:
            auth_url = f"{self.api_url}/auth/token"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    auth_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                ) as response:
                    if response.status < 400:
                        result = await response.json()
                        return result.get("access_token")
            
            return None
        except Exception:
            return None