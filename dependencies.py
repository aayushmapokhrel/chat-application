from fastapi import Depends, HTTPException, status
from models import UserRole
from auth import get_current_active_user
from models import User


def role_required(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource",
            )
        return current_user

    return role_checker
