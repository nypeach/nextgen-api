"""
Data models for NextGen Master endpoints.
Defines the structure of data returned from /master/* endpoints.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class MasterCodesResponse:
    """
    Response model for /master/codes endpoint.

    The API returns a simple list of code category names.
    """
    codes: List[str]
    total_count: int

    @classmethod
    def from_api_response(cls, api_response: List[str]) -> 'MasterCodesResponse':
        """
        Create MasterCodesResponse from API response.

        Args:
            api_response: Raw list of strings from API

        Returns:
            MasterCodesResponse instance
        """
        return cls(
            codes=api_response,
            total_count=len(api_response)
        )

    def get_codes_by_pattern(self, pattern: str) -> List[str]:
        """
        Filter codes by a pattern (e.g., 'appointment', 'condition').

        Args:
            pattern: Pattern to search for (case-insensitive)

        Returns:
            List of matching codes
        """
        pattern_lower = pattern.lower()
        return [code for code in self.codes if pattern_lower in code.lower()]

    def has_code(self, code_name: str) -> bool:
        """
        Check if a specific code exists.

        Args:
            code_name: Name of the code to check

        Returns:
            True if code exists, False otherwise
        """
        return code_name in self.codes


@dataclass
class CodeCategory:
    """
    Model for a single code category.
    This will be useful for future endpoints that return detailed code information.
    """
    name: str
    description: Optional[str] = None
    active: bool = True
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeCategory':
        """
        Create CodeCategory from dictionary data.

        Args:
            data: Dictionary containing code category data

        Returns:
            CodeCategory instance
        """
        return cls(
            name=data.get('name', ''),
            description=data.get('description'),
            active=data.get('active', True),
            created_date=cls._parse_date(data.get('created_date')),
            last_updated=cls._parse_date(data.get('last_updated'))
        )

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            # Handle common date formats
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None


@dataclass
class CodeDetail:
    """
    Model for detailed code information.
    This will be useful for future endpoints like /master/codes/{codeType}.
    """
    code: str
    description: str
    category: str
    active: bool = True
    display_order: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], category: str = '') -> 'CodeDetail':
        """
        Create CodeDetail from dictionary data.

        Args:
            data: Dictionary containing code detail data
            category: The category this code belongs to

        Returns:
            CodeDetail instance
        """
        return cls(
            code=data.get('code', ''),
            description=data.get('description', ''),
            category=category,
            active=data.get('active', True),
            display_order=data.get('display_order'),
            additional_data=data.get('additional_data')
        )