from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None


class Room(RoomBase):
    id: int
    created_at: datetime
    created_by: int

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    room_id: int


class Message(MessageBase):
    id: int
    room_id: int
    sender_id: int
    sent_at: datetime

    class Config:
        from_attributes = True
