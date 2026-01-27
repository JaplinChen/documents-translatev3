import logging
from typing import Any

from fastapi import HTTPException, Request, status
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)


class UserInfo(BaseModel):
    uid: str
    username: str
    email: str | None = None
    groups: list[str] = []
    attributes: dict[str, Any] = {}


class AuthProvider:
    """
    SSO 認證接口預留基類。
    未來接入 AD、OAuth2 或 OIDC 時，只需繼承此類並實作 authenticate 方法。
    """

    async def authenticate(self, request: Request) -> UserInfo | None:
        raise NotImplementedError("Subclasses must implement authenticate")


class MockAuthProvider(AuthProvider):
    """預設開發環境使用的 Mock 認證"""

    async def authenticate(self, request: Request) -> UserInfo | None:
        # 在開發模式下，我們暫時回傳一個預設的管理員帳號
        return UserInfo(
            uid="admin-001",
            username="LocalAdmin",
            groups=["admin", "it-manager"],
        )


class AuthManager:
    def __init__(self, provider: AuthProvider):
        self.provider = provider

    async def get_current_user(self, request: Request) -> UserInfo:
        user = await self.provider.authenticate(request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未授權的存取，請登入公司 SSO",
            )
        return user


# 全域實例，預設使用 Mock
# 未來只需根據環境變數位換 Provider 即可完成 SSO 接入
auth_manager = AuthManager(MockAuthProvider())
