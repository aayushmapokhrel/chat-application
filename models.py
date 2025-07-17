from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from database import Base


class UserRole(str, PyEnum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="sender")
    rooms = relationship("Room", secondary="user_rooms", back_populates="members")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    members = relationship("User", secondary="user_rooms", back_populates="rooms")
    messages = relationship("Message", back_populates="room")


class UserRoom(Base):
    __tablename__ = "user_rooms"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(500))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    sent_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("Room", back_populates="messages")
    sender = relationship("User", back_populates="messages")
