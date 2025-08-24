"""
OAuth 2.0 client for NextGen API authentication.
Implements the same token management logic as the Postman pre-request script.
"""
import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..config import NextGenConfig
from ..exceptions.nextgen_exceptions import AuthenticationError, TokenExpiredError


logger = logging.getLogger(__name__)


class NextGenOAuthClient:
    """OAuth 2.0 client for NextGen API with automatic token management."""
    
    def __init__(self, config: NextGenConfig):
        """
        Initialize the OAuth client.
        
        Args:
            config: NextGen API configuration
        """
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
        self._session = requests.Session()
        
        # Set up session with default headers
        self._session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': self.config.accept,
            'Accept-Encoding': self.config.accept_encoding,
            'Connection': self.config.connection,
        })
        
        # Configure SSL verification and redirects
        self._session.verify = self.config.verify_ssl
        if hasattr(self._session, 'max_redirects'):
            self._session.max_redirects = 10 if self.config.follow_redirects else 0
    
    @property
    def access_token(self) -> Optional[str]:
        """Get the current access token, refreshing if necessary."""
        if self._should_refresh_token():
            self._refresh_token()
        return self._access_token
    
    @property
    def is_authenticated(self) -> bool:
        """Check if we have a valid access token."""
        return self._access_token is not None and not self._is_token_expired()
    
    def _should_refresh_token(self) -> bool:
        """
        Check if we should refresh the token.
        Mirrors the logic from the Postman pre-request script.
        """
        if not self._access_token or not self._token_expiration:
            logger.info("Token or expiration date missing.")
            return True
        
        if self._is_token_expired():
            logger.info("The token has expired.")
            return True
        
        logger.info("Token exists and is valid.")
        return False
    
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired."""
        if not self._token_expiration:
            return True
        return self._token_expiration <= datetime.now()
    
    def _refresh_token(self):
        """
        Refresh the access token using client credentials flow.
        Implements the same logic as the Postman pre-request script.
        """
        logger.info("Refreshing access token...")
        
        # Prepare token request parameters (matches Postman script)
        params = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'site_id': self.config.site_id,
            'grant_type': self.config.grant_type
        }
        
        # Add username/password if using password grant type
        if self.config.grant_type == 'password':
            username = getattr(self.config, 'username', None)
            password = getattr(self.config, 'password', None)
            if username and password:
                params.update({
                    'username': username,
                    'password': password
                })
        
        try:
            # Make token request
            response = self._session.post(
                self.config.token_url,
                data=params,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                timeout=self.config.timeout
            )
            
            logger.debug(f"Token request URL: {self.config.token_url}")
            logger.debug(f"Token request params: {params}")
            
            if response.status_code != 200:
                logger.error(f"Failed to acquire access token. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                raise AuthenticationError(
                    f"Token request failed with status {response.status_code}: {response.text}"
                )
            
            token_data = response.json()
            logger.info("Successfully acquired access token.")
            
            # Extract token and calculate expiration (matches Postman script)
            self._access_token = token_data.get('access_token')
            if not self._access_token:
                raise AuthenticationError("No access_token in response")
            
            # Calculate expiration time
            expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
            self._token_expiration = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info(f"Token expires at: {self._token_expiration}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during token refresh: {e}")
            raise AuthenticationError(f"Failed to refresh token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise AuthenticationError(f"Failed to refresh token: {e}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict with Authorization header containing Bearer token
        
        Raises:
            AuthenticationError: If unable to get valid token
        """
        if not self.access_token:
            raise AuthenticationError("Unable to obtain access token")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        # Add session ID header if configured
        if self.config.x_ng_session_id:
            headers['x-ng-sessionid'] = self.config.x_ng_session_id
        
        return headers
    
    def authenticate(self) -> bool:
        """
        Authenticate with the API and obtain an access token.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self._refresh_token()
            return self.is_authenticated
        except AuthenticationError:
            return False
    
    def revoke_token(self):
        """Revoke the current token and clear stored credentials."""
        # Note: NextGen API may not have a revoke endpoint
        # This method clears the local token
        self._access_token = None
        self._token_expiration = None
        logger.info("Token revoked and cleared from local storage.")
    
    def __enter__(self):
        """Context manager entry."""
        if not self.is_authenticated:
            self.authenticate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Clean up session
        self._session.close()