from pytz import timezone
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from models import all_models
from core.configs import settings
from core.security import verify_password
from pydantic import EmailStr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
import smtplib



oauth2_schema = OAuth2PasswordBearer(tokenUrl='users/login')


async def autenticar(email: EmailStr, password: str, db: AsyncSession) -> Optional[UserModel]:
    async with db as session:
        query = select(UserModel).filter(UserModel.email == email)
        result = await session.execute(query)
        user: UserModel = result.scalars().unique().one_or_none()

        if not user:
            return "user_not_found"
        
        if not verify_password(password, user.hashed_password):
            return "incorrect_password"
        
        if not user.is_verified:
            return "email_not_verified"
        
        return user
    

def _criar_token(tipo_token: str, tempo_vida: timedelta, sub: str) -> str:
    payload = {}
    sp = timezone('America/Sao_Paulo')
    expira = datetime.now(tz=sp) + tempo_vida

    payload['type'] = tipo_token
    payload['exp'] = expira
    payload['iat'] = datetime.now(tz=sp)
    payload['sub'] = str(sub)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)


def criar_token_acesso(sub: str) -> str:
    return _criar_token(
        tipo_token='access_token',
        tempo_vida=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        sub=sub
    )

def send_verification_email(email, code):
    subject = "Código de Verificação"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
            <h2 style="color: #333;">Olá!</h2>
            <p style="font-size: 24px;">Nós recebemos uma solicitação para um código de validação para a sua conta na vIAbilize.</p>
            <br>
            <p style="font-size: 24px;">Código de ativação: <span style="font-size: 36px;"><b>{code}</b></span></p>
            <ul>
                <li style="font-size: 24px;">Este código é válido por 30 minutos, além de ser pessoal, intransferível e não deve ser compartilhado com terceiros.</li>
                <li style="font-size: 24px;">Se você não solicitou este código, pode ignorar com segurança este e-mail.</li>
                <li style="font-size: 24px;">Outra pessoa pode ter digitado seu endereço de e-mail por engano.</li>
            </ul>
            <br>
            <br>
            <p style="font-size: 20px;">Obrigado,</p>
            <p style="font-size: 20px;">Equipe vIAbilize</p>
        </body>
    </html>
    """

    sender_email = config("SENDER_EMAIL")
    sender_password = config("SENDER_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = email
    text = "Para mais informações, verifique seu email."
    html = body

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())


def send_welcome_email(email):
    subject = "Bem-vindo à vIAbilize!"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
            <h2 style="color: #333;">Bem-vindo à vIAbilize!</h2>
            <p style="font-size: 24px;">Olá,</p>
            <p style="font-size: 24px;">É com grande satisfação que damos as boas-vindas à plataforma vIAbilize! Estamos empolgados por você ter se juntado a nós.</p>
            <br>
            <p style="font-size: 24px;">A vIAbilize é uma plataforma inovadora de visualização e compartilhamento da realidade capturada, projetada para revolucionar a forma como você interage com seus projetos e clientes. Aqui está um breve resumo do que você pode esperar:</p>
            <ul>
                <li style="font-size: 24px;">Visualização instantânea de fotos 360° em tours virtuais</li>
                <li style="font-size: 24px;">Filmagens e modelos 3D em nuvem de pontos e objeto</li>
                <li style="font-size: 24px;">Ferramentas ágeis para gerar anotações e compartilhar relatórios</li>
                <li style="font-size: 24px;">Soluções personalizadas para engenheiros, gestores de obras, arquitetos, geólogos, topógrafos e muito mais</li>
            </ul>
            <p style="font-size: 24px;">Estamos aqui para ajudar você a turbinar o relacionamento com seus clientes e parceiros de projetos. Não hesite em entrar em contato se tiver alguma dúvida ou precisar de assistência.</p>
            <br>
            <br>
            <p style="font-size: 20px;">Bem-vindo a bordo!</p>
            <p style="font-size: 20px;">Equipe vIAbilize</p>
        </body>
    </html>
    """

    sender_email = config("SENDER_EMAIL")
    sender_password = config("SENDER_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = email
    text = "Bem-vindo à vIAbilize! Para mais informações, verifique seu email."
    html = body

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
