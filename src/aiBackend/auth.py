"""
JWT authentication utilities for AI Backend service.
"""
import logging
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
import os
from config import settings

logger = logging.getLogger(__name__)

def load_public_key() -> str:
    """Load the public key for JWT verification."""
    try:
        with open(settings.pub_key_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Public key file not found at {settings.pub_key_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading public key: {e}")
        raise

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        public_key = load_public_key()
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            options={"verify_exp": True}
        )
        return payload
    except ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except JWTClaimsError as e:
        logger.warning(f"JWT claims error: {e}")
        return None
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying JWT: {e}")
        return None

def get_username_from_token(token: str) -> Optional[str]:
    """
    Extract username from JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Username if token is valid, None otherwise
    """
    payload = verify_jwt_token(token)
    if payload and 'username' in payload:
        return payload['username']
    return None

def is_token_valid(token: str) -> bool:
    """
    Check if JWT token is valid.
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is valid, False otherwise
    """
    return verify_jwt_token(token) is not None
