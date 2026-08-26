"""Mongo client for face-auth."""

from __future__ import annotations

import logging
from typing import Optional

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import FaceAuthConfig
from app.core.exceptions import StorageError

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self, config: FaceAuthConfig):
        self.config = config
        try:
            self._client = MongoClient(config.mongo_uri, serverSelectionTimeoutMS=5000)
            self._db: Database = self._client[config.mongo_database]
            self._client.admin.command("ping")
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"MongoDB connection failed: {exc}") from exc

        self._ensure_indexes()
        logger.info("MongoDB connected db=%s", config.mongo_database)

    def _ensure_indexes(self) -> None:
        self.users.create_index([("email", ASCENDING)], unique=True)
        self.users.create_index([("user_id", ASCENDING)], unique=True)
        self.invites.create_index([("token", ASCENDING)], unique=True)
        self.invites.create_index([("email", ASCENDING)])
        self.usage_logs.create_index([("timestamp", ASCENDING)])

    @property
    def users(self) -> Collection:
        return self._db[self.config.users_collection]

    @property
    def invites(self) -> Collection:
        return self._db[self.config.invites_collection]

    @property
    def usage_logs(self) -> Collection:
        return self._db[self.config.usage_logs_collection]

    @property
    def app_settings(self) -> Collection:
        return self._db[self.config.app_settings_collection]


    def close(self) -> None:
        self._client.close()


_mongo: Optional[MongoDB] = None


def get_mongo(config: Optional[FaceAuthConfig] = None) -> MongoDB:
    global _mongo
    if _mongo is None:
        from app.config import get_config

        _mongo = MongoDB(config or get_config())
    return _mongo


def reset_mongo() -> None:
    global _mongo
    if _mongo is not None:
        _mongo.close()
    _mongo = None
