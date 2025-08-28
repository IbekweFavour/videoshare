from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, String, Integer, DateTime, ForeignKey, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship

# ====== Config ======
SECRET_KEY = "change-me-in-prod-please"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ====== DB setup ======
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Video(Base):
    __tablename__ = "videos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String)
    genre: Mapped[str] = mapped_column(String)
    publisher: Mapped[str] = mapped_column(String)
    avg_rating: Mapped[int] = mapped_column(Integer, default=0)

engine = create_engine("sqlite:///videoshare.db", echo=False)
Base.metadata.create_all(engine)

# seed some demo videos if table empty
with Session(engine) as s:
    if s.scalar(select(func.count(Video.id))) == 0:
        s.add_all([
            Video(title="Neon Nights", genre="Sci‑Fi", publisher="Studio K", avg_rating=5),
            Video(title="Cloud Kitchen", genre="Drama", publisher="Urban Films", avg_rating=4),
            Video(title="Salsa 101", genre="Education", publisher="DanceCo", avg_rating=5),
            Video(title="Trail Run POV", genre="Sports", publisher="GoWild", avg_rating=3),
        ])
        s.commit()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ====== Schemas ======
class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    class Config:
        from_attributes = True

class RegisterIn(BaseModel):
    email: EmailStr
    name: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class VideoOut(BaseModel):
    id: int
    title: str
    genre: str
    publisher: str
    avg_rating: int

# ====== App ======
app = FastAPI(title="VideoShare API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to read current user from Authorization: Bearer token
def get_current_user(token: str | None = None):
    # We do a light dependency to be explicit in endpoints when needed.
    return None

# -------- Auth Endpoints --------
@app.post("/auth/register", response_model=UserOut)
def register(payload: RegisterIn):
    with Session(engine) as s:
        exists = s.scalar(select(User).where(User.email == payload.email))
        if exists:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(email=str(payload.email).lower(), name=payload.name, password_hash=get_password_hash(payload.password))
        s.add(user)
        s.commit()
        s.refresh(user)
        return user

@app.post("/auth/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm expects fields: username, password
    with Session(engine) as s:
        user = s.scalar(select(User).where(User.email == form.username.lower()))
        if not user or not verify_password(form.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        token = create_access_token({"sub": str(user.id), "email": user.email})
        return TokenOut(access_token=token, user=user)  # type: ignore[arg-type]

# -------- Video Endpoints --------
@app.get("/videos/latest", response_model=List[VideoOut])
def latest():
    with Session(engine) as s:
        items = s.scalars(select(Video).order_by(Video.id.desc())).all()
        return [VideoOut.model_validate(v, from_attributes=True) for v in items]

@app.get("/videos", response_model=List[VideoOut])
def search(q: Optional[str] = None):
    with Session(engine) as s:
        stmt = select(Video)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(func.lower(Video.title).like(like) | func.lower(Video.genre).like(like))
        items = s.scalars(stmt.order_by(Video.id.desc())).all()
        return [VideoOut.model_validate(v, from_attributes=True) for v in items]
