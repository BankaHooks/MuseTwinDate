from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Optional
import secrets
from .models import User, Like, Skip, Block, Report, Chat, Payment, BlindDate

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

async def create_like(session: AsyncSession, from_user_id: int, to_user_id: int) -> Optional[Like]:
    existing = await session.execute(
        select(Like).where(
            and_(Like.from_user_id == from_user_id, Like.to_user_id == to_user_id)
        )
    )
    existing = existing.scalars().first()
    if existing:
        return existing
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
        select(Like).where(and_(Like.to_user_id == user_id, Like.is_mutual == False)).order_by(Like.created_at.desc())
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
    skip = Skip(user_id=user_id, skipped_user_id=skipped_user_id, created_at=datetime.utcnow())
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

async def delete_old_skips(session: AsyncSession, user_id: int, days: int = 1):
    cutoff = datetime.utcnow() - timedelta(days=days)
    await session.execute(delete(Skip).where(and_(Skip.user_id == user_id, Skip.created_at < cutoff)))
    await session.commit()

async def get_candidate_pool(session: AsyncSession, current_user_id: int, limit: int = 300) -> List[User]:
    current_user = await get_user_by_id(session, current_user_id)
    await delete_old_skips(session, current_user_id, days=1)
    skipped = await get_skipped_user_ids(session, current_user_id)
    blocked_by_me = await get_blocked_user_ids(session, current_user_id)
    blocked_me = await get_blockers_for_user(session, current_user_id)
    likes_from_me = await session.execute(
        select(Like.to_user_id).where(Like.from_user_id == current_user_id)
    )
    liked_ids = likes_from_me.scalars().all()
    exclude = set([current_user_id] + skipped + blocked_by_me + blocked_me + liked_ids)
    stmt = select(User).where(
        and_(
            User.id.notin_(exclude),
            User.is_banned == False,
            User.is_hidden == False
        )
    )
    if current_user.search_city_only and current_user.city:
        stmt = stmt.where(User.city == current_user.city)
    if current_user.preferred_gender == "Мужской":
        stmt = stmt.where(User.gender == "Мужской")
    elif current_user.preferred_gender == "Женский":
        stmt = stmt.where(User.gender == "Женский")
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

async def get_likes_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Like.id)).where(Like.to_user_id == user_id))
    return result.scalar() or 0

async def get_likes_given_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Like.id)).where(Like.from_user_id == user_id))
    return result.scalar() or 0

async def get_mutual_likes_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Like.id)).where(and_(Like.from_user_id == user_id, Like.is_mutual == True)))
    return result.scalar() or 0

async def update_like_notification_count(session: AsyncSession, user: User, count: int):
    user.last_like_notification_count = count
    await session.commit()

async def update_last_activity(session: AsyncSession, user: User):
    user.last_activity = datetime.utcnow()
    await session.commit()

async def get_random_bot(session: AsyncSession, exclude_user_ids: list = None) -> Optional[User]:
    stmt = select(User).where(
        User.telegram_id < 0,
        User.is_banned == False,
        User.is_hidden == False
    )
    if exclude_user_ids:
        stmt = stmt.where(User.id.notin_(exclude_user_ids))
    stmt = stmt.order_by(func.random()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_random_real_user(session: AsyncSession) -> Optional[User]:
    stmt = select(User).where(
        User.telegram_id > 0,
        User.is_banned == False
    )
    stmt = stmt.order_by(func.random()).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def create_blind_date(session: AsyncSession, user1_id: int, user2_id: int, song: str, artist: str) -> BlindDate:
    blind_date = BlindDate(
        user1_id=user1_id,
        user2_id=user2_id,
        song=song,
        artist=artist,
        user1_listened=False,
        user2_listened=False
    )
    session.add(blind_date)
    await session.commit()
    await session.refresh(blind_date)
    return blind_date

async def get_blind_date_by_id(session: AsyncSession, blind_date_id: int) -> Optional[BlindDate]:
    result = await session.execute(select(BlindDate).where(BlindDate.id == blind_date_id))
    return result.scalar_one_or_none()

async def mark_blind_date_listened(session: AsyncSession, blind_date_id: int, user_id: int) -> bool:
    blind_date = await get_blind_date_by_id(session, blind_date_id)
    if not blind_date:
        return False
    if blind_date.user1_id == user_id:
        blind_date.user1_listened = True
    elif blind_date.user2_id == user_id:
        blind_date.user2_listened = True
    else:
        return False
    await session.commit()
    return blind_date.user1_listened and blind_date.user2_listened

async def get_active_blind_date(session: AsyncSession, user_id: int) -> Optional[BlindDate]:
    result = await session.execute(
        select(BlindDate).where(
            or_(
                and_(BlindDate.user1_id == user_id, BlindDate.user1_listened == False),
                and_(BlindDate.user2_id == user_id, BlindDate.user2_listened == False)
            )
        ).order_by(BlindDate.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()

async def generate_referral_code(session: AsyncSession, telegram_id: int) -> str:
    for _ in range(5):
        code = f"ref_{secrets.token_urlsafe(6)}"
        existing = await get_user_by_referral_code(session, code)
        if not existing:
            return code
    return f"ref_{secrets.token_urlsafe(6)}{telegram_id}"

async def get_user_by_referral_code(session: AsyncSession, code: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.referral_code == code))
    return result.scalar_one_or_none()

async def add_referral(session: AsyncSession, referrer_id: int, new_user_id: int):
    referrer = await get_user_by_id(session, referrer_id)
    if not referrer:
        return
    referrer.referral_count += 1
    referrer.referral_discount = min(referrer.referral_count * 10, 90)
    await session.commit()

async def apply_referral_discount(session: AsyncSession, user_id: int, base_price: int) -> int:
    user = await get_user_by_id(session, user_id)
    if not user:
        return base_price
    discount = user.referral_discount or 0
    if discount > 90:
        discount = 90
    final_price = int(base_price * (1 - discount / 100))
    return final_price

async def update_referral_reminder(session: AsyncSession, user: User):
    user.last_referral_reminder = datetime.utcnow()
    await session.commit()

from utils.helpers import parse_comma_separated

from utils.helpers import parse_comma_separated

async def get_users_by_game(session: AsyncSession, game: str, exclude_user_id: int, limit: int = 10) -> List[User]:
    from utils.helpers import parse_comma_separated
    game_norm = game.lower().strip()
    stmt = select(User).where(
        User.id != exclude_user_id,
        User.is_banned == False,
        User.is_hidden == False,
        User.favorite_games.isnot(None),
        User.favorite_games != ""
    ).limit(limit * 3)
    result = await session.execute(stmt)
    users = result.scalars().all()
    filtered = []
    for u in users:
        if u.favorite_games:
            games_set = parse_comma_separated(u.favorite_games)
            if game_norm in games_set:
                filtered.append(u)
                if len(filtered) >= limit:
                    break
    return filtered