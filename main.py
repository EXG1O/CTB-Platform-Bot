from fastapi import FastAPI

from core.enums import Mode
from core.settings import MODE
import api
import bot

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await bot.start()
    yield
    await bot.stop()


app = FastAPI(
    debug=MODE == Mode.DEBUG,
    openapi_url='/openapi.json' if MODE == Mode.DEBUG else None,
    lifespan=lifespan,
)
app.include_router(api.router)
