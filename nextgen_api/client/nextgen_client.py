"""
Main NextGen API client.
Provides access to all NextGen API services and handles authentication.
"""

import logging
from typing import Optional

from ..config import NextGenConfig, get_config
from ..auth.oauth_client import NextGenOAuthClient
from ..services.master_service import MasterService
from ..services.auth_service import AuthService
from ..exceptions.nextgen_exceptions import NextGenAPIError, ConfigurationError

logger = logging.getLogger(__name__)


class NextGenClient:
    """
    Main client for NextGen API.

    This is the primary entry point for interacting with the NextGen API.
    It handles authentication and provides access to all service modules.
    """

    def __init__(self, config: Optional[NextGenConfig] = None):
        """
        Initialize the NextGen API client.

        Args:
            config: Optional NextGenConfig. If not provided, loads from environment.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Load configuration
            self.config = config or get_config()

            # Initialize OAuth client for authentication
            self.oauth_client = NextGenOAuthClient(self.config)

            # Initialize services (lazy loading could be added here)
            self._master_service = None
            self._auth_service = None

            logger.info("NextGen API client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize NextGen client: {e}")
            raise ConfigurationError(f"Client initialization failed: {e}")

    @property
    def master(self) -> MasterService:
        """
        Access to Master data services.

        Handles endpoints like:
        - /master/codes
        - /master/allergies
        - /master/diagnoses
        - etc.

        Returns:
            MasterService instance
        """
        if self._master_service is None:
            self._master_service = MasterService(self)
        return self._master_service

    @property
    def auth(self) -> AuthService:
        """
        Access to Authentication services.

        Handles endpoints like:
        - /auth-services/identrust-mas/send-challenge
        - /auth-services/mfa/*
        - etc.

        Returns:
            AuthService instance
        """
        if self._auth_service is None:
            self._auth_service = AuthService(self)
        return self._auth_service

    def authenticate(self) -> bool:
        """
        Explicitly authenticate with the API.

        This is usually not necessary as authentication is handled automatically,
        but can be useful for testing or pre-authentication.

        Returns:
            True if authentication successful

        Raises:
            NextGenAPIError: If authentication fails
        """
        try:
            success = self.oauth_client.authenticate()
            if success:
                logger.info("Client authentication successful")
            else:
                logger.error("Client authentication failed")
            return success
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    @property
    def is_authenticated(self) -> bool:
        """
        Check if the client is currently authenticated.

        Returns:
            True if authenticated with valid token
        """
        return self.oauth_client.is_authenticated

    def get_auth_headers(self):
        """
        Get current authentication headers.

        Returns:
            Dict of headers including Authorization Bearer token
        """
        return self.oauth_client.get_auth_headers()

    def test_connection(self) -> bool:
        """
        Test the API connection by making a simple request.

        Returns:
            True if connection is working
        """
        try:
            # Use the master codes endpoint as a simple test
            codes = self.master.get_codes()
            logger.info(f"Connection test successful - retrieved {codes.total_count} code categories")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_client_info(self) -> dict:
        """
        Get information about the client configuration.

        Returns:
            Dict containing client information (without sensitive data)
        """
        return {
            "base_url": self.config.base_url,
            "client_id": self.config.client_id[:8] + "..." if self.config.client_id else None,
            "site_id": self.config.site_id,
            "grant_type": self.config.grant_type,
            "is_authenticated": self.is_authenticated,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
        }

    def close(self):
        """
        Clean up client resources.

        Call this when you're done using the client to clean up
        any persistent connections or resources.
        """
        try:
            if hasattr(self.oauth_client, '_session'):
                self.oauth_client._session.close()
            logger.info("NextGen client closed successfully")
        except Exception as e:
            logger.warning(f"Error closing client: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self):
        """String representation of the client."""
        return (
            f"NextGenClient(base_url='{self.config.base_url}', "
            f"authenticated={self.is_authenticated})"
        )