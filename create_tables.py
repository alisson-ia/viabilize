from backend.core.configs import settings
from backend.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker



AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_tables() -> None:
    import backend.structure.models
    print('Criando as tabelas no banco de dados...')

    # Criando as tabelas (drop e create) com engine.begin()
    async with engine.begin() as conn:
        await conn.run_sync(settings.DBBaseModel.metadata.drop_all)
        await conn.run_sync(settings.DBBaseModel.metadata.create_all)

    print('Tabelas criadas com sucesso.')


if __name__ == '__main__':
    import asyncio
    asyncio.run(create_tables())
