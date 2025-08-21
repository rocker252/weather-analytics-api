import pytest
from httpx import ASGITransport, AsyncClient

from weather_analytics_api.api import app
from weather_analytics_api.routers.auth import create_access_token


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def access_token():
    # Create a test JWT token
    return create_access_token(data={"sub": "testuser"})


@pytest.fixture
def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}
