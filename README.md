FastAPI Chat Application

A real-time chat application built with FastAPI that supports JWT authentication, WebSocket messaging, PostgreSQL persistence, and role-based access control.
🚀 Features

    ✅ JWT Authentication: Secure login and signup with password hashing
    ✅ Role-Based Access Control (RBAC): Restrict access to endpoints based on user roles (admin/user)
    ✅ WebSocket Chat: Real-time chat support via WebSockets
    ✅ Persistent Message Storage: Messages are stored in PostgreSQL and fetched using pagination
    ✅ Room-based Communication: Chatrooms with isolated conversations

🧱 Tech Stack
Component 	Technology
Backend 	FastAPI, Python 3.10+
Database 	PostgreSQL
ORM 	SQLAlchemy (or SQLModel)
Authentication 	JWT (via python-jose), OAuth2
WebSocket 	FastAPI WebSocket
Password Hashing 	passlib
⚙️ Setup Instructions
✅ Prerequisites

    Python 3.10+
    PostgreSQL 12

📥 Installation

    Clone the repository:

git clone https://github.com/aayushmapokhrel/chat-application.git
cd chat-application

    Set up virtual environment:

python -m venv venv
# Activate environment
source venv/bin/activate        # For Linux/macOS
venv\Scripts\activate         # For Windows

    Install dependencies:

pip install -r requirements.txt

    Configure environment:

cp  .env
# Edit .env
DATABASE_URL=postgresql://user:password@localhost:5432/chat_app
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

🗃️ Database Setup

    Create PostgreSQL Database:

psql -U postgres -c "CREATE DATABASE chatdb;"

    Run Migrations / Create Tables:

from database import Base, engine
Base.metadata.create_all(bind=engine)

▶️ Running the Application

uvicorn main:app --reload

Open interactive docs at: http://localhost:8000/docs
🔐 API Endpoints
Method 	Endpoint 	Description
POST 	/signup 	Register new user
POST  /admin-signup Register Admin
POST 	/token 	Login and get JWT token
GET 	/rooms/ 	Get paginated chat history
POST  /rooms/ Create room
PUT   /rooms/{room_id} Update room 
DELETE  /rooms/{room_id} Delete Room
WS 	/ws/{room_id} 	WebSocket for real-time chat
GET  /admin/users   user list
POST /admin/promote/{user_id} promote user to admin
📦 Database Models

    User Role: ADMIN, USER
    User: id, username, email, hashed_password, role, created_at, messages, rooms
    Room: id, name, description, created_at, created_by, members, messages
    UserRoom: user_id, room_id, joined_at
    Message: id, content,room_id, sender_id, sent_at, room, sender

🧪 Testing with Postman

    Import the Postman Collection
    Set Environment Variable:
        base_url = http://localhost:8000

🧑‍💻 Author

Aayushma Pokhrel
GitHub Profile
