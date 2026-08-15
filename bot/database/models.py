from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    gender = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    city = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    favorite_band = Column(String(255), nullable=True)
    favorite_songs = Column(Text, nullable=True)
    preferred_gender = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    photo_file_id = Column(String(255), nullable=True)
    photo_local_path = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)
    premium_expiry = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_security_notice = Column(DateTime, nullable=True)
    likes_today = Column(Integer, default=0)
    last_like_date = Column(DateTime, nullable=True)
    search_city_only = Column(Boolean, default=False)

    sent_likes = relationship("Like", foreign_keys="Like.from_user_id", back_populates="from_user")
    received_likes = relationship("Like", foreign_keys="Like.to_user_id", back_populates="to_user")
    skips = relationship("Skip", foreign_keys="Skip.user_id", back_populates="user")
    blocks_given = relationship("Block", foreign_keys="Block.blocker_id", back_populates="blocker")
    blocks_received = relationship("Block", foreign_keys="Block.blocked_id", back_populates="blocked")
    reports_sent = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_mutual = Column(Boolean, default=False)
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_likes")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_likes")

class Skip(Base):
    __tablename__ = "skips"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skipped_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="skips")

class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocks_given")
    blocked = relationship("User", foreign_keys=[blocked_id], back_populates="blocks_received")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_sent")
    reported = relationship("User", foreign_keys=[reported_id])

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    telegram_payment_charge_id = Column(String(255), unique=True)
    amount = Column(Integer)
    duration_months = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=False)