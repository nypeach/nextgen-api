"""
Authentication service for NextGen API.
Handles authentication-related endpoints like identity verification and challenges.
"""

import logging
from typing import Dict, Any, Optional, List
import json

from .base_service import BaseService
from ..exceptions.nextgen_exceptions import NextGenAPIError, ClientError, ValidationError

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Service for NextGen authentication-related API endpoints."""

    def __init__(self, client):
        """
        Initialize the authentication service.

        Args:
            client: NextGenClient instance
        """
        super().__init__(client)
        self.base_path = "/auth-services"

    def send_identrust_challenge(self) -> Dict[str, Any]:
        """
        Send an identity trust MAS (Multi-factor Authentication Service) challenge.

        This endpoint initiates an identity verification process using Identrust's
        Multi-factor Authentication Service.

        Returns:
            Dict containing challenge response data

        Raises:
            NextGenAPIError: If the request fails
        """
        logger.info("Sending Identrust MAS challenge")

        endpoint = f"{self.base_path}/identrust-mas/send-challenge"

        try:
            response_data = self._make_request("GET", endpoint)
            logger.info("Successfully sent Identrust challenge")
            return response_data

        except Exception as e:
            logger.error(f"Failed to send Identrust challenge: {e}")
            raise

    def verify_identity_challenge(self,
                                challenge_id: str,
                                response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an identity challenge response.

        Args:
            challenge_id: The challenge identifier from send_challenge
            response_data: The challenge response data

        Returns:
            Dict containing verification result

        Raises:
            NextGenAPIError: If verification fails
            ValidationError: If input data is invalid
        """
        if not challenge_id:
            raise ValidationError("challenge_id is required")

        if not response_data:
            raise ValidationError("response_data is required")

        logger.info(f"Verifying identity challenge: {challenge_id}")

        endpoint = f"{self.base_path}/identrust-mas/verify-challenge/{challenge_id}"

        try:
            result = self._make_request("POST", endpoint, json_data=response_data)
            logger.info(f"Challenge verification completed for: {challenge_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to verify challenge {challenge_id}: {e}")
            raise

    def get_challenge_status(self, challenge_id: str) -> Dict[str, Any]:
        """
        Get the status of an authentication challenge.

        Args:
            challenge_id: The challenge identifier

        Returns:
            Dict containing challenge status information

        Raises:
            NextGenAPIError: If the request fails
            ValidationError: If challenge_id is invalid
        """
        if not challenge_id:
            raise ValidationError("challenge_id is required")

        logger.info(f"Getting challenge status: {challenge_id}")

        endpoint = f"{self.base_path}/identrust-mas/challenge-status/{challenge_id}"

        try:
            status_data = self._make_request("GET", endpoint)
            logger.info(f"Retrieved challenge status for: {challenge_id}")
            return status_data

        except Exception as e:
            logger.error(f"Failed to get challenge status {challenge_id}: {e}")
            raise

    def initiate_mfa(self,
                    user_identifier: str,
                    mfa_method: str = "sms") -> Dict[str, Any]:
        """
        Initiate multi-factor authentication for a user.

        Args:
            user_identifier: User ID or identifier
            mfa_method: MFA method (sms, email, app, etc.)

        Returns:
            Dict containing MFA initiation response

        Raises:
            NextGenAPIError: If the request fails
            ValidationError: If input parameters are invalid
        """
        if not user_identifier:
            raise ValidationError("user_identifier is required")

        if mfa_method not in ["sms", "email", "app", "voice"]:
            raise ValidationError(f"Invalid MFA method: {mfa_method}")

        logger.info(f"Initiating MFA for user: {user_identifier} via {mfa_method}")

        endpoint = f"{self.base_path}/mfa/initiate"

        payload = {
            "user_identifier": user_identifier,
            "method": mfa_method
        }

        try:
            response_data = self._make_request("POST", endpoint, json_data=payload)
            logger.info(f"MFA initiated for user: {user_identifier}")
            return response_data

        except Exception as e:
            logger.error(f"Failed to initiate MFA for {user_identifier}: {e}")
            raise

    def verify_mfa_code(self,
                       mfa_session_id: str,
                       verification_code: str) -> Dict[str, Any]:
        """
        Verify an MFA code.

        Args:
            mfa_session_id: MFA session identifier from initiate_mfa
            verification_code: The code provided by user

        Returns:
            Dict containing MFA verification result

        Raises:
            NextGenAPIError: If verification fails
            ValidationError: If input parameters are invalid
        """
        if not mfa_session_id:
            raise ValidationError("mfa_session_id is required")

        if not verification_code:
            raise ValidationError("verification_code is required")

        logger.info(f"Verifying MFA code for session: {mfa_session_id}")

        endpoint = f"{self.base_path}/mfa/verify"

        payload = {
            "session_id": mfa_session_id,
            "code": verification_code
        }

        try:
            result = self._make_request("POST", endpoint, json_data=payload)
            logger.info(f"MFA verification completed for session: {mfa_session_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to verify MFA for session {mfa_session_id}: {e}")
            raise

    def get_auth_methods(self, user_identifier: str) -> List[Dict[str, Any]]:
        """
        Get available authentication methods for a user.

        Args:
            user_identifier: User ID or identifier

        Returns:
            List of available authentication methods

        Raises:
            NextGenAPIError: If the request fails
            ValidationError: If user_identifier is invalid
        """
        if not user_identifier:
            raise ValidationError("user_identifier is required")

        logger.info(f"Getting auth methods for user: {user_identifier}")

        endpoint = f"{self.base_path}/methods/{user_identifier}"

        try:
            methods = self._make_request("GET", endpoint)
            logger.info(f"Retrieved {len(methods) if isinstance(methods, list) else 'unknown'} auth methods")
            return methods if isinstance(methods, list) else []

        except Exception as e:
            logger.error(f"Failed to get auth methods for {user_identifier}: {e}")
            raise

    def validate_session(self, session_token: str) -> Dict[str, Any]:
        """
        Validate an authentication session token.

        Args:
            session_token: Session token to validate

        Returns:
            Dict containing session validation result

        Raises:
            NextGenAPIError: If validation fails
            ValidationError: If session_token is invalid
        """
        if not session_token:
            raise ValidationError("session_token is required")

        logger.info("Validating session token")

        endpoint = f"{self.base_path}/session/validate"

        payload = {
            "session_token": session_token
        }

        try:
            result = self._make_request("POST", endpoint, json_data=payload)
            logger.info("Session validation completed")
            return result

        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            raise

    def logout_session(self, session_token: str) -> bool:
        """
        Logout/invalidate an authentication session.

        Args:
            session_token: Session token to logout

        Returns:
            True if logout successful

        Raises:
            NextGenAPIError: If logout fails
        """
        if not session_token:
            raise ValidationError("session_token is required")

        logger.info("Logging out session")

        endpoint = f"{self.base_path}/session/logout"

        payload = {
            "session_token": session_token
        }

        try:
            result = self._make_request("POST", endpoint, json_data=payload)
            logger.info("Session logout completed")
            return result.get('success', True) if isinstance(result, dict) else True

        except Exception as e:
            logger.error(f"Failed to logout session: {e}")
            raise