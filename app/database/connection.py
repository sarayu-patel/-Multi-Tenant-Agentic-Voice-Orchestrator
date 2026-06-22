from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

# module-level client — set once at startup, reused across all requests
_client: AsyncIOMotorClient = None


def get_db() -> AsyncIOMotorDatabase:
    return _client[settings.MONGODB_DB_NAME]


async def connect():
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    # quick connectivity check so we fail fast on bad credentials
    await _client.admin.command("ping")
    print("Connected to MongoDB")


async def disconnect():
    global _client
    if _client:
        _client.close()
        print("Disconnected from MongoDB")
