"""
Configuration management for the NextGen API library.
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class NextGenConfig:
    """Configuration class for NextGen API settings."""
    
    # OAuth 2.0 credentials
    client_id: str
    client_secret: str
    site_id: str
    
    # API endpoints (NextGen specific URLs)
    base_url: str = "https://nativeapi.nextgen.com/nge/prod/nge-api/api"
    token_url: str = "https://nativeapi.nextgen.com/nge/prod/nge-oauth/token"
    authorization_url: str = "https://nativeapi.nextgen.com/nge/prod/nge-oauth/authorize"
    
    # OAuth settings
    grant_type: str = "client_credentials"
    scope: Optional[str] = None
    
    # Session settings
    x_ng_session_id: Optional[str] = None
    
    # Request settings
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    follow_redirects: bool = True
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Default headers
    user_agent: str = "NextGenAPI-Python/1.0.0"
    accept: str = "*/*"
    accept_encoding: str = "gzip, deflate, br"
    connection: str = "keep-alive"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.client_id:
            raise ValueError("client_id is required")
        if not self.client_secret:
            raise ValueError("client_secret is required")
        if not self.site_id:
            raise ValueError("site_id is required")


def load_config() -> NextGenConfig:
    """
    Load configuration from environment variables.
    
    Environment variables:
    - NEXTGEN_CLIENT_ID: OAuth client ID (required)
    - NEXTGEN_CLIENT_SECRET: OAuth client secret (required)
    - NEXTGEN_SITE_ID: Site ID for the API (required)
    - NEXTGEN_BASE_URL: Base URL for API endpoints
    - NEXTGEN_TOKEN_URL: OAuth token endpoint URL
    - NEXTGEN_AUTHORIZATION_URL: OAuth authorization endpoint URL
    - NEXTGEN_GRANT_TYPE: OAuth grant type
    - NEXTGEN_X_NG_SESSION_ID: Session ID header value
    - NEXTGEN_TIMEOUT: Request timeout in seconds
    - NEXTGEN_MAX_RETRIES: Maximum number of retries
    - NEXTGEN_VERIFY_SSL: Verify SSL certificates (true/false)
    - NEXTGEN_FOLLOW_REDIRECTS: Follow HTTP redirects (true/false)
    - NEXTGEN_USER_AGENT: Custom user agent string
    
    Returns:
        NextGenConfig: Configuration object
    
    Raises:
        ValueError: If required environment variables are missing
    """
    client_id = os.getenv("NEXTGEN_CLIENT_ID")
    client_secret = os.getenv("NEXTGEN_CLIENT_SECRET")
    site_id = os.getenv("NEXTGEN_SITE_ID")
    
    if not client_id:
        raise ValueError(
            "NEXTGEN_CLIENT_ID environment variable is required. "
            "Please set it or copy .env.example to .env and fill in your credentials."
        )
    
    if not client_secret:
        raise ValueError(
            "NEXTGEN_CLIENT_SECRET environment variable is required. "
            "Please set it or copy .env.example to .env and fill in your credentials."
        )
    
    if not site_id:
        raise ValueError(
            "NEXTGEN_SITE_ID environment variable is required. "
            "Please set it or copy .env.example to .env and fill in your credentials."
        )
    
    # Handle boolean environment variables
    verify_ssl = os.getenv("NEXTGEN_VERIFY_SSL", "true").lower() == "true"
    follow_redirects = os.getenv("NEXTGEN_FOLLOW_REDIRECTS", "true").lower() == "true"
    
    return NextGenConfig(
        client_id=client_id,
        client_secret=client_secret,
        site_id=site_id,
        base_url=os.getenv("NEXTGEN_BASE_URL", NextGenConfig.base_url),
        token_url=os.getenv("NEXTGEN_TOKEN_URL", NextGenConfig.token_url),
        authorization_url=os.getenv("NEXTGEN_AUTHORIZATION_URL", NextGenConfig.authorization_url),
        grant_type=os.getenv("NEXTGEN_GRANT_TYPE", "client_credentials"),
        x_ng_session_id=os.getenv("NEXTGEN_X_NG_SESSION_ID"),
        timeout=int(os.getenv("NEXTGEN_TIMEOUT", "30")),
        max_retries=int(os.getenv("NEXTGEN_MAX_RETRIES", "3")),
        verify_ssl=verify_ssl,
        follow_redirects=follow_redirects,
        user_agent=os.getenv("NEXTGEN_USER_AGENT", NextGenConfig.user_agent),
    )


# Global configuration instance
config = None

def get_config() -> NextGenConfig:
    """Get the global configuration instance, loading it if necessary."""
    global config
    if config is None:
        config = load_config()
    return config


def set_config(new_config: NextGenConfig):
    """Set the global configuration instance."""
    global config
    config = new_config