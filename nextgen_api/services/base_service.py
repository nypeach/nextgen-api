"""
Base service class for NextGen API services.
Provides common functionality for making authenticated API requests.
"""

import logging
from typing import Dict, Any, Optional, Union, List
import requests

from ..exceptions.nextgen_exceptions import (
    NextGenAPIError,
    ClientError,
    ServerError,
    RateLimitError,
    NetworkError
)

logger = logging.getLogger(__name__)


class BaseService:
    """Base class for all NextGen API services."""

    def __init__(self, client):
        """
        Initialize the base service.

        Args:
            client: NextGenClient instance
        """
        self.client = client
        self.config = client.config
        self.oauth_client = client.oauth_client

    def _make_request(self,
                     method: str,
                     endpoint: str,
                     params: Optional[Dict[str, Any]] = None,
                     json_data: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> Union[Dict, List, str]:
        """
        Make an authenticated request to the NextGen API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (will be appended to base_url)
            params: Query parameters
            json_data: JSON data for POST/PUT requests
            headers: Additional headers

        Returns:
            Response data (parsed JSON or raw text)

        Raises:
            NextGenAPIError: For various API errors
        """
        # Construct full URL
        if endpoint.startswith('/'):
            url = f"{self.config.base_url}{endpoint}"
        else:
            url = f"{self.config.base_url}/{endpoint}"

        # Get authentication headers
        auth_headers = self.oauth_client.get_auth_headers()

        # Merge with additional headers
        request_headers = {
            'User-Agent': self.config.user_agent,
            'Accept': self.config.accept,
            'Accept-Encoding': self.config.accept_encoding,
            'Connection': self.config.connection,
        }
        request_headers.update(auth_headers)

        if headers:
            request_headers.update(headers)

        # Add Content-Type for JSON requests
        if json_data:
            request_headers['Content-Type'] = 'application/json'

        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Headers: {list(request_headers.keys())}")
        logger.debug(f"Params: {params}")

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )

            # Log response details
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            return self._handle_response(response)

        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {e}")

    def _handle_response(self, response: requests.Response) -> Union[Dict, List, str]:
        """
        Handle the HTTP response and extract data.

        Args:
            response: requests.Response object

        Returns:
            Parsed response data

        Raises:
            NextGenAPIError: For various API errors
        """
        # Handle different status codes
        if response.status_code == 200:
            return self._parse_response_data(response)
        elif response.status_code == 401:
            # Token might be expired, try to refresh
            logger.warning("Received 401, attempting token refresh")
            try:
                self.oauth_client._refresh_token()
                # Don't retry automatically - let the caller handle it
                raise ClientError("Unauthorized - token may need refresh",
                                status_code=401,
                                response_data=self._get_error_data(response))
            except Exception as e:
                raise ClientError(f"Authentication failed: {e}",
                                status_code=401,
                                response_data=self._get_error_data(response))
        elif response.status_code == 403:
            raise ClientError("Forbidden - insufficient permissions",
                            status_code=403,
                            response_data=self._get_error_data(response))
        elif response.status_code == 404:
            raise ClientError("Not found",
                            status_code=404,
                            response_data=self._get_error_data(response))
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded",
                               status_code=429,
                               response_data=self._get_error_data(response))
        elif 400 <= response.status_code < 500:
            raise ClientError(f"Client error: {response.status_code}",
                            status_code=response.status_code,
                            response_data=self._get_error_data(response))
        elif 500 <= response.status_code < 600:
            raise ServerError(f"Server error: {response.status_code}",
                            status_code=response.status_code,
                            response_data=self._get_error_data(response))
        else:
            raise NextGenAPIError(f"Unexpected status code: {response.status_code}",
                                status_code=response.status_code,
                                response_data=self._get_error_data(response))

    def _parse_response_data(self, response: requests.Response) -> Union[Dict, List, str]:
        """Parse response data based on content type."""
        content_type = response.headers.get('content-type', '').lower()

        if 'application/json' in content_type:
            try:
                return response.json()
            except ValueError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                return response.text
        else:
            return response.text

    def _get_error_data(self, response: requests.Response) -> Dict[str, Any]:
        """Extract error data from response."""
        try:
            return response.json()
        except ValueError:
            return {'error_text': response.text}

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.

        Args:
            endpoint: API endpoint

        Returns:
            Full URL
        """
        if endpoint.startswith('/'):
            return f"{self.config.base_url}{endpoint}"
        else:
            return f"{self.config.base_url}/{endpoint}"

    def _log_request(self, method: str, url: str, **kwargs):
        """Log request details."""
        logger.info(f"{method} {url}")
        if kwargs.get('params'):
            logger.debug(f"Query params: {kwargs['params']}")
        if kwargs.get('json'):
            logger.debug(f"JSON data: {kwargs['json']}")

    def _log_response(self, response: requests.Response):
        """Log response details."""
        logger.info(f"Response: {response.status_code}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Response headers: {dict(response.headers)}")
            if response.text:
                logger.debug(f"Response body: {response.text[:500]}...")  # First 500 chars