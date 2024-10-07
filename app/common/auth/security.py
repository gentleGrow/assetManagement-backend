from typing import Any

from fastapi import HTTPException, Security, status
from fastapi.security.oauth2 import OAuth2PasswordBearer

from app.common.util.logging import logging
from app.module.auth.jwt import JWTBuilder

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_jwt_token(encode_token: str = Security(oauth2_scheme)) -> dict[str, Any]:
    try:
        token = JWTBuilder.decode_token(encode_token)
    except Exception as e:
        logging.error(f"Token decoding error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = token.get("user")
    if user_id is None:
        logging.error("사용자 id를 찾지 못 하였습니다.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자 id를 찾지 못 하였습니다.")
    return token
