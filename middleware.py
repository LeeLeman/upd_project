from fastapi import Request
from jose import JWTError, jwt

from config import ALGORITHM, SECRET_KEY


async def add_user_to_request(request: Request, call_next):
    token = request.cookies.get("user")
    request.state.user = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = {
                "email": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "role": payload.get("role"),
            }
        except JWTError:
            pass

    response = await call_next(request)
    return response
