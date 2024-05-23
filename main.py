from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import requests

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


engine = create_engine(SQLALCHEMY_DATABASE_URL)


Base = declarative_base()


templates = Jinja2Templates(directory="templates")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


Base.metadata.create_all(bind=engine)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


app = FastAPI()


class UserRegistration(BaseModel):
    username: str
    email: EmailStr
    password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


@app.post("/register/")
async def register(user_data: UserRegistration):
    db = SessionLocal()
    user = db.query(User).filter(User.username == user_data.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return {"message": "User registered successfully", "user_data": user_data}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

