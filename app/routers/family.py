# app/routers/family.py
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models.user import User
from app.models.family import Family, FamilyMember
from app.models.invite import FamilyInvite
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.asset import Asset
from app.models.credit_source import CreditSource
from app.models.income_stream import IncomeStream
from app.models.financial_goal import FinancialGoal
from app.utils.security import get_current_active_user
from app.utils.email import send_family_invite
from app.schemas.invite import (
    FamilyInviteCreate,
    FamilyInviteResponse,
    UserPendingInvite,
)
from pydantic import BaseModel

router = APIRouter()


class FamilyCreate(BaseModel):
    name: str
    import_existing_data: bool = False
    import_from_date: str = None
    import_to_date: str = None
    import_transactions: bool = True
    import_budgets: bool = True
    import_credit_sources: bool = True
    import_assets: bool = True
    import_income_streams: bool = True
    import_financial_goals: bool = True


class FamilyResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class FamilyDetailResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime
    members: list = []
    pending_invites: list = []

    class Config:
        from_attributes = True


@router.get("/families")
async def list_user_families(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List all families the user belongs to."""
    result = await session.execute(
        select(Family)
        .join(FamilyMember)
        .where(FamilyMember.user_id == current_user.id)
        .options(selectinload(Family.members))
    )
    families = result.unique().scalars().all()
    return families


@router.post("/families")
async def create_family(
    family_data: FamilyCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new family."""
    # Create family
    new_family = Family(name=family_data.name, created_by=current_user.id)
    session.add(new_family)
    await session.flush()

    # Add creator as admin
    creator_member = FamilyMember(
        family_id=new_family.id, user_id=current_user.id, role="admin"
    )
    session.add(creator_member)

    # Import data if requested
    if family_data.import_existing_data:
        await _import_user_data(
            session,
            current_user.id,
            new_family.id,
            family_data,
        )

    # Set active family
    current_user.active_family_id = new_family.id

    await session.commit()
    await session.refresh(new_family)

    return new_family


@router.get("/families/{family_id}")
async def get_family(
    family_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get family details."""
    # Check if user is member
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this family"
        )

    result = await session.execute(
        select(Family)
        .where(Family.id == family_id)
        .options(selectinload(Family.members))
    )
    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Family not found"
        )

    return family


@router.patch("/families/{family_id}")
async def update_family(
    family_id: int,
    name: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Update family name (admin only)."""
    # Check if user is admin
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == "admin",
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update family"
        )

    result = await session.execute(select(Family).where(Family.id == family_id))
    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Family not found"
        )

    family.name = name
    await session.commit()

    return family


