from fastapi import (
    FastAPI,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
from models import (
    User as UserModel,
    Room as RoomModel,
    Message as MessageModel,
    UserRole,
)
from schemas import (
    UserCreate,
    User as UserSchema,
    Token,
    RoomBase,
    Room as RoomSchema,
    MessageCreate,
    Message as MessageSchema,
)
from auth import (
    get_current_user,
    get_current_active_user,
    create_access_token,
    authenticate_user,
    get_password_hash,
)
from database import get_db, Base, engine
from dependencies import role_required
from datetime import datetime, timedelta
from config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
import json
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)

    async def broadcast(self, message: str, room_id: int):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)


manager = ConnectionManager()


@app.post("/admin-signup", response_model=UserSchema)
def admin_signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=UserRole.ADMIN,  # Force admin role
    )
    db.add(db_user)
    db.commit()
    return db_user


@app.post("/signup", response_model=UserSchema)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=UserRole.USER,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/rooms/", response_model=RoomSchema)
def create_room(
    room: RoomBase,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_room = RoomModel(**room.dict(), created_by=current_user.id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@app.get("/rooms/", response_model=List[RoomSchema])
def read_rooms(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    rooms = db.query(RoomModel).offset(skip).limit(limit).all()
    return rooms


@app.put("/rooms/{room_id}", response_model=RoomSchema)
def update_room(
    room_id: int,
    room: RoomBase,
    current_user: UserModel = Depends(role_required(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    db_room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Update room properties
    db_room.name = room.name
    db_room.description = room.description

    db.commit()
    db.refresh(db_room)
    return db_room


@app.delete("/rooms/{room_id}")
def delete_room(
    room_id: int,
    current_user: UserModel = Depends(role_required(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    db_room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    db.query(MessageModel).filter(MessageModel.room_id == room_id).delete()

    db.delete(db_room)
    db.commit()

    return {"message": "Room deleted successfully"}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_id: int, token: str, db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user = db.query(UserModel).filter(UserModel.username == username).first()
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        room = db.query(RoomModel).filter(RoomModel.id == room_id).first()
        if not room:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await manager.connect(websocket, room_id)

        messages = (
            db.query(MessageModel)
            .filter(MessageModel.room_id == room_id)
            .order_by(MessageModel.sent_at.desc())
            .limit(10)
            .all()
        )
        for message in reversed(messages):
            await websocket.send_json(
                {
                    "content": message.content,
                    "sender": message.sender.username,
                    "sent_at": message.sent_at.isoformat(),
                }
            )

        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            db_message = MessageModel(
                content=message_data["content"], room_id=room_id, sender_id=user.id
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)

            await manager.broadcast(
                json.dumps(
                    {
                        "content": db_message.content,
                        "sender": user.username,
                        "sent_at": db_message.sent_at.isoformat(),
                    }
                ),
                room_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(websocket, room_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@app.get("/admin/users", response_model=List[UserSchema])
def get_all_users(
    current_user: UserModel = Depends(role_required(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    return db.query(UserModel).all()


@app.post("/admin/promote/{user_id}")
def promote_user(
    user_id: int,
    current_user: UserModel = Depends(role_required(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.role = UserRole.ADMIN
    db.commit()
    db.refresh(db_user)
    return {"message": "User promoted to admin"}
