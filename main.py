import asyncio
from flask import Flask
from asgiref.wsgi import WsgiToAsgi
from app.routes import api_bp
from app.postgresql import engine, db
from app.models import (
    ProcessedEventModel,
    AccountModel,
    AuthorizationModel,
    FundingModel,
    RefundModel,
)

app_flask = Flask(__name__)
app_flask.register_blueprint(api_bp)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(db.metadata.create_all)


# Викликаємо створення таблиць під час запуску додатку
asyncio.run(init_db())

# Асинхронна обгортка для ASGI (uvicorn)
app = WsgiToAsgi(app_flask)
