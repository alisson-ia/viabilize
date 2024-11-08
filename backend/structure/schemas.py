from typing import Optional
from pydantic import BaseModel, EmailStr



class UsuarioSchemaBase(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    totp_secret: Optional[str] = None
    is_admin: Optional[bool] = False
    is_active: Optional[bool] = False
    is_verified: Optional[bool] = False
    plan_id: Optional[int] = None
    reset_token: Optional[str] = None
    reset_token_expiration: Optional[str] = None
    subscription_id: Optional[str] = None
    subscription_status: Optional[str] = "inactive"

    class Config:
        from_attributes = True


class UsuarioSchemaCreate(UsuarioSchemaBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str


class ResendOTPSchema(BaseModel):
    email: EmailStr
