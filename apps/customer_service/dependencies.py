from typing import Optional

from fastapi import Header, HTTPException, Request

from domain.customer_service.context import CurrentUser


async def get_current_user(
    request: Request,
    x_qa_user_id: Optional[str] = Header(default=None, alias="X-QA-User-Id"),
) -> CurrentUser:
    if not x_qa_user_id:
        raise HTTPException(status_code=401, detail="缺少内部试用用户标识")

    user = request.app.state.customer_repository.find_active(x_qa_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="内部试用用户不可用")

    return user
