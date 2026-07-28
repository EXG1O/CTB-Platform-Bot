from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

import bot

from .deps import verify_app_token, verify_telegram_token

telegram_router = APIRouter(dependencies=[Depends(verify_telegram_token)])
app_router = APIRouter(dependencies=[Depends(verify_app_token)])


@telegram_router.post('/telegram/', status_code=status.HTTP_202_ACCEPTED)
async def telegram(request: Request, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(bot.feed_update, await request.body())
