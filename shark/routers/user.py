from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, MembershipLevel
from ..schemas import UserOut, MembershipLevelOut, PurchaseMembership
from .auth import get_current_user, get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/memberships", response_model=List[MembershipLevelOut])
def list_memberships(db: Session = Depends(get_db)):
    return db.query(MembershipLevel).all()

@router.post("/purchase_membership", response_model=UserOut)
def purchase_membership(purchase: PurchaseMembership, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    membership = db.query(MembershipLevel).filter(MembershipLevel.level_code == purchase.membership_level_code).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership level not found")
    
    # Here we would integrate with Payment Gateway.
    # For now, we assume success.
    
    # Calculate new expiration date (default +30 days)
    now = datetime.utcnow()
    if current_user.membership_expire_at and current_user.membership_expire_at > now:
        # Extend existing valid membership
        current_user.membership_expire_at += timedelta(days=30)
    else:
        # Start new membership period
        current_user.membership_expire_at = now + timedelta(days=30)

    current_user.membership_id = membership.id
    db.commit()
    db.refresh(current_user)
    return current_user
