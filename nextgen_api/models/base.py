"""
Base model class for NextGen API data structures.
Provides common functionality for all model classes.
"""
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseModel(ABC):
    """
    Abstract base class for all NextGen API models.

    Provides common functionality like serialization, validation,
    and utility methods that all models should have.
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary representation.

        This method should be implemented by subclasses to provide
        a dictionary representation of the model data.

        Returns:
            Dictionary representation of the model
        """
        # Default implementation using dataclass fields if available
        if hasattr(self, '__dataclass_fields__'):
            return {
                field.name: getattr(self, field.name)
                for field in self.__dataclass_fields__.values()
            }

        # Fallback to instance variables
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Convert the model to a JSON string.

        Args:
            indent: Number of spaces to use for indentation (None for compact)

        Returns:
            JSON string representation of the model
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Create a model instance from a dictionary.

        Args:
            data: Dictionary containing model data

        Returns:
            Model instance

        Note:
            This is a generic implementation. Subclasses should override
            this method if they need custom deserialization logic.
        """
        # This is a basic implementation - subclasses should override for custom logic
        if hasattr(cls, '__dataclass_fields__'):
            # For dataclasses, filter to only known fields
            field_names = set(cls.__dataclass_fields__.keys())
            filtered_data = {k: v for k, v in data.items() if k in field_names}
            return cls(**filtered_data)

        # Fallback for non-dataclass models
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'BaseModel':
        """
        Create a model instance from a JSON string.

        Args:
            json_str: JSON string containing model data

        Returns:
            Model instance

        Raises:
            ValueError: If JSON is invalid
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model attributes from a dictionary.

        Args:
            data: Dictionary containing updated values
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def copy(self) -> 'BaseModel':
        """
        Create a copy of the model.

        Returns:
            New instance with the same data
        """
        return self.__class__.from_dict(self.to_dict())

    def __eq__(self, other) -> bool:
        """Check equality with another model instance."""
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()

    def __ne__(self, other) -> bool:
        """Check inequality with another model instance."""
        return not self.__eq__(other)