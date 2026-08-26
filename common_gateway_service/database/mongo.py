from pymongo import MongoClient

from common_gateway_service.core.config import settings


_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_db():
    return get_client()[settings.mongodb_db_name]


def get_users_collection():
    collection = get_db()["users"]
    collection.create_index("email", unique=True)
    return collection

