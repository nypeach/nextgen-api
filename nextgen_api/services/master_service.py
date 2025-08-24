"""
Master data service for NextGen API.
Handles endpoints under /master/* for code lookups and reference data.
"""

import logging
from typing import List, Dict, Any, Optional

from .base_service import BaseService
from ..models.master import MasterCodesResponse, CodeDetail, CodeCategory
from ..exceptions.nextgen_exceptions import NextGenAPIError, ValidationError

logger = logging.getLogger(__name__)


class MasterService(BaseService):
    """Service for accessing NextGen master data endpoints."""

    def __init__(self, client):
        """
        Initialize the master service.

        Args:
            client: NextGenClient instance
        """
        super().__init__(client)
        self.base_path = "/master"

    def get_codes(self) -> MasterCodesResponse:
        """
        Get list of available code categories.

        Returns:
            MasterCodesResponse containing list of code category names

        Raises:
            NextGenAPIError: If the request fails
        """
        logger.info("Fetching available code categories from /master/codes")

        endpoint = f"{self.base_path}/codes"

        try:
            # Make the API request - returns List[str]
            raw_response = self._make_request("GET", endpoint)

            # Validate response
            if not isinstance(raw_response, list):
                raise NextGenAPIError(f"Expected list response, got {type(raw_response)}")

            # Convert to model
            codes_response = MasterCodesResponse.from_api_response(raw_response)

            logger.info(f"Successfully retrieved {codes_response.total_count} code categories")

            return codes_response

        except Exception as e:
            logger.error(f"Failed to fetch master codes: {e}")
            raise

    def get_code_details(self, code_category: str) -> List[CodeDetail]:
        """
        Get detailed information for a specific code category.

        Args:
            code_category: The code category name (e.g., "2012_condition_codes")

        Returns:
            List of CodeDetail objects for the category

        Raises:
            NextGenAPIError: If the request fails
            ValidationError: If code_category is invalid
        """
        if not code_category:
            raise ValidationError("code_category is required")

        logger.info(f"Fetching details for code category: {code_category}")

        endpoint = f"{self.base_path}/codes/{code_category}"

        try:
            raw_response = self._make_request("GET", endpoint)

            # Convert response to CodeDetail objects
            if isinstance(raw_response, list):
                code_details = [
                    CodeDetail.from_dict(item, code_category)
                    if isinstance(item, dict)
                    else CodeDetail(code=str(item), description=str(item), category=code_category)
                    for item in raw_response
                ]
            else:
                # Handle case where response is not a list
                logger.warning(f"Unexpected response type for {code_category}: {type(raw_response)}")
                code_details = []

            logger.info(f"Retrieved {len(code_details)} code details for {code_category}")
            return code_details

        except Exception as e:
            logger.error(f"Failed to fetch details for {code_category}: {e}")
            raise

    def search_codes(self,
                    code_category: str,
                    search_term: Optional[str] = None,
                    limit: Optional[int] = None) -> List[CodeDetail]:
        """
        Search within a specific code category.

        Args:
            code_category: The code category to search in
            search_term: Optional search term to filter results
            limit: Optional limit on number of results

        Returns:
            List of matching CodeDetail objects

        Raises:
            NextGenAPIError: If the request fails
            ValidationError: If code_category is invalid
        """
        if not code_category:
            raise ValidationError("code_category is required")

        logger.info(f"Searching in {code_category} with term: {search_term}")

        endpoint = f"{self.base_path}/codes/{code_category}"
        params = {}

        if search_term:
            params['search'] = search_term
        if limit:
            params['limit'] = limit

        try:
            raw_response = self._make_request("GET", endpoint, params=params)

            # Convert response to CodeDetail objects
            if isinstance(raw_response, list):
                code_details = [
                    CodeDetail.from_dict(item, code_category)
                    if isinstance(item, dict)
                    else CodeDetail(code=str(item), description=str(item), category=code_category)
                    for item in raw_response
                ]

                # Apply limit if not handled by API
                if limit and len(code_details) > limit:
                    code_details = code_details[:limit]
            else:
                code_details = []

            logger.info(f"Found {len(code_details)} matching codes in {code_category}")
            return code_details

        except Exception as e:
            logger.error(f"Failed to search codes in {code_category}: {e}")
            raise

    def list_codes_by_pattern(self, pattern: str) -> MasterCodesResponse:
        """
        Get all code categories and filter by pattern.

        Args:
            pattern: Pattern to search for in code names

        Returns:
            MasterCodesResponse with filtered codes

        Raises:
            NextGenAPIError: If the request fails
        """
        logger.info(f"Listing codes with pattern: {pattern}")

        try:
            # Get all codes first
            all_codes = self.get_codes()

            # Filter by pattern
            filtered_codes = all_codes.get_codes_by_pattern(pattern)

            # Create new response with filtered codes
            filtered_response = MasterCodesResponse(
                codes=filtered_codes,
                total_count=len(filtered_codes)
            )

            logger.info(f"Found {filtered_response.total_count} codes matching pattern '{pattern}'")
            return filtered_response

        except Exception as e:
            logger.error(f"Failed to list codes by pattern '{pattern}': {e}")
            raise

    def validate_code_exists(self, code_category: str) -> bool:
        """
        Check if a code category exists.

        Args:
            code_category: Code category name to check

        Returns:
            True if the code category exists
        """
        try:
            all_codes = self.get_codes()
            return all_codes.has_code(code_category)
        except Exception as e:
            logger.error(f"Failed to validate code existence for '{code_category}': {e}")
            return False