@router.delete("/families/{family_id}")
async def delete_family(
    family_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete family (creator only)."""
    result = await session.execute(select(Family).where(Family.id == family_id))
    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Family not found"
        )

    if family.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only creator can delete family",
        )

    await session.delete(family)
    await session.commit()

    return {"message": "Family deleted"}


# INVITE ENDPOINTS


@router.post("/families/{family_id}/members/invite")
async def send_family_invite_endpoint(
    family_id: int,
    invite_data: FamilyInviteCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Send family invite by email (admin only)."""
    # Check if user is admin
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == "admin",
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can invite members"
        )

    # Get family
    result = await session.execute(select(Family).where(Family.id == family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Family not found"
        )

    # Check if user already invited
    result = await session.execute(
        select(FamilyInvite).where(
            and_(
                FamilyInvite.family_id == family_id,
                FamilyInvite.invited_email == invite_data.invited_email,
                not FamilyInvite.accepted,
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite already sent to this email",
        )

    # Check if user already member
    result = await session.execute(
        select(FamilyMember)
        .join(User)
        .where(
            and_(
                FamilyMember.family_id == family_id,
                User.email == invite_data.invited_email,
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member",
        )

    # Generate token
    token = secrets.token_urlsafe(32)

    # Create invite
    invite = FamilyInvite(
        family_id=family_id,
        invited_email=invite_data.invited_email,
        invited_by_user_id=current_user.id,
        role=invite_data.role,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    session.add(invite)
    await session.commit()

    # Send email
    send_family_invite(
        invite_data.invited_email,
        current_user.full_name,
        family.name,
        token,
    )

    return FamilyInviteResponse.model_validate(invite)


@router.get("/families/{family_id}/invites")
async def list_family_invites(
    family_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """List pending invites for a family (admin only)."""
    # Check if user is admin
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == "admin",
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can view invites",
        )

    result = await session.execute(
        select(FamilyInvite)
        .where(
            and_(
                FamilyInvite.family_id == family_id, not FamilyInvite.accepted
            )
        )
        .order_by(FamilyInvite.created_at.desc())
    )
    invites = result.scalars().all()

    return [FamilyInviteResponse.model_validate(i) for i in invites]


@router.delete("/families/{family_id}/invites/{invite_id}")
async def cancel_invite(
    family_id: int,
    invite_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a pending invite (admin only)."""
    # Check if user is admin
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == "admin",
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can cancel invites"
        )

    result = await session.execute(
        select(FamilyInvite).where(
            and_(FamilyInvite.id == invite_id, FamilyInvite.family_id == family_id)
        )
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
        )

    await session.delete(invite)
    await session.commit()

    return {"message": "Invite cancelled"}


# PUBLIC ENDPOINT - Accept invite (no auth required for token verification)


@router.post("/invites/{token}/accept")
async def accept_family_invite(
    token: str, session: AsyncSession = Depends(get_session)
):
    """Accept a family invite (public endpoint)."""
    # Find invite by token
    result = await session.execute(
        select(FamilyInvite).where(FamilyInvite.token == token)
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite link"
        )

    if invite.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already accepted"
        )

    if datetime.utcnow() > invite.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has expired"
        )

    # Get family for response
    result = await session.execute(
        select(Family).where(Family.id == invite.family_id)
    )
    family = result.scalar_one_or_none()

    return {
        "family_id": invite.family_id,
        "family_name": family.name,
        "invited_email": invite.invited_email,
        "role": invite.role,
        "token": token,
    }


@router.post("/invites/{token}/accept/confirm")
async def confirm_accept_family_invite(
    token: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Confirm acceptance of family invite (requires auth)."""
    # Find invite
    result = await session.execute(
        select(FamilyInvite).where(FamilyInvite.token == token)
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite"
        )

    if invite.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already accepted"
        )

    if datetime.utcnow() > invite.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has expired"
        )

    # Verify email matches
    if current_user.email.lower() != invite.invited_email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email does not match invite",
        )

    # Add user to family
    family_member = FamilyMember(
        family_id=invite.family_id,
        user_id=current_user.id,
        role=invite.role,
    )
    session.add(family_member)

    # Mark invite as accepted
    invite.accepted = True
    invite.accepted_by_user_id = current_user.id
    invite.accepted_at = datetime.utcnow()

    # Set as active family
    current_user.active_family_id = invite.family_id

    await session.commit()

    # Get family info
    result = await session.execute(
        select(Family).where(Family.id == invite.family_id)
    )
    family = result.scalar_one_or_none()

    return {"message": "Invite accepted", "family_id": family.id, "family_name": family.name}


@router.get("/user/pending-invites")
async def get_user_pending_invites(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get user's pending invites."""
    result = await session.execute(
        select(FamilyInvite)
        .where(
            and_(
                FamilyInvite.invited_email == current_user.email,
                not FamilyInvite.accepted,
                FamilyInvite.expires_at > datetime.utcnow(),
            )
        )
        .order_by(FamilyInvite.created_at.desc())
    )
    invites = result.scalars().all()

    return [UserPendingInvite.model_validate(i) for i in invites]


# MEMBER MANAGEMENT


@router.patch("/families/{family_id}/members/{member_id}")
async def update_member_role(
    family_id: int,
    member_id: int,
    role: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Change member role (admin only)."""
    # Check if current user is admin
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == "admin",
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change roles"
        )

    result = await session.execute(
        select(FamilyMember).where(
            and_(FamilyMember.id == member_id, FamilyMember.family_id == family_id)
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    if role not in ["admin", "member", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role"
        )

    member.role = role
    await session.commit()

    return member


@router.delete("/families/{family_id}/members/{member_id}")
async def remove_member(
    family_id: int,
    member_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove member from family (admin only)."""
    # Check if current user is admin
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == "admin",
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can remove members",
        )

    result = await session.execute(
        select(FamilyMember).where(
            and_(FamilyMember.id == member_id, FamilyMember.family_id == family_id)
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    await session.delete(member)
    await session.commit()

    return {"message": "Member removed"}


@router.post("/families/{family_id}/set-active")
async def set_active_family(
    family_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Set active family for user."""
    # Check if user is member
    result = await session.execute(
        select(FamilyMember).where(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this family"
        )

    current_user.active_family_id = family_id
    await session.commit()

    return {"message": "Active family set", "family_id": family_id}


@router.get("/user/active-family")
async def get_active_family(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    """Get user's active family."""
    if not current_user.active_family_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active family set"
        )

    result = await session.execute(
        select(Family).where(Family.id == current_user.active_family_id)
    )
    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Active family not found"
        )

    return family


# HELPER FUNCTIONS


async def _import_user_data(
    session: AsyncSession,
    user_id: int,
    family_id: int,
    import_config: FamilyCreate,
):
    """Import user's data to a new family."""
    from_date = None
    to_date = None

    if import_config.import_from_date:
        from_date = datetime.fromisoformat(import_config.import_from_date)

    if import_config.import_to_date:
        to_date = datetime.fromisoformat(import_config.import_to_date)

    # Import transactions
    if import_config.import_transactions:
        result = await session.execute(
            select(Transaction).where(Transaction.user_id == user_id)
        )
        transactions = result.scalars().all()

        for txn in transactions:
            if from_date and txn.date < from_date:
                continue
            if to_date and txn.date > to_date:
                continue
            txn.family_id = family_id

    # Import budgets
    if import_config.import_budgets:
        result = await session.execute(
            select(Budget).where(Budget.user_id == user_id)
        )
        budgets = result.scalars().all()
        for budget in budgets:
            budget.family_id = family_id

    # Import credit sources
    if import_config.import_credit_sources:
        result = await session.execute(
            select(CreditSource).where(CreditSource.user_id == user_id)
        )
        credit_sources = result.scalars().all()
        for cs in credit_sources:
            cs.family_id = family_id

    # Import assets
    if import_config.import_assets:
        result = await session.execute(
            select(Asset).where(Asset.user_id == user_id)
        )
        assets = result.scalars().all()
        for asset in assets:
            asset.family_id = family_id

    # Import income streams
    if import_config.import_income_streams:
        result = await session.execute(
            select(IncomeStream).where(IncomeStream.user_id == user_id)
        )
        income_streams = result.scalars().all()
        for stream in income_streams:
            stream.family_id = family_id

    # Import financial goals
    if import_config.import_financial_goals:
        result = await session.execute(
            select(FinancialGoal).where(FinancialGoal.user_id == user_id)
        )
        goals = result.scalars().all()
        for goal in goals:
            goal.family_id = family_id

    await session.flush()