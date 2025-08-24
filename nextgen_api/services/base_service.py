"""
Base service class for NextGen API services.
Provides common functionality for making authenticated API requests.
"""
import logging
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urljoin
import requests

from ..auth.oauth_client import NextGenOAuthClient
from ..config import NextGenConfig, get_config
from ..exceptions.nextgen_exceptions import (
    NextGenAPIError, ServerError, ClientError, NetworkError,
    RateLimitError, ValidationError
)


logger = logging.getLogger(__name__)


class BaseService:
    """Base class for all NextGen API services."""

    def __init__(self, config: Optional[NextGenConfig] = None, oauth_client: Optional[NextGenOAuthClient] = None):
        """
        Initialize the service.

        Args:
            config: NextGen API configuration. If None, will load from environment.
            oauth_client: OAuth client for authentication. If None, will create one.
        """
        self.config = config or get_config()
        self.oauth_client = oauth_client or NextGenOAuthClient(self.config)
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

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint path.

        Args:
            endpoint: API endpoint path (e.g., '/master/codes')

        Returns:
            Full URL for the API request
        """
        # Remove leading slash if present to avoid double slashes
        endpoint = endpoint.lstrip('/')
        return urljoin(self.config.base_url + '/', endpoint)

    def _get_request_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Get headers for API requests including authentication.

        Args:
            additional_headers: Additional headers to include

        Returns:
            Dictionary of headers for the request
        """
        headers = self.oauth_client.get_auth_headers()

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions for errors.

        Args:
            response: requests Response object

        Returns:
            Parsed JSON response data

        Raises:
            NextGenAPIError: For various API error conditions
        """
        # Log response details for debugging
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        # Handle successful responses
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response.text}")
                raise NextGenAPIError(
                    f"Invalid JSON response: {e}",
                    status_code=response.status_code,
                    response_data={'raw_content': response.text}
                )

        # Try to parse error response
        error_data = {}
        try:
            error_data = response.json()
        except ValueError:
            error_data = {'raw_content': response.text}

        # Handle specific error status codes
        if response.status_code == 401:
            # Force token refresh on next request
            self.oauth_client.revoke_token()
            raise ClientError(
                "Authentication failed - token may be invalid",
                status_code=response.status_code,
                response_data=error_data
            )

        elif response.status_code == 403:
            raise ClientError(
                "Access forbidden - insufficient permissions",
                status_code=response.status_code,
                response_data=error_data
            )

        elif response.status_code == 404:
            raise ClientError(
                "Resource not found",
                status_code=response.status_code,
                response_data=error_data
            )

        elif response.status_code == 429:
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=response.status_code,
                response_data=error_data
            )

        elif 400 <= response.status_code < 500:
            error_message = error_data.get('message', f'Client error: {response.status_code}')
            raise ClientError(
                error_message,
                status_code=response.status_code,
                response_data=error_data
            )

        elif 500 <= response.status_code < 600:
            error_message = error_data.get('message', f'Server error: {response.status_code}')
            raise ServerError(
                error_message,
                status_code=response.status_code,
                response_data=error_data
            )

        else:
            raise NextGenAPIError(
                f"Unexpected response status: {response.status_code}",
                status_code=response.status_code,
                response_data=error_data
            )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Form data for the request body
            json_data: JSON data for the request body
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response data

        Raises:
            NextGenAPIError: For various API error conditions
        """
        url = self._build_url(endpoint)
        request_headers = self._get_request_headers(headers)
        request_timeout = timeout or self.config.timeout

        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Headers: {request_headers}")
        logger.debug(f"Params: {params}")
        logger.debug(f"Data: {data}")
        logger.debug(f"JSON: {json_data}")

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                timeout=request_timeout
            )

            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise NetworkError(f"Request timeout: {e}")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise NetworkError(f"Connection error: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise NetworkError(f"Request error: {e}")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response data
        """
        return self._make_request('GET', endpoint, params=params, headers=headers, timeout=timeout)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint path
            data: Form data for the request body
            json_data: JSON data for the request body
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response data
        """
        return self._make_request(
            'POST', endpoint, params=params, data=data,
            json_data=json_data, headers=headers, timeout=timeout
        )

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint path
            data: Form data for the request body
            json_data: JSON data for the request body
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response data
        """
        return self._make_request(
            'PUT', endpoint, params=params, data=data,
            json_data=json_data, headers=headers, timeout=timeout
        )

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response data
        """
        return self._make_request('DELETE', endpoint, params=params, headers=headers, timeout=timeout)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if hasattr(self, '_session'):
            self._session.close()