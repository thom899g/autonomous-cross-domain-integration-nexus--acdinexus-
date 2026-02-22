"""
Firebase configuration and initialization.
Centralized Firebase setup with proper credential validation and error handling.
Uses environment variables for security in production.
"""
import os
import json
from typing import Optional, Dict, Any
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_admin.exceptions import FirebaseError

class FirebaseConfig:
    """Firebase configuration manager with validation and fallback mechanisms."""
    
    _initialized: bool = False
    _db_instance = None
    _storage_instance = None
    
    @classmethod
    def initialize(cls, credential_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase with proper error handling and validation.
        
        Args:
            credential_path: Path to service account JSON file
            
        Returns:
            bool: True if initialization successful
        """
        if cls._initialized:
            logger.warning("Firebase already initialized")
            return True
            
        try:
            # Priority: env variable > file path > environment credentials
            if credential_path and os.path.exists(credential_path):
                cred = credentials.Certificate(credential_path)
            elif os.environ.get('FIREBASE_CREDENTIALS_JSON'):
                cred_dict = json.loads(os.environ['FIREBASE_CREDENTIALS_JSON'])
                cred = credentials.Certificate(cred_dict)
            else:
                # For local development with default credentials
                cred = credentials.ApplicationDefault()
                logger.info("Using default application credentials")
            
            # Initialize with project ID from env or default
            project_id = os.environ.get('FIREBASE_PROJECT_ID')
            firebase_admin.initialize_app(cred, {
                'projectId': project_id,
                'storageBucket': f"{project_id}.appspot.com"
            })
            
            cls._initialized = True
            logger.success("Firebase initialized successfully")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Credential file not found: {e}")
            return False
        except ValueError as e:
            logger.error(f"Invalid Firebase credentials: {e}")
            return False
        except FirebaseError as e:
            logger.error(f"Firebase initialization error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected initialization error: {e}")
            return False
    
    @classmethod
    def get_db(cls) -> firestore.Client:
        """Get Firestore client with lazy initialization."""
        if not cls._initialized:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        
        if cls._db_instance is None:
            try:
                cls._db_instance = firestore.client()
                logger.debug("Firestore client created")
            except Exception as e:
                logger.error(f"Failed to create Firestore client: {e}")
                raise
        return cls._db_instance
    
    @classmethod
    def get_storage(cls) -> storage.Bucket:
        """Get Cloud Storage bucket instance."""
        if not cls._initialized:
            raise RuntimeError("Firebase not initialized. Call initialize() first.")
        
        if cls._storage_instance is None:
            try:
                cls._storage_instance = storage.bucket()
                logger.debug("Storage bucket instance created")
            except Exception as e:
                logger.error(f"Failed to create storage bucket: {e}")
                raise
        return cls._storage_instance
    
    @classmethod
    def cleanup(cls):
        """Cleanup Firebase resources