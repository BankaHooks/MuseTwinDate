from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Optional
from .models import User, Like, Skip, Block, Report, Chat, Payment

async def create_user(session: AsyncSession, telegram_id: int, username: str = None, **kwargs) -> User:
    user = User(telegram_id=telegram_id, username=username, **kwargs)
    session.add(user)
    await session.commit()
    return user

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def update_user(session: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    await session.commit()
    return user

async def create_like(session: AsyncSession, from_user_id: int, to_user_id: int) -> Like:
    like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
    session.add(like)
    await session.commit()
    other = await session.execute(
        select(Like).where(and_(Like.from_user_id == to_user_id, Like.to_user_id == from_user_id))
    )
    other_like = other.scalar_one_or_none()
    if other_like:
        like.is_mutual = True
        other_like.is_mutual = True
        session.add_all([like, other_like])
        await session.commit()
        chat = Chat(user1_id=min(from_user_id, to_user_id), user2_id=max(from_user_id, to_user_id))
        session.add(chat)
        await session.commit()
    return like

async def get_likes_received(session: AsyncSession, user_id: int) -> List[Like]:
    result = await session.execute(
        select(Like).where(Like.to_user_id == user_id).order_by(Like.created_at.desc())
    )
    return result.scalars().all()

async def get_like_between(session: AsyncSession, user1_id: int, user2_id: int) -> Optional[Like]:
    result = await session.execute(
        select(Like).where(
            or_(
                and_(Like.from_user_id == user1_id, Like.to_user_id == user2_id),
                and_(Like.from_user_id == user2_id, Like.to_user_id == user1_id)
            )
        )
    )
    return result.scalars().first()

async def create_skip(session: AsyncSession, user_id: int, skipped_user_id: int):
    skip = Skip(user_id=user_id, skipped_user_id=skipped_user_id)
    session.add(skip)
    await session.commit()

async def get_skipped_user_ids(session: AsyncSession, user_id: int) -> List[int]:
    result = await session.execute(select(Skip.skipped_user_id).where(Skip.user_id == user_id))
    return result.scalars().all()

async def create_block(session: AsyncSession, blocker_id: int, blocked_id: int):
    block = Block(blocker_id=blocker_id, blocked_id=blocked_id)
    session.add(block)
    await session.commit()

async def get_blocked_user_ids(session: AsyncSession, user_id: int) -> List[int]:
    result = await session.execute(select(Block.blocked_id).where(Block.blocker_id == user_id))
    return result.scalars().all()

async def get_blockers_for_user(session: AsyncSession, user_id: int) -> List[int]:
    result = await session.execute(select(Block.blocker_id).where(Block.blocked_id == user_id))
    return result.scalars().all()

async def create_report(session: AsyncSession, reporter_id: int, reported_id: int, reason: str, description: str = None):
    report = Report(reporter_id=reporter_id, reported_id=reported_id, reason=reason, description=description)
    session.add(report)
    await session.commit()
    return report

async def get_reports(session: AsyncSession, resolved: bool = False) -> List[Report]:
    result = await session.execute(select(Report).where(Report.resolved == resolved).order_by(Report.created_at.desc()))
    return result.scalars().all()

async def get_chats_for_user(session: AsyncSession, user_id: int) -> List[Chat]:
    result = await session.execute(
        select(Chat).where(or_(Chat.user1_id == user_id, Chat.user2_id == user_id))
    )
    return result.scalars().all()

async def set_premium(session: AsyncSession, user_id: int, duration_months: int):
    user = await get_user_by_id(session, user_id)
    if user:
        user.is_premium = True
        user.premium_expiry = datetime.utcnow() + timedelta(days=30*duration_months)
        await session.commit()
        return user
    return None

async def record_payment(session: AsyncSession, user_id: int, charge_id: str, amount: int, duration_months: int, expiry: datetime):
    payment = Payment(user_id=user_id, telegram_payment_charge_id=charge_id,
                      amount=amount, duration_months=duration_months, expiry_date=expiry)
    session.add(payment)
    await session.commit()
    return payment

async def get_candidate_pool(session: AsyncSession, current_user_id: int, limit: int = 300) -> List[User]:
    current_user = await get_user_by_id(session, current_user_id)
    skipped = await get_skipped_user_ids(session, current_user_id)
    blocked_by_me = await get_blocked_user_ids(session, current_user_id)
    blocked_me = await get_blockers_for_user(session, current_user_id)
    likes_from_me = await session.execute(
        select(Like.to_user_id).where(Like.from_user_id == current_user_id)
    )
    liked_ids = likes_from_me.scalars().all()
    exclude = set([current_user_id] + skipped + blocked_by_me + blocked_me + liked_ids)

    stmt = select(User).where(
        and_(User.id.notin_(exclude), User.is_banned == False)
    )
    if current_user.search_city_only and current_user.city:
        stmt = stmt.where(User.city == current_user.city)
    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

async def can_like(session: AsyncSession, user: User) -> bool:
    if user.is_premium:
        return True
    today = datetime.utcnow().date()
    if user.last_like_date is None or user.last_like_date.date() < today:
        user.likes_today = 0
        user.last_like_date = datetime.utcnow()
        await session.commit()
    return user.likes_today < 30

async def increment_likes(session: AsyncSession, user: User):
    user.likes_today += 1
    if user.last_like_date is None or user.last_like_date.date() < datetime.utcnow().date():
        user.likes_today = 1
        user.last_like_date = datetime.utcnow()
    await session.commit()

from sqlalchemy import func

async def get_likes_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Like.id)).where(Like.to_user_id == user_id))
    return result.scalar() or 0

async def update_like_notification_count(session: AsyncSession, user: User, count: int):
    user.last_like_notification_count = count
    await session.commit()

async def update_last_activity(session: AsyncSession, user: User):
    user.last_activity = datetime.utcnow()
    await session.commit()

async def create_user(session: AsyncSession, telegram_id: int, username: str = None, **kwargs) -> User:
    user = User(telegram_id=telegram_id, username=username, **kwargs)
    session.add(user)
    await session.commit()
    return user

from sqlalchemy import func

async def get_likes_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Like.id)).where(Like.to_user_id == user_id))
    return result.scalar() or 0

async def update_like_notification_count(session: AsyncSession, user: User, count: int):
    user.last_like_notification_count = count
    await session.commit()

async def update_last_activity(session: AsyncSession, user: User):
    user.last_activity = datetime.utcnow()
    await session.commit()