from backend.core.configs import settings
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime



class UserModel(settings.DBBaseModel):
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    totp_secret = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    logs = relationship("LogModel", back_populates="user")


class LogModel(settings.DBBaseModel):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity = Column(String, nullable=False)

    user = relationship("UserModel", back_populates="logs")

