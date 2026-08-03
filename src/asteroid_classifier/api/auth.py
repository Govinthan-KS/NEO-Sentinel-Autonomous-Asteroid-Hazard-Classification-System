import os
import time
from typing import Dict, List
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from asteroid_classifier.core.logging import get_logger

logger = get_logger()

from dotenv import load_dotenv
load_dotenv()

# Setup Supabase JWKS client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
if not SUPABASE_URL:
    logger.warning("SUPABASE_URL is not set. JWT verification will fail.")

JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
jwks_client = jwt.PyJWKClient(JWKS_URL)

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # Supabase uses these algorithms, and requires audience and issuer validation
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "ES384", "RS256", "PS256", "HS256"],
            audience="authenticated",
            issuer=f"{SUPABASE_URL}/auth/v1"
        )
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    except jwt.ExpiredSignatureError:
        logger.warning("JWT validation failed: Expired signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# In-memory rate limiting state
# Maps user_id -> List of timestamps
RATE_LIMIT_STATE: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 10

def rate_limit_predict(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token."
        )

    now = time.time()
    
    # Prune old timestamps for all users to prevent memory accumulation
    # Creating a list of keys to safely iterate and potentially delete
    keys_to_delete = []
    for uid, timestamps in RATE_LIMIT_STATE.items():
        valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
        if not valid_timestamps:
            keys_to_delete.append(uid)
        else:
            RATE_LIMIT_STATE[uid] = valid_timestamps
            
    for uid in keys_to_delete:
        del RATE_LIMIT_STATE[uid]

    # Check limit for current user
    user_timestamps = RATE_LIMIT_STATE.get(user_id, [])
    
    if len(user_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        logger.warning(f"Rate limit exceeded for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {MAX_REQUESTS_PER_WINDOW} predictions per minute allowed."
        )

    user_timestamps.append(now)
    RATE_LIMIT_STATE[user_id] = user_timestamps
    
    return current_user

def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security_optional)) -> dict | None:
    if not credentials:
        return None
    try:
        token = credentials.credentials
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "ES384", "RS256", "PS256", "HS256"],
            audience="authenticated",
            issuer=f"{SUPABASE_URL}/auth/v1"
        )
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
    except Exception:
        return None

from fastapi import Request

CONTACT_RATE_LIMIT_STATE: Dict[str, List[float]] = {}
CONTACT_RATE_LIMIT_WINDOW = 86400  # 24 hours
CONTACT_MAX_REQUESTS = 3

def rate_limit_contact(request: Request, current_user: dict | None = Depends(get_optional_user)):
    client_id = current_user.get("user_id") if current_user else (request.client.host if request.client else "unknown")
    
    now = time.time()
    
    # Prune old timestamps
    keys_to_delete = []
    for uid, timestamps in CONTACT_RATE_LIMIT_STATE.items():
        valid_timestamps = [t for t in timestamps if now - t < CONTACT_RATE_LIMIT_WINDOW]
        if not valid_timestamps:
            keys_to_delete.append(uid)
        else:
            CONTACT_RATE_LIMIT_STATE[uid] = valid_timestamps
            
    for uid in keys_to_delete:
        del CONTACT_RATE_LIMIT_STATE[uid]

    user_timestamps = CONTACT_RATE_LIMIT_STATE.get(client_id, [])
    
    if len(user_timestamps) >= CONTACT_MAX_REQUESTS:
        logger.warning(f"Contact rate limit exceeded for client: {client_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {CONTACT_MAX_REQUESTS} contact messages per 24 hours allowed."
        )

    user_timestamps.append(now)
    CONTACT_RATE_LIMIT_STATE[client_id] = user_timestamps
    
    return current_user

