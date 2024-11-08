from sqlalchemy.ext.asyncio import AsyncSession
from structure.models import LogModel
from datetime import datetime



async def log_user_activity(user_id: int, activity: str, db: AsyncSession):
    log_entry = LogModel(
        datetime=datetime.utcnow(),
        user_id=user_id,
        activity=activity
    )
    async with db as session:
        session.add(log_entry)
        await session.commit()