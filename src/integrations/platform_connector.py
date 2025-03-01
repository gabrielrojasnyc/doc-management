import os
import json
import aiohttp
import importlib
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

class PlatformConnector:
    """
    Handles integration with various document management platforms.
    Provides a standardized interface for pushing classification results.
    """
    
    def __init__(self):
        """Initialize the platform connector with available integrations"""
        debug_mode = os.getenv("DEBUG", "")
        self.debug_mode = debug_mode.lower() in ["true", "1"]
        
        self.platforms = {
            "BU_doccloud": {
                "name": "BU DocCloud",
                "description": "Native BU document management platform",
                "api_url": os.getenv("BU_DOCCLOUD_API_URL", "https://api.doccloud.BU.com/v1")
            },
            "sharepoint": {
                "name": "Microsoft SharePoint",
                "description": "Microsoft's document management and storage system",
                "api_url": os.getenv("SHAREPOINT_API_URL", "")
            },
            "box": {
                "name": "Box",
                "description": "Cloud content management platform",
                "api_url": os.getenv("BOX_API_URL", "https://api.box.com/2.0")
            },
            "dropbox": {
                "name": "Dropbox",
                "description": "File hosting service",
                "api_url": os.getenv("DROPBOX_API_URL", "https://api.dropboxapi.com/2")
            },
            "google_drive": {
                "name": "Google Drive",
                "description": "Google's file storage and synchronization service",
                "api_url": os.getenv("GDRIVE_API_URL", "https://www.googleapis.com/drive/v3")
            },
            "onedrive": {
                "name": "Microsoft OneDrive",
                "description": "Microsoft's file hosting service",
                "api_url": os.getenv("ONEDRIVE_API_URL", "https://graph.microsoft.com/v1.0/me/drive")
            }
        }
    
    def get_supported_platforms(self) -> List[Dict[str, str]]:
        """
        Get list of supported document management platforms
        
        Returns:
            List of supported platforms with name and description
        """
        return [
            {
                "id": platform_id,
                "name": platform_info["name"],
                "description": platform_info["description"]
            }
            for platform_id, platform_info in self.platforms.items()
        ]
    
    async def push_classification(
        self,
        platform: str,
        document_id: str,
        file: UploadFile,
        classification_result: Dict[str, Any],
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Push classification results to the specified document management platform
        
        Args:
            platform: Platform identifier
            document_id: Unique document identifier
            file: The document file
            classification_result: Classification results
            callback_url: Optional URL to notify when upload is complete
            
        Returns:
            Dictionary with upload result status
        """
        # In debug mode, return a mock successful response
        if self.debug_mode:
            print(f"DEBUG MODE: Mock upload to {platform} platform")
            return {
                "success": True,
                "platform_document_id": f"mock-{document_id}",
                "platform": platform,
                "debug_mode": True,
                "document_type": classification_result["document_type"]
            }
            
        # Validate platform
        if platform not in self.platforms:
            return {
                "success": False,
                "error": f"Unsupported platform: {platform}"
            }
        
        # Try to load platform-specific integration if available
        try:
            # Check if we have a custom integration module for this platform
            integration_module = importlib.import_module(f"src.integrations.platforms.{platform}")
            connector = integration_module.PlatformConnector()
            return await connector.push_document(document_id, file, classification_result, callback_url)
        except (ImportError, ModuleNotFoundError):
            # Fall back to generic implementation
            return await self._generic_platform_upload(
                platform, document_id, file, classification_result, callback_url
            )
    
    async def _generic_platform_upload(
        self,
        platform: str,
        document_id: str,
        file: UploadFile,
        classification_result: Dict[str, Any],
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generic implementation for uploading to document platforms
        
        Args:
            platform: Platform identifier
            document_id: Unique document identifier
            file: The document file
            classification_result: Classification results
            callback_url: Optional URL to notify when upload is complete
            
        Returns:
            Dictionary with upload result status
        """
        platform_config = self.platforms[platform]
        api_url = platform_config["api_url"]
        
        # Reset file position to start
        await file.seek(0)
        file_content = await file.read()
        
        # Prepare metadata for upload
        metadata = {
            "document_id": document_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "document_type": classification_result["document_type"],
            "classification_metadata": classification_result["metadata"],
            "confidence_score": classification_result["confidence_score"]
        }
        
        # Implementation for generic upload
        # This is a simplified example that would need to be customized for each platform
        try:
            # Example API request to upload document
            async with aiohttp.ClientSession() as session:
                # Upload document file
                upload_url = f"{api_url}/documents"
                
                # Create form data with file and metadata
                form_data = aiohttp.FormData()
                form_data.add_field(
                    name="file",
                    value=file_content,
                    filename=file.filename,
                    content_type=file.content_type
                )
                form_data.add_field(
                    name="metadata", 
                    value=json.dumps(metadata),
                    content_type="application/json"
                )
                
                # Make POST request to upload document
                async with session.post(upload_url, data=form_data) as response:
                    if response.status < 400:
                        upload_result = await response.json()
                        
                        # Notify callback URL if provided
                        if callback_url:
                            callback_data = {
                                "document_id": document_id,
                                "platform": platform,
                                "status": "success",
                                "platform_document_id": upload_result.get("id", ""),
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
                            "platform_document_id": upload_result.get("id", ""),
                            "platform": platform
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Upload failed with status {response.status}: {error_text}",
                            "platform": platform
                        }
        
        except Exception as e:
            # Handle any exceptions
            return {
                "success": False,
                "error": str(e),
                "platform": platform
            }