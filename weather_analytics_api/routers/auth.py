from fastapi import APIRouter

from weather_analytics_api.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def get_token():
    # Simple token for testing, normally you'd validate user/password
    access_token = create_access_token(data={"sub": "testuser"})
    return {"access_token": access_token, "token_type": "bearer"}
