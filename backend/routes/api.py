from fastapi import APIRouter
from routes.endpoints import user


api_router = APIRouter()
api_router.include_router(user.router, prefix='/users', tags=['Users'])
#api_router.include_router(plan.router, prefix='/plans', tags=['Plans'])
#api_router.include_router(project.router, prefix='/chats', tags=['Chats'])
#api_router.include_router(admin.router, prefix='/admin', tags=['Admin'])
#api_router.include_router(stripe.router, prefix='/stripe', tags=['Stripe'])
