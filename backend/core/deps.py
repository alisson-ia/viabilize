from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from core.database import Session
from core.auth import oauth2_schema
from core.configs import settings
from structure.models import UserModel


# Dicionário para armazenar usuários em cache
user_cache = {}


class TokenData(BaseModel):
    username: Optional[str] = None


async def get_session() -> AsyncGenerator:
    session: AsyncSession = Session()
    try:
        yield session
    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    finally:
        await session.close()


async def get_current_user(db: AsyncSession = Depends(get_session), token: str = Depends(oauth2_schema)) -> UserModel:
    credential_exception: HTTPException = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Não foi possível autenticar a credencial', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM], options={'verify_aud': False})       
        username: str = payload.get('sub')
        if username is None:
            raise credential_exception       
        token_data: TokenData = TokenData(username=username)
    except JWTError:
        raise credential_exception

    # Verifica se o usuário está em cache
    if username in user_cache:
        return user_cache[username]

    async with db as session:
        query = select(UserModel).filter(UserModel.id == int(token_data.username))
        result = await session.execute(query)
        user: UserModel = result.scalars().unique().one_or_none()
        if user is None:
            raise credential_exception
        
        # Armazena o usuário em cache
        user_cache[username] = user
        return user
