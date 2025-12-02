from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, UserRole, MembershipLevel
from ..schemas import UserOut, UserUpdateAdmin
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.get("/users", response_model=List[UserOut])
def list_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_admin), 
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_update: UserUpdateAdmin,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.role is not None:
        user.role = user_update.role
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
        
    if user_update.membership_level_code is not None:
        membership = db.query(MembershipLevel).filter(MembershipLevel.level_code == user_update.membership_level_code).first()
        if not membership:
            raise HTTPException(status_code=400, detail="Invalid membership level code")
        user.membership_id = membership.id
        
    db.commit()
    db.refresh(user)
    return user
