import os
from typing import List, Any
import json

from databases import Database
from dotenv import load_dotenv
from pkg_resources import resource_filename

from src.message import MessageData

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class DatabaseManager:
    def __init__(self):
        self.db = Database(DATABASE_URL)

    async def connect(self):
        if not self.db.is_connected:
            await self.db.connect()

    async def disconnect(self):
        if self.db.is_connected:
            await self.db.disconnect()

    async def create_schema(self):
        schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "init", "schema.sql"))
        print(f"Loading schema from: {schema_path}")
        with open(schema_path) as f:
            schema_sql = f.read()

        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
        for stmt in statements:
            await self.db.execute(stmt)

    async def is_channel_in_database(self, channel_name: str) -> bool:
        query = "SELECT COUNT(*) FROM channels WHERE username = :channel_name"
        row = await self.db.fetch_val(query, {"channel_name": channel_name})
        return row > 0

    async def save_channel_record(self, records: List[Any]) -> None:
        query = """
            INSERT INTO channels (
                original_channel_id,
                channel_url,
                username,
                title,
                participants_count,
                date,
                scam,
                verified,
                has_link,
                fake
            )
            VALUES (
                :original_channel_id,
                :channel_url,
                :username,
                :title,
                :participants_count,
                :date,
                :scam,
                :verified,
                :has_link,
                :fake
            )
            ON CONFLICT (original_channel_id) DO NOTHING
        """
        for record in records:
            await self.db.execute(query, {
                "original_channel_id": record.original_channel_id,
                "channel_url": record.channel_url,
                "username": record.username,
                "title": record.title,
                "participants_count": record.participants_count,
                "date": record.date,
                "scam": record.scam,
                "verified": record.verified,
                "has_link": record.has_link,
                "fake": record.fake
            })

    async def get_last_processed_message_id(self, channel_id: int) -> int:
        query = "SELECT last_processed_message_id FROM channel_state WHERE original_channel_id = :channel_id"
        result = await self.db.fetch_val(query, {"channel_id": channel_id})
        return result or 0

    async def update_last_processed_message_id(self, original_channel_id: int, message_id: int) -> None:
        query = """
            INSERT INTO channel_state (original_channel_id, last_processed_message_id)
            VALUES (:original_channel_id, :message_id)
            ON CONFLICT (original_channel_id)
            DO UPDATE SET last_processed_message_id = EXCLUDED.last_processed_message_id,
                          updated_at = CURRENT_TIMESTAMP
        """
        await self.db.execute(query, {
            "original_channel_id": original_channel_id,
            "message_id": message_id,
        })

    async def update_channel_state(self, original_channel_id: int, message_id: int) -> None:
        query = """
            INSERT INTO channel_state (original_channel_id, last_processed_message_id)
            VALUES (:original_channel_id, :message_id)
            ON CONFLICT (original_channel_id) DO UPDATE
            SET last_processed_message_id = EXCLUDED.last_processed_message_id,
                updated_at = CURRENT_TIMESTAMP
        """
        await self.db.execute(query, {
            "original_channel_id": original_channel_id,
            "message_id": message_id
        })

    async def save_message_record(self, m: MessageData) -> None:
        query = """
            INSERT INTO messages (
                original_message_id,
                original_channel_id,
                channel_username,
                date,
                message,
                message_eng,
                lang_code,
                ts_config,
                pinned,
                views,
                forwards,
                edit_date,
                url_in_message,
                fwd_from,
                fwd_from_date,
                fwd_from_channel_id,
                fwd_from_channel_username,
                fwd_from_channel_link,
                fwd_from_id,
                media
            )
            VALUES (
                :original_message_id,
                :original_channel_id,
                :channel_username,
                :date,
                :message,
                :message_eng,
                :lang_code,
                :ts_config,
                :pinned,
                :views,
                :forwards,
                :edit_date,
                :url_in_message,
                :fwd_from,
                :fwd_from_date,
                :fwd_from_channel_id,
                :fwd_from_channel_username,
                :fwd_from_channel_link,
                :fwd_from_id,
                :media
            )
            ON CONFLICT (original_message_id, original_channel_id) DO NOTHING
        """
        data = m.model_dump()

        if isinstance(data.get("media"), dict):
            data["media"] = json.dumps(data["media"])

        await self.db.execute(query, data)

    async def save_reactions(
            self,
            original_message_id: int,
            original_channel_id: int,
            emoticon: str,
            emoticon_count: int,
            document_id: int = None,
            emoticon_base64: str = None,
    ) -> None:
        query = """
            INSERT INTO reactions (
                original_message_id,
                original_channel_id,
                emoticon,
                emoticon_count,
                document_id,
                emoticon_base64
            )
            VALUES (
                :original_message_id,
                :original_channel_id,
                :emoticon,
                :emoticon_count,
                :document_id,
                :emoticon_base64
            )
            ON CONFLICT DO NOTHING
        """
        await self.db.execute(query, {
            "original_message_id": original_message_id,
            "original_channel_id": original_channel_id,
            "emoticon": emoticon,
            "emoticon_count": emoticon_count,
            "document_id": document_id,
            "emoticon_base64": emoticon_base64,
        })

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
