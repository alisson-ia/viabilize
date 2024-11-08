import random
from typing import List
from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from structure.models import UserModel
from structure.schemas import UsuarioSchemaBase, UsuarioSchemaCreate, OTPVerify, UserLogin, ResendOTPSchema, PilotSchemaCreate
from core.deps import get_session, get_current_user, user_cache
from core.security import get_password_hash
from core.auth import autenticar, criar_token_acesso, send_verification_email, send_welcome_email
from core.logging import log_user_activity



router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")


@router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(user: UsuarioSchemaCreate, db: AsyncSession = Depends(get_session)):
    
    totp_secret = str(random.randint(100000, 999999)) 
   
    new_user = UserModel(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        totp_secret=totp_secret
    )

    async with db as session:
        try:
            session.add(new_user)
            await session.commit()

            # Envia o código OTP por email
            send_verification_email(user.email, totp_secret)

            return {"message": "Usuário cadastrado com sucesso! Um código de verificação foi enviado para seu email."}

        except IntegrityError as e:
            await session.rollback()
            if 'email' in str(e.orig):
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='E-mail já cadastrado.')
            else:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='Erro ao cadastrar usuário')


@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(otp_data: ResendOTPSchema, db: AsyncSession = Depends(get_session)):
    email = otp_data.email
    async with db as session:
        user = await session.execute(select(UserModel).filter(UserModel.email == email))
        user = user.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        if user.is_verified:
            raise HTTPException(status_code=400, detail="Este usuário já foi verificado.")

        new_otp = str(random.randint(100000, 999999))

        user.totp_secret = new_otp
        await session.commit()

        send_verification_email(user.email, new_otp)

        return {"message": "Novo código enviado com sucesso. Verifique seu e-mail."}


@router.post("/verify-otp", status_code=status.HTTP_201_CREATED)
async def verify_otp(otp: OTPVerify, db: AsyncSession = Depends(get_session)):
    async with db as session: 
        user = await session.execute(select(UserModel).filter(UserModel.email == otp.email))
        user = user.scalars().first()  

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        if user.totp_secret != otp.otp_code:
            raise HTTPException(status_code=400, detail="Código inválido.")

        # Atualiza o status do usuário para verificado
        user.is_verified = True
        user.is_active = True
        await session.commit() 
    
    send_welcome_email(user.email)
    return {"message": "Código OTP verificado com sucesso! Seu cadastro está completo."}


@router.post('/login')
async def login(credentials: UserLogin, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_session)):
    user = await autenticar(email=credentials.email, password=credentials.password, db=db)
    
    if user == "user_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Usuário inexistente. Verifique o email fornecido.')
    
    if user == "incorrect_password":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Senha incorreta. Por favor, tente novamente.')

    if user == "email_not_verified":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Por favor, verifique seu email antes de fazer login.')
    
    # Adiciona um registro na tabela de logs em background
    background_tasks.add_task(log_user_activity, user.id, "login", db)

    return JSONResponse(content={'access_token': criar_token_acesso(sub=user.id), 'token_type': 'bearer'}, status_code=status.HTTP_200_OK)


@router.get('/logged', response_model=UsuarioSchemaBase)
def get_logged(user: UserModel = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    
    return user


@router.get('/all', response_model=List[UsuarioSchemaBase])
async def get_users(db: AsyncSession = Depends(get_session), user_logged: UserModel = Depends(get_current_user)):
    async with db as session:
        query = select(UserModel)
        result = await session.execute(query)
        users: List[UsuarioSchemaBase] = result.scalars().unique().all()

        return users
    

@router.get('/user', response_model=List[UsuarioSchemaBase], status_code=status.HTTP_200_OK)
async def get_user(db: AsyncSession = Depends(get_session), user_logged: UserModel = Depends(get_current_user)):
    async with db as session:
        query = select(UserModel).filter(UserModel.id == user_logged.id)
        result = await session.execute(query)
        user: List[UsuarioSchemaBase] = result.scalars().unique().all()

        if user:
            return user
        else:
            raise HTTPException(detail='Usuário não encontrado.', status_code=status.HTTP_404_NOT_FOUND)
        

@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(user_logged: UserModel = Depends(get_current_user)):
    # Limpa o cache do usuário
    if user_logged.username in user_cache:
        del user_cache[user_logged.username]
    return {"message": "Logout realizado com sucesso."}
