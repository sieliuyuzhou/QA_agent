from fastapi import Depends, HTTPException

from domain.customer_service.context import CurrentUser
from .dependencies import get_current_user


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
