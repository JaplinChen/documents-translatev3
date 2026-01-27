from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, Request

from backend.tools.auth_helper import AuthManager, MockAuthProvider, UserInfo

@pytest.mark.asyncio
async def test_mock_auth_provider():
    provider = MockAuthProvider()
    request = MagicMock(spec=Request)
    user = await provider.authenticate(request)
    assert user.username == "LocalAdmin"
    assert "admin" in user.groups


@pytest.mark.asyncio
async def test_auth_manager_success():
    mock_provider = AsyncMock()
    mock_provider.authenticate.return_value = UserInfo(
        uid="u1",
        username="testuser",
    )

    manager = AuthManager(mock_provider)
    request = MagicMock(spec=Request)
    user = await manager.get_current_user(request)
    assert user.uid == "u1"


@pytest.mark.asyncio
async def test_auth_manager_unauthorized():
    mock_provider = AsyncMock()
    mock_provider.authenticate.return_value = None

    manager = AuthManager(mock_provider)
    request = MagicMock(spec=Request)
    with pytest.raises(HTTPException) as excinfo:
        await manager.get_current_user(request)
    assert excinfo.value.status_code == 401
