import os
import json
import asyncio
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from loguru import logger
import base64
import hashlib

class CredentialManager:
    """Manages secure storage and retrieval of authentication credentials."""
    
    def __init__(self, storage_path: str = None):
        """Initialize credential manager.
        
        Args:
            storage_path: Path to store encrypted credentials
        """
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser('~'), '.voiceassistant', 'credentials'
        )
        self._ensure_storage_directory()
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _ensure_storage_directory(self):
        """Ensure credential storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Set restrictive permissions on the directory (Windows)
        try:
            import stat
            os.chmod(self.storage_path, stat.S_IRWXU)  # Owner read/write/execute only
        except Exception as e:
            logger.warning(f"Could not set directory permissions: {e}")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credential storage.
        
        Returns:
            Encryption key bytes
        """
        key_file = os.path.join(self.storage_path, '.key')
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read encryption key: {e}")
                # Fall through to create new key
        
        # Create new encryption key
        key = Fernet.generate_key()
        
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions on key file
            import stat
            os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)  # Owner read/write only
            
            logger.info("Created new encryption key for credential storage")
            return key
            
        except Exception as e:
            logger.error(f"Failed to create encryption key: {e}")
            raise
    
    def _get_credential_file_path(self, service_name: str) -> str:
        """Get file path for storing service credentials.
        
        Args:
            service_name: Name of the service (e.g., 'google_oauth')
            
        Returns:
            Full path to credential file
        """
        # Hash service name to avoid filesystem issues
        service_hash = hashlib.sha256(service_name.encode()).hexdigest()[:16]
        return os.path.join(self.storage_path, f"{service_hash}.cred")
    
    async def store_credentials(self, service_name: str, credentials: Dict[str, Any]) -> bool:
        """Store encrypted credentials for a service.
        
        Args:
            service_name: Name of the service
            credentials: Credential data to store
            
        Returns:
            True if storage successful
        """
        try:
            # Serialize credentials to JSON
            cred_json = json.dumps(credentials, indent=2)
            
            # Encrypt credentials
            encrypted_data = self._cipher.encrypt(cred_json.encode())
            
            # Store to file
            file_path = self._get_credential_file_path(service_name)
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            import stat
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
            
            logger.info(f"Stored credentials for service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials for {service_name}: {e}")
            return False
    
    async def get_credentials(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt credentials for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Decrypted credential data or None if not found
        """
        try:
            file_path = self._get_credential_file_path(service_name)
            
            if not os.path.exists(file_path):
                logger.debug(f"No credentials found for service: {service_name}")
                return None
            
            # Read encrypted data
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt credentials
            decrypted_data = self._cipher.decrypt(encrypted_data)
            credentials = json.loads(decrypted_data.decode())
            
            logger.debug(f"Retrieved credentials for service: {service_name}")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {service_name}: {e}")
            return None
    
    async def delete_credentials(self, service_name: str) -> bool:
        """Delete stored credentials for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if deletion successful
        """
        try:
            file_path = self._get_credential_file_path(service_name)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted credentials for service: {service_name}")
            else:
                logger.debug(f"No credentials to delete for service: {service_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credentials for {service_name}: {e}")
            return False
    
    async def list_stored_services(self) -> list[str]:
        """List all services with stored credentials.
        
        Returns:
            List of service names with stored credentials
        """
        try:
            services = []
            
            if not os.path.exists(self.storage_path):
                return services
            
            # This is a simplified approach - in practice, you might want to
            # maintain a separate index file mapping hashes to service names
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.cred'):
                    # For now, we'll use a reverse lookup approach
                    # In production, consider maintaining a service name index
                    services.append(filename.replace('.cred', ''))
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to list stored services: {e}")
            return []
    
    async def clear_all_credentials(self) -> bool:
        """Clear all stored credentials (use with caution).
        
        Returns:
            True if clearing successful
        """
        try:
            if os.path.exists(self.storage_path):
                import shutil
                shutil.rmtree(self.storage_path)
                logger.warning("Cleared all stored credentials")
            
            # Recreate storage directory
            self._ensure_storage_directory()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear all credentials: {e}")
            return False
    
    def is_service_authenticated(self, service_name: str) -> bool:
        """Check if credentials exist for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if credentials are stored for the service
        """
        file_path = self._get_credential_file_path(service_name)
        return os.path.exists(file_path)
    
    async def update_credentials(self, service_name: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in stored credentials.
        
        Args:
            service_name: Name of the service
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful
        """
        try:
            # Get existing credentials
            existing_creds = await self.get_credentials(service_name)
            if not existing_creds:
                logger.error(f"No existing credentials found for {service_name}")
                return False
            
            # Update with new values
            existing_creds.update(updates)
            
            # Store updated credentials
            return await self.store_credentials(service_name, existing_creds)
            
        except Exception as e:
            logger.error(f"Failed to update credentials for {service_name}: {e}")
            return